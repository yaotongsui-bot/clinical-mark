"""Stage 2a: check AI facts against pre-decision records (records are the gold standard).

Measurable statements (a lab or vital sign that is high / low / abnormal / normal) are decided
by code from the recorded values and bounds. Statements without a measurable form go to the
judge panel with a reference context retrieved by hybrid search (VeriFact, NEJM AI 2026); the
judges never see the other AI atoms.

Labels follow VeriFact: supported, not_supported, not_addressed; plus unverifiable for statements
that cannot be checked against structured records at all (vague wording, alarm events, necessity).
"""

from __future__ import annotations

import datetime as dt
import json
import re
import statistics

from . import records, rules
from .panel import Request
from .retrieve import Retriever

SUPPORTED, NOT_SUPPORTED, NOT_ADDRESSED, UNVERIFIABLE = "supported", "not_supported", "not_addressed", "unverifiable"
LABELS = (SUPPORTED, NOT_SUPPORTED, NOT_ADDRESSED, UNVERIFIABLE)
JUDGE_SCHEMA = {"type": "object", "required": ["label", "evidence", "reason"],
                "properties": {"label": {"type": "string", "enum": [SUPPORTED, NOT_SUPPORTED, NOT_ADDRESSED]},
                               "evidence": {"type": "array", "items": {"type": "string"}},
                               "reason": {"type": "string", "maxLength": 400}}}
VITAL_WINDOW = dt.timedelta(hours=6)
RECENT_WINDOW = dt.timedelta(hours=24)
_NEGATION = re.compile(r"\b(no|not|without|absence of|denies)\b", re.I)
_ALARM = re.compile(r"\balarms?\b", re.I)
_VAGUE = re.compile(r"\b(symptoms?|signs?)\b", re.I)
_NECESSITY = re.compile(r"\b(need(ed|s)?|necessary|required|indicated|warranted)\b", re.I)
_HEDGE = re.compile(r"\b(potential|possible|possibly|may|might|could|can indicate|suggest\w*|likely|"
                    r"suspect\w*|suspicion|risk (of|for)|at risk)\b", re.I)
# A past-history statement is not checked against current values ("history of hypertension").
_HISTORY = re.compile(r"\bhistory of\b", re.I)
# A statement that only reports a value ("Potassium is 3.4 mEq/L") is checked against the recorded
# values, not against a direction the atomizer inferred from it.
_DIRECTION_WORD = re.compile(
    r"\b(high|low|elevated|raised|increased|decreased|reduced|depressed|abnormal|normal|deranged|above|below|"
    r"rising|falling|worsen\w*|improv\w*|hyper\w+|hypo\w+|tachy\w*|brady\w*|febrile|afebrile|"
    r"leukocyt\w*|acidosis|alkalosis|acidemi\w*|alkalemi\w*)\b", re.I)
_BOUNDARY = re.compile(r"\b(low|high)[- ]normal\b", re.I)
_BORDERLINE = re.compile(r"\bborderline\b", re.I)
_NAME_WITH_DIGITS = re.compile(r"\b[a-z]+\d+[a-z]*\b|\d{1,2}:\d{2}(:\d{2})?|\b\d{4}-\d{2}-\d{2}\b", re.I)
# What the patient was on when a value was taken is context, not the value ("SpO2 91% on 2 L/min").
_VALUE_CONTEXT = re.compile(r"\b(?:while\s+)?(?:on|with|via)\s+(?:an?\s+)?(?:fi\s?o2\b|peep\b|\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?\s*"
                            r"(?:%\s*)?(?:l\b|l/min|lpm|liters?|litres?|fi\s?o2|oxygen|o2)).*$", re.I)
_NUMBER = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?)(?:\s*(?:-|–|to)\s*(-?\d+(?:\.\d+)?))?(?!\w|\.\d)")


def _stated_values(text: str) -> list[tuple[float, float, float]]:
    """(low, high, tolerance) for each value or range the statement gives; tolerance is half a unit
    of the stated precision (3.4 matches 3.35 to 3.45)."""
    out = []
    text = _VALUE_CONTEXT.sub(" ", text.replace("−", "-"))
    for m in _NUMBER.finditer(_NAME_WITH_DIGITS.sub(" ", text)):
        a, b = m.group(1), m.group(2) or m.group(1)
        decimals = max(len(a.partition(".")[2]), len(b.partition(".")[2]))
        lo, hi = sorted((float(a), float(b)))
        out.append((lo, hi, 0.5 * 10 ** -decimals + 1e-9))
    return out


