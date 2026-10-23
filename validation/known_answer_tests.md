# Known-answer tests

Inputs with a known answer, built by make_controls.py from the clinicians' own actions and from suggestions the evaluator judged correct. They test the evaluator without human labels; they do not show whether its verdicts agree with clinicians on real AI answers.

## Error injection (every edited suggestion carries one error)

Each edited suggestion was evaluated alone. Detected: the evaluator gave the expected kind of verdict (fact not_supported; treatment not_done or partial_match). Missed: it judged the suggestion correct. Not scored: it gave no verdict (not_addressed, vague_target, condition_not_met, ...).

| Error | Edit | n | Detected | Missed | Not scored | Sensitivity | Sensitivity when scored |
|---|---|---|---|---|---|---|---|
| direction | reverse a supported abnormality | 22 | 21 | 0 | 1 | 95.5% (21/22) | 100.0% (21/21) |
| drug | matched treatment -> drug from a group never given | 60 | 60 | 0 | 0 | 100.0% (60/60) | 100.0% (60/60) |
| stop | matched 'Continue X' -> 'Discontinue X' | 60 | 60 | 0 | 0 | 100.0% (60/60) | 100.0% (60/60) |
| added | add 'Start X' from a group never given | 60 | 60 | 0 | 0 | 100.0% (60/60) | 100.0% (60/60) |

- Fabricated 'currently receiving X' premises about the inserted drug (from edited 'Continue X' suggestions): {'not_addressed': 26, 'not_supported': 1} (anything but supported is correct).

### Missed or not scored

| Error | Case | Edited suggestion | Verdict | Label | Reason |
|---|---|---|---|---|---|
| direction | M36893762-R08 | Monitor blood pressure closely due to recent low readings. | not scored | no atom |  |

## Doctor as AI (every suggestion is true)

80 cases; each suggestion is a treatment the clinicians gave after the decision.

| Measure | Expected | Result |
|---|---|---|
| Treatment agreement (strict) | 100% | 100.0% (610/610) |
| Suggestions matched, of all treatment suggestions | 100% | 100.0% (610/610) |
| Vital recall | 100% | 99.5% (213/214) |
| All recall | 100% | 99.5% (607/610) |
| 'Currently receiving X' premises supported | 100% | 100.0% (50/50) |

- Treatment labels: {'match': 610}
- Routed to the monitoring track: none
- Premise labels (from 'Continue X'): {'supported': 50}
- Suggestions without a treatment atom: 0

### Suggestions not matched

| Case | Suggestion | Clinician class | AI-side class | Label | Reason |
|---|---|---|---|---|---|

