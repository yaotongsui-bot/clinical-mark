"""Collect the fact atoms of the eICU test runs for labelling, without opening any verdict.

Reads only results_eicu/<generator>/ours_vote/atoms/*.json (the splitter's output) and applies the
same safety nets run.py applies (cm/atomize.safety_nets), so the list equals the facts every system
judges. cases/*.json, which hold verdicts, are never read.

Writes atoms.csv: key (generator|atom_id), generator, case_id, atom_id, claim_id, fact_kind, text,
sentence. Generators whose split is not there yet are reported and skipped; rerun when they are.

Usage:  python reference/fact_gold_eicu/collect_atoms.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from cm import atomize  # noqa: E402

GENERATORS = ["gpt-oss-120b", "deepseek-v4.1-flash", "qwen2.5-7b"]


def main() -> None:
    rows = []
    for g in GENERATORS:
        atom_dir = ROOT / "results_eicu" / g / "ours_vote" / "atoms"
        triples = {t["triple_id"]: t for t in json.loads(
            (ROOT / "input" / f"eicu_triples_{g}.json").read_text(encoding="utf-8"))["triples"]}
        files = sorted(atom_dir.glob("*.json")) if atom_dir.exists() else []
        if len(files) < len(triples):
            print(f"{g}: split not complete ({len(files)} of {len(triples)} cases); skipped")
            continue
        n = 0
        for f in files:
            claims = triples[f.stem]["ai_generated"]["claims"]
            atoms = atomize.safety_nets(json.loads(f.read_text(encoding="utf-8")),
                                        [{"claim_id": c["claim_id"], "text": c["text"]} for c in claims])
            for a in atoms:
                if a["kind"] != "fact":
                    continue
                rows.append({"key": f"{g}|{a['atom_id']}", "generator": g, "case_id": f.stem,
                             "atom_id": a["atom_id"], "claim_id": a["claim_id"],
                             "fact_kind": a.get("fact_kind", ""), "text": a["text"],
                             "sentence": a.get("claim_text", "")})
                n += 1
        print(f"{g}: {n} fact atoms")
    with (HERE / "atoms.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["key", "generator", "case_id", "atom_id", "claim_id",
                                                    "fact_kind", "text", "sentence"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} atoms to {HERE / 'atoms.csv'}")


if __name__ == "__main__":
    main()
