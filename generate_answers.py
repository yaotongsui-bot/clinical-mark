"""Generate the AI answers that get evaluated.

Variant "original" copies the system prompt, model, options and validation of the original
batch_generate_demo_claims.py (1-3 actions, temperature 0). Variant "open" changes only the
answer budget: up to 10 actions, most important first, so coverage is not capped by the
3-action limit. --samples K with --temperature > 0 draws K answers per case (seed + k) to
measure run-to-run variation; even at temperature 0 the model is not fully reproducible.

Usage
  python generate_answers.py --out input/mimic_triples_fixed.json      # fill answers cleared by fix_input.py
  python generate_answers.py --variant open --samples 3 --temperature 0.7
An existing --out file is resumed (only cases without an answer are generated); otherwise the
source is copied and its answers are kept as ai_generated_reference.
"""

from __future__ import annotations

import argparse
import copy
import datetime
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENDPOINT = "http://127.0.0.1:11434"
MODEL = "qwen2.5:7b-instruct-q4_K_M"
OPTIONS = {"temperature": 0, "seed": 20260925, "num_ctx": 32768, "num_predict": 400, "num_gpu": 99}
ALLOWED = {
    "ordered", "administered", "treatment_performed", "therapy_continued",
    "monitored", "specimen_collected", "procedure_performed",
    "imaging_performed", "assessment_performed", "disposition",
}
SYSTEM = (
    "You are testing a clinical action generation interface on deidentified data. "
    "Use only the record before the decision point. Return JSON with key claims, "
    "containing 1 to 3 distinct, concise, prospective clinical actions. "
    "Each claim must have text, action_type, and target. "
    "Choose action_type from ordered, administered, treatment_performed, "
    "therapy_continued, monitored, specimen_collected, procedure_performed, "
    "imaging_performed, assessment_performed, disposition. "
    "Do not imply a medication was administered based only on an order. "
    "Do not claim knowledge of what clinicians did after the decision point."
)
# The generator occasionally drifts into Chinese at temperature > 0; such answers are regenerated.
_CJK_RANGES = ((0x3000, 0x303F), (0x4E00, 0x9FFF), (0xFF00, 0xFFEF))  # CJK punctuation, ideographs, full-width forms
NON_ENGLISH = re.compile("[" + "".join(f"{chr(a)}-{chr(b)}" for a, b in _CJK_RANGES) + "]")
NEAR_MISS = {"monitoring": "monitored", "monitor": "monitored", "administer": "administered",
             "administration": "administered", "order": "ordered", "assessment": "assessment_performed",
             "assess": "assessment_performed", "procedure": "procedure_performed",
             "imaging": "imaging_performed", "treatment": "treatment_performed",
             "continue": "therapy_continued", "continued": "therapy_continued"}
VARIANTS = {
    "original": {"system": SYSTEM, "max_claims": 3, "num_predict": 400},
    "open": {"system": SYSTEM.replace(
        "containing 1 to 3 distinct, concise, prospective clinical actions.",
        "containing every distinct, concise, prospective clinical action you would recommend "
        "for the next 24 hours (up to 10), most important first."),
        "max_claims": 10, "num_predict": 1200},
}


