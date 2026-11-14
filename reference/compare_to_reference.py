"""Compare every model's base-set result with the claude-ref reference run.

Writes reference/reference_comparison.md, reference/reference_comparison.json and
reference/reference_disagreements.csv.

Items are aligned inside one sentence and one kind by their wording (numbers count), because the rule tuples are too
coarse here: most facts share the concept "other", so "PEEP is 5" and "FiO2 is 40%" would look like the same item.
"""

from __future__ import annotations

import collections
import csv
import difflib
import json
import re
from pathlib import Path

from compare_models import MODELS, TIER, kappa, load

ROOT = Path(__file__).resolve().parents[1]
RUNS = {m: ROOT / "results_models" / m for m in MODELS}
RUNS["panel (3 judges)"] = ROOT / "results_deepseek_cloud"
REF = ROOT / "results_reference" / "base"
STOP = set("a an the is are was were be being been of to for in on at and or with by via per currently current patient".split())
MIN_SCORE = 0.5


def tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9.]+", text.lower().replace("%", "")) if t.strip(".") and t not in STOP}


def score(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    jaccard = len(ta & tb) / len(ta | tb) if ta | tb else 0.0
    return max(jaccard, difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() - 0.1)


def scored_items(cases: dict[str, dict]) -> dict[tuple[str, str], list[dict]]:
    out: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for case in cases.values():
        for x in case["facts"] + case["actions"]:
            out[(x["claim_id"], x["kind"])].append(x)
    return out


def align(ref: dict, other: dict) -> list[tuple[dict, dict]]:
    """Greedy one-to-one matching, best wording first."""
    pairs = []
    for key, rows in ref.items():
        candidates = sorted(((score(r["text"], o["text"]), i, j) for i, r in enumerate(rows)
                             for j, o in enumerate(other.get(key, []))), reverse=True)
        used_r, used_o = set(), set()
        for value, i, j in candidates:
            if value >= MIN_SCORE and i not in used_r and j not in used_o:
                used_r.add(i)
                used_o.add(j)
                pairs.append((rows[i], other[key][j]))
    return pairs


def agreement(pairs: list[tuple[dict, dict]]) -> dict:
    tiers = [(TIER[a["label"]], TIER[b["label"]]) for a, b in pairs]
    return {"n": len(pairs), "tier_agreement": sum(x == y for x, y in tiers) / len(tiers) if tiers else None,
            "label_agreement": sum(a["label"] == b["label"] for a, b in pairs) / len(pairs) if pairs else None,
            "kappa": kappa(tiers)}


def fmt(value: float | None, percent: bool = True) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1%}" if percent else f"{value:.2f}"


