"""Test-retest stability: compare item labels of two runs of the same evaluation (judge cache cleared).

Usage: python stability_compare.py results_fixed validation/retest_fixed validation/stability_results_fixed.md
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_annotations import gwet_ac1  # noqa: E402

first, second, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])


def labels(run: Path) -> dict:
    found = {}
    for p in sorted((run / "cases").glob("*.json")):
        case = json.loads(p.read_text(encoding="utf-8"))
        for x in case["facts"]:
            found[f"{case['case_id']}|{x['atom_id']}"] = ("fact", x.get("method", "rule"), x["label"])
        for x in case["actions"]:
            found[f"{case['case_id']}|{x['atom_id']}"] = (x["track"], x.get("method", "rule"), x["label"])
    return found


a, b = labels(first), labels(second)
common = sorted(set(a) & set(b))
lines = [f"# Test-retest stability: `{first.name}` vs `{second.name}`", "",
         "The second run has its own judge cache, filled when it was first run with an empty judge cache;",
         "the atomizer output is shared. The comparison is between two independent judge runs under fixed",
         "settings: it shows repeatability, not correctness.", "",
         f"- Items compared: {len(common)} (only in first: {len(set(a) - set(b))}, only in second: {len(set(b) - set(a))})", "",
         "| Stratum | n | Identical labels | Gwet's AC1 |", "|---|---|---|---|"]
groups = {"all items": common}
for key in sorted({a[i][1] for i in common}):
    groups[f"method = {key}"] = [i for i in common if a[i][1] == key]
for key in sorted({a[i][0] for i in common}):
    groups[f"item type = {key}"] = [i for i in common if a[i][0] == key]
for name, ids in groups.items():
    same = sum(a[i][2] == b[i][2] for i in ids)
    classes = sorted({a[i][2] for i in ids} | {b[i][2] for i in ids})
    ac1 = gwet_ac1([[a[i][2], b[i][2]] for i in ids], classes) if len(classes) > 1 else 1.0
    lines.append(f"| {name} | {len(ids)} | {same / len(ids) * 100:.1f}% | {'-' if ac1 is None else f'{ac1:.2f}'} |")
changed = [i for i in common if a[i][2] != b[i][2]]
lines += ["", "## Items whose label changed", "", "| Item | Method | First | Second |", "|---|---|---|---|"]
lines += [f"| {i} | {a[i][1]} | {a[i][2]} | {b[i][2]} |" for i in changed]
lines += ["", "Changes by method: " + str(dict(Counter(a[i][1] for i in changed)))]
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[:16]))