def _stated_value_check(rows: list[dict], concept: str, text: str, decision: dt.datetime) -> dict | None:
    """Supported when every stated value (or range) matches a value recorded before the decision,
    preferring the 24 h before it; None when the statement gives no usable value."""
    stated = _stated_values(text)
    if not stated:
        return None
    # A stated value may come from a bedside reading (fingerstick glucose) that series() leaves out
    # when laboratory rows exist, so both are searched.
    bedside = records.series([r for r in rows if r["concept"] == concept and r.get("table") != "lab"], concept)
    values = sorted({v["rid"]: v for v in records.series(rows, concept) + bedside}.values(),
                    key=lambda v: v["observed_at"])
    name = rules.concept_name(concept)
    if not values:
        return {"label": NOT_ADDRESSED, "evidence": [], "reason": f"No {name} recorded before the decision time."}
    window = [v for v in values if records.ts(v["observed_at"]) >= decision - RECENT_WINDOW] or values[-1:]
    recorded = [v["value"] for v in values]
    lo_all, hi_all = min(recorded), max(recorded)

    def hits(pool, lo, hi, tol):
        return [v for v in pool if lo - tol <= v["value"] <= hi + tol]

    matched, missing = [], []
    for lo, hi, tol in stated:
        found = hits(window, lo, hi, tol) or hits(values, lo, hi, tol)
        (matched if found else missing).append((lo, hi, found))
    unit = values[-1]["unit"]
    shown = lambda lo, hi: f"{lo:g}" if lo == hi else f"{lo:g}-{hi:g}"
    if missing:
        far = all(hi < lo_all / 3 or lo > hi_all * 3 for lo, hi, _ in missing)
        if far:  # e.g. calcium stated in mmol/L against mg/dL records
            return {"label": UNVERIFIABLE, "evidence": [_cite(v) for v in window[-3:]],
                    "reason": f"The stated {name} ({', '.join(shown(lo, hi) for lo, hi, _ in missing)}) is far outside every "
                              f"recorded value ({lo_all:g} to {hi_all:g} {unit}); probably another unit or specimen."}
        w = [v["value"] for v in window]
        return {"label": NOT_SUPPORTED, "evidence": [_cite(v) for v in window[-3:]],
                "reason": f"No recorded {name} matches the stated {', '.join(shown(lo, hi) for lo, hi, _ in missing)}; "
                          f"values in the 24 h before the decision ranged {min(w):g} to {max(w):g} {unit} "
                          f"(latest {window[-1]['value']:g})."}
    cited = [v for _, _, found in matched for v in found[-1:]]
    seen = ", ".join("%g at %s" % (v["value"], v["observed_at"]) for v in cited[-3:])
    return {"label": SUPPORTED, "evidence": [_cite(v) for v in cited[-3:]],
            "reason": f"The stated {name} ({', '.join(shown(lo, hi) for lo, hi, _ in matched)}) matches recorded values "
                      f"before the decision ({seen})."}


def _meets(status: str, direction: str) -> bool:
    return {"high": status == "high", "low": status == "low",
            "abnormal": status != "normal", "normal": status == "normal"}[direction]


def _cite(row: dict) -> dict:
    low = row["bound_low"] if row["bound_low"] is not None else "-"
    high = row["bound_high"] if row["bound_high"] is not None else "-"
    return {"rid": row["rid"], "time": row["observed_at"], "item": row["label"],
            "value": row["value"], "unit": row["unit"], "bounds": f"{low} to {high}",
            "bounds_basis": row["bound_basis"], "status": row["status"]}


def _unverifiable(reason: str) -> dict:
    return {"label": UNVERIFIABLE, "method": "rule", "evidence": [], "reason": reason}


