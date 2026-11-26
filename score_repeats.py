"""Repeat spread on the eICU test set: the same setups run three times (CLINICAL_MARK_REPEAT=1..3, seed
shifted per repeat, temperature unchanged), scored against the frozen reference.

For each setup: sentence and atom agreement in each repeat, their mean (95% CI from 1000 case bootstraps of
the three-repeat mean) and range, and how many atoms and sentences got a different verdict in at least one
repeat. For the method comparisons: the sentence-agreement difference in each repeat and its three-repeat
mean with a case-bootstrap CI.

Usage
  python score_repeats.py results_eicu_dx results_eicu_dx_r2 results_eicu_dx_r3 --out results_eicu_dx/REPEATS.md
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

import score_bhc as sb
from score_baseline85 import labels_of, three
from score_eicu import GENERATORS, PAIRS, RUNS, frozen_ok, sentence

ROOT = Path(__file__).resolve().parent
NS = sb.CODE["not_supported"]


def load(root: Path, run: str) -> dict[str, str]:
    out = {}
    for g in GENERATORS:
        out.update({f"{g}|{k}": three(v) for k, v in labels_of(root / g / run).items()})
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("roots", nargs="+", type=Path, help="one results root per repeat, repeat 1 first")
    p.add_argument("--reference", type=Path,
                   default=ROOT / "reference" / "fact_gold_eicu" / "fact_gold_eicu_claude.frozen.csv")
    p.add_argument("--out", type=Path, default=ROOT / "results_eicu_dx" / "REPEATS.md")
    p.add_argument("--runs", nargs="+", default=list(RUNS), help="setups to score (default: all)")
    args = p.parse_args()
    runs = {r: RUNS[r] for r in args.runs}
    pairs = [(a, b) for a, b in PAIRS if a in runs and b in runs]
    if not frozen_ok(args.reference):
        raise SystemExit(f"{args.reference} does not match FROZEN.sha256")
    with args.reference.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ref = {r["key"]: r["label"] for r in rows}
    keys = sorted(ref)
    case_of = {r["key"]: r["case_id"] for r in rows}
    cases = sorted(set(case_of.values()))
    sents = sorted({sentence(k) for k in keys})
    sent_atoms = defaultdict(list)
    for i, k in enumerate(keys):
        sent_atoms[sentence(k)].append(i)
    sent_case = [case_of[keys[sent_atoms[s][0]]] for s in sents]
    atom_by_case, sent_by_case = defaultdict(list), defaultdict(list)
    for i, k in enumerate(keys):
        atom_by_case[case_of[k]].append(i)
    for i, c in enumerate(sent_case):
        sent_by_case[c].append(i)
    t_atom = np.array([sb.CODE[ref[k]] for k in keys])
    t_sent = np.array([NS if (t_atom[sent_atoms[s]] == NS).any() else 0 for s in sents])
    draws = [np.random.RandomState(i).choice(cases, size=len(cases), replace=True) for i in range(sb.B)]
    draw_atoms = [np.concatenate([atom_by_case[c] for c in d]) for d in draws]
    draw_sents = [np.concatenate([sent_by_case[c] for c in d]) for d in draws]

    right_sent, right_atom, flags = {}, {}, {}
    for run in runs:
        rs, ra, fl, preds = [], [], [], []
        for root in args.roots:
            lab = load(root, run)
            missing = [k for k in keys if k not in lab]
            if missing:
                raise SystemExit(f"{root}/{run}: {len(missing)} atoms without a verdict")
            pa = np.array([sb.CODE[lab[k]] for k in keys])
            ps = np.array([NS if (pa[sent_atoms[s]] == NS).any() else 0 for s in sents])
            preds.append((pa, ps))
            ra.append(pa == t_atom)
            rs.append(ps == t_sent)
            fl.append(((pa == NS) & (t_atom == NS)).sum() / max(1, (t_atom == NS).sum()))
        right_sent[run], right_atom[run], flags[run] = np.array(rs), np.array(ra), fl
        right_sent[run + ":preds"] = preds

    def mean_ci(mat: np.ndarray, draw_idx: list[np.ndarray]) -> tuple[float, float, float]:
        point = float(mat.mean())
        boot = [float(mat[:, idx].mean()) for idx in draw_idx]
        return point, float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))

    n = len(args.roots)
    lines = ["# eICU test set: spread over repeats", "",
             f"Repeats: {', '.join(f'`{r.as_posix()}`' for r in args.roots)} (repeat 1 first). Same atoms, records, "
             "retrieval and judge settings; each repeat shifts the seed of every model request "
             "(`CLINICAL_MARK_REPEAT`), so every request is sent again. Judges at temperature 0 (all of the "
             "evaluator's) repeat only the serving's own variation; VeriFact's judge samples at temperature 0.1. "
             f"Frozen reference, {len(keys)} atoms, {len(sents)} sentences. CIs: 1000 case bootstraps of the "
             f"{n}-repeat mean.", "",
             "## Agreement per repeat", "",
             "| Run | Sentence agreement by repeat | Mean (95% CI) | Range | Atom agreement by repeat | Mean | "
             "Not Supported found, mean | Atoms with any changed verdict | Sentences with any changed verdict |",
             "|---" * 9 + "|"]
    numbers = {}
    for run in runs:
        s, a = right_sent[run], right_atom[run]
        preds = right_sent[run + ":preds"]
        atom_unstable = sum(1 for i in range(len(keys)) if len({int(pp[0][i]) for pp in preds}) > 1)
        sent_unstable = sum(1 for i in range(len(sents)) if len({int(pp[1][i]) for pp in preds}) > 1)
        sm, slo, shi = mean_ci(s, draw_sents)
        am = float(a.mean())
        per_s = [float(x.mean()) for x in s]
        per_a = [float(x.mean()) for x in a]
        numbers[run] = {"sentence": per_s, "atom": per_a, "sentence_mean_ci": [sm, slo, shi],
                        "ns_found": [float(x) for x in flags[run]], "atoms_changed": atom_unstable,
                        "sentences_changed": sent_unstable}
        lines.append(f"| {run} | {' / '.join(f'{x * 100:.1f}' for x in per_s)} | {sm * 100:.1f}% ({slo * 100:.1f} to "
                     f"{shi * 100:.1f}) | {(max(per_s) - min(per_s)) * 100:.1f} | "
                     f"{' / '.join(f'{x * 100:.1f}' for x in per_a)} | {am * 100:.1f}% | "
                     f"{np.mean(flags[run]) * 100:.1f}% | {atom_unstable} ({atom_unstable / len(keys) * 100:.1f}%) | "
                     f"{sent_unstable} ({sent_unstable / len(sents) * 100:.1f}%) |")
    lines += ["", "## Method comparisons over repeats (sentence agreement, A minus B)", "",
              "| A | B | By repeat | Mean of repeats (95% CI) |", "|---|---|---|---|"]
    for a_run, b_run in pairs:
        d = right_sent[a_run].astype(float) - right_sent[b_run].astype(float)
        per = [float(x.mean()) for x in d]
        m, lo, hi = mean_ci(d, draw_sents)
        numbers[f"{a_run}-{b_run}"] = {"by_repeat": per, "mean_ci": [m, lo, hi]}
        lines.append(f"| {a_run} | {b_run} | {' / '.join(f'{x * 100:+.1f}' for x in per)} | "
                     f"{m * 100:+.1f} ({lo * 100:+.1f} to {hi * 100:+.1f}) |")
    lines += ["", "Runs:", ""] + [f"- `{r}`: {d}" for r, d in runs.items()]
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    args.out.with_suffix(".json").write_text(json.dumps(numbers, indent=1) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
