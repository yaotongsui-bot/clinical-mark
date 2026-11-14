"""Write the split standard for the base answers and score every model's split against it.

Outputs reference/split_standard.csv and reference/split_standard.md. Atoms are aligned inside one sentence and one kind
by wording; every atom counts, goals and code-added premises included.
"""

from __future__ import annotations

import collections
import csv
import json
from pathlib import Path

from compare_to_reference import score

ROOT = Path(__file__).resolve().parents[1]
MODELS = ["deepseek-v4-pro_0813", "kimi-k3.1-pro", "mimo-v2.6-pro", "deepseek-v4.1-flash", "glm-5.3", "glm-5.3-flash", "minimax-m3.1-flash", "muse-spark-open"]
THRESHOLD = 0.5
RULES = """## Rules used

1. One atom per independently checkable target. A listed item is its own atom ("AST, ALT, alkaline phosphatase" gives three).
2. A general word followed by "including" is replaced by the items listed.
3. Assessing and managing are separate actions, because code checks them on different tracks. Two words for one check stay together ("assess and monitor").
4. Each ventilator, PCA or CRRT setting is its own fact, so each value can be checked. Settings named inside "continue ventilation" stay facts, not extra actions.
5. "Continue X" also gives the fact that X is under way. A stated order or device is a fact.
6. A purpose with no target of its own is not an atom ("for blood pressure control"). A named target stays a goal ("maintain SpO2 above 85%").
7. Conditions and things to look for are not facts, as in the atomizer prompt.
"""


def cases(path: Path) -> dict[str, list[dict]]:
    return {f.stem: json.loads(f.read_text(encoding="utf-8"))["atoms"] for f in sorted((path / "cases").glob("*.json"))}


def by_key(rows: list[dict]) -> dict[tuple, list[dict]]:
    out = collections.defaultdict(list)
    for a in rows:
        out[(a["claim_id"], a["kind"])].append(a)
    return out


def aligned(ref: dict, other: dict) -> tuple[int, Counter]:
    total, per = 0, collections.Counter()
    for key, rows in ref.items():
        pairs = sorted(((score(r["text"], o["text"]), i, j) for i, r in enumerate(rows) for j, o in enumerate(other.get(key, []))), reverse=True)
        used_r, used_o = set(), set()
        for value, i, j in pairs:
            if value >= THRESHOLD and i not in used_r and j not in used_o:
                used_r.add(i)
                used_o.add(j)
                total += 1
                per[key[1]] += 1
    return total, per


Counter = collections.Counter


def main() -> None:
    standard = cases(ROOT / "results_reference" / "base")
    with (ROOT / "reference" / "split_standard.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["case_id", "claim_id", "sentence", "atom_id", "kind", "fact_kind", "text", "concept", "direction", "action_class", "target", "conditional"])
        for cid, rows in standard.items():
            for a in rows:
                writer.writerow([cid, a["claim_id"], a["claim_text"], a["atom_id"], a["kind"], a.get("fact_kind", ""), a["text"], a.get("concept", ""),
                                 a.get("direction", ""), a.get("action_class", ""), a.get("target", ""), a.get("conditional", "")])
    kinds = Counter(a["kind"] for rows in standard.values() for a in rows)
    n = sum(kinds.values())
    table = []
    for m in MODELS:
        run = cases(ROOT / "results_models" / m)
        hits, per = 0, Counter()
        sentence_same = sentences = 0
        size = 0
        for cid, rows in standard.items():
            ref, other = by_key(rows), by_key(run[cid])
            size += len(run[cid])
            h, p = aligned(ref, other)
            hits += h
            per.update(p)
            claims = {a["claim_id"] for a in rows}
            for claim in claims:
                sentences += 1
                rc = {k: v for k, v in ref.items() if k[0] == claim}
                oc = {k: v for k, v in other.items() if k[0] == claim}
                h2, _ = aligned(rc, oc)
                sentence_same += h2 == sum(map(len, rc.values())) == sum(map(len, oc.values()))
        precision, recall = hits / size, hits / n
        table.append((m, size, hits, precision, recall, 2 * hits / (size + n), per["fact"] / kinds["fact"], per["action"] / kinds["action"], sentence_same / sentences))
    table.sort(key=lambda r: -r[5])
    lines = ["# Split standard, base answers", "", f"{len(standard)} cases, {n} atoms: {kinds['fact']} facts, {kinds['action']} actions, {kinds['goal']} goals. "
             "Written by Claude and checked against eight models' splits; not reviewed by a clinician.", "", RULES,
             "## Models against the standard", "", "| Model | Atoms | Matched | Precision | Recall | F1 | Facts found | Actions found | Sentences split the same |", "|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]:.1%} | {r[4]:.1%} | {r[5]:.2f} | {r[6]:.1%} | {r[7]:.1%} | {r[8]:.1%} |" for r in table]
    (ROOT / "reference" / "split_standard.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
