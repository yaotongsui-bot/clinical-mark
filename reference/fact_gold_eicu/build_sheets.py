"""Record sheets for labelling the eICU test reference (see GUIDELINE.md).

For each sampled case: the fact atoms of every answer set, then every record known before T in
condensed form (running at T, orders, infusions, medications, labs, charted items, documented
treatments, microbiology). records/<case>.tsv holds every row for search. Reads atoms.csv and
sample.json; no verdict is read.

Usage:  python reference/fact_gold_eicu/build_sheets.py
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from cm import records, records_eicu  # noqa: E402


def short(stamp: str) -> str:
    return (stamp or "")[5:16]


def condensed(rows: list[dict], T: dt.datetime) -> list[str]:
    day = T - dt.timedelta(hours=24)
    recent = {id(r) for r in rows if records.ts(r["observed_at"]) and records.ts(r["observed_at"]) >= day}
    out = ["## Running at T (infusions, scheduled medications)"]
    out += [f"  {r['text']}" for r in rows if r["ongoing_at_decision"] and r["semantics"] == "administration"]
    out += ["", "## PRN orders"]
    out += [f"  {short(r['observed_at'])} {r['text']}" for r in rows if r["source_type"] == "medication_order"]
    out += ["", "## Infusions ended before T (oldest first)"]
    out += [f"  {r['text']}" for r in rows if r["source_type"] == "treatment" and not r["ongoing_at_decision"]]
    out += ["", "## Medications given once or ended before T"]
    out += [f"  {r['text']}" for r in rows
            if r["source_type"] == "medication_administration" and not r["ongoing_at_decision"]]
    labs = defaultdict(list)
    for r in rows:
        if r["source_type"] == "laboratory":
            labs[r["label"]].append(r)
    out += ["", "## Laboratory (newest first, up to 5)"]
    for k, v in sorted(labs.items()):
        vals = "; ".join(f"{short(x['observed_at'])} {x['text'][len(k) + 2:]}" for x in reversed(v[-5:]))
        out.append(f"  {k}: {vals}" + (f"   [+{len(v) - 5} earlier]" if len(v) > 5 else ""))
    chart = defaultdict(list)
    for r in rows:
        if r["source_type"] == "monitoring":
            chart[r["label"]].append(r)
    out += ["", "## Charted items (latest; last 24 h range, or recent distinct values)"]
    for k, v in sorted(chart.items()):
        latest = v[-1]
        line = f"  {latest['text']} @{short(latest['observed_at'])}"
        nums = [x["value"] for x in v if id(x) in recent and x["value"] is not None]
        if latest["value"] is not None and len(nums) > 1:
            line += f"   24h {min(nums):g}-{max(nums):g} (n={len(nums)})"
        else:
            seen = []
            for x in reversed(v[:-1]):
                if x["text"] != latest["text"] and x["text"] not in [s[0] for s in seen]:
                    seen.append((x["text"], f"{x['text'][len(k) + 2:]} @{short(x['observed_at'])}"))
                if len(seen) >= 3:
                    break
            if seen:
                line += "   earlier: " + "; ".join(s[1] for s in seen)
        out.append(line)
    out += ["", "## Treatments documented"]
    out += [f"  {short(r['observed_at'])} {r['text'][len('Treatment documented: '):]}" for r in rows
            if r["source_type"] == "treatment_documentation"]
    out += ["", "## Microbiology"]
    out += [f"  {short(r['observed_at'])} {r['text']}" for r in rows if r["source_type"] == "specimen"]
    return out


def main() -> None:
    sample = json.loads((HERE / "sample.json").read_text(encoding="utf-8"))
    with (HERE / "atoms.csv").open(encoding="utf-8", newline="") as handle:
        atoms = [a for a in csv.DictReader(handle) if a["case_id"] in set(sample["cases"])]
    by_case = defaultdict(list)
    for a in atoms:
        by_case[a["case_id"]].append(a)
    triples = {t["triple_id"]: t for t in json.loads(
        (ROOT / "input" / "eicu_triples.json").read_text(encoding="utf-8"))["triples"]}
    chosen = [triples[c] for c in sample["cases"]]
    rows_by_case = records_eicu.load_admission_rows(ROOT / "data" / "eicu-demo", chosen)
    (HERE / "sheets").mkdir(exist_ok=True)
    (HERE / "records").mkdir(exist_ok=True)
    for t in chosen:
        case = t["triple_id"]
        rows = rows_by_case.get(case, [])
        with (HERE / "records" / f"{case}.tsv").open("w", encoding="utf-8", newline="") as handle:
            w = csv.writer(handle, delimiter="\t")
            w.writerow(["time", "source", "type", "text"])
            for r in rows:
                w.writerow([r["observed_at"], r["source_type"], r["semantics"], r["text"]])
        head = t["case_prompt"]["text"].split("\n")[0]
        out = [f"# {case}   T = {t['decision_point']}   records before T: {len(rows)}", f"{head}", "", "## Atoms"]
        for a in sorted(by_case[case], key=lambda a: (a["generator"], a["atom_id"])):
            out.append(f"{a['key']} [{a['fact_kind']}] {a['text']}   <- {a['sentence']}")
        out.append("")
        out += condensed(rows, records.ts(t["decision_point"]))
        (HERE / "sheets" / f"{case}.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{len(chosen)} sheets, {len(atoms)} atoms")


if __name__ == "__main__":
    main()
