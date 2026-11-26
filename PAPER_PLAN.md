# Paper plan

Written 2026-11-14. Decisions by the user: narrow the claim to fact verification; freeze the system
and treat the 85 MIMIC-IV demo cases as the development set; build an untouched test set on the eICU
demo; give the answer generators time-stamped input and test at least three of them.

## Claim

Checking an AI system's statements about an ICU patient against time-indexed structured records
needs state-aware, deterministic checks. Retrieval plus an LLM judge (VeriFact) misses most
statements the records contradict; a hybrid verifier (code for measurable facts and current state,
an LLM vote for the rest) finds most of them, also with a small local judge.

Not in the main claim: action concordance with clinician actions and omission detection. They have
no baseline and no validation; they stay in the repository as secondary analyses.

## Evidence so far (development set only)

`results_baseline85/RESULTS.md`: 85 cases, 486 fact atoms, reference written by Claude.

- VeriFact 59-68% agreement, 11-24% of Not Supported statements found; this evaluator 79% (local
  8B judge) to 88% (cloud vote), 58-73% found; 91.5% with VeriFact's label definitions.
- Ablation ladder with one local judge: time cut and reranker add nothing; this evaluator's rules in
  VeriFact's prompt add nothing; this evaluator's retrieval and context add about 6 points; code
  checks about 10.

Why this is not yet publishable evidence:

1. The reference is an LLM's, written by the model family that helped write the system's rules.
2. The system was changed after seeing the reference (two guard fixes, label alignment).
3. One database, 85 cases, one answer generator.
4. The generator's input had no timestamps (16,000 characters of values, one clock time), so it
   could not know that a patient had been extubated; the commonest error type is partly an artefact
   of the input.

## Design from here

| Part | Development set | Test set |
|---|---|---|
| Data | MIMIC-IV demo, 85 ICU stays (frozen at tag `v1.0-dev85`) | eICU Collaborative Research Database Demo v2.0.1 (open access, ODbL; over 2,500 unit stays, 20 hospitals) |
| Decision time | ICU admission + 24 h | the same |
| Generator input | values without times (as frozen) | every record with its time |
| Generators | deepseek-v4.1-flash | at least three models of different strength |
| System changes | allowed until the freeze | none after the freeze, apart from the eICU data adapter and item mapping |
| Reference | Claude, 486 atoms | clinicians on a stratified sample (two raters and adjudication); Claude on the rest, validated against the clinician sample |

Rules for the test set:

- The adapter and the item mapping are written from the eICU schema and documentation, not from
  verdicts. No system output on test cases is compared with any reference before the analysis plan
  below is fixed.
- Analysis plan: primary metric percent agreement with the reference at the sentence level (a
  sentence is wrong if any fact in it is Not Supported), so that systems with different
  decompositions can be compared end to end; secondary Gwet's AC1, MCC, sensitivity and PPV for
  Not Supported at the atom level. Confidence intervals by bootstrap over cases. Three repeats for
  sampled judges.
- Systems compared: VeriFact (its prompt, hybrid retrieval, one judge), this evaluator with VeriFact
  labels (full and all-to-judge), each with the same local judge and with the same strong judge.

Optional: VeriFact-BHC (MIMIC-III, clinician labels) to show the VeriFact port reproduces its
published results and to test this evaluator's judging on notes. Needs PhysioNet credentialing in
the user's or supervisor's own name; local models only.

## Order of work

1. Freeze: commit and tag the current system. Done at `v1.0-dev85`.
2. eICU adapter: records before T in the evaluator's row format; item mapping for the measures in
   `rules/measures.json`; case selection with a fixed seed. Status 2026-11-17: demo downloaded to
   `data/eicu-demo/` and surveyed; no code yet. The page says
   20 hospitals but `patient.csv.gz` has 186 distinct `hospitalid` values; check before describing it.
   Status 2026-11-17: done. `rules/eicu_items.json`, `cm/records_eicu.py`, `run.py --source eicu`,
   `run_baseline85.py --source eicu --atoms <run folder>`; tests in `tests/test_records_eicu.py`.
   100 cases (seed 20261117) from 1,189 usable stays, 75 hospitals (`input/eicu_triples.json`).