def main() -> None:
    ref_cases = load(REF)
    ref = scored_items(ref_cases)
    ref_summary = json.loads((REF / "summary.json").read_text(encoding="utf-8"))
    ref_n = sum(len(v) for v in ref.values())
    ref_false = {x["atom_id"] for rows in ref.values() for x in rows if x["kind"] == "fact" and x["label"] == "not_supported"}
    ref_false_cases = {c for c, v in ref_cases.items() if any(x["label"] == "not_supported" for x in v["facts"])}
    votes: dict[str, dict] = collections.defaultdict(dict)
    rows, payload = [], {}
    for name, path in RUNS.items():
        cases = load(path)
        other = scored_items(cases)
        pairs = align(ref, other)
        other_n = sum(len(v) for v in other.values())
        facts = [p for p in pairs if p[0]["kind"] == "fact"]
        actions = [p for p in pairs if p[0]["kind"] == "action"]
        judged = [p for p in pairs if p[0].get("method") == "llm_panel" and p[1].get("method") == "llm_panel"]
        caught = sum(a["atom_id"] in ref_false and b["label"] == "not_supported" for a, b in facts)
        aligned_false = sum(a["atom_id"] in ref_false for a, _ in facts)
        flagged = sum(b["label"] == "not_supported" for _, b in facts)
        false_cases = {c for c, v in cases.items() if any(x["label"] == "not_supported" for x in v["facts"])}
        accuracy_gap = [abs(cases[c]["metrics"]["fact_accuracy"] - ref_cases[c]["metrics"]["fact_accuracy"]) for c in cases
                        if cases[c]["metrics"]["fact_accuracy"] is not None and ref_cases[c]["metrics"]["fact_accuracy"] is not None]
        s = json.loads((path / "summary.json").read_text(encoding="utf-8"))
        for a, b in pairs:
            votes[a["atom_id"]][name] = b["label"]
        row = {"model": name, "items": other_n, "aligned": len(pairs), "precision": len(pairs) / other_n, "recall": len(pairs) / ref_n,
               "f1": 2 * len(pairs) / (other_n + ref_n), "all": agreement(pairs), "facts": agreement(facts), "actions": agreement(actions),
               "judged": agreement(judged), "false_aligned": aligned_false, "false_caught": caught, "false_flagged": flagged,
               "case_false_agree": sum((c in false_cases) == (c in ref_false_cases) for c in cases) / len(cases),
               "case_accuracy_gap": sum(accuracy_gap) / len(accuracy_gap),
               "fact_accuracy": s["facts"]["accuracy"], "treat_agree": s["treatment_actions"]["precision_lenient"],
               "key_recall": s["coverage"]["vital"]["micro"], "cases_false": len(false_cases)}
        rows.append(row)
        payload[name] = row
    lines = ["# Models against the reference", "",
             "The reference is Claude's own splitting and judgment under the same rules and the same retrieved records. "
             "It is a comparison anchor, not clinician ground truth.", "",
             f"Reference: {ref_n} scored items, fact accuracy {ref_summary['facts']['accuracy']:.1%}, "
             f"{len(ref_false)} false facts in {len(ref_false_cases)} cases, treatment agreement "
             f"{ref_summary['treatment_actions']['precision_lenient']:.1%}, key treatment recall {ref_summary['coverage']['vital']['micro']:.1%}.", "",
             "## Splitting", "", "| Model | Items | Aligned | Precision | Recall | F1 |", "|---|---|---|---|---|---|"]
    lines += [f"| {r['model']} | {r['items']} | {r['aligned']} | {r['precision']:.1%} | {r['recall']:.1%} | {r['f1']:.2f} |" for r in rows]
    lines += ["", "## Verdicts on aligned items (positive / negative / undetermined)", "",
              "| Model | All items | Kappa | Facts | Fact kappa | Actions | Both judged by a model (n) | Agreement | Kappa |", "|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| {r['model']} | {fmt(r['all']['tier_agreement'])} | {fmt(r['all']['kappa'], False)} | {fmt(r['facts']['tier_agreement'])} | "
              f"{fmt(r['facts']['kappa'], False)} | {fmt(r['actions']['tier_agreement'])} | {r['judged']['n']} | {fmt(r['judged']['tier_agreement'])} | "
              f"{fmt(r['judged']['kappa'], False)} |" for r in rows]
    lines += ["", "## False facts and case-level results", "",
              "| Model | Reference false facts aligned | Also called false | Called false on aligned items | Same false-fact status by case | Mean case accuracy gap | Fact accuracy | Cases with false fact | Treatment agreement | Key recall |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| {r['model']} | {r['false_aligned']} | {r['false_caught']} | {r['false_flagged']} | {r['case_false_agree']:.1%} | {r['case_accuracy_gap']:.1%} | "
              f"{r['fact_accuracy']:.1%} | {r['cases_false']} | {r['treat_agree']:.1%} | {r['key_recall']:.1%} |" for r in rows]
    out = ROOT / "reference"
    (out / "reference_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "reference_comparison.json").write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    with (out / "reference_disagreements.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        names = list(RUNS)
        writer.writerow(["atom_id", "text", "reference_label", "reference_method", "reference_reason", "aligned", "disagree", *names])
        table = []
        for items in ref.values():
            for x in items:
                v = votes.get(x["atom_id"], {})
                disagree = sum(TIER[label] != TIER[x["label"]] for label in v.values())
                table.append((disagree, x, v))
        for disagree, x, v in sorted(table, key=lambda t: (-t[0], t[1]["atom_id"])):
            writer.writerow([x["atom_id"], x["text"], x["label"], x.get("method"), x.get("reason"), len(v), disagree, *[v.get(n, "") for n in names]])
    print("\n".join(lines))


if __name__ == "__main__":
    main()
