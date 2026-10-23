"""Score the evaluator against clinician annotations, with the statistics VeriFact reports.

Ground truth per item: the adjudicated label if present, otherwise the majority of the annotators
(at least two agreeing). Items without a majority are listed for adjudication and left out.

Reported (VeriFact, Chung et al., NEJM AI 2026):
  - inter-annotator agreement: mean pairwise percent agreement and Gwet's AC1 (multi-rater);
  - evaluator vs ground truth: percent agreement, Gwet's AC1, Matthews correlation coefficient
    (multiclass), and per-label sensitivity / specificity / PPV / NPV;
  - also with labels binarized to supported vs not;
  - 95% confidence intervals from 1000 bootstrap resamples of cases;
  - strata by item type (fact / treatment / monitoring) and by how the machine decided
    (deterministic code, rule, judge panel).

Machine labels are mapped onto the annotators' three labels:
  fact:       supported, not_supported, not_addressed (unverifiable -> not_addressed)
  treatment:  match -> supported, partial_match -> not_supported, everything else -> not_addressed
  monitoring: performed -> supported, everything else -> not_addressed

Usage
  python score_annotations.py results_fixed annotation_set/annotations.csv --out annotation_set/validation_report.md
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

CLASSES = ("supported", "not_supported", "not_addressed")
TO_TRIAD = {
    "fact": {"supported": "supported", "not_supported": "not_supported"},
    "treatment": {"match": "supported", "partial_match": "not_supported"},
    "monitoring": {"performed": "supported"},
}
B = 1000
SEED = 20261012


def machine_triad(item_type: str, label: str) -> str:
    return TO_TRIAD[item_type].get(label, "not_addressed")


def gwet_ac1(ratings: list[list[str]], classes=CLASSES) -> float | None:
    """Gwet's AC1 for any number of raters per item (items with fewer than two ratings are skipped)."""
    items = [r for r in ratings if len(r) >= 2]
    if not items:
        return None
    q = len(classes)
    pa = sum(sum(n * (n - 1) for n in Counter(r).values()) / (len(r) * (len(r) - 1)) for r in items) / len(items)
    pi = {k: sum(Counter(r)[k] / len(r) for r in items) / len(items) for k in classes}
    pe = sum(p * (1 - p) for p in pi.values()) / (q - 1)
    return (pa - pe) / (1 - pe) if pe != 1 else None


def mcc(truth: list[str], pred: list[str], classes=CLASSES) -> float | None:
    """Multiclass Matthews correlation coefficient (Gorodkin)."""
    s = len(truth)
    if not s:
        return None
    c = sum(t == p for t, p in zip(truth, pred))
    t_k = Counter(truth)
    p_k = Counter(pred)
    num = c * s - sum(p_k[k] * t_k[k] for k in classes)
    den = math.sqrt((s * s - sum(p_k[k] ** 2 for k in classes)) * (s * s - sum(t_k[k] ** 2 for k in classes)))
    return num / den if den else None


def per_class(truth: list[str], pred: list[str], classes=CLASSES) -> dict:
    out = {}
    for k in classes:
        tp = sum(t == k and p == k for t, p in zip(truth, pred))
        fn = sum(t == k and p != k for t, p in zip(truth, pred))
        fp = sum(t != k and p == k for t, p in zip(truth, pred))
        tn = len(truth) - tp - fn - fp
        ratio = lambda a, b: a / b if b else None  # noqa: E731
        out[k] = {"n": tp + fn, "sensitivity": ratio(tp, tp + fn), "specificity": ratio(tn, tn + fp),
                  "ppv": ratio(tp, tp + fp), "npv": ratio(tn, tn + fn)}
    return out


def agreement_stats(pairs: list[tuple[str, str]], classes=CLASSES) -> dict:
    truth, pred = [t for t, _ in pairs], [p for _, p in pairs]
    return {"n": len(pairs),
            "percent_agreement": sum(t == p for t, p in pairs) / len(pairs) if pairs else None,
            "gwet_ac1": gwet_ac1([[t, p] for t, p in pairs], classes), "mcc": mcc(truth, pred, classes)}


def bootstrap(items: list[dict], fn, key: str) -> tuple[float | None, float | None]:
    by_case = defaultdict(list)
    for it in items:
        by_case[it["case_id"]].append(it)
    cases = sorted(by_case)
    rng = random.Random(SEED)
    values = []
    for _ in range(B):
        sample = [it for c in (rng.choice(cases) for _ in cases) for it in by_case[c]]
        v = fn(sample).get(key) if sample else None
        if v is not None:
            values.append(v)
    if not values:
        return None, None
    values.sort()
    return values[int(0.025 * len(values))], values[int(0.975 * len(values)) - 1]


