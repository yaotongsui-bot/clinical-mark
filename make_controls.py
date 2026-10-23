"""Build known-answer inputs that test the evaluator without human labels.

Both are ordinary input files for run.py; each case carries a `control` block with what is expected.

  input/control_doctor_as_ai.json
      Positive control. Each case's AI answer is replaced by the clinicians' own treatment actions
      after the decision, one suggestion per treatment class the coverage analysis counts
      ("Administer Cefazolin.", "Continue Norepinephrine."). Every suggestion is true by
      construction: each one not matched is a false alarm, and vital recall should be 100%.

  input/control_error_injection.json
      Error injection. Suggestions that earlier runs judged correct are edited to carry one known
      error, and each edited suggestion is evaluated on its own as a separate case:
        direction  a supported abnormality is reversed ("hypokalemia" -> "hyperkalemia")
        drug       a matched treatment is replaced by a drug from a group never given in the admission
        stop       a matched "Continue X" becomes "Discontinue X"
        added      a treatment from a group never given is suggested ("Start norepinephrine.")

Usage
  python make_controls.py
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from cm import records, rules

ROOT = Path(__file__).resolve().parent
SOURCES = [("results_fixed", "mimic_triples_fixed.json"), ("results_open_s1", "mimic_triples_open_s1.json")]
CLEAN = {"supported", "match", "performed", "unverifiable", "not_addressed", "unobservable"}
# Reversing an abnormality: swap the prefix (hypokalemia -> hyperkalemia) or the whole word.
_PREFIX = re.compile(r"(hypo|hyper)(?=kal|natr|chlor|magnes|calc|phosph|glyc|tensi)|(tachy|brady)(?=cardi|pn)", re.I)
_OPPOSITE = {"hypo": "hyper", "hyper": "hypo", "tachy": "brady", "brady": "tachy",
             "leukocytosis": "leukopenia", "leukopenia": "leukocytosis",
             "thrombocytopenia": "thrombocytosis", "thrombocytosis": "thrombocytopenia",
             "elevated": "low", "high": "low", "increased": "decreased", "low": "elevated", "decreased": "increased"}
_LEVEL = {"high": re.compile(r"\b(elevated|high|increased)\b", re.I), "low": re.compile(r"\b(low|decreased)\b", re.I)}
DRUGS = ["norepinephrine", "vancomycin", "furosemide", "insulin", "amiodarone", "propofol", "heparin",
         "levetiracetam", "sodium bicarbonate", "magnesium sulfate", "calcium gluconate", "potassium chloride",
         "dexamethasone", "packed red blood cells"]
PER_TYPE = 60
PREFIX = {"direction": "R", "drug": "D", "stop": "S", "added": "A"}  # case-id suffix per error type


def _eligible(path: Path) -> list[dict]:
    triples = json.loads(path.read_text(encoding="utf-8"))["triples"]
    return [t for t in triples if t["evaluation_eligibility"]["decision_within_icu_stay"] is True]


def _shell(triple: dict, triple_id: str, claims: list[dict], control: dict) -> dict:
    keep = ("stay_id", "decision_point", "evaluation_eligibility", "clinician_actions")
    return {"triple_id": triple_id, **{k: triple[k] for k in keep},
            "ai_generated": {"claims": claims}, "control": control}


def doctor_as_ai(triples: list[dict]) -> list[dict]:
    out = []
    for t in triples:
        by_class: dict[str, list[dict]] = {}
        for action in sorted(records.postdecision_actions(t), key=lambda a: a["observed_at"]):
            if rules.importance(action["class"]) != "routine":
                by_class.setdefault(action["class"], []).append(action)
        claims = []
        for cls, rows in by_class.items():
            target = rows[0]["target"].strip()
            same = [r for r in rows if r["target"].strip() == target]
            verb = ("Continue" if all(r["spans_decision_point"] for r in same) else
                    "Perform" if all(r["action_type"] == "procedure_performed" for r in same) else "Administer")
            claims.append({"claim_id": f"{t['triple_id']}A{len(claims) + 1}", "text": f"{verb} {target}.",
                           "doctor_class": cls})
        if claims:
            out.append(_shell(t, t["triple_id"], claims, {"type": "doctor_as_ai"}))
    return out


def _replacement(used_groups: set[str], offset: int) -> str | None:
    for k in range(len(DRUGS)):
        drug = DRUGS[(offset + k) % len(DRUGS)]
        cls, _ = rules.classify_ai(drug, f"Start {drug}.")
        if cls and rules.importance(cls) != "routine" and rules.group_of(cls) not in used_groups:
            return drug
    return None


def _opposite(word: str) -> str:
    new = _OPPOSITE[word.lower()]
    return new[0].upper() + new[1:] if word[0].isupper() else new


def _reverse(text: str, fact: dict) -> str | None:
    """Reverse the abnormality behind a supported fact, in the sentence the fact came from."""
    for pattern, concept, direction in rules.DIAGNOSIS_TERMS:
        if (concept, direction) != (fact["concept"], fact["direction"]):
            continue
        for match in pattern.finditer(text):
            end = match.end() + re.match(r"[\w-]*", text[match.end():]).end()
            word = text[match.start():end]
            prefix = _PREFIX.match(word)
            if prefix:
                return text[:match.start()] + _opposite(prefix.group(0)) + text[match.start() + prefix.end():]
            if word.lower() in _OPPOSITE:
                return text[:match.start()] + _opposite(word) + text[end:]
    level = _LEVEL.get(fact["direction"])
    match = level.search(text) if level else None
    if match:
        return text[:match.start()] + _opposite(match.group(0)) + text[match.end():]
    return None


def _given_before(project: Path, mimic_root: Path) -> dict[str, set[str]]:
    """Treatment groups administered before the decision, per case: replacements avoid them so an
    injected 'Continue X' really is false."""
    triples = _eligible(project / "input" / SOURCES[0][1])
    out: dict[str, set[str]] = {}
    for case_id, rows in records.load_admission_rows(mimic_root, triples).items():
        # Medication and treatment rows carry the drug or item name, as the evaluator reads them.
        found = (rules.classify_target(r["label"] or r["text"]) for r in rows if r["semantics"] == "administration")
        out[case_id] = {rules.group_of(c) for c in found if c}
    return out


def error_injection(project: Path, mimic_root: Path) -> list[dict]:
    picked: dict[str, list[dict]] = {"direction": [], "drug": [], "stop": [], "added": []}
    given_before = _given_before(project, mimic_root)
    for run, input_name in SOURCES:
        triples = {t["triple_id"]: t for t in _eligible(project / "input" / input_name)}
        for index, path in enumerate(sorted((project / run / "cases").glob("*.json"))):
            case = json.loads(path.read_text(encoding="utf-8"))
            t = triples[case["case_id"]]
            used = {a["group"] for a in records.postdecision_actions(t)} | given_before.get(case["case_id"], set())
            texts = {a["claim_id"]: a["claim_text"] for a in case["atoms"]}
            for claim_id, text in texts.items():
                facts = [x for x in case["facts"] if x["claim_id"] == claim_id]
                actions = [x for x in case["actions"] if x["claim_id"] == claim_id]
                if any(x["label"] not in CLEAN for x in facts + actions) or any(x["conditional"] for x in actions):
                    continue
                source = {"source_run": run, "source_case": case["case_id"], "source_claim": claim_id, "original": text}
                for fact in facts:
                    if fact["label"] == "supported" and fact["method"] == "deterministic":
                        edited = _reverse(text, fact)
                        if edited and edited != text:
                            picked["direction"].append((t, {**source, "type": "direction", "edited": edited,
                                                            "expected": "fact not_supported"}))
                            break
                treated = [x for x in actions if x["track"] == "treatment" and x["label"] == "match"]
                for action in treated[:1]:
                    target = action["target"].strip()
                    where = re.search(re.escape(target), text, re.I) if target else None
                    drug = _replacement(used | {rules.group_of(action["treatment_class"])}, index)
                    if where and drug and action["action_class"] in {"start", "administer", "continue"}:
                        edited = text[:where.start()] + drug + text[where.end():]
                        picked["drug"].append((t, {**source, "type": "drug", "edited": edited, "inserted": drug,
                                                   "expected": "treatment not_done"}))
                    if action["action_class"] == "continue" and re.match(r"\s*continue\b", text, re.I):
                        edited = re.sub(r"^\s*continue\b", "Discontinue", text, count=1, flags=re.I)
                        picked["stop"].append((t, {**source, "type": "stop", "edited": edited,
                                                   "expected": "treatment partial_match"}))
            drug = _replacement(used, index)
            if drug and run == SOURCES[0][0]:  # one added treatment per case
                picked["added"].append((t, {"source_run": run, "source_case": case["case_id"], "source_claim": None,
                                            "original": None, "type": "added", "edited": f"Start {drug}.", "inserted": drug,
                                            "expected": "treatment not_done"}))
    out = []
    for kind, items in picked.items():
        # Spread over cases first: at most one item per case until every case had a turn.
        ordered, used_cases = [], set()
        for t, control in items:
            if control["source_case"] not in used_cases:
                used_cases.add(control["source_case"])
                ordered.append((t, control))
        ordered += [x for x in items if x not in ordered]
        for n, (t, control) in enumerate(ordered[:PER_TYPE], 1):
            triple_id = f"{t['triple_id']}-{PREFIX[kind]}{n:02d}"
            out.append(_shell(t, triple_id, [{"claim_id": f"{triple_id}A1", "text": control["edited"]}], control))
        print(f"{kind}: {len(items)} candidates, {min(len(ordered), PER_TYPE)} used")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=ROOT / "input")
    parser.add_argument("--mimic-root", type=Path, default=ROOT / "data" / "mimic-iv-demo")
    args = parser.parse_args()
    positive = doctor_as_ai(_eligible(ROOT / "input" / "mimic_triples_fixed.json"))
    (args.out_dir / "control_doctor_as_ai.json").write_text(
        json.dumps({"triples": positive}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"doctor_as_ai: {len(positive)} cases, {sum(len(t['ai_generated']['claims']) for t in positive)} suggestions, "
          f"{sum(c['text'].startswith('Continue') for t in positive for c in t['ai_generated']['claims'])} 'Continue'")
    injected = error_injection(ROOT, args.mimic_root.resolve())
    (args.out_dir / "control_error_injection.json").write_text(
        json.dumps({"triples": injected}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"error_injection: {len(injected)} cases")


if __name__ == "__main__":
    main()
