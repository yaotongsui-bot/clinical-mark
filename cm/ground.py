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
    indicators = []
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
    if not indicators:
        return {"label": NOT_ADDRESSED, "evidence": [],
                "reason": "No ventilator or intubation record before the decision time."}
    when, positive, row = max(indicators, key=lambda x: x[0])
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
    (r"oxygen|o2", "O2 Flow O2 saturation Inspired O2 Fraction"),
    (r"epithelial|urine|cast|bacteria", "Urine Epithelial Cells Bacteria"),
]


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
            "delivered": _delivered(atom["text"], rows, records.ts(triple["decision_point"]))}


_ADMINISTRATION_CLAIM = re.compile(r"\b(receiv\w*|given|administ\w*|infus\w*|currently on)\b", re.I)
_NOT_GIVEN = re.compile(r"not given|held|stopped|discontinu", re.I)
# Charted items show delivery only for devices; others that name a treatment are assessments
# ("Braden Nutrition", "Richmond-RAS Scale"), and laboratory rows are tests ("Methadone, Urine").
_DEVICE_CHARTING = re.compile(r"(pca\b|bipap|cpap|ventilator|o2 delivery device|peep|tidal volume|inspired o2)", re.I)


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
    if drug:
        return bool(re.search(drug, name, re.I))
    found = rules.classify_target(name)
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


def _administration_guard(statement: str, label: str, cited: list[dict], delivered: bool | None) -> str | None:
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
    if label == NOT_SUPPORTED and not any((_NOT_GIVEN.search(r["text"]) or r["semantics"] == "mar_other")
                                          and _about(r, treatment) for r in cited):
        return "No cited record shows this treatment was withheld or stopped; absence of a record is not_addressed."
    return None


def finalize(pending: dict, verdict: dict) -> dict:
    alias = pending["alias"]
    cited = [alias[c] for c in verdict["cites"]]
    label, reason = verdict["label"], verdict["reason"]
    downgrade = _administration_guard(pending.get("statement", ""), label, cited, pending.get("delivered"))
    if downgrade:
        label, reason = NOT_ADDRESSED, f"{downgrade} (Panel verdict: {verdict['label']}.)"
    return {"label": label, "reason": reason, "method": "llm_panel",
            "panel": {"agreement": verdict["agreement"], "votes": verdict["votes"],
                      **({"panel_label": verdict["label"]} if downgrade else {})},
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


def verify(atom: dict, rows: list[dict], triple: dict, system: str, retriever: Retriever) -> dict:
    """A final result, or {'pending': Request, 'alias': ...} for the judge panel."""
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
