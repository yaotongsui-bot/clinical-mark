"""Reference annotations written by hand in a compact line format, converted to the evaluator's schemas.

Atomization (reference/atoms_*.txt), one block per case:
    ## <case id>
    A1                                  claim suffix; the claim id is <case id><suffix>
    F|<kind>|<concept>|<direction>|<time>|<text>      fact; kind = obs | pre | jud | und
    A|<action_class>|<concept>|<target>|<0/1>|<text>  action; the number is `conditional`
    G|<concept>|<text>                                goal
Specimen is "urine" when the text says urine, "none" for treatment premises, else "unspecified".
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cm import atomize, rules  # noqa: E402

KIND = {"obs": "observed", "pre": "presupposition", "jud": "judgment", "und": "underspecified"}
DIRECTIONS = set(atomize.DIRECTIONS)
TIMES = {"current", "recent", "persistent", "unspecified"}
ACTIONS = set(atomize.ACTION_CLASSES) - {"none"}
CONCEPTS = set(rules.ALL_CONCEPTS)


def parse_atoms(paths: list[str]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    case = claim = None
    for path in paths:
        for n, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            where = f"{path}:{n}"
            if not line or line.startswith("#!"):
                continue
            if line.startswith("## "):
                case, claim = line[3:].strip(), None
                assert case not in out, f"{where}: duplicate case {case}"
                out[case] = []
                continue
            if "|" not in line:
                claim = f"{case}{line}"
                continue
            assert case and claim, f"{where}: atom before a claim line"
            f = line.split("|")
            base = {"claim_id": claim, "fact_kind": "none", "direction": "none", "time": "none",
                    "specimen": "none", "action_class": "none", "target": "", "conditional": False}
            if f[0] == "F":
                assert len(f) == 6, f"{where}: fact needs 6 fields"
                _, kind, concept, direction, time, text = f
                assert kind in KIND and concept in CONCEPTS and direction in DIRECTIONS and time in TIMES, where
                specimen = "urine" if "urine" in text.lower() else ("none" if concept == "none" else "unspecified")
                atom = {**base, "kind": "fact", "fact_kind": KIND[kind], "concept": concept, "direction": direction,
                        "time": time, "specimen": specimen, "text": text}
            elif f[0] == "A":
                assert len(f) == 6, f"{where}: action needs 6 fields"
                _, cls, concept, target, cond, text = f
                assert cls in ACTIONS and concept in CONCEPTS and cond in {"0", "1"}, where
                atom = {**base, "kind": "action", "action_class": cls, "concept": concept, "target": target,
                        "conditional": cond == "1", "text": text}
            elif f[0] == "G":
                assert len(f) == 3, f"{where}: goal needs 3 fields"
                assert f[1] in CONCEPTS, where
                atom = {**base, "kind": "goal", "concept": f[1], "text": f[2]}
            else:
                raise AssertionError(f"{where}: unknown line {line!r}")
            out[case].append(atom)
    return out


def check_coverage(atoms: dict[str, list[dict]], triples: dict[str, dict]) -> None:
    for cid, t in triples.items():
        want = {c["claim_id"] for c in t["ai_generated"]["claims"]}
        have = {a["claim_id"] for a in atoms.get(cid, [])}
        assert want == have, f"{cid}: claims without atoms {sorted(want - have)}, unknown {sorted(have - want)}"


if __name__ == "__main__":
    atoms = parse_atoms(sorted(glob.glob(str(ROOT / "reference" / "atoms_*.txt"))))
    print(len(atoms), "cases", sum(map(len, atoms.values())), "atoms")
