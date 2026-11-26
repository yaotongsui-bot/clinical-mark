"""Load the editable rule files and expose concept / treatment-class lookups."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEASURES = json.loads((ROOT / "rules" / "measures.json").read_text(encoding="utf-8"))
TREATMENTS = json.loads((ROOT / "rules" / "treatments.json").read_text(encoding="utf-8"))

CONCEPTS: dict[str, dict] = MEASURES["concepts"]
COMPOSITES: dict[str, dict] = {k: v for k, v in MEASURES["composites"].items() if not k.startswith("_")}
SYNDROMES: dict[str, dict] = {k: v for k, v in MEASURES["syndromes"].items() if not k.startswith("_")}
# Terms are word prefixes ('hypertensi'); the leading boundary keeps 'antihypertensive' from matching.
DIAGNOSIS_TERMS = [(re.compile(rf"\b(?:{p})", re.I), c, d) for p, c, d in MEASURES["diagnosis_terms"]["terms"]]
TEXT_ALIASES = [(re.compile(p, re.I), c) for p, c in MEASURES["text_aliases"]["terms"]]

CLASSES: list[dict] = TREATMENTS["classes"]
CLASS_BY_ID = {c["id"]: c for c in CLASSES}
GROUPS = {c["group"] for c in CLASSES}
AI_GROUPS = [(re.compile(p, re.I), g) for p, g in TREATMENTS["ai_groups"]["terms"]]
_CLASS_PATTERNS = [(c, [re.compile(p, re.I) for p in c["patterns"]]) for c in CLASSES]

ALL_CONCEPTS = sorted(set(CONCEPTS) | set(COMPOSITES) | set(SYNDROMES)) + ["other", "none"]


def concept_name(concept: str) -> str:
    for table in (CONCEPTS, COMPOSITES, SYNDROMES):
        if concept in table:
            return table[concept]["name"]
    return concept


def itemid_index() -> dict[tuple[str, str], str]:
    """(table, itemid) -> concept, for both pre- and post-decision rows."""
    index = {}
    for concept, spec in CONCEPTS.items():
        for table in ("lab", "chart", "output"):
            for itemid in spec.get(table, []):
                index[(table, str(itemid))] = concept
    return index


def leaf_members(concept: str) -> list[str]:
    if concept in COMPOSITES:
        out = []
        for member in COMPOSITES[concept]["members"]:
            out.extend(m for m in leaf_members(member) if m not in out)
        return out
    if concept in SYNDROMES:
        return [c for c, _ in SYNDROMES[concept]["all"]]
    return [concept] if concept in CONCEPTS else []


def same_finding(fact_concept: str, finding: str) -> bool:
    """Whether a fact about fact_concept speaks about the finding: the same measure, one of its
    components (SpO2 for oxygenation), or a narrow parent such as a syndrome (metabolic acidosis for
    low bicarbonate). Panels ('electrolytes', 'CBC') are too broad to name a finding."""
    if fact_concept == finding or fact_concept in leaf_members(finding):
        return True
    members = leaf_members(fact_concept)
    return len(members) <= 2 and any(m in members for m in leaf_members(finding) or [finding])


def diagnosis_override(text: str) -> tuple[str, str] | None:
    for pattern, concept, direction in DIAGNOSIS_TERMS:
        if pattern.search(text):
            return concept, direction
    return None


def alias_concept(text: str) -> str | None:
    for pattern, concept in TEXT_ALIASES:
        if pattern.search(text):
            return concept
    return None


def classify_target(target: str, text: str = "") -> str | None:
    """Return the first treatment class whose pattern matches the target."""
    target = (target or "").strip()
    for spec, patterns in _CLASS_PATTERNS:
        context = spec.get("context")
        if context and re.search(context["target"], target, re.I) and re.search(context["text"], text or ""):
            return spec["id"]
        if any(p.search(target) for p in patterns):
            return spec["id"]
    return None


def also_classes(name: str) -> set[str]:
    """Other classes a product also delivers, whatever class it is filed under."""
    return {cls for spec in CLASSES for pattern, cls in spec.get("also_counts_as", []) if re.search(pattern, name or "", re.I)}


def classify_doctor(row: dict) -> str:
    found = classify_target(str(row.get("target") or ""), str(row.get("text") or ""))
    if found:
        return found
    return "other_procedure" if row.get("action_type") == "procedure_performed" else "other_medication"


def classify_ai(target: str, text: str) -> tuple[str | None, str]:
    """Return (class or group id, 'class'|'group'|'none') for an AI treatment action.

    A group word ("transfusion", "ventilation") gives the group, unless the target also names exactly
    one class of that group ("red blood cell transfusion", "non-invasive ventilation").
    """
    for pattern, group in AI_GROUPS:
        word = pattern.search(target or "")
        if word:
            named = {spec["id"] for spec, patterns in _CLASS_PATTERNS if spec["group"] == group
                     and any(p.search(target) and not p.search(word.group(0)) for p in patterns)}
            return (named.pop(), "class") if len(named) == 1 else (group, "group")
    for source in (target, text):  # the whole sentence is context: "Heparin Sodium (Prophylaxis)"
        found = classify_target(source or "", text or "")
        if found and found != "routine":
            return found, "class"
    return None, "none"


def group_of(class_id: str) -> str:
    spec = CLASS_BY_ID.get(class_id)
    return spec["group"] if spec else class_id


def importance(class_id: str) -> str:
    """Static importance of a treatment class: vital / okay / routine."""
    spec = CLASS_BY_ID.get(class_id)
    return spec["importance"] if spec else "routine"


def indications(class_id: str) -> list[tuple[str, str, float | None]]:
    """(concept, direction, treatment threshold or None) for each indication of a class."""
    spec = CLASS_BY_ID.get(class_id)
    return [(x[0], x[1], x[2] if len(x) > 2 else None) for x in spec.get("indications", [])] if spec else []


_GENERIC = [re.compile(p, re.I) for p in TREATMENTS["generic_patterns"]]
PARTIAL_GROUPS = set(TREATMENTS["partial_within_groups"])


def named_drug(text: str, class_id: str) -> str | None:
    """The specific drug pattern an AI target names within an agent-specific class, if any."""
    spec = CLASS_BY_ID.get(class_id)
    if not spec or not spec.get("agent_specific"):
        return None
    for pattern in spec["patterns"]:
        if any(g.pattern == pattern for g in _GENERIC):
            continue
        if re.search(pattern, text or "", re.I):
            return pattern
    return None


def is_observable(class_or_group: str) -> bool:
    spec = CLASS_BY_ID.get(class_or_group)
    return not (spec and spec.get("observable") is False)


def class_name(class_id: str) -> str:
    """Display name of a treatment class, or of a group (its member classes joined)."""
    spec = CLASS_BY_ID.get(class_id)
    if spec:
        return spec["name"]
    members = [spec["name"] for spec in CLASSES if spec["group"] == class_id]
    if members:
        return " / ".join(members)
    return {"other_medication": "other medication", "other_procedure": "other procedure"}.get(class_id, class_id)
