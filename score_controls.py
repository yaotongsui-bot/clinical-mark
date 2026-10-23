"""Score the known-answer tests built by make_controls.py.

  doctor-as-AI     every suggestion is true: a non-match is a false alarm; vital recall should be 100%
  error injection  every edited suggestion carries one known error: detected / missed / not scored

Usage
  python score_controls.py [--out validation/known_answer_tests.md]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTROLS = ROOT / "validation" / "controls"
DISAGREE = {"not_done", "partial_match"}


def _cases(kind: str) -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((CONTROLS / kind / "cases").glob("*.json"))}


def _inputs(kind: str) -> list[dict]:
    return json.loads((ROOT / "input" / f"control_{kind}.json").read_text(encoding="utf-8"))["triples"]


def _pct(n: int, d: int) -> str:
    return f"{n / d * 100:.1f}% ({n}/{d})" if d else "-"


def _cell(text) -> str:
    return str(text).replace("|", "/").replace("\n", " ")


def doctor_as_ai(lines: list[str]) -> dict:
    cases = _cases("doctor_as_ai")
    doctor_class = {c["claim_id"]: c["doctor_class"] for t in _inputs("doctor_as_ai") for c in t["ai_generated"]["claims"]}
    treatment, monitoring, facts, failures, dropped = Counter(), Counter(), Counter(), [], []
    for case_id, case in cases.items():
        seen = {a["claim_id"] for a in case["actions"] if a["track"] == "treatment"}
        for claim_id, cls in doctor_class.items():
            if claim_id.startswith(f"{case_id}A") and claim_id not in seen:
                dropped.append((case_id, claim_id, cls))
        for a in case["actions"]:
            if a["track"] == "monitoring":
                monitoring[a["label"]] += 1
                continue
            treatment[a["label"]] += 1
            if a["label"] != "match":
                failures.append((case_id, a["claim_text"], doctor_class.get(a["claim_id"]), a.get("treatment_class"),
                                 a["label"], a["reason"]))
        for f in case["facts"]:
            facts[f["label"]] += 1
    summary = json.loads((CONTROLS / "doctor_as_ai" / "summary.json").read_text(encoding="utf-8"))
    cov = summary["coverage"]
    scored = treatment["match"] + treatment["partial_match"] + treatment["not_done"]
    n_treat = sum(treatment.values())
    lines += [
        "## Doctor as AI (every suggestion is true)", "",
        f"{len(cases)} cases; each suggestion is a treatment the clinicians gave after the decision.", "",
        "| Measure | Expected | Result |", "|---|---|---|",
        f"| Treatment agreement (strict) | 100% | {_pct(treatment['match'], scored)} |",
        f"| Suggestions matched, of all treatment suggestions | 100% | {_pct(treatment['match'], n_treat)} |",
        f"| Vital recall | 100% | {cov['vital']['micro'] * 100:.1f}% ({cov['vital']['covered']}/{cov['vital']['total']}) |",
        f"| All recall | 100% | {cov['all']['micro'] * 100:.1f}% ({cov['all']['covered']}/{cov['all']['total']}) |",
        f"| 'Currently receiving X' premises supported | 100% | {_pct(facts['supported'], sum(facts.values()))} |", "",
        f"- Treatment labels: {dict(treatment)}",
        f"- Routed to the monitoring track: {dict(monitoring) or 'none'}",
        f"- Premise labels (from 'Continue X'): {dict(facts) or 'none'}",
        f"- Suggestions without a treatment atom: {len(dropped)}", "",
        "### Suggestions not matched", "",
        "| Case | Suggestion | Clinician class | AI-side class | Label | Reason |", "|---|---|---|---|---|---|"]
    lines += [f"| {c} | {_cell(t)} | {d} | {a} | {lab} | {_cell(r)} |" for c, t, d, a, lab, r in failures]
    if dropped:
        lines += ["", "### Suggestions without a treatment atom", "", "| Case | Claim | Clinician class |", "|---|---|---|"]
        lines += [f"| {c} | {k} | {d} |" for c, k, d in dropped]
    not_supported = [(cid, f["text"], f["label"], f["reason"]) for cid, case in cases.items()
                     for f in case["facts"] if f["label"] != "supported"]
    if not_supported:
        lines += ["", "### Premises not supported", "", "| Case | Statement | Label | Reason |", "|---|---|---|---|"]
        lines += [f"| {c} | {_cell(s)} | {lab} | {_cell(r)} |" for c, s, lab, r in not_supported]
    lines.append("")
    return {"treatment_labels": dict(treatment), "monitoring_labels": dict(monitoring), "fact_labels": dict(facts),
            "vital_recall": cov["vital"]["micro"], "all_recall": cov["all"]["micro"], "without_treatment_atom": len(dropped)}


def _outcome(kind: str, case: dict) -> tuple[str, str, str]:
    """(detected | missed | not scored, label, reason) for the edited suggestion of one case."""
    if kind == "direction":
        items, wrong, right = case["facts"], {"not_supported"}, "supported"
    else:
        items, wrong, right = [a for a in case["actions"] if a["track"] == "treatment"], DISAGREE, "match"
    hit = [x for x in items if x["label"] in wrong]
    miss = [x for x in items if x["label"] == right]
    pick = (hit or miss or items or [None])[0]
    verdict = "detected" if hit else "missed" if miss else "not scored"
    return verdict, pick["label"] if pick else "no atom", pick["reason"] if pick else ""


def error_injection(lines: list[str]) -> dict:
    cases = _cases("error_injection")
    rows = []
    for t in _inputs("error_injection"):
        control, case = t["control"], cases.get(t["triple_id"])
        verdict, label, reason = _outcome(control["type"], case) if case else ("not scored", "no case", "")
        inserted = (control.get("inserted") or "").lower()  # only a premise about the inserted drug is false
        premise = [f["label"] for f in (case or {}).get("facts", []) if inserted and inserted in f["text"].lower()
                   and f["text"].lower().startswith("the patient is currently")]
        rows.append({"type": control["type"], "case": t["triple_id"], "edited": control["edited"],
                     "verdict": verdict, "label": label, "reason": reason, "premise": premise})
    lines += ["## Error injection (every edited suggestion carries one error)", "",
              "Each edited suggestion was evaluated alone. Detected: the evaluator gave the expected kind of "
              "verdict (fact not_supported; treatment not_done or partial_match). Missed: it judged the "
              "suggestion correct. Not scored: it gave no verdict (not_addressed, vague_target, condition_not_met, ...).", "",
              "| Error | Edit | n | Detected | Missed | Not scored | Sensitivity | Sensitivity when scored |",
              "|---|---|---|---|---|---|---|---|"]
    edits = {"direction": "reverse a supported abnormality", "drug": "matched treatment -> drug from a group never given",
             "stop": "matched 'Continue X' -> 'Discontinue X'", "added": "add 'Start X' from a group never given"}
    table = {}
    for kind, edit in edits.items():
        group = [r for r in rows if r["type"] == kind]
        c = Counter(r["verdict"] for r in group)
        table[kind] = dict(c)
        lines.append(f"| {kind} | {edit} | {len(group)} | {c['detected']} | {c['missed']} | {c['not scored']} | "
                     f"{_pct(c['detected'], len(group))} | {_pct(c['detected'], c['detected'] + c['missed'])} |")
    premises = Counter(lab for r in rows for lab in r["premise"])
    lines += ["", "- Fabricated 'currently receiving X' premises about the inserted drug (from edited 'Continue X' "
                  f"suggestions): {dict(premises) or 'none'} (anything but supported is correct).", "",
              "### Missed or not scored", "", "| Error | Case | Edited suggestion | Verdict | Label | Reason |",
              "|---|---|---|---|---|---|"]
    lines += [f"| {r['type']} | {r['case']} | {_cell(r['edited'])} | {r['verdict']} | {r['label']} | {_cell(r['reason'])} |"
              for r in rows if r["verdict"] != "detected"]
    lines.append("")
    return {"by_error": table, "fabricated_premises": dict(premises)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "validation" / "known_answer_tests.md")
    args = parser.parse_args()
    lines = ["# Known-answer tests", "",
             "Inputs with a known answer, built by make_controls.py from the clinicians' own actions and from "
             "suggestions the evaluator judged correct. They test the evaluator without human labels; they "
             "do not show whether its verdicts agree with clinicians on real AI answers.", ""]
    result = {"error_injection": error_injection(lines), "doctor_as_ai": doctor_as_ai(lines)}
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    args.out.with_suffix(".json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print("\n".join(lines[:40]))


if __name__ == "__main__":
    main()
