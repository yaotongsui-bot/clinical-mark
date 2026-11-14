# Model selection: final record

Closed 2026-11-06. This records the chosen setup and what supports it. All references are Claude's own work, not clinician truth.

## Chosen setup (run.py defaults)

| Stage | Choice |
|---|---|
| Splitting | `deepseek-v4-pro:0813` with `prompts/ai_atomizer.txt` |
| Judging | Majority vote of `deepseek-v4-pro:0813`, `minimax-m3.1-flash`, `glm-5.3` |
| Everything measurable | Code and rule files, as before |

Kimi was excluded at the user's request. The earlier prompt is in `prompts/ai_atomizer_v1.txt`.

## Evidence

| Check | Result | File |
|---|---|---|
| Vote, 20 blind cases (133 judged items) | 91.7% agreement, kappa 0.80 on blind verdicts; 94.0%, kappa 0.85 after review; 12/12 false facts found, 16 flagged | `blind20_comparison_blind.md`, `blind20_comparison.md` |
| Vote, 85 base cases (275 judged items) | 96.4%, kappa 0.91; leans high, because the reference was revised after seeing model disagreements | `vote_comparison.md` |
| Other votes | With deepseek-v4.1-flash or mimo-v2.6-pro in place of glm-5.3: 91.7% on the blind cases after review, 95.6% and 95.3% on base | `replacement_comparison.md` |
| Splitting, pro with the new prompt | F1 0.919 on base (was 0.837), 0.907 on blind (was 0.878); facts found 91.6% and 85.7% (were 62.8% and 76.0%) | `split_trial.md` |
| Known-answer tests | 202/202 injected errors found; 610/610 clinician actions matched. These mainly test code rules, and they ran with the earlier prompt | `../validation/known_answer_tests_current.md` |

The blind figures are the best estimate of judging quality. The new prompt was written from the base review, so its base gain leans high.

## Fixed in the pipeline

- "Replete magnesium" no longer counts as nutrition.
- Oxygen device rows count as delivery, and "None" or an ended non-invasive ventilation procedure can show a treatment is off.
- A value check ignores context such as "on 2 L/min".
- Ventilator-setting statements always see the latest O2 device rows, and the judge prompt treats a setting as stale after a later non-ventilator device.
- A later non-invasive device ends "on mechanical ventilation".
- Potassium phosphate counts as potassium replacement.

## Not verified

- The final setup has not been run end to end: splitting and judging were tested separately. The final prompt has not been through the known-answer tests.
- Existing results and pages elsewhere in this project predate these changes.
- `run_all.sh` will request answers cached before 2026-11-06 again, because prompts changed.
- `results_final/s1` to `s3` are stopped partial runs; do not use them. `results_final/base` is the pro-split vote with flash and mimo.

## Questions for clinicians

1. Does an infusion that ended within the past 24 hours, with no running record, count as "currently being given"? Six of the eight remaining blind disagreements turn on this.
2. Does "Dialysis patient" support chronic kidney disease?
3. Does "Pressure Ulcer Stage #1" with value code 2 support a stage 1 ulcer?
4. Should judges treat a value such as troponin-T 0.01 ng/mL as normal when the record gives no range?

The sheet for clinician labels is `../annotation_set/`; these labels are the step that can replace Claude's reference.
