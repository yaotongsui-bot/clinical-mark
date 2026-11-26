"""Compare the three-model vote with Claude's blind verdicts on the 20 test cases. Writes reference/blind20_comparison.md
and reference/blind20_disagreements.csv. Reference verdicts were written before any model judged these items."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from compare_models import TIER, kappa, load

ROOT = Path(__file__).resolve().parents[1]
SINGLE = ["deepseek-v4-pro:0813:cloud", "minimax-m3.1-flash:cloud", "glm-5.3:cloud"]


def items(path: Path) -> dict[str, dict]:
    return {x["atom_id"]: x for c in load(path).values() for x in c["facts"] + c["actions"]}


def row(name: str, pairs: list[tuple[str, str]], ci: str = "") -> str:
    agree = sum(a == b for a, b in pairs) / len(pairs)
    false_ref = sum(a == "negative" for a, _ in pairs)
    found = sum(a == b == "negative" for a, b in pairs)
    flagged = sum(b == "negative" for _, b in pairs)
    return f"| {name} | {len(pairs)} | {agree:.1%}{ci} | {kappa(pairs):.2f} | {found}/{false_ref} | {flagged} | {found} |"


def main() -> None:
    ref, vote = items(ROOT / "results_blind20" / "reference"), items(ROOT / "results_blind20" / "vote")
    assert set(ref) == set(vote)
    keys = sorted(ref)
    judged = [k for k in keys if vote[k].get("method") == "llm_panel"]
    by_case: dict[str, list[str]] = {}
    for k in judged:
        by_case.setdefault(k.split("A")[0], []).append(k)
    rng = random.Random(0)
    right = {k: TIER[ref[k]["label"]] == TIER[vote[k]["label"]] for k in judged}
    boots = []
    for _ in range(2000):
        draw = [k for c in rng.choices(sorted(by_case), k=len(by_case)) for k in by_case[c]]
        boots.append(sum(right[k] for k in draw) / len(draw))
    boots.sort()
    pair = lambda ks: [(TIER[ref[k]["label"]], TIER[vote[k]["label"]]) for k in ks]
    lines = ["# Blind test: 20 up-to-10-claim cases", "", "Claude wrote the split and the verdicts before any model judged these items. The judges are "
             "deepseek-v4-pro:0813, minimax-m3.1-flash and glm-5.3. Not clinician truth.", "",
             "| Items | n | Agreement (95% CI by case) | Kappa | False facts found | Flagged false | Flags right |", "|---|---|---|---|---|---|---|",
             row("All", pair(keys)), row("Facts", pair([k for k in keys if vote[k]["kind"] == "fact"])), row("Actions", pair([k for k in keys if vote[k]["kind"] == "action"])),
             row("Judged by the vote", pair(judged), f" ({boots[50]:.1%} to {boots[1949]:.1%})"), "", "## Single judges, before the code guard", "",
             "| Judge | n | Agreement | Kappa | False facts found | Flagged false | Flags right |", "|---|---|---|---|---|---|---|"]
    raw = lambda x: x.get("panel", {}).get("panel_label") or x["label"]
    for m in SINGLE:
        pairs = [(TIER[raw(ref[k])], TIER[vote[k]["panel"]["votes"][m]]) for k in judged if vote[k]["panel"]["votes"].get(m) in TIER]
        lines.append(row(m.replace(":cloud", ""), pairs))
    agreement = [vote[k]["panel"]["agreement"] for k in judged]
    lines += ["", f"Unanimous {agreement.count('3/3')}, two to one {agreement.count('2/3')}, split {agreement.count('split')}."]
    (ROOT / "reference" / "blind20_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (ROOT / "reference" / "blind20_disagreements.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["atom_id", "text", "reference", "vote", "votes", "vote_reason", "reference_reason"])
        for k in keys:
            if TIER[ref[k]["label"]] != TIER[vote[k]["label"]]:
                writer.writerow([k, vote[k]["text"], ref[k]["label"], vote[k]["label"], json.dumps(vote[k].get("panel", {}).get("votes", {})), vote[k].get("reason"), ref[k].get("reason")])
    print("\n".join(lines))


if __name__ == "__main__":
    main()
