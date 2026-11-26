"""Judge VeriFact-BHC propositions with local models (Route A), laid out like VeriFact's own pipeline.

Judge style (--judge-style):
  verifact  VeriFact's judge, as in packages/llm_judge (judge.py, prompts.py): its system prompt and
            few-shot prompt (prompts/verifact_system.txt, prompts/verifact_fewshot.txt), the input
            {"text", "reference"} as JSON with indent 4, output {"verdict", "reason"}, the verdict
            title-cased and checked, temperature 0.1, top_p 1.0, up to 5 samples until it is valid.
  ours      this project's judge rules (prompts/bhc_judge.txt) and the three-model majority vote.

Reference context (--context):
  released  the exact context VeriFact's judge saw (verifact/reference_payloads.parquet) for one
            released model and setting; default Llama-70B, rerank, N = 50, absolute time, whole EHR.
  ours      this project's retrieval (bge-m3 + BM25 with distribution-based score fusion, no reranker)
            over sentence facts of reference_ehr/ehr_noteevents.csv.gz, written in VeriFact's
            absolute-time format (verifact style) or as numbered records (ours style).

Replay check: --source-model Llama-8B --judge-style verifact --judge-models llama3.1:8b-instruct-q4_K_M
re-judges the released Llama-8B contexts with a local Llama 3.1 8B; verdict_matches_release then shows
how closely this implementation reproduces VeriFact's released verdicts (VeriFact's replay script
reports the same column and also does not expect identical text).

The release is MIMIC-III credentialed data: only local Ollama models are accepted, and the output
folder (which holds note text in model_cache.jsonl) is ignored by git.

Usage
  python run_bhc.py --out-dir results_bhc/vf_llama8b_replay --source-model Llama-8B \
      --judge-models llama3.1:8b-instruct-q4_K_M --sample 600
  python run_bhc.py --judge-style ours --out-dir results_bhc/ours_panel_released --sample 600
  python score_bhc.py results_bhc/vf_llama8b_replay results_bhc/ours_panel_released
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from cm import notes, verifact_bhc as vb
from cm.llm import LLM
from cm.panel import Panel, Request

ROOT = Path(__file__).resolve().parent
OURS_SCHEMA = {"type": "object", "required": ["label", "evidence", "reason"],
               "properties": {"label": {"type": "string", "enum": list(vb.LABELS)},
                              "evidence": {"type": "array", "items": {"type": "string"}},
                              "reason": {"type": "string"}}}
# VeriFact's SimpleVerdict (schema.py): two strings; the verdict is checked after title-casing.
VERIFACT_SCHEMA = {"type": "object", "required": ["verdict", "reason"],
                   "properties": {"verdict": {"type": "string"}, "reason": {"type": "string"}}}
VERIFACT_SAMPLING = {"temperature": 0.1, "top_p": 1.0}
VERIFACT_ATTEMPTS = 5  # num_invalid_output_retries in scripts/evaluate/replay_physionet_v1_1_0.py
STRATA = ["author_type", "proposition_type"]


def parse_verifact(out: dict) -> dict:
    """validate_simple_verdict: title-case the verdict and require one of the three labels."""
    verdict = str(out.get("verdict", "")).title()
    if verdict not in vb.TO_VERIFACT.values():
        raise ValueError(f"invalid verdict {out.get('verdict')!r}")
    return {"label": vb.norm_label(verdict), "reason": str(out.get("reason", ""))}


def pick(props: pd.DataFrame, args) -> pd.DataFrame:
    if args.author_type != "all":
        props = props[props["author_type"] == args.author_type]
    if args.proposition_type != "all":
        props = props[props["proposition_type"] == args.proposition_type]
    if args.subjects:
        props = props[props["subject_id"].isin(args.subjects.split(","))]
    if args.limit_subjects:
        keep = sorted(props["subject_id"].unique(), key=lambda s: (len(s), s))[:args.limit_subjects]
        props = props[props["subject_id"].isin(keep)]
    if args.sample and args.sample < len(props):
        # Same share from every author x proposition-type stratum, fixed seed.
        frac = args.sample / len(props)
        keep = [i for _, g in props.groupby(STRATA)
                for i in g.sample(n=max(1, round(len(g) * frac)), random_state=args.seed).index]
        props = props.loc[keep]
    return props.sort_values(["subject_id", "proposition_id"]).reset_index(drop=True)


def released_context(root: Path, props: pd.DataFrame, args) -> tuple[pd.DataFrame, dict[str, str]]:
    configs = vb.load_rater_configurations(root)
    raters = vb.select_raters(configs, args.source_model, retrieval_method=args.retrieval_method,
                              top_n=str(args.source_top_n), reference_format=args.reference_format,
                              reference_only_admission=str(args.admission_only).lower())
    verdicts = vb.load_verdicts(root, args.source_model, list(raters["rater_alias"]))
    verdicts = verdicts.merge(raters[["rater_alias", "fact_type"]], on="rater_alias")
    merged = props.merge(verdicts, on="proposition_id", how="left")
    # VeriFact pairs each proposition type with the same fact type when both exist.
    same = merged["fact_type"] == merged["proposition_type"]
    if same.any():
        merged = merged[same | ~merged["proposition_id"].isin(merged.loc[same, "proposition_id"])]
    if merged["proposition_id"].duplicated().any():
        aliases = sorted(merged.loc[merged["proposition_id"].duplicated(keep=False), "rater_alias"].unique())
        raise SystemExit(f"several rater configurations per proposition ({aliases}); narrow the setting")
    missing = merged["reference_id"].isna().sum()
    if missing:
        print(f"{missing} propositions have no released verdict for this setting and are skipped", flush=True)
        merged = merged[merged["reference_id"].notna()]
    merged = merged.rename(columns={"label": "verifact_label", "verdict": "verifact_verdict"})
    refs = vb.load_references(root, set(merged["reference_id"].astype(str)))
    return merged.reset_index(drop=True), refs


def make_request(args, system: str, template: str, r, reference, alias: dict) -> Request:
    if args.judge_style == "verifact":
        payload = json.dumps({"text": r.text, "reference": reference}, indent=4, ensure_ascii=False)
        return Request(key=r.proposition_id, stage="bhc_judge", case_id=r.subject_id, system=system,
                       user=template.replace("{json}", payload), schema=VERIFACT_SCHEMA, cite_key="evidence",
                       needs_cite=set(), allowed=set(), fallback="not_addressed", parse=parse_verifact,
                       attempts=VERIFACT_ATTEMPTS, sampling=VERIFACT_SAMPLING)
    return Request(key=r.proposition_id, stage="bhc_judge", case_id=r.subject_id, system=system,
                   user=json.dumps({"text": r.text, "reference": reference}, ensure_ascii=False),
                   schema=OURS_SCHEMA, cite_key="evidence",
                   needs_cite={"supported", "not_supported"} if alias else set(), allowed=set(alias),
                   fallback="not_addressed")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--release-dir", type=Path)
    p.add_argument("--out-dir", type=Path, default=ROOT / "results_bhc" / "run")
    p.add_argument("--judge-style", choices=["verifact", "ours"], default="verifact")
    p.add_argument("--context", choices=["released", "ours"], default="released")
    p.add_argument("--judge-models", default=None,
                   help="comma-separated; default llama3.1:8b-instruct-q4_K_M (verifact) or the three-model "
                        "panel qwen2.5:14b, llama3.1:8b-instruct-q4_K_M, gemma4:12b (ours)")
    p.add_argument("--judge-think", default="", help="comma-separated judges in reasoning mode")
    p.add_argument("--author-type", choices=["llm", "human", "all"], default="all")
    p.add_argument("--proposition-type", choices=["claim", "sentence", "all"], default="all")
    p.add_argument("--subjects", help="comma-separated subject_id values")
    p.add_argument("--limit-subjects", type=int)
    p.add_argument("--sample", type=int, help="stratified random sample of this many propositions")
    p.add_argument("--seed", type=int, default=20261112)
    # Released-context setting (also names the VeriFact baseline that score_bhc.py compares against).
    p.add_argument("--source-model", default="Llama-70B")
    p.add_argument("--retrieval-method", default="rerank")
    p.add_argument("--source-top-n", type=int, default=50)
    p.add_argument("--reference-format", default="absolute_time")
    p.add_argument("--admission-only", action="store_true", help="current admission instead of whole EHR")
    # Our retrieval.
    p.add_argument("--retrieval", choices=["hybrid", "dense", "bm25"], default="hybrid")
    p.add_argument("--top-n", type=int, default=50)
    p.add_argument("--embeddings-dir", type=Path, default=ROOT / "embeddings_bhc")
    args = p.parse_args()

    if args.judge_models is None:
        args.judge_models = ("llama3.1:8b-instruct-q4_K_M" if args.judge_style == "verifact"
                             else "qwen2.5:14b,llama3.1:8b-instruct-q4_K_M,gemma4:12b")
    judges = [m.strip() for m in args.judge_models.split(",") if m.strip()]
    vb.check_local_models(judges)
    root = vb.release_dir(args.release_dir, ROOT)
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.judge_style == "verifact":
        system = (ROOT / "prompts" / "verifact_system.txt").read_text(encoding="utf-8")
        template = (ROOT / "prompts" / "verifact_fewshot.txt").read_text(encoding="utf-8")
    else:
        system, template = (ROOT / "prompts" / "bhc_judge.txt").read_text(encoding="utf-8"), ""
    started = time.time()

    props = pick(vb.load_propositions(root), args)
    print(f"{len(props)} propositions from {props['subject_id'].nunique()} subjects", flush=True)
    llm = LLM(out / "model_cache.jsonl")
    panel = Panel(llm, judges, {m.strip() for m in args.judge_think.split(",") if m.strip()})
    rows = []
    if args.context == "released":
        props, refs = released_context(root, props, args)
        for r in props.itertuples():
            panel.submit(make_request(args, system, template, r, refs[str(r.reference_id)], {}))
            rows.append({"proposition_id": r.proposition_id, "subject_id": r.subject_id,
                         "author_type": r.author_type, "proposition_type": r.proposition_type,
                         "rater_alias": r.rater_alias, "reference_id": r.reference_id,
                         "verifact_label": r.verifact_label, "n_reference": None})
    else:
        from cm.retrieve import Embedder, Retriever

        ehr = root / "reference_ehr"
        by_subject = notes.read_notes(ehr / "ehr_noteevents.csv.gz", set(props["subject_id"]))
        admissions = notes.read_admissions(ehr / "admissions.csv.gz") if (ehr / "admissions.csv.gz").exists() else {}
        if args.admission_only and not admissions:
            raise SystemExit("--admission-only needs reference_ehr/admissions.csv.gz")
        embedder = Embedder(args.embeddings_dir.resolve()) if args.retrieval != "bm25" else None
        retriever = Retriever(embedder, args.retrieval, args.top_n)
        facts = {s: notes.reference_rows(n, admission=admissions.get(s) if args.admission_only else None)
                 for s, n in by_subject.items()}
        for i, r in enumerate(props.itertuples(), 1):
            picked = retriever.search(r.text, r.text, facts.get(r.subject_id, []))
            alias = {f"R{k}": f for k, f in enumerate(picked, 1)}
            rows.append({"proposition_id": r.proposition_id, "subject_id": r.subject_id,
                         "author_type": r.author_type, "proposition_type": r.proposition_type,
                         "rater_alias": "", "reference_id": "", "verifact_label": None, "n_reference": len(alias)})
            if not alias:  # nothing retrieved (BM25 only returns rows sharing a word): no judge needed
                continue
            if args.judge_style == "verifact":
                reference = notes.absolute_time_context(picked, admissions.get(r.subject_id))
            else:
                reference = [{"id": k, "date": f["observed_at"][:10], "time": f["observed_at"][11:16] or "unknown",
                              "note_type": f["source_type"], "text": f["text"]} for k, f in alias.items()]
            panel.submit(make_request(args, system, template, r, reference, alias))
            if i % 200 == 0:
                print(f"[retrieve] {i}/{len(props)} ({time.time() - started:.0f}s)", flush=True)
        if embedder:
            embedder.save()

    print(f"judge ({args.judge_style}): {len(panel.requests)} items x {len(judges)} models {judges}", flush=True)
    panel.run()
    for row in rows:
        if row["proposition_id"] not in panel.requests:
            row.update(label="not_addressed", verdict=vb.TO_VERIFACT["not_addressed"], agreement="rule", votes="{}",
                       reason="No note fact related to the statement was retrieved.")
            continue
        v = panel.verdict(row["proposition_id"])
        row.update(label=v["label"], verdict=vb.TO_VERIFACT[v["label"]], agreement=v["agreement"],
                   votes=json.dumps(v["votes"]), reason=v["reason"])
        if all(x is None for x in v["votes"].values()):
            row["agreement"] = "invalid"  # no valid verdict after every attempt (VeriFact leaves it unscored)
    df = pd.DataFrame(rows)
    if args.context == "released":
        df["verdict_matches_release"] = df["label"] == df["verifact_label"]
    df.to_csv(out / "verdicts.csv", index=False)
    meta = {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()}
    meta.update(release_dir=str(root), judges=judges, n=len(rows), llm_calls=llm.calls, cache_hits=llm.cache_hits,
                seconds=round(time.time() - started))
    (out / "run.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    note = ""
    if args.context == "released":
        note = f"; matches the released {args.source_model} verdict: {df['verdict_matches_release'].mean():.1%}"
    print(f"wrote {out / 'verdicts.csv'} ({len(rows)} rows, {llm.calls} model calls{note})", flush=True)


if __name__ == "__main__":
    main()
