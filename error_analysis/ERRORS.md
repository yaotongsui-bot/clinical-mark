# eICU test set: error analysis

Every false flag and miss of the test runs against the frozen reference (`reference/fact_gold_eicu/fact_gold_eicu_claude.frozen.csv`, checksum verified), at the atom level with VeriFact's three labels (`unverifiable` counts as Not Addressed). Written by `analyze_errors.py`; one row per error in `errors.csv`, causes in `causes.csv`.

- False flag: the setup says Not Supported, the reference says Supported or Not Addressed (rate over the 765 reference atoms that are not Not Supported).
- Miss: the reference says Not Supported, the setup does not (rate over the 200 Not Supported atoms).
- Other: Supported vs Not Addressed, either way (counted only).

Both result sets are shown side by side; neither is the primary one. First runs: `results_eicu/` (pre-specified analysis). With case header: `results_eicu_dx/` (repeat 1 of three). "Persists" marks a header-set error that recurs in the same direction in repeats 2 and 3 (`results_eicu_dx_r2/`, `_r3/`).

## Reading

Numbers are given as first runs / with case header. Causes were coded by Claude for every false flag and miss of
the cloud vote and of VeriFact with deepseek-v4-pro (392 atom-run pairs on 307 atoms), from the atom, the
reference evidence and note, and the system's stated reason. The case records were opened where these did not
settle it (cases E172015, E297175, E454584, E521456). There is one cause per atom and run. Where the two
result sets gave different reasons, the cause fits the header run and the note says so. A single coder from the
model family that wrote the reference did this coding; no second coder has checked it.

**How the errors split.** VeriFact errs by missing: 163 / 159 of the 200 Not Supported facts (80-82%), against
41 / 45 false flags (5-6% of the rest). The vote misses 62 / 71 (31-36%) and false-flags 89 / 78 (10-12%).
Almost every vote miss is also a VeriFact miss (55 of 62, 65 of 71). VeriFact's errors recur across repeats
more often than the vote's: 93% against 79% of header-run errors recur in the same direction in all three repeats.

**VeriFact's misses come from reading the record as a history, not as a state at T.**

- An earlier value or an ended state accepted for a statement about the present: 86 / 83 misses, about half.
  Examples: hyperkalemia from potassium 6.3-6.9 hours earlier when the latest value is 4.2 (E3223097); infusions
  that stopped before T; BiPAP or ventilator settings charted before the patient moved to nasal cannula or
  high-flow oxygen.
- A treatment-table entry, an order or a placement taken as the treatment being given: 28 / 28. Examples:
  "milrinone" in the treatment table read as a running infusion, PRN orders read as given, and a pericardial
  drain placement read as a drain in place.
