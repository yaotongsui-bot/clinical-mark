"""Score splitting prompts and models against Claude's split standards (85 base cases and the 20 blind cases).

    python reference/try_splitter.py run <model> <prompt name>     split all 105 cases; answers cached in results_split_trial
    python reference/try_splitter.py score                         write reference/split_trial.md
"""

from __future__ import annotations

import collections
import glob
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "reference"))
from cm import atomize  # noqa: E402
from cm.llm import LLM  # noqa: E402
from compare_splits import aligned, by_key  # noqa: E402

TRIAL = ROOT / "results_split_trial"
PLAN = json.loads((ROOT / "reference" / "open_split" / "sample_plan.json").read_text(encoding="utf-8"))
TRIPLE_SETS = {"base": ROOT / "input" / "mimic_triples_deepseek.json", "blind20": ROOT / "reference" / "open_split" / "triples_blind20.json"}
STANDARD = {"base": ROOT / "results_reference" / "base", "blind20": ROOT / "results_blind20" / "reference"}


def triples(group: str) -> list[dict]:
    rows = json.loads(TRIPLE_SETS[group].read_text(encoding="utf-8"))["triples"]
    return [t for t in rows if t["evaluation_eligibility"]["decision_within_icu_stay"] is True and t["ai_generated"]]


def with_nets(atoms: list[dict], triple: dict) -> list[dict]:
    claims = [{"claim_id": c["claim_id"], "text": c["text"]} for c in triple["ai_generated"]["claims"]]
    return atomize.safety_nets(atoms, claims)


def run(model: str, prompt_name: str) -> None:
    system = (ROOT / "prompts" / f"{prompt_name}.txt").read_text(encoding="utf-8")
    folder = TRIAL / f"{model.replace(':', '_')}__{prompt_name}"
    folder.mkdir(parents=True, exist_ok=True)
    llm = LLM(folder / "model_cache.jsonl")
    for group in TRIPLE_SETS:
        rows = triples(group)
        with ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(lambda t: (t, atomize.atomize(t, llm, f"{model}:cloud", system)), rows))
        out = {t["triple_id"]: with_nets(atoms, t) for t, atoms in results}
        (folder / f"{group}.json").write_text(json.dumps(out, ensure_ascii=False) + "\n", encoding="utf-8")
        print(model, prompt_name, group, sum(map(len, out.values())), flush=True)


def standard(group: str) -> dict[str, list[dict]]:
    return {Path(f).stem: json.loads(Path(f).read_text(encoding="utf-8"))["atoms"] for f in glob.glob(str(STANDARD[group] / "cases" / "*.json"))}


def old_runs(model: str) -> dict[str, dict]:
    name = model.replace(":", "_")
    base = {Path(f).stem: json.loads(Path(f).read_text(encoding="utf-8"))["atoms"] for f in glob.glob(str(ROOT / "results_models" / name / "cases" / "*.json"))}
    blind = {}
    for p in PLAN:
        path = ROOT / "results_models_open" / f"s{p['sample']}" / name / "cases" / f"{p['case']}.json"
        blind[p["case"]] = json.loads(path.read_text(encoding="utf-8"))["atoms"]
    return {"base": base, "blind20": blind}


def score_group(std: dict, run_: dict) -> tuple:
    kinds = collections.Counter(a["kind"] for rows in std.values() for a in rows)
    total = sum(kinds.values())
    size = hits = 0
    per = collections.Counter()
    for cid, rows in std.items():
        got = run_[cid]
        size += len(got)
        h, p = aligned(by_key(rows), by_key(got))
        hits += h
        per.update(p)
    return size, hits / size, hits / total, 2 * hits / (size + total), per["fact"] / kinds["fact"], per["action"] / kinds["action"]


def score() -> None:
    lines = ["# Splitting prompts against the standards", "", "Standards: Claude's split of the 85 base cases and of the 20 blind cases. Matching is by wording, so absolute numbers lean low.", "",
             "| Group | Model | Prompt | Atoms | Precision | Recall | F1 | Facts found | Actions found |", "|---|---|---|---|---|---|---|---|---|"]
    models = ["deepseek-v4-pro:0813", "muse-spark-open"]
    for group in STANDARD:
        std = standard(group)
        lines.append(f"| {group} | standard | - | {sum(map(len, std.values()))} | | | | | |")
        for model in models:
            s = score_group(std, old_runs(model)[group])
            lines.append(f"| {group} | {model} | current | {s[0]} | {s[1]:.1%} | {s[2]:.1%} | {s[3]:.3f} | {s[4]:.1%} | {s[5]:.1%} |")
            path = TRIAL / f"{model.replace(':', '_')}__ai_atomizer_v2" / f"{group}.json"
            if path.exists():
                s = score_group(std, json.loads(path.read_text(encoding="utf-8")))
                lines.append(f"| {group} | {model} | v2 | {s[0]} | {s[1]:.1%} | {s[2]:.1%} | {s[3]:.3f} | {s[4]:.1%} | {s[5]:.1%} |")
    (ROOT / "reference" / "split_trial.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(sys.argv[2], sys.argv[3])
    else:
        score()
