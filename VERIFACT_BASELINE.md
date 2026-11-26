# VeriFact-BHC as the baseline: comparison and research plan

Written 2026-11-12. Sources: VeriFact arXiv v1 (2501.16672) and the GitHub repo
(philipchung/verifact). The NEJM AI version and the PhysioNet dataset page were not read (the page
returned 404 / 502), so the dataset file list below comes from the repo README and NEJM AI numbers
may differ slightly.

## 1. What VeriFact and VeriFact-BHC are

- **Task.** Check each proposition of a Brief Hospital Course (BHC), a retrospective discharge
  narrative, against the patient's EHR. Two BHCs per patient: the human-written one from the
  discharge summary and one written by Llama 3.1 70B from the admission's notes.
- **Data.** MIMIC-III v1.4, 100 random patients, free-text notes only (ICU notes, radiology,
  cardiology, discharge summaries). 13,290 propositions: 9,108 atomic claims, 4,182 sentences.
- **Reference EHR.** All notes except the discharge summary, decomposed the same way into facts and
  stored in Qdrant. Retrieval is dense, hybrid (bge-m3 dense + sparse, distribution-based score
  fusion) or hybrid + bge-reranker-v2-m3, with N = 5, 10, 25 or 50, current admission or whole EHR.
  Context is formatted by relevance, absolute time or relative time.
- **Judge.** One model, Llama 3.1 70B Instruct (AWQ INT4), temperature 0.1, JSON output. Labels:
  Supported / Not Supported / Not Addressed.
- **Ground truth.** 25 clinicians, 3 labels per proposition, majority vote; 478 three-way splits went
  to 2 more clinicians and then to consensus. 1,618 annotation hours.
- **Results.** Inter-clinician agreement up to 88.5% (LLM-written, atomic; AC1 0.88). VeriFact vs
  ground truth: 92.7% (LLM-written, sentence) and 88.8% (LLM-written, atomic). On human-written
  text, Supported-vs-rest agreement is 79.2% / 78.5%. Best setting: hybrid + rerank, N = 50, whole
  EHR, absolute time or relevance format. The number of facts mattered most, then the retrieval method,
  and performance had not saturated at N = 50.
- **Stated limitations.** No omission detection. The EHR is treated as complete truth. The judge
  leans to Not Supported over Not Addressed (binarizing negatives raises human-written agreement by
  10-15%). No tuning of prompts or models. Sentence propositions can hold several claims.
- **Release.** "MIMIC-III-Ext-VeriFact-BHC" v1.1.0 on PhysioNet, credentialed access under the
  MIMIC data use agreement. Per the repo README it holds the BHCs, the propositions, the clinician
  annotations, VeriFact verdicts and the reference EHRs, and a replay script
  (`scripts/evaluate/replay_physionet_v1_1_0.py`) uses the released propositions and contexts. The code is MIT.

## 2. How clinical_mark differs

| Aspect | VeriFact / VeriFact-BHC | clinical_mark |
|---|---|---|
| Text evaluated | Retrospective BHC narrative | Prospective ICU recommendation at T = ICU admission + 24 h |
| Data | MIMIC-III, free-text notes only | MIMIC-IV demo, structured tables only (labs, chart, prescriptions, eMAR, inputs, procedures) |
| Reference scope | Whole EHR in the best setting, no time cut | Current admission before T; event time and entry time must both precede T |
| Decomposition | Sentences or atomic claims, same pipeline for text and EHR | Fact / action / goal atoms; presuppositions inside actions become facts |
| Retrieval | bge-m3 dense + sparse, fusion, bge reranker, N = 50 | bge-m3 dense + BM25 (stand-in for M3 sparse), fusion, no reranker, N = 50, chronological |
| Judge | One LLM | Code rules for labs, vital signs and ventilation; majority of three models from different families for the rest |
| Labels | Supported / Not Supported / Not Addressed | The same three plus `unverifiable`; a missing record is never `not_supported` |
| Beyond fact checking | None | Action concordance with clinician actions in (T, T + 24 h], omission (vital recall), known-answer tests, test-retest |
| Ground truth | 25 clinicians, adjudicated | None yet. The current reference is Claude's own labels; `annotation_set/` awaits three clinicians |