def _leaf(rows: list[dict], concept: str, direction: str, time: str, decision: dt.datetime) -> dict:
    values = records.series(rows, concept)
    name = rules.concept_name(concept)
    if not values:
        return {"label": NOT_ADDRESSED, "evidence": [], "reason": f"No {name} recorded before the decision time."}
    kind = rules.CONCEPTS[concept]["kind"]
    latest = values[-1]
    window = [v for v in values if records.ts(v["observed_at"]) >= decision - RECENT_WINDOW]
    if time in {"recent", "persistent"} and not window:
        return {"label": NOT_ADDRESSED, "evidence": [_cite(latest)],
                "reason": f"No {name} in the 24 h before the decision (last at {latest['observed_at']})."}
    if time == "recent":
        values = window
        hits = [v for v in values if _meets(v["status"], direction)]
        cited = (hits or values)[-3:]
        return {"label": SUPPORTED if hits else NOT_SUPPORTED, "evidence": [_cite(v) for v in cited],
                "reason": f"{len(hits)} of {len(values)} {name} values in the 24 h before the decision were {direction}."}
    if kind == "vital":
        recent = [v for v in values if records.ts(v["observed_at"]) >= decision - VITAL_WINDOW] or [latest]
        median = statistics.median(v["value"] for v in recent)
        low, high = latest["bound_low"], latest["bound_high"]
        status = ("low" if low is not None and median < low else
                  "high" if high is not None and median > high else "normal")
        rule = rules.CONCEPTS[concept].get("rule", "")
        return {"label": SUPPORTED if _meets(status, direction) else NOT_SUPPORTED,
                "evidence": [_cite(v) for v in recent[-4:]],
                "reason": f"Median {name} over the 6 h before the decision: {median:g} {latest['unit']} "
                          f"({len(recent)} readings), {status} by the rule '{rule}'.",
                "computed": {"median": median, "status": status, "n": len(recent)}}
    hit = _meets(latest["status"], direction)
    if time == "persistent" and hit:
        values = window
        n_hits = sum(_meets(v["status"], direction) for v in values)
        return {"label": SUPPORTED, "evidence": [_cite(v) for v in values[-3:]],
                "reason": f"Latest {name} {latest['value']:g} {latest['unit']} (reference {_cite(latest)['bounds']}); "
                          f"{n_hits} of {len(values)} values in the 24 h before the decision were {direction}."}
    return {"label": SUPPORTED if hit else NOT_SUPPORTED, "evidence": [_cite(v) for v in values[-3:]],
            "reason": f"Latest {name} {latest['value']:g} {latest['unit']} at {latest['observed_at']} "
                      f"(reference {_cite(latest)['bounds']}) is {latest['status']}, "
                      f"{'consistent' if hit else 'not consistent'} with '{direction}'."}


def _composite(rows, concept, direction, time, decision) -> dict:
    members = rules.leaf_members(concept)
    results = {m: _leaf(rows, m, direction, time, decision)
               for m in members if rules.CONCEPTS[m]["kind"] in {"lab", "vital"}}
    with_data = {m: r for m, r in results.items() if r["label"] != NOT_ADDRESSED}
    name = rules.concept_name(concept)
    if not with_data:
        return {"label": NOT_ADDRESSED, "evidence": [],
                "reason": f"None of the {name} components were recorded before the decision time."}
    if direction == "normal":
        bad = [m for m, r in with_data.items() if r["label"] == NOT_SUPPORTED]
        label, chosen = (NOT_SUPPORTED if bad else SUPPORTED), (bad or list(with_data))
    else:
        good = [m for m, r in with_data.items() if r["label"] == SUPPORTED]
        label, chosen = (SUPPORTED if good else NOT_SUPPORTED), (good or list(with_data))
    evidence = [e for m in chosen for e in with_data[m]["evidence"][-1:]]
    summary = "; ".join(f"{rules.concept_name(m)}: {'yes' if r['label'] == SUPPORTED else 'no'}"
                        for m, r in with_data.items())
    return {"label": label, "evidence": evidence,
            "reason": f"'{name} {direction}' holds when any component is {direction}. {summary}."}


