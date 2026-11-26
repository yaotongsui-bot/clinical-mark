"""Score fact verdicts on the 85 cases against a reference, with VeriFact's metrics (score_bhc.py).

Reference: a CSV with columns atom_id,label (supported | not_supported | not_addressed), or a run folder
(cases/*.json) whose fact labels are taken as the reference. Runs: a folder with verdicts.csv
(run_baseline85.py) or with cases/*.json (run.py). Only atoms present in the reference are scored.

This project's extra label `unverifiable` has no VeriFact counterpart; for the three-label metrics it is
counted as not_addressed (no verdict either way), and the number of such atoms is reported.

Usage
  python score_baseline85.py reference/fact_gold_claude.csv results_baseline85/vf_hybrid_nocut \
      results_baseline85/vf_hybrid_cut results_final_claude_split --out results_baseline85/score.md
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

import score_bhc as sb
from cm import verifact_bhc as vb

ROOT = Path(__file__).resolve().parent


def labels_of(path: Path) -> dict[str, str]:
    if path.is_file():
        with path.open(encoding="utf-8", newline="") as handle:
            return {r["atom_id"]: r["label"] for r in csv.DictReader(handle) if r.get("label")}
    if (path / "verdicts.csv").exists():
        return labels_of(path / "verdicts.csv")
    out = {}
    for case in sorted((path / "cases").glob("*.json")):
        for f in json.loads(case.read_text(encoding="utf-8"))["facts"]:
            out[f["atom_id"]] = f["label"]
    return out


def three(label: str) -> str:
    return "not_addressed" if label == "unverifiable" else label


def section(name: str, ref: dict[str, str], run: dict[str, str]) -> tuple[list[str], dict]:
    keys = sorted(k for k in ref if k in run and three(run[k]) in sb.CODE and ref[k] in sb.CODE)
    t = np.array([sb.CODE[ref[k]] for k in keys])
    p = np.array([sb.CODE[three(run[k])] for k in keys])
    c = sb.confusion_matrix(t, p)
    m = sb.metrics(c)
    ci = sb.bootstrap(t, p, ["agreement", "ac1", "mcc", "bin_agreement", "bin_ac1"])
    lines = [f"## {name}", "",
             f"- Scored {len(keys)} of {len(ref)} reference atoms; missing in the run: {len(set(ref) - set(run))}; "
             f"`unverifiable` counted as not addressed: {sum(run[k] == 'unverifiable' for k in keys)}.", "",
             "| Percent agreement | Gwet's AC1 | MCC | Binarized agreement | Binarized AC1 |", "|---|---|---|---|---|",
             f"| {sb.pct(m['agreement'], ci['agreement'])} | {sb.num(m['ac1'], ci['ac1'])} | {sb.num(m['mcc'], ci['mcc'])} | "
             f"{sb.pct(m['bin_agreement'], ci['bin_agreement'])} | {sb.num(m['bin_ac1'], ci['bin_ac1'])} |", "",
             "| Reference \\ run | " + " | ".join(vb.TO_VERIFACT[k] for k in vb.LABELS) + " | Sensitivity | PPV |",
             "|---" * (len(vb.LABELS) + 3) + "|"]
    for i, k in enumerate(vb.LABELS):
        pl = sb.per_label(c)[k]
        lines.append(f"| {vb.TO_VERIFACT[k]} | " + " | ".join(str(c[i, j]) for j in range(len(vb.LABELS))) +
                     f" | {sb.pct(pl['tpr'])} | {sb.pct(pl['ppv'])} |")
    return lines + [""], {k: run[k] for k in keys}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("reference", type=Path)
    p.add_argument("runs", nargs="+", type=Path)
    p.add_argument("--out", type=Path, default=ROOT / "results_baseline85" / "score.md")
    args = p.parse_args()
    ref = {k: v for k, v in labels_of(args.reference).items() if v in sb.CODE}
    lines = ["# Fact verdicts on the 85 cases against the reference", "",
             f"Reference: `{args.reference.as_posix()}` ({len(ref)} fact atoms). Metrics as in VeriFact's irr_metrics; "
             "95% CIs from 1000 bootstrap resamples of atoms.", ""]
    scored = {}
    for run in args.runs:
        block, scored[run.name] = section(run.name, ref, labels_of(run))
        lines += block
    names = list(scored)
    if len(names) >= 2:
        lines += ["## Paired differences in percent agreement (same atoms)", "",
                  "| Run A | Run B | A minus B (95% CI) | Only A right | Only B right |", "|---|---|---|---|---|"]
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                keys = sorted(set(scored[a]) & set(scored[b]))
                ra = np.array([three(scored[a][k]) == ref[k] for k in keys])
                rb = np.array([three(scored[b][k]) == ref[k] for k in keys])
                diffs = [ra[idx].mean() - rb[idx].mean() for idx in
                         (np.random.RandomState(s).choice(len(keys), size=len(keys), replace=True) for s in range(sb.B))]
                lines.append(f"| {a} | {b} | {(ra.mean() - rb.mean()) * 100:+.1f} "
                             f"({np.percentile(diffs, 2.5) * 100:+.1f} to {np.percentile(diffs, 97.5) * 100:+.1f}) | "
                             f"{(ra & ~rb).sum()} | {(~ra & rb).sum()} |")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
