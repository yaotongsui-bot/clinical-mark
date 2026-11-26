"""eICU Collaborative Research Database Demo v2.0.1 as the evaluator's record rows.

Produces the same row dicts as cm/records.py (MIMIC-IV), so fact checking, retrieval and the judges
run unchanged. Items are mapped to canonical item ids (MIMIC-IV ids) by rules/eicu_items.json.

eICU times are minute offsets from unit admission. Each stay gets a synthetic clock: 2100-01-01 at
the unit admission time of day (unitadmittime24), so offsets read as dates and times. The decision
time T is unit admission + 24 h. A row is known before T when its event offset and, where the table
has one, its entry offset are before T (lab: labresultrevisedoffset; nurse and respiratory charting:
their entry offsets). Rows from earlier in the same hospital stay (negative offsets) are included,
as the MIMIC loader includes the whole admission.

Usage from run.py: --source eicu --mimic-root data/eicu-demo (the flag names the data root).
"""

from __future__ import annotations

import datetime as dt
import json
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd

from . import records

ROOT = Path(__file__).resolve().parents[1]
MAP = json.loads((ROOT / "rules" / "eicu_items.json").read_text(encoding="utf-8"))
T_MIN = MAP["decision_offset_minutes"]
RUN_GAP = MAP["running_infusion_max_gap_minutes"]
DEVICE_ITEM = "226732"
DEVICES = [(re.compile(p, re.I), canonical) for p, canonical in MAP["devices"]]
_ONCE = re.compile(r"^\s*(once|one|stat|x1|once x1|now)\b", re.I)
_UNIT_FIX = (("hr", "hour"), ("hrs", "hour"))


def stay_of(case_id: str) -> int:
    return int(str(case_id).lstrip("E"))


def device_name(raw: str) -> str | None:
    """Free-text oxygen device -> the canonical device vocabulary of rules/measures.json, or None."""
    text = str(raw).strip()
    for pattern, canonical in DEVICES:
        if pattern.search(text):
            return canonical
    return None


def _num(value) -> float | None:
    try:
        v = float(value)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def _fmt(v: float) -> str:
    return f"{v:g}"


class Clock:
    """Synthetic absolute times for one stay."""

    def __init__(self, admit_time24: str):
        h, m, s = (int(x) for x in str(admit_time24 or "00:00:00").split(":"))
        self.admit = dt.datetime(2100, 1, 1, h, m, s)

    def at(self, offset) -> str:
        return (self.admit + dt.timedelta(minutes=float(offset))).strftime("%Y-%m-%d %H:%M:%S")


def _read(root: Path, table: str, stays: set[int], **kw) -> pd.DataFrame:
    df = pd.read_csv(root / f"{table}.csv.gz", low_memory=False, **kw)
    return df[df["patientunitstayid"].isin(stays)]


def patients(root: Path) -> pd.DataFrame:
    return pd.read_csv(root / "patient.csv.gz", low_memory=False)


