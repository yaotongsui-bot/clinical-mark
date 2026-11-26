"""Turn labels.txt into fact_gold_eicu_claude.csv and check it covers every sampled atom exactly once.

labels.txt lines: key|S/NS/NA|evidence|note, where key = generator|atom_id.

Usage:  python reference/fact_gold_eicu/finalize.py [--allow-partial]
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABEL = {"S": "supported", "NS": "not_supported", "NA": "not_addressed"}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--allow-partial", action="store_true")
    args = p.parse_args()
    sample = json.loads((HERE / "sample.json").read_text(encoding="utf-8"))
    cases, clinician = set(sample["cases"]), set(sample["clinician_cases"])
    with (HERE / "atoms.csv").open(encoding="utf-8", newline="") as handle:
        atoms = {a["key"]: a for a in csv.DictReader(handle) if a["case_id"] in cases}
    rows, count = [], collections.Counter()
    path = HERE / "labels.txt"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    for n, line in enumerate(lines, 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("|")
        key, label = f"{parts[0]}|{parts[1]}", parts[2]
        evidence, note = (parts[3] if len(parts) > 3 else ""), (parts[4] if len(parts) > 4 else "")
        if key not in atoms:
            raise SystemExit(f"line {n}: unknown or unsampled atom {key}")
        if label not in LABEL:
            raise SystemExit(f"line {n}: unknown label {label!r}")
        count[key] += 1
        a = atoms[key]
        rows.append({"key": key, "generator": a["generator"], "case_id": a["case_id"], "atom_id": a["atom_id"],
                     "fact_kind": a["fact_kind"], "text": a["text"], "label": LABEL[label], "evidence": evidence,
                     "note": note, "clinician_case": int(a["case_id"] in clinician)})
    dupes = [k for k, v in count.items() if v > 1]
    missing = sorted(set(atoms) - set(count))
    if dupes:
        raise SystemExit(f"labelled more than once: {dupes[:5]}")
    if missing and not args.allow_partial:
        raise SystemExit(f"{len(missing)} sampled atoms not labelled yet, e.g. {missing[:3]}")
    order = list(atoms)
    rows.sort(key=lambda r: order.index(r["key"]))
    fields = ["key", "generator", "case_id", "atom_id", "fact_kind", "text", "label", "evidence", "note",
              "clinician_case"]
    with (HERE / "fact_gold_eicu_claude.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    by_gen = collections.Counter((r["generator"], r["label"]) for r in rows)
    print(f"{len(rows)} of {len(atoms)} sampled atoms labelled; missing {len(missing)}")
    print({f"{g}:{l}": n for (g, l), n in sorted(by_gen.items())})


if __name__ == "__main__":
    main()
