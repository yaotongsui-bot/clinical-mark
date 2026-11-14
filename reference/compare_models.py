"""Compare the evaluator's results across judge/atomizer models on the same frozen answers.

Writes reference/model_comparison.md and reference/model_comparison.json:
  - per model and answer set: item counts and the main measures;
  - pairwise agreement on atomization (F1 of normalized item tuples, per sentence);
  - pairwise agreement on verdicts for items both models extracted (same sentence and tuple, four tiers);
  - per sentence, how far the models disagree, to focus the reference answer.

An item tuple is what the rule files decide, so wording does not count:
  fact   -> (fact, concept, direction)
  action -> (action, action class, treatment class or measure)
"""

from __future__ import annotations

import collections
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ["deepseek-v4.1-flash", "glm-5.3-flash", "minimax-m3.1-flash", "glm-5.3", "mimo-v2.6-pro",
          "muse-spark-open", "deepseek-v4-pro_0813", "kimi-k3.1-pro"]
SETS = {"base": ROOT / "results_models", "s1": ROOT / "results_models_open/s1",
        "s2": ROOT / "results_models_open/s2", "s3": ROOT / "results_models_open/s3"}
TIER = {"supported": "positive", "not_supported": "negative", "not_addressed": "undetermined", "unverifiable": "undetermined",
        "match": "positive", "partial_match": "positive", "performed": "positive", "not_done": "negative",
        "not_performed": "negative", "vague_target": "undetermined", "unobservable": "undetermined",
        "condition_not_met": "undetermined"}


def item_key(x: dict) -> tuple:
    if x["kind"] == "fact":
        return ("fact", x.get("concept"), x.get("direction"))
    return ("action", x.get("action_class"), x.get("treatment_class") or x.get("concept"))


def load(path: Path) -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((path / "cases").glob("*.json"))}


def sentence_items(cases: dict[str, dict]) -> dict[str, collections.Counter]:
    out: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for case in cases.values():
        for a in case["atoms"]:
            if a["kind"] != "goal":
                out[a["claim_id"]][item_key(a)] += 1
    return out


def verdicts(cases: dict[str, dict], judged_only: bool = False) -> dict[tuple, str]:
    """(sentence, tuple) -> tier; a tuple seen twice in one sentence keeps its first verdict."""
    out: dict[tuple, str] = {}
    for case in cases.values():
        for x in case["facts"] + case["actions"]:
            if not judged_only or x.get("method") == "llm_panel":
                out.setdefault((x["claim_id"], item_key(x)), TIER[x["label"]])
    return out


def f1(a: dict, b: dict) -> float:
    both = sum(sum((a.get(k, collections.Counter()) & b.get(k, collections.Counter())).values()) for k in set(a) | set(b))
    na, nb = sum(sum(c.values()) for c in a.values()), sum(sum(c.values()) for c in b.values())
    return 2 * both / (na + nb) if na + nb else 1.0


def kappa(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    n = len(pairs)
    po = sum(x == y for x, y in pairs) / n
    ca, cb = collections.Counter(x for x, _ in pairs), collections.Counter(y for _, y in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe != 1 else None


def main() -> None:
    lines = ["# Model comparison", "", "Each model split the frozen answers and was the only judge; the code rules are the same.", ""]
    payload: dict = {}
    for name, root in SETS.items():
        runs = {m: load(root / m) for m in MODELS}
        assert all(len(c) == 85 for c in runs.values()), name
        lines += [f"## Answer set {name}", "",
                  "| Model | Items | Facts | Actions | Goals | Fact accuracy | Cases with false fact | Treatment agreement | Key treatments mentioned | Facts omitted | Judged by a model |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
        rows = []
        for m in MODELS:
            s = json.loads((root / m / "summary.json").read_text(encoding="utf-8"))
            ai = s["ai_atoms"]
            row = {"model": m, "items": sum(ai.values()), **ai, "fact_accuracy": s["facts"]["accuracy"],
                   "cases_false": s["facts"]["cases_with_not_supported"] / 85,
                   "treat_agree": s["treatment_actions"]["precision_lenient"], "key_recall": s["coverage"]["vital"]["micro"],
                   "facts_omitted": s["omissions"]["facts"]["omitted"], "judged": s["judge_panel"]["items"]}
            rows.append(row)
            lines.append(f"| {m} | {row['items']} | {ai['fact']} | {ai['action']} | {ai.get('goal', 0)} | {row['fact_accuracy']:.1%} | "
                         f"{row['cases_false']:.1%} | {row['treat_agree']:.1%} | {row['key_recall']:.1%} | {row['facts_omitted']} | {row['judged']} |")
        items = {m: sentence_items(c) for m, c in runs.items()}
        verd = {m: verdicts(c) for m, c in runs.items()}
        judged = {m: verdicts(c, judged_only=True) for m, c in runs.items()}
        pairs = []
        for a, b in itertools.combinations(MODELS, 2):
            shared = sorted(set(verd[a]) & set(verd[b]))
            vp = [(verd[a][k], verd[b][k]) for k in shared]
            k = kappa(vp)
            jp = [(judged[a][key], judged[b][key]) for key in set(judged[a]) & set(judged[b])]
            pairs.append({"a": a, "b": b, "item_f1": f1(items[a], items[b]), "shared": len(shared),
                          "verdict_agreement": sum(x == y for x, y in vp) / len(vp) if vp else None, "kappa": k,
                          "judged_agreement": sum(x == y for x, y in jp) / len(jp) if jp else None, "judged_kappa": kappa(jp)})
        mean = lambda key: sum(p[key] for p in pairs if p[key] is not None) / max(1, sum(p[key] is not None for p in pairs))
        lines += ["", f"Pairwise means over {len(pairs)} model pairs: item F1 {mean('item_f1'):.2f}, verdict agreement on shared items "
                      f"{mean('verdict_agreement'):.1%}, Cohen's kappa {mean('kappa'):.2f}; on items both judged by a model "
                      f"(code rules left out) {mean('judged_agreement'):.1%}, kappa {mean('judged_kappa'):.2f}.", "",
                  "| Model | Mean item F1 with the others | Mean verdict agreement | Mean kappa |", "|---|---|---|---|"]
        per = {}
        for m in MODELS:
            mine = [p for p in pairs if m in (p["a"], p["b"])]
            per[m] = {k: sum(p[k] for p in mine if p[k] is not None) / max(1, sum(p[k] is not None for p in mine))
                      for k in ("item_f1", "verdict_agreement", "kappa")}
            lines.append(f"| {m} | {per[m]['item_f1']:.2f} | {per[m]['verdict_agreement']:.1%} | {per[m]['kappa']:.2f} |")
        lines.append("")
        payload[name] = {"rows": rows, "pairs": pairs, "per_model": per}
    out = ROOT / "reference"
    (out / "model_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "model_comparison.json").write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
