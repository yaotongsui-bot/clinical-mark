"""Build a blinded annotation set for validating the evaluator against clinicians (VeriFact protocol).

VeriFact (Chung et al., NEJM AI 2026) had every proposition of each sampled patient labeled by three
clinicians from the patient's chart, without showing them the system's verdict; a majority vote gave
the ground truth and three-way disagreements were adjudicated. This script prepares the same:

  <out>/charts/<case>.html   the patient's records: the admission before the decision time, then the
                             clinician actions and measurements after it
  <out>/annotations.csv      one row per AI statement or action, three empty annotator columns and an
                             adjudication column; machine verdicts are NOT included
  <out>/INSTRUCTIONS.md      label definitions

Usage
  python make_annotation_set.py results_fixed --triples input/mimic_triples_fixed.json \
      --cases 20 --out annotation_set
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import random
from pathlib import Path

from cm import records

ROOT = Path(__file__).resolve().parent
LABELS = "supported | not_supported | not_addressed"
INSTRUCTIONS = """# Annotation instructions

Each row of `annotations.csv` is one statement or action taken from an AI answer. Open the case's
chart in `charts/<case_id>.html` and label the row from the chart alone. Do not use outside medical
knowledge to decide what is true; decide what the record shows. Work independently of the other
annotators. Put your label in your own column (annotator_1, annotator_2 or annotator_3).

## fact rows: is the statement true for the patient at the decision time?

- supported: the records before the decision time show it is true.
- not_supported: the records before the decision time show it is false.
- not_addressed: the records do not show either way (including vague statements).

## treatment rows: did the clinicians do what the AI suggested, after the decision time?

- supported: the clinicians recorded the same treatment (same drug or treatment class, same direction:
  start / continue / stop / adjust).
- not_supported: the clinicians did something conflicting for the same goal (a different drug of the
  same class, the opposite direction, or for example extubation instead of continued ventilation).
- not_addressed: no recorded clinician action corresponds to the suggestion.

## monitoring rows: was the suggested measurement or assessment recorded after the decision time?

- supported: it was measured or charted after the decision time.
- not_addressed: it was not, or the chart cannot show it (for example "assess for causes of ...").

Use the `notes` column for anything unclear. After all three annotators finish, rows where all three
labels differ are settled in the `adjudicated` column by discussion.

## Optional, one reviewer: atomization_review.csv

Each row is one sentence of an AI answer and the items the evaluator extracted from it
(`[fact]`, `[action]`, `[goal]`). Answer yes / no:

- all_checkable_statements_extracted: every fact the sentence states or takes for granted, and every
  action it suggests, is among the extracted items.
- extracted_items_faithful: each extracted item says what the sentence says (no added certainty, no
  lost negation or condition).

## Optional, one reviewer: treatment_reference_review.csv

Each row is a treatment class the clinicians used after the decision time, with the tier the rules
gave it: vital (must not be missed) or okay. Using the chart:

- tier_should_be: vital, okay or routine.
- ai_answer_addresses_it: yes, partly or no, judged from the AI answer shown in the row.

