"""Error analysis on the eICU test set: every false flag and miss against the frozen reference.

Atom level, VeriFact's three labels (`unverifiable` counts as Not Addressed, as in score_eicu.py):

- False flag: the setup says Not Supported, the reference says Supported or Not Addressed.
- Miss: the reference says Not Supported, the setup says Supported or Not Addressed.
- Other disagreement: Supported vs Not Addressed (counted only).

Both result sets are analysed side by side and neither is treated as primary: the first runs
(`results_eicu/`, the pre-specified analysis) and the rerun with the case header (`results_eicu_dx/`).
Repeats 2 and 3 of the header rerun only mark whether a header-set error recurs, in the same direction, in
all three repeats.

Strata: fact kind (the reference's `fact_kind`), generator, topic (keyword rules on the atom text, `topic`
below), the evaluator's route for the atom (code check or judge, from the vote run's review sheet), and the
header and rule-7 atoms of score_eicu.py's sensitivity analysis. For the detailed runs (the cloud vote and
VeriFact with deepseek-v4-pro) every false flag and miss carries a cause from `error_analysis/causes.csv`
(columns key, run, direction, cause, note), coded by Claude from the atom, the reference evidence and the
system's reason, with the case records opened where these did not settle it. Causes are listed in CAUSES.

Usage
  python analyze_errors.py                       # error_analysis/ERRORS.md, errors.csv, ERRORS.json
  python analyze_errors.py --coding-sheet FILE   # also lists the detailed runs' errors for cause coding
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from score_baseline85 import labels_of, three
from score_eicu import GENERATORS, RUNS, frozen_ok

ROOT = Path(__file__).resolve().parent
REFERENCE = ROOT / "reference" / "fact_gold_eicu" / "fact_gold_eicu_claude.frozen.csv"
OUT = ROOT / "error_analysis"
SETS = {"first": ROOT / "results_eicu", "header": ROOT / "results_eicu_dx"}
SET_NAMES = {"first": "First runs (pre-specified)", "header": "With case header"}
REPEATS = [ROOT / "results_eicu_dx_r2", ROOT / "results_eicu_dx_r3"]
DETAILED = ("ours_vote", "vf_pro_cut")
SHORT = {
    "ours_vote": "Evaluator, vote", "ours_pro": "Evaluator, deepseek-v4-pro",
    "vf_pro_cut": "VeriFact, deepseek-v4-pro", "ours_llama": "Evaluator, llama 8B",
    "ours_llama_alljudge": "Evaluator, llama 8B, no code", "vf_llama_cut": "VeriFact, llama 8B",
    "vf_llama_nocut": "VeriFact, llama 8B, all records",
}
OVERLAP_PAIRS = [("ours_vote", "vf_pro_cut"), ("ours_pro", "vf_pro_cut"), ("ours_llama", "vf_llama_cut")]
KINDS = ("observed", "presupposition", "judgment")
FF, MISS, OTHER = "false_flag", "miss", "other"
NS = "not_supported"

TOPICS = [  # first match wins; atoms matching none fall into "Other"
    ("Ventilation and oxygen", r"ventilat|intubat|extubat|bipap|cpap|peep|fio2|tidal|(?<!blood )pressure[- ]support|\bpsv\b|"
                               r"set rate|set respiratory rate|nasal cannula|oxygen(?! saturation)|\bo2\b(?! sat)|room air|high[- ]flow|"
                               r"trach|face ?mask|non-?rebreather|airway|weaned|spontaneous breathing"),
    ("Devices, procedures and monitoring", r"catheter|drain|\bline\b|\btube\b|monitoring|telemetry|foley|dialysis|"
                                           r"head of bed|pericardiocentesis|consultation|underwent|performed|"
                                           r"currently in the [a-z ]*icu"),
    ("Drugs, infusions and orders", r"being given|receiving|infusion|administered|\bdrip\b|sedation|\bgiven\b|"
                                    r"ordered|orders? (?:is|are) active|scheduled|protocol|currently on|being used|"
                                    r"supplementation|prophylaxis|nebuliz|bolus|\bpca\b|as-needed|\bprn\b|therapy|available"),
    ("Labs", r"potassium|sodium|h(?:a)?emoglobin|platelet|\bwbc\b|white (?:blood )?cell|leukocyt|creatinine|"
             r"glucose|lactate|bicarbonate|\bph\b|\bp(?:a)?o2|\bp(?:a)?co2|pco₂|hypercapni|magnes|phosph|calc|\binr\b|"
             r"\bpt\b|\bptt\b|fibrinogen|an(?:a)?emi|kal(?:a)?emia|natr(?:a)?emia|glyc(?:a)?emia|acidosis|"
             r"alkalosis|\bbun\b|urem|troponin|bilirubin|albumin|chloride|hematocrit|thrombocyt|leukopenia|\bbnp\b|"
             r"\bast\b|\balt\b|ammonia|salicylate|\blab"),
    ("Vital signs and haemodynamics", r"blood pressure|\bbp\b|hypotens|hypertens|\bmap\b|mean arterial|systolic|"
                                      r"diastolic|\bsbp\b|\bdbp\b|heart rate|pulse|tachycard|bradycard|temperature|fever|febrile|"
                                      r"hypotherm|respiratory rate|tachypn|saturation|spo2|desaturat|hypox|vital|"
                                      r"cardiac index|vascular resistance|pa mean|hemodynamic|intracranial pressure"),
    ("Neurological, sedation and pain scores", r"\bgcs\b|glasgow|\brass\b|cam-icu|pain|agitation|tremor|"
                                               r"consciousness|mental status"),
    ("Diagnoses and conditions", r"present|ongoing|history|diagnos|admitted|sepsis|shock|failure|injury|"
                                 r"bleed|infection|possible|suspected|risk|needed|potential|stable|refractory|"
                                 r"abnormal|trending|overload|inadequate|diminished|persistent|instability"),
]

CAUSES = {  # code: (label, description); one per false flag or miss of the detailed runs, coded by Claude
    "past_as_current": ("Earlier value or ended state taken as current",
                        "An earlier lab or vital-sign value, an ended infusion, or a device or ventilator setting from "
                        "before a change, accepted for a statement about the present."),
    "record_as_given": ("Documentation or order taken as given",
                        "A treatment-table entry, an order (PRN, or marked running although the infusion had stopped) "
                        "or a device placement taken as the treatment being given or the device in place."),
    "addressed_called_na": ("Addressed statement called Not Addressed",
                            "The records address the statement without showing it (the reference's Not Supported), "
                            "but the system answered Not Addressed; includes the evaluator's administration guard and "
                            "its 'no ventilator record' rule."),
    "treatment_not_accepted": ("Documented treatment not accepted as given",
                               "A drug documented in the treatment table within 24 h (guideline rule 7) or under an "
                               "active scheduled order, rejected because eICU has no administration row."),
    "vent_gap": ("Ventilator charting gap read as extubation",
                 "The code rule (more than 6 h without a ventilator row means not ventilated) applied although no "
                 "extubation was charted."),
    "header_only": ("Evidence only in the case header",
                    "The fact rests on the admission diagnosis or unit, which the first runs' records did not have."),
    "window_or_range": ("Different window, summary or threshold",
                        "The same recent values summarised differently: a stated range checked against every value, "
                        "the 6 h median or a 24 h count instead of the latest value, or a value at a threshold."),
    "qualifier": ("Qualifier read differently",
                  "A qualifier, tense or detail (persistent, fluctuating, borderline, active, ongoing, as-needed, "
                  "infusion, device) read more strictly than the reference, or not checked."),
    "code_rule": ("Code check tested another claim",
                  "The code check tested a different claim, component or item than the statement: 'as low as 71' as "
                  "'low', a trend as the current state, diastolic pressure not checked, fingerstick glucose not "
                  "counted."),
    "evidence_missed": ("Deciding records not retrieved or misread",
                        "The rows that decide the statement were not in the system's context, or were misread."),
    "judgement_statement": ("Judgement statement judged",
                            "A risk, possibility or need statement that the reference leaves Not Addressed, judged "
                            "against values instead."),
    "judge_mismatch": ("Reason addresses another statement",
                       "The vote's stated reason discusses a different statement from the one judged."),
    "reference_doubtful": ("Reference label doubtful",
                           "On re-reading the records the reference label looks wrong or arguable; listed in "
                           "reference/fact_gold_eicu/CHANGES.md, label not changed."),
}


def topic(text: str) -> str:
    t = text.lower()
    for name, pattern in TOPICS:
        if re.search(pattern, t):
            return name
    return "Other"


def direction(ref: str, sys: str) -> str | None:
    if ref == sys:
        return None
    if sys == NS:
        return FF
    if ref == NS:
        return MISS
    return OTHER


def run_labels(root: Path, run: str) -> dict[str, str]:
    out = {}
    for g in GENERATORS:
        out.update({f"{g}|{k}": three(v) for k, v in labels_of(root / g / run).items()})
    return out


def run_reasons(root: Path, run: str) -> dict[str, str]:
    out = {}
    for g in GENERATORS:
        if run.startswith("vf_"):
            with (root / g / run / "verdicts.csv").open(encoding="utf-8", newline="") as handle:
                for r in csv.DictReader(handle):
                    out[f"{g}|{r['atom_id']}"] = r["reason"]
        else:
            with (root / g / run / "review_sheet.csv").open(encoding="utf-8-sig", newline="") as handle:
                for r in csv.DictReader(handle):
                    if r["track"] == "fact":
                        votes = f" [votes: {r['panel_votes']}]" if r["panel_votes"] else ""
                        out[f"{g}|{r['atom_id']}"] = f"{r['reason']}{votes}"
    return out


def routes(root: Path) -> dict[str, str]:
    out = {}
    for g in GENERATORS:
        with (root / g / "ours_vote" / "review_sheet.csv").open(encoding="utf-8-sig", newline="") as handle:
            for r in csv.DictReader(handle):
                if r["track"] == "fact":
                    out[f"{g}|{r['atom_id']}"] = "code" if r["method"] == "deterministic" else "judge"
    return out


def pct(n: int, d: int) -> str:
    return f"{n} ({n / d * 100:.0f}%)" if d else f"{n} (-)"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--coding-sheet", type=Path, help="write the detailed runs' errors as text for cause coding")
    args = p.parse_args()
    if not frozen_ok(REFERENCE):
        raise SystemExit(f"{REFERENCE} does not match FROZEN.sha256")
    with REFERENCE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ref = {r["key"]: r for r in rows}
    keys = sorted(ref)
    header = {r["key"] for r in rows if "dmission diagnosis" in r["evidence"] or "Unit type" in r["evidence"]}
    rule7 = {r["key"] for r in rows if "intermittent" in (r["note"] + r["evidence"]).lower()} - header
    topic_of = {k: topic(ref[k]["text"]) for k in keys}
    route_of = routes(SETS["header"])
    if route_of != routes(SETS["first"]):
        raise SystemExit("the vote's code/judge routes differ between the result sets")

    labels = {(s, run): run_labels(root, run) for s, root in SETS.items() for run in RUNS}
    reasons = {(s, run): run_reasons(root, run) for s, root in SETS.items() for run in RUNS}
    rep_labels = {run: [run_labels(root, run) for root in REPEATS] for run in RUNS}
    err = {}  # (set, run) -> {key: direction}
    for (s, run), lab in labels.items():
        missing = [k for k in keys if k not in lab]
        if missing:
            raise SystemExit(f"{s}/{run}: {len(missing)} atoms without a verdict")
        err[(s, run)] = {k: d for k in keys if (d := direction(ref[k]["label"], lab[k]))}

    def persists(run: str, k: str, d: str) -> bool:
        return all(direction(ref[k]["label"], rl[k]) == d for rl in rep_labels[run])

    causes = {}
    cause_file = args.out / "causes.csv"
    if cause_file.exists():
        with cause_file.open(encoding="utf-8", newline="") as handle:
            for r in csv.DictReader(handle):
                causes[(r["key"], r["run"])] = r
    todo = sorted({(k, run, d) for s in SETS for run in DETAILED for k, d in err[(s, run)].items() if d != OTHER})
    uncoded = [(k, run, d) for k, run, d in todo if (k, run) not in causes]
    bad = [(k, run) for k, run, d in todo if (k, run) in causes
           and (causes[(k, run)]["direction"] != d or causes[(k, run)]["cause"] not in CAUSES)]
    extra = sorted(set(causes) - {(k, run) for k, run, _ in todo})
    if bad or extra:
        raise SystemExit(f"causes.csv: {len(bad)} rows with a wrong direction or unknown cause {bad[:5]}; "
                         f"{len(extra)} rows that are not errors {extra[:5]}")

    if args.coding_sheet:
        by_atom = defaultdict(list)
        for k, run, d in uncoded:
            by_atom[k].append((run, d))
        lines = []
        for k in sorted(by_atom, key=lambda x: (ref[x]["case_id"], x)):
            r = ref[k]
            lines.append(f"### {k} | {r['fact_kind']} | {topic_of[k]} | route {route_of[k]}"
                         f"{' | HEADER' if k in header else ''}{' | RULE7' if k in rule7 else ''}")
            lines.append(f"ATOM: {r['text']}")
            lines.append(f"REF {r['label']}: {r['evidence']} || {r['note']}")
            for run, d in by_atom[k]:
                for s in SETS:
                    if err[(s, run)].get(k) == d:
                        lines.append(f"  {run} {s} {d} -> {labels[(s, run)][k]}: {reasons[(s, run)].get(k, '')[:420]}")
            lines.append("")
        args.coding_sheet.write_text("\n".join(lines), encoding="utf-8")
        print(f"coding sheet: {len(by_atom)} atoms, {len(uncoded)} errors -> {args.coding_sheet}")

    args.out.mkdir(exist_ok=True)
    fields = ["set", "run", "key", "generator", "case_id", "atom_id", "fact_kind", "topic", "route", "header_atom",
              "rule7_atom", "text", "reference_label", "system_label", "direction", "persists_in_3_repeats",
              "cause", "cause_note", "reference_evidence", "reference_note", "system_reason"]
    with (args.out / "errors.csv").open("w", encoding="utf-8", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=fields)
        w.writeheader()
        for (s, run), errs in err.items():
            for k, d in errs.items():
                r = ref[k]
                c = causes.get((k, run), {}) if d != OTHER and run in DETAILED else {}
                w.writerow({"set": s, "run": run, "key": k, "generator": r["generator"], "case_id": r["case_id"],
                            "atom_id": r["atom_id"], "fact_kind": r["fact_kind"], "topic": topic_of[k],
                            "route": route_of[k], "header_atom": int(k in header), "rule7_atom": int(k in rule7),
                            "text": r["text"], "reference_label": r["label"], "system_label": labels[(s, run)][k],
                            "direction": d,
                            "persists_in_3_repeats": int(persists(run, k, d)) if s == "header" else "",
                            "cause": c.get("cause", ""), "cause_note": c.get("note", ""),
                            "reference_evidence": r["evidence"], "reference_note": r["note"],
                            "system_reason": reasons[(s, run)].get(k, "")})

    n_ns = sum(ref[k]["label"] == NS for k in keys)
    n_non = len(keys) - n_ns
    numbers = {}
    L = ["# eICU test set: error analysis", "",
         "Every false flag and miss of the test runs against the frozen reference "
         "(`reference/fact_gold_eicu/fact_gold_eicu_claude.frozen.csv`, checksum verified), at the atom level with "
         "VeriFact's three labels (`unverifiable` counts as Not Addressed). Written by `analyze_errors.py`; one row "
         "per error in `errors.csv`, causes in `causes.csv`.", "",
         f"- False flag: the setup says Not Supported, the reference says Supported or Not Addressed (rate over the "
         f"{n_non} reference atoms that are not Not Supported).",
         f"- Miss: the reference says Not Supported, the setup does not (rate over the {n_ns} Not Supported atoms).",
         "- Other: Supported vs Not Addressed, either way (counted only).", "",
         "Both result sets are shown side by side; neither is the primary one. First runs: `results_eicu/` "
         "(pre-specified analysis). With case header: `results_eicu_dx/` (repeat 1 of three). \"Persists\" marks a "
         "header-set error that recurs in the same direction in repeats 2 and 3 (`results_eicu_dx_r2/`, `_r3/`).", ""]
    reading = args.out / "reading.md"
    if reading.exists():
        L += [reading.read_text(encoding="utf-8").rstrip(), ""]

    # 1. Counts for every setup
    L += ["## 1. Errors by direction, every setup", "",
          "| Setup | Set | S to NS | NA to NS | False flags (rate) | NS to S | NS to NA | Misses (rate) | "
          "Other (S/NA) | Header errors persisting in 3 repeats |", "|---" * 10 + "|"]
    for run in RUNS:
        for s in SETS:
            e = err[(s, run)]
            c = Counter((ref[k]["label"], labels[(s, run)][k]) for k in e)
            ff = sum(d == FF for d in e.values())
            mi = sum(d == MISS for d in e.values())
            ot = sum(d == OTHER for d in e.values())
            per = ""
            if s == "header":
                fm = [k for k, d in e.items() if d != OTHER]
                kept = sum(persists(run, k, e[k]) for k in fm)
                per = f"{kept} of {len(fm)} ({kept / len(fm) * 100:.0f}%)"
            numbers[f"{s}|{run}"] = {"false_flags": ff, "misses": mi, "other": ot,
                                     "ns_found": 1 - mi / n_ns, "ns_ppv": (n_ns - mi) / (n_ns - mi + ff)}
            L.append(f"| {SHORT[run]} | {s} | {c[('supported', NS)]} | {c[('not_addressed', NS)]} | "
                     f"{pct(ff, n_non)} | {c[(NS, 'supported')]} | {c[(NS, 'not_addressed')]} | {pct(mi, n_ns)} | "
                     f"{ot} | {per} |")
    L += ["", "S = Supported, NS = Not Supported, NA = Not Addressed (reference label first). Not Supported found "
          "= 1 - misses/200 and PPV = true flags/(true flags + false flags) reproduce `SCORES.md`.", ""]

    # 2. Overlap
    L += ["## 2. Shared and separate errors", "",
          "| A | B | Set | Misses: both | only A | only B | False flags: both | only A | only B |",
          "|---" * 9 + "|"]
    for a, b in OVERLAP_PAIRS:
        for s in SETS:
            ea, eb = err[(s, a)], err[(s, b)]
            cells = []
            for d in (MISS, FF):
                ka = {k for k, x in ea.items() if x == d}
                kb = {k for k, x in eb.items() if x == d}
                cells += [len(ka & kb), len(ka - kb), len(kb - ka)]
            L.append(f"| {SHORT[a]} | {SHORT[b]} | {s} | " + " | ".join(map(str, cells)) + " |")
    L.append("")

    # 3. Strata for the detailed runs
    def strata_table(title: str, groups: dict[str, set[str]]) -> list[str]:
        cols = [(s, run) for run in DETAILED for s in SETS]
        out = [f"### {title}", "",
               "| Stratum | Reference not NS / NS | " + " | ".join(f"{SHORT[run]}, {s}: false flags / misses"
                                                             for s, run in cols) + " |",
               "|---" * (2 + len(cols)) + "|"]
        for name, ks in groups.items():
            nn = sum(ref[k]["label"] != NS for k in ks)
            nm = len(ks) - nn
            cells = []
            for s, run in cols:
                e = err[(s, run)]
                ff = sum(e.get(k) == FF for k in ks)
                mi = sum(e.get(k) == MISS for k in ks)
                cells.append(f"{pct(ff, nn)} / {pct(mi, nm)}")
            out.append(f"| {name} | {nn} / {nm} | " + " | ".join(cells) + " |")
        return out + [""]

    def group_by(f) -> dict[str, set[str]]:
        g = defaultdict(set)
        for k in keys:
            g[f(k)].add(k)
        return g

    kinds = group_by(lambda k: ref[k]["fact_kind"])
    gens = group_by(lambda k: ref[k]["generator"])
    tops = group_by(lambda k: topic_of[k])
    rts = group_by(lambda k: route_of[k])
    L += ["## 3. Where the vote and VeriFact (deepseek-v4-pro) err", "",
          "Counts with rates in brackets: false flags over the stratum's atoms that are not Not Supported in the "
          "reference, misses over its Not Supported atoms.", ""]
    L += strata_table("By fact kind (reference)", {k: kinds[k] for k in KINDS})
    L += strata_table("By generator", {g: gens[g] for g in GENERATORS})
    order = [t for t, _ in TOPICS] + ["Other"]
    L += strata_table("By topic (keyword rules on the atom text)", {t: tops[t] for t in order if t in tops})
    L += strata_table("By the evaluator's route (code check or judge; VeriFact judges every atom)",
                      {"Code check (367)": rts["code"], "Judge (598)": rts["judge"]})
    L += strata_table("Header and rule-7 atoms", {"Header atoms (54)": header, "Rule-7 atoms (21)": rule7,
                                                  "All other atoms": set(keys) - header - rule7})

    # 4. Causes
    L += ["## 4. Causes", "",
          f"Coded for every false flag and miss of the two runs in either set: {len(todo)} (atom, run) pairs, "
          f"{len(todo) - len(uncoded)} coded, {len(uncoded)} uncoded.", ""]
    if CAUSES:
        L += ["| Code | Cause | Description |", "|---|---|---|"]
        L += [f"| `{c}` | {lab} | {desc} |" for c, (lab, desc) in CAUSES.items()] + [""]
        for run in DETAILED:
            L += [f"### {SHORT[run]}", "",
                  "| Cause | First: false flags | First: misses | Header: false flags | Header: misses | "
                  "Header errors persisting in 3 repeats |", "|---" * 6 + "|"]
            for c in CAUSES:
                cells = []
                for s in SETS:
                    for d in (FF, MISS):
                        cells.append(sum(1 for k, x in err[(s, run)].items()
                                         if x == d and causes.get((k, run), {}).get("cause") == c))
                hk = [k for k, x in err[("header", run)].items() if x != OTHER
                      and causes.get((k, run), {}).get("cause") == c]
                kept = sum(persists(run, k, err[("header", run)][k]) for k in hk)
                if any(cells):
                    L.append(f"| {CAUSES[c][0]} | " + " | ".join(map(str, cells)) + f" | {kept} of {len(hk)} |")
            L.append("")
            for title, groups in (("fact kind", KINDS), ("generator", GENERATORS)):
                L += [f"{SHORT[run]}, causes by {title} (errors, first / header):", "",
                      "| Cause | " + " | ".join(groups) + " |", "|---" * (1 + len(groups)) + "|"]
                for c in CAUSES:
                    cells = []
                    for gname in groups:
                        n = [sum(1 for k, x in err[(s, run)].items() if x != OTHER
                                 and causes.get((k, run), {}).get("cause") == c
                                 and (ref[k]["fact_kind"] if title == "fact kind" else ref[k]["generator"]) == gname)
                             for s in SETS]
                        cells.append(f"{n[0]} / {n[1]}")
                    if any(c2 != "0 / 0" for c2 in cells):
                        L.append(f"| {CAUSES[c][0]} | " + " | ".join(cells) + " |")
                L.append("")
        L += ["### Errors both systems make (same atom, same direction), by cause pair", "",
              "| Set | Direction | Vote's cause | VeriFact's cause | Atoms |", "|---|---|---|---|---|"]
        for s in SETS:
            for d in (MISS, FF):
                both = [k for k, x in err[(s, "ours_vote")].items() if x == d and err[(s, "vf_pro_cut")].get(k) == d]
                pairs = Counter((causes.get((k, "ours_vote"), {}).get("cause", "?"),
                                 causes.get((k, "vf_pro_cut"), {}).get("cause", "?")) for k in both)
                single = sum(n for n in pairs.values() if n == 1)
                for (ca, cb), n in pairs.most_common():
                    if n > 1:
                        L.append(f"| {s} | {d.replace('_', ' ')} | {CAUSES.get(ca, ('?',))[0]} | "
                                 f"{CAUSES.get(cb, ('?',))[0]} | {n} |")
                L.append(f"| {s} | {d.replace('_', ' ')} | Other pairs, one atom each | | {single} |")
                L.append(f"| {s} | {d.replace('_', ' ')} | All shared | | {len(both)} |")
        L.append("")
    (args.out / "ERRORS.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (args.out / "ERRORS.json").write_text(json.dumps(numbers, indent=1) + "\n", encoding="utf-8")
    print(f"{args.out / 'ERRORS.md'} written; causes: {len(todo) - len(uncoded)} of {len(todo)} coded")


if __name__ == "__main__":
    main()