- Not Addressed for a statement the records address without showing (the reference's Not Supported): 18 / 19.
  Unchecked qualifiers ("active", "ongoing", "broad-spectrum", "variability"): 15 / 14. Retrieval that
  returned no relevant rows, for example "no blood pressure values" when only respiratory rate rows came back:
  13 / 13.
- By fact kind, VeriFact misses 83-84% of Not Supported presuppositions ("X is currently being given", "the
  patient is on ventilation"), against 22-31% for the vote. By topic it misses 88-93% of Not Supported
  ventilation and oxygen facts.

**VeriFact's few false flags** come mostly from comparing a stated range with every value in the record rather
than the recent ones: 21 / 21, for example "SBP 150-170s" rejected because of a 124 earlier in the stay.
Strict qualifiers ("persistent" read as every value elevated) account for 8 / 10, and missed rows for 8 / 9.

**The vote's false flags come from rules more than from judges.**

- The code check tested another claim: 19 / 19. "Fluctuating" or "intermittent" hypertension, tachycardia or
  hypoxemia was checked as the current state, and "MAP as low as 71" as "MAP is low". Diastolic pressure is
  not checked for "diastolic hypertension", and fingerstick glucose is not counted as glucose.
- A treatment documented in the treatment table within 24 h (guideline rule 7), or under an active scheduled
  order, was rejected for lack of an administration row, which eICU does not have: 18 / 23. Rule-7 facts are
  48% / 67% false-flagged by the vote.
- A different summary of the same values (6 h median against the latest value, or a code threshold such as
  SpO2 90%): 10 / 10. A ventilator charting gap read as extubation: 5 / 5.
- Judgement statements ("risk of", "possible", "is needed") that the reference leaves Not Addressed but the
  judges rejected against values: 6 / 8.
- Diagnoses only in the case header: 11 / 0. The header removes these.
- In the first runs, 6 false flags carry a vote reason about another statement, for example a reason about
  borderline glucose for "Sepsis is present" (E1829278). The header run has none. This was not traced to its
  source and needs a check of the judge prompt and the cached responses.

**The vote's misses** are mostly judged facts (44 / 53 of 62 / 71). An earlier value or ended state accounts for
20 / 27: the judges accept earlier device rows or ended infusions (15 / 22), and the code's value check accepts an
earlier matching value instead of the latest (5 / 5). The administration guard turns a judged "supported" into
Not Addressed for a statement the reference calls Not Supported (6 / 8). For code-checked facts, a 6 h median or
a 24 h count stands in for the latest value (7 / 7).

**Shared errors.** Most errors both systems make are the same misreading: an earlier value or ended state (18 /
23 shared misses) and documentation taken as given (5 / 7). The vote avoids most of VeriFact's misses through
code checks and the "running at decision time" rows. What remains is mostly judged facts about devices and
infusions whose stop the records show only indirectly (a later device row, a rate of 0, no charting for over 4 h).

**Reference labels in doubt.** Five atoms look wrongly or arguably labelled on re-reading:
`E172015A2::07` (MAP 58-112 is charted), `E172015A3::11` (magnesium 1.6 against the 1.6-2.6 range of rule 9),
`E297175A1::03` (a lab FiO2 of 45% is later than the 40% called latest), `E521456A3::08` (CAM-ICU "No" is
charted three times) and `E1290248A1::02` (SpO2 drops read as artefact). They are listed in
`reference/fact_gold_eicu/CHANGES.md`; the frozen reference is unchanged. Together they account for 5 / 5 vote
errors and 3 / 3 VeriFact errors.

**What this means for the comparison.** VeriFact's deficit is structural: it misses state changes and treats
documentation as administration, and these errors recur across repeats. Many of the vote's false flags come from
fixable evaluator rules: code checks that test a different claim, the 6 h median, the treatment-table rule and
the ventilator gap. These four causes account for 63 / 68 of its 151 / 149 errors (about 42-46%). They were found
on the test set, so any fix needs a new test set before it can be claimed.

## 1. Errors by direction, every setup

| Setup | Set | S to NS | NA to NS | False flags (rate) | NS to S | NS to NA | Misses (rate) | Other (S/NA) | Header errors persisting in 3 repeats |
|---|---|---|---|---|---|---|---|---|---|
| Evaluator, vote | first | 80 | 9 | 89 (12%) | 44 | 18 | 62 (31%) | 72 |  |
| Evaluator, vote | header | 69 | 9 | 78 (10%) | 56 | 15 | 71 (36%) | 54 | 118 of 149 (79%) |
| Evaluator, deepseek-v4-pro | first | 207 | 21 | 228 (30%) | 43 | 8 | 51 (26%) | 36 |  |
| Evaluator, deepseek-v4-pro | header | 114 | 14 | 128 (17%) | 63 | 12 | 75 (38%) | 43 | 133 of 203 (66%) |
| VeriFact, deepseek-v4-pro | first | 39 | 2 | 41 (5%) | 127 | 36 | 163 (82%) | 109 |  |
| VeriFact, deepseek-v4-pro | header | 43 | 2 | 45 (6%) | 124 | 35 | 159 (80%) | 82 | 190 of 204 (93%) |
| Evaluator, llama 8B | first | 240 | 25 | 265 (35%) | 65 | 9 | 74 (37%) | 24 |  |
| Evaluator, llama 8B | header | 225 | 26 | 251 (33%) | 65 | 8 | 73 (36%) | 25 | 309 of 324 (95%) |
| Evaluator, llama 8B, no code | first | 363 | 27 | 390 (51%) | 77 | 0 | 77 (38%) | 8 |  |
| Evaluator, llama 8B, no code | header | 370 | 28 | 398 (52%) | 77 | 0 | 77 (38%) | 6 | 450 of 475 (95%) |
| VeriFact, llama 8B | first | 220 | 19 | 239 (31%) | 142 | 5 | 147 (74%) | 26 |  |
| VeriFact, llama 8B | header | 179 | 18 | 197 (26%) | 150 | 6 | 156 (78%) | 22 | 333 of 353 (94%) |
| VeriFact, llama 8B, all records | first | 221 | 16 | 237 (31%) | 139 | 5 | 144 (72%) | 39 |  |
| VeriFact, llama 8B, all records | header | 193 | 18 | 211 (28%) | 146 | 5 | 151 (76%) | 32 | 334 of 362 (92%) |

S = Supported, NS = Not Supported, NA = Not Addressed (reference label first). Not Supported found = 1 - misses/200 and PPV = true flags/(true flags + false flags) reproduce `SCORES.md`.

## 2. Shared and separate errors

| A | B | Set | Misses: both | only A | only B | False flags: both | only A | only B |
|---|---|---|---|---|---|---|---|---|
| Evaluator, vote | VeriFact, deepseek-v4-pro | first | 55 | 7 | 108 | 9 | 80 | 32 |
| Evaluator, vote | VeriFact, deepseek-v4-pro | header | 65 | 6 | 94 | 12 | 66 | 33 |
| Evaluator, deepseek-v4-pro | VeriFact, deepseek-v4-pro | first | 46 | 5 | 117 | 14 | 214 | 27 |
| Evaluator, deepseek-v4-pro | VeriFact, deepseek-v4-pro | header | 69 | 6 | 90 | 14 | 114 | 31 |
| Evaluator, llama 8B | VeriFact, llama 8B | first | 55 | 19 | 92 | 101 | 164 | 138 |
| Evaluator, llama 8B | VeriFact, llama 8B | header | 56 | 17 | 100 | 74 | 177 | 123 |

## 3. Where the vote and VeriFact (deepseek-v4-pro) err

Counts with rates in brackets: false flags over the stratum's atoms that are not Not Supported in the reference, misses over its Not Supported atoms.

### By fact kind (reference)

| Stratum | Reference not NS / NS | Evaluator, vote, first: false flags / misses | Evaluator, vote, header: false flags / misses | VeriFact, deepseek-v4-pro, first: false flags / misses | VeriFact, deepseek-v4-pro, header: false flags / misses |
|---|---|---|---|---|---|
| observed | 398 / 70 | 40 (10%) / 32 (46%) | 36 (9%) / 32 (46%) | 36 (9%) / 53 (76%) | 37 (9%) / 52 (74%) |
| presupposition | 323 / 126 | 36 (11%) / 28 (22%) | 36 (11%) / 39 (31%) | 4 (1%) / 106 (84%) | 7 (2%) / 104 (83%) |
| judgment | 44 / 4 | 13 (30%) / 2 (50%) | 6 (14%) / 0 (0%) | 1 (2%) / 4 (100%) | 1 (2%) / 3 (75%) |

### By generator

| Stratum | Reference not NS / NS | Evaluator, vote, first: false flags / misses | Evaluator, vote, header: false flags / misses | VeriFact, deepseek-v4-pro, first: false flags / misses | VeriFact, deepseek-v4-pro, header: false flags / misses |
|---|---|---|---|---|---|
| gpt-oss-120b | 182 / 80 | 21 (12%) / 26 (32%) | 18 (10%) / 26 (32%) | 7 (4%) / 62 (78%) | 8 (4%) / 60 (75%) |
| deepseek-v4.1-flash | 460 / 70 | 49 (11%) / 24 (34%) | 43 (9%) / 27 (39%) | 31 (7%) / 60 (86%) | 32 (7%) / 59 (84%) |
| qwen2.5-7b | 123 / 50 | 19 (15%) / 12 (24%) | 17 (14%) / 18 (36%) | 3 (2%) / 41 (82%) | 5 (4%) / 40 (80%) |

### By topic (keyword rules on the atom text)

| Stratum | Reference not NS / NS | Evaluator, vote, first: false flags / misses | Evaluator, vote, header: false flags / misses | VeriFact, deepseek-v4-pro, first: false flags / misses | VeriFact, deepseek-v4-pro, header: false flags / misses |
|---|---|---|---|---|---|
| Ventilation and oxygen | 127 / 43 | 10 (8%) / 17 (40%) | 10 (8%) / 19 (44%) | 6 (5%) / 40 (93%) | 5 (4%) / 38 (88%) |
| Devices, procedures and monitoring | 10 / 8 | 1 (10%) / 4 (50%) | 1 (10%) / 5 (62%) | 0 (0%) / 7 (88%) | 0 (0%) / 7 (88%) |
| Drugs, infusions and orders | 215 / 84 | 19 (9%) / 16 (19%) | 23 (11%) / 23 (27%) | 2 (1%) / 65 (77%) | 3 (1%) / 65 (77%) |
| Labs | 159 / 14 | 6 (4%) / 5 (36%) | 7 (4%) / 5 (36%) | 9 (6%) / 10 (71%) | 8 (5%) / 9 (64%) |
| Vital signs and haemodynamics | 153 / 37 | 26 (17%) / 14 (38%) | 26 (17%) / 14 (38%) | 19 (12%) / 27 (73%) | 23 (15%) / 27 (73%) |
| Neurological, sedation and pain scores | 24 / 3 | 3 (12%) / 1 (33%) | 2 (8%) / 1 (33%) | 3 (12%) / 3 (100%) | 3 (12%) / 3 (100%) |
| Diagnoses and conditions | 77 / 11 | 24 (31%) / 5 (45%) | 9 (12%) / 4 (36%) | 2 (3%) / 11 (100%) | 3 (4%) / 10 (91%) |

### By the evaluator's route (code check or judge; VeriFact judges every atom)

| Stratum | Reference not NS / NS | Evaluator, vote, first: false flags / misses | Evaluator, vote, header: false flags / misses | VeriFact, deepseek-v4-pro, first: false flags / misses | VeriFact, deepseek-v4-pro, header: false flags / misses |
|---|---|---|---|---|---|
| Code check (367) | 314 / 53 | 35 (11%) / 18 (34%) | 35 (11%) / 18 (34%) | 27 (9%) / 40 (75%) | 29 (9%) / 38 (72%) |
| Judge (598) | 451 / 147 | 54 (12%) / 44 (30%) | 43 (10%) / 53 (36%) | 14 (3%) / 123 (84%) | 16 (4%) / 121 (82%) |

### Header and rule-7 atoms

| Stratum | Reference not NS / NS | Evaluator, vote, first: false flags / misses | Evaluator, vote, header: false flags / misses | VeriFact, deepseek-v4-pro, first: false flags / misses | VeriFact, deepseek-v4-pro, header: false flags / misses |
|---|---|---|---|---|---|
| Header atoms (54) | 46 / 8 | 17 (37%) / 4 (50%) | 1 (2%) / 4 (50%) | 1 (2%) / 8 (100%) | 0 (0%) / 7 (88%) |
| Rule-7 atoms (21) | 21 / 0 | 10 (48%) / 0 (-) | 14 (67%) / 0 (-) | 1 (5%) / 0 (-) | 3 (14%) / 0 (-) |
| All other atoms | 698 / 192 | 62 (9%) / 58 (30%) | 63 (9%) / 67 (35%) | 39 (6%) / 155 (81%) | 42 (6%) / 152 (79%) |

## 4. Causes

Coded for every false flag and miss of the two runs in either set: 392 (atom, run) pairs, 392 coded, 0 uncoded.

| Code | Cause | Description |
|---|---|---|
| `past_as_current` | Earlier value or ended state taken as current | An earlier lab or vital-sign value, an ended infusion, or a device or ventilator setting from before a change, accepted for a statement about the present. |
| `record_as_given` | Documentation or order taken as given | A treatment-table entry, an order (PRN, or marked running although the infusion had stopped) or a device placement taken as the treatment being given or the device in place. |
| `addressed_called_na` | Addressed statement called Not Addressed | The records address the statement without showing it (the reference's Not Supported), but the system answered Not Addressed; includes the evaluator's administration guard and its 'no ventilator record' rule. |
| `treatment_not_accepted` | Documented treatment not accepted as given | A drug documented in the treatment table within 24 h (guideline rule 7) or under an active scheduled order, rejected because eICU has no administration row. |
| `vent_gap` | Ventilator charting gap read as extubation | The code rule (more than 6 h without a ventilator row means not ventilated) applied although no extubation was charted. |
| `header_only` | Evidence only in the case header | The fact rests on the admission diagnosis or unit, which the first runs' records did not have. |
| `window_or_range` | Different window, summary or threshold | The same recent values summarised differently: a stated range checked against every value, the 6 h median or a 24 h count instead of the latest value, or a value at a threshold. |
| `qualifier` | Qualifier read differently | A qualifier, tense or detail (persistent, fluctuating, borderline, active, ongoing, as-needed, infusion, device) read more strictly than the reference, or not checked. |
| `code_rule` | Code check tested another claim | The code check tested a different claim, component or item than the statement: 'as low as 71' as 'low', a trend as the current state, diastolic pressure not checked, fingerstick glucose not counted. |
| `evidence_missed` | Deciding records not retrieved or misread | The rows that decide the statement were not in the system's context, or were misread. |
| `judgement_statement` | Judgement statement judged | A risk, possibility or need statement that the reference leaves Not Addressed, judged against values instead. |
| `judge_mismatch` | Reason addresses another statement | The vote's stated reason discusses a different statement from the one judged. |
| `reference_doubtful` | Reference label doubtful | On re-reading the records the reference label looks wrong or arguable; listed in reference/fact_gold_eicu/CHANGES.md, label not changed. |

### Evaluator, vote

| Cause | First: false flags | First: misses | Header: false flags | Header: misses | Header errors persisting in 3 repeats |
|---|---|---|---|---|---|
| Earlier value or ended state taken as current | 0 | 20 | 0 | 27 | 17 of 27 |
| Documentation or order taken as given | 0 | 6 | 0 | 8 | 6 of 8 |
| Addressed statement called Not Addressed | 0 | 12 | 0 | 12 | 7 of 12 |
| Documented treatment not accepted as given | 18 | 0 | 23 | 0 | 16 of 23 |
| Ventilator charting gap read as extubation | 5 | 0 | 5 | 0 | 5 of 5 |
| Evidence only in the case header | 11 | 2 | 0 | 0 | 0 of 0 |
| Different window, summary or threshold | 10 | 7 | 10 | 7 | 17 of 17 |
| Qualifier read differently | 5 | 7 | 3 | 8 | 10 of 11 |
| Code check tested another claim | 19 | 4 | 19 | 4 | 23 of 23 |
| Deciding records not retrieved or misread | 6 | 2 | 7 | 3 | 8 of 10 |
| Judgement statement judged | 6 | 0 | 8 | 0 | 5 of 8 |
| Reason addresses another statement | 6 | 0 | 0 | 0 | 0 of 0 |
| Reference label doubtful | 3 | 2 | 3 | 2 | 4 of 5 |

Evaluator, vote, causes by fact kind (errors, first / header):

| Cause | observed | presupposition | judgment |
|---|---|---|---|
| Earlier value or ended state taken as current | 11 / 11 | 9 / 16 | 0 / 0 |
| Documentation or order taken as given | 0 / 0 | 6 / 8 | 0 / 0 |
| Addressed statement called Not Addressed | 0 / 0 | 11 / 12 | 1 / 0 |
| Documented treatment not accepted as given | 0 / 0 | 18 / 23 | 0 / 0 |
| Ventilator charting gap read as extubation | 1 / 1 | 4 / 4 | 0 / 0 |
| Evidence only in the case header | 3 / 0 | 3 / 0 | 7 / 0 |
| Different window, summary or threshold | 13 / 13 | 4 / 4 | 0 / 0 |
| Qualifier read differently | 9 / 9 | 3 / 2 | 0 / 0 |
| Code check tested another claim | 23 / 23 | 0 / 0 | 0 / 0 |
| Deciding records not retrieved or misread | 7 / 7 | 1 / 3 | 0 / 0 |
| Judgement statement judged | 0 / 0 | 2 / 3 | 4 / 5 |
| Reason addresses another statement | 1 / 0 | 3 / 0 | 2 / 0 |
| Reference label doubtful | 4 / 4 | 0 / 0 | 1 / 1 |

Evaluator, vote, causes by generator (errors, first / header):

| Cause | gpt-oss-120b | deepseek-v4.1-flash | qwen2.5-7b |
|---|---|---|---|
| Earlier value or ended state taken as current | 9 / 9 | 9 / 10 | 2 / 8 |
| Documentation or order taken as given | 3 / 3 | 2 / 4 | 1 / 1 |
| Addressed statement called Not Addressed | 5 / 5 | 1 / 1 | 6 / 6 |
| Documented treatment not accepted as given | 5 / 8 | 6 / 8 | 7 / 7 |
| Ventilator charting gap read as extubation | 2 / 2 | 2 / 2 | 1 / 1 |
| Evidence only in the case header | 5 / 0 | 6 / 0 | 2 / 0 |
| Different window, summary or threshold | 3 / 3 | 13 / 13 | 1 / 1 |
| Qualifier read differently | 4 / 3 | 6 / 6 | 2 / 2 |
| Code check tested another claim | 4 / 4 | 16 / 16 | 3 / 3 |
| Deciding records not retrieved or misread | 2 / 3 | 6 / 7 | 0 / 0 |
| Judgement statement judged | 2 / 4 | 0 / 0 | 4 / 4 |
| Reason addresses another statement | 3 / 0 | 3 / 0 | 0 / 0 |
| Reference label doubtful | 0 / 0 | 3 / 3 | 2 / 2 |

### VeriFact, deepseek-v4-pro

| Cause | First: false flags | First: misses | Header: false flags | Header: misses | Header errors persisting in 3 repeats |
|---|---|---|---|---|---|
| Earlier value or ended state taken as current | 0 | 86 | 0 | 83 | 80 of 83 |
| Documentation or order taken as given | 0 | 28 | 0 | 28 | 28 of 28 |
| Addressed statement called Not Addressed | 0 | 18 | 0 | 19 | 18 of 19 |
| Documented treatment not accepted as given | 1 | 0 | 3 | 0 | 1 of 3 |
| Evidence only in the case header | 1 | 1 | 0 | 0 | 0 of 0 |
| Different window, summary or threshold | 21 | 0 | 21 | 0 | 20 of 21 |
| Qualifier read differently | 8 | 15 | 10 | 14 | 20 of 24 |
| Deciding records not retrieved or misread | 8 | 13 | 9 | 13 | 19 of 22 |
| Judgement statement judged | 1 | 0 | 1 | 0 | 1 of 1 |
| Reference label doubtful | 1 | 2 | 1 | 2 | 3 of 3 |

VeriFact, deepseek-v4-pro, causes by fact kind (errors, first / header):

| Cause | observed | presupposition | judgment |
|---|---|---|---|
| Earlier value or ended state taken as current | 31 / 30 | 55 / 53 | 0 / 0 |
| Documentation or order taken as given | 0 / 0 | 27 / 27 | 1 / 1 |
| Addressed statement called Not Addressed | 4 / 4 | 13 / 14 | 1 / 1 |
| Documented treatment not accepted as given | 0 / 0 | 1 / 3 | 0 / 0 |
| Evidence only in the case header | 1 / 0 | 0 / 0 | 1 / 0 |
| Different window, summary or threshold | 21 / 21 | 0 / 0 | 0 / 0 |
| Qualifier read differently | 16 / 18 | 6 / 5 | 1 / 1 |
| Deciding records not retrieved or misread | 14 / 14 | 7 / 8 | 0 / 0 |
| Judgement statement judged | 0 / 0 | 1 / 1 | 0 / 0 |
| Reference label doubtful | 2 / 2 | 0 / 0 | 1 / 1 |

VeriFact, deepseek-v4-pro, causes by generator (errors, first / header):

| Cause | gpt-oss-120b | deepseek-v4.1-flash | qwen2.5-7b |
|---|---|---|---|
| Earlier value or ended state taken as current | 31 / 30 | 35 / 34 | 20 / 19 |
| Documentation or order taken as given | 12 / 12 | 5 / 5 | 11 / 11 |
| Addressed statement called Not Addressed | 6 / 7 | 6 / 6 | 6 / 6 |
| Documented treatment not accepted as given | 0 / 1 | 1 / 1 | 0 / 1 |
| Evidence only in the case header | 1 / 0 | 1 / 0 | 0 / 0 |
| Different window, summary or threshold | 5 / 5 | 15 / 16 | 1 / 0 |
| Qualifier read differently | 8 / 7 | 13 / 14 | 2 / 3 |
| Deciding records not retrieved or misread | 6 / 6 | 14 / 14 | 1 / 2 |
| Judgement statement judged | 0 / 0 | 0 / 0 | 1 / 1 |
| Reference label doubtful | 0 / 0 | 1 / 1 | 2 / 2 |

### Errors both systems make (same atom, same direction), by cause pair

| Set | Direction | Vote's cause | VeriFact's cause | Atoms |
|---|---|---|---|---|
| first | miss | Earlier value or ended state taken as current | Earlier value or ended state taken as current | 18 |
| first | miss | Addressed statement called Not Addressed | Earlier value or ended state taken as current | 7 |
| first | miss | Documentation or order taken as given | Documentation or order taken as given | 5 |
| first | miss | Different window, summary or threshold | Earlier value or ended state taken as current | 4 |
| first | miss | Different window, summary or threshold | Deciding records not retrieved or misread | 3 |
| first | miss | Qualifier read differently | Qualifier read differently | 3 |
| first | miss | Reference label doubtful | Reference label doubtful | 2 |
| first | miss | Evidence only in the case header | Addressed statement called Not Addressed | 2 |
| first | miss | Qualifier read differently | Addressed statement called Not Addressed | 2 |
| first | miss | Other pairs, one atom each | | 9 |
| first | miss | All shared | | 55 |
| first | false flag | Other pairs, one atom each | | 9 |
| first | false flag | All shared | | 9 |
| header | miss | Earlier value or ended state taken as current | Earlier value or ended state taken as current | 23 |
| header | miss | Documentation or order taken as given | Documentation or order taken as given | 7 |
| header | miss | Addressed statement called Not Addressed | Earlier value or ended state taken as current | 7 |
| header | miss | Qualifier read differently | Qualifier read differently | 4 |
| header | miss | Different window, summary or threshold | Earlier value or ended state taken as current | 4 |
| header | miss | Addressed statement called Not Addressed | Documentation or order taken as given | 3 |
| header | miss | Qualifier read differently | Addressed statement called Not Addressed | 3 |
| header | miss | Different window, summary or threshold | Deciding records not retrieved or misread | 3 |
| header | miss | Reference label doubtful | Reference label doubtful | 2 |
| header | miss | Other pairs, one atom each | | 9 |
| header | miss | All shared | | 65 |
| header | false flag | Documented treatment not accepted as given | Documented treatment not accepted as given | 3 |
| header | false flag | Qualifier read differently | Qualifier read differently | 2 |
| header | false flag | Other pairs, one atom each | | 7 |
| header | false flag | All shared | | 12 |