def _syndrome(rows, concept, direction, decision) -> dict:
    spec = rules.SYNDROMES[concept]
    parts, evidence = [], []
    for member, want in spec["all"]:
        values = records.series(rows, member)
        if not values:
            return {"label": NOT_ADDRESSED, "evidence": evidence,
                    "reason": f"No {rules.concept_name(member)} recorded, so {spec['name']} cannot be judged."}
        latest = values[-1]
        evidence.append(_cite(latest))
        parts.append((member, want, _meets(latest["status"], want), latest))
    present = all(ok for _, _, ok, _ in parts)
    detail = "; ".join(f"{rules.concept_name(m)} {v['value']:g} ({w} required: {'yes' if ok else 'no'})"
                       for m, w, ok, v in parts)
    return {"label": SUPPORTED if present == (direction != "absent") else NOT_SUPPORTED, "evidence": evidence,
            "reason": f"{spec['name']}: {detail}."}


_VENTILATION_CLAIM = re.compile(r"mechanical ventilation|invasive ventilation|ventilator|intubat", re.I)
_NONINVASIVE = re.compile(r"non-?invasive|bipap|cpap", re.I)


def _ventilation_status(rows: list[dict], decision: dt.datetime) -> dict:
    """Is the patient on invasive ventilation at T? Decided from the latest ventilation indicator."""
    spec = rules.MEASURES["ventilation_status"]
    indicators, last_tube = [], ""
    device_values = {v.casefold() for v in spec["negative_devices"]}
    tubes = {v.casefold() for v in spec["tube_devices"]}
    for r in rows:
        if r["ongoing_at_decision"] and re.search(r"invasive ventilation", r["text"], re.I) \
                and not _NONINVASIVE.search(r["text"]):
            return {"label": SUPPORTED, "reason": "Invasive ventilation was running at the decision time.",
                    "evidence": [{"rid": r["rid"], "time": r["observed_at"], "item": r["text"]}]}
        raw = (r.get("value_text") or "").strip().rstrip(".").upper()
        if r["table"] == "chart" and r["itemid"] in spec["positive_chart_items"]:
            negative = any(v.upper() == raw for v in spec["negative_chart_values"])
            indicators.append((r["observed_at"], not negative, r))
        elif r["table"] == "lab" and r["itemid"] in spec["lab_values"]:
            verdict = spec["lab_values"][r["itemid"]].get(raw)
            if verdict is not None:
                indicators.append((r["observed_at"], verdict, r))
        elif r["table"] == "chart" and r["itemid"] == spec["device_item"]:
            device = raw.casefold()
            if device in tubes:
                last_tube = max(last_tube, r["observed_at"])
            elif device in device_values:
                indicators.append((r["observed_at"], False, r))
    # A tube device charted after a mask or cannula row means the patient went back on the tube.
    indicators = [x for x in indicators if x[1] or x[2].get("itemid") != spec["device_item"] or x[0] >= last_tube]
    if not indicators:
        return {"label": NOT_ADDRESSED, "evidence": [],
                "reason": "No ventilator or intubation record before the decision time."}
    when, positive, row = max(indicators, key=lambda x: (x[0], not x[1]))
    gap = (decision - records.ts(when)).total_seconds() / 3600
    cite = [{"rid": row["rid"], "time": when, "item": row["text"]}]
    if not positive:
        return {"label": NOT_SUPPORTED, "evidence": cite,
                "reason": f"The latest record before the decision ({when}) reads '{row['text']}'."}
    if gap > spec["max_gap_hours"]:
        return {"label": NOT_SUPPORTED, "evidence": cite,
                "reason": f"The last ventilator/intubation record ('{row['text']}') was {gap:.1f} h before the decision, "
                          f"with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the "
                          f"rule (> {spec['max_gap_hours']} h without a record) the patient was not ventilated at T."}
    return {"label": SUPPORTED, "evidence": cite,
            "reason": f"Ventilator charting {gap:.1f} h before the decision ('{row['text']}')."}


_EXPANSIONS = [
    (r"ventilat|intubat", "Intubated Ventilator Ventilator Mode PEEP set Invasive Ventilation"),
    (r"alarm", "Alarm Alarms On"),
    (r"oxygen|o2", "O2 Flow O2 Delivery Device O2 saturation Inspired O2 Fraction"),
    (r"epithelial|urine|cast|bacteria", "Urine Epithelial Cells Bacteria"),
]


_VENT_SETTING = re.compile(r"\b(peep|tidal volume|fi\s?o2|inspired o2|set (respiratory )?rate|respiratory rate \(set\)|"
                          r"ventilator (mode|setting)\w*|pressure support|psv|minute ventilation)\b", re.I)


