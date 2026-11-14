"""Search the record sheets while labelling (the reader's free search over the record).

Usage:  python reference/fact_gold/peek.py CASE=regex [CASE=regex ...]
Prints the case's atoms, everything running at T, and every sheet line matching the regex
(case-insensitive), tagged with its section.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

for arg in sys.argv[1:]:
    case, _, pattern = arg.partition("=")
    rx = re.compile(pattern, re.I) if pattern else None
    lines = (HERE / "sheets" / f"{case}.txt").read_text(encoding="utf-8").splitlines()
    section, shown = "", []
    for line in lines:
        if line.startswith("## "):
            section = line[3:].split(" (")[0]
            continue
        if line.startswith("# ") or section in ("Atoms", "Running at T"):
            if line.strip():
                shown.append(line if section != "Running at T" else f"[run] {line.strip()[40:]}")
        elif rx and rx.search(line):
            shown.append(f"[{section[:12]}] {line.strip()}")
    print("\n".join(s[:330] for s in shown))
    print()
