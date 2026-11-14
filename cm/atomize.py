"""Stage 1: split the AI answer into fact / action / goal atoms (the AI side never sees records)."""

from __future__ import annotations

import json
import re

from . import rules

DIRECTIONS = ["high", "low", "abnormal", "normal", "present", "absent", "changed", "other", "none"]
ACTION_CLASSES = ["monitor", "assess", "start", "continue", "stop", "adjust", "administer",
                  "order_test", "procedure", "consult", "other", "none"]
SCHEMA = {
    "type": "object", "required": ["atoms"],
    "properties": {"atoms": {"type": "array", "items": {
        "type": "object",
        "required": ["claim_id", "kind", "fact_kind", "text", "concept", "direction", "time",
                     "specimen", "action_class", "target", "conditional"],
        "properties": {
            "claim_id": {"type": "string"},
            "kind": {"type": "string", "enum": ["fact", "action", "goal"]},
            "fact_kind": {"type": "string", "enum": ["observed", "presupposition", "judgment", "underspecified", "none"]},
            "text": {"type": "string"},
            "concept": {"type": "string", "enum": rules.ALL_CONCEPTS},
            "direction": {"type": "string", "enum": DIRECTIONS},
            "time": {"type": "string", "enum": ["current", "recent", "persistent", "unspecified", "none"]},
            "specimen": {"type": "string", "enum": ["blood", "urine", "other", "unspecified", "none"]},
            "action_class": {"type": "string", "enum": ACTION_CLASSES},
            "target": {"type": "string"},
            "conditional": {"type": "boolean"},
        }}}},
}
_HIGH = re.compile(r"\b(elevated|high|increased|raised|above)\b", re.I)
_LOW = re.compile(r"\b(low|decreased|reduced|below|depleted)\b", re.I)
_MONITORING = re.compile(r"^\s*(continue\s+)?(to\s+)?(close(ly)?\s+)?(monitor|track|trend)\w*\b"
                         r"|^\s*continue\s+[\w\s-]{0,30}?monitoring\b", re.I)
_STOPPING = re.compile(r"^\s*(discontinue|stop|hold|cease)\b", re.I)
_CONDITIONAL = re.compile(r"\b(if|as needed|consider|when indicated|if necessary|prn)\b", re.I)


# Within the clause before a diagnosis term, the LAST cue decides: a condition / purpose / example /
# negation / past cue ("as needed for", "to prevent", "signs of", "such as", "any", "no", "history of")
# means the term is not asserted as present; a premise cue ("causes of", "to address", "given",
# "due to") means it is taken as present.
_NOT_A_PREMISE = re.compile(
    r"\b(if|when|unless|as needed|prn|prevent\w*|avoid\w*|risk (of|for)|signs? of|symptoms? of|any|"
    r"(monitor\w*|watch|screen\w*|evaluat\w*|assess\w*|check\w*|look\w*|alarms?) for|rule out|possible|potential|"
    r"suspected|such as|including|eg|no|not|without|denies|history of|prior|previous\w*|resolved)\b", re.I)
_PREMISE = re.compile(
    r"\b(causes? of|etiology of|address\w*|treat\w*|correct\w*|manage\w*|given|due to|because of|"
    r"secondary to|in the setting of|ongoing|persistent|current)\b", re.I)
# A condition or a resolution right after the term: "manage hyperkalemia if present", "hypoglycemia,
# if confirmed", "hypokalemia has resolved".
_CONDITION_AFTER = re.compile(
    r"^[\s,(]*((if|when)\s+(present|any|applicable|confirmed|suspected|indicated|noted|found|"
    r"(it|they)\s+(is present|are present|occurs?|develops?|persists?|recurs?))|"
    r"((has|have|had|is|was)\s+)?(been\s+)?(resolved|resolving|improved|improving|corrected|normalized))\b", re.I)
# A term naming a monitor setting, not the patient's state: "desaturation limit of 88%",
# "hypotension alarm".
_SETTING_AFTER = re.compile(r"^\s+(limits?|alarms?|thresholds?|settings?|parameters?)\b", re.I)
# A premise worded as history, absence or resolution states what the claim says, not presence.
_FRAMED = re.compile(r"\b(history of|no|not|without|resolved)\b", re.I)


