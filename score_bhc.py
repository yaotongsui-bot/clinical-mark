"""Score run_bhc.py verdicts against the VeriFact-BHC clinician ground truth (human_gt), computed the
way VeriFact's irr_metrics package does (scripts/analysis_verifact/2_compute_verifact_metrics.py):

- Percent agreement: share of propositions where the rater equals human_gt.
- Gwet's AC1 (irrCAC, identity weights) on the two-rater table rater x human_gt; the categories are
  the labels that occur in that table, as irrCAC finds them when none are given.
- MCC (scikit-learn's multiclass formula) and per-label TPR / TNR / PPV / NPV from the confusion matrix.
- Binarized: "Supported" vs "Not Supported or Addressed" (irr_metrics.binarize).
- 95% CIs: 1000 bootstrap resamples of propositions; resample i takes the rows that pandas
  sample(frac=1, replace=True, random_state=i) takes, i.e. RandomState(i).choice(n, n); percentile
  interval. Agreement and AC1 resample the propositions in proposition_id order (the ratings-table
  columns); MCC and per-label metrics resample the merged rows in ground-truth file order.
- Strata: author_type x proposition_type (llm_claim, llm_sentence, human_claim, human_sentence).
Propositions without a valid verdict are left out, as VeriFact drops missing verdicts.
tests/test_bhc.py checks these formulas against irrCAC and scikit-learn when they are installed.

When a run used the released context, VeriFact's own verdicts on the same propositions are scored
too, with a paired bootstrap CI for the difference in agreement.

Usage
  python score_bhc.py results_bhc/vf_llama8b_replay [more run folders] --out results_bhc/score.md
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from cm import verifact_bhc as vb

ROOT = Path(__file__).resolve().parent
B = 1000
K = len(vb.LABELS)
CODE = {k: i for i, k in enumerate(vb.LABELS)}


def confusion_matrix(t: np.ndarray, p: np.ndarray) -> np.ndarray:
    """C[i, j] = number of items with truth i and rater j (label codes 0..K-1)."""
    return np.bincount(t * K + p, minlength=K * K).reshape(K, K)


def binarize_cm(c: np.ndarray) -> np.ndarray:
    """Supported vs Not Supported or Addressed (codes 1 and 2 merged)."""
    return np.array([[c[0, 0], c[0, 1:].sum()], [c[1:, 0].sum(), c[1:, 1:].sum()]])


def agreement(c: np.ndarray) -> float:
    return float(np.trace(c) / c.sum())


def gwet_ac1(c: np.ndarray) -> float | None:
    """irrCAC gwet() for two raters, identity weights, categories found in the data."""
    n = c.sum()
    marg = (c.sum(axis=0) + c.sum(axis=1)) / (2 * n)
    present = marg[marg > 0]
    q = len(present)
    pa = np.trace(c) / n
    if q < 2:
        return 1.0 if pa == 1 else None
    pe = float((present * (1 - present)).sum() / (q - 1))
    return float((pa - pe) / (1 - pe)) if pe != 1 else None


def mcc(c: np.ndarray) -> float:
    """sklearn.metrics.matthews_corrcoef (multiclass); 0.0 when undefined, as scikit-learn returns."""
    t_sum, p_sum = c.sum(axis=1), c.sum(axis=0)
    s, correct = c.sum(), np.trace(c)
    cov_ytyp = correct * s - (t_sum * p_sum).sum()
    cov_ypyp = s * s - (p_sum * p_sum).sum()
    cov_ytyt = s * s - (t_sum * t_sum).sum()
    den = float(cov_ytyt) * float(cov_ypyp)
    return float(cov_ytyp / math.sqrt(den)) if den else 0.0


def per_label(c: np.ndarray) -> dict:
    out = {}
    for i, k in enumerate(vb.LABELS):
        tp = c[i, i]
        fp, fn = c[:, i].sum() - tp, c[i, :].sum() - tp
        tn = c.sum() - tp - fp - fn
        r = lambda a, b: float(a / b) if b else float("nan")  # noqa: E731
        out[k] = {"support": int(tp + fn), "tpr": r(tp, tp + fn), "tnr": r(tn, tn + fp),
                  "ppv": r(tp, tp + fp), "npv": r(tn, tn + fn)}
    return out


def metrics(c: np.ndarray) -> dict:
    b = binarize_cm(c)
    out = {"agreement": agreement(c), "ac1": gwet_ac1(c), "mcc": mcc(c),
           "bin_agreement": agreement(b), "bin_ac1": gwet_ac1(b)}
    for k, v in per_label(c).items():
        out.update({f"{k}:{m}": v[m] for m in ("tpr", "tnr", "ppv", "npv")})
    return out


def bootstrap(t: np.ndarray, p: np.ndarray, keys: list[str]) -> dict[str, tuple[float | None, float | None]]:
    n = len(t)
    values = {k: [] for k in keys}
    for i in range(B):
        idx = np.random.RandomState(i).choice(n, size=n, replace=True)
        m = metrics(confusion_matrix(t[idx], p[idx]))
        for k in keys:
            if m[k] is not None and not math.isnan(m[k]):
                values[k].append(m[k])
    return {k: ((float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if v else (None, None))
            for k, v in values.items()}


def codes(df: pd.DataFrame, col: str) -> tuple[np.ndarray, np.ndarray]:
    return df["gt"].map(CODE).to_numpy(), df[col].map(CODE).to_numpy()


def summarize(df: pd.DataFrame, col: str) -> tuple[dict, dict]:
    """Point values and CIs; agreement-type metrics in proposition_id order, classification in gt order."""
    t_id, p_id = codes(df.sort_values("proposition_id"), col)
    t_gt, p_gt = codes(df.sort_values("gt_order"), col)
    point = metrics(confusion_matrix(t_gt, p_gt))
    ci = bootstrap(t_id, p_id, ["agreement", "ac1", "bin_agreement", "bin_ac1"])
    ci.update(bootstrap(t_gt, p_gt, ["mcc"] + [f"{k}:{m}" for k in vb.LABELS for m in ("tpr", "tnr", "ppv", "npv")]))
    return point, ci


def pct(v, ci=None) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "-"
    s = f"{v * 100:.1f}%"
    return s + (f" ({ci[0] * 100:.1f} to {ci[1] * 100:.1f})" if ci and ci[0] is not None else "")


def num(v, ci=None) -> str:
    if v is None:
        return "-"
    return f"{v:.3f}" + (f" ({ci[0]:.3f} to {ci[1]:.3f})" if ci and ci[0] is not None else "")


HEAD = ["| Stratum | n | Percent agreement (95% CI) | Gwet's AC1 (95% CI) | MCC (95% CI) | "
        "Binarized agreement (95% CI) | Binarized AC1 (95% CI) |", "|---|---|---|---|---|---|---|"]


def metric_row(df: pd.DataFrame, col: str, title: str) -> str:
    m, ci = summarize(df, col)
    return (f"| {title} | {len(df)} | {pct(m['agreement'], ci['agreement'])} | {num(m['ac1'], ci['ac1'])} | "
            f"{num(m['mcc'], ci['mcc'])} | {pct(m['bin_agreement'], ci['bin_agreement'])} | "
            f"{num(m['bin_ac1'], ci['bin_ac1'])} |")


def label_table(df: pd.DataFrame, col: str) -> list[str]:
    m, ci = summarize(df, col)
    support = per_label(confusion_matrix(*codes(df, col)))
    lines = ["| Label | Support | TPR (sensitivity) | TNR (specificity) | PPV | NPV |", "|---|---|---|---|---|---|"]
    for k in vb.LABELS:
        lines.append(f"| {vb.TO_VERIFACT[k]} | {support[k]['support']} | " +
                     " | ".join(pct(m[f'{k}:{x}'], ci[f'{k}:{x}']) for x in ("tpr", "tnr", "ppv", "npv")) + " |")
    return lines


def confusion_table(df: pd.DataFrame, col: str) -> list[str]:
    c = confusion_matrix(*codes(df, col))
    lines = ["| human_gt \\ rater | " + " | ".join(vb.TO_VERIFACT[k] for k in vb.LABELS) + " |",
             "|---" * (K + 1) + "|"]
    for i, t in enumerate(vb.LABELS):
        lines.append(f"| {vb.TO_VERIFACT[t]} | " + " | ".join(str(c[i, j]) for j in range(K)) + " |")
    return lines


def report_run(run: Path, gt: pd.DataFrame) -> list[str]:
    df = pd.read_csv(run / "verdicts.csv", dtype=str, keep_default_na=False)
    meta = json.loads((run / "run.json").read_text(encoding="utf-8")) if (run / "run.json").exists() else {}
    total = len(df)
    df = df.merge(gt, on="proposition_id", how="inner")
    valid = df["label"].isin(vb.LABELS)
    if "agreement" in df:
        valid &= df["agreement"] != "invalid"
    df = df[valid]
    has_vf = "verifact_label" in df and len(df) > 0 and df["verifact_label"].isin(vb.LABELS).all()
    lines = [f"## {run.name}", "",
             f"- Judge style `{meta.get('judge_style', '?')}`; context `{meta.get('context', '?')}`; "
             f"judges {meta.get('judges', '?')}"
             f"{' (reasoning: ' + meta['judge_think'] + ')' if meta.get('judge_think') else ''}.",
             f"- Scored {len(df)} of {total} propositions ({df['subject_id'].nunique()} subjects); "
             f"left out: no valid verdict or no ground truth.",
             f"- Panel splits (fallback Not Addressed): {(df['agreement'] == 'split').sum()}.", ""]
    if meta.get("context") == "released":
        lines.insert(3, f"- Released context and baseline: {meta.get('source_model')}, {meta.get('retrieval_method')}, "
                        f"N={meta.get('source_top_n')}, {meta.get('reference_format')}, "
                        f"{'current admission' if meta.get('admission_only') else 'whole EHR'}.")
        if has_vf:
            lines.insert(4, f"- Same verdict as the released {meta.get('source_model')} verdict: "
                            f"{(df['label'] == df['verifact_label']).mean():.1%}.")
    raters = [("label", "This run")] + ([("verifact_label", f"VeriFact released {meta.get('source_model', '')}")]
                                        if has_vf else [])
    for col, name in raters:
        lines += [f"### {name}", "", *HEAD, metric_row(df, col, "all_samples")]
        for (author, ptype), g in df.groupby(["author_type", "proposition_type"]):
            lines.append(metric_row(g, col, f"{author}_{ptype}"))
        lines += ["", *label_table(df, col), "", *confusion_table(df, col), ""]
    if has_vf:
        by_id = df.sort_values("proposition_id")
        right = (by_id["label"] == by_id["gt"]).to_numpy()
        vright = (by_id["verifact_label"] == by_id["gt"]).to_numpy()
        diffs = []
        for i in range(B):
            idx = np.random.RandomState(i).choice(len(right), size=len(right), replace=True)
            diffs.append(right[idx].mean() - vright[idx].mean())
        lo, hi = np.percentile(diffs, 2.5), np.percentile(diffs, 97.5)
        lines += ["### Difference (this run minus VeriFact, same propositions and context)", "",
                  f"- Percent agreement: {(right.mean() - vright.mean()) * 100:+.1f} points "
                  f"(95% CI {lo * 100:+.1f} to {hi * 100:+.1f}).",
                  f"- Both right {(right & vright).sum()}, only this run {(right & ~vright).sum()}, "
                  f"only VeriFact {(~right & vright).sum()}, neither {(~right & ~vright).sum()}.", ""]
    return lines


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("runs", nargs="+", type=Path)
    p.add_argument("--release-dir", type=Path)
    p.add_argument("--out", type=Path, default=ROOT / "results_bhc" / "score.md")
    args = p.parse_args()
    gt = vb.load_ground_truth(vb.release_dir(args.release_dir, ROOT))[["proposition_id", "label"]]
    gt = gt.rename(columns={"label": "gt"}).assign(gt_order=range(len(gt)))
    lines = ["# VeriFact-BHC: agreement with the clinician ground truth", "",
             "Ground truth: `human_gt` in propositions/human_verdicts.csv.gz. Metrics as in VeriFact's "
             "irr_metrics: percent agreement, Gwet's AC1, MCC, per-label TPR / TNR / PPV / NPV; binarized = "
             "Supported vs Not Supported or Addressed; 95% CIs from 1000 bootstrap resamples of propositions.", ""]
    for run in args.runs:
        lines += report_run(run.resolve(), gt)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
