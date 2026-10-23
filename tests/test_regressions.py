"""Regression checks for scoring defects found by review and by the known-answer tests.

Run from the project folder:  python -m unittest discover tests
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cm import atomize, concord, ground, records, rules  # noqa: E402

T = dt.datetime(2150, 1, 2, 12, 0)


def _premises(text: str) -> list[str]:
    return [a["text"] for a in atomize.presupposition_safety_net([], [{"claim_id": "X1", "text": text}])]


def _doctor(cls: str, target: str, text: str, hour: int = 14) -> dict:
    return {"aid": f"{target}-{hour}", "text": text, "target": target, "action_type": "administered",
            "observed_at": f"2150-01-02 {hour:02d}:00:00", "spans_decision_point": False, "class": cls,
            "group": rules.group_of(cls)}


def _treat(text: str, target: str, action_class: str, doctor: list[dict]) -> str:
    cls, level = rules.classify_ai(target, text)
    atom = {"atom_id": "a1", "claim_id": "X1", "kind": "action", "text": text, "target": target,
            "action_class": action_class, "conditional": False, "treatment_class": cls, "class_level": level}
    return concord.check_treatment(atom, doctor, [], "", "X", 24.0)["label"]


def _record(text: str, semantics: str, label: str = "", table: str | None = None, hours_before: int = 2) -> dict:
    when = (T - dt.timedelta(hours=hours_before)).strftime("%Y-%m-%d %H:%M:%S")
    return records._row("r", "x", text, when, semantics=semantics, table=table, label=label)


class Premises(unittest.TestCase):
    def test_negated_past_or_resolved_terms_are_not_premises(self):
        for text in ["No hypokalemia.", "History of hypokalemia.", "Hypokalemia has resolved.",
                     "Monitor potassium; no hypokalemia now.", "Monitor for signs of infection, including fever.",
                     "Evaluate and manage hyperkalemia if present.", "Address any desaturation events.",
                     "Consider antihypertensive therapy if necessary."]:
            self.assertEqual(_premises(text), [], text)

    def test_a_history_statement_from_the_atomizer_is_kept(self):
        atom = {"atom_id": "X1::01", "claim_id": "X1", "kind": "fact", "fact_kind": "presupposition",
                "text": "The patient has a history of hypertension.", "concept": "blood_pressure", "direction": "high"}
        claims = [{"claim_id": "X1", "text": "Monitor vital signs, given the history of hypertension."}]
        self.assertEqual(atomize.drop_unasserted_premises([atom], claims), [atom])

    def test_asserted_terms_are_premises(self):
        for text, premise in [("Administer IV potassium chloride to correct hypokalemia.", "Hypokalemia is present."),
                              ("Assess for potential causes of hypokalemia.", "Hypokalemia is present."),
                              ("Monitor oxygen saturation closely given hypoxemia.", "Hypoxemia is present.")]:
            self.assertEqual(_premises(text), [premise], text)


class Classification(unittest.TestCase):
    def test_a_named_class_within_a_group_is_kept(self):
        cases = {("red blood cell transfusion", "Consider red blood cell transfusion."): "transfusion_rbc",
                 ("non-invasive ventilation", "Start non-invasive ventilation."): "ventilation_noninvasive",
                 ("Heparin Sodium", "Administer Heparin Sodium (Prophylaxis)."): "dvt_prophylaxis",
                 ("blood product transfusion", "Consider blood product transfusion."): "transfusion",
                 ("anticoagulation", "Continue anticoagulation."): "anticoagulation",
                 ("ventilator weaning", "Begin ventilator weaning."): "ventilation"}
        for (target, text), expected in cases.items():
            self.assertEqual(rules.classify_ai(target, text)[0], expected, target)
        self.assertEqual(rules.classify_target("Non-invasive Ventilation"), "ventilation_noninvasive")

    def test_named_class_must_match(self):
        platelets = [_doctor("transfusion_other", "Platelets", "Platelets infusion started at")]
        self.assertNotEqual(_treat("Transfuse red blood cells.", "red blood cell transfusion", "administer", platelets),
                            "match")
        invasive = [_doctor("ventilation_invasive", "Invasive Ventilation", "Invasive Ventilation performed")]
        self.assertNotEqual(_treat("Start non-invasive ventilation.", "non-invasive ventilation", "start", invasive),
                            "match")

    def test_named_drug_matches_across_classes(self):
        prophylaxis = [_doctor("dvt_prophylaxis", "Heparin", "Ordered: Heparin 5000 UNIT SC")]
        self.assertEqual(_treat("Administer heparin.", "heparin", "administer", prophylaxis), "match")


class Direction(unittest.TestCase):
    def test_increase_needs_a_rate_increase(self):
        down = [_doctor("vasopressor", "Norepinephrine", "Norepinephrine infusion at 0.2 mcg/kg/min", 13),
                _doctor("vasopressor", "Norepinephrine", "Norepinephrine infusion at 0.1 mcg/kg/min", 15)]
        up = [_doctor("vasopressor", "Norepinephrine", "Norepinephrine infusion at 0.1 mcg/kg/min", 13),
              _doctor("vasopressor", "Norepinephrine", "Norepinephrine infusion at 0.2 mcg/kg/min", 15)]
        self.assertEqual(_treat("Increase norepinephrine.", "norepinephrine", "adjust", down), "partial_match")
        self.assertEqual(_treat("Increase norepinephrine.", "norepinephrine", "adjust", up), "match")

    def test_stopping_a_continued_drug_disagrees_and_does_not_cover_it(self):
        given = [_doctor("antimicrobial", "Vancomycin", "Given: Vancomycin")]
        self.assertEqual(_treat("Discontinue vancomycin.", "vancomycin", "stop", given), "partial_match")
        atom = {"atom_id": "a1", "claim_id": "X1", "kind": "action", "action_class": "stop",
                "treatment_class": "antimicrobial", "class_level": "class"}
        gold = [{"class": "antimicrobial", "importance": "vital"}]
        self.assertFalse(concord.coverage(gold, [atom], {"a1": {"evidence": []}})[0]["covered"])
        self.assertEqual(atomize.normalize([{"claim_id": "X1", "kind": "action", "fact_kind": "none",
                                              "text": "Discontinue vancomycin.", "concept": "other", "direction": "none",
                                              "time": "none", "specimen": "none", "action_class": "adjust",
                                              "target": "vancomycin", "conditional": False}],
                                            [{"claim_id": "X1", "text": "Discontinue vancomycin."}])[0]["action_class"],
                         "stop")


class Administration(unittest.TestCase):
    def test_not_given_is_not_a_dose(self):
        for event in ["Not Given", "Not Started", "Not Given per Sliding Scale", "Not Applied", "Flushed", "Hold Dose"]:
            self.assertFalse(records.mar_given(event), event)
        for event in ["Administered", "Started", "Restarted", "Delayed Administered", "Administered Bolus from IV Drip"]:
            self.assertTrue(records.mar_given(event), event)

    def test_receiving_needs_a_dose_of_that_treatment(self):
        statement = "The patient is currently receiving heparin."
        orders_and_other_drug = [_record("Order: Heparin Flush 5000 UNIT (active at decision time)", "order", "Heparin Flush"),
                                 _record("Running at decision time: Infusion/input Vasopressin", "administration", "Vasopressin")]
        delivered = ground._delivered(statement, orders_and_other_drug, T)
        self.assertFalse(delivered)
        self.assertIsNotNone(ground._administration_guard(statement, "supported", orders_and_other_drug, delivered))
        dose = orders_and_other_drug + [_record("MAR Administered: Heparin", "administration", "Heparin")]
        self.assertTrue(ground._delivered(statement, dose, T))
        self.assertFalse(ground._delivered(statement, [_record("MAR Not Given: Heparin", "mar_other", "Heparin")], T))
        self.assertFalse(ground._delivered("The patient is currently receiving methadone.",
                                           [_record("Methadone, Urine: NEG", "measurement", "Methadone, Urine", "lab")], T))
        self.assertTrue(ground._delivered("The patient is currently on non-invasive ventilation (BiPAP/CPAP).",
                                          [_record("BiPap IPAP: 12 cmH2O", "measurement", "BiPap IPAP", "chart")], T))


class DecisionTime(unittest.TestCase):
    def test_only_what_was_known_at_the_decision_is_used(self):
        """Uses the bundled MIMIC demo. A finished infusion entered after T is unknown at T. One still
        running at T is kept (MIMIC writes the row when it ends), but without its end time."""
        mimic = ROOT / "data" / "mimic-iv-demo"
        triples = json.loads((ROOT / "input" / "mimic_triples_fixed.json").read_text(encoding="utf-8"))["triples"]
        stays = {str(t["stay_id"]): t for t in triples if t["evaluation_eligibility"]["decision_within_icu_stay"]}
        finished_late, running = {}, {}
        with gzip.open(mimic / "icu" / "inputevents.csv.gz", "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                t = stays.get(row["stay_id"])
                if not t:
                    continue
                start, end, stored, decision = (records.ts(row["starttime"]), records.ts(row["endtime"]),
                                                records.ts(row["storetime"]), records.ts(t["decision_point"]))
                rid = f"inputevents:{row['orderid']}:{row['itemid']}:{row['starttime']}"
                if start < decision and end <= decision and stored >= decision:
                    finished_late.setdefault(t["triple_id"], set()).add(rid)
                elif start < decision < end:
                    running.setdefault(t["triple_id"], {})[rid] = row["endtime"]
        cases = sorted(set(finished_late) & set(running))[:2]
        self.assertTrue(cases)
        rows = records.load_admission_rows(mimic, [t for t in stays.values() if t["triple_id"] in cases])
        for case in cases:
            known = {r["rid"]: r for r in rows[case]}
            self.assertFalse(set(known) & finished_late[case], case)
            for rid, end in running[case].items():
                if rid in known:
                    self.assertTrue(known[rid]["ongoing_at_decision"])
                    self.assertNotIn(end, known[rid]["text"])


if __name__ == "__main__":
    unittest.main()
