"""MIMIC-III clinical notes (NOTEEVENTS) as the reference EHR, in VeriFact's layout.

The VeriFact-BHC release keeps the reference EHR as MIMIC-III tables (repository script
scripts/dataset/sample_mimic_dataset.py):
  reference_ehr/ehr_noteevents.csv.gz   every note of the 100 patients except the discharge summaries
                                        (NOTEEVENTS columns ROW_ID, SUBJECT_ID, HADM_ID, CHARTDATE,
                                        CHARTTIME, STORETIME, CATEGORY, DESCRIPTION, CGID, ISERROR, TEXT)
  reference_ehr/admissions.csv.gz       the BHC admission of each patient (ADMISSIONS columns,
                                        ADMITTIME and DISCHTIME are used)
Column names are matched without regard to case, so the full MIMIC-III NOTEEVENTS / ADMISSIONS
tables can be read the same way.

VeriFact turns notes into "facts" (sentences, or LLM atomic claims, after semantic chunking to 128
tokens). Here a fact is a sentence-like span cut at about 60 words, which stands in for VeriFact's
sentence fact type; atomic claims of notes are not built. Identical fact texts are kept once
(VeriFact's deduplicate_text).

The reference context is written exactly as VeriFact's "absolute time" format
(packages/llm_judge/src/llm_judge/reference_context.py), so a judge sees the same layout whichever
retrieval produced the facts.
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import re
import sys
from collections import defaultdict
from pathlib import Path

DISCHARGE = "discharge summary"
MAX_WORDS = 60
_DEID = re.compile(r"\[\*\*(.*?)\*\*\]")  # MIMIC-III de-identification placeholders
_BREAK = re.compile(r"\n\s*\n|\n(?=\s*(?:[-*•]|\d+[.)])\s)|(?<=[.!?])\s+(?=[A-Z])")


def _open(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return path.open(encoding="utf-8", newline="")


def _rows(path: Path):
    csv.field_size_limit(min(sys.maxsize, 2 ** 31 - 1))
    with _open(path) as handle:
        reader = csv.DictReader(handle)
        reader.fieldnames = [f.strip().lower() for f in reader.fieldnames or []]
        yield from reader


def _get(row: dict, name: str) -> str:
    return (row.get(name) or "").strip()


def _ts(value: str) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(value.strip()) if value and value.strip() else None
    except ValueError:
        return None


def read_notes(path: Path, subjects: set[str] | None = None) -> dict[str, list[dict]]:
    """subject_id -> notes, sorted by CHARTDATE, CHARTTIME, STORETIME. Rows marked ISERROR are dropped."""
    out: dict[str, list[dict]] = defaultdict(list)
    for n, row in enumerate(_rows(path), 1):
        if n == 1 and not {"subject_id", "text"} <= set(row):
            raise ValueError(f"{path.name} needs SUBJECT_ID and TEXT columns; it has {sorted(row)}")
        subject = _get(row, "subject_id")
        if subjects is not None and subject not in subjects:
            continue
        if _get(row, "iserror") in {"1", "1.0", "True", "true"}:
            continue
        out[subject].append({
            "note_id": _get(row, "row_id") or f"n{n}", "subject_id": subject, "hadm_id": _get(row, "hadm_id"),
            "chartdate": _ts(_get(row, "chartdate")), "charttime": _ts(_get(row, "charttime")),
            "storetime": _ts(_get(row, "storetime")), "category": _get(row, "category"),
            "description": _get(row, "description"), "text": row.get("text") or ""})
    for notes in out.values():
        notes.sort(key=_order)
    return out


def read_admissions(path: Path) -> dict[str, tuple[dt.datetime, dt.datetime]]:
    """subject_id -> (ADMITTIME, DISCHTIME) of the first listed admission, as VeriFact's judge_subject."""
    out = {}
    for row in _rows(path):
        subject = _get(row, "subject_id")
        if subject not in out:
            out[subject] = (_ts(_get(row, "admittime")), _ts(_get(row, "dischtime")))
    return out


def _order(row: dict):
    far = dt.datetime.max
    return (row["chartdate"] or far, row["charttime"] or far, row["storetime"] or far)


def clean(text: str) -> str:
    """'[**Hospital1 18**]' -> 'Hospital1 18'; collapse spaces inside a line."""
    text = _DEID.sub(lambda m: m.group(1).strip(), text)
    return "\n".join(" ".join(line.split()) for line in text.splitlines())


def split_facts(text: str) -> list[str]:
    spans = []
    for part in _BREAK.split(clean(text)):
        words = " ".join(part.split()).split(" ")
        for start in range(0, len(words), MAX_WORDS):
            span = " ".join(words[start:start + MAX_WORDS]).strip(" -*•")
            if len(span) >= 3 and re.search(r"[A-Za-z]", span):
                spans.append(span)
    return spans


def reference_rows(notes: list[dict], *, admission: tuple[dt.datetime, dt.datetime] | None = None,
                   exclude_discharge: bool = True, deduplicate: bool = True) -> list[dict]:
    """Fact rows from a patient's notes for cm.retrieve.Retriever.

    admission: (start, end) keeps notes whose CHARTDATE falls from midnight of the start date to
    23:59:59 of the end date (VeriFact's reference_only_admission); None keeps the whole EHR.
    """
    rows, seen = [], set()
    if admission:
        lo = dt.datetime.combine(admission[0].date(), dt.time.min)
        hi = dt.datetime.combine(admission[1].date(), dt.time(23, 59, 59))
    for note in notes:
        if exclude_discharge and note["category"].lower().startswith(DISCHARGE):
            continue
        if admission and not (note["chartdate"] and lo <= note["chartdate"] <= hi):
            continue
        when = note["charttime"] or note["chartdate"]
        for i, fact in enumerate(split_facts(note["text"]), 1):
            if deduplicate:
                if fact in seen:
                    continue
                seen.add(fact)
            rows.append({"rid": f"{note['note_id']}:{i}", "text": fact,
                         "observed_at": when.isoformat(sep=" ") if when else "",
                         "chartdate": note["chartdate"], "charttime": note["charttime"],
                         "storetime": note["storetime"], "category": note["category"],
                         "description": note["description"],
                         "source_type": " / ".join(x for x in (note["category"], note["description"]) if x) or "note",
                         "table": "note", "label": ""})
    return rows


def _stamp(value: dt.datetime | None) -> str:
    return str(value) if value else "None"  # pandas Timestamp prints as 'YYYY-MM-DD HH:MM:SS'


def absolute_time_context(facts: list[dict], admission: tuple[dt.datetime, dt.datetime] | None) -> str:
    """VeriFact's 'absolute time' reference context, character for character."""
    start, end = admission or (None, None)
    out = (f"Hospital Admission Start: {_stamp(start)}\n"
           f"Hospital Admission End: {_stamp(end)}\n"
           "Electronic Health Record Context\n"
           "Ordered by Time (Earliest to Latest):\n")
    for i, f in enumerate(sorted(facts, key=_order), 1):
        date = f["chartdate"].strftime("%Y-%m-%d") if f["chartdate"] else "Unknown"
        time = f["charttime"].strftime("%H:%M:%S") if f["charttime"] else "Unknown"
        out += (f"{i}. Date: {date}, Time: {time}, Note Category: {f['category']}, "
                f"Note Description: {f['description']} | Text: {f['text']}\n")
    return out