def _asserted(preceding: str, following: str = "") -> bool:
    if _CONDITION_AFTER.search(following) or _SETTING_AFTER.search(following):
        return False
    parts = re.split(r"[.;,]", preceding.replace("e.g.", "eg").replace("i.e.", "ie"))
    clause = parts.pop()
    # A list item belongs to the clause that opened the list:
    # "assess for signs of sepsis, including fever, leukocytosis, and hypotension".
    while parts and len(clause.split()) <= 3 and not _NOT_A_PREMISE.search(clause) \
            and not _PREMISE.search(clause):
        clause = parts.pop() + "," + clause
    last_not = max((m.end() for m in _NOT_A_PREMISE.finditer(clause)), default=-1)
    last_yes = max((m.end() for m in _PREMISE.finditer(clause)), default=-1)
    return last_not < 0 or last_yes > last_not


def _term_span(text: str, match: re.Match) -> tuple[int, int]:
    """The whole word a diagnosis-term prefix starts ('hypokal' -> 'hypokalemia')."""
    return match.start(), re.match(r"[\w-]*", text[match.end():]).end() + match.end()
_TREATMENT_OR_ALARM = re.compile(r"\b(alarms?|settings?|limits?)\b", re.I)
_TREATMENT_WORDS = re.compile(r"\b(administ\w*|given|giving|receiv\w*|infus\w*|therapy|treatment|ventilat\w*|"
                              r"intubat\w*|order\w*|dose|drip|on [a-z]+ (?:therapy|support))\b", re.I)


def fact_concept(text: str, direction: str) -> tuple[str, str]:
    """Concept of a fact from the rule files only; the model's concept field is not trusted.

    Facts about treatments, alarms or monitor settings become 'other' so the judge model reads the records.
    """
    if any(_SETTING_AFTER.search(text[_term_span(text, m)[1]:]) for p, _, _ in rules.DIAGNOSIS_TERMS
           for m in p.finditer(text)):
        return "other", direction
    override = rules.diagnosis_override(text)
    if override:
        return override
    if _TREATMENT_OR_ALARM.search(text) or (
            _TREATMENT_WORDS.search(text) and rules.classify_ai(text, text)[0] not in (None, "routine")):
        return "other", direction
    concept = rules.alias_concept(text) or "other"
    if direction in {"other", "none", "present"} and concept in rules.CONCEPTS:
        direction = "high" if _HIGH.search(text) else "low" if _LOW.search(text) else direction
    return concept, direction


def presupposition_safety_net(atoms: list[dict], claims: list[dict]) -> list[dict]:
    """Add premise facts the atomizer missed, e.g. 'to address hyponatremia and hypokalemia'."""
    added = []
    for claim in claims:
        have = {(a["concept"], a.get("direction")) for a in atoms + added
                if a["claim_id"] == claim["claim_id"] and a["kind"] == "fact"}
        taken: list[tuple[int, int]] = []
        for pattern, concept, direction in rules.DIAGNOSIS_TERMS:
            for match in pattern.finditer(claim["text"]):
                start, end = _term_span(claim["text"], match)
                if any(s <= start < e for s, e in taken):
                    continue
                taken.append((start, end))
                if not _asserted(claim["text"][:start], claim["text"][end:]) or (concept, direction) in have:
                    continue
                word = claim["text"][start:end]
                added.append({"atom_id": f"{claim['claim_id']}::R{len(added) + 1:02d}",
                              "claim_id": claim["claim_id"], "claim_text": claim["text"], "kind": "fact",
                              "text": f"{word[0].upper() + word[1:]} is present.", "concept": concept,
                              "fact_kind": "presupposition", "direction": direction, "time": "current",
                              "specimen": "blood", "notes": ["premise added from the diagnosis-term table (missed by the atomizer)"]})
                have.add((concept, direction))
    return atoms + added