Two VeriFact limitations are what this project addresses: omissions (stage 4) and the Not Supported /
Not Addressed confusion (the missing-record rule, code checks, `unverifiable`). This project's main
gap is VeriFact's strength: there is no clinician ground truth. The figures in
`reference/FINAL_SUMMARY.md` (91.7%, kappa 0.80 on 20 blind cases) are measured against Claude's
reference and cannot be compared with VeriFact's 92.7%.

## 3. Plan

**Decision (2026-11-12): Route A is the main experiment.** No new clinician labels will be collected,
so VeriFact-BHC's adjudicated labels are the only clinician ground truth available. Route B can no
longer be scored against clinicians; it stays as the application demonstration, checked by
known-answer tests and Claude's reference only.

### Route A (main): this evaluator's fact module on VeriFact-BHC

- Baseline numbers need no rerun: VeriFact's released verdicts, scored on the same ground truth, are
  the baseline (Llama 3.1 70B does not fit the 16 GB local GPU anyway).
- Step 1, judge only: with VeriFact's released propositions and retrieved contexts, replace the single
  judge with this project's judge prompt and the local three-model vote. Same inputs, so the
  difference is the judge alone. Also run each local judge alone, so that the gain from voting is
  separated from the gain from model choice.
- Step 2, label calibration: this project's missing-record rule and `unverifiable` label target
  VeriFact's known Not Supported vs Not Addressed confusion. Report the 3 x 3 confusion matrix
  against ground truth, not only overall agreement.
- Step 3, retrieval: this project's retrieval (no reranker, BM25 for the sparse side) against
  VeriFact's hybrid + rerank, with N = 10 to 100. This needs the reference EHR facts from the
  release and a local index.
- Metrics: percent agreement and Gwet's AC1 with 95% CIs, split by BHC author (human / LLM) and
  proposition type (atomic / sentence), as in the paper.
- What does not transfer: code rules for labs and vital signs (BHC-side records are notes, not
  table rows), action concordance and omissions. The contributions tested here are the judge
  panel, the judge prompt rules and label calibration.
- Needed: credentialed PhysioNet access; local models only (see the data-use constraint below);
  note atomization in `cm/records.py` only for step 3.

### Local-model history (relevant to Route A)

The first evaluator ran fully local: atomizer `qwen2.5:14b`, judge panel `gemma4:12b` (reasoning
mode), `llama3.1:8b-instruct-q4_K_M`, `qwen2.5:14b`, majority vote. Records:

| Folder | Content |
|---|---|
| `results/`, `results_fixed/` | qwen2.5:7b answers, original and repaired input (fact accuracy 60.6% and 76.0%) |
| `results_open_s1..s3/` | Up to 10 suggestions, 3 samples |
| `results_deepseek/`, `results_open_deepseek_s1..s3/` | Frozen deepseek answers, local evaluator (fact accuracy 76.6%) |
| `validation/retest_fixed/`, `validation/stability_results_fixed.md` | Test-retest: 481/481 identical |
| `validation/sensitivity_fixed/sensitivity.md` | 28 panel-judged facts re-judged by each local judge alone, by retrieval and N; agreement with the panel 68%-96% (gemma4 lowest) |
| `validation/controls/`, `validation/known_answer_tests.md` | Known-answer tests: 201/202 injected errors, 610/610 clinician actions |

These runs predate the 2026-11-04 and 2026-11-06 fixes and prompt changes, and the local panel was
never scored against Claude's reference (`reference/` compares cloud models only). The sensitivity
analysis compares each judge with the panel, not with a ground truth. Before Route A, rerun the local
panel with the current prompts on the base 85 cases and score it with `reference/compare_to_reference.py`,
to see how far it falls behind the cloud vote.

