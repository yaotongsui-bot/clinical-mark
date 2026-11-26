"""Write one condensed record sheet per case for labelling the fact gold standard (see GUIDELINE.md).

Evidence is every record of the current admission known before the decision time T, read with the
project's MIMIC loader (cm/records.load_admission_rows). No verdict, retrieval or reason from any
system is read. Outputs:
  sheets/<case>.txt    atoms to label, then every record type in condensed form
  records/<case>.tsv   every row, for search

Usage:  python reference/fact_gold/build_sheets.py
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
from cm import records  # noqa: E402


def short(stamp: str) -> str:
    return (stamp or "")[5:16]


def main() -> None:
    triples = {t["triple_id"]: t for t in json.loads(
        (ROOT / "input" / "mimic_triples_deepseek.json").read_text(encoding="utf-8"))["triples"]}
    with (ROOT / "reference" / "split_standard.csv").open(encoding="utf-8", newline="") as handle:
        atoms = [r for r in csv.DictReader(handle) if r["kind"] == "fact"]
    by_case = defaultdict(list)
    for a in atoms:
        by_case[a["case_id"]].append(a)
    chosen = [triples[c] for c in sorted(by_case)]
    rows_by_case = records.load_admission_rows(ROOT / "data" / "mimic-iv-demo", chosen)
    (HERE / "sheets").mkdir(exist_ok=True)
    (HERE / "records").mkdir(exist_ok=True)
    for t in chosen:
        case = t["triple_id"]
        T = records.ts(t["decision_point"])
        day = T - dt.timedelta(hours=24)
        rows = rows_by_case.get(case, [])
        recent = [r for r in rows if records.ts(r["observed_at"]) and records.ts(r["observed_at"]) >= day]
        with (HERE / "records" / f"{case}.tsv").open("w", encoding="utf-8", newline="") as handle:
            w = csv.writer(handle, delimiter="\t")
            w.writerow(["time", "source", "type", "text"])
            for r in rows:
                w.writerow([r["observed_at"], r["source_type"], r["semantics"], r["text"]])
        out = [f"# {case}   T = {t['decision_point']}   ICU stay {t['stay_id']}   records before T: {len(rows)}",
               "", "## Atoms"]
        for a in by_case[case]:
            out.append(f"{a['atom_id']} [{a['fact_kind']}] {a['text']}   <- {a['sentence']}")
        out += ["", "## Running at T"]
        out += [f"  {r['text']}" for r in rows if r["ongoing_at_decision"] and r["source_type"] != "medication_order"]
        out += ["", "## Orders active at T"]
        out += [f"  {short(r['observed_at'])} {r['text']}" for r in rows
                if r["source_type"] == "medication_order" and r["ongoing_at_decision"]]
        stopped = defaultdict(list)
        for r in rows:
            if r["source_type"] == "medication_order" and not r["ongoing_at_decision"]:
                stopped[r["label"]].append(r["text"].split("(")[-1].rstrip(")"))
        out += ["", "## Orders stopped before T (drug: stop times)"]
        out += [f"  {k}: {'; '.join(v[-3:])}" for k, v in sorted(stopped.items())]
        for source, title in (("treatment", "Infusions / inputs ended before T"), ("procedure", "Procedures ended before T")):
            groups = defaultdict(list)
            for r in rows:
                if r["source_type"] == source and not r["ongoing_at_decision"]:
                    groups[r["label"]].append(r)
            out += ["", f"## {title} (item: last 24 h intervals; earlier count)"]
            for k, v in sorted(groups.items()):
                last = [x for x in v if x in recent]
                earlier = len(v) - len(last)
                desc = "; ".join(x["text"].split(" ", 2)[-1][len(k):].strip() or short(x["observed_at"]) for x in last[-6:])
                out.append(f"  {k}: {desc if last else '-'}" + (f"   [+{earlier} earlier, last ended "
                           f"{v[-1]['text'].rsplit(' to ', 1)[-1].rstrip(')')[5:16]}]" if earlier else ""))
        emar = defaultdict(list)
        for r in rows:
            if r["source_type"] == "medication_administration":
                emar[r["label"]].append(r)
        out += ["", "## eMAR (drug: last 24 h events; earlier given count)"]
        for k, v in sorted(emar.items()):
            last = [f"{short(x['observed_at'])[6:]} {x['text'].split(':')[0][4:]}" for x in v if x in recent]
            earlier = sum(1 for x in v if x not in recent and x["semantics"] == "administration")
            out.append(f"  {k}: {', '.join(last) if last else '-'}" + (f"   [+{earlier} earlier given]" if earlier else ""))
        labs = defaultdict(list)
        for r in rows:
            if r["source_type"] == "laboratory":
                labs[r["label"]].append(r)
        out += ["", "## Laboratory (newest first, up to 4; [reference range])"]
        for k, v in sorted(labs.items()):
            ref = next(([x["lower"], x["upper"]] for x in reversed(v) if x["lower"] is not None or x["upper"] is not None), None)
            vals = "; ".join(f"{short(x['observed_at'])} {x['text'][len(k) + 2:]}" for x in reversed(v[-4:]))
            out.append(f"  {k}: {vals}" + (f"   [{ref[0]}-{ref[1]}]" if ref else ""))
        chart = defaultdict(list)
        for r in rows:
            if r["source_type"] == "monitoring":
                chart[r["label"]].append(r)
        out += ["", "## Charted items (latest; last 24 h range or recent values)"]
        for k, v in sorted(chart.items()):
            latest = v[-1]
            line = f"  {k}: {latest['text'][len(k) + 2:]} @{short(latest['observed_at'])}"
            nums = [x["value"] for x in v if x in recent and x["value"] is not None]
            if len(nums) > 1 and latest["value_text"] is None:
                line += f"   24h {min(nums):g}-{max(nums):g} (n={len(nums)})"
            elif latest["value_text"] is not None:
                seen = []
                for x in reversed(v):
                    item = f"{x['text'][len(k) + 2:]} @{short(x['observed_at'])}"
                    if x["text"] != latest["text"] and x["text"] not in [s[0] for s in seen]:
                        seen.append((x["text"], item))
                    if len(seen) >= 2:
                        break
                if seen:
                    line += "   earlier: " + "; ".join(s[1] for s in seen)
            out.append(line)
        out += ["", "## Microbiology"]
        out += [f"  {short(r['observed_at'])} {r['text']}" for r in rows if r["source_type"] == "specimen"]
        (HERE / "sheets" / f"{case}.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{len(chosen)} sheets, {len(atoms)} atoms")


if __name__ == "__main__":
    main()
