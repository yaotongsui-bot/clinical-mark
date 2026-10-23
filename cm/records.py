"""The gold-standard side: patient records before and after the decision time."""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import re
from collections import defaultdict
from pathlib import Path

from . import rules

ITEM_INDEX = rules.itemid_index()
_ALARM = re.compile(r"\b(?:alarms?|limits?|thresholds?)\b", re.I)
_MAR_GIVEN = re.compile(r"administered|given|applied|started|restarted|bolus", re.I)
_MAR_NOT = re.compile(r"\s*not\b", re.I)  # "Not Given", "Not Started", "Not Given per Sliding Scale"


def mar_given(event: str) -> bool:
    """An eMAR event that is a dose ("Administered", "Started", "Applied"); "Not Given" is not."""
    return bool(_MAR_GIVEN.search(event)) and not _MAR_NOT.match(event)


def ts(value) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(str(value)).replace(tzinfo=None)
    except ValueError:
        return None


def _number(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def series(rows: list[dict], concept: str) -> list[dict]:
    """Time-ordered values of one leaf concept, with the bounds used to classify each value."""
    spec = rules.CONCEPTS.get(concept)
    if not spec:
        return []
    picked = [r for r in rows if r["concept"] == concept and r["value"] is not None]
    if spec["kind"] == "lab":
        lab_rows = [r for r in picked if r["table"] == "lab"]
        picked = lab_rows or picked  # bedside duplicates only when no laboratory row exists
    out = []
    for r in picked:
        if "thresholds" in spec:
            lower, upper = spec["thresholds"].get("low"), spec["thresholds"].get("high")
            basis = "rule"
        elif r["lower"] is not None or r["upper"] is not None:
            lower, upper, basis = r["lower"], r["upper"], "lab_reference"
        else:
            lower, upper = spec.get("fallback_bounds", [None, None])
            basis = "fallback_reference"
        status = ("low" if lower is not None and r["value"] < lower else
                  "high" if upper is not None and r["value"] > upper else "normal")
        out.append({**r, "bound_low": lower, "bound_high": upper, "bound_basis": basis, "status": status})
    out.sort(key=lambda r: r["observed_at"])
    return out


def postdecision_actions(triple: dict) -> list[dict]:
    """Recorded clinician actions in the 24 h after T (the gold standard for AI actions)."""
    decision = ts(triple["decision_point"])
    icu_end = ts(triple["evaluation_eligibility"].get("icu_outtime"))
    out = []
    for row in triple.get("clinician_actions") or []:
        start = ts(row.get("observed_at"))
        spans = bool(row.get("spans_decision_point"))
        if start is None:
            continue
        if not spans and (start <= decision or (icu_end and start >= icu_end)):
            continue
        if spans and row.get("action_type") != "therapy_continued":
            continue
        cls = rules.classify_doctor(row)
        out.append({"aid": row["action_id"], "text": row.get("text") or "", "target": row.get("target") or "",
                    "action_type": row.get("action_type"), "observed_at": row.get("observed_at"),
                    "spans_decision_point": spans, "class": cls, "group": rules.group_of(cls)})
    return out


def _read_gz(path: Path):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle)


def load_post_observations(mimic_root: Path, triples: list[dict]) -> dict[str, list[dict]]:
    """Measurements charted in (T, T+24h], clipped at ICU discharge, keyed by case id.

    Several cases may share one ICU stay (e.g. variants of the same AI answer).
    """
    windows = defaultdict(list)
    for t in triples:
        decision = ts(t["decision_point"])
        end = decision + dt.timedelta(days=1)
        icu_end = ts(t["evaluation_eligibility"].get("icu_outtime"))
        if icu_end:
            end = min(end, icu_end)
        windows[str(t["stay_id"])].append((t["triple_id"], decision, end))
    hadm_to_stays = defaultdict(list)
    for row in _read_gz(mimic_root / "icu" / "icustays.csv.gz"):
        if row["stay_id"] in windows:
            hadm_to_stays[row["hadm_id"]].append(row["stay_id"])
    out: dict[str, list[dict]] = defaultdict(list)

    def add(stay_id: str, table: str, row: dict, ordinal: int) -> None:
        concept = ITEM_INDEX.get((table, row.get("itemid") or ""))
        if concept is None:
            return
        charted = ts(row.get("charttime"))
        value = (row.get("value") or row.get("valuenum") or "").strip()
        if charted is None or not value:
            return
        for case_id, start, end in windows[stay_id]:
            if start < charted <= end:
                out[case_id].append({"concept": concept, "itemid": row.get("itemid"),
                                     "record_id": f"{table}:{row.get('itemid')}:{row['charttime']}:{ordinal}",
                                     "observed_at": row["charttime"], "value": value,
                                     "unit": row.get("valueuom") or ""})

    for ordinal, row in enumerate(_read_gz(mimic_root / "icu" / "chartevents.csv.gz"), 1):
        if row.get("stay_id") in windows:
            add(row["stay_id"], "chart", row, ordinal)
    for ordinal, row in enumerate(_read_gz(mimic_root / "icu" / "outputevents.csv.gz"), 1):
        if row.get("stay_id") in windows:
            add(row["stay_id"], "output", row, ordinal)
    for ordinal, row in enumerate(_read_gz(mimic_root / "hosp" / "labevents.csv.gz"), 1):
        for stay_id in hadm_to_stays.get(row.get("hadm_id") or "", []):
            add(stay_id, "lab", row, ordinal)
    return out


