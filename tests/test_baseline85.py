"""VeriFact baseline on the 85 cases: retrieval rules and context format (no model calls).

Run:  python -m unittest tests.test_baseline85
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cm import baseline  # noqa: E402

VOCAB = ["potassium", "sodium", "heart", "norepinephrine", "oxygen"]


class FakeEmbedder:
    """Bag-of-words vectors over a tiny vocabulary, normalized like bge-m3's."""

    def embed(self, texts):
        out = []
        for t in texts:
            v = np.array([t.lower().count(w) for w in VOCAB], dtype=np.float32) + 0.01
            out.append(v / np.linalg.norm(v))
        return np.stack(out)


class FakeReranker:
    def scores(self, query, texts):
        return np.array([-len(t) for t in texts], dtype=np.float32)  # shortest text first


def row(text, t):
    return {"text": text, "observed_at": f"2150-01-0{t} 0{t}:00:00", "source_type": "laboratory",
            "semantics": "measurement"}


ROWS = [row("Potassium: 3.1 mEq/L", 1), row("Potassium: 3.1 mEq/L", 2), row("Sodium: 130 mEq/L", 3),
        row("Heart Rate: 110 bpm", 4), row("Infusion/input Norepinephrine at 0.05 mcg/kg/min", 5),
        row("O2 Flow: 2 L/min oxygen", 6)]


class RetrievalTests(unittest.TestCase):
    def test_dense_top_n(self):
        got = baseline.retrieve("potassium low", ROWS, "dense", 2, FakeEmbedder())
        self.assertEqual([r["text"] for r in got], ["Potassium: 3.1 mEq/L"] * 2)

    def test_hybrid_keeps_identical_text_once(self):
        got = baseline.retrieve("potassium low", ROWS, "hybrid", 3, FakeEmbedder())
        texts = [r["text"] for r in got]
        self.assertEqual(texts.count("Potassium: 3.1 mEq/L"), 1)
        self.assertEqual(texts[0], "Potassium: 3.1 mEq/L")
        # N from each retriever, fused, then de-duplicated: fewer than N can remain, as in VeriFact.
        self.assertEqual(len(texts), 2)

    def test_rerank_reorders_the_fused_pool(self):
        got = baseline.retrieve("potassium norepinephrine", ROWS, "rerank", 2, FakeEmbedder(), FakeReranker())
        lengths = [len(r["text"]) for r in got]
        self.assertEqual(lengths, sorted(lengths))
        with self.assertRaises(ValueError):
            baseline.retrieve("potassium", ROWS, "rerank", 2, FakeEmbedder(), None)

    def test_context_format(self):
        start, end = baseline.span(ROWS, None)
        text = baseline.absolute_time_context([ROWS[3], ROWS[0]], start, end)
        self.assertEqual(text.splitlines(), [
            "Hospital Admission Start: 2150-01-01 01:00:00",
            "Hospital Admission End: 2150-01-06 06:00:00",
            "Electronic Health Record Context",
            "Ordered by Time (Earliest to Latest):",
            "1. Date: 2150-01-01, Time: 01:00:00, Note Category: laboratory, Note Description: measurement "
            "| Text: Potassium: 3.1 mEq/L",
            "2. Date: 2150-01-04, Time: 04:00:00, Note Category: laboratory, Note Description: measurement "
            "| Text: Heart Rate: 110 bpm"])


if __name__ == "__main__":
    unittest.main()