### Route B status (2026-11-13)

The user chose to run Route B on the 85 cases first, with Claude as the reference. Built:
`cm/baseline.py`, `run_baseline85.py`, `score_baseline85.py` (README section "VeriFact baseline on
the 85 cases"). Main comparison: the same 486 fact atoms (Claude's split standard), VeriFact's
judging vs this evaluator's, with and without the time cut.

The existing Claude reference cannot be the gold standard for this comparison: 199 of its fact labels
are this evaluator's code output and the rest were judged on this evaluator's retrieved records, so
this evaluator scores 97.9% against it by construction. Next step: a new Claude reference for the 486
atoms, judged against the full records before T (not retrieved), blind to both systems, using
VeriFact's label definitions, frozen before scoring.

Done 2026-11-13: the new reference is `reference/fact_gold/` (guideline, sheets, labels, frozen CSV);
first results in `results_baseline85/RESULTS.md`. End-to-end comparison with VeriFact's own
decomposition deferred by the user.

### Route B (secondary): VeriFact as a method baseline on this task

Run a faithful VeriFact configuration on the 85 cases' fact atoms and compare it with this
evaluator. Without clinician labels, both are scored against Claude's reference and the
known-answer tests, so this route shows behaviour, not accuracy.

- Baseline: atomic claims, one LLM judge, hybrid + rerank, N = 50, absolute time, no time cut
  (VeriFact's best setting), VeriFact's prompt and three labels.
- Ablations, adding one change at a time: time cut at T; code rules for measurable facts;
  three-model vote; `unverifiable` label and missing-record rule; presupposition extraction.
- Metrics as in `score_annotations.py`: percent agreement, Gwet's AC1, per-label sensitivity / PPV,
  bootstrap CIs over cases. Report the Not Supported vs Not Addressed confusion separately, since it
  is VeriFact's known bias.
- Needed: the reranker (not in Ollama; run bge-reranker-v2-m3 locally, e.g. via sentence-transformers).

### Data-use constraint

VeriFact-BHC is MIMIC-III credentialed data. The PhysioNet data use agreement does not allow sending
it to third-party services that may keep it. The current defaults call cloud models through
`OLLAMA_API_KEY`, which must not be used on this dataset. Route A must run on local models (for
example the `run_all.sh` set) or on a service approved for credentialed MIMIC data. Route B uses the
MIMIC-IV demo (ODbL), so the current setup is fine there.

## 4. Contributions this can support

1. Leakage-safe reference: a time cut at the decision point instead of the whole EHR.
2. Hybrid verification: code for measurable facts, LLM vote for the rest.
3. Calibrated negatives: `not_addressed` vs `not_supported` vs `unverifiable`.
4. Beyond VeriFact: action concordance and omission detection.

## 5. Order of work

1. Obtain MIMIC-III-Ext-VeriFact-BHC (received from the instructor, 2026-11-12; downloading). The
   tooling is in place: `run_bhc.py` (steps 1 and 3), `score_bhc.py`, `cm/verifact_bhc.py`,
   `cm/notes.py`; see the README section "VeriFact-BHC track". First check on arrival: the reader's
   assumptions about label strings and configuration values.
2. Meanwhile, rerun the local panel with current prompts on the base 85 cases and score it against
   Claude's reference; choose the local judges.
3. Replay check: VeriFact's judge (verbatim prompts, temperature 0.1) with a local Llama 3.1 8B on
   the released Llama-8B contexts, compared with the released Llama-8B verdicts and scored with the
   irr_metrics-equivalent `score_bhc.py`. This shows the local setup reproduces VeriFact before
   anything is changed.
4. Route A step 1 (judge only) and step 2 (label calibration) on the released contexts.
5. Route A step 3 (retrieval) with `--context ours`.
6. Route B as the application demonstration.