def chat(payload: dict) -> dict:
    request = urllib.request.Request(ENDPOINT + "/api/chat", data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.load(response)


def validate(raw: dict, triple_id: str, max_claims: int, num_ctx: int) -> list[dict]:
    if raw.get("done_reason") not in (None, "stop"):
        raise ValueError(f"Unexpected done_reason={raw.get('done_reason')}")
    if (raw.get("prompt_eval_count") or 0) >= num_ctx - 400:
        raise ValueError("Prompt may have been truncated by context limit")
    claims = json.loads(raw["message"]["content"]).get("claims")
    if not isinstance(claims, list) or not 1 <= len(claims) <= max_claims:
        raise ValueError(f"Expected 1-{max_claims} claims")
    for idx, claim in enumerate(claims, 1):
        if not isinstance(claim, dict) or not all(
                isinstance(claim.get(k), str) and claim[k].strip() for k in ("text", "action_type", "target")):
            raise ValueError(f"Claim {idx} lacks required text")
        # The evaluator ignores action_type (its atomizer decides), so near misses are normalized.
        if NON_ENGLISH.search(claim["text"] + claim["target"]):
            raise ValueError(f"Claim {idx} is not written in English; write every claim in English")
        claim["action_type"] = NEAR_MISS.get(claim["action_type"].strip().lower(), claim["action_type"].strip())
        if claim["action_type"] not in ALLOWED:
            raise ValueError(f"Claim {idx} has unknown action_type {claim['action_type']!r}")
        claim["claim_id"] = f"{triple_id}A{idx}"
        claim["arm"] = MODEL
    return claims


def generate(source: Path, out: Path, variant: str, temperature: float, seed: int) -> None:
    spec = VARIANTS[variant]
    options = {**OPTIONS, "temperature": temperature, "seed": seed, "num_predict": spec["num_predict"]}
    if out.exists():
        doc = json.loads(out.read_text(encoding="utf-8"))  # resume: fill cases without an answer
    else:
        doc = json.loads(source.read_text(encoding="utf-8"))
        for triple in doc["triples"]:
            triple["ai_generated_reference"] = triple.get("ai_generated")
            triple["ai_generated"] = None
    raw_log = out.with_name(out.stem + "_generation_raw.jsonl")
    for i, triple in enumerate(doc["triples"], 1):
        if triple.get("ai_generated"):
            continue
        if triple["evaluation_eligibility"]["decision_within_icu_stay"] is not True:
            continue  # never evaluated
        tid = triple["triple_id"]
        payload = {"model": MODEL, "stream": False, "format": "json", "options": options,
                   "messages": [{"role": "system", "content": spec["system"]},
                                {"role": "user", "content": triple["case_prompt"]["text"]}]}
        started = time.monotonic()
        for attempt in range(3):
            raw = chat(payload)
            try:
                claims = validate(raw, tid, spec["max_claims"], options["num_ctx"])
                break
            except (ValueError, json.JSONDecodeError) as exc:
                if attempt == 2:
                    raise
                payload["messages"].append({"role": "user", "content": (
                    f"Your previous JSON did not match the required schema: {exc}. Regenerate the entire "
                    "JSON object. Use only the action_type values " + ", ".join(sorted(ALLOWED)) + ".")})
        triple["ai_generated"] = {"arm": MODEL, "variant": variant, "claims": claims, "options": options,
                                  "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        with raw_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"triple_id": tid, "response": raw}, ensure_ascii=False) + "\n")
        print(f"[{out.stem} {i}/{len(doc['triples'])}] {tid} claims={len(claims)} "
              f"({time.monotonic() - started:.1f}s)", flush=True)
        if i % 10 == 0:  # checkpoint; rerunning resumes
            out.write_text(json.dumps(doc, ensure_ascii=False) + "\n", encoding="utf-8")
    doc["generation"] = {**doc.get("generation", {}), "model": MODEL, "variant": variant,
                         "system_prompt": spec["system"], "options": options}
    out.write_text(json.dumps(doc, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "input" / "mimic_triples_fixed.json")
    parser.add_argument("--out", type=Path, help="output file (single sample); default input/mimic_triples_<variant>_s<k>.json")
    parser.add_argument("--variant", choices=sorted(VARIANTS), default="original")
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()
    for k in range(1, args.samples + 1):
        out = args.out if args.out and args.samples == 1 else \
            ROOT / "input" / f"mimic_triples_{args.variant}_s{k}.json"
        generate(args.source, out, args.variant, args.temperature, OPTIONS["seed"] + k - 1)
        print(f"done -> {out}", flush=True)


if __name__ == "__main__":
    main()
