"""Select the eICU test cases and write their time-stamped case prompts (test set, see PAPER_PLAN.md).

Cases: unit stays from the eICU Collaborative Research Database Demo v2.0.1 that are the patient's
first ICU stay of the hospitalisation, admitted directly (unitstaytype "admit"), still in the unit at
T = unit admission + 24 h, with laboratory and nurse charting before T. A fixed-seed random sample.

The case prompt lists every record of the 24 h before T with its time, oldest first, under a short
header (age, sex, unit type, admission diagnosis). Infusions and medication orders appear as known at
T (running at T, or with their start and end). Dates are synthetic (2100-01-01 is the day of unit
admission); times of day are real.

Output: input/eicu_triples.json in the triple format run.py and generate_answers.py read. Clinician
actions after T are not built: the test set is for fact verification only.

Usage:  python make_eicu_cases.py [--n 100] [--seed 20261117]
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from cm import records_eicu as eicu

ROOT = Path(__file__).resolve().parent


def header(p, decision: str) -> str:
    dx = "" if str(p.apacheadmissiondx) == "nan" else f"; admission diagnosis: {p.apacheadmissiondx}"
    return (f"ICU stay {p.patientunitstayid} ({p.unittype}; {p.gender}, age {p.age}{dx}).\n"
            f"Decision point: {decision} (ICU admission + 24h).\n"
            "Every record of the 24 hours before the decision point is listed with its time, oldest first. "
            "Dates are shifted (2100-01-01 is the day of ICU admission); times of day are real. Infusions and "
            "medication orders are shown as known at the decision point.\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT / "data" / "eicu-demo")
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20261117)
    parser.add_argument("--out", type=Path, default=ROOT / "input" / "eicu_triples.json")
    args = parser.parse_args()

    pat = eicu.patients(args.root)
    eligible = pat[(pat["unitvisitnumber"] == 1) & (pat["unitstaytype"] == "admit")
                   & (pat["unitdischargeoffset"] > eicu.T_MIN)]
    stays = set(eligible["patientunitstayid"])
    full = eicu.stay_rows(args.root, stays, None, eicu.T_MIN)
    usable = sorted(s for s in stays if any(r["source_type"] == "laboratory" for r in full.get(s, []))
                    and sum(r["source_type"] == "monitoring" for r in full.get(s, [])) >= 24)
    picked = sorted(random.Random(args.seed).sample(usable, args.n))
    window = eicu.stay_rows(args.root, set(picked), 0, eicu.T_MIN)
    by_id = eligible.set_index("patientunitstayid")
    triples = []
    for stay in picked:
        p = by_id.loc[stay]
        p.patientunitstayid = stay
        clock = eicu.Clock(p.unitadmittime24)
        decision = clock.at(eicu.T_MIN)
        lines = [f"[{r['observed_at'][:16]}] {r['text']}" for r in window.get(stay, [])]
        text = header(p, decision) + "\n".join(lines)
        triples.append({
            "triple_id": f"E{stay}", "domain": "eicu-crd-demo-2.0.1", "stay_id": stay,
            "subject_id": str(p.uniquepid), "hospital_id": int(p.hospitalid), "unit_type": str(p.unittype),
            "decision_point": decision,
            "evaluation_eligibility": {"decision_within_icu_stay": True,
                                       "icu_outtime": clock.at(p.unitdischargeoffset)},
            "case_prompt": {"text": text, "records": len(lines), "chars": len(text)},
            "ai_generated": None, "clinician_actions": []})
    doc = {"source": "eICU Collaborative Research Database Demo v2.0.1 (ODbL)", "selection": {
        "rule": "first unit stay, unitstaytype admit, unit discharge after T, labs and >= 24 charted rows before T",
        "eligible": len(stays), "usable": len(usable), "seed": args.seed, "n": args.n}, "triples": triples}
    args.out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    sizes = sorted(t["case_prompt"]["chars"] for t in triples)
    print(f"eligible {len(stays)}, usable {len(usable)}, picked {len(picked)} from "
          f"{len({t['hospital_id'] for t in triples})} hospitals; prompt chars median {sizes[len(sizes) // 2]}, "
          f"max {sizes[-1]}; wrote {args.out}")


if __name__ == "__main__":
    main()
