"""Evaluate AI ICU recommendations against the patient's own records (records = gold standard).

Stages
  1. AI atomization   (deepseek-v4-pro:0813)  AI answer -> fact / action / goal atoms. Sees no records.
  2. Fact check       code for measurable facts (labs, vitals, ventilation status); the judge panel
                      for the rest, against pre-decision records.
  3. Action check     monitoring by code; treatments by code (rule-file class, named drug,
                      direction); the judge panel only for actions the rule file cannot classify.
  4. Coverage         treatment classes the clinicians used, graded vital / okay (problem-linked
                      when an indication was present at the decision time), vs. what the AI addressed.

Usage
  python run.py [--out-dir results] [--case M37067082] [--limit 5]

Model responses are kept in <out-dir>/model_cache.jsonl, so an interrupted run resumes by rerunning
the same command.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cm import atomize, concord, ground, records, report, rules
from cm.llm import LLM
from cm.panel import Panel
from cm.retrieve import Embedder, Retriever

ROOT = Path(__file__).resolve().parent


def prompt(name: str) -> str:
    return (ROOT / "prompts" / f"{name}.txt").read_text(encoding="utf-8")


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--triples", type=Path, default=ROOT / "input" / "mimic_triples_fixed.json")
    parser.add_argument("--mimic-root", type=Path, default=ROOT / "data" / "mimic-iv-demo")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results")
    parser.add_argument("--case", action="append", help="evaluate only these case ids")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--ai-model", default="deepseek-v4-pro:0813:cloud")
    parser.add_argument("--judge-models", default="deepseek-v4-pro:0813:cloud,minimax-m3.1-flash:cloud,glm-5.3:cloud",
                        help="comma-separated judge panel; the majority label wins")
    parser.add_argument("--judge-think", default="",
                        help="comma-separated judges that answer in reasoning mode ('' for none)")
    parser.add_argument("--cloud-workers", type=int, default=10,
                        help="requests sent at once to a :cloud judge (Ollama Max allows 10, Pay as you go / Pro 3; "
                             "the panel drops to 3 if the cloud refuses)")
    parser.add_argument("--retrieval", choices=["hybrid", "dense", "bm25"], default="hybrid")
    parser.add_argument("--top-n", type=int, default=50, help="reference facts retrieved per proposition")
    parser.add_argument("--facts-all-judge", action="store_true",
                        help="ablation: every fact goes to the judge panel (no code checks, rule labels or guard)")
    parser.add_argument("--labels", choices=["clinical_mark", "verifact"], default="clinical_mark",
                        help="fact labels: this project's four (with unverifiable) or VeriFact's three, with "
                             "prompts/fact_judge_vf.txt and VeriFact's definitions in the guard")
    parser.add_argument("--embeddings-dir", type=Path, default=ROOT / "embeddings",
                        help="bge-m3 vector cache; runs started at the same time each need their own copy")
    args = parser.parse_args()

    out = args.out_dir.resolve()
    for sub in ("atoms", "cases"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    llm = LLM(out / "model_cache.jsonl")
    judges = [m.strip() for m in args.judge_models.split(",") if m.strip()]
    triples = json.loads(args.triples.read_text(encoding="utf-8"))["triples"]
    triples = [t for t in triples if t["evaluation_eligibility"]["decision_within_icu_stay"] is True]
    if args.case:
        triples = [t for t in triples if t["triple_id"] in set(args.case)]
    if args.limit:
        triples = triples[:args.limit]
    started = time.time()

    # Stage 1: one model for every case, then free the GPU for the judges.
    atomizer_prompt = prompt("ai_atomizer")
    atoms_by_case, todo = {}, []
    for t in triples:
        path = out / "atoms" / f"{t['triple_id']}.json"
        if path.exists():
            atoms_by_case[t["triple_id"]] = json.loads(path.read_text(encoding="utf-8"))
        else:
            todo.append(t)
    # A cloud atomizer splits several cases at once (each request and its cached answer are unchanged).
    workers = max(1, args.cloud_workers) if args.ai_model.endswith(":cloud") else 1
    with ThreadPoolExecutor(max_workers=workers) as pool:
        split = pool.map(lambda t: (t, atomize.atomize(t, llm, args.ai_model, atomizer_prompt)), todo)
        for i, (t, atoms) in enumerate(split, len(atoms_by_case) + 1):
            write_json(out / "atoms" / f"{t['triple_id']}.json", atoms)
            atoms_by_case[t["triple_id"]] = atoms
            kinds = {k: sum(a["kind"] == k for a in atoms) for k in ("fact", "action", "goal")}
            print(f"[atomize {i}/{len(triples)}] {t['triple_id']} {kinds} ({time.time() - started:.0f}s)", flush=True)
    llm.unload(args.ai_model)
    for t in triples:
        claims = [{"claim_id": c["claim_id"], "text": c["text"]} for c in t["ai_generated"]["claims"]]
        atoms_by_case[t["triple_id"]] = atomize.safety_nets(atoms_by_case[t["triple_id"]], claims)

    # Stages 2-3: code decides what it can; everything else is queued for the judge panel.
    print("loading MIMIC: admission records before the decision, observations after it ...", flush=True)
    observations = records.load_post_observations(args.mimic_root.resolve(), triples)
    admission = records.load_admission_rows(args.mimic_root.resolve(), triples)
    embedder = Embedder(args.embeddings_dir.resolve()) if args.retrieval != "bm25" else None
    retriever = Retriever(embedder, args.retrieval, args.top_n)
    fact_prompt = prompt("fact_judge_vf" if args.labels == "verifact" else "fact_judge")
    action_prompt = prompt("action_judge")
    think = {m.strip() for m in args.judge_think.split(",") if m.strip()}
    panel = Panel(llm, judges, think, cloud_workers=args.cloud_workers)
    work = []
    for t in triples:
        case_id = t["triple_id"]
        pre = admission.get(case_id, [])
        doctor = records.postdecision_actions(t)
        decision = records.ts(t["decision_point"])
        icu_out = records.ts(t["evaluation_eligibility"].get("icu_outtime"))
        window_end = min(decision + dt.timedelta(days=1), icu_out or decision + dt.timedelta(days=1))
        window_hours = (window_end - decision).total_seconds() / 3600
        obs = observations.get(case_id, [])
        facts, actions = [], []
        for atom in atoms_by_case[case_id]:
            if atom["kind"] == "fact":
                facts.append((atom, ground.verify(atom, pre, t, fact_prompt, retriever, args.facts_all_judge,
                                                  args.labels)))
            elif atom["kind"] == "action":
                lab_order = atom["action_class"] == "order_test" and bool(rules.leaf_members(atom["concept"]))
                if atom["action_class"] in {"monitor", "assess"} or lab_order:
                    result = {**concord.check_monitoring(atom, obs, window_hours), "method": "rule"}
                    actions.append((atom, result, "monitoring"))
                else:
                    actions.append((atom, concord.check_treatment(atom, doctor, obs, action_prompt, case_id,
                                                                  window_hours), "treatment"))
        for _, result in facts:
            if "pending" in result:
                panel.submit(result["pending"])
        for _, result, _ in actions:
            if "pending" in result:
                panel.submit(result["pending"])
        work.append({"triple": t, "facts": facts, "actions": actions, "doctor": doctor, "window_hours": window_hours,
                     "gold": concord.gold_classes(doctor, pre, decision)})
    print(f"judge panel: {len(panel.requests)} items x {len(judges)} models {judges}", flush=True)
    panel.run()

    # Stage 4: finalize, coverage, metrics.
    cases = []
    for w in work:
        t = w["triple"]
        case_id = t["triple_id"]
        facts = [{**atom, **(ground.finalize(r, panel.verdict(r["pending"].key)) if "pending" in r else r)}
                 for atom, r in w["facts"]]
        actions = [{**atom, **(concord.finalize_treatment(r, panel.verdict(r["pending"].key)) if "pending" in r else r),
                    "track": track} for atom, r, track in w["actions"]]
        results = {a["atom_id"]: a for a in actions}
        atoms = atoms_by_case[case_id]
        cov = concord.coverage(w["gold"], atoms, results)
        cov3 = concord.coverage(w["gold"], atoms, results, max_claims=3)
        omitted_facts = concord.fact_omissions(w["gold"], facts)
        case = {"case_id": case_id, "decision_point": t["decision_point"],
                "claims": [c["text"] for c in t["ai_generated"]["claims"]],
                "atoms": atoms, "facts": facts, "actions": actions, "coverage": cov, "coverage_at3": cov3,
                "fact_omissions": omitted_facts,
                "doctor_actions_in_window": len(w["doctor"]), "observation_window_hours": round(w["window_hours"], 1),
                "scoresheet": report.scoresheet(facts),
                "metrics": report.case_metrics(facts, actions, cov, cov3, omitted_facts)}
        write_json(out / "cases" / f"{case_id}.json", case)
        cases.append(case)
        m = case["metrics"]
        print(f"[evaluate] {case_id} facts={len(facts)} not_supported={m['not_supported']} "
              f"treat_precision={m['treatment_precision']} vital_recall={m['recall_vital']}", flush=True)

    summary = report.summarize(cases)
    if embedder:
        embedder.save()
    meta = {"triples": args.triples.name, "ai_model": args.ai_model, "judge_models": judges,
            "facts_all_judge": args.facts_all_judge, "labels": args.labels,
            "judge_think": sorted(think), "retrieval": args.retrieval, "top_n": args.top_n,
            "llm_calls": llm.calls, "cache_hits": llm.cache_hits}
    write_json(out / "summary.json", {**summary, "run": meta})
    report.write_markdown(out / "report.md", summary, cases, meta)
    report.write_review_sheet(out / "review_sheet.csv", cases)
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
