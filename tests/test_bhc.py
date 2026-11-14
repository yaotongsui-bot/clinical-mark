"""VeriFact-BHC track: release reader, note facts, VeriFact-format context, run and score on a small
synthetic release, and the metric formulas against irrCAC / scikit-learn (skipped if not installed).

No model is called: LLM.json is replaced by a stub. Run:  python -m unittest tests.test_bhc
"""

from __future__ import annotations

import datetime as dt
import gzip
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import run_bhc  # noqa: E402
import score_bhc  # noqa: E402
from cm import notes, verifact_bhc as vb  # noqa: E402
from cm.llm import LLM  # noqa: E402

NOTE = ("Pt is a 67yo M w/ [**Known lastname 123**] CHF.\n\nStarted on heparin drip. No evidence of pneumonia "
        "on CXR.\n- Lasix 40 mg IV given\n- plan: consider CT")


def _gz_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as h:
        df.to_csv(h, index=False)


def make_release(root: Path) -> None:
    props = pd.DataFrame({
        "proposition_id": [f"p{i}" for i in range(8)],
        "text": ["Patient has CHF.", "Heparin was started.", "Patient had pneumonia.", "Patient went to Mars.",
                 "Lasix was given.", "CT was done.", "Patient is 67.", "Patient is female."],
        "subject_id": ["1"] * 4 + ["2"] * 4,
        "author_type": ["llm", "llm", "human", "human"] * 2,
        "proposition_type": ["claim", "sentence"] * 4})
    _gz_csv(root / "propositions/propositions.csv.gz", props)
    gt = ["Supported", "Supported", "Not Supported", "Not Addressed", "Supported", "Not Supported", "Supported",
          "Not Supported"]
    _gz_csv(root / "propositions/human_verdicts.csv.gz", props.assign(human_gt=gt).drop(columns="subject_id"))
    (root / "verifact").mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"model": ["Llama-70B"] * 3, "rater_alias": ["a1", "a2", "a3"],
                  "rater_name": ["model=Llama-70B,x", "model=Llama-70B,y", "model=Llama-70B,z"],
                  "fact_type": ["claim", "sentence", "claim"], "retrieval_method": ["rerank", "rerank", "dense"],
                  "top_n": ["50", "50", "50"], "reference_format": ["absolute time"] * 3,
                  "reference_only_admission": ["False"] * 3, "deduplicate_text": ["True"] * 3}
                 ).to_csv(root / "verifact/rater_configurations.csv", index=False)
    rows = []
    for _, r in props.iterrows():
        alias = "a1" if r.proposition_type == "claim" else "a2"
        rows.append({"model": "Llama-70B", "proposition_id": r.proposition_id, "rater_alias": alias,
                     "reference_id": f"ref-{r.proposition_id}", "verdict": "Supported"})
        rows.append({"model": "Llama-70B", "proposition_id": r.proposition_id, "rater_alias": "a3",
                     "reference_id": f"ref3-{r.proposition_id}", "verdict": "Not Addressed"})
    pd.DataFrame(rows).to_parquet(root / "verifact/verdicts.parquet", index=False)
    pd.DataFrame({"reference_id": [r["reference_id"] for r in rows], "reference": ["ctx " + NOTE] * len(rows)}
                 ).to_parquet(root / "verifact/reference_payloads.parquet", index=False)
    _gz_csv(root / "reference_ehr/ehr_noteevents.csv.gz", pd.DataFrame({
        "ROW_ID": ["10", "11", "12", "13"], "SUBJECT_ID": ["1", "1", "2", "1"], "HADM_ID": ["100", "100", "200", "90"],
        "CHARTDATE": ["2150-01-01", "2150-01-05", "2150-02-01", "2140-03-03"],
        "CHARTTIME": ["2150-01-01 08:00:00", "", "2150-02-01 09:00:00", ""],
        "STORETIME": ["", "", "", ""],
        "CATEGORY": ["Physician ", "Discharge summary", "Nursing", "Radiology"],
        "DESCRIPTION": ["Progress", "Report", "Note", "CHEST (PA & LAT)"],
        "CGID": ["", "", "", ""], "ISERROR": ["", "", "", ""],
        "TEXT": [NOTE, "BRIEF HOSPITAL COURSE: secret", NOTE, "Old film shows cardiomegaly."]}))
    _gz_csv(root / "reference_ehr/admissions.csv.gz", pd.DataFrame({
        "SUBJECT_ID": ["1", "2"], "HADM_ID": ["100", "200"],
        "ADMITTIME": ["2149-12-31 22:00:00", "2150-01-30 10:00:00"],
        "DISCHTIME": ["2150-01-05 12:00:00", "2150-02-03 15:00:00"]}))


