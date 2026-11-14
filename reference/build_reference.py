"""Run the evaluator with hand-written reference answers (model name claude-ref) instead of model calls.

    python reference/build_reference.py dump      write the atomization answers to the cache, then write the
                                                  judge requests to reference/judge_requests.json
    python reference/build_reference.py run       add reference/verdicts_*.txt to the cache and finish the run

Verdict files hold one line per judge request:  <request key>|<label>|<cited ids, comma-separated>|<reason>
Results go to results_reference/base, in the same format as every other run.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "reference"))
import run as evaluator  # noqa: E402
from cm import atomize  # noqa: E402
from compact import check_coverage, parse_atoms  # noqa: E402

MODEL = "claude-ref"
OUT = ROOT / "results_reference" / "base"
TRIPLES = ROOT / "input" / "mimic_triples_deepseek.json"
REQUESTS = ROOT / "reference" / "judge_requests.json"
ARGV = ["run.py", "--triples", str(TRIPLES), "--out-dir", str(OUT), "--ai-model", MODEL, "--judge-models", MODEL,
        "--judge-think", "", "--mimic-root", str(ROOT / "data" / "mimic-iv-demo")]


def write_atomization() -> None:
    triples = json.loads(TRIPLES.read_text(encoding="utf-8"))["triples"]
    triples = {t["triple_id"]: t for t in triples if t["evaluation_eligibility"]["decision_within_icu_stay"] is True}
    atoms = parse_atoms(sorted(glob.glob(str(ROOT / "reference" / "atoms_*.txt"))))
    check_coverage(atoms, triples)
    system = (ROOT / "prompts" / "ai_atomizer.txt").read_text(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "model_cache.jsonl").open("w", encoding="utf-8") as handle:
        for cid, t in triples.items():
            user, _ = atomize.user_prompt(t)
            record = {"stage": "ai_atomization", "case_id": cid, "elapsed_seconds": 0,
                      "request": [MODEL, system, user, atomize.SCHEMA], "reasoning": None, "done_reason": "reference",
                      "raw_response": "", "response": {"atoms": atoms[cid]}}
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(len(atoms), "cases of atoms written to the cache")


def dump_requests() -> None:
    write_atomization()

    def capture(panel) -> None:
        rows = [{"key": r.key, "stage": r.stage, "case_id": r.case_id, "system": r.system, "user": r.user,
                 "schema": r.schema, "cite_key": r.cite_key} for r in panel.requests.values()]
        REQUESTS.write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding="utf-8")
        print(len(rows), "judge requests written to", REQUESTS)
        raise SystemExit(0)

    evaluator.Panel.run = capture
    sys.argv = ARGV
    evaluator.main()


def run_all() -> None:
    write_atomization()
    requests = {r["key"]: r for r in json.loads(REQUESTS.read_text(encoding="utf-8"))}
    verdicts = {}
    dropped = []
    # The blind verdicts first; reference/adjudicated.txt then replaces any it names (see that file's header).
    for path in [*sorted(glob.glob(str(ROOT / "reference" / "verdicts_*.txt"))), str(ROOT / "reference" / "adjudicated.txt")]:
        adjudicated = path.endswith("adjudicated.txt")
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            key, label, cites, reason = line.split("|", 3)
            if key not in requests:
                assert not adjudicated, f"unknown request {key}"
                dropped.append(key)  # the rule files now decide this item, or its wording changed
                continue
            assert adjudicated or key not in verdicts, f"duplicate verdict {key}"
            verdicts[key] = (label, [c.strip() for c in cites.split(",") if c.strip()], reason.strip())
    print(len(dropped), "blind verdicts no longer needed:", dropped)
    missing = sorted(set(requests) - set(verdicts))
    assert not missing, f"{len(missing)} requests without a verdict, e.g. {missing[:5]}"
    with (OUT / "model_cache.jsonl").open("a", encoding="utf-8") as handle:
        for key, (label, cites, reason) in verdicts.items():
            r = requests[key]
            cited = cites if r["cite_key"] == "evidence" else (cites[0] if cites else None)
            response = {"label": label, r["cite_key"]: cited, "reason": reason}
            record = {"stage": f"{r['stage']}:{MODEL}", "case_id": r["case_id"], "elapsed_seconds": 0,
                      "request": [MODEL, r["system"], r["user"], r["schema"]], "reasoning": None,
                      "done_reason": "reference", "raw_response": "", "response": response}
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(len(verdicts), "verdicts written to the cache")
    sys.argv = ARGV
    evaluator.main()


if __name__ == "__main__":
    {"dump": dump_requests, "run": run_all}[sys.argv[1]]()
