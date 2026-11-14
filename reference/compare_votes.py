"""Compare three-model votes on Claude's split with Claude's reference verdicts. Writes reference/vote_comparison.md.

Same atoms and records in every run, so items match by atom id. Single-model rows use each judge's own vote, before the
code guard, against the reference label before the guard.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from compare_models import TIER, kappa, load

ROOT = Path(__file__).resolve().parents[1]
RUNS = {"pro + minimax + glm-5.3": "results_final_claude_split", "pro + flash + mimo": "results_final_claude_split_pro_flash_mimo",
        "pro + mimo + glm-5.3": "results_final_claude_split_pro_mimo_glm"}
SINGLE = ["deepseek-v4-pro:0813:cloud", "mimo-v2.6-pro:cloud", "deepseek-v4.1-flash:cloud", "minimax-m3.1-flash:cloud", "glm-5.3:cloud"]


def items(path: str) -> dict[str, dict]:
    return {x["atom_id"]: x for c in load(ROOT / path).values() for x in c["facts"] + c["actions"]}


def row(pairs: list[tuple[str, str]]) -> tuple:
    agree = sum(a == b for a, b in pairs) / len(pairs)
    false_ref = sum(a == "negative" for a, _ in pairs)
    found = sum(a == b == "negative" for a, b in pairs)
    flagged = sum(b == "negative" for _, b in pairs)
    return len(pairs), agree, kappa(pairs), found, false_ref, flagged


def main() -> None:
    ref = items("results_reference/base")
    runs = {n: items(p) for n, p in RUNS.items()}
    judged = sorted(k for k, x in next(iter(runs.values())).items() if x.get("method") == "llm_panel")
    lines = ["# Votes on Claude's split", "", f"{len(judged)} items judged by a model, 85 cases. The reference is Claude's and was revised after seeing earlier model "
             "disagreements, so absolute agreement leans high.", "", "| Vote | Agreement (95% CI) | Kappa | False facts found | Flagged false | Flags right | Unanimous | Split |", "|---|---|---|---|---|---|---|---|"]
    by_case: dict[str, list[str]] = {}
    for k in judged:
        by_case.setdefault(k.split("A")[0], []).append(k)
    cases = sorted(by_case)
    rng = random.Random(0)
    draws = [[k for c in rng.choices(cases, k=len(cases)) for k in by_case[c]] for _ in range(2000)]
    right = {n: {k: TIER[run[k]["label"]] == TIER[ref[k]["label"]] for k in judged} for n, run in runs.items()}
    for n, run in runs.items():
        pairs = [(TIER[ref[k]["label"]], TIER[run[k]["label"]]) for k in judged]
        size, agree, kap, found, false_ref, flagged = row(pairs)
        boots = sorted(sum(right[n][k] for k in d) / len(d) for d in draws)
        agreement = [run[k].get("panel", {}).get("agreement") for k in judged]
        lines.append(f"| {n} | {agree:.1%} ({boots[50]:.1%} to {boots[1949]:.1%}) | {kap:.2f} | {found}/{false_ref} | {flagged} | {found} | {agreement.count('3/3')} | {agreement.count('split')} |")
    names = list(runs)
    lines += ["", "## Differences between votes (agreement points, 95% CI)", ""]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            d = sorted(sum(right[a][k] - right[b][k] for k in s) / len(s) for s in draws)
            lines.append(f"- {a} minus {b}: {sum(right[a].values()) / len(judged) - sum(right[b].values()) / len(judged):+.1%} ({d[50]:+.1%} to {d[1949]:+.1%})")
    lines += ["", "## Single judges, before the code guard", "", "| Judge | Agreement | Kappa | False facts found | Flagged false | Flags right |", "|---|---|---|---|---|---|"]
    raw = lambda x: x.get("panel", {}).get("panel_label") or x["label"]
    pooled = {k: {m: v for run in runs.values() for m, v in run[k].get("panel", {}).get("votes", {}).items()} for k in judged}
    for m in SINGLE:
        pairs = [(TIER[raw(ref[k])], TIER[pooled[k][m]]) for k in judged if pooled[k].get(m) in TIER]
        size, agree, kap, found, false_ref, flagged = row(pairs)
        lines.append(f"| {m.replace(':cloud', '')} | {agree:.1%} | {kap:.2f} | {found}/{false_ref} | {flagged} | {found} |")
    (ROOT / "reference" / "vote_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    for n in runs:
        s = json.loads((ROOT / RUNS[n] / "summary.json").read_text(encoding="utf-8"))
        print(n, s["run"]["llm_calls"], s["facts"]["accuracy"], s["facts"]["labels"], s["facts"]["cases_with_not_supported"], s["treatment_actions"]["precision_lenient"], s["coverage"]["vital"]["micro"])


if __name__ == "__main__":
    main()
