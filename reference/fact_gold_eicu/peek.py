"""Search the test record sheets while labelling (the reader's free search over the record).

Usage:  python reference/fact_gold_eicu/peek.py CASE=regex [CASE=regex ...]
Prints the case header and atoms, every medication, infusion, documented treatment and microbiology
line in full, and the laboratory and charted-item lines that match the regex (case-insensitive) or the
default vital-sign and device terms. For the full rows, search records/CASE.tsv.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILTERED = ("Laboratory", "Charted items")
DEFAULT = (r"Heart Rate|Respiratory Rate|saturation|Blood Pressure|Temperature F|O2 Delivery|O2 Flow|O2 L/%|"
           r"Admin Device|Inspired O2|PEEP|Tidal|Ventilator|PSV|Pain Level|GCS Total|Glucose finger|Airway|Sedation|INR|PT\b|"
           r"White Blood|Hemoglobin|Hematocrit|Creatinine|Potassium|Sodium|Lactate|Platelet|Bicarbonate|BNP|"
           r"Troponin|SpO2|Pulse|Urea Nitrogen|Magnesium|Calcium|Anion|PTT")

for arg in sys.argv[1:]:
    case, _, pattern = arg.partition("=")
    rx = re.compile(DEFAULT + (f"|{pattern}" if pattern else ""), re.I)
    section, shown, last = "", [], None
    for line in (HERE / "sheets" / f"{case}.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].split(" (")[0]
            if section not in FILTERED and section != "Atoms":
                shown.append(f"-- {section}")
            continue
        if not line.strip():
            continue
        if section in FILTERED:
            if rx.search(line):
                shown.append(f"[{section[:4]}] {line.strip()}")
        elif section == "Atoms" and "   <- " in line:
            atom, _, sentence = line.partition("   <- ")
            if sentence != last:
                shown.append(f"  << {sentence}")
                last = sentence
            shown.append(atom)
        else:
            shown.append(line.strip() if section else line)
    print("\n".join(s[:300] for s in shown))
    print()
