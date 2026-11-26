"""Build a blinded annotation set for validating the evaluator against clinicians (VeriFact protocol).

VeriFact (Chung et al., NEJM AI 2026) had every proposition of each sampled patient labeled by three
clinicians from the patient's chart, without showing them the system's verdict; a majority vote gave
the ground truth and three-way disagreements were adjudicated. This script prepares the same:

  <out>/charts/<case>.html   the patient's records: the admission before the decision time, then the
                             clinician actions and measurements after it
  <out>/annotations.csv      one row per AI statement or action, three empty annotator columns and an
                             adjudication column; machine verdicts are NOT included
  <out>/INSTRUCTIONS.md      label definitions

Several answer sets can be sampled into one sheet (each case appears in one set only). Besides the AI
statements and actions, each treated abnormality gets a "finding" row (mentioned / omitted), which
checks the fact-omission count.

Usage
  python make_annotation_set.py --run base,results_deepseek_cloud,input/mimic_triples_deepseek.json,14 \
      --run s1,results_open_deepseek_s1_cloud,input/mimic_triples_open_deepseek_s1.json,6 --out annotation_set
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
LABELS = {"fact": "supported | not_supported | unverifiable",
          "treatment": "agrees | disagrees | undetermined",
          "monitoring": "agrees | disagrees | undetermined",
          "finding": "mentioned | omitted"}
INSTRUCTIONS = """# Annotation instructions

Each row of `annotations.csv` is one statement or action taken from an AI answer, or one abnormality
the clinicians treated. Open the row's chart, `charts/<chart>.html`, and label the row from the chart
alone. Do not use outside medical knowledge to decide what is true; decide what the record shows.
Work independently of the other annotators. Put your label in your own column (annotator_1,
annotator_2 or annotator_3). The allowed labels for each row are in its `labels` column.

## fact rows: is the statement true for the patient at the decision time?

- supported: the records before the decision time show it is true. A stated value counts as true
  when a recorded value before the decision matches it.
- not_supported: the records before the decision time show it is false.
- unverifiable: the records show neither way, or the statement is too vague to check.

## treatment rows: did the clinicians do what the AI suggested, after the decision time?

- agrees: the clinicians recorded the same treatment class in the same direction (start / continue /
  stop / increase / decrease). Another drug of the same class for the same aim also agrees.
- disagrees: no recorded clinician action corresponds to the suggestion, or the clinicians went the
  opposite way (the AI says stop and the drug continues; the AI says increase and the dose went
  down; the AI says change a dose and no change is recorded; continued ventilation vs extubation).
- undetermined: the suggestion names no concrete treatment ("optimize management"), its condition
  did not occur, or the chart cannot show it.

## monitoring rows: was the suggested measurement or assessment recorded after the decision time?

- agrees: it was measured or charted after the decision time.
- disagrees: it could have been charted but was not.
- undetermined: the chart cannot show it (for example "assess for causes of ...").

## finding rows: does the AI answer mention this abnormality?

Each row names an abnormality present before the decision that the clinicians then treated (the
treatment is given). Read the AI answer at the top of the chart.

- mentioned: the answer states or takes for granted something about this measure, right or wrong
  (a value, high/low, or a diagnosis such as "hypocalcemia"). A suggestion to monitor it alone does
  not count.
- omitted: the answer says nothing about it.

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
gave it: vital (key treatment, must not be missed) or okay. Using the chart:

- tier_should_be: vital, okay or routine.
- ai_answer_addresses_it: yes, partly or no, judged from the AI answer shown in the row.

The last row of each chart asks for vital treatments the clinicians gave that are missing from the list.
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


