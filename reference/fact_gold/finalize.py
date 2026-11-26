"""Turn labels.txt into fact_gold_claude.csv and check it covers every fact atom exactly once.

labels.txt lines: atom_id|S/NS/NA|evidence|note. seen_before marks atoms whose case Claude had seen a
system's verdict or an earlier reference verdict for in the same conversation before labelling.

Usage:  python reference/fact_gold/finalize.py [--allow-partial]
"""

from __future__ import annotations

import argparse
import collections
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LABEL = {"S": "supported", "NS": "not_supported", "NA": "not_addressed"}
# Cases whose verdicts Claude saw before labelling: the baseline smoke test (M30057454, M37067082) and
# lines of the earlier blind reference printed while inspecting reference/blind_v1.
SEEN = {"M30057454", "M37067082", "M31205490", "M33987268", "M36753294", "M37049133", "M35514836",
        "M32128372", "M34100191"}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--allow-partial", action="store_true")
    args = p.parse_args()
    with (ROOT / "reference" / "split_standard.csv").open(encoding="utf-8", newline="") as handle:
        atoms = {r["atom_id"]: r for r in csv.DictReader(handle) if r["kind"] == "fact"}
    rows, seen_ids = [], collections.Counter()
    for n, line in enumerate((HERE / "labels.txt").read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        atom_id, label, evidence, note = (line.split("|") + ["", "", ""])[:4]
        if atom_id not in atoms:
            raise SystemExit(f"line {n}: unknown atom {atom_id}")
        if label not in LABEL:
            raise SystemExit(f"line {n}: unknown label {label!r}")
        seen_ids[atom_id] += 1
        a = atoms[atom_id]
        rows.append({"atom_id": atom_id, "case_id": a["case_id"], "fact_kind": a["fact_kind"], "text": a["text"],
                     "label": LABEL[label], "evidence": evidence, "note": note,
                     "seen_before": int(a["case_id"] in SEEN)})
    dupes = [k for k, v in seen_ids.items() if v > 1]
    missing = sorted(set(atoms) - set(seen_ids))
    if dupes:
        raise SystemExit(f"labelled more than once: {dupes}")
    if missing and not args.allow_partial:
        raise SystemExit(f"{len(missing)} atoms not labelled yet, e.g. {missing[:5]}")
    order = list(atoms)
    rows.sort(key=lambda r: order.index(r["atom_id"]))
    with (HERE / "fact_gold_claude.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    counts = collections.Counter(r["label"] for r in rows)
    kinds = collections.Counter((r["fact_kind"], r["label"]) for r in rows)
    print(f"{len(rows)} of {len(atoms)} atoms, {len({r['case_id'] for r in rows})} cases; {dict(counts)}; "
          f"seen_before {sum(r['seen_before'] for r in rows)}; missing {len(missing)}")
    print({f"{k[0]}:{k[1]}": v for k, v in sorted(kinds.items())})


if __name__ == "__main__":
    main()
