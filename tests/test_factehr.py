"""FactEHR baseline: prompt, answer parsing and the binary scoring (no model calls).

Run:  python -m unittest tests.test_factehr
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import run_factehr  # noqa: E402
import score_factehr  # noqa: E402


class PromptTests(unittest.TestCase):
    def setUp(self):
        self.template = (ROOT / "prompts" / f"{run_factehr.PROMPT}.txt").read_text(encoding="utf-8")

    def test_template_as_published(self):
        # entailment_binary6.tmpl keeps a space before two line breaks and ends with a blank line.
        self.assertIn("with the following keys: \n'entailment_prediction'", self.template)
        self.assertIn("can be entailed. \nOnly return", self.template)
        self.assertTrue(self.template.endswith("Here is the JSON-formatted answer:\n\n"))
        self.assertEqual(self.template.count("{premise}"), 1)
        self.assertEqual(self.template.count("{hypothesis}"), 1)

    def test_fill_keeps_braces_in_record_text(self):
        got = run_factehr.fill(self.template, "1. Text: dose {per kg}", "Heparin is given.")
        self.assertIn("Premise: 1. Text: dose {per kg}\nHypothesis: Heparin is given.\n", got)


class ParseTests(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(run_factehr.parse({"entailment_prediction": 1}), "supported")
        self.assertEqual(run_factehr.parse({"entailment_prediction": "0"}), "not_supported")

    def test_other_values_rejected(self):
        with self.assertRaises(KeyError):
            run_factehr.parse({"entailment_prediction": 2})


class BinaryScoringTests(unittest.TestCase):
    def test_merge(self):
        self.assertEqual(score_factehr.binary("supported"), "supported")
        for label in ("not_supported", "not_addressed", "unverifiable"):
            self.assertEqual(score_factehr.binary(label), "not_supported")


if __name__ == "__main__":
    unittest.main()