def fmt(value, ci=None, percent=False) -> str:
    if value is None:
        return "-"
    text = f"{value * 100:.1f}%" if percent else f"{value:.2f}"
    if ci and ci[0] is not None:
        lo, hi = ci
        text += f" ({lo * 100:.1f}% to {hi * 100:.1f}%)" if percent else f" ({lo:.2f} to {hi:.2f})"
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("annotations", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    machine = {}
    for path in sorted((args.run / "cases").glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        for x in case["facts"]:
            machine[f"{case['case_id']}|{x['atom_id']}"] = ("fact", x["label"], x.get("method", "rule"))
        for x in case["actions"]:
            machine[f"{case['case_id']}|{x['atom_id']}"] = (x["track"], x["label"], x.get("method", "rule"))

    with args.annotations.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    items, unresolved, raters = [], [], []
    for row in rows:
        labels = [row[c].strip() for c in ("annotator_1", "annotator_2", "annotator_3") if row.get(c, "").strip()]
        bad = [lab for lab in labels + [row.get("adjudicated", "").strip()] if lab and lab not in CLASSES]
        if bad:
            raise ValueError(f"{row['item_id']}: unknown label(s) {bad}; use one of {CLASSES}")
        if len(labels) >= 2:
            raters.append(labels)
        truth = row.get("adjudicated", "").strip()
        if not truth and labels:
            label, n = Counter(labels).most_common(1)[0]
            truth = label if n >= 2 else ""
        if not truth:
            if labels:
                unresolved.append(row["item_id"])
            continue
        item_type, label, method = machine[row["item_id"]]
        items.append({"case_id": row["case_id"], "item_type": item_type, "method": method, "truth": truth,
                      "pred": machine_triad(item_type, label), "machine_label": label})

    lines = ["# Evaluator validation against clinician annotations", "",
             f"- Run: `{args.run}`; annotations: `{args.annotations}`",
             f"- Items with a ground-truth label: {len(items)}; awaiting adjudication: {len(unresolved)}; "
             f"cases: {len({i['case_id'] for i in items})}",
             f"- Confidence intervals: {B} bootstrap resamples of cases.", ""]
    if raters:
        pairwise = [a == b for r in raters for a, b in combinations(r, 2)]
        lines += ["## Inter-annotator agreement (the ceiling for the evaluator)", "",
                  f"Items with two or more annotators: {len(raters)}; mean pairwise percent agreement "
                  f"{fmt(sum(pairwise) / len(pairwise), percent=True)}; Gwet's AC1 {fmt(gwet_ac1(raters))}.", ""]
    if not items:
        lines.append("No item has a ground-truth label yet.")
        args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return

    def three(sample):
        return agreement_stats([(i["truth"], i["pred"]) for i in sample])

    def binary(sample):
        pairs = [(i["truth"] == "supported", i["pred"] == "supported") for i in sample]
        return agreement_stats([("supported" if t else "other", "supported" if p else "other") for t, p in pairs],
                               ("supported", "other"))

    lines += ["## Evaluator vs ground truth", "",
              "| Stratum | n | Percent agreement | Gwet's AC1 | MCC |", "|---|---|---|---|---|"]
    strata = [("all items (3 labels)", items, three), ("all items (supported vs not)", items, binary)]
    for key in ("item_type", "method"):
        for value in sorted({i[key] for i in items}):
            strata.append((f"{key} = {value}", [i for i in items if i[key] == value], three))
    for name, sample, fn in strata:
        st = fn(sample)
        lines.append(f"| {name} | {st['n']} | {fmt(st['percent_agreement'], bootstrap(sample, fn, 'percent_agreement'), True)} | "
                     f"{fmt(st['gwet_ac1'], bootstrap(sample, fn, 'gwet_ac1'))} | {fmt(st['mcc'], bootstrap(sample, fn, 'mcc'))} |")
    lines += ["", "## Per-label performance (all items)", "",
              "| Label | n (truth) | Sensitivity | Specificity | PPV | NPV |", "|---|---|---|---|---|---|"]
    for label, st in per_class([i["truth"] for i in items], [i["pred"] for i in items]).items():
        lines.append(f"| {label} | {st['n']} | {fmt(st['sensitivity'], percent=True)} | {fmt(st['specificity'], percent=True)} | "
                     f"{fmt(st['ppv'], percent=True)} | {fmt(st['npv'], percent=True)} |")
    confusion = Counter((i["truth"], i["pred"]) for i in items)
    lines += ["", "## Confusion matrix (rows: ground truth, columns: evaluator)", "",
              "| | " + " | ".join(CLASSES) + " |", "|---|" + "---|" * len(CLASSES)]
    for t in CLASSES:
        lines.append(f"| {t} | " + " | ".join(str(confusion[(t, p)]) for p in CLASSES) + " |")
    if unresolved:
        lines += ["", "## Awaiting adjudication", "", ", ".join(unresolved)]
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
