"""Pool several evaluation runs (samples of the same AI) and report metrics with 95% bootstrap CIs.

Cases are resampled with replacement (the same case set for every sample in a bootstrap round),
so the interval reflects both case-to-case and sample-to-sample variation.

Usage
  python summarize_samples.py results_open_s1 results_open_s2 results_open_s3 \
      --baseline results_fixed --out results_open_summary.md
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

B = 1000
SEED = 20261011


def load(run: Path) -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((run / "cases").glob("*.json"))}


def _ratio(num: float, den: float) -> float | None:
    return num / den if den else None


def _recall(cases: list[dict], key: str, tier: str | None) -> float | None:
    rows = [g for c in cases for g in c[key] if tier is None or g["importance"] == tier]
    return _ratio(sum(g["covered"] for g in rows), len(rows))


def _treatment(cases: list[dict], labels: set[str]) -> int:
    return sum(a["label"] in labels for c in cases for a in c["actions"] if a["track"] == "treatment")


# (name, is_percentage, metric over a list of case results)
METRICS = [
    ("AI suggestions per case", False, lambda cs: _ratio(sum(len(c["claims"]) for c in cs), len(cs))),
    ("Fact accuracy", True, lambda cs: _ratio(
        sum(f["label"] == "supported" for c in cs for f in c["facts"]),
        sum(f["label"] in {"supported", "not_supported"} for c in cs for f in c["facts"]))),
    ("not_supported facts per case", False, lambda cs: _ratio(
        sum(f["label"] == "not_supported" for c in cs for f in c["facts"]), len(cs))),
    ("Cases with a not_supported fact", True, lambda cs: _ratio(
        sum(any(f["label"] == "not_supported" for f in c["facts"]) for c in cs), len(cs))),
    ("Treatment agreement (strict)", True, lambda cs: _ratio(
        _treatment(cs, {"match"}), _treatment(cs, {"match", "partial_match", "not_done"}))),
    # The reported verdicts are four tiers per item: a partial match (same aim, other drug or direction) agrees.
    ("Treatment agreement (partial counts as agreeing)", True, lambda cs: _ratio(
        _treatment(cs, {"match", "partial_match"}), _treatment(cs, {"match", "partial_match", "not_done"}))),
    ("Vital recall", True, lambda cs: _recall(cs, "coverage", "vital")),
    ("Vital recall, first 3 suggestions", True, lambda cs: _recall(cs, "coverage_at3", "vital")),
    ("All recall", True, lambda cs: _recall(cs, "coverage", None)),
    ("All recall, first 3 suggestions", True, lambda cs: _recall(cs, "coverage_at3", None)),
]


def interval(samples: list[dict[str, dict]], metric) -> tuple[float | None, float | None, float | None]:
    ids = sorted(set.intersection(*(set(s) for s in samples)))
    point = metric([s[i] for s in samples for i in ids])
    rng = random.Random(SEED)
    stats = []
    for _ in range(B):
        pick = [rng.choice(ids) for _ in ids]
        value = metric([s[i] for s in samples for i in pick])
        if value is not None:
            stats.append(value)
    stats.sort()
    if not stats:
        return point, None, None
    return point, stats[int(0.025 * len(stats))], stats[int(0.975 * len(stats)) - 1]


def fmt(percent: bool, value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.1f}%" if percent else f"{value:.2f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", nargs="+", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    samples = [load(r) for r in args.runs]
    base = load(args.baseline) if args.baseline else None
    head = ["Metric", f"Pooled samples ({len(samples)}, 95% CI)"] + [r.name for r in args.runs]
    if base:
        head.append(f"Baseline {args.baseline.name} (95% CI)")
    lines = ["# Pooled samples", "",
             f"{B} bootstrap resamples of cases (all samples share the resampled case set).", "",
             "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for name, percent, metric in METRICS:
        point, lo, hi = interval(samples, metric)
        row = [name, f"{fmt(percent, point)} ({fmt(percent, lo)} to {fmt(percent, hi)})"]
        row += [fmt(percent, metric(list(s.values()))) for s in samples]
        if base:
            bp, blo, bhi = interval([base], metric)
            row.append(f"{fmt(percent, bp)} ({fmt(percent, blo)} to {fmt(percent, bhi)})")
        lines.append("| " + " | ".join(row) + " |")
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