def _latest_devices(rows: list[dict], decision_rows: int = 2) -> list[dict]:
    """The last O2 device rows: search ranks these low for a PEEP or tidal volume statement, yet they show
    whether the setting still applies."""
    item = rules.MEASURES["ventilation_status"]["device_item"]
    found = [r for r in rows if r["table"] == "chart" and r["itemid"] == item]
    return sorted(found, key=lambda r: r["observed_at"])[-decision_rows:]


def _judge_request(atom: dict, rows: list[dict], triple: dict, system: str, retriever: Retriever) -> dict:
    """Retrieve reference facts (hybrid search) and build a panel request; the panel decides later."""
    sparse_query = atom["text"]
    for pattern, extra in _EXPANSIONS:
        if re.search(pattern, sparse_query, re.I):
            sparse_query += " " + extra
    cls, _ = rules.classify_ai(atom["text"], atom["text"])
    if cls:
        for spec in rules.CLASSES:
            if cls in (spec["id"], spec["group"]):
                sparse_query += " " + " ".join(re.sub(r"[^a-z ]", " ", p) for p in spec["patterns"])
    pool = [r for r in rows if r["semantics"] != "alarm_setting" or re.search(r"alarm", atom["text"], re.I)]
    picked = retriever.search(atom["text"], sparse_query, pool)
    if picked and _VENT_SETTING.search(atom["text"]):
        have = {r["rid"] for r in picked}
        picked = sorted(picked + [r for r in _latest_devices(rows) if r["rid"] not in have], key=lambda r: r["observed_at"])
    if not picked:
        return {"label": NOT_ADDRESSED, "evidence": [], "method": "rule",
                "reason": "No pre-decision record related to the statement was retrieved."}
    alias = {f"R{i}": r for i, r in enumerate(picked, 1)}
    # VeriFact formats the reference context in chronological order with absolute date, time and source.
    packet = {"decision_time": triple["decision_point"], "ai_statement": atom["text"],
              "ai_original_sentence": atom["claim_text"],
              "records_in_time_order": [
                  {"id": k, "date": r["observed_at"][:10], "time": r["observed_at"][11:16],
                   "source": r["source_type"], "type": r["semantics"], "text": r["text"],
                   **({"ongoing_at_decision": True} if r["ongoing_at_decision"] else {})}
                  for k, r in alias.items()]}
    request = Request(key=f"fact:{atom['atom_id']}", stage="fact_judge", case_id=triple["triple_id"],
                      system=system, user=json.dumps(packet, ensure_ascii=False), schema=JUDGE_SCHEMA,
                      cite_key="evidence", needs_cite={SUPPORTED, NOT_SUPPORTED}, allowed=set(alias),
                      fallback=NOT_ADDRESSED)
    return {"pending": request, "alias": alias, "statement": atom["text"],
            "delivered": _delivered(atom["text"], rows, records.ts(triple["decision_point"])),
            "running": _running(atom["text"], rows), "mentioned": _mentioned(atom["text"], rows)}


_ADMINISTRATION_CLAIM = re.compile(r"\b(receiv\w*|given|administ\w*|infus\w*|currently on)\b", re.I)
_NOT_GIVEN = re.compile(r"not given|held|stopped|discontinu", re.I)
_RATE_INTERVAL = re.compile(r" at [\d.]+ \S+/(hour|min)\b.*\(.* to .*\)$")  # a rate infusion with its end time
# Charted items show delivery only for devices; others that name a treatment are assessments
# ("Braden Nutrition", "Richmond-RAS Scale"), and laboratory rows are tests ("Methadone, Urine").
_DEVICE_CHARTING = re.compile(r"(pca\b|bipap|cpap|ventilator|o2 delivery device|o2 flow|peep|tidal volume|inspired o2)", re.I)


def _treatment(statement: str) -> tuple[str, str, str | None] | None:
    """(class or group, level, named drug) of a 'receiving / given' statement, or None."""
    target, level = rules.classify_ai(statement, statement) if _ADMINISTRATION_CLAIM.search(statement) else (None, "")
    return (target, level, rules.named_drug(statement, target) if level == "class" else None) if target else None


