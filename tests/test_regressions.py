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


class CheapJudgeFixes(unittest.TestCase):
    """Defects found by comparing the cloud models with the reference run (2026-11-06)."""

    def test_replete_as_a_verb_is_not_nutrition(self):
        self.assertEqual(rules.classify_target("Replete magnesium"), "magnesium_replacement")
        self.assertEqual(rules.classify_target("Replete potassium"), "potassium_replacement")
        self.assertEqual(rules.classify_target("Replete with Fiber (Full)"), "nutrition")

    def test_potassium_phosphate_also_delivers_potassium(self):
        row = _record("Infusion/input: K Phos", "administration", "K Phos")
        self.assertTrue(ground._delivered("The patient is receiving potassium replacement.", [row], T))

    def test_oxygen_device_charting_shows_delivery(self):
        row = _record("O2 Delivery Device(s): Nasal cannula", "observation", "O2 Delivery Device(s)", "chart")
        none = _record("O2 Delivery Device(s): None", "observation", "O2 Delivery Device(s)", "chart")
        statement = "The patient is currently receiving supplemental oxygen."
        self.assertTrue(ground._delivered(statement, [row], T))
        self.assertFalse(ground._delivered(statement, [none], T))

    def test_device_charting_can_show_treatment_was_off(self):
        none = {**_record("O2 Delivery Device(s): None", "observation", "O2 Delivery Device(s)", "chart"),
                "itemid": "226732", "value_text": "None"}
        cannula = {**_record("O2 Delivery Device(s): Nasal cannula", "observation", "O2 Delivery Device(s)", "chart"),
                   "itemid": "226732", "value_text": "Nasal cannula"}
        ended = _record("Procedure Non-invasive Ventilation (2150-01-01 10:00:00 to 2150-01-01 18:00:00)", "administration")
        oxygen, niv = "The patient is currently on supplemental oxygen.", "The patient is currently on noninvasive ventilation."
        self.assertIsNone(ground._administration_guard(oxygen, ground.NOT_SUPPORTED, [none], True))
        self.assertIsNotNone(ground._administration_guard(oxygen, ground.NOT_SUPPORTED, [cannula], True))
        self.assertIsNone(ground._administration_guard(niv, ground.NOT_SUPPORTED, [cannula], False))
        self.assertIsNone(ground._administration_guard(niv, ground.NOT_SUPPORTED, [ended], False))
        insulin = "Insulin infusion is currently being given."
        self.assertIsNotNone(ground._administration_guard(insulin, ground.NOT_SUPPORTED, [none], True))

    def test_oxygen_context_is_not_the_stated_value(self):
        self.assertEqual([v[:2] for v in ground._stated_values("Recent SpO2 is 91% on 2 L/min.")], [(91.0, 91.0)])
        self.assertEqual([v[:2] for v in ground._stated_values("The most recent pO2 is 194 mm Hg on FiO2 40%.")], [(194.0, 194.0)])
        self.assertEqual([v[:2] for v in ground._stated_values("Potassium is 3.4 mEq/L.")], [(3.4, 3.4)])

    def _vent(self, *device_hours):
        peep = {**_record("PEEP set: 5 cmH2O", "observation", "PEEP set", "chart", 6), "itemid": "220339", "value_text": "5"}
        rows = [peep]
        for device, hours in device_hours:
            rows.append({**_record(f"O2 Delivery Device(s): {device}", "observation", "O2 Delivery Device(s)", "chart", hours),
                         "itemid": "226732", "value_text": device})
        return ground._ventilation_status(rows, T)["label"]

    def test_later_oxygen_device_ends_ventilation(self):
        self.assertEqual(self._vent(("Nasal cannula", 3)), ground.NOT_SUPPORTED)
        self.assertEqual(self._vent(("Nasal cannula", 5), ("Endotracheal tube", 3)), ground.SUPPORTED)

    def test_vent_setting_request_includes_the_latest_device(self):
        peep = {**_record("PEEP set: 5 cmH2O", "observation", "PEEP set", "chart", 6), "itemid": "220339", "value_text": "5", "rid": "a"}
        device = {**_record("O2 Delivery Device(s): Nasal cannula", "observation", "O2 Delivery Device(s)", "chart", 3),
                  "itemid": "226732", "value_text": "Nasal cannula", "rid": "b"}

        class Top1:
            def search(self, query, sparse, pool):
                return [peep]
        atom = {"atom_id": "X::1", "text": "PEEP is 5 cmH2O.", "claim_text": "PEEP is 5 cmH2O."}
        triple = {"decision_point": "2150-01-02 12:00:00", "triple_id": "X"}
        request = ground._judge_request(atom, [peep, device], triple, "", Top1())
        self.assertEqual({r["rid"] for r in request["alias"].values()}, {"a", "b"})


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
        # The opposite direction disagrees (it is not a partial match).
        self.assertEqual(_treat("Increase norepinephrine.", "norepinephrine", "adjust", down), "not_done")
        self.assertEqual(_treat("Increase norepinephrine.", "norepinephrine", "adjust", up), "match")

    def test_stopping_a_continued_drug_disagrees_and_does_not_cover_it(self):
        given = [_doctor("antimicrobial", "Vancomycin", "Given: Vancomycin")]
        self.assertEqual(_treat("Discontinue vancomycin.", "vancomycin", "stop", given), "not_done")
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