def _packet(user: str) -> dict:
    """The input JSON of either judge style."""
    if user.startswith("{"):
        return json.loads(user)
    return json.loads(user.rsplit("Input JSON:\n", 1)[1].rsplit("\nOutput JSON:", 1)[0])


CALLS = []


def stub_json(self, model, system, user, schema, **kw):
    """Supported if the proposition's last word is in the reference, otherwise not addressed."""
    CALLS.append({"model": model, "system": system, "user": user, "schema": schema, **kw})
    packet = _packet(user)
    ref = json.dumps(packet["reference"]).lower()
    word = packet["text"].rstrip(".").split()[-1].lower()
    hit = word in ref
    self.calls += 1
    if "verdict" in schema["properties"]:
        if word == "female":  # first sample invalid: exercises the retry with a new seed
            return {"verdict": "Maybe" if kw["sampling"]["seed"] == 20261011 else "not supported", "reason": "r"}
        return {"verdict": "supported" if hit else "not addressed", "reason": "stub"}
    evidence = [packet["reference"][0]["id"]] if isinstance(packet["reference"], list) and packet["reference"] else []
    return {"label": "supported" if hit else "not_addressed", "evidence": evidence, "reason": "stub"}


class ReaderTests(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(vb.norm_label("Not Supported"), "not_supported")
        self.assertEqual(vb.norm_label(" not_addressed "), "not_addressed")
        self.assertEqual(vb.norm_label("SUPPORTED"), "supported")
        self.assertIsNone(vb.norm_label("maybe"))

    def test_hosted_models_refused(self):
        with self.assertRaises(SystemExit):
            vb.check_local_models(["qwen2.5:14b", "glm-5.3:cloud"])
        vb.check_local_models(["qwen2.5:14b"])

    def test_verifact_title_case_check(self):
        self.assertEqual(run_bhc.parse_verifact({"verdict": "not supported", "reason": "x"})["label"], "not_supported")
        with self.assertRaises(ValueError):
            run_bhc.parse_verifact({"verdict": "Partially Supported"})

    def test_note_facts(self):
        facts = notes.split_facts(NOTE)
        self.assertIn("Pt is a 67yo M w/ Known lastname 123 CHF.", facts)
        self.assertIn("Lasix 40 mg IV given", facts)
        self.assertIn("No evidence of pneumonia on CXR.", facts)
        long = notes.split_facts(" ".join(["word"] * 130))
        self.assertEqual([len(f.split()) for f in long], [60, 60, 10])

    def test_context_format_matches_verifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_release(Path(tmp))
            by_subject = notes.read_notes(Path(tmp) / "reference_ehr" / "ehr_noteevents.csv.gz")
            adm = notes.read_admissions(Path(tmp) / "reference_ehr" / "admissions.csv.gz")
        rows = notes.reference_rows(by_subject["1"])
        self.assertFalse(any("secret" in r["text"] for r in rows))        # discharge summary left out
        self.assertEqual(rows[0]["category"], "Radiology")                  # oldest note first
        only = notes.reference_rows(by_subject["1"], admission=adm["1"])
        self.assertNotIn("Radiology", {r["category"] for r in only})      # 2140 note is another admission
        text = notes.absolute_time_context(rows[:2], adm["1"])
        self.assertEqual(text.splitlines()[:5], [
            "Hospital Admission Start: 2149-12-31 22:00:00",
            "Hospital Admission End: 2150-01-05 12:00:00",
            "Electronic Health Record Context",
            "Ordered by Time (Earliest to Latest):",
            "1. Date: 2140-03-03, Time: Unknown, Note Category: Radiology, Note Description: CHEST (PA & LAT) "
            "| Text: Old film shows cardiomegaly."])
        self.assertTrue(text.splitlines()[5].startswith("2. Date: 2150-01-01, Time: 08:00:00, Note Category: Physician"))


class MetricTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.RandomState(3)
        self.t = rng.choice(3, size=200, p=[0.6, 0.25, 0.15])
        self.p = np.where(rng.rand(200) < 0.75, self.t, rng.choice(3, size=200))

    def test_against_reference_libraries(self):
        c = score_bhc.confusion_matrix(self.t, self.p)
        try:
            from sklearn.metrics import matthews_corrcoef
        except ImportError:
            self.skipTest("scikit-learn not installed")
        self.assertAlmostEqual(score_bhc.mcc(c), matthews_corrcoef(self.t, self.p), places=12)
        try:
            from irrCAC.raw import CAC
        except ImportError:
            self.skipTest("irrCAC not installed")
        labels = np.array(vb.LABELS)
        table = pd.DataFrame({"human_gt": labels[self.t], "ai": labels[self.p]})
        self.assertAlmostEqual(score_bhc.gwet_ac1(c), CAC(table).gwet()["est"]["coefficient_value"], places=4)
        b = score_bhc.binarize_cm(c)
        bt = table.map(lambda x: "Supported" if x == "supported" else "Not Supported or Addressed")
        self.assertAlmostEqual(score_bhc.gwet_ac1(b), CAC(bt).gwet()["est"]["coefficient_value"], places=4)
        # A label absent from both raters: irrCAC drops it from the categories.
        two = pd.DataFrame({"h": ["supported", "supported", "not_supported"], "a": ["supported", "not_supported", "not_supported"]})
        c2 = score_bhc.confusion_matrix(two["h"].map(score_bhc.CODE).to_numpy(), two["a"].map(score_bhc.CODE).to_numpy())
        self.assertAlmostEqual(score_bhc.gwet_ac1(c2), CAC(two).gwet()["est"]["coefficient_value"], places=4)

    def test_bootstrap_rows_match_pandas_sample(self):
        df = pd.DataFrame({"x": range(37)})
        for i in (0, 5, 999):
            self.assertTrue((df.sample(frac=1.0, replace=True, random_state=i)["x"].to_numpy() ==
                             np.random.RandomState(i).choice(37, size=37, replace=True)).all())


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "release"
        make_release(self.root)
        CALLS.clear()

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, *extra, models="a:1,b:1,c:1"):
        out = Path(self.tmp.name) / ("run" + re.sub(r"\W", "", "_".join(extra)))
        argv = ["run_bhc.py", "--release-dir", str(self.root), "--out-dir", str(out), "--judge-models", models, *extra]
        with mock.patch.object(LLM, "json", stub_json), mock.patch.object(LLM, "unload", lambda s, m: None), \
                mock.patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()):
            run_bhc.main()
        return out, pd.read_csv(out / "verdicts.csv", dtype=str, keep_default_na=False)

    def test_verifact_judge_on_released_context(self):
        out, df = self._run(models="llama3.1:8b")
        self.assertEqual(len(df), 8)
        # Claim propositions use rater a1 (fact_type claim), sentences a2; dense rater a3 is not selected.
        self.assertEqual(set(df.loc[df["proposition_type"] == "claim", "rater_alias"]), {"a1"})
        self.assertEqual(set(df.loc[df["proposition_type"] == "sentence", "rater_alias"]), {"a2"})
        got = df.set_index("proposition_id")
        self.assertEqual(got.loc["p0", "verdict"], "Supported")
        self.assertEqual(got.loc["p3", "verdict"], "Not Addressed")
        self.assertEqual(got.loc["p7", "verdict"], "Not Supported")  # second sample after an invalid one
        call = next(c for c in CALLS if '"Patient has CHF."' in c["user"])
        self.assertEqual(call["system"], (ROOT / "prompts" / "verifact_system.txt").read_text(encoding="utf-8"))
        self.assertIn('{\n    "text": "Patient has CHF.",\n    "reference": "ctx Pt is', call["user"])
        self.assertTrue(call["user"].endswith("}\nOutput JSON:"))
        self.assertEqual((call["sampling"]["temperature"], call["sampling"]["top_p"]), (0.1, 1.0))
        report = Path(self.tmp.name) / "score.md"
        with mock.patch.object(sys, "argv", ["score_bhc.py", str(out), "--release-dir", str(self.root),
                                             "--out", str(report)]), redirect_stdout(io.StringIO()):
            score_bhc.main()
        text = report.read_text(encoding="utf-8")
        self.assertIn("### VeriFact released Llama-70B", text)
        self.assertIn("| llm_claim | 2 |", text)
        self.assertIn("### Difference", text)

    def test_our_retrieval_with_verifact_context(self):
        _, df = self._run("--context", "ours", "--retrieval", "bm25", "--top-n", "5", models="llama3.1:8b")
        got = df.set_index("proposition_id")
        self.assertEqual(got.loc["p0", "label"], "supported")
        self.assertEqual((got.loc["p3", "n_reference"], got.loc["p3", "agreement"]), ("0", "rule"))
        call = next(c for c in CALLS if '"Patient has CHF."' in c["user"])
        self.assertIn('"reference": "Hospital Admission Start: 2149-12-31 22:00:00\\n', call["user"])

    def test_our_judge_panel(self):
        _, df = self._run("--judge-style", "ours", "--context", "ours", "--retrieval", "bm25")
        self.assertEqual(df.set_index("proposition_id").loc["p0", "agreement"], "3/3")
        call = CALLS[0]
        self.assertEqual(call["system"], (ROOT / "prompts" / "bhc_judge.txt").read_text(encoding="utf-8"))
        self.assertIsInstance(json.loads(call["user"])["reference"], list)

    def test_sample_is_stratified(self):
        _, df = self._run("--sample", "4", models="llama3.1:8b")
        self.assertEqual(len(df), 4)
        self.assertEqual(df.groupby(["author_type", "proposition_type"]).size().tolist(), [1, 1, 1, 1])


if __name__ == "__main__":
    unittest.main()
