# Evaluation of AI clinical suggestions against patient records

- Input: `control_doctor_as_ai.json`; 80 cases, 7.62 AI suggestions per case on average.
- Models: atomizer `deepseek-v4.1-flash:cloud`; judge panel `deepseek-v4.1-flash:cloud`, `glm-5.3-flash:cloud`, `qwen2.5:14b` (majority vote; reasoning mode: none); 173 new model calls, 0 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 0.3% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 54 |
| supported / not_supported / not_addressed / unverifiable | 49 / 3 / 2 / 0 |
| Fact accuracy = supported / (supported + not_supported) | 94.2% |
| Cases with at least one not_supported fact | 1 / 80 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 0 | - | {} |
| presupposed by an action | 54 | 94.2% | {'supported': 49, 'not_addressed': 2, 'not_supported': 3} |
| clinical judgment | 0 | - | {} |
| vague | 0 | - | {} |

## 2. How close is the AI to what clinicians did?

Target (same class, or the drug the AI named) and direction (continue / stop / adjust) are decided by code; suggestions the rule file cannot classify go to the judge panel.

| Metric | Value |
|---|---|
| Treatment action atoms | 609 |
| Labels | {'match': 609} |
| Agreement (strict) = match / (match + partial_match + not_done) | 100.0% |
| Agreement (lenient) = (match + partial_match) / same | 100.0% |

Monitoring/assessment atoms: 1 (reported separately, not part of agreement): {'performed': 1}; performed rate among observable items 100.0%. 0 'goal' atoms with no concrete action are not scored.

## 3. What did the AI miss?

Vital = a class the rule file marks vital, or one whose indication was present at the decision time (for example low potassium followed by potassium chloride). Other non-routine classes are okay.

| Recall | All suggestions (micro / per-case) | First 3 suggestions only (micro / per-case) |
|---|---|---|
| vital (213/214) | 99.5% / 99.9% | 42.1% / 47.1% |
| okay (394/396) | 99.5% / 99.7% | 35.6% / 46.9% |
| all (607/610) | 99.5% / 99.7% | 37.9% / 51.0% |

144 clinician actions answered an abnormality present at the decision time; the AI missed 0 of them. Most often missed vital classes: renal replacement therapy (1)

### Problem-linked omissions

| Case | Clinicians gave | Indication at the decision time | AI suggestions |
|---|---|---|---|

## 4. not_supported facts

| Case | AI sentence | Atomic fact | Kind | Evidence |
|---|---|---|---|---|
| M32391858 | Administer Potassium Chloride Replacement (Critical Care and Oncology). | Potassium is low. | presupposed by an action | Latest potassium 3.4 mEq/L at 2201-10-31 02:06:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| M32391858 | Administer Neutra-Phos. | Phosphate is low. | presupposed by an action | Latest phosphate 2.8 mg/dL at 2201-10-31 02:06:00 (reference 2.7 to 4.5) is normal, not consistent with 'low'. |
| M32391858 | Administer Magnesium Sulfate. | Magnesium is low. | presupposed by an action | Latest magnesium 1.9 mg/dL at 2201-10-31 02:06:00 (reference 1.6 to 2.6) is normal, not consistent with 'low'. |

## 5. Judge panel

27 items went to the judge panel. Agreement: {'3/3': 24, 'split': 2, '2/3': 1} (split = no majority; the conservative label was used and the item needs human review).

## 6. Per-case score sheets

| Case | Facts | supported | not_supported | not_addressed | unverifiable | Treatment agreement | Vital recall | All recall |
|---|---|---|---|---|---|---|---|---|
| M37067082 | 0 | - | - | - | - | 100.0% | - | 100.0% |
| M31205490 | 0 | - | - | - | - | 100.0% | - | 100.0% |
| M33987268 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M36753294 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M37049133 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M35514836 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M32128372 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M34100191 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 91.7% | 94.7% |
| M32155744 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M31494479 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M35009126 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M39635619 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M34629895 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M32604416 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M34170353 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M36496303 | 0 | - | - | - | - | 100.0% | - | 100.0% |
| M32506122 | 0 | - | - | - | - | 100.0% | - | 100.0% |
| M31921355 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | 100.0% |
| M32359580 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M35128235 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M33348260 | 0 | - | - | - | - | 100.0% | - | 100.0% |
| M31959184 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M38507547 | 2 | 50.0% | 0.0% | 50.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M35636875 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | 100.0% |
| M35258379 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M32119961 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M39880770 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M33383124 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M31338022 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M38907302 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M33558396 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M37267577 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M39544395 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M37057036 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M35436337 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M37293400 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M31269608 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M30665396 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M35446858 | 0 | - | - | - | - | 100.0% | - | 100.0% |
| M36427705 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M34107647 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M32283063 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M39268883 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M34578020 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M37509585 | 0 | - | - | - | - | 100.0% | - | 100.0% |
| M38540883 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M30849778 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M35026312 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M33683112 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M30757476 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M36558922 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M37507305 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | 100.0% |
| M38197705 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M39492446 | 0 | - | - | - | - | 100.0% | - | 100.0% |
| M39497668 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M30913302 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | 100.0% |
| M30585761 | 0 | - | - | - | - | 100.0% | - | 100.0% |
| M30057454 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M33846653 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M33177122 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M32374504 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | 100.0% |
| M32587226 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M36091287 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M34499716 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M32391858 | 5 | 40.0% | 60.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M36059427 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M30458995 | 0 | - | - | - | - | 100.0% | - | 100.0% |
| M30101877 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M39084876 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M30932571 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M38587181 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M34531557 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 92.3% |
| M39061571 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M38430513 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M32166508 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M37127068 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M39711498 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% |
| M33281088 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M39142259 | 0 | - | - | - | - | 100.0% | 100.0% | 100.0% |
| M36107367 | 0 | - | - | - | - | 100.0% | 100.0% | 92.9% |
