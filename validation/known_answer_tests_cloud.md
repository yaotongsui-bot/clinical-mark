# Known-answer tests

Inputs with a known answer, built by make_controls.py from the clinicians' own actions and from suggestions the evaluator judged correct. They test the evaluator without human labels; they do not show whether its verdicts agree with clinicians on real AI answers.

## Error injection (every edited suggestion carries one error)

Each edited suggestion was evaluated alone. Detected: the evaluator gave the expected kind of verdict (fact not_supported; treatment not_done or partial_match). Missed: it judged the suggestion correct. Not scored: it gave no verdict (not_addressed, vague_target, condition_not_met, ...).

| Error | Edit | n | Detected | Missed | Not scored | Sensitivity | Sensitivity when scored |
|---|---|---|---|---|---|---|---|
| direction | reverse a supported abnormality | 22 | 22 | 0 | 0 | 100.0% (22/22) | 100.0% (22/22) |
| drug | matched treatment -> drug from a group never given | 60 | 60 | 0 | 0 | 100.0% (60/60) | 100.0% (60/60) |
| stop | matched 'Continue X' -> 'Discontinue X' | 60 | 60 | 0 | 0 | 100.0% (60/60) | 100.0% (60/60) |
| added | add 'Start X' from a group never given | 60 | 60 | 0 | 0 | 100.0% (60/60) | 100.0% (60/60) |

- Fabricated 'currently receiving X' premises about the inserted drug (from edited 'Continue X' suggestions): {'not_addressed': 26, 'not_supported': 1} (anything but supported is correct).

### Missed or not scored

| Error | Case | Edited suggestion | Verdict | Label | Reason |
|---|---|---|---|---|---|

## Doctor as AI (every suggestion is true)

80 cases; each suggestion is a treatment the clinicians gave after the decision.

| Measure | Expected | Result |
|---|---|---|
| Treatment agreement (strict) | 100% | 100.0% (609/609) |
| Suggestions matched, of all treatment suggestions | 100% | 100.0% (609/609) |
| Vital recall | 100% | 99.5% (213/214) |
| All recall | 100% | 99.5% (607/610) |
| 'Currently receiving X' premises supported | 100% | 90.7% (49/54) |

- Treatment labels: {'match': 609}
- Routed to the monitoring track: {'performed': 1}
- Premise labels (from 'Continue X'): {'supported': 49, 'not_supported': 3, 'not_addressed': 2}
- Suggestions without a treatment atom: 1

### Suggestions not matched

| Case | Suggestion | Clinician class | AI-side class | Label | Reason |
|---|---|---|---|---|---|

### Suggestions without a treatment atom

| Case | Claim | Clinician class |
|---|---|---|
| M32119961 | M32119961A9 | imaging |

### Premises not supported

| Case | Statement | Label | Reason |
|---|---|---|---|
| M32391858 | Potassium is low. | not_supported | Latest potassium 3.4 mEq/L at 2201-10-31 02:06:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| M32391858 | Phosphate is low. | not_supported | Latest phosphate 2.8 mg/dL at 2201-10-31 02:06:00 (reference 2.7 to 4.5) is normal, not consistent with 'low'. |
| M32391858 | Magnesium is low. | not_supported | Latest magnesium 1.9 mg/dL at 2201-10-31 02:06:00 (reference 1.6 to 2.6) is normal, not consistent with 'low'. |
| M37049133 | D5NS is currently being given. | not_addressed | The judges disagreed; the conservative label was used and the item needs human review. |
| M38507547 | Dextrose 5% is currently being given. | not_addressed | The judges disagreed; the conservative label was used and the item needs human review. |