def _about(row: dict, treatment: tuple[str, str, str | None] | None) -> bool:
    """A named drug must appear by name, a named class must match ("potassium chloride" is not met by
    magnesium), a group named in general terms ("pain management") is met by any member."""
    if treatment is None:
        return True
    target, level, drug = treatment
    name = row["label"] if row["table"] is None and row["label"] else row["text"]  # drug or item name
    if rules.group_of(target) == "oxygen":  # device charting, which the treatment classes do not cover
        return bool(re.match(r"o2 (delivery device|flow)", name, re.I)) and not re.search(r":\s*none\b", name, re.I)
    if drug:
        return bool(re.search(drug, name, re.I))
    found = rules.classify_target(name)
    if target in rules.also_classes(name):
        return True
    return found is not None and (found == target if level == "class"
                                  else rules.group_of(found) == rules.group_of(target))


def _delivered(statement: str, rows: list[dict], decision: dt.datetime) -> bool | None:
    """Was the treatment of a 'receiving / given' statement delivered in the 24 h before the decision
    (administration, device charting, or running at T)? None when no known treatment is named."""
    treatment = _treatment(statement)
    if treatment is None:
        return None
    return any((r["semantics"] == "administration" or (r["table"] == "chart" and _DEVICE_CHARTING.match(r["label"])))
               and (r["ongoing_at_decision"] or records.ts(r["observed_at"]) >= decision - RECENT_WINDOW)
               and _about(r, treatment) for r in rows)


def _running(statement: str, rows: list[dict]) -> bool | None:
    """Is the treatment of a 'receiving / given' statement running at the decision time? None when no
    known treatment is named."""
    treatment = _treatment(statement)
    if treatment is None:
        return None
    return any(r["ongoing_at_decision"] and r["semantics"] == "administration" and _about(r, treatment) for r in rows)


def _mentioned(statement: str, rows: list[dict]) -> bool | None:
    """Do the records mention the treatment of a 'receiving / given' statement at all (an order, a
    dose, an eMAR event, a procedure or device charting)? Laboratory rows and assessments do not
    count. None when no known treatment is named."""
    treatment = _treatment(statement)
    if treatment is None:
        return None
    return any((r["semantics"] in {"administration", "order", "mar_other"} or r["source_type"] == "procedure"
                or (r["table"] == "chart" and _DEVICE_CHARTING.match(r["label"] or "")))
               and _about(r, treatment) for r in rows)


def _ended_infusion(row: dict, treatment, running: bool | None) -> bool:
    """A rate infusion of this treatment that ended before the decision time, with none of it running
    at that time, shows the infusion was stopped."""
    return running is False and row["semantics"] == "administration" and not row["ongoing_at_decision"] \
        and bool(_RATE_INTERVAL.search(row["text"])) and _about(row, treatment)


def _shows_off(row: dict, treatment: tuple[str, str, str | None] | None) -> bool:
    """Does this record show that oxygen or non-invasive ventilation was off? For these treatments the record is
    device charting or an ended procedure, not a held or stopped drug."""
    if treatment is None or rules.group_of(treatment[0]) not in {"oxygen", "ventilation"}:
        return False
    spec = rules.MEASURES["ventilation_status"]
    if row["table"] == "chart" and row["itemid"] == spec["device_item"]:
        device = (row.get("value_text") or "").strip().casefold()
        if rules.group_of(treatment[0]) == "oxygen":
            return device == "none"
        return device in {v.casefold() for v in spec["negative_devices"]} and not _NONINVASIVE.search(device)
    return rules.group_of(treatment[0]) == "ventilation" and not row["ongoing_at_decision"] and \
        row["text"].startswith("Procedure") and bool(re.search(r"ventilation", row["text"], re.I))