def stay_rows(root: Path, stays: set[int], start: float | None = None, end: float = T_MIN,
              clocks: dict[int, Clock] | None = None) -> dict[int, list[dict]]:
    """Rows per stay with event (and entry) offsets in [start, end); start None = whole hospital stay.

    Infusions and medications are summarised as known at `end` (running at `end` or ended before it).
    """
    pat = patients(root)
    pat = pat[pat["patientunitstayid"].isin(stays)]
    if clocks is None:
        clocks = {r.patientunitstayid: Clock(r.unitadmittime24) for r in pat.itertuples()}
    lo = -float("inf") if start is None else start
    out: dict[int, list[dict]] = defaultdict(list)

    def keep(event, entry=None) -> bool:
        return lo <= event < end and (entry is None or entry != entry or entry < end)

    # Case header (patient table), entered at unit admission: ICU unit, sex and age, APACHE admission
    # diagnosis. Added 2026-11-17 after the first scoring (PAPER_PLAN.md, deviations): the generators and the
    # test reference saw this header, the systems did not.
    if keep(0):
        for r in pat.itertuples():
            if r.patientunitstayid not in clocks:
                continue
            when, stay = clocks[r.patientunitstayid].at(0), r.patientunitstayid
            out[stay].append(records._row(f"pat:{stay}:unit", "admission", f"ICU unit: {r.unittype}", when,
                                          semantics="recorded_fact", label="ICU unit"))
            out[stay].append(records._row(f"pat:{stay}:patient", "admission", f"Patient: {r.gender}, age {r.age}",
                                          when, semantics="recorded_fact", label="Patient"))
            if not pd.isna(r.apacheadmissiondx):
                out[stay].append(records._row(
                    f"pat:{stay}:dx", "admission", f"Admission diagnosis (APACHE): {r.apacheadmissiondx}", when,
                    semantics="recorded_fact", label="Admission diagnosis"))

    # Laboratory
    lab = _read(root, "lab", stays)
    bounds = MAP["lab_bounds_by_unit"]
    for r in lab.itertuples():
        if not keep(r.labresultoffset, r.labresultrevisedoffset):
            continue
        name = str(r.labname)
        value = _num(r.labresult)
        raw = "" if pd.isna(r.labresulttext) else str(r.labresulttext).strip()
        unit = "" if pd.isna(r.labmeasurenameinterface) else str(r.labmeasurenameinterface).strip()
        lower = upper = None
        if name in bounds:
            lower, upper = (bounds[name].get(unit.casefold()) or [None, None])
        if name in MAP["lab"]:
            itemid, label, table = *MAP["lab"][name], "lab"
        elif name in MAP["lab_chart"]:
            itemid, label, table = *MAP["lab_chart"][name], "chart"
        else:
            itemid, label, table = f"eicu:lab:{name}", name, "lab"
        shown = f"{_fmt(value)} {unit}".strip() if value is not None else raw
        out[r.patientunitstayid].append(records._row(
            f"lab:{r.labid}", "laboratory", f"{label}: {shown}", clocks[r.patientunitstayid].at(r.labresultoffset),
            semantics="measurement", table=table, itemid=itemid, label=label, value=value,
            value_text=None if value is not None else raw, unit=unit, lower=lower, upper=upper))

    # Nurse charting: vital signs, devices, scores, assessments
    nurse = _read(root, "nurseCharting", stays)
    device_nurse = set(MAP["device_sources"]["nurse"])
    for r in nurse.itertuples():
        if not keep(r.nursingchartoffset, r.nursingchartentryoffset):
            continue
        name = str(r.nursingchartcelltypevalname)
        if name in MAP["nurse_skip"]:
            continue
        raw = "" if pd.isna(r.nursingchartvalue) else str(r.nursingchartvalue).strip()
        when = clocks[r.patientunitstayid].at(r.nursingchartoffset)
        rid = f"nurse:{r.nursingchartid}"
        out[r.patientunitstayid].append(_charted(rid, when, name, str(r.nursingchartcelltypevallabel), raw,
                                                 MAP["nurse"].get(name), name in device_nurse
                                                 or str(r.nursingchartcelltypevallabel) in device_nurse))

    # Respiratory charting: ventilator settings, oxygen flow and devices
    resp = _read(root, "respiratoryCharting", stays)
    device_resp = set(MAP["device_sources"]["resp"])
    for r in resp.itertuples():
        if not keep(r.respchartoffset, r.respchartentryoffset):
            continue
        name = str(r.respchartvaluelabel)
        raw = "" if pd.isna(r.respchartvalue) else str(r.respchartvalue).strip()
        raw = MAP["resp_value_map"].get(name, {}).get(raw, raw)
        when = clocks[r.patientunitstayid].at(r.respchartoffset)
        out[r.patientunitstayid].append(_charted(f"resp:{r.respchartid}", when, name, name, raw,
                                                 MAP["resp"].get(name), name in device_resp))

    # Airway (respiratoryCare): context only
    care = _read(root, "respiratoryCare", stays)
    for r in care.itertuples():
        if not keep(r.respcarestatusoffset) or pd.isna(r.airwaytype):
            continue
        extra = ", ".join(str(x) for x in (r.airwaysize, r.airwayposition) if not pd.isna(x))
        out[r.patientunitstayid].append(records._row(
            f"care:{r.respcareid}", "monitoring", f"Airway: {r.airwaytype}" + (f" ({extra})" if extra else ""),
            clocks[r.patientunitstayid].at(r.respcarestatusoffset), semantics="recorded_fact", label="Airway"))

    # Continuous infusions (infusiondrug), summarised into rate intervals
    inf = _read(root, "infusiondrug", stays)
    for (stay, drug), group in inf.groupby(["patientunitstayid", "drugname"]):
        out[stay].extend(_infusion_rows(str(drug), group, clocks[stay], lo, end))

    # Medication orders
    med = _read(root, "medication", stays)
    for r in med.itertuples():
        if pd.isna(r.drugname) or str(r.drugordercancelled).strip().lower() == "yes":
            continue
        if not (r.drugstartoffset < end and r.drugorderoffset < end):
            continue
        stop = r.drugstopoffset
        if r.drugstartoffset < lo and stop > r.drugstartoffset and stop <= end:
            continue  # ended before the window and the order is not active at its end
        out[r.patientunitstayid].append(_medication_row(r, clocks[r.patientunitstayid], end))

    # Documented treatments: context only
    treat = _read(root, "treatment", stays)
    for r in treat.itertuples():
        if not keep(r.treatmentoffset):
            continue
        parts = str(r.treatmentstring).split("|")
        out[r.patientunitstayid].append(records._row(
            f"treat:{r.treatmentid}", "treatment_documentation", "Treatment documented: " + " | ".join(parts[-3:]),
            clocks[r.patientunitstayid].at(r.treatmentoffset), semantics="recorded_fact", label=parts[-1]))

    # Microbiology
    micro = _read(root, "microLab", stays)
    for r in micro.itertuples():
        if not keep(r.culturetakenoffset):
            continue
        org = "no organism reported" if pd.isna(r.organism) else str(r.organism)
        out[r.patientunitstayid].append(records._row(
            f"micro:{r.microlabid}", "specimen", f"Microbiology {r.culturesite}: {org}",
            clocks[r.patientunitstayid].at(r.culturetakenoffset), semantics="recorded_fact"))

    for rows in out.values():
        rows.sort(key=lambda row: row["observed_at"])
    return out