The last row of each case asks for vital treatments the clinicians gave that are missing from the list.
"""
SOURCES = {"laboratory": "Laboratory results", "monitoring": "Bedside charting",
           "medication_administration": "Medication administration record (eMAR; includes Not Given / Held events)",
           "medication_order": "Medication orders", "treatment": "Infusions and inputs", "procedure": "Procedures",
           "specimen": "Microbiology"}


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:  # BOM so Excel reads UTF-8
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _table(rows: list[dict], columns: list[tuple[str, str]]) -> str:
    head = "".join(f"<th>{html.escape(title)}</th>" for title, _ in columns)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(r.get(key, '') if r.get(key) is not None else ''))}</td>"
                                    for _, key in columns) + "</tr>" for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def chart_html(triple: dict, pre: list[dict], actions: list[dict], observations: list[dict]) -> str:
    claims = "".join(f"<li>{html.escape(c['text'])}</li>" for c in triple["ai_generated"]["claims"])
    by_source: dict[str, list[dict]] = {}
    for r in pre:
        by_source.setdefault(r["source_type"], []).append(r)
    sections = []
    for source, rows in sorted(by_source.items()):
        shown = [{**r, "range": f"{r['lower']} to {r['upper']}" if r.get("lower") is not None or r.get("upper") is not None else ""}
                 for r in rows]
        sections.append(f"<details open><summary>{html.escape(SOURCES.get(source, source))} ({len(rows)} rows)</summary>"
                        + _table(shown, [("time", "observed_at"), ("record", "text"), ("reference range", "range")])
                        + "</details>")
    style = ("body{font-family:system-ui,sans-serif;margin:16px;max-width:1100px}table{border-collapse:collapse;"
             "width:100%;font-size:13px}td,th{border:1px solid #ccc;padding:3px 6px;text-align:left;vertical-align:top}"
             "summary{font-weight:600;margin:8px 0;cursor:pointer}h2{margin-top:28px}")
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>{triple['triple_id']}</title>"
            f"<style>{style}</style></head><body>"
            f"<h1>Case {triple['triple_id']}</h1><p>Decision time: <b>{triple['decision_point']}</b></p>"
            f"<h2>AI answer being checked</h2><ol>{claims}</ol>"
            f"<h2>Records before the decision time (this admission)</h2>{''.join(sections)}"
            f"<h2>Clinician actions after the decision time</h2>"
            + _table(sorted(actions, key=lambda a: a["observed_at"]),
                     [("time", "observed_at"), ("action type", "action_type"), ("record", "text"),
                      ("already running at decision", "spans_decision_point")])
            + "<h2>Measurements after the decision time</h2>"
            + _table(sorted(observations, key=lambda o: o["observed_at"]),
                     [("time", "observed_at"), ("measure", "concept"), ("value", "value"), ("unit", "unit")])
            + "</body></html>")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path, help="an evaluation output directory (with cases/)")
    parser.add_argument("--triples", type=Path, required=True)
    parser.add_argument("--mimic-root", type=Path, default=ROOT / "data" / "mimic-iv-demo")
    parser.add_argument("--cases", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20261012)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--types", default="fact,treatment,monitoring",
                        help="item types to annotate; VeriFact annotated everything, but monitoring items carry little information")
    args = parser.parse_args()

    results = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((args.run / "cases").glob("*.json"))}
    rng = random.Random(args.seed)
    # Half of the sample from cases with a not_supported fact, so the rare class is represented.
    flagged = sorted(c for c, r in results.items() if any(f["label"] == "not_supported" for f in r["facts"]))
    others = sorted(set(results) - set(flagged))
    k = min(len(flagged), args.cases // 2)
    chosen = sorted(rng.sample(flagged, k) + rng.sample(others, min(len(others), args.cases - k)))

    triples = {t["triple_id"]: t for t in json.loads(args.triples.read_text(encoding="utf-8"))["triples"]
               if t["triple_id"] in chosen}
    selected = [triples[c] for c in chosen]
    pre_rows = records.load_admission_rows(args.mimic_root.resolve(), selected)
    observations = records.load_post_observations(args.mimic_root.resolve(), selected)
    (args.out / "charts").mkdir(parents=True, exist_ok=True)
    rows = []
    for case_id in chosen:
        triple, result = triples[case_id], results[case_id]
        (args.out / "charts" / f"{case_id}.html").write_text(
            chart_html(triple, pre_rows.get(case_id, []), records.postdecision_actions(triple),
                       observations.get(case_id, [])), encoding="utf-8")
        items = [("fact", x) for x in result["facts"]] + [(x["track"], x) for x in result["actions"]]
        for item_type, x in items:
            if item_type not in args.types.split(","):
                continue
            rows.append({"item_id": f"{case_id}|{x['atom_id']}", "case_id": case_id, "item_type": item_type,
                         "ai_sentence": x["claim_text"], "statement": x["text"],
                         "labels": LABELS if item_type != "monitoring" else "supported | not_addressed",
                         "annotator_1": "", "annotator_2": "", "annotator_3": "", "adjudicated": "", "notes": ""})
    _write_csv(args.out / "annotations.csv", rows)
    # Optional reviews of the two parts the item labels cannot validate: the split into items, and the
    # reference list behind the omission metric. Machine verdicts are not shown here either.
    atomization, reference = [], []
    for case_id in chosen:
        result = results[case_id]
        for claim_id, sentence in dict.fromkeys((a["claim_id"], a["claim_text"]) for a in result["atoms"]):
            items = " || ".join(f"[{a['kind']}] {a['text']}" for a in result["atoms"] if a["claim_id"] == claim_id)
            atomization.append({"case_id": case_id, "ai_sentence": sentence, "extracted_items": items,
                                "all_checkable_statements_extracted": "", "extracted_items_faithful": "", "notes": ""})
        answer = " / ".join(result["claims"])
        # Ordered by tier and name: the result's own order puts uncovered classes first, which would hint at verdicts.
        listed = sorted(result["coverage"], key=lambda g: (g["importance"] != "vital", g["name"]))
        for g in listed + [{"name": "(missing from this list)", "doctor_targets": [], "importance": "", "indication": ""}]:
            reference.append({"case_id": case_id, "treatment_class": g["name"],
                              "clinician_records": "; ".join(g["doctor_targets"]), "rule_tier": g["importance"],
                              "why_vital": g["indication"] or ("listed as vital in the rules" if g["importance"] == "vital"
                                                               else ""), "ai_answer": answer, "tier_should_be": "",
                              "ai_answer_addresses_it": "", "notes": ""})
    _write_csv(args.out / "atomization_review.csv", atomization)
    _write_csv(args.out / "treatment_reference_review.csv", reference)
    (args.out / "INSTRUCTIONS.md").write_text(INSTRUCTIONS, encoding="utf-8")
    (args.out / "manifest.json").write_text(json.dumps(
        {"run": str(args.run), "cases": chosen, "items": len(rows), "seed": args.seed,
         "cases_with_not_supported_in_sample": k}, indent=1) + "\n", encoding="utf-8")
    print(f"{len(chosen)} cases, {len(rows)} items -> {args.out}")


if __name__ == "__main__":
    main()
