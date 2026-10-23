"""Compare two evaluation runs (e.g. before / after the input fix) and write a Markdown summary.

Usage
  python compare_runs.py results results_fixed --out results_fixed/comparison.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(run: Path) -> tuple[dict, dict[str, dict]]:
    summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    cases = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((run / "cases").glob("*.json"))}
    return summary, cases


def pct(value) -> str:
    return "-" if value is None else f"{value * 100:.1f}%"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    (sa, ca), (sb, cb) = load(args.before), load(args.after)
    fa, fb = sa["facts"], sb["facts"]
    labels = ("supported", "not_supported", "not_addressed", "unverifiable")

    def row(name, a, b):
        return f"| {name} | {a} | {b} |"

    lines = [
        f"# Run comparison: `{args.before.name}` -> `{args.after.name}`", "",
        f"| Metric | {args.before.name} | {args.after.name} |", "|---|---|---|",
        row("Fact atoms", fa["n"], fb["n"]),
        row(" / ".join(labels), " / ".join(str(fa["labels"].get(k, 0)) for k in labels),
            " / ".join(str(fb["labels"].get(k, 0)) for k in labels)),
        row("Fact accuracy", pct(fa["accuracy"]), pct(fb["accuracy"])),
        row("Cases with a not_supported fact", fa["cases_with_not_supported"], fb["cases_with_not_supported"]),
        row("Treatment agreement (strict)", pct(sa["treatment_actions"]["precision_strict"]),
            pct(sb["treatment_actions"]["precision_strict"])),
        row("Monitoring performed rate", pct(sa["monitoring_actions"]["performed_rate"]),
            pct(sb["monitoring_actions"]["performed_rate"])),
        row("Vital recall", pct(sa["coverage"]["vital"]["micro"]), pct(sb["coverage"]["vital"]["micro"])),
        row("All recall", pct(sa["coverage"]["all"]["micro"]), pct(sb["coverage"]["all"]["micro"])),
    ]
    changed = [cid for cid in sorted(set(ca) & set(cb)) if ca[cid]["claims"] != cb[cid]["claims"]]
    lines += ["", "## Cases whose AI answer changed", "",
              f"{len(changed)} of {len(set(ca) & set(cb))} AI answers changed. The generator is not fully reproducible "
              "even with an identical prompt (2 of 4 old prompts reproduced the old answer), so changes in single cases "
              "cannot all be attributed to the input repair; compare the aggregate metrics.", "",
              "| Case | Before | After | not_supported before -> after |", "|---|---|---|---|"]
    for cid in changed:
        before, after = ca[cid], cb[cid]
        lines.append(f"| {cid} | {'<br>'.join(before['claims'])} | {'<br>'.join(after['claims'])} | "
                     f"{before['metrics']['not_supported']} -> {after['metrics']['not_supported']} |")
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main()
