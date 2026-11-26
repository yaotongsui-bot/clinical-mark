"""FactEHR entailment judge as a second published baseline on the eICU test set.

FactEHR (Munnangi et al., MLHC 2025, PMLR 298; github.com/som-shahlab/factehr) scores a fact by asking
an LLM whether the source note entails it ("precision", note => fact). As in its code:
  - prompt data/prompt_templates/binary_entailment/entailment_binary6.tmpl, verbatim in
    prompts/factehr_entailment_binary6.txt, sent as one user message;
  - generation settings src/factehr/clients/generation_params.json (temperature 0.01, top_p 0.9) and
    25 new tokens for binary entailment (docs/experiments.md);
  - answer {"entailment_prediction": 1 or 0}; 1 = Supported, 0 = Not Supported (FactEHR has no third
    label, so a fact the records do not address is also 0).
Applied here:
  - premise = every record row of the hospital stay known before T, the rows VeriFact's baseline
    retrieves from, rendered in the same absolute-time format (cm/baseline.py) - no retrieval;
  - hypothesis = each fact atom of the evaluator's split (the same atoms every other run judges);
  - judge deepseek-v4-pro (as in vf_pro_cut), one call per atom, think off. The context window is set
    to 131072 tokens so the longest record (about 80k tokens) is not cut; the prompt token count the
    server reports is kept in model_cache.jsonl to check this.
  - Like every cloud call in this project, the client appends the answer schema to the (empty) system
    message, and an answer cut off at the token limit is asked again with more room.

Usage
  python run_factehr.py --source eicu --triples input/eicu_triples_gpt-oss-120b.json \
      --atoms results_eicu/gpt-oss-120b/ours_vote --out-dir results_eicu_dx/gpt-oss-120b/fe_pro_cut
  python score_factehr.py
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cm import baseline, records
from cm.llm import LLM, REPEAT
from run_baseline85 import fact_atoms

ROOT = Path(__file__).resolve().parent
PROMPT = "factehr_entailment_binary6"
SCHEMA = {"type": "object", "required": ["entailment_prediction"],
          "properties": {"entailment_prediction": {"enum": [0, 1, "0", "1"]}}}
SAMPLING = {"temperature": 0.01, "top_p": 0.9, "num_ctx": 131072}
MAX_NEW_TOKENS = 25
TO_LABEL = {1: "supported", 0: "not_supported"}
TO_VERIFACT = {"supported": "Supported", "not_supported": "Not Supported"}


def fill(template: str, premise: str, hypothesis: str) -> str:
    """str.format would trip over braces in record text, so the two fields are replaced literally."""
    return template.replace("{premise}", premise).replace("{hypothesis}", hypothesis)


def parse(answer: dict) -> str:
    return TO_LABEL[int(answer["entailment_prediction"])]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--triples", type=Path, required=True)
    p.add_argument("--atoms", type=Path, required=True, help="a run.py output folder or a split CSV")
    p.add_argument("--source", choices=["mimic", "eicu"], default="eicu")
    p.add_argument("--data-root", type=Path, default=None, help="data root (default by --source)")
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--judge-model", default="deepseek-v4-pro:0813:cloud")
    p.add_argument("--workers", type=int, default=6, help="requests at once")
    p.add_argument("--case", action="append")
    args = p.parse_args()

    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    atoms = fact_atoms(args.atoms)
    triples = {t["triple_id"]: t for t in json.loads(args.triples.read_text(encoding="utf-8"))["triples"]}
    cases = sorted({a["case_id"] for a in atoms} & set(args.case or triples))
    atoms = [a for a in atoms if a["case_id"] in cases]
    chosen = [triples[c] for c in cases]
    print(f"{len(atoms)} fact atoms in {len(cases)} cases; loading records before T ...", flush=True)
    if args.source == "eicu":
        from cm import records_eicu
        rows_by_case = records_eicu.load_admission_rows((args.data_root or ROOT / "data" / "eicu-demo").resolve(), chosen)
    else:
        rows_by_case = records.load_admission_rows((args.data_root or ROOT / "data" / "mimic-iv-demo").resolve(), chosen)
    premise = {}
    for c in cases:
        rows = rows_by_case.get(c, [])
        start, stop = baseline.span(rows, records.ts(triples[c]["decision_point"]))
        premise[c] = baseline.absolute_time_context(rows, start, stop)

    template = (ROOT / "prompts" / f"{PROMPT}.txt").read_text(encoding="utf-8")
    llm = LLM(out / "model_cache.jsonl")

    def judge(a: dict) -> dict:
        row = {"atom_id": a["atom_id"], "case_id": a["case_id"], "fact_kind": a["fact_kind"], "text": a["text"],
               "records_in_case": len(rows_by_case.get(a["case_id"], [])), "premise_chars": len(premise[a["case_id"]])}
        try:
            answer = llm.json(args.judge_model, "", fill(template, premise[a["case_id"]], a["text"]), SCHEMA,
                              num_predict=MAX_NEW_TOKENS, stage=f"factehr_judge:{args.judge_model}",
                              case_id=a["case_id"], sampling=SAMPLING)
            label = parse(answer)
            row.update(label=label, verdict=TO_VERIFACT[label], reason="")
        except (ValueError, RuntimeError) as exc:
            row.update(label="", verdict="", reason=f"no valid verdict: {exc}"[:300])
        return row

    print(f"judge {args.judge_model}: {len(atoms)} atoms, {args.workers} at once", flush=True)
    rows_out = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for i, row in enumerate(pool.map(judge, atoms), 1):
            rows_out.append(row)
            if i % 25 == 0:
                print(f"[judge] {i}/{len(atoms)} ({time.time() - started:.0f}s)", flush=True)
    with (out / "verdicts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows_out[0]))
        writer.writeheader()
        writer.writerows(rows_out)
    failed = sum(not r["label"] for r in rows_out)
    meta = {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()}
    meta.update(repeat=REPEAT, n=len(rows_out), no_verdict=failed, llm_calls=llm.calls, cache_hits=llm.cache_hits,
                seconds=round(time.time() - started), prompt=PROMPT, sampling=SAMPLING, max_new_tokens=MAX_NEW_TOKENS,
                method="FactEHR entailment judge: whole record before T as premise, one judge, no retrieval, "
                       "no code checks, two labels")
    (out / "run.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out / 'verdicts.csv'} ({len(rows_out)} atoms, {failed} without a verdict, "
          f"{llm.calls} model calls)", flush=True)


if __name__ == "__main__":
    main()