def _sample(results: dict, n: int, rng: random.Random, exclude: set[str]) -> tuple[list[str], int]:
    """Half of the sample from cases with a not_supported fact, so the rare class is represented."""
    pool = {c: r for c, r in results.items() if c not in exclude}
    flagged = sorted(c for c, r in pool.items() if any(f["label"] == "not_supported" for f in r["facts"]))
    others = sorted(set(pool) - set(flagged))
    k = min(len(flagged), n // 2)
    return sorted(rng.sample(flagged, k) + rng.sample(others, min(len(others), n - k))), k


def _blank() -> dict:
    return {"annotator_1": "", "annotator_2": "", "annotator_3": "", "adjudicated": "", "notes": ""}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="append", required=True,
                        help="tag,results_dir,triples_json,n_cases (repeatable); each case is used by one run only")
    parser.add_argument("--mimic-root", type=Path, default=ROOT / "data" / "mimic-iv-demo")
    parser.add_argument("--seed", type=int, default=20261104)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--types", default="fact,treatment,finding",
                        help="item types to annotate (fact, treatment, monitoring, finding); "
                             "monitoring items carry little information")
    args = parser.parse_args()
    types = set(args.types.split(","))
    rng = random.Random(args.seed)
    (args.out / "charts").mkdir(parents=True, exist_ok=True)
    rows, atomization, reference, manifest, used = [], [], [], [], set()
    for spec in args.run:
        tag, run_dir, triples_path, n = spec.split(",")
        run_dir = Path(run_dir)
        results = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((run_dir / "cases").glob("*.json"))}
        chosen, k = _sample(results, int(n), rng, used)
        used.update(chosen)
        triples = {t["triple_id"]: t for t in json.loads(Path(triples_path).read_text(encoding="utf-8"))["triples"]
                   if t["triple_id"] in chosen}
        selected = [triples[c] for c in chosen]
        pre_rows = records.load_admission_rows(args.mimic_root.resolve(), selected)
        observations = records.load_post_observations(args.mimic_root.resolve(), selected)
        manifest.append({"tag": tag, "run": str(run_dir), "triples": triples_path, "cases": chosen,
                         "cases_with_not_supported_in_sample": k})
        for case_id in chosen:
            triple, result, chart = triples[case_id], results[case_id], f"{tag}_{case_id}"
            (args.out / "charts" / f"{chart}.html").write_text(
                chart_html(triple, pre_rows.get(case_id, []), records.postdecision_actions(triple),
                           observations.get(case_id, [])), encoding="utf-8")
            base = {"case_id": case_id, "answer_set": tag, "chart": chart}
            items = [("fact", x) for x in result["facts"]] + [(x["track"], x) for x in result["actions"]]
            for item_type, x in items:
                if item_type in types:
                    rows.append({"item_id": f"{tag}|{case_id}|{x['atom_id']}", **base, "item_type": item_type,
                                 "ai_sentence": x["claim_text"], "statement": x["text"], "labels": LABELS[item_type],
                                 **_blank()})
            if "finding" in types:  # every treated abnormality, mentioned or not, so the sheet gives no hint
                for f in sorted(result["fact_omissions"], key=lambda f: f["name"]):
                    rows.append({"item_id": f"{tag}|{case_id}|finding:{f['concept']}:{f['direction']}", **base,
                                 "item_type": "finding", "ai_sentence": "",
                                 "statement": f"{f['name']} {f['direction']} before the decision; the clinicians gave "
                                              f"{', '.join(f['treated_by'])}. ({f['reason']})",
                                 "labels": LABELS["finding"], **_blank()})
            for claim_id, sentence in dict.fromkeys((a["claim_id"], a["claim_text"]) for a in result["atoms"]):
                extracted = " || ".join(f"[{a['kind']}] {a['text']}" for a in result["atoms"] if a["claim_id"] == claim_id)
                atomization.append({**base, "ai_sentence": sentence, "extracted_items": extracted,
                                    "all_checkable_statements_extracted": "", "extracted_items_faithful": "", "notes": ""})
            answer = " / ".join(result["claims"])
            # Ordered by tier and name: the result's own order puts uncovered classes first, which would hint at verdicts.
            listed = sorted(result["coverage"], key=lambda g: (g["importance"] != "vital", g["name"]))
            for g in listed + [{"name": "(missing from this list)", "doctor_targets": [], "importance": "", "indication": ""}]:
                reference.append({**base, "treatment_class": g["name"], "clinician_records": "; ".join(g["doctor_targets"]),
                                  "rule_tier": g["importance"],
                                  "why_vital": g["indication"] or ("listed as vital in the rules" if g["importance"] == "vital" else ""),
                                  "ai_answer": answer, "tier_should_be": "", "ai_answer_addresses_it": "", "notes": ""})
    _write_csv(args.out / "annotations.csv", rows)
    _write_csv(args.out / "atomization_review.csv", atomization)
    _write_csv(args.out / "treatment_reference_review.csv", reference)
    (args.out / "INSTRUCTIONS.md").write_text(INSTRUCTIONS, encoding="utf-8")
    counts = {t: sum(r["item_type"] == t for r in rows) for t in sorted({r["item_type"] for r in rows})}
    (args.out / "manifest.json").write_text(json.dumps(
        {"runs": manifest, "items": len(rows), "items_by_type": counts, "seed": args.seed}, indent=1) + "\n",
        encoding="utf-8")
    print(f"{len(used)} cases, {len(rows)} items {counts} -> {args.out}")


if __name__ == "__main__":
    main()
