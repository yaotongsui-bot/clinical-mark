"""eICU adapter: time window, item mapping, devices, infusion intervals, medication orders.

Builds a tiny synthetic eICU demo folder; no model calls. Run:  python -m unittest tests.test_records_eicu
"""

from __future__ import annotations

import datetime as dt
import gzip
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cm import ground, records_eicu as eicu  # noqa: E402

STAY = 1001


def write(root: Path, name: str, rows: list[dict]) -> None:
    with gzip.open(root / f"{name}.csv.gz", "wt", encoding="utf-8", newline="") as h:
        pd.DataFrame(rows).to_csv(h, index=False)


def make(root: Path) -> None:
    write(root, "patient", [{"patientunitstayid": STAY, "uniquepid": "p1", "hospitalid": 7, "unittype": "MICU",
                             "gender": "Male", "age": "70", "apacheadmissiondx": "Sepsis", "unitadmittime24": "08:00:00",
                             "unitvisitnumber": 1, "unitstaytype": "admit", "unitdischargeoffset": 3000}])
    write(root, "lab", [
        {"labid": 1, "patientunitstayid": STAY, "labresultoffset": 300, "labname": "potassium", "labresult": 3.1,
         "labresulttext": "3.1", "labmeasurenameinterface": "mmol/L", "labresultrevisedoffset": 330},
        {"labid": 2, "patientunitstayid": STAY, "labresultoffset": 1430, "labname": "potassium", "labresult": 4.0,
         "labresulttext": "4.0", "labmeasurenameinterface": "mmol/L", "labresultrevisedoffset": 1450},  # known after T
        {"labid": 3, "patientunitstayid": STAY, "labresultoffset": 400, "labname": "ionized calcium", "labresult": 1.05,
         "labresulttext": "1.05", "labmeasurenameinterface": "mmol/L", "labresultrevisedoffset": 420}])
    write(root, "nurseCharting", [
        {"nursingchartid": 10, "patientunitstayid": STAY, "nursingchartoffset": 600, "nursingchartentryoffset": 600,
         "nursingchartcelltypevallabel": "O2 Admin Device", "nursingchartcelltypevalname": "O2 Admin Device",
         "nursingchartvalue": "vent"},
        {"nursingchartid": 11, "patientunitstayid": STAY, "nursingchartoffset": 1300, "nursingchartentryoffset": 1300,
         "nursingchartcelltypevallabel": "O2 Admin Device", "nursingchartcelltypevalname": "O2 Admin Device",
         "nursingchartvalue": "NC"},
        {"nursingchartid": 12, "patientunitstayid": STAY, "nursingchartoffset": 1380, "nursingchartentryoffset": 1380,
         "nursingchartcelltypevallabel": "Heart Rate", "nursingchartcelltypevalname": "Heart Rate",
         "nursingchartvalue": "112"},
        {"nursingchartid": 13, "patientunitstayid": STAY, "nursingchartoffset": 1500, "nursingchartentryoffset": 1500,
         "nursingchartcelltypevallabel": "Heart Rate", "nursingchartcelltypevalname": "Heart Rate",
         "nursingchartvalue": "90"}])
    write(root, "respiratoryCharting", [
        {"respchartid": 20, "patientunitstayid": STAY, "respchartoffset": 590, "respchartentryoffset": 590,
         "respcharttypecat": "respFlowSettings", "respchartvaluelabel": "PEEP", "respchartvalue": "5"}])
    write(root, "respiratoryCare", [{"respcareid": 30, "patientunitstayid": STAY, "respcarestatusoffset": 100,
                                     "airwaytype": "Oral ETT", "airwaysize": 7.5, "airwayposition": 22}])
    write(root, "infusiondrug", [
        {"infusiondrugid": i, "patientunitstayid": STAY, "infusionoffset": off, "drugname": name, "drugrate": rate}
        for i, (off, name, rate) in enumerate([
            (700, "Norepinephrine (mcg/min)", "5"), (760, "Norepinephrine (mcg/min)", "5"),
            (820, "Norepinephrine (mcg/min)", "10"), (1400, "Norepinephrine (mcg/min)", "10"),
            (500, "Propofol (mcg/kg/min)", "20"), (900, "Propofol (mcg/kg/min)", "0")], 40)])
    write(root, "medication", [
        {"medicationid": 50, "patientunitstayid": STAY, "drugorderoffset": 100, "drugstartoffset": 120,
         "drugivadmixture": "No", "drugordercancelled": "No", "drugname": "VANCOMYCIN 1 G", "dosage": "1 2",
         "routeadmin": "IV", "frequency": "Q12H", "prn": "No", "drugstopoffset": 4000},
        {"medicationid": 51, "patientunitstayid": STAY, "drugorderoffset": 100, "drugstartoffset": 120,
         "drugivadmixture": "No", "drugordercancelled": "No", "drugname": "ONDANSETRON", "dosage": "4 1",
         "routeadmin": "IV", "frequency": "Q6H PRN", "prn": "Yes", "drugstopoffset": 4000}])
    write(root, "treatment", [{"treatmentid": 60, "patientunitstayid": STAY, "treatmentoffset": 200,
                               "treatmentstring": "pulmonary|ventilation and oxygenation|mechanical ventilation",
                               "activeupondischarge": False}])
    write(root, "microLab", [{"microlabid": 70, "patientunitstayid": STAY, "culturetakenoffset": 200,
                              "culturesite": "Blood", "organism": "no growth", "antibiotic": None,
                              "sensitivitylevel": None}])


class EicuAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        make(cls.root)
        cls.rows = eicu.load_admission_rows(cls.root, [{"triple_id": f"E{STAY}", "stay_id": STAY}])[f"E{STAY}"]
        cls.text = [r["text"] for r in cls.rows]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_only_rows_known_before_T(self):
        self.assertIn("Potassium: 3.1 mmol/L", self.text)
        self.assertNotIn("Potassium: 4 mmol/L", self.text)  # resulted after T
        self.assertFalse(any("Heart Rate: 90" in t for t in self.text))  # charted after T

    def test_case_header_rows(self):
        header = {r["label"]: r for r in self.rows if r["source_type"] == "admission"}
        self.assertEqual(header["Admission diagnosis"]["text"], "Admission diagnosis (APACHE): Sepsis")
        self.assertEqual(header["ICU unit"]["text"], "ICU unit: MICU")
        self.assertEqual(header["Patient"]["text"], "Patient: Male, age 70")
        self.assertEqual(header["Admission diagnosis"]["observed_at"], "2100-01-01 08:00:00")  # unit admission
        post = eicu.load_post_observations(self.root, [{"triple_id": f"E{STAY}", "stay_id": STAY}])[f"E{STAY}"]
        self.assertFalse(any(o["record_id"].startswith("pat:") for o in post))

    def test_mapping_and_concepts(self):
        k = next(r for r in self.rows if r["text"].startswith("Potassium"))
        self.assertEqual((k["itemid"], k["concept"]), ("50971", "potassium"))
        hr = next(r for r in self.rows if r["text"].startswith("Heart Rate"))
        self.assertEqual(hr["concept"], "heart_rate")
        ica = next(r for r in self.rows if r["text"].startswith("Free Calcium"))
        self.assertEqual((ica["lower"], ica["upper"]), (1.12, 1.32))

    def test_devices_and_ventilation_status(self):
        self.assertEqual(eicu.device_name("trach / vent"), "Tracheostomy tube")
        self.assertEqual(eicu.device_name("RA"), "None")
        self.assertEqual(eicu.device_name("BiPAP 12/8"), "Bipap mask")
        self.assertEqual(eicu.device_name("T-piece"), "T-piece")
        devices = [r["value_text"] for r in self.rows if r["itemid"] == "226732"]
        self.assertEqual(devices, ["Endotracheal tube", "Nasal cannula"])
        status = ground._ventilation_status(self.rows, dt.datetime(2100, 1, 2, 8, 0))
        self.assertEqual(status["label"], "not_supported")  # nasal cannula after the last ventilator row

    def test_infusions(self):
        noradr = [t for t in self.text if "Norepinephrine" in t]
        self.assertEqual(len(noradr), 2)
        self.assertTrue(noradr[0].startswith("Infusion/input Norepinephrine at 5 mcg/min ("))
        self.assertTrue(noradr[1].startswith("Running at decision time (started"))
        self.assertIn("at 10 mcg/min", noradr[1])
        propofol = [t for t in self.text if "Propofol" in t]
        self.assertEqual(len(propofol), 1)
        self.assertRegex(propofol[0], r"^Infusion/input Propofol at 20 mcg/kg/min \(.* to .*\)$")  # stopped by rate 0

    def test_medications(self):
        vanc = next(r for r in self.rows if "VANCOMYCIN" in r["text"])
        self.assertTrue(vanc["ongoing_at_decision"])
        self.assertEqual(vanc["semantics"], "administration")
        ond = next(r for r in self.rows if "ONDANSETRON" in r["text"])
        self.assertEqual(ond["semantics"], "order")
        self.assertEqual(ond["text"].count("PRN"), 1)


if __name__ == "__main__":
    unittest.main()