def _charted(rid: str, when: str, name: str, group: str, raw: str, mapped, is_device: bool) -> dict:
    """One nurse or respiratory charting row in canonical form."""
    if is_device:
        canonical = device_name(raw)
        if canonical:
            return records._row(rid, "monitoring", f"O2 Delivery Device(s): {canonical} (charted: {raw})", when,
                                semantics="measurement", table="chart", itemid=DEVICE_ITEM,
                                label="O2 Delivery Device(s)", value_text=canonical)
        return records._row(rid, "monitoring", f"{name}: {raw}", when, semantics="measurement", table="chart",
                            itemid=f"eicu:{name}", label=name, value_text=raw)
    value = _num(raw)
    if mapped:
        itemid, label, unit = mapped
        if itemid == "223761" and value is not None and value < 50:  # a Celsius value in a Fahrenheit field
            value = round(value * 9 / 5 + 32, 1)
        shown = f"{_fmt(value)} {unit}".strip() if value is not None else raw
        return records._row(rid, "monitoring", f"{label}: {shown}", when, semantics="measurement", table="chart",
                            itemid=itemid, label=label, value=value, value_text=None if value is not None else raw,
                            unit=unit)
    if name in ("Value", "nan"):
        label = group
    elif name == group or group == "nan" or name.startswith(group):
        label = name
    else:
        label = f"{group} {name}"
    return records._row(rid, "monitoring", f"{label}: {raw}", when, semantics="measurement", table="chart",
                        itemid=f"eicu:{label}", label=label, value=value, value_text=None if value is not None else raw)


def _drug_and_unit(drugname: str) -> tuple[str, str]:
    m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", drugname)
    name, unit = (m.group(1).strip(), m.group(2).strip()) if m else (drugname.strip(), "")
    for a, b in _UNIT_FIX:
        unit = re.sub(rf"/{a}\b", f"/{b}", unit)
    return name, unit


