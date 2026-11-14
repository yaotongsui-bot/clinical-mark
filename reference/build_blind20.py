"""Blind test on 20 up-to-10-claim cases: Claude's split and verdicts are written before any model judges these items.

    python reference/build_blind20.py dump    cache the split and write reference/open_split/judge_requests.json
    python reference/build_blind20.py run     add reference/open_split/verdicts.txt and write results_blind20/reference
    python reference/build_blind20.py judge <folder> <judges, comma-separated>    a vote on the same atoms, in results_blind20/<folder>
"""

from __future__ import annotations

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
FOLDER = ROOT / "reference" / "open_split"
TRIPLES = FOLDER / "triples_blind20.json"
REQUESTS = FOLDER / "judge_requests.json"
OUT = ROOT / "results_blind20" / "reference"
VOTE = ROOT / "results_blind20" / "vote"


def argv(out: Path, judges: list[str]) -> list[str]:
    args = ["run.py", "--triples", str(TRIPLES), "--out-dir", str(out), "--ai-model", MODEL, "--judge-think", ""]
    return args + (["--judge-models", ",".join(judges)] if judges else [])


def split_lines() -> list[str]:
    triples = {t["triple_id"]: t for t in json.loads(TRIPLES.read_text(encoding="utf-8"))["triples"]}
    atoms = parse_atoms([str(FOLDER / "atoms_blind20.txt")])
    check_coverage(atoms, triples)
    system = (ROOT / "prompts" / "ai_atomizer.txt").read_text(encoding="utf-8")
    lines = []
    for cid, t in triples.items():
        user, _ = atomize.user_prompt(t)
        lines.append(json.dumps({"stage": "ai_atomization", "case_id": cid, "elapsed_seconds": 0, "request": [MODEL, system, user, atomize.SCHEMA],
                                 "reasoning": None, "done_reason": "reference", "raw_response": "", "response": {"atoms": atoms[cid]}}, ensure_ascii=False))
    print(sum(map(len, atoms.values())), "atoms in", len(atoms), "cases")
    return lines


def write_split(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    if not (out / "model_cache.jsonl").exists() or out == OUT:
        (out / "model_cache.jsonl").write_text("\n".join(split_lines()) + "\n", encoding="utf-8")
    for sub in ("atoms", "cases"):
        for f in (out / sub).glob("*.json") if (out / sub).exists() else []:
            f.unlink()


def dump() -> None:
    write_split(OUT)

    def capture(panel) -> None:
        rows = [{"key": r.key, "stage": r.stage, "case_id": r.case_id, "system": r.system, "user": r.user, "schema": r.schema, "cite_key": r.cite_key}
                for r in panel.requests.values()]
        REQUESTS.write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding="utf-8")
        print(len(rows), "judge requests written")
        raise SystemExit(0)

    evaluator.Panel.run = capture
    sys.argv = argv(OUT, [MODEL])
    evaluator.main()


def run_reference() -> None:
    write_split(OUT)
    requests = {r["key"]: r for r in json.loads(REQUESTS.read_text(encoding="utf-8"))}
    verdicts = {}
    for line in (FOLDER / "verdicts.txt").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            key, label, cites, reason = line.split("|", 3)
            assert key in requests, key
            assert key not in verdicts, key
            verdicts[key] = (label, [c.strip() for c in cites.split(",") if c.strip()], reason.strip())
    # Revisions after checking disagreements with the first vote; verdicts.txt stays the blind original.
    for line in (FOLDER / "adjudicated.txt").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            key, label, cites, reason = line.split("|", 3)
            assert key in verdicts, key
            verdicts[key] = (label, [c.strip() for c in cites.split(",") if c.strip()], reason.strip())
    missing = sorted(set(requests) - set(verdicts))
    assert not missing, f"{len(missing)} without a verdict: {missing[:5]}"
    with (OUT / "model_cache.jsonl").open("a", encoding="utf-8") as handle:
        for key, (label, cites, reason) in verdicts.items():
            r = requests[key]
            answer = cites if r["cite_key"] == "evidence" else (cites[0] if cites else None)
            handle.write(json.dumps({"stage": f"{r['stage']}:{MODEL}", "case_id": r["case_id"], "elapsed_seconds": 0, "request": [MODEL, r["system"], r["user"], r["schema"]],
                                     "reasoning": None, "done_reason": "reference", "raw_response": "", "response": {"label": label, r["cite_key"]: answer, "reason": reason}}, ensure_ascii=False) + "\n")
    sys.argv = argv(OUT, [MODEL])
    evaluator.main()


def judge(name: str, judges: list[str]) -> None:
    out = ROOT / "results_blind20" / name
    write_split(out)
    sys.argv = argv(out, judges)
    evaluator.main()


if __name__ == "__main__":
    if sys.argv[1] == "judge":
        judge(sys.argv[2], sys.argv[3].split(","))
    else:
        {"dump": dump, "run": run_reference}[sys.argv[1]]()
