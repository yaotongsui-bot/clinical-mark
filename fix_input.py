"""Repair text values the frozen input lost, and rebuild the AI's case prompt from the repaired rows.

The original extractor rendered every lab/chart row from `valuenum`. Text results therefore became
blank ("Intubated" instead of "Intubated: NOT INTUBATED.") or internal codes ("Ventilator Mode 11"
instead of "Ventilator Mode: CPAP/PSV"). Only those rows are changed here; the time cut, case
selection, clinician actions and every other prompt line stay byte-identical. The old AI answer
is kept under `ai_generated_before_fix` and `ai_generated` is cleared for regeneration.

Usage
  python fix_input.py
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECTIONS = {"Laboratory": "laboratory", "Vital signs": "monitoring"}
_SUFFIX = re.compile(r"( \((?:latest \d+ of \d+ measurements|recorded [^)]*)\))$")


def _rows(path: Path):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle)


def _is_number(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def load_raw_text_values(mimic_root: Path, triples: list[dict]) -> dict[str, str]:
    """record_id -> original MIMIC text for prompt rows whose text value was lost when frozen."""
    wanted = {e.get("record_id") for t in triples for e in t["case_prompt"].get("evidence") or []}
    out = {}

    def keep(key: str, value: str) -> None:
        value = (value or "").strip()
        if key in wanted and value and not _is_number(value):
            out[key] = value

    for row in _rows(mimic_root / "hosp" / "labevents.csv.gz"):
        keep(f"labevents:{row['labevent_id']}", row.get("value"))
    for row in _rows(mimic_root / "icu" / "chartevents.csv.gz"):
        keep(f"chartevents:{row['stay_id']}:{row['itemid']}:{row['charttime']}", row.get("value"))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--triples", type=Path, default=ROOT / "input" / "mimic_frozen_triples.json")
    parser.add_argument("--mimic-root", type=Path, default=ROOT / "data" / "mimic-iv-demo")
    parser.add_argument("--out", type=Path, default=ROOT / "input" / "mimic_triples_fixed.json")
    args = parser.parse_args()

    doc = json.loads(args.triples.read_text(encoding="utf-8"))
    raw_text = load_raw_text_values(args.mimic_root.resolve(), doc["triples"])
    changed_rows, changed_cases = 0, 0
    for triple in doc["triples"]:
        prompt = triple["case_prompt"]
        lines = prompt["text"].split("\n")
        # The two sections are exactly '; '.join(row texts); refuse to patch anything else.
        for i, line in enumerate(lines):
            head, _, body = line.partition(": ")
            if head in SECTIONS:
                rendered = "; ".join(e["text"] for e in prompt["evidence"] if e["source_type"] == SECTIONS[head])
                if body.rstrip(".") != rendered.rstrip("."):
                    raise ValueError(f"{triple['triple_id']}: '{head}' line does not match its evidence rows")
        n = 0
        for row in prompt["evidence"]:
            value = raw_text.get(row.get("record_id"))
            if not value or row["source_type"] not in SECTIONS.values():
                continue
            details = row.setdefault("details", {})
            suffix = _SUFFIX.search(row["text"])
            # Keep a numeric code next to the text: for scales (GCS, RASS, Braden) it is the score.
            code = f" ({details['value']})" if str(details.get("value") or "").strip() else ""
            row["text"] = f"{details.get('label') or row['text']}: {value}{code}{suffix.group(1) if suffix else ''}"
            details["frozen_value"] = details.get("value")
            details["value"] = value
            details["value_source"] = "restored_text_from_mimic"
            n += 1
        for i, line in enumerate(lines):
            head, _, body = line.partition(": ")
            if head in SECTIONS:
                rendered = "; ".join(e["text"] for e in prompt["evidence"] if e["source_type"] == SECTIONS[head])
                lines[i] = f"{head}: {rendered}{'.' if body.endswith('.') else ''}"
        prompt["text"] = "\n".join(lines)
        triple["ai_generated_before_fix"] = triple.get("ai_generated")
        triple["ai_generated"] = None
        triple["input_fix"] = {"restored_text_rows": n}
        changed_rows += n
        changed_cases += bool(n)
    doc["input_fix"] = {
        "description": "Lab/chart rows whose text result was lost (blank or numeric code) restored from MIMIC; "
                       "only the Laboratory and Vital signs prompt lines were re-rendered.",
        "restored_rows": changed_rows, "cases_changed": changed_cases,
        "known_limitation": "Chart rows with no valuenum at all were dropped by the original extractor and are still absent.",
        "source": str(args.triples),
    }
    args.out.write_text(json.dumps(doc, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"restored {changed_rows} rows in {changed_cases}/{len(doc['triples'])} cases -> {args.out}")


if __name__ == "__main__":
    main()
