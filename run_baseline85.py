"""VeriFact baseline on this project's 85 ICU cases (Route B, main comparison).

The baseline judges the same fact atoms as this project's evaluator (Claude's split standard,
reference/split_standard.csv), so the two can be compared item by item; only the fact checking
differs. VeriFact as in its code (see cm/baseline.py and run_bhc.py):
  - every record row of the admission is a fact, retrieved per atom (hybrid or rerank, N = 50);
  - context in VeriFact's absolute-time format;
  - VeriFact's judge prompt and settings (prompts/verifact_*.txt, temperature 0.1, up to 5 samples),
    one local model, default llama3.1:8b-instruct-q4_K_M;
  - no code checks, no time-of-administration guard, three labels only.

--time-cut before   records known before the decision time T (this project's reference EHR)
--time-cut none     the whole admission, including records after T (VeriFact's whole-EHR setting;
                    it shows what is gained by cutting at T)

Usage
  python run_baseline85.py --out-dir results_baseline85/vf_hybrid_nocut --time-cut none
  python run_baseline85.py --out-dir results_baseline85/vf_hybrid_cut --time-cut before
  python run_baseline85.py --retrieval-method rerank ...   (needs sentence-transformers and torch)
  python score_baseline85.py REFERENCE.csv results_baseline85/vf_hybrid_nocut results_final_claude_split
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

from cm import baseline, records
from cm.llm import LLM, REPEAT
from cm.panel import Panel, Request
from cm.retrieve import Embedder
from run_bhc import VERIFACT_ATTEMPTS, VERIFACT_SAMPLING, VERIFACT_SCHEMA, parse_verifact

ROOT = Path(__file__).resolve().parent
TO_VERIFACT = {"supported": "Supported", "not_supported": "Not Supported", "not_addressed": "Not Addressed"}
FAR_FUTURE = "2300-01-01 00:00:00"


def fact_atoms(path: Path) -> list[dict]:
    """Fact atoms from a split CSV (reference/split_standard.csv) or from a run.py output folder
    (cases/*.json, the atoms after the safety nets), so the baseline judges the same atoms."""
    if path.is_dir():
        out = []
        for case in sorted((path / "cases").glob("*.json")):
            for f in json.loads(case.read_text(encoding="utf-8"))["facts"]:
                out.append({"atom_id": f["atom_id"], "case_id": case.stem, "fact_kind": f.get("fact_kind", ""),
                            "text": f["text"], "kind": "fact"})
        return out
    with path.open(encoding="utf-8", newline="") as handle:
        return [r for r in csv.DictReader(handle) if r["kind"] == "fact"]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--triples", type=Path, default=ROOT / "input" / "mimic_triples_deepseek.json")
    p.add_argument("--atoms", type=Path, default=ROOT / "reference" / "split_standard.csv")
    p.add_argument("--source", choices=["mimic", "eicu"], default="mimic")
    p.add_argument("--mimic-root", type=Path, default=None, help="data root (default by --source)")
    p.add_argument("--out-dir", type=Path, default=ROOT / "results_baseline85" / "run")
    p.add_argument("--time-cut", choices=["before", "none"], default="none")
    p.add_argument("--retrieval-method", choices=["dense", "hybrid", "rerank"], default="hybrid")
    p.add_argument("--top-n", type=int, default=50)
    p.add_argument("--judge-model", default="llama3.1:8b-instruct-q4_K_M")
    p.add_argument("--cloud-workers", type=int, default=10, help="requests at once for a :cloud judge")
    p.add_argument("--prompt", default="verifact_fewshot",
                   help="judge template in prompts/ (verifact_fewshot; verifact_fewshot_rules adds this "
                        "evaluator's judging rules as instruction 5)")
    p.add_argument("--case", action="append")
    p.add_argument("--embeddings-dir", type=Path, default=ROOT / "embeddings_baseline85")
    args = p.parse_args()

    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    atoms = fact_atoms(args.atoms)
    triples = {t["triple_id"]: t for t in json.loads(args.triples.read_text(encoding="utf-8"))["triples"]}
    cases = sorted({a["case_id"] for a in atoms} & set(args.case or triples))
    atoms = [a for a in atoms if a["case_id"] in cases]
    missing = sorted({a["case_id"] for a in atoms} - set(triples))
    if missing:
        raise SystemExit(f"cases not in {args.triples.name}: {missing[:5]}")
    chosen = [triples[c] for c in cases]
    print(f"{len(atoms)} fact atoms in {len(cases)} cases; loading records (time cut: {args.time_cut}) ...", flush=True)
    if args.source == "eicu":
        from cm import records_eicu
        root = (args.mimic_root or ROOT / "data" / "eicu-demo").resolve()
        if args.time_cut == "none":  # the whole stay, including records after T
            clocks, stays = records_eicu._clocks_for(root, chosen)
            rows = records_eicu.stay_rows(root, set(stays), None, float("inf"), clocks)
            rows_by_case = {case: rows.get(stay, []) for stay, ids in stays.items() for case in ids}
        else:
            rows_by_case = records_eicu.load_admission_rows(root, chosen)
    else:
        if args.time_cut == "none":
            chosen = [{**t, "decision_point": FAR_FUTURE} for t in chosen]
        rows_by_case = records.load_admission_rows((args.mimic_root or ROOT / "data" / "mimic-iv-demo").resolve(), chosen)

    embedder = Embedder(args.embeddings_dir.resolve())
    reranker = baseline.Reranker() if args.retrieval_method == "rerank" else None
    system = (ROOT / "prompts" / "verifact_system.txt").read_text(encoding="utf-8")
    template = (ROOT / "prompts" / f"{args.prompt}.txt").read_text(encoding="utf-8")
    llm = LLM(out / "model_cache.jsonl")
    panel = Panel(llm, [args.judge_model], cloud_workers=args.cloud_workers)
    meta_rows = []
    for i, a in enumerate(atoms, 1):
        rows = rows_by_case.get(a["case_id"], [])
        picked = baseline.retrieve(a["text"], rows, args.retrieval_method, args.top_n, embedder, reranker)
        end = records.ts(triples[a["case_id"]]["decision_point"]) if args.time_cut == "before" else None
        start, stop = baseline.span(rows, end)
        reference = baseline.absolute_time_context(picked, start, stop)
        payload = json.dumps({"text": a["text"], "reference": reference}, indent=4, ensure_ascii=False)
        panel.submit(Request(key=a["atom_id"], stage="verifact_judge", case_id=a["case_id"], system=system,
                             user=template.replace("{json}", payload), schema=VERIFACT_SCHEMA, cite_key="evidence",
                             needs_cite=set(), allowed=set(), fallback="not_addressed", parse=parse_verifact,
                             attempts=VERIFACT_ATTEMPTS, sampling=VERIFACT_SAMPLING))
        meta_rows.append({"atom_id": a["atom_id"], "case_id": a["case_id"], "fact_kind": a["fact_kind"],
                          "text": a["text"], "n_reference": len(picked), "records_in_case": len(rows)})
        if i % 50 == 0:
            print(f"[retrieve] {i}/{len(atoms)} ({time.time() - started:.0f}s)", flush=True)
    embedder.save()
    print(f"judge {args.judge_model}: {len(panel.requests)} atoms", flush=True)
    panel.run()
    for row in meta_rows:
        v = panel.verdict(row["atom_id"])
        valid = any(x is not None for x in v["votes"].values())
        row.update(label=v["label"] if valid else "", verdict=TO_VERIFACT[v["label"]] if valid else "",
                   reason=v["reason"] if valid else "no valid verdict after every sample")
    with (out / "verdicts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(meta_rows[0]))
        writer.writeheader()
        writer.writerows(meta_rows)
    meta = {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()}
    meta.update(repeat=REPEAT, n=len(meta_rows), llm_calls=llm.calls, cache_hits=llm.cache_hits, seconds=round(time.time() - started),
                method="VeriFact baseline: one judge, VeriFact prompt, no code checks")
    (out / "run.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out / 'verdicts.csv'} ({len(meta_rows)} atoms, {llm.calls} model calls)", flush=True)


if __name__ == "__main__":
    main()
