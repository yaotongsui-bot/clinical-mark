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
   `rules/measures.json`; case selection with a fixed seed.
3. Time-stamped case prompts; answers from three generators.
4. Run the systems; hold the outputs unscored.
5. Clinician sample and Claude reference; then score once.
