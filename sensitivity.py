"""Sensitivity analysis of the fact judge, following VeriFact (Chung et al., NEJM AI 2026).

VeriFact varied the retrieval method, the number of retrieved facts N, the fact representation and
the judge model (with and without reasoning), and chose the setting with the best agreement with
clinicians. This script re-judges the facts of an evaluation run that need a model (statements
without a measurable form), one factor at a time around the default (hybrid retrieval, N = 50):

  retrieval in {bm25, dense, hybrid} at N = 50
  N in {10, 25, 50, 100} with hybrid retrieval
  each judge model on its own; gemma4:12b in reasoning mode only at the default retrieval
  (reasoning takes 20-130 s per item, so the full grid would take many hours)

Every configuration is compared with the ground truth from score_annotations-style consensus labels
when --annotations is given, otherwise with the run's own panel verdicts.

Usage
  python sensitivity.py results_fixed --triples input/mimic_triples_fixed.json \
      [--annotations annotation_set/annotations.csv] --out sensitivity_fixed
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from cm import ground, records
from cm.llm import LLM
from cm.panel import Panel
from cm.retrieve import Embedder, Retriever
from score_annotations import CLASSES, agreement_stats

ROOT = Path(__file__).resolve().parent
JUDGES = [("gemma4:12b", False), ("gemma4:12b", True), ("llama3.1:8b-instruct-q4_K_M", False), ("qwen2.5:14b", False)]
RETRIEVAL = [("bm25", 50), ("dense", 50), ("hybrid", 10), ("hybrid", 25), ("hybrid", 50), ("hybrid", 100)]
DEFAULT = ("hybrid", 50)


def consensus(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    out = {}
    for row in rows:
        labels = [row[c].strip() for c in ("annotator_1", "annotator_2", "annotator_3") if row.get(c, "").strip()]
        truth = row.get("adjudicated", "").strip()
        if not truth and labels:
            label, n = Counter(labels).most_common(1)[0]
            truth = label if n >= 2 else ""
        if truth:
            out[row["item_id"]] = truth
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--triples", type=Path, required=True)
    parser.add_argument("--mimic-root", type=Path, default=ROOT / "data" / "mimic-iv-demo")
    parser.add_argument("--annotations", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    cases = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((args.run / "cases").glob("*.json"))}
    truth = consensus(args.annotations) if args.annotations else {}
    targets = []  # (case_id, atom, reference label)
    for case_id, case in cases.items():
        for fact in case["facts"]:
            item_id = f"{case_id}|{fact['atom_id']}"
            if fact.get("method") != "llm_panel":
                continue
            if args.annotations and item_id not in truth:
                continue
            targets.append((case_id, fact, truth.get(item_id, fact["label"])))
    if not targets:
        raise SystemExit("no judge-panel facts to analyse")
    triples = {t["triple_id"]: t for t in json.loads(args.triples.read_text(encoding="utf-8"))["triples"]
               if t["triple_id"] in {c for c, _, _ in targets}}
    rows = records.load_admission_rows(args.mimic_root.resolve(), list(triples.values()))
    args.out.mkdir(parents=True, exist_ok=True)
    llm = LLM(args.out / "model_cache.jsonl")
    embedder = Embedder(ROOT / "embeddings")
    system = (ROOT / "prompts" / "fact_judge.txt").read_text(encoding="utf-8")
    reference = "clinician consensus" if args.annotations else f"panel verdicts in {args.run}"
    lines = ["# Fact-judge sensitivity analysis", "",
             f"- {len(targets)} facts judged by the panel in `{args.run}`; reference: {reference}.",
             "- Labels: " + ", ".join(CLASSES) + ".", "",
             "| Retrieval | N | Judge | Reasoning | Percent agreement | Gwet's AC1 | MCC | Labels |",
             "|---|---|---|---|---|---|---|---|"]
    results = []
    for mode, top_n in RETRIEVAL:
        retriever = Retriever(embedder, mode, top_n)
        pending = {}
        for case_id, atom, _ in targets:
            req = ground._judge_request(atom, rows.get(case_id, []), triples[case_id], system, retriever)
            pending[atom["atom_id"]] = req
        for model, think in JUDGES:
            if think and (mode, top_n) != DEFAULT:
                continue
            panel = Panel(llm, [model], {model} if think else set())
            for req in pending.values():
                if "pending" in req:
                    panel.submit(req["pending"])
            panel.run()
            pairs, labels = [], Counter()
            for case_id, atom, ref in targets:
                req = pending[atom["atom_id"]]
                label = (ground.finalize(req, panel.verdict(req["pending"].key))["label"] if "pending" in req
                         else req["label"])
                labels[label] += 1
                pairs.append((ref, label))
            st = agreement_stats(pairs)
            results.append({"retrieval": mode, "top_n": top_n, "judge": model, "reasoning": think, **st,
                            "labels": dict(labels)})
            ac1 = "-" if st["gwet_ac1"] is None else f"{st['gwet_ac1']:.2f}"
            mcc = "-" if st["mcc"] is None else f"{st['mcc']:.2f}"
            lines.append(f"| {mode} | {top_n} | {model} | {'yes' if think else 'no'} | "
                         f"{st['percent_agreement'] * 100:.1f}% | {ac1} | {mcc} | {dict(labels)} |")
            print(lines[-1], flush=True)
    embedder.save()
    (args.out / "sensitivity.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    (args.out / "sensitivity.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
