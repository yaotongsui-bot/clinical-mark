"""Metrics, a Markdown report, per-case score sheets, and a review sheet."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

FACT_LABELS = ("supported", "not_supported", "not_addressed", "unverifiable")
TREATMENT_SCORED = ("match", "partial_match", "not_done")
KIND_NAME = {"observed": "stated outright", "presupposition": "presupposed by an action",
             "judgment": "clinical judgment", "underspecified": "vague"}
TIER_NAME = {"vital": "vital", "okay": "okay", "all": "all"}


def _rate(num: int, den: int) -> float | None:
    return round(num / den, 3) if den else None


def _pct(value: float | None) -> str:
    return "-" if value is None else f"{value * 100:.1f}%"


def recall(cov: list[dict], tier: str | None = None) -> tuple[int, int]:
    rows = [g for g in cov if tier is None or g["importance"] == tier]
    return sum(g["covered"] for g in rows), len(rows)


def scoresheet(facts: list[dict]) -> dict:
    """VeriFact-style score sheet: the share of each label among a case's AI statements."""
    labels = Counter(f["label"] for f in facts)
    out = {"n": len(facts), **{k: labels[k] for k in FACT_LABELS},
           **{f"{k}_share": _rate(labels[k], len(facts)) for k in FACT_LABELS}}
    out["reasons"] = {k: [f"{f['text']} -- {f['reason']}" for f in facts if f["label"] == k]
                      for k in ("not_supported", "not_addressed")}
    return out


def case_metrics(facts: list[dict], actions: list[dict], cov: list[dict], cov3: list[dict]) -> dict:
    f = Counter(x["label"] for x in facts)
    t = Counter(x["label"] for x in actions if x["track"] == "treatment")
    scored = sum(t[k] for k in TREATMENT_SCORED)
    out = {"fact_accuracy": _rate(f["supported"], f["supported"] + f["not_supported"]),
           "not_supported": f["not_supported"], "treatment_precision": _rate(t["match"], scored)}
    for suffix, rows in (("", cov), ("_at3", cov3)):
        for tier in ("vital", "okay", None):
            hit, n = recall(rows, tier)
            out[f"recall_{tier or 'all'}{suffix}"] = _rate(hit, n)
    return out


def _micro_macro(cases: list[dict], key: str, tier: str | None) -> dict:
    hit = n = 0
    per_case = []
    for c in cases:
        h, m = recall(c[key], tier)
        hit, n = hit + h, n + m
        if m:
            per_case.append(h / m)
    return {"covered": hit, "total": n, "micro": _rate(hit, n),
            "macro": round(sum(per_case) / len(per_case), 3) if per_case else None}


def summarize(cases: list[dict]) -> dict:
    facts = [f for c in cases for f in c["facts"]]
    fact_labels = Counter(f["label"] for f in facts)
    by_kind = {}
    for kind in KIND_NAME:
        labels = Counter(f["label"] for f in facts if f["fact_kind"] == kind)
        by_kind[kind] = {"n": sum(labels.values()), "labels": dict(labels),
                         "accuracy": _rate(labels["supported"], labels["supported"] + labels["not_supported"])}
    treatments = [a for c in cases for a in c["actions"] if a["track"] == "treatment"]
    monitoring = [a for c in cases for a in c["actions"] if a["track"] == "monitoring"]
    t_labels = Counter(a["label"] for a in treatments)
    m_labels = Counter(a["label"] for a in monitoring)
    scored = sum(t_labels[k] for k in TREATMENT_SCORED)
    gold = [g for c in cases for g in c["coverage"]]
    judged = [x for c in cases for x in c["facts"] + c["actions"] if x.get("method") == "llm_panel"]
    items = [x for c in cases for x in c["facts"] + c["actions"]]
    unscored = {"not_addressed", "unverifiable", "unobservable", "vague_target", "condition_not_met"}
    return {
        "cases_evaluated": len(cases),
        "claims_per_case": round(sum(len(c["claims"]) for c in cases) / len(cases), 2) if cases else None,
        "ai_atoms": dict(Counter(a["kind"] for c in cases for a in c["atoms"])),
        "unscored_share": _rate(sum(x["label"] in unscored for x in items), len(items)),
        "facts": {"n": len(facts), "labels": dict(fact_labels),
                  "accuracy": _rate(fact_labels["supported"], fact_labels["supported"] + fact_labels["not_supported"]),
                  "cases_with_not_supported": sum(any(f["label"] == "not_supported" for f in c["facts"]) for c in cases),
                  "by_fact_kind": by_kind},
        "treatment_actions": {"n": len(treatments), "labels": dict(t_labels),
                              "precision_strict": _rate(t_labels["match"], scored),
                              "precision_lenient": _rate(t_labels["match"] + t_labels["partial_match"], scored)},
        "monitoring_actions": {"n": len(monitoring), "labels": dict(m_labels),
                               "performed_rate": _rate(m_labels["performed"], m_labels["performed"] + m_labels["not_performed"])},
        "goals_excluded": sum(1 for c in cases for a in c["atoms"] if a["kind"] == "goal"),
        "coverage": {
            **{f"{tier or 'all'}": _micro_macro(cases, "coverage", tier) for tier in ("vital", "okay", None)},
            **{f"{tier or 'all'}_at3": _micro_macro(cases, "coverage_at3", tier) for tier in ("vital", "okay", None)},
            "problem_linked": sum(g["problem_linked"] for g in gold),
            "problem_linked_missed": sum(g["problem_linked"] and not g["covered"] for g in gold),
            "most_missed_vital": Counter(g["name"] for g in gold if g["importance"] == "vital" and not g["covered"]).most_common(10),
        },
        "judge_panel": {"items": len(judged),
                        "agreement": dict(Counter(x["panel"]["agreement"] for x in judged))},
        "gold_standard": "patient records (pre-decision records for facts; post-decision clinician actions for actions)",
    }


