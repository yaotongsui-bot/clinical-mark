"""Compare the three-model vote on Claude's split (results_final_claude_split) with Claude's reference verdicts.

Both runs use the same atoms and records, so items match by atom id. Writes reference/final_comparison.md and
reference/final_disagreements.csv.
"""

from __future__ import annotations

import collections
import csv
import json
import random
from pathlib import Path

from compare_models import TIER, kappa, load

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "results_final_claude_split"
REF = ROOT / "results_reference" / "base"


def items(cases: dict) -> dict[str, dict]:
    return {x["atom_id"]: x for c in cases.values() for x in c["facts"] + c["actions"]}


def line(name: str, keys: list[str], ref: dict, run: dict) -> str:
    pairs = [(TIER[ref[k]["label"]], TIER[run[k]["label"]]) for k in keys]
    by_case = collections.defaultdict(list)
    for k, (a, b) in zip(keys, pairs):
        by_case[k.split("A")[0]].append(a == b)
    cases = sorted(by_case)
    rng = random.Random(0)
    boots = sorted(sum(v for c in rng.choices(cases, k=len(cases)) for v in by_case[c]) / max(1, sum(len(by_case[c]) for c in cases)) for _ in range(1))
    draws = []
    for _ in range(2000):
        draw = [v for c in rng.choices(cases, k=len(cases)) for v in by_case[c]]
        draws.append(sum(draw) / len(draw))
    draws.sort()
    agree = sum(a == b for a, b in pairs) / len(pairs)
    false_ref = sum(a == "negative" for a, _ in pairs)
    found = sum(a == b == "negative" for a, b in pairs)
    flagged = sum(b == "negative" for _, b in pairs)
    return f"| {name} | {len(keys)} | {agree:.1%} ({draws[50]:.1%} to {draws[1949]:.1%}) | {kappa(pairs):.2f} | {found}/{false_ref} | {flagged} | {found} |"


def main() -> None:
    ref_cases, run_cases = load(REF), load(RUN)
    ref, run = items(ref_cases), items(run_cases)
    assert set(ref) == set(run), "the two runs should score the same atoms"
    keys = sorted(ref)
    judged = [k for k in keys if run[k].get("method") == "llm_panel"]
    facts = [k for k in keys if run[k]["kind"] == "fact"]
    actions = [k for k in keys if run[k]["kind"] == "action"]
    summary = json.loads((RUN / "summary.json").read_text(encoding="utf-8"))
    ref_summary = json.loads((REF / "summary.json").read_text(encoding="utf-8"))
    agreement = collections.Counter(str(run[k].get("panel", {}).get("agreement")) for k in judged)
    lines = ["# Three-model vote on Claude's split", "",
             "Atoms: reference/split_standard.csv. Judges: deepseek-v4-pro:0813, deepseek-v4.1-flash, mimo-v2.6-pro. "
             "Reference verdicts are Claude's and were revised once after seeing earlier model disagreements, so agreement may lean high.", "",
             "| Items | n | Agreement (95% CI) | Kappa | False facts found | Flagged false | Flags right |", "|---|---|---|---|---|---|---|",
             line("All", keys, ref, run), line("Facts", facts, ref, run), line("Actions", actions, ref, run), line("Judged by the vote", judged, ref, run), "",
             f"Vote on judged items: {dict(agreement)}.", "",
             "| Result | Vote | Reference |", "|---|---|---|",
             f"| Fact accuracy | {summary['facts']['accuracy']:.1%} | {ref_summary['facts']['accuracy']:.1%} |",
             f"| False facts | {summary['facts']['labels']['not_supported']} | {ref_summary['facts']['labels']['not_supported']} |",
             f"| Cases with a false fact | {summary['facts']['cases_with_not_supported']} | {ref_summary['facts']['cases_with_not_supported']} |",
             f"| Treatment agreement | {summary['treatment_actions']['precision_lenient']:.1%} | {ref_summary['treatment_actions']['precision_lenient']:.1%} |",
             f"| Key treatment recall | {summary['coverage']['vital']['micro']:.1%} | {ref_summary['coverage']['vital']['micro']:.1%} |"]
    (ROOT / "reference" / "final_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (ROOT / "reference" / "final_disagreements.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["atom_id", "text", "reference", "vote", "method", "votes", "vote_reason", "reference_reason"])
        for k in keys:
            if TIER[ref[k]["label"]] != TIER[run[k]["label"]]:
                writer.writerow([k, run[k]["text"], ref[k]["label"], run[k]["label"], run[k].get("method"), json.dumps(run[k].get("panel", {}).get("votes", {})),
                                 run[k].get("reason"), ref[k].get("reason")])
    print("\n".join(lines))


if __name__ == "__main__":
    main()