def _administration_guard(statement: str, label: str, cited: list[dict], delivered: bool | None,
                          running: bool | None = None) -> str | None:
    """The judges often cite orders or another drug's record for 'receiving / given X', and sometimes
    support what was never given, so support is checked against the records; with no known treatment
    named, support must cite more than orders. not_supported must cite a record of X showing it was
    withheld or stopped. Returns the reason for a downgrade to not_addressed, or None."""
    if not _ADMINISTRATION_CLAIM.search(statement):
        return None
    if label == SUPPORTED and delivered is False:
        return "No administration of this treatment is recorded in the 24 h before the decision."
    if label == SUPPORTED and delivered is None and cited and all(r["semantics"] == "order" for r in cited):
        return "Only orders were cited; an order does not show that the treatment was given."
    treatment = _treatment(statement)  # a stopped flush says nothing about potassium chloride
    if label == NOT_SUPPORTED and not any(_shows_off(r, treatment) or _ended_infusion(r, treatment, running) or
                                          ((_NOT_GIVEN.search(r["text"]) or r["semantics"] == "mar_other") and _about(r, treatment))
                                          for r in cited):
        return "No cited record shows this treatment was withheld or stopped; absence of a record is not_addressed."
    return None


def _verifact_guard(statement: str, label: str, cited: list[dict], delivered: bool | None,
                    mentioned: bool | None) -> tuple[str, str] | None:
    """The guard under VeriFact's labels: a treatment the records mention but do not show given in
    the 24 h before the decision is not_supported (addressed, not supported); not_addressed only
    when the records never mention it. Returns (new label, reason) or None."""
    if not _ADMINISTRATION_CLAIM.search(statement):
        return None
    if label == SUPPORTED and delivered is False:
        if mentioned:
            return NOT_SUPPORTED, "The records mention this treatment but show no administration in the 24 h before the decision."
        return NOT_ADDRESSED, "No record of this treatment."
    if label == SUPPORTED and delivered is None and cited and all(r["semantics"] == "order" for r in cited):
        return NOT_SUPPORTED, "Only orders were cited; an order does not show that the treatment was given."
    if label == NOT_ADDRESSED and delivered is False and mentioned:
        return NOT_SUPPORTED, "The records mention this treatment but show no administration in the 24 h before the decision."
    return None


def finalize(pending: dict, verdict: dict) -> dict:
    alias = pending["alias"]
    cited = [alias[c] for c in verdict["cites"]]
    label, reason = verdict["label"], verdict["reason"]
    statement = pending.get("statement", "")
    if pending.get("no_guard"):
        change = None
    elif pending.get("verifact_labels"):
        change = _verifact_guard(statement, label, cited, pending.get("delivered"), pending.get("mentioned"))
    else:
        downgrade = _administration_guard(statement, label, cited, pending.get("delivered"), pending.get("running"))
        change = (NOT_ADDRESSED, downgrade) if downgrade else None
    if change:
        label, reason = change[0], f"{change[1]} (Panel verdict: {verdict['label']}.)"
    return {"label": label, "reason": reason, "method": "llm_panel",
            "panel": {"agreement": verdict["agreement"], "votes": verdict["votes"],
                      **({"panel_label": verdict["label"]} if change else {})},
            "evidence": [{"rid": r["rid"], "time": r["observed_at"], "item": r["text"]} for r in cited]}


def indication_present(rows: list[dict], concept: str, direction: str, decision: dt.datetime,
                       threshold: float | None = None) -> tuple[bool, str]:
    """Was this abnormality present at the decision time? Used to find problem-linked actions.

    With a treatment threshold, the latest lab value (or the 6 h vital-sign median) is compared
    with it instead of the reference range.
    """
    if threshold is not None and concept in rules.CONCEPTS:
        values = records.series(rows, concept)
        if not values:
            return False, ""
        if rules.CONCEPTS[concept]["kind"] == "vital":
            recent = [v for v in values if records.ts(v["observed_at"]) >= decision - VITAL_WINDOW] or values[-1:]
            value = statistics.median(v["value"] for v in recent)
        else:
            value = values[-1]["value"]
        present = value > threshold if direction == "high" else value < threshold
        op = ">" if direction == "high" else "<"
        return present, (f"Latest {rules.concept_name(concept)} {value:g} {values[-1]['unit']} "
                         f"(treatment threshold {op} {threshold:g}).")
    if concept in rules.SYNDROMES:
        result = _syndrome(rows, concept, "present", decision)
    elif concept in rules.COMPOSITES:
        result = _composite(rows, concept, direction, "current", decision)
    elif concept in rules.CONCEPTS and rules.CONCEPTS[concept]["kind"] in {"lab", "vital"}:
        result = _leaf(rows, concept, direction, "current", decision)
    else:
        return False, ""
    return result["label"] == SUPPORTED, result["reason"]