def _evidence_text(evidence: list[dict]) -> str:
    parts = []
    for e in evidence[:3]:
        value = f" {e['value']} {e.get('unit', '')}".rstrip() if "value" in e else ""
        bounds = f" (reference {e['bounds']})" if "bounds" in e else ""
        parts.append(f"{e.get('time', '')} {e.get('item', '')}{value}{bounds}".strip())
    return "; ".join(parts)


def _cell(text: str) -> str:
    return str(text).replace("|", "/").replace("\n", " ")


def write_markdown(path: Path, summary: dict, cases: list[dict], meta: dict) -> None:
    s = summary
    f, t, m, cov, panel = s["facts"], s["treatment_actions"], s["monitoring_actions"], s["coverage"], s["judge_panel"]
    lines = [
        "# Evaluation of AI clinical suggestions against patient records", "",
        f"- Input: `{meta['triples']}`; {s['cases_evaluated']} cases, {s['claims_per_case']} AI suggestions per case on average.",
        f"- Models: atomizer `{meta['ai_model']}`; judge panel {', '.join(f'`{x}`' for x in meta['judge_models'])} "
        f"(majority vote; reasoning mode: {', '.join(meta.get('judge_think') or []) or 'none'}); "
        f"{meta['llm_calls']} new model calls, {meta['cache_hits']} cache hits.",
        "- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); "
        f"retrieval {meta.get('retrieval')}, top {meta.get('top_n')} records per statement.",
        "- Gold standard: pre-decision records for facts; clinician actions recorded after the decision "
        "(24 h or until ICU discharge) for actions.",
        "- A missing record does not prove something did not happen. Thresholds, treatment classes and "
        "importance tiers come from the editable files in `rules/`.",
        f"- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, "
        f"condition_not_met): {_pct(s['unscored_share'])} of all judged items.", "",
        "## 1. Does the AI state false facts?", "",
        "| Metric | Value |", "|---|---|",
        f"| Fact atoms | {f['n']} |",
        f"| supported / not_supported / not_addressed / unverifiable | "
        f"{' / '.join(str(f['labels'].get(k, 0)) for k in FACT_LABELS)} |",
        f"| Fact accuracy = supported / (supported + not_supported) | {_pct(f['accuracy'])} |",
        f"| Cases with at least one not_supported fact | {f['cases_with_not_supported']} / {s['cases_evaluated']} |", "",
        "| Fact kind | n | Accuracy | Labels |", "|---|---|---|---|",
    ]
    for kind, row in f["by_fact_kind"].items():
        lines.append(f"| {KIND_NAME[kind]} | {row['n']} | {_pct(row['accuracy'])} | {row['labels']} |")
    lines += ["", "## 2. How close is the AI to what clinicians did?", "",
              "Target (same class, or the drug the AI named) and direction (continue / stop / adjust) are decided "
              "by code; suggestions the rule file cannot classify go to the judge panel.", "",
              "| Metric | Value |", "|---|---|",
              f"| Treatment action atoms | {t['n']} |",
              f"| Labels | {t['labels']} |",
              f"| Agreement (strict) = match / (match + partial_match + not_done) | {_pct(t['precision_strict'])} |",
              f"| Agreement (lenient) = (match + partial_match) / same | {_pct(t['precision_lenient'])} |", "",
              f"Monitoring/assessment atoms: {m['n']} (reported separately, not part of agreement): {m['labels']}; "
              f"performed rate among observable items {_pct(m['performed_rate'])}. "
              f"{s['goals_excluded']} 'goal' atoms with no concrete action are not scored.", "",
              "## 3. What did the AI miss?", "",
              "Vital = a class the rule file marks vital, or one whose indication was present at the decision time "
              "(for example low potassium followed by potassium chloride). Other non-routine classes are okay.", "",
              "| Recall | All suggestions (micro / per-case) | First 3 suggestions only (micro / per-case) |",
              "|---|---|---|"]
    for tier in ("vital", "okay", "all"):
        a, b = cov[tier], cov[f"{tier}_at3"]
        lines.append(f"| {TIER_NAME[tier]} ({a['covered']}/{a['total']}) | {_pct(a['micro'])} / {_pct(a['macro'])} | "
                     f"{_pct(b['micro'])} / {_pct(b['macro'])} |")
    lines += ["", f"{cov['problem_linked']} clinician actions answered an abnormality present at the decision time; "
              f"the AI missed {cov['problem_linked_missed']} of them. Most often missed vital classes: "
              + ", ".join(f"{k} ({v})" for k, v in cov["most_missed_vital"]), "",
              "### Problem-linked omissions", "",
              "| Case | Clinicians gave | Indication at the decision time | AI suggestions |", "|---|---|---|---|"]
    for c in cases:
        for g in c["coverage"]:
            if g["problem_linked"] and not g["covered"]:
                lines.append(f"| {c['case_id']} | {g['name']} ({', '.join(g['doctor_targets'][:2])}) | "
                             f"{_cell(g['indication'])} | {'<br>'.join(_cell(x) for x in c['claims'])} |")
    lines += ["", "## 4. not_supported facts", "",
              "| Case | AI sentence | Atomic fact | Kind | Evidence |", "|---|---|---|---|---|"]
    for c in cases:
        for x in c["facts"]:
            if x["label"] == "not_supported":
                lines.append(f"| {c['case_id']} | {_cell(x['claim_text'])} | {_cell(x['text'])} | "
                             f"{KIND_NAME.get(x['fact_kind'], x['fact_kind'])} | {_cell(x['reason'])} |")
    lines += ["", "## 5. Judge panel", "",
              f"{panel['items']} items went to the judge panel. Agreement: {panel['agreement']} "
              "(split = no majority; the conservative label was used and the item needs human review).", "",
              "## 6. Per-case score sheets", "",
              "| Case | Facts | supported | not_supported | not_addressed | unverifiable | Treatment agreement | "
              "Vital recall | All recall |", "|---|---|---|---|---|---|---|---|---|"]
    for c in cases:
        sh, mm = c["scoresheet"], c["metrics"]
        lines.append(f"| {c['case_id']} | {sh['n']} | {_pct(sh['supported_share'])} | {_pct(sh['not_supported_share'])} | "
                     f"{_pct(sh['not_addressed_share'])} | {_pct(sh['unverifiable_share'])} | "
                     f"{_pct(mm['treatment_precision'])} | {_pct(mm['recall_vital'])} | {_pct(mm['recall_all'])} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_review_sheet(path: Path, cases: list[dict]) -> None:
    """One row per judged AI atom with the machine verdict, for manual review."""
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["case_id", "atom_id", "ai_sentence", "atom", "track", "subtype", "machine_label", "method",
                         "panel_votes", "reason", "evidence"])
        for c in cases:
            rows = [(x, "fact", x["fact_kind"]) for x in c["facts"]] + \
                   [(x, x["track"], x["action_class"]) for x in c["actions"]]
            for x, track, sub in rows:
                votes = x.get("panel", {}).get("votes")
                writer.writerow([c["case_id"], x["atom_id"], x["claim_text"], x["text"], track, sub, x["label"],
                                 x.get("method", "rule"), "; ".join(f"{k}: {v}" for k, v in votes.items()) if votes else "",
                                 x["reason"], _evidence_text(x["evidence"])])