class SettingsAndValues(unittest.TestCase):
    """Fixes of 2026-11-04: monitor settings are not findings; a stated value is checked as a value."""

    def test_a_desaturation_limit_is_not_low_oxygen(self):
        for text in ["Continue supplemental oxygen to maintain SpO2 above the desaturation limit of 88%.",
                     "Set alarms for desaturation.", "Set SpO2 desaturation limit at 88%."]:
            self.assertEqual(_premises(text), [], text)
        self.assertEqual(atomize.fact_concept("The desaturation limit is set at 88%.", "low")[0], "other")
        self.assertEqual(atomize.fact_concept("The patient has recurrent desaturations to 91%.", "low"), ("oxygenation", "low"))
        self.assertEqual(atomize.fact_concept("MAP is 59-67 mmHg.", "low")[0], "map")

    @staticmethod
    def _k(value, hours_before=2):
        when = (T - dt.timedelta(hours=hours_before)).strftime("%Y-%m-%d %H:%M:%S")
        return {"rid": f"k{value}", "concept": "potassium", "value": value, "table": "lab", "lower": 3.3, "upper": 5.1,
                "observed_at": when, "unit": "mEq/L", "label": "Potassium"}

    def _verify(self, text, rows, direction="low"):
        atom = {"atom_id": "X1::01", "claim_id": "X1", "kind": "fact", "fact_kind": "observed", "text": text,
                "concept": "potassium", "direction": direction, "time": "current", "specimen": "blood"}
        return ground.verify(atom, rows, {"decision_point": T.strftime("%Y-%m-%d %H:%M:%S")}, "", None)["label"]

    def test_a_stated_value_equal_to_the_record_is_supported(self):
        rows = [self._k(3.9, 10), self._k(3.4)]
        self.assertEqual(self._verify("Potassium is 3.4 mEq/L.", rows), "supported")
        self.assertEqual(self._verify("Potassium is 3.4-3.9 mEq/L.", rows), "supported")
        self.assertEqual(self._verify("Potassium is 3.0 mEq/L.", rows), "not_supported")
        self.assertEqual(self._verify("Potassium is 1.2 mmol/L.", [self._k(4.0)]), "unverifiable")  # likely another unit
        # A direction word keeps the direction check: 3.4 is inside the reference range.
        self.assertEqual(self._verify("Potassium is low at 3.4 mEq/L.", rows), "not_supported")
        self.assertEqual(self._verify("Potassium is low-normal.", rows), "supported")
        # A bedside reading counts even when laboratory values exist (fingerstick glucose).
        bedside = {**self._k(5.6), "rid": "bedside", "table": "chart", "lower": None, "upper": None}
        self.assertEqual(self._verify("Fingerstick potassium is 5.6.", rows + [bedside]), "supported")


class CloudReplies(unittest.TestCase):
    """A reply cut off by the output budget gets more room; an empty reply is never sent back (HTTP 400)."""

    def _run(self, replies):
        import copy
        import tempfile
        from cm.llm import LLM
        with tempfile.TemporaryDirectory() as tmp:
            llm = LLM(Path(tmp) / "cache.jsonl")
            sent = []

            def post(path, payload, timeout=900, cloud=False):
                sent.append(copy.deepcopy(payload))
                return replies[len(sent) - 1]

            llm._post = post
            schema = {"type": "object", "required": ["ok"], "properties": {"ok": {"type": "boolean"}}}
            return llm.json("m:cloud", "s", "u", schema, num_predict=500), sent

    def test_a_truncated_reply_is_retried_with_a_larger_budget(self):
        out, sent = self._run([{"message": {"content": ""}, "done_reason": "length"},
                               {"message": {"content": '{"ok": true}'}, "done_reason": "stop"}])
        self.assertEqual(out, {"ok": True})
        self.assertEqual([p["options"]["num_predict"] for p in sent], [500, 2000])
        self.assertEqual(len(sent[1]["messages"]), 2)

    def test_an_empty_reply_is_not_sent_back(self):
        out, sent = self._run([{"message": {"content": ""}, "done_reason": "stop"},
                               {"message": {"content": '{"ok": true}'}, "done_reason": "stop"}])
        self.assertEqual(out, {"ok": True})
        self.assertEqual([m["role"] for m in sent[1]["messages"]], ["system", "user", "user"])


class Omissions(unittest.TestCase):
    def test_a_finding_counts_as_mentioned_by_the_same_or_a_narrow_concept(self):
        self.assertTrue(rules.same_finding("potassium", "potassium"))
        self.assertTrue(rules.same_finding("spo2", "oxygenation"))
        self.assertTrue(rules.same_finding("metabolic_acidosis", "bicarbonate"))
        self.assertFalse(rules.same_finding("electrolytes", "potassium"))
        self.assertFalse(rules.same_finding("other", "wbc"))

    def test_a_treated_finding_no_fact_mentions_is_omitted(self):
        gold = [{"name": "antimicrobials", "indications": [{"concept": "wbc", "direction": "high", "reason": "WBC 17.8"}]},
                {"name": "cultures", "indications": [{"concept": "wbc", "direction": "high", "reason": "WBC 17.8"}]},
                {"name": "potassium replacement", "indications": [{"concept": "potassium", "direction": "low", "reason": "K 3.0"}]}]
        facts = [{"atom_id": "X1::02", "concept": "potassium"}]
        out = {r["concept"]: r for r in concord.fact_omissions(gold, facts)}
        self.assertEqual(len(out), 2)
        self.assertFalse(out["wbc"]["mentioned"])
        self.assertEqual(out["wbc"]["treated_by"], ["antimicrobials", "cultures"])
        self.assertEqual(out["potassium"]["by_atoms"], ["X1::02"])


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
