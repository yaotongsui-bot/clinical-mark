"""Score the eICU test runs against the frozen test reference (PAPER_PLAN.md, analysis plan).

Primary: percent agreement at the sentence level. A sentence (one suggestion, atom ids
`<case>A<n>::...`) is wrong if any of its fact atoms is Not Supported; the run's sentence verdict is
built the same way from its atom verdicts. Secondary, at the atom level: percent agreement over the
three VeriFact labels, Gwet's AC1, MCC, and sensitivity and PPV for Not Supported. 95% CIs from 1000
bootstrap resamples of cases (all atoms of a drawn case, for every answer set, go in together).

This project's extra label `unverifiable` counts as Not Addressed, as in score_baseline85.py.

Usage
  python score_eicu.py [--reference reference/fact_gold_eicu/fact_gold_eicu_claude.frozen.csv]
      [--out results_eicu/SCORES.md]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

import score_bhc as sb
from score_baseline85 import labels_of, three

ROOT = Path(__file__).resolve().parent
GENERATORS = ("gpt-oss-120b", "deepseek-v4.1-flash", "qwen2.5-7b")
RUNS = {  # folder: description
    "ours_vote": "Evaluator, cloud vote (deepseek-v4-pro, minimax-m3.1-flash, glm-5.3)",
    "ours_pro": "Evaluator, deepseek-v4-pro judge",
    "vf_pro_cut": "VeriFact, deepseek-v4-pro judge, records cut at T",
    "ours_llama": "Evaluator, llama3.1:8b judge",
    "ours_llama_alljudge": "Evaluator, llama3.1:8b judge, every fact to the judge (no code checks)",
    "vf_llama_cut": "VeriFact, llama3.1:8b judge, records cut at T",
    "vf_llama_nocut": "VeriFact, llama3.1:8b judge, all records (as published)",
}
PAIRS = [  # same judge, method compared; then ablations
    ("ours_pro", "vf_pro_cut"), ("ours_llama", "vf_llama_cut"), ("ours_vote", "vf_pro_cut"),
    ("ours_llama", "ours_llama_alljudge"), ("ours_llama_alljudge", "vf_llama_cut"),
    ("vf_llama_cut", "vf_llama_nocut"), ("ours_vote", "ours_pro"), ("ours_pro", "ours_llama"),
]
S, NS = sb.CODE["supported"], sb.CODE["not_supported"]


def frozen_ok(path: Path) -> bool:
    """The frozen copy must carry the checksum recorded for the reference in FROZEN.sha256."""
    listed = {}
    for line in (path.parent / "FROZEN.sha256").read_text(encoding="utf-8").splitlines():
        digest, name = line.split(maxsplit=1)
        listed[Path(name.lstrip("*")).name] = digest
    return hashlib.sha256(path.read_bytes()).hexdigest() == listed.get("fact_gold_eicu_claude.csv")


def sentence(key: str) -> str:
    return key.split("::")[0]


class Scored:
    """Reference and run labels on the shared keys, with the case of each key and each sentence."""

    def __init__(self, ref: dict[str, str], case_of: dict[str, str], run: dict[str, str]):
        self.keys = sorted(k for k in ref if k in run)
        self.missing = len(ref) - len(self.keys)
        self.unverifiable = sum(run[k] == "unverifiable" for k in self.keys)
        self.t = np.array([sb.CODE[ref[k]] for k in self.keys])
        self.p = np.array([sb.CODE[three(run[k])] for k in self.keys])
        self.case = np.array([case_of[k] for k in self.keys])
        sents = defaultdict(list)
        for i, k in enumerate(self.keys):
            sents[sentence(k)].append(i)
        self.sent_ids = sorted(sents)
        self.st = np.array([NS if (self.t[sents[s]] == NS).any() else S for s in self.sent_ids])
        self.sp = np.array([NS if (self.p[sents[s]] == NS).any() else S for s in self.sent_ids])
        self.sent_case = np.array([case_of[self.keys[sents[s][0]]] for s in self.sent_ids])

    def subset(self, cases: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Atom and sentence indices for a bootstrap draw of cases (with repeats)."""
        atom_idx = np.concatenate([CASE_INDEX[id(self)][0].get(c, EMPTY) for c in cases])
        sent_idx = np.concatenate([CASE_INDEX[id(self)][1].get(c, EMPTY) for c in cases])
        return self.t[atom_idx], self.p[atom_idx], self.st[sent_idx], self.sp[sent_idx]


EMPTY = np.array([], dtype=int)
CASE_INDEX: dict[int, tuple[dict, dict]] = {}


def index(sc: Scored) -> None:
    by_case_atoms, by_case_sents = defaultdict(list), defaultdict(list)
    for i, c in enumerate(sc.case):
        by_case_atoms[c].append(i)
    for i, c in enumerate(sc.sent_case):
        by_case_sents[c].append(i)
    CASE_INDEX[id(sc)] = ({c: np.array(v) for c, v in by_case_atoms.items()},
                          {c: np.array(v) for c, v in by_case_sents.items()})