3. Time-stamped case prompts; answers from three generators. Status 2026-11-17: prompts list every
   record of the 24 h before T with its time (median 15,600 characters). Generators, chosen outside the
   judge vote's model families where possible: gpt-oss:120b (cloud, strong), deepseek-v4.1-flash
   (cloud, the development-set generator; same family as one judge), qwen2.5:7b-instruct (local, weak).
   Up to three suggestions per case, temperature 0, as on the development set.
   Both systems judge the same atoms (this evaluator's split), as on the development set; the
   sentence-level primary metric is computed from those atom verdicts. VeriFact's own decomposition
   remains deferred.
4. Run the systems; hold the outputs unscored.
5. Clinician sample and Claude reference; then score once. Status 2026-11-17: Claude reference done and
   frozen before any test output was read (`reference/fact_gold_eicu/`: 965 atoms in 100 cases, 731
   Supported / 200 Not Supported / 34 Not Addressed; `FROZEN.sha256`). Clinician subset drawn: 20
   cases, 199 atoms (`sample.json`, field `clinician_cases`). Clinician labelling not started.
   Status 2026-11-17 later: all 21 test runs scored once (`score_eicu.py`, `results_eicu/RESULTS.md`,
   `SCORES.md`). Sentence agreement: cloud vote 81.9%, VeriFact with deepseek-v4-pro 71.1%, evaluator
   with deepseek-v4-pro 69.0%, with llama 60.9%, VeriFact with llama 53.6%. Not done: three repeats of
   the sampled judges, clinician validation.
   Status 2026-11-17, error analysis: `error_analysis/ERRORS.md` (`analyze_errors.py`). Every false flag and
   miss of all setups is listed in both result sets. The vote's and VeriFact's (deepseek-v4-pro) are coded
   by cause and stratified by fact kind, generator and topic. VeriFact's misses are mostly earlier values or
   ended states taken as current and documentation taken as given. The vote's false flags are mostly
   evaluator rules (code checks testing another claim, the treatment-table rule, the 6 h median) and the
   header. Five doubtful reference labels are logged in `CHANGES.md`, unchanged.

## Deviations from the plan

1. 2026-11-17, after the first scoring: the eICU adapter (`cm/records_eicu.py`) now also gives the
   systems the case header from the patient table (ICU unit, sex and age, APACHE admission diagnosis) as
   three rows at unit admission. The generators and the test reference had this header; the systems did
   not, so 54 reference atoms rested on evidence the systems could not see. This changes the adapter
   after test outputs were seen, which the rules above exclude; it was decided by the user and is
   reported as such. Both result sets are kept: `results_eicu/` (adapter as planned, the pre-specified
   analysis) and `results_eicu_dx/` (with the header rows), each scored against the same frozen
   reference. Atoms and judge settings are unchanged; unchanged model requests are answered from the
   first runs' caches. No other system change. Result (`results_eicu_dx/RESULTS.md`): the vote's lead
   over VeriFact is unchanged (+10.8 sentence agreement); the single-judge comparisons moved by 2-6
   points, as much from retrieval shifts on unchanged atoms as from the header, so the three repeats of
   each sampled judge are needed before reporting same-judge differences.
   Repeats done on this configuration (`results_eicu_dx/REPEATS.md`): every setup within 1.5 points over
   three repeats; mean sentence agreement vote 82.3%, VeriFact with the strong judge 71.1% (+11.2,
   +6.7 to +15.6); same-judge differences +4.8 (strong, +0.3 to +9.2) and +4.5 (local, -1.3 to +10.1).
   The repeats were run on the header configuration only, not on `results_eicu/`.
2. 2026-11-18, after scoring: a second published baseline was added on the header configuration, the
   FactEHR entailment judge (`run_factehr.py`, `score_factehr.py`, `results_eicu_dx/FACTEHR.md`). It is
   not part of the pre-specified analysis and is reported as an added comparison.
   - Run once, on two of the three answer sets (gpt-oss-120b, deepseek-v4.1-flash). qwen2.5-7b was not
     run, by the user's decision.
   - Every run is compared on the same two answer sets.
   - It is scored as planned (FactEHR's 0 = Not Supported) and also with Not Supported and Not Addressed
     merged for every run, since FactEHR has no third label.
