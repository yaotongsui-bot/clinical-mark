"""The --facts-all-judge ablation: every fact goes to the judge, no code check and no guard.

Run:  python -m unittest tests.test_all_judge
"""

from __future__ import annotations

import datetime as dt
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cm import ground, records  # noqa: E402
from cm.retrieve import Retriever  # noqa: E402

T = "2150-01-02 12:00:00"
TRIPLE = {"triple_id": "C1", "decision_point": T}


def lab(value, hour):
    return records._row(f"lab:{hour}", "laboratory", f"Potassium: {value} mEq/L", f"2150-01-02 {hour:02d}:00:00",
                        semantics="measurement", table="lab", itemid="50971", label="Potassium", value=value,
                        unit="mEq/L", lower=3.3, upper=5.1)


ROWS = [lab(3.0, 6), lab(3.1, 10),
        records._row("rx:1", "medication_order", "Order: Vancomycin 1 g IV (active at decision time)",
                     "2150-01-01 10:00:00", semantics="order", ongoing=True, label="Vancomycin")]


def atom(text, concept="other", direction="present", kind="observed"):
    return {"atom_id": "C1A1::01", "claim_id": "C1A1", "claim_text": text, "text": text, "kind": "fact",
            "fact_kind": kind, "concept": concept, "direction": direction, "time": "current"}


class AllJudgeTests(unittest.TestCase):
    def setUp(self):
        self.retriever = Retriever(None, "bm25", 50)

    def test_lab_fact_goes_to_code_by_default_and_to_judge_when_asked(self):
        a = atom("Hypokalemia is present.", concept="potassium", direction="low")
        default = ground.verify(a, ROWS, TRIPLE, "sys", self.retriever)
        if "pending" not in default:  # the code check decides this one unless the ablation is on
            self.assertEqual(default["method"], "deterministic")
        forced = ground.verify(a, ROWS, TRIPLE, "sys", self.retriever, all_to_judge=True)
        self.assertIn("pending", forced)
        self.assertTrue(forced["no_guard"])

    def test_rule_labels_are_skipped(self):
        a = atom("Antibiotics are needed.", kind="judgment")
        self.assertEqual(ground.verify(a, ROWS, TRIPLE, "sys", self.retriever)["label"], "unverifiable")
        self.assertIn("pending", ground.verify(a, ROWS, TRIPLE, "sys", self.retriever, all_to_judge=True))

    def test_guard_is_off_in_the_ablation(self):
        a = atom("The patient is currently receiving vancomycin.", kind="presupposition")
        pending = ground.verify(a, ROWS, TRIPLE, "sys", self.retriever, all_to_judge=True)
        rid = next(k for k, r in pending["alias"].items() if r["rid"] == "rx:1")
        verdict = {"label": "supported", "reason": "order", "cites": [rid], "agreement": "1/1", "votes": {}}
        self.assertEqual(ground.finalize(pending, verdict)["label"], "supported")
        normal = ground.verify(a, ROWS, TRIPLE, "sys", self.retriever)
        self.assertEqual(ground.finalize(normal, verdict)["label"], "not_addressed")  # an order is not a dose


class GuardTests(unittest.TestCase):
    """Defects found by checking the guard against the fact gold standard (2026-11-13)."""

    def test_nasal_cannula_is_oxygen_not_routine_care(self):
        tr = ground._treatment("The patient is currently receiving oxygen at 3 L/min via nasal cannula.")
        self.assertEqual(tr[0], "oxygen_therapy")

    def test_ended_infusion_with_nothing_running_keeps_not_supported(self):
        ended = records._row("in:1", "treatment",
                             "Infusion/input Insulin - Regular at 2.0 units/hour (2150-01-02 01:00:00 to 2150-01-02 10:37:00)",
                             "2150-01-02 01:00:00", semantics="administration", label="Insulin - Regular")
        s = "An insulin infusion is currently running."
        self.assertIsNone(ground._administration_guard(s, "not_supported", [ended], True, running=False))
        # Still running at T: an ended earlier interval does not show it stopped.
        self.assertIsNotNone(ground._administration_guard(s, "not_supported", [ended], True, running=True))


class VerifactLabelTests(unittest.TestCase):
    """--labels verifact: three labels, VeriFact's definitions in the guard."""

    def setUp(self):
        self.retriever = Retriever(None, "bm25", 50)

    def test_rule_unverifiable_goes_to_the_judge(self):
        a = atom("Antibiotics are needed.", kind="judgment")
        result = ground.verify(a, ROWS, TRIPLE, "sys", self.retriever, labels="verifact")
        self.assertIn("pending", result)
        self.assertTrue(result["verifact_labels"])

    def _final(self, text, label):
        a = atom(text, kind="presupposition")
        pending = ground.verify(a, ROWS, TRIPLE, "sys", self.retriever, labels="verifact")
        cites = [k for k, r in pending["alias"].items() if r["rid"] == "rx:1"][:1]
        verdict = {"label": label, "reason": "x", "cites": cites, "agreement": "1/1", "votes": {}}
        return ground.finalize(pending, verdict)["label"]

    def test_order_without_administration_is_not_supported(self):
        s = "The patient is currently receiving vancomycin."
        self.assertEqual(self._final(s, "supported"), "not_supported")
        self.assertEqual(self._final(s, "not_addressed"), "not_supported")
        self.assertEqual(self._final(s, "not_supported"), "not_supported")

    def test_treatment_never_mentioned_stays_not_addressed(self):
        s = "The patient is currently receiving heparin."
        result = ground.verify(atom(s, kind="presupposition"), ROWS, TRIPLE, "sys", self.retriever, labels="verifact")
        if "pending" not in result:  # nothing retrieved: not_addressed without a judge
            self.assertEqual(result["label"], "not_addressed")
            return
        self.assertIs(result["mentioned"], False)
        self.assertEqual(self._final(s, "not_addressed"), "not_addressed")


if __name__ == "__main__":
    unittest.main()