def point(t, p, st, sp) -> dict:
    a = sb.metrics(sb.confusion_matrix(t, p))
    s = sb.metrics(sb.confusion_matrix(st, sp))
    return {"sent_agreement": s["agreement"], "sent_ac1": s["bin_ac1"],
            "sent_sens": s["not_supported:tpr"], "sent_ppv": s["not_supported:ppv"],
            "atom_agreement": a["agreement"], "atom_ac1": a["ac1"], "atom_mcc": a["mcc"],
            "atom_sens": a["not_supported:tpr"], "atom_ppv": a["not_supported:ppv"]}


def bootstrap(sc: Scored, cases: list[str]) -> dict[str, tuple]:
    vals = defaultdict(list)
    for i in range(sb.B):
        draw = np.random.RandomState(i).choice(cases, size=len(cases), replace=True)
        for k, v in point(*sc.subset(draw)).items():
            if v is not None and not np.isnan(v):
                vals[k].append(v)
    return {k: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) for k, v in vals.items()}


def paired(a: Scored, b: Scored, cases: list[str], level: str) -> tuple[float, float, float, int, int]:
    """A minus B in percent agreement on the shared items, case bootstrap; counts of items only one got right."""
    if level == "sent":
        ka, kb = dict(zip(a.sent_ids, range(len(a.sent_ids)))), dict(zip(b.sent_ids, range(len(b.sent_ids))))
        shared = sorted(set(ka) & set(kb))
        ra = np.array([a.st[ka[s]] == a.sp[ka[s]] for s in shared])
        rb = np.array([b.st[kb[s]] == b.sp[kb[s]] for s in shared])
        case = np.array([a.sent_case[ka[s]] for s in shared])
    else:
        ka, kb = dict(zip(a.keys, range(len(a.keys)))), dict(zip(b.keys, range(len(b.keys))))
        shared = sorted(set(ka) & set(kb))
        ra = np.array([a.t[ka[k]] == a.p[ka[k]] for k in shared])
        rb = np.array([b.t[kb[k]] == b.p[kb[k]] for k in shared])
        case = np.array([a.case[ka[k]] for k in shared])
    by_case = defaultdict(list)
    for i, c in enumerate(case):
        by_case[c].append(i)
    diffs = []
    for i in range(sb.B):
        draw = np.random.RandomState(i).choice(cases, size=len(cases), replace=True)
        idx = np.concatenate([np.array(by_case.get(c, []), dtype=int) for c in draw])
        if len(idx):
            diffs.append(ra[idx].mean() - rb[idx].mean())
    return (float(ra.mean() - rb.mean()), float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5)),
            int((ra & ~rb).sum()), int((~ra & rb).sum()))


def fmt(v, ci=None, pct=True) -> str:
    return sb.pct(v, ci) if pct else sb.num(v, ci)