def verify(atom: dict, rows: list[dict], triple: dict, system: str, retriever: Retriever,
           all_to_judge: bool = False, labels: str = "clinical_mark") -> dict:
    """A final result, or {'pending': Request, 'alias': ...} for the judge panel.

    all_to_judge (ablation): every fact goes to the judge panel with retrieved records; no code
    checks, no rule labels and no administration guard after the verdict.
    labels="verifact": VeriFact's three labels only. Statements this project would mark unverifiable
    go to the judge instead, and the guard applies VeriFact's definitions (a treatment the records
    mention but do not show given is not_supported).
    """
    if all_to_judge:
        result = _judge_request(atom, rows, triple, system, retriever)
        return {**result, "no_guard": True} if "pending" in result else result
    result = _verify_rules(atom, rows, triple, system, retriever)
    if labels == "verifact":
        if result.get("label") == UNVERIFIABLE:
            result = _judge_request(atom, rows, triple, system, retriever)
        if "pending" in result:
            result = {**result, "verifact_labels": True}
    return result


def _verify_rules(atom: dict, rows: list[dict], triple: dict, system: str, retriever: Retriever) -> dict:
    decision = records.ts(triple["decision_point"])
    concept, direction, time = atom["concept"], atom["direction"], atom.get("time", "current")
    measurable_dir = direction in {"high", "low", "abnormal", "normal"}
    measurable = concept in rules.CONCEPTS or concept in rules.COMPOSITES or concept in rules.SYNDROMES
    if _ALARM.search(atom["text"]):
        return _unverifiable("The source records alarm threshold settings, not alarm events.")
    if atom["fact_kind"] == "underspecified" or (direction == "changed" and measurable):
        return _unverifiable("Vague statement (no specific measure or direction of change).")
    if (atom.get("specimen") == "urine" or re.search(r"\burine\b", atom["text"], re.I)) and measurable:
        return _unverifiable("Urine results have no reference range in the record, so high/low cannot be judged.")
    if concept == "other" and _VAGUE.search(atom["text"]):
        return _unverifiable("Refers to unspecified 'symptoms' or 'signs'.")
    if _NECESSITY.search(atom["text"]):
        return _unverifiable("A statement of clinical necessity; structured records hold no such judgment.")
    if _HEDGE.search(atom["text"]):
        return _unverifiable("A hedged statement ('suspected', 'risk of', 'could indicate'), not a checkable fact.")
    if not _NEGATION.search(atom["text"]) and not _HISTORY.search(atom["text"]):
        leaf = concept in rules.CONCEPTS and rules.CONCEPTS[concept]["kind"] in {"lab", "vital"}
        if leaf and concept != "temperature" and not _DIRECTION_WORD.search(_BOUNDARY.sub(" ", atom["text"])):
            by_value = _stated_value_check(rows, concept, atom["text"], decision)
            if by_value:
                return {**by_value, "method": "deterministic"}
            if _BORDERLINE.search(atom["text"]):
                return _unverifiable("'Borderline' without a value names no direction to check.")
        if leaf and _BOUNDARY.search(atom["text"]):  # "low-normal" is still within the normal range
            direction, measurable_dir = "normal", True
        if concept in rules.SYNDROMES and direction in {"present", "absent"}:
            return {**_syndrome(rows, concept, direction, decision), "method": "deterministic"}
        if concept in rules.CONCEPTS and rules.CONCEPTS[concept]["kind"] in {"lab", "vital"} and measurable_dir:
            return {**_leaf(rows, concept, direction, time, decision), "method": "deterministic"}
        if concept in rules.COMPOSITES and measurable_dir:
            return {**_composite(rows, concept, direction, time, decision), "method": "deterministic"}
    if concept == "other" and _VENTILATION_CLAIM.search(atom["text"]) and not _NONINVASIVE.search(atom["text"]) \
            and not _NEGATION.search(atom["text"]):
        return {**_ventilation_status(rows, decision), "method": "deterministic"}
    if atom["fact_kind"] == "judgment":
        return _unverifiable("A clinical judgment (diagnosis, cause or necessity) with no directly comparable record.")
    return _judge_request(atom, rows, triple, system, retriever)
