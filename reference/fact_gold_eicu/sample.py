"""Draw the test cases to label and the clinician subset (fixed seed). Writes sample.json.

The unit is the case: all fact atoms of all three answer sets in a drawn case are labelled, against
one reading of its records. The clinician subset is drawn from the labelled cases.

Usage:  python reference/fact_gold_eicu/sample.py [--cases 50] [--clinician-cases 20]
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cases", type=int, default=50)
    p.add_argument("--clinician-cases", type=int, default=20)
    p.add_argument("--seed", type=int, default=20261118)
    args = p.parse_args()
    ids = sorted(t["triple_id"] for t in json.loads(
        (ROOT / "input" / "eicu_triples.json").read_text(encoding="utf-8"))["triples"])
    rng = random.Random(args.seed)
    cases = sorted(rng.sample(ids, args.cases)) if args.cases < len(ids) else ids
    clinician = sorted(rng.sample(cases, args.clinician_cases))
    doc = {"seed": args.seed, "cases": cases, "clinician_cases": clinician,
           "note": "All fact atoms of all answer sets in these cases are labelled by Claude; the clinician cases "
                   "are labelled independently by two clinicians, with adjudication."}
    (HERE / "sample.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"{len(cases)} cases to label, {len(clinician)} for clinicians -> {HERE / 'sample.json'}")


if __name__ == "__main__":
    main()