def continue_presuppositions(atoms: list[dict]) -> list[dict]:
    """'Continue X' takes for granted that X is already running; add that fact if it is missing."""
    added = []
    for atom in atoms:
        if atom["kind"] != "action" or atom.get("action_class") != "continue" or not atom.get("treatment_class"):
            continue
        group = rules.group_of(atom["treatment_class"])
        same_claim = [a for a in atoms + added if a["claim_id"] == atom["claim_id"] and a["kind"] == "fact"]
        if any(rules.group_of(rules.classify_ai(a["text"], a["text"])[0] or "") == group for a in same_claim):
            continue
        if group == "ventilation":
            text = ("The patient is currently on non-invasive ventilation (BiPAP/CPAP)."
                    if re.search(r"non-?invasive|bipap|cpap", f"{atom['target']} {atom['text']}", re.I)
                    else "The patient is currently on mechanical ventilation.")
        else:
            text = f"The patient is currently receiving {atom['target']}."
        added.append({"atom_id": f"{atom['claim_id']}::P{len(added) + 1:02d}", "claim_id": atom["claim_id"],
                      "claim_text": atom["claim_text"], "kind": "fact", "text": text, "concept": "other",
                      "fact_kind": "presupposition", "direction": "present", "time": "current",
                      "specimen": "none", "notes": ["premise implied by a 'continue X' action"]})
    return atoms + added


def drop_unasserted_premises(atoms: list[dict], claims: list[dict]) -> list[dict]:
    """Apply the safety net's premise test to the atomizer's own premises.

    The atomizer sometimes turns a watch-for or a condition into a premise ('assess and manage
    hyperkalemia if present' -> 'Hyperkalemia is present.'). A premise is kept only if the claim
    asserts its diagnosis term at least once; premises without a diagnosis term, and premises that
    keep the claim's own framing ('The patient has a history of hypertension.'), are kept as they are.
    """
    text_of = {c["claim_id"]: c["text"] for c in claims}
    kept = []
    for atom in atoms:
        if atom["kind"] == "fact" and atom.get("fact_kind") == "presupposition" and not _FRAMED.search(atom["text"]):
            text = text_of.get(atom["claim_id"], "")
            spans = [_term_span(text, m) for p, c, d in rules.DIAGNOSIS_TERMS
                     if (c, d) == (atom["concept"], atom.get("direction")) for m in p.finditer(text)]
            if spans and not any(_asserted(text[:s], text[e:]) for s, e in spans):
                continue
        kept.append(atom)
    return kept


def refresh_concepts(atoms: list[dict]) -> list[dict]:
    """Re-apply the rule-file concept mapping to saved atoms, so a rule change reaches atoms split
    in an earlier run without splitting the answer again (the mapping is idempotent)."""
    out = []
    for atom in atoms:
        if atom["kind"] == "fact":
            concept, direction = fact_concept(atom["text"], atom.get("direction", "none"))
            if (concept, direction) != (atom["concept"], atom.get("direction")):
                atom = {**atom, "concept": concept, "direction": direction,
                        "notes": atom.get("notes", []) + [f"concept updated by the rule files: {atom['concept']} -> {concept}"]}
        out.append(atom)
    return out


def safety_nets(atoms: list[dict], claims: list[dict]) -> list[dict]:
    """Idempotent rule-based corrections applied after the model's atomization."""
    atoms = refresh_concepts(atoms)
    return continue_presuppositions(presupposition_safety_net(drop_unasserted_premises(atoms, claims), claims))


def user_prompt(triple: dict) -> tuple[str, list[dict]]:
    claims = [{"claim_id": c["claim_id"], "text": c["text"]} for c in triple["ai_generated"]["claims"]]
    return "AI answer claims:\n" + json.dumps(claims, ensure_ascii=False, indent=1), claims


def validate(response: dict, claims: list[dict], allow_missing: bool = False) -> list[dict]:
    by_id = {c["claim_id"]: c for c in claims}
    atoms = response.get("atoms")
    if not isinstance(atoms, list) or not atoms:
        raise ValueError("atoms must be a non-empty array")
    seen = set()
    for atom in atoms:
        if atom.get("claim_id") not in by_id:
            raise ValueError(f"unknown claim_id {atom.get('claim_id')!r}; copy claim_id exactly")
        if not str(atom.get("text") or "").strip():
            raise ValueError("every atom needs non-empty text")
        seen.add(atom["claim_id"])
    missing = set(by_id) - seen
    if missing and not allow_missing:
        raise ValueError(f"claims without atoms: {sorted(missing)}; every claim needs at least one atom")
    return atoms


