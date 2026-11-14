"""Compare judges that scored the same atoms (results_bakeoff) with blind reference labels.

Writes reference/judge_comparison.md and reference/judge_disagreements.csv. Only items a model judged are compared;
code decides the rest identically in every run.
"""

from __future__ import annotations

import collections
import csv
import json
import random
from pathlib import Path

from compare_models import TIER, kappa, load
from compare_to_reference import REF, scored_items

ROOT = Path(__file__).resolve().parents[1]
MODELS = ["deepseek-v4-pro_0813", "kimi-k3.1-pro", "deepseek-v4.1-flash", "mimo-v2.6-pro"]
CODE = {"S": "positive", "P": "positive", "N": "negative", "A": "undetermined", "U": "undetermined"}
# Tokens per 85 cases are measured from the cached requests by chars/4; prices are per million (input, output).
PRICE = {"deepseek-v4-pro_0813": (0.99, 3.96), "kimi-k3.1-pro": (2.0, 10.0), "deepseek-v4.1-flash": (0.30, 1.20), "mimo-v2.6-pro": (None, None)}


def reference_labels(items: dict) -> tuple[dict, int]:
    labels = {}
    for line in (ROOT / "reference" / "bakeoff_verdicts.txt").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            atom, code = line.split("|")
            labels[atom] = CODE[code]
    text = {(x["claim_id"], x["kind"], x["text"].strip().lower()): x for rows in scored_items(load(REF)).values() for x in rows}
    carried = 0
    for atom, x in items.items():
        hit = text.get((x["claim_id"], x["kind"], x["text"].strip().lower()))
        if atom not in labels and hit and hit.get("method") == "llm_panel":
            labels[atom] = TIER[hit["label"]]
            carried += 1
    return labels, carried


def score(reference: dict, pred: dict) -> dict:
    keys = sorted(set(reference) & set(pred))
    pairs = [(reference[k], pred[k]) for k in keys]
    false_ref = [k for k in keys if reference[k] == "negative"]
    flagged = [k for k in keys if pred[k] == "negative"]
    agree = sum(a == b for a, b in pairs) / len(pairs)
    cases = sorted({k.split("A")[0] for k in keys})
    by_case = collections.defaultdict(list)
    for k in keys:
        by_case[k.split("A")[0]].append(reference[k] == pred[k])
    rng = random.Random(0)
    boots = []
    for _ in range(2000):
        draw = [v for c in rng.choices(cases, k=len(cases)) for v in by_case[c]]
        boots.append(sum(draw) / len(draw))
    boots.sort()
    return {"n": len(keys), "agree": agree, "low": boots[50], "high": boots[1949], "kappa": kappa(pairs),
            "false_found": sum(pred[k] == "negative" for k in false_ref), "false_total": len(false_ref),
            "flagged": len(flagged), "flag_right": sum(reference[k] == "negative" for k in flagged)}


def main() -> None:
    runs = {m: load(ROOT / "results_bakeoff" / m) for m in MODELS}
    items = {x["atom_id"]: x for c in runs[MODELS[0]].values() for x in c["facts"] + c["actions"] if x.get("method") == "llm_panel"}
    reference, carried = reference_labels(items)
    reference = {k: v for k, v in reference.items() if k in items}
    pred = {m: {x["atom_id"]: TIER[x["label"]] for c in runs[m].values() for x in c["facts"] + c["actions"] if x["atom_id"] in items} for m in MODELS}
    pro, kimi, flash = pred[MODELS[0]], pred[MODELS[1]], pred[MODELS[2]]
    designs = {m: pred[m] for m in MODELS}
    designs["pro; kimi rechecks its 'not supported'"] = {k: kimi[k] if pro[k] == "negative" else pro[k] for k in pro}
    designs["flash; pro rechecks its non-positive"] = {k: pro[k] if flash[k] != "positive" else flash[k] for k in flash}
    designs["flash; kimi rechecks its non-positive"] = {k: kimi[k] if flash[k] != "positive" else flash[k] for k in flash}
    designs["pro + flash; kimi on disagreement"] = {k: pro[k] if pro[k] == flash[k] else kimi[k] for k in pro}
    final = load(ROOT / "results_final" / "base")
    designs["chosen vote: pro, flash, mimo"] = {x["atom_id"]: TIER[x["label"]] for c in final.values() for x in c["facts"] + c["actions"] if x["atom_id"] in items}
    extra = {"pro; kimi rechecks its 'not supported'": sum(v == "negative" for v in pro.values()),
             "flash; pro rechecks its non-positive": sum(v != "positive" for v in flash.values()),
             "flash; kimi rechecks its non-positive": sum(v != "positive" for v in flash.values()),
             "pro + flash; kimi on disagreement": sum(pro[k] != flash[k] for k in pro)}
    lines = ["# Judges on the same atoms", "", f"{len(items)} model-judged items of deepseek-v4-pro:0813's split, {len(reference)} with a reference label "
             f"({carried} carried from identical wording, the rest labelled blind). 95% intervals: bootstrap by case.", "",
             "| Design | n | Agreement (95% CI) | Kappa | False facts found | Flagged false | Flags right | Extra calls |", "|---|---|---|---|---|---|---|---|"]
    table = {}
    for name, p in designs.items():
        s = score(reference, p)
        table[name] = s
        lines.append(f"| {name} | {s['n']} | {s['agree']:.1%} ({s['low']:.1%} to {s['high']:.1%}) | {s['kappa']:.2f} | {s['false_found']}/{s['false_total']} | "
                     f"{s['flagged']} | {s['flag_right']} | {extra.get(name, 0)} |")
    (ROOT / "reference" / "judge_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "reference" / "judge_comparison.json").write_text(json.dumps(table, indent=1) + "\n", encoding="utf-8")
    with (ROOT / "reference" / "judge_disagreements.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["atom_id", "text", "reference", "disagree", *MODELS])
        for k in sorted(reference, key=lambda k: -sum(pred[m][k] != reference[k] for m in MODELS)):
            d = sum(pred[m][k] != reference[k] for m in MODELS)
            if d:
                writer.writerow([k, items[k]["text"], reference[k], d, *[pred[m][k] for m in MODELS]])
    print("\n".join(lines))


if __name__ == "__main__":
    main()
