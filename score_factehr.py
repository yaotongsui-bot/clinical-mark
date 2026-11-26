"""Score the FactEHR baseline on the eICU test set against the frozen reference, next to the runs it is
compared with (run_factehr.py).

FactEHR has two labels (1 = entailed, 0 = not), so it is scored two ways:
  1. As the analysis plan scores every run: three labels; a sentence is wrong if any of its facts is Not
     Supported. FactEHR's 0 counts as Not Supported (its prompt: "the hypothesis contains information
     that cannot be entailed by the premise").
  2. Binary, for every run: Supported vs not (Not Supported and Not Addressed merged, in the reference and
     in each run); a sentence is wrong if any of its facts is not Supported. This removes the cost to
     FactEHR of having no Not Addressed label.
Runs are read from results_eicu_dx/ (records with the case header rows), first run of each judge, as in
results_eicu_dx/SCORES.md. 95% CIs from 1000 bootstrap resamples of cases.

Usage
  python score_factehr.py [--results results_eicu_dx] [--out results_eicu_dx/FACTEHR.md]
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

import score_bhc as sb
from score_baseline85 import labels_of, three
from score_eicu import GENERATORS, ROOT, Scored, fmt, frozen_ok, index, paired

RUNS = {
    "ours_vote": "ClinicalMark: code checks + cloud vote (deepseek-v4-pro, minimax-m3.1-flash, glm-5.3)",
    "ours_pro": "ClinicalMark: code checks + deepseek-v4-pro judge",
    "vf_pro_cut": "VeriFact: retrieval (top 50) + deepseek-v4-pro judge, records cut at T",
    "fe_pro_cut": "FactEHR: whole record before T + deepseek-v4-pro entailment judge, no retrieval",
}
PAIRS = [("ours_vote", "fe_pro_cut"), ("ours_pro", "fe_pro_cut"), ("vf_pro_cut", "fe_pro_cut")]


def binary(label: str) -> str:
    """Supported vs not: Not Addressed (and this project's `unverifiable`) merged into Not Supported."""
    return "supported" if three(label) == "supported" else "not_supported"


def point(sc: Scored, t, p, st, sp, binary_scheme: bool) -> dict:
    a = sb.metrics(sb.confusion_matrix(t, p))
    s = sb.metrics(sb.confusion_matrix(st, sp))
    return {"sent_agreement": s["agreement"], "sent_ac1": s["bin_ac1"],
            "sent_sens": s["not_supported:tpr"], "sent_ppv": s["not_supported:ppv"],
            "atom_agreement": a["agreement"],
            # With merged labels one of the three codes is empty; AC1 is then taken over two categories.
            "atom_ac1": a["bin_ac1"] if binary_scheme else a["ac1"], "atom_mcc": a["mcc"],
            "atom_sens": a["not_supported:tpr"], "atom_ppv": a["not_supported:ppv"]}


def bootstrap(sc: Scored, cases: list[str], binary_scheme: bool) -> dict[str, tuple]:
    vals = defaultdict(list)
    for i in range(sb.B):
        draw = np.random.RandomState(i).choice(cases, size=len(cases), replace=True)
        for k, v in point(sc, *sc.subset(draw), binary_scheme).items():
            if v is not None and not np.isnan(v):
                vals[k].append(v)
    return {k: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) for k, v in vals.items()}


def table(rows) -> list[str]:
    out = ["| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | "
           "Atoms | Atom agreement | Atom AC1 | Atom MCC |", "|---" * 10 + "|"]
    for name, sc, m, ci in rows:
        out.append(f"| {name} | {len(sc.sent_ids)} | {fmt(m['sent_agreement'], ci.get('sent_agreement'))} | "
                   f"{fmt(m['sent_ac1'], ci.get('sent_ac1'), False)} | {fmt(m['sent_sens'], ci.get('sent_sens'))} | "
                   f"{fmt(m['sent_ppv'], ci.get('sent_ppv'))} | {len(sc.keys)} | "
                   f"{fmt(m['atom_agreement'], ci.get('atom_agreement'))} | "
                   f"{fmt(m['atom_ac1'], ci.get('atom_ac1'), False)} | {fmt(m['atom_mcc'], ci.get('atom_mcc'), False)} |")
    return out