def table(rows: list[tuple[str, Scored, dict, dict]]) -> list[str]:
    out = ["| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | "
           "Atoms | Atom agreement | Atom AC1 | Atom MCC | Not Supported found | Not Supported PPV |",
           "|---" * 12 + "|"]
    for name, sc, m, ci in rows:
        out.append(f"| {name} | {len(sc.sent_ids)} | {fmt(m['sent_agreement'], ci.get('sent_agreement'))} | "
                   f"{fmt(m['sent_ac1'], ci.get('sent_ac1'), False)} | {fmt(m['sent_sens'], ci.get('sent_sens'))} | "
                   f"{fmt(m['sent_ppv'], ci.get('sent_ppv'))} | {len(sc.keys)} | "
                   f"{fmt(m['atom_agreement'], ci.get('atom_agreement'))} | {fmt(m['atom_ac1'], ci.get('atom_ac1'), False)} | "
                   f"{fmt(m['atom_mcc'], ci.get('atom_mcc'), False)} | {fmt(m['atom_sens'], ci.get('atom_sens'))} | "
                   f"{fmt(m['atom_ppv'], ci.get('atom_ppv'))} |")
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--reference", type=Path,
                   default=ROOT / "reference" / "fact_gold_eicu" / "fact_gold_eicu_claude.frozen.csv")
    p.add_argument("--results", type=Path, default=ROOT / "results_eicu")
    p.add_argument("--out", type=Path, default=ROOT / "results_eicu" / "SCORES.md")
    args = p.parse_args()
    if not frozen_ok(args.reference):
        raise SystemExit(f"{args.reference} does not match FROZEN.sha256")
    with args.reference.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ref = {r["key"]: r["label"] for r in rows}
    case_of = {r["key"]: r["case_id"] for r in rows}
    cases = sorted({r["case_id"] for r in rows})

    scored: dict[str, dict[str, Scored]] = {}
    for run in RUNS:
        merged = {}
        for g in GENERATORS:
            labels = labels_of(args.results / g / run)
            merged.update({f"{g}|{k}": v for k, v in labels.items()})
        scored[run] = {"all": Scored(ref, case_of, merged)}
        for g in GENERATORS:
            sub = {k: v for k, v in ref.items() if k.startswith(g + "|")}
            scored[run][g] = Scored(sub, case_of, merged)
        for sc in scored[run].values():
            index(sc)

    n_sent = len({sentence(k) for k in ref})
    ref_wrong = sum(1 for s in {sentence(k) for k in ref}
                    if any(ref[k] == "not_supported" for k in ref if sentence(k) == s))
    lines = ["# eICU test set: fact verdicts against the frozen reference", "",
             f"Runs: `{args.results.resolve().relative_to(ROOT).as_posix()}/`.", "",
             f"Reference: `{args.reference.relative_to(ROOT).as_posix()}` (checksum matches `FROZEN.sha256`): "
             f"{len(ref)} fact atoms in {len(cases)} cases, {n_sent} sentences ({ref_wrong} wrong: at least one "
             "Not Supported fact). Written by Claude before any test output was read; the clinician check of "
             "20 cases is still to come.", "",
             "Primary metric (PAPER_PLAN.md): sentence agreement, where a sentence is wrong if any of its facts is "
             "Not Supported. Secondary: atom-level agreement over the three labels, Gwet's AC1, MCC, and "
             "sensitivity (found) and PPV for Not Supported. 95% CIs from 1000 bootstrap resamples of cases. "
             "`unverifiable` counts as Not Addressed. Each sampled judge was run once (the plan's three "
             "repeats are not done).", ""]
    numbers = {}
    for group in ("all",) + GENERATORS:
        title = "All three answer sets" if group == "all" else f"Answers from {group}"
        block = []
        for run, desc in RUNS.items():
            sc = scored[run][group]
            m = point(sc.t, sc.p, sc.st, sc.sp)
            ci = bootstrap(sc, cases)
            numbers[f"{group}/{run}"] = {"point": m, "ci": ci, "atoms": len(sc.keys), "sentences": len(sc.sent_ids),
                                         "missing": sc.missing, "unverifiable": sc.unverifiable}
            block.append((run, sc, m, ci))
        lines += [f"## {title}", ""] + table(block) + [""]
        if group == "all":
            notes = [f"`{run}`: {sc.missing} reference atoms missing from the run, {sc.unverifiable} `unverifiable`"
                     for run, sc, _, _ in block if sc.missing or sc.unverifiable]
            lines += ["Coverage: " + ("; ".join(notes) if notes else "every run has a verdict for every atom.") + "",
                      ""]
    # Sensitivity: the case header (unit type, APACHE admission diagnosis) was in the reference sheets but
    # is not among the rows cm/records_eicu.py gives the systems; rule 7 of the guideline was added while
    # labelling. Rescore without the atoms whose reference label rests on either.
    header = {r["key"] for r in rows if "dmission diagnosis" in r["evidence"] or "Unit type" in r["evidence"]}
    rule7 = {r["key"] for r in rows if "intermittent" in (r["note"] + r["evidence"]).lower()} - header
    for title, drop in ((f"Sensitivity: without the {len(header)} atoms whose reference evidence is the admission "
                         "diagnosis or unit type (case header, not in the systems' records)", header),
                        (f"Sensitivity: also without the {len(rule7)} atoms decided by guideline rule 7 (intermittent "
                         "drugs documented in the treatment table count as given)", header | rule7)):
        sub = {k: v for k, v in ref.items() if k not in drop}
        block = []
        for run in RUNS:
            merged = {}
            for g in GENERATORS:
                merged.update({f"{g}|{k}": v for k, v in labels_of(args.results / g / run).items()})
            sc = Scored(sub, case_of, merged)
            index(sc)
            m = point(sc.t, sc.p, sc.st, sc.sp)
            ci = bootstrap(sc, cases)
            numbers[f"sens{len(drop)}/{run}"] = {"point": m, "ci": ci, "atoms": len(sc.keys)}
            block.append((run, sc, m, ci))
        lines += [f"## {title}", ""] + table(block) + [""]
    lines += ["## Paired differences, all answer sets (same items, case bootstrap)", "",
              "| A | B | Sentence agreement A minus B (95% CI) | Only A right / only B right | "
              "Atom agreement A minus B (95% CI) | Only A right / only B right |", "|---" * 6 + "|"]
    for a, b in PAIRS:
        s = paired(scored[a]["all"], scored[b]["all"], cases, "sent")
        t = paired(scored[a]["all"], scored[b]["all"], cases, "atom")
        lines.append(f"| {a} | {b} | {s[0] * 100:+.1f} ({s[1] * 100:+.1f} to {s[2] * 100:+.1f}) | {s[3]} / {s[4]} | "
                     f"{t[0] * 100:+.1f} ({t[1] * 100:+.1f} to {t[2] * 100:+.1f}) | {t[3]} / {t[4]} |")
        numbers[f"paired/{a}-{b}"] = {"sentence": s, "atom": t}
    lines += ["", "Runs:", ""] + [f"- `{r}`: {d}" for r, d in RUNS.items()]
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    args.out.with_suffix(".json").write_text(json.dumps(numbers, indent=1) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
