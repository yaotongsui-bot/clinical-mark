"""Stage 2b: compare AI actions with what clinicians recorded after the decision (the gold standard).

Monitoring/assessment actions are checked against post-decision measurements by code.
Treatment actions are matched by code: the rule file gives the treatment group, then target
(same class, or the specific drug the AI named) and direction (continue / stop / adjust) are
checked against the recorded rows. Only AI actions the rule file cannot classify go to the
judge panel.

Treatment labels: match, partial_match (same goal, different agent or direction), not_done,
condition_not_met (a conditional suggestion with no matching action), vague_target, unobservable.
Monitoring labels: performed, not_performed, unobservable.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict

from . import rules
from .ground import indication_present
from .panel import Request
from .retrieve import bm25

MATCH, PARTIAL, NOT_DONE = "match", "partial_match", "not_done"
CONDITION_NOT_MET, VAGUE, UNOBSERVABLE = "condition_not_met", "vague_target", "unobservable"
PERFORMED, NOT_PERFORMED = "performed", "not_performed"
ACTION_SCHEMA = {"type": "object", "required": ["label", "match", "reason"],
                 "properties": {"label": {"type": "string", "enum": [MATCH, PARTIAL, NOT_DONE]},
                                "match": {"type": ["string", "null"]},
                                "reason": {"type": "string", "maxLength": 400}}}
_UNOBSERVABLE_ASSESS = re.compile(
    r"\b(causes?|etiolog\w*|reasons?|signs? of|symptoms? of|underlying|for (infection|bleeding|sepsis))\b", re.I)


def check_monitoring(atom: dict, observations: list[dict], window_hours: float) -> dict:
    concept = atom["concept"]
    if _UNOBSERVABLE_ASSESS.search(atom["text"]):
        return {"label": UNOBSERVABLE, "evidence": [],
                "reason": "Assessing causes or signs is clinical reasoning that structured records cannot show."}
    members = rules.leaf_members(concept)
    if not members:
        return {"label": UNOBSERVABLE, "evidence": [],
                "reason": "No structured record item corresponds to this monitoring/assessment target."}
    by_concept = defaultdict(list)
    for obs in observations:
        by_concept[obs["concept"]].append(obs)
    measured = {m: by_concept[m] for m in members if by_concept[m]}
    name = rules.concept_name(concept)
    window = f"the {window_hours:.1f} h observation window after the decision (24 h or until ICU discharge)"
    if not measured:
        return {"label": NOT_PERFORMED, "evidence": [], "reason": f"No {name} measurement in {window}."}
    detail = ", ".join(f"{rules.concept_name(m)} x{len(v)}" for m, v in measured.items())
    evidence = [{"rid": o["record_id"], "time": o["observed_at"], "item": rules.concept_name(m),
                 "value": f"{o['value']} {o['unit']}".strip()} for m, v in measured.items() for o in v[:2]]
    return {"label": PERFORMED, "evidence": evidence, "reason": f"Measured in {window}: {detail}."}


def _candidates(atom: dict, doctor_actions: list[dict]) -> list[dict]:
    cls, level = atom.get("treatment_class"), atom.get("class_level")
    if cls:
        group = cls if level == "group" else rules.group_of(cls)
        return [a for a in doctor_actions if a["group"] == group]
    pool = [a for a in doctor_actions if a["class"] not in {"routine", "lines_devices"}]
    scores = bm25(f"{atom['target']} {atom['text']}", [f"{a['target']} {a['text']}" for a in pool])
    ranked = sorted(range(len(pool)), key=lambda i: -scores[i])
    return [pool[i] for i in ranked if scores[i] > 0][:15]


def _dedupe(rows: list[dict], limit: int = 20) -> list[dict]:
    """One row per (target, action type, already-running) with an occurrence count."""
    seen: dict[tuple, dict] = {}
    for row in sorted(rows, key=lambda r: r["observed_at"]):
        key = (row["target"].casefold(), row["action_type"], row["spans_decision_point"])
        if key in seen:
            seen[key]["occurrences"] += 1
        else:
            seen[key] = {**row, "occurrences": 1}
    return list(seen.values())[:limit]


def _ventilator_charting(atom: dict, observations: list[dict]) -> dict | None:
    """Ventilation is often absent from the action tables but visible in charted vent settings.

    "Continue ventilation" is confirmed by any post-decision ventilator charting; "adjust the
    settings" requires one charted setting to take at least two different values.
    """
    if rules.group_of(atom.get("treatment_class") or "") != "ventilation" or atom["action_class"] not in {"continue", "adjust"}:
        return None
    rows = [o for o in observations if o["concept"] == "ventilator"]
    if not rows:
        return None
    if atom["action_class"] == "adjust":
        by_item = defaultdict(set)
        for o in rows:
            by_item[o["itemid"]].add(o["value"])
        changed = [i for i, values in by_item.items() if len(values) > 1]
        if not changed:
            return None
        rows = [o for o in rows if o["itemid"] in changed]
        reason = f"Ventilator settings changed after the decision ({len(changed)} settings took different values)."
    else:
        reason = f"Ventilator settings were still charted after the decision ({len(rows)} records), so ventilation continued."
    return {"label": MATCH, "method": "rule", "reason": reason,
            "evidence": [{"rid": o["record_id"], "time": o["observed_at"], "item": "ventilator setting",
                          "value": f"{o['value']} {o['unit']}".strip(), "class": "ventilation_invasive"}
                         for o in rows[:3]]}


_RATE = re.compile(r"\bat\s+([\d.]+)\s*([a-z%]+(?:/[a-z]+)*)", re.I)


def _cite_rows(rows: list[dict], limit: int = 2) -> list[dict]:
    return [{"rid": r["aid"], "time": r["observed_at"], "item": r["text"].strip(), "class": r["class"]}
            for r in sorted(rows, key=lambda r: r["observed_at"])[:limit]]


_UP = re.compile(r"\b(increas\w*|up-?titrat\w*|titrate up|escalat\w*|rais\w*)\b", re.I)
_DOWN = re.compile(r"\b(decreas\w*|reduc\w*|wean\w*|taper\w*|lower\w*|down-?titrat\w*|titrate down)\b", re.I)


def _rate_moves(rows: list[dict]) -> dict[str, set[str]]:
    """Per target, the directions ('up', 'down') in which the recorded infusion rate moved after T."""
    rates = defaultdict(list)
    for r in sorted(rows, key=lambda r: r["observed_at"]):
        m = _RATE.search(r["text"])
        if m:
            rates[r["target"].casefold()].append(round(float(m.group(1)), 3))
    moves = {t: {"up" if b > a else "down" for a, b in zip(v, v[1:]) if b != a} for t, v in rates.items()}
    return {t: m for t, m in moves.items() if m}


def _decide(atom: dict, rows: list[dict], observations: list[dict]) -> dict:
    """Target and direction decided by code from the same-group recorded actions."""
    cls, level, action = atom["treatment_class"], atom["class_level"], atom["action_class"]
    name = rules.class_name(cls)
    pool = rows if level == "group" else [r for r in rows if r["class"] == cls]
    if rules.group_of(cls) == "ventilation" and not re.search(r"extubat|wean", atom["text"], re.I):
        extubated = [r for r in rows if r["class"] == "extubation"]
        pool = [r for r in pool if r["class"] != "extubation"]
        if extubated and not pool:
            return {"label": PARTIAL, "evidence": _cite_rows(extubated), "method": "rule",
                    "reason": "The AI suggested continuing or adjusting ventilation; the clinicians extubated after the decision."}
    drug = rules.named_drug(f"{atom['target']} {atom['text']}", cls) if level == "class" else None
    if drug and not pool:  # "heparin" suggested and prophylactic heparin given: the named drug was used
        pool = [r for r in rows if re.search(drug, f"{r['target']} {r['text']}", re.I)]
    if not pool:
        others = ", ".join(sorted({rules.class_name(r["class"]) for r in rows}))
        if rules.group_of(cls) in rules.PARTIAL_GROUPS:
            return {"label": PARTIAL, "evidence": _cite_rows(rows), "method": "rule",
                    "reason": f"The clinicians used {others} for the same goal, not the suggested {name}."}
        return {"label": CONDITION_NOT_MET if atom["conditional"] else NOT_DONE, "evidence": [], "method": "rule",
                "reason": f"The clinicians recorded {others}, but not the suggested {name}."}
    if drug:
        same = [r for r in pool if re.search(drug, f"{r['target']} {r['text']}", re.I)]
        if not same:
            used = ", ".join(sorted({r["target"].strip() for r in pool})[:4])
            return {"label": PARTIAL, "evidence": _cite_rows(pool), "method": "rule",
                    "reason": f"The drug the AI named ({drug}) was not used; the clinicians used {used} from the same class."}
        pool = same
    if action == "stop":
        return {"label": PARTIAL, "evidence": _cite_rows(pool), "method": "rule",
                "reason": f"The AI suggested stopping, but {name} is still recorded after the decision."}
    if action == "adjust":
        if rules.group_of(cls) == "ventilation":
            charted = _ventilator_charting(atom, observations)
            if charted:
                return charted
        else:
            moves = _rate_moves(pool)
            wanted = "up" if _UP.search(atom["text"]) else "down" if _DOWN.search(atom["text"]) else None
            changed = [t for t, m in moves.items() if wanted is None or wanted in m]
            if changed:
                return {"label": MATCH, "method": "rule",
                        "evidence": _cite_rows([r for r in pool if r["target"].casefold() in changed]),
                        "reason": f"The {name} infusion rate changed after the decision ({', '.join(changed)})."}
            if moves:  # "increase norepinephrine" while the rate only went down
                return {"label": PARTIAL, "evidence": _cite_rows(pool), "method": "rule",
                        "reason": f"The {name} infusion rate moved {'down' if wanted == 'up' else 'up'} after the "
                                  f"decision, not {wanted} as suggested."}
        if atom["conditional"]:  # "adjust if needed": whether the condition arose is unknown
            return {"label": CONDITION_NOT_MET, "evidence": _cite_rows(pool), "method": "rule",
                    "reason": f"{name} continued after the decision without a recorded dose or setting change; "
                              f"the suggestion was conditional."}
        return {"label": PARTIAL, "evidence": _cite_rows(pool), "method": "rule",
                "reason": f"{name} continued after the decision, but no dose or setting change is recorded."}
    note = " (already running before the decision and continued)" if all(r["spans_decision_point"] for r in pool) else ""
    condition = " The suggestion was conditional; the record does not show whether the condition was met." \
        if atom["conditional"] else ""
    return {"label": MATCH, "evidence": _cite_rows(pool), "method": "rule",
            "reason": f"Clinicians recorded {name} after the decision{note}.{condition}"}


def check_treatment(atom: dict, doctor_actions: list[dict], observations: list[dict], system: str,
                    case_id: str, window_hours: float) -> dict:
    """A final result, or {'pending': Request, ...} when only the judge panel can match the target."""
    cls = atom.get("treatment_class")
    if cls and not rules.is_observable(cls):
        return {"label": UNOBSERVABLE, "evidence": [], "method": "rule",
                "reason": f"{rules.class_name(cls)} is not captured by the source action tables."}
    rows = _candidates(atom, doctor_actions)
    if cls:
        if not rows:
            charted = _ventilator_charting(atom, observations)
            if charted:
                return charted
            if atom["action_class"] == "stop":
                return {"label": MATCH, "evidence": [], "method": "rule",
                        "reason": f"No {rules.class_name(cls)} recorded after the decision, consistent with stopping it."}
            if atom["action_class"] == "adjust" and rules.group_of(cls) == "ventilation" and \
                    any(o["concept"] == "ventilator" for o in observations):
                return {"label": CONDITION_NOT_MET if atom["conditional"] else NOT_DONE, "evidence": [],
                        "method": "rule", "reason": "Ventilator settings were charted after the decision but did not change."}
            return {"label": CONDITION_NOT_MET if atom["conditional"] else NOT_DONE, "evidence": [], "method": "rule",
                    "reason": f"No {rules.class_name(cls)} action recorded in the {window_hours:.1f} h observation "
                              f"window after the decision."}
        return _decide(atom, rows, observations)
    vague = {"label": VAGUE, "evidence": [], "method": "rule",
             "reason": "The suggestion names no specific drug or treatment that the rule file can classify, "
                       "and no corresponding clinician action was found."}
    candidates = _dedupe(rows)
    if not candidates:
        return vague
    alias = {f"R{i}": row for i, row in enumerate(candidates, 1)}
    packet = {"ai_action": {"text": atom["text"], "original_sentence": atom["claim_text"],
                            "action_class": atom["action_class"], "target": atom["target"],
                            "conditional": atom["conditional"]},
              "recorded_actions": [{"id": k, "time": r["observed_at"], "action_type": r["action_type"],
                                    "target": r["target"], "text": r["text"].strip(),
                                    "occurrences": r["occurrences"],
                                    "spans_decision_point": r["spans_decision_point"]}
                                   for k, r in alias.items()]}
    request = Request(key=f"action:{atom['atom_id']}", stage="action_judge", case_id=case_id, system=system,
                      user=json.dumps(packet, ensure_ascii=False), schema=ACTION_SCHEMA, cite_key="match",
                      needs_cite={MATCH, PARTIAL}, allowed=set(alias), fallback=NOT_DONE)
    return {"pending": request, "alias": alias, "vague": vague}


def finalize_treatment(pending: dict, verdict: dict) -> dict:
    panel = {"agreement": verdict["agreement"], "votes": verdict["votes"]}
    if verdict["label"] == NOT_DONE:
        return {**pending["vague"], "method": "llm_panel", "panel": panel}
    alias = pending["alias"]
    return {"label": verdict["label"], "reason": verdict["reason"], "method": "llm_panel", "panel": panel,
            "evidence": [{"rid": alias[c]["aid"], "time": alias[c]["observed_at"],
                          "item": alias[c]["text"].strip(), "class": alias[c]["class"]}
                         for c in verdict["cites"][:1]]}


def gold_classes(doctor_actions: list[dict], pre_rows: list[dict], decision) -> list[dict]:
    """Treatment classes the clinicians used after T, each graded vital / okay.

    A class is vital when the rule file marks it vital, or when one of its indications was
    present at T (a problem-linked action, e.g. potassium 3.0 followed by potassium chloride).
    """
    by_class = defaultdict(list)
    for action in doctor_actions:
        if rules.importance(action["class"]) != "routine":
            by_class[action["class"]].append(action)
    out = []
    for cls, rows in by_class.items():
        linked = []
        for concept, direction, threshold in rules.indications(cls):
            present, reason = indication_present(pre_rows, concept, direction, decision, threshold)
            if present:
                linked.append(reason)
        static = rules.importance(cls)
        out.append({"class": cls, "name": rules.class_name(cls),
                    "importance": "vital" if static == "vital" or linked else "okay",
                    "problem_linked": bool(linked), "indication": " ".join(linked),
                    "doctor_targets": sorted({r["target"].strip() for r in rows})[:6], "doctor_rows": len(rows)})
    return out


def _claim_index(claim_id: str) -> int:
    match = re.search(r"A(\d+)$", claim_id)
    return int(match.group(1)) if match else 0


def coverage(gold: list[dict], atoms: list[dict], results: dict[str, dict],
             max_claims: int | None = None) -> list[dict]:
    """Mark each gold class covered when an AI action (from the first max_claims claims) addresses it."""
    out = []
    for entry in gold:
        cls = entry["class"]
        by = []
        for atom in atoms:
            # Suggesting to stop a treatment does not cover a treatment the clinicians gave.
            if atom["kind"] != "action" or not atom.get("treatment_class") or atom["action_class"] == "stop":
                continue
            if max_claims is not None and _claim_index(atom["claim_id"]) > max_claims:
                continue
            hit = (atom["treatment_class"] == cls if atom["class_level"] == "class"
                   else atom["treatment_class"] == rules.group_of(cls))
            cited = any(e.get("class") == cls for e in results.get(atom["atom_id"], {}).get("evidence", []))
            if hit or cited:
                by.append(atom["atom_id"])
        out.append({**entry, "covered": bool(by), "by_atoms": by})
    return sorted(out, key=lambda r: (r["importance"] != "vital", r["covered"], r["class"]))
