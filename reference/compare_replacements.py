"""Compare replacements for glm-5.3 in the vote, on the base cases and on the 20 blind cases. Writes reference/replacement_comparison.md.

Blind 20 is scored twice: against the blind verdicts (revisions left out) and against the revised reference.
"""

from __future__ import annotations

from pathlib import Path

from compare_models import TIER, kappa, load

ROOT = Path(__file__).resolve().parents[1]
BASE = {"pro + minimax + glm-5.3": "results_final_claude_split", "pro + minimax + mimo": "results_final_claude_split_pro_minimax_mimo",
        "pro + minimax + flash": "results_final_claude_split_pro_minimax_flash"}
BLIND = {"pro + minimax + glm-5.3": "results_blind20/vote", "pro + minimax + mimo": "results_blind20/pro_minimax_mimo",
         "pro + minimax + flash": "results_blind20/pro_minimax_flash"}
CODE = {"supported": "positive", "not_supported": "negative", "not_addressed": "undetermined", "not_done": "negative"}


def items(path: str) -> dict[str, dict]:
    return {x["atom_id"]: x for c in load(ROOT / path).values() for x in c["facts"] + c["actions"]}


def row(name: str, ref: dict[str, str], run: dict[str, dict], keys: list[str]) -> str:
    pairs = [(ref[k], TIER[run[k]["label"]]) for k in keys]
    agree = sum(a == b for a, b in pairs) / len(pairs)
    false_ref = sum(a == "negative" for a, _ in pairs)
    found = sum(a == b == "negative" for a, b in pairs)
    flagged = sum(b == "negative" for _, b in pairs)
    agreement = [run[k].get("panel", {}).get("agreement") for k in keys]
    return f"| {name} | {len(keys)} | {agree:.1%} | {kappa(pairs):.2f} | {found}/{false_ref} | {flagged} | {found} | {agreement.count('3/3')} | {agreement.count('split')} |"


def table(title: str, ref: dict[str, str], runs: dict[str, str]) -> list[str]:
    loaded = {n: items(p) for n, p in runs.items()}
    keys = sorted(k for k, x in next(iter(loaded.values())).items() if x.get("method") == "llm_panel")
    return [f"## {title}", "", "| Vote | n | Agreement | Kappa | False facts found | Flagged false | Flags right | Unanimous | Split |", "|---|---|---|---|---|---|---|---|---|",
            *[row(n, ref, run, keys) for n, run in loaded.items()], ""]


def main() -> None:
    base_ref = {k: TIER[x["label"]] for k, x in items("results_reference/base").items()}
    revised = {k: TIER[x["label"]] for k, x in items("results_blind20/reference").items()}
    blind = dict(revised)
    for line in (ROOT / "reference" / "open_split" / "verdicts.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith(("fact:", "action:")):
            key, label = line.split("|")[:2]
            atom = key.split(":", 1)[1]
            if atom in blind and blind[atom] != TIER.get(label, blind[atom]) and label in TIER and key.startswith("fact:"):
                blind[atom] = TIER[label]
    lines = ["# Replacing glm-5.3 in the vote", "", "Items judged by a model. References are Claude's, not clinician truth.", ""]
    lines += table("Blind 20, blind verdicts", blind, BLIND) + table("Blind 20, revised verdicts", revised, BLIND) + table("Base 85 (reference revised after seeing earlier models)", base_ref, BASE)
    (ROOT / "reference" / "replacement_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