def normalize(atoms: list[dict], claims: list[dict]) -> list[dict]:
    """Attach ids and apply the deterministic rule-file mappings on top of the model's fields."""
    by_id = {c["claim_id"]: c for c in claims}
    out = []
    for index, atom in enumerate(atoms, 1):
        text = atom["text"].strip()
        item = {"atom_id": f"{atom['claim_id']}::{index:02d}", "claim_id": atom["claim_id"],
                "claim_text": by_id[atom["claim_id"]]["text"], "kind": atom["kind"], "text": text,
                "concept": atom["concept"], "notes": []}
        if atom["kind"] == "fact":
            item.update(fact_kind=atom["fact_kind"] if atom["fact_kind"] != "none" else "observed",
                        direction=atom["direction"], time=atom["time"], specimen=atom["specimen"])
            concept, direction = fact_concept(text, item["direction"])
            if concept != item["concept"]:
                item["notes"].append(f"concept set by the rule files: {item['concept']} -> {concept}")
            item["concept"], item["direction"] = concept, direction
        elif atom["kind"] == "action":
            action_class = atom["action_class"] if atom["action_class"] != "none" else "other"
            target = atom["target"].strip()
            if action_class != "monitor" and _MONITORING.search(text):
                item["notes"].append(f"action class corrected by rule: {action_class} -> monitor")
                action_class = "monitor"
            elif action_class != "stop" and _STOPPING.search(text):
                item["notes"].append(f"action class corrected by rule: {action_class} -> stop")
                action_class = "stop"
            item.update(action_class=action_class, target=target,
                        conditional=bool(atom["conditional"] or _CONDITIONAL.search(text)))
            if action_class in {"monitor", "assess", "order_test"}:
                # The model's concept field is unreliable; only the rule file decides.
                item["concept"] = rules.alias_concept(f"{target} {text}") or "other"
            if action_class not in {"monitor", "assess"}:
                cls, level = rules.classify_ai(target, text)
                item.update(treatment_class=cls, class_level=level)
        out.append(item)
    return out


def _fallback(claim: dict) -> dict:
    """Keep a claim the model never split as one whole-sentence action atom."""
    return {"claim_id": claim["claim_id"], "kind": "action", "fact_kind": "none", "text": claim["text"],
            "concept": "other", "direction": "none", "time": "none", "specimen": "none",
            "action_class": "other", "target": "", "conditional": False}


def atomize(triple: dict, llm, model: str, system: str, claims: list[dict] | None = None) -> list[dict]:
    """Split the whole answer; claims the model keeps dropping are retried one at a time."""
    if claims is None:
        user, claims = user_prompt(triple)
    else:
        user = "AI answer claims:\n" + json.dumps(claims, ensure_ascii=False, indent=1)
    for attempt in range(3):
        try:
            response = llm.json(model, system, user, SCHEMA, num_predict=4096,
                                stage="ai_atomization", case_id=triple["triple_id"])
        except ValueError:
            # Unparseable output (a long answer runs past the token budget) repeats on a seeded retry.
            break
        try:
            raw = validate(response, claims, allow_missing=attempt == 2)
        except ValueError as exc:
            user += f"\nYour previous output was invalid: {exc}. Return corrected JSON."
            continue
        atoms = normalize(raw, claims)
        done = {a["claim_id"] for a in raw}
        for claim in claims:
            if claim["claim_id"] not in done:
                atoms += atomize(triple, llm, model, system, [claim])
        return atoms
    if len(claims) > 1:
        return [a for claim in claims for a in atomize(triple, llm, model, system, [claim])]
    atoms = normalize([_fallback(claims[0])], claims)
    atoms[0]["notes"].append("atomizer failed repeatedly; the whole sentence was kept as one atom")
    return atoms