def _row(rid: str, source_type: str, text: str, observed_at: str, *, semantics: str, table: str | None = None,
         itemid: str = "", label: str = "", value=None, value_text: str | None = None, unit: str = "",
         lower=None, upper=None, ongoing: bool = False) -> dict:
    concept = ITEM_INDEX.get((table, itemid)) if table and semantics == "measurement" else None
    return {"rid": rid, "source_type": source_type, "text": text, "value_text": value_text,
            "observed_at": observed_at, "table": table, "itemid": itemid, "label": label,
            "concept": concept, "value": value, "unit": unit, "lower": lower, "upper": upper,
            "semantics": semantics, "ongoing_at_decision": ongoing}


def load_admission_rows(mimic_root: Path, triples: list[dict]) -> dict[str, list[dict]]:
    """Every record of the current hospital admission that was known before the decision time.

    This is the reference EHR of VeriFact (Chung et al., NEJM AI 2026): the whole admission up to T,
    not only what the AI was shown. A row counts as known when its event time is before T and, if it
    has an entry time, it was entered before T. Infusions and procedures still running at T are the
    exception: MIMIC writes such a row when the interval ends, so it is kept with only what was known
    at its start (start time, item, rate), not its end time or total.
    """
    decisions = defaultdict(list)  # several cases may share one ICU stay
    for t in triples:
        decisions[str(t["stay_id"])].append((t["triple_id"], ts(t["decision_point"])))
    stay_to_hadm, hadm_cases = {}, defaultdict(list)
    for row in _read_gz(mimic_root / "icu" / "icustays.csv.gz"):
        stay_to_hadm[row["stay_id"]] = row["hadm_id"]
        if row["stay_id"] in decisions:
            hadm_cases[row["hadm_id"]].extend(decisions[row["stay_id"]])
    stay_cases = {stay: hadm_cases[hadm] for stay, hadm in stay_to_hadm.items() if hadm in hadm_cases}
    chart_labels = {r["itemid"]: r["label"] for r in _read_gz(mimic_root / "icu" / "d_items.csv.gz")}
    lab_labels = {r["itemid"]: r["label"] for r in _read_gz(mimic_root / "hosp" / "d_labitems.csv.gz")}
    out: dict[str, list[dict]] = defaultdict(list)

    def known(event, stored, decision) -> bool:
        event, stored = ts(event), ts(stored)
        return event is not None and event < decision and (stored is None or stored < decision)

    for row in _read_gz(mimic_root / "hosp" / "labevents.csv.gz"):
        for case_id, decision in hadm_cases.get(row.get("hadm_id") or "", []):
            if not known(row["charttime"], row.get("storetime"), decision):
                continue
            label = lab_labels.get(row["itemid"], row["itemid"])
            value = _number(row.get("valuenum"))
            raw = (row.get("value") or "").strip()
            unit = row.get("valueuom") or ""
            shown = raw if value is None else f"{value:g} {unit}".strip()
            out[case_id].append(_row(
                f"lab:{row['labevent_id']}", "laboratory", f"{label}: {shown}", row["charttime"],
                semantics="measurement", table="lab", itemid=row["itemid"], label=label, value=value,
                value_text=raw if value is None else None, unit=unit,
                lower=_number(row.get("ref_range_lower")), upper=_number(row.get("ref_range_upper"))))
    for row in _read_gz(mimic_root / "icu" / "chartevents.csv.gz"):
        for case_id, decision in stay_cases.get(row.get("stay_id") or "", []):
            if not known(row["charttime"], row.get("storetime"), decision):
                continue
            label = chart_labels.get(row["itemid"], row["itemid"])
            value = _number(row.get("valuenum"))
            raw = (row.get("value") or "").strip()
            unit = row.get("valueuom") or ""
            if row["itemid"] == "223762" and value is not None:  # Temperature Celsius -> Fahrenheit
                value, unit = round(value * 9 / 5 + 32, 1), "F"
            numeric_raw = _number(raw) is not None
            if value is not None and numeric_raw:
                shown = f"{value:g} {unit}".strip()
            elif value is not None:
                shown = f"{raw} ({value:g})"  # scales keep their score: "Spontaneously (4)"
            else:
                shown = raw
            semantics = "alarm_setting" if _ALARM.search(label) else "measurement"
            out[case_id].append(_row(
                f"chart:{row['stay_id']}:{row['itemid']}:{row['charttime']}", "monitoring", f"{label}: {shown}",
                row["charttime"], semantics=semantics, table="chart", itemid=row["itemid"], label=label,
                value=value, value_text=None if numeric_raw else raw, unit=unit))
    for row in _read_gz(mimic_root / "hosp" / "emar.csv.gz"):
        for case_id, decision in hadm_cases.get(row.get("hadm_id") or "", []):
            if not known(row["charttime"], row.get("storetime"), decision):
                continue
            event = (row.get("event_txt") or "charted").strip()
            given = mar_given(event)
            out[case_id].append(_row(
                f"emar:{row['emar_id']}", "medication_administration", f"MAR {event}: {row.get('medication') or ''}",
                row["charttime"], semantics="administration" if given else "mar_other", label=row.get("medication") or ""))
    for row in _read_gz(mimic_root / "hosp" / "prescriptions.csv.gz"):
        for case_id, decision in hadm_cases.get(row.get("hadm_id") or "", []):
            start, stop = ts(row.get("starttime")), ts(row.get("stoptime"))
            if start is None or start >= decision:
                continue
            dose = " ".join(x for x in (row.get("dose_val_rx"), row.get("dose_unit_rx"), row.get("route")) if x)
            active = stop is None or stop > decision
            status = "active at decision time" if active else f"stopped {row.get('stoptime')}"
            out[case_id].append(_row(
                f"rx:{row['pharmacy_id']}:{row['starttime']}", "medication_order",
                f"Order: {row.get('drug')} {dose} ({status})", row["starttime"], semantics="order", ongoing=active,
                label=row.get("drug") or ""))
    for table, kind in (("inputevents", "Infusion/input"), ("procedureevents", "Procedure")):
        for row in _read_gz(mimic_root / "icu" / f"{table}.csv.gz"):
            for case_id, decision in stay_cases.get(row.get("stay_id") or "", []):
                start, end = ts(row.get("starttime")), ts(row.get("endtime"))
                if start is None or start >= decision:
                    continue
                running = end is not None and end > decision
                # Interval rows are written when the interval ends (98% of those running at T are stored
                # at or after their end), so a row running at T is kept with what was known at its start.
                if not running and not known(row["starttime"], row.get("storetime"), decision):
                    continue
                label = chart_labels.get(row["itemid"], row["itemid"])
                rate = f" at {row['rate']} {row.get('rateuom') or ''}".rstrip() if row.get("rate") else ""
                amount = f" {row['amount']} {row.get('amountuom') or ''}".rstrip() if row.get("amount") and not rate else ""
                if running:
                    text = f"Running at decision time (started {row['starttime']}): {kind} {label}{rate}"
                else:
                    text = f"{kind} {label}{amount}{rate} ({row['starttime']} to {row.get('endtime')})"
                out[case_id].append(_row(
                    f"{table}:{row.get('orderid') or ''}:{row['itemid']}:{row['starttime']}",
                    "treatment" if table == "inputevents" else "procedure", text, row["starttime"],
                    semantics="administration", ongoing=running, label=label))
    for row in _read_gz(mimic_root / "hosp" / "microbiologyevents.csv.gz"):
        for case_id, decision in hadm_cases.get(row.get("hadm_id") or "", []):
            when = row.get("charttime") or row.get("chartdate")
            if not known(when, row.get("storetime"), decision):
                continue
            result = " ".join(x for x in (row.get("org_name"), row.get("interpretation")) if x) or "no organism reported"
            out[case_id].append(_row(
                f"micro:{row['microevent_id']}", "specimen",
                f"Microbiology {row.get('spec_type_desc')}: {row.get('test_name')}: {result}", when,
                semantics="recorded_fact"))
    for rows in out.values():
        rows.sort(key=lambda r: r["observed_at"])
    return out