def _infusion_rows(drugname: str, group: pd.DataFrame, clock: Clock, lo: float, end: float) -> list[dict]:
    """Rate intervals known at `end`: consecutive charted rates of one drug become one interval; a rate
    of 0 ends it. The last interval is running at `end` if its last charting is within RUN_GAP."""
    name, unit = _drug_and_unit(drugname)
    rows, current = [], None  # current = [start, last, rate]
    charted = group[group["infusionoffset"] < end].sort_values("infusionoffset")
    for r in charted.itertuples():
        rate = _num(r.drugrate)
        if rate is None:
            continue
        if current and (rate != current[2] or rate == 0):
            rows.append((current[0], r.infusionoffset, current[2], False))
            current = None
        if rate > 0:
            current = current or [r.infusionoffset, r.infusionoffset, rate]
            current[1] = r.infusionoffset
    if current:
        running = end - current[1] <= RUN_GAP
        rows.append((current[0], current[1], current[2], running))
    out = []
    unit_txt = f" {unit}" if unit else ""
    for start, stop, rate, running in rows:
        if stop < lo:
            continue
        if running:
            text = f"Running at decision time (started {clock.at(start)}): Infusion/input {name} at {_fmt(rate)}{unit_txt}"
        else:
            text = f"Infusion/input {name} at {_fmt(rate)}{unit_txt} ({clock.at(start)} to {clock.at(stop)})"
        out.append(records._row(f"inf:{drugname}:{start}", "treatment", text, clock.at(start), semantics="administration",
                                ongoing=running, label=name))
    return out


def _medication_row(r, clock: Clock, end: float) -> dict:
    name = str(r.drugname).strip()
    # eICU's dosage field holds a coded dose ("5 3"); the drug name usually carries the strength.
    detail = " ".join(str(x).strip() for x in (r.routeadmin, r.frequency) if not pd.isna(x) and str(x).strip())
    start, stop = r.drugstartoffset, r.drugstopoffset
    active = not (stop > start) or stop > end  # a stop offset at or before the start means none recorded
    prn = str(r.prn).strip().lower() == "yes"
    once = bool(_ONCE.match(str(r.frequency))) if not pd.isna(r.frequency) else False
    rid = f"med:{r.medicationid}"
    when = clock.at(start)
    if prn:
        status = "active at decision time" if active else f"stopped {clock.at(stop)}"
        prn_txt = "" if re.search(r"\bprn\b", detail, re.I) else " PRN"
        return records._row(rid, "medication_order", f"Order: {name} {detail}{prn_txt} ({status})", when,
                            semantics="order", ongoing=active, label=name)
    if once:
        return records._row(rid, "medication_administration", f"Given once: {name} {detail} ({when})", when,
                            semantics="administration", label=name)
    if active:
        return records._row(rid, "medication_administration",
                            f"Running at decision time (scheduled order started {when}): Medication {name} {detail}",
                            when, semantics="administration", ongoing=True, label=name)
    return records._row(rid, "medication_administration", f"Medication {name} {detail} ({when} to {clock.at(stop)})",
                        when, semantics="administration", label=name)


# ---- The interface run.py uses (same as cm/records.py) ----

def _clocks_for(root: Path, triples: list[dict]) -> tuple[dict[int, Clock], dict[int, list[str]]]:
    stays = defaultdict(list)
    for t in triples:
        stays[stay_of(t["stay_id"])].append(t["triple_id"])
    pat = patients(root)
    pat = pat[pat["patientunitstayid"].isin(stays)]
    return {r.patientunitstayid: Clock(r.unitadmittime24) for r in pat.itertuples()}, stays


def load_admission_rows(root: Path, triples: list[dict]) -> dict[str, list[dict]]:
    """Every record of the hospital stay known before T = unit admission + 24 h, per case id."""
    clocks, stays = _clocks_for(root, triples)
    rows = stay_rows(root, set(stays), None, T_MIN, clocks)
    return {case: rows.get(stay, []) for stay, cases in stays.items() for case in cases}


def load_post_observations(root: Path, triples: list[dict]) -> dict[str, list[dict]]:
    """Measurements charted in (T, T + 24 h], clipped at unit discharge, for the monitoring checks."""
    clocks, stays = _clocks_for(root, triples)
    pat = patients(root).set_index("patientunitstayid")
    out: dict[str, list[dict]] = defaultdict(list)
    for stay, cases in stays.items():
        end = min(T_MIN + 1440, float(pat.loc[stay, "unitdischargeoffset"]))
        rows = stay_rows(root, {stay}, T_MIN + 1e-9, end + 1e-9, {stay: clocks[stay]}).get(stay, [])
        obs = [{"concept": r["concept"], "itemid": r["itemid"], "record_id": r["rid"], "observed_at": r["observed_at"],
                "value": r["value"] if r["value"] is not None else r["value_text"], "unit": r["unit"]}
               for r in rows if r["concept"]]
        for case in cases:
            out[case] = obs
    return out