def prompt_tokens(results: Path, gens: list[str]) -> list[int]:
    out = []
    for g in gens:
        cache = results / g / "fe_pro_cut" / "model_cache.jsonl"
        if cache.exists():
            for line in cache.read_text(encoding="utf-8").splitlines():
                n = json.loads(line).get("prompt_tokens")
                if n:
                    out.append(int(n))
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--reference", type=Path,
                   default=ROOT / "reference" / "fact_gold_eicu" / "fact_gold_eicu_claude.frozen.csv")
    p.add_argument("--results", type=Path, default=ROOT / "results_eicu_dx")
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--generators", nargs="+", default=None,
                   help="answer sets to score (default: those with a finished FactEHR run); every run is scored "
                        "on the same answer sets")
    args = p.parse_args()
    out_path = args.out or args.results / "FACTEHR.md"
    if not frozen_ok(args.reference):
        raise SystemExit(f"{args.reference} does not match FROZEN.sha256")
    gens = args.generators or [g for g in GENERATORS if (args.results / g / "fe_pro_cut" / "verdicts.csv").exists()]
    if not gens:
        raise SystemExit("no finished FactEHR run")
    with args.reference.open(encoding="utf-8", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["generator"] in gens]
    ref = {r["key"]: r["label"] for r in rows}
    kind = {r["key"]: r.get("fact_kind", "") for r in rows}
    case_of = {r["key"]: r["case_id"] for r in rows}
    cases = sorted({r["case_id"] for r in rows})
    labels = {run: {f"{g}|{k}": v for g in gens for k, v in labels_of(args.results / g / run).items()}
              for run in RUNS}

    numbers: dict = {}
    scored: dict = {}
    lines = ["# eICU test set: FactEHR entailment judge as a second baseline", "",
             f"Runs: `{args.results.resolve().relative_to(ROOT).as_posix()}/` (records with the case header rows; "
             "first run of each judge). Reference: the frozen test reference "
             f"(`{args.reference.relative_to(ROOT).as_posix()}`, checksum matches): {len(ref)} fact atoms in "
             f"{len(cases)} cases. 95% CIs from 1000 bootstrap resamples of cases.", "",
             f"Answer sets scored: {', '.join(gens)}" + ("" if len(gens) == len(GENERATORS) else
             f" (not {', '.join(g for g in GENERATORS if g not in gens)}: no FactEHR run; every run is scored on "
             "the same answer sets, so the numbers differ from SCORES.md)") + ".", "",
             "Every run judges the same fact atoms; only the fact checking differs. All three single-judge runs "
             "use deepseek-v4-pro.", ""]
    lines += [f"- `{r}`: {d}" for r, d in RUNS.items()] + [""]
    toks = prompt_tokens(args.results, gens)
    fe = labels["fe_pro_cut"]
    no_verdict = sum(1 for k in ref if k not in fe)
    if toks:
        lines += [f"FactEHR coverage: {len(ref) - no_verdict} of {len(ref)} reference atoms have a verdict. Prompt "
                  f"size per call: median {int(np.median(toks)):,} tokens, largest {max(toks):,} (context window set "
                  f"to 131,072, so no record was cut); {sum(toks):,} prompt tokens over {len(toks)} calls.", ""]
    for scheme, title, note in (
            (False, "Scoring 1: three labels, as in the analysis plan",
             "FactEHR's 0 counts as Not Supported. A sentence is wrong if any of its facts is Not Supported."),
            (True, "Scoring 2: binary for every run (Supported vs not)",
             "Not Supported and Not Addressed merged in the reference and in every run. A sentence is wrong if "
             "any of its facts is not Supported.")):
        r_use = {k: binary(v) for k, v in ref.items()} if scheme else ref
        tag = "binary" if scheme else "three"
        scored[tag] = {}
        block = []
        for run in RUNS:
            run_labels = {k: binary(v) for k, v in labels[run].items()} if scheme else labels[run]
            sc = Scored(r_use, case_of, run_labels)
            index(sc)
            m = point(sc, sc.t, sc.p, sc.st, sc.sp, scheme)
            ci = bootstrap(sc, cases, scheme)
            scored[tag][run] = sc
            numbers[f"{tag}/{run}"] = {"point": m, "ci": ci, "atoms": len(sc.keys), "sentences": len(sc.sent_ids)}
            block.append((run, sc, m, ci))
        lines += [f"## {title}", "", note, ""] + table(block) + [""]
        per = ["| Run | " + " | ".join(gens) + " |", "|---" * (len(gens) + 1) + "|"]
        for run in RUNS:
            cells = []
            for g in gens:
                sub = {k: v for k, v in r_use.items() if k.startswith(g + "|")}
                run_labels = {k: binary(v) for k, v in labels[run].items()} if scheme else labels[run]
                sc = Scored(sub, case_of, run_labels)
                m = sb.metrics(sb.confusion_matrix(sc.st, sc.sp))
                cells.append(f"{m['agreement'] * 100:.1f}%")
                numbers[f"{tag}/{g}/{run}/sent_agreement"] = m["agreement"]
            per.append(f"| {run} | " + " | ".join(cells) + " |")
        lines += ["Sentence agreement by answer set:", ""] + per + [""]
        lines += ["Paired differences (same items, case bootstrap):", "",
                  "| A | B | Sentence agreement A minus B (95% CI) | Only A right / only B right | "
                  "Atom agreement A minus B (95% CI) | Only A right / only B right |", "|---" * 6 + "|"]
        for a, b in PAIRS:
            s = paired(scored[tag][a], scored[tag][b], cases, "sent")
            t = paired(scored[tag][a], scored[tag][b], cases, "atom")
            lines.append(f"| {a} | {b} | {s[0] * 100:+.1f} ({s[1] * 100:+.1f} to {s[2] * 100:+.1f}) | {s[3]} / {s[4]} | "
                         f"{t[0] * 100:+.1f} ({t[1] * 100:+.1f} to {t[2] * 100:+.1f}) | {t[3]} / {t[4]} |")
            numbers[f"{tag}/paired/{a}-{b}"] = {"sentence": s, "atom": t}
        lines.append("")

    # Where the runs differ: atom verdicts against the reference, by reference label and by fact kind.
    lines += ["## Atom verdicts by reference label", "",
              "| Run | Reference Supported: flagged Not Supported | Reference Not Supported: found | "
              "Reference Not Addressed: called Supported |", "|---" * 4 + "|"]
    n_lab = Counter(ref.values())
    for run in RUNS:
        got = {k: three(labels[run][k]) for k in ref if k in labels[run]}
        fp = sum(1 for k, v in got.items() if ref[k] == "supported" and v == "not_supported")
        tp = sum(1 for k, v in got.items() if ref[k] == "not_supported" and v == "not_supported")
        na = sum(1 for k, v in got.items() if ref[k] == "not_addressed" and v == "supported")
        lines.append(f"| {run} | {fp} of {n_lab['supported']} | {tp} of {n_lab['not_supported']} | "
                     f"{na} of {n_lab['not_addressed']} |")
        numbers[f"by_label/{run}"] = {"false_flags": fp, "found": tp, "na_called_supported": na}
    kinds = sorted({v for v in kind.values() if v})
    if kinds:
        lines += ["", "FactEHR false flags (reference Supported, FactEHR Not Supported) by fact kind:", "",
                  "| Fact kind | Reference Supported | FactEHR flagged | VeriFact flagged | ClinicalMark vote flagged |",
                  "|---" * 5 + "|"]
        for kd in kinds:
            keys = [k for k in ref if kind[k] == kd and ref[k] == "supported"]
            flags = [sum(1 for k in keys if three(labels[r].get(k, "")) == "not_supported")
                     for r in ("fe_pro_cut", "vf_pro_cut", "ours_vote")]
            lines.append(f"| {kd} | {len(keys)} | " + " | ".join(str(f) for f in flags) + " |")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out_path.with_suffix(".json").write_text(json.dumps(numbers, indent=1) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
