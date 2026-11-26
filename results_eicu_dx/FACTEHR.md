# eICU test set: FactEHR entailment judge as a second baseline

Runs: `results_eicu_dx/` (records with the case header rows; first run of each judge). Reference: the frozen test reference (`reference/fact_gold_eicu/fact_gold_eicu_claude.frozen.csv`, checksum matches): 792 fact atoms in 100 cases. 95% CIs from 1000 bootstrap resamples of cases.

Answer sets scored: gpt-oss-120b, deepseek-v4.1-flash (not qwen2.5-7b: no FactEHR run; every run is scored on the same answer sets, so the numbers differ from SCORES.md).

Every run judges the same fact atoms; only the fact checking differs. All three single-judge runs use deepseek-v4-pro.

- `ours_vote`: ClinicalMark: code checks + cloud vote (deepseek-v4-pro, minimax-m3.1-flash, glm-5.3)
- `ours_pro`: ClinicalMark: code checks + deepseek-v4-pro judge
- `vf_pro_cut`: VeriFact: retrieval (top 50) + deepseek-v4-pro judge, records cut at T
- `fe_pro_cut`: FactEHR: whole record before T + deepseek-v4-pro entailment judge, no retrieval

FactEHR coverage: 792 of 792 reference atoms have a verdict. Prompt size per call: median 17,010 tokens, largest 101,160 (context window set to 131,072, so no record was cut); 16,148,573 prompt tokens over 792 calls.

## Scoring 1: three labels, as in the analysis plan

FactEHR's 0 counts as Not Supported. A sentence is wrong if any of its facts is Not Supported.

| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | Atoms | Atom agreement | Atom AC1 | Atom MCC |
|---|---|---|---|---|---|---|---|---|---|
| ours_vote | 461 | 82.6% (78.7 to 86.2) | 0.702 (0.628 to 0.770) | 72.4% (64.1 to 80.3) | 69.3% (60.4 to 77.2) | 792 | 80.2% (77.0 to 83.4) | 0.754 (0.709 to 0.797) | 0.498 (0.436 to 0.564) |
| ours_pro | 461 | 75.3% (71.2 to 79.7) | 0.560 (0.478 to 0.649) | 68.7% (59.5 to 78.3) | 56.1% (48.5 to 64.1) | 792 | 75.3% (71.8 to 78.8) | 0.690 (0.640 to 0.740) | 0.398 (0.331 to 0.470) |
| vf_pro_cut | 461 | 70.9% (66.7 to 75.4) | 0.560 (0.474 to 0.643) | 24.6% (18.1 to 31.7) | 50.0% (39.0 to 61.8) | 792 | 70.7% (67.0 to 74.5) | 0.641 (0.588 to 0.694) | 0.226 (0.162 to 0.294) |
| fe_pro_cut | 461 | 71.4% (67.2 to 75.6) | 0.530 (0.441 to 0.615) | 42.5% (33.6 to 51.3) | 50.9% (43.2 to 58.8) | 792 | 79.4% (75.8 to 82.9) | 0.757 (0.712 to 0.800) | 0.339 (0.265 to 0.419) |

Sentence agreement by answer set:

| Run | gpt-oss-120b | deepseek-v4.1-flash |
|---|---|---|
| ours_vote | 81.5% | 83.5% |
| ours_pro | 74.0% | 76.2% |
| vf_pro_cut | 68.0% | 73.2% |
| fe_pro_cut | 70.0% | 72.4% |

Paired differences (same items, case bootstrap):

| A | B | Sentence agreement A minus B (95% CI) | Only A right / only B right | Atom agreement A minus B (95% CI) | Only A right / only B right |
|---|---|---|---|---|---|
| ours_vote | fe_pro_cut | +11.3 (+6.7 to +15.8) | 87 / 35 | +0.8 (-2.8 to +4.5) | 91 / 85 |
| ours_pro | fe_pro_cut | +3.9 (-1.1 to +8.9) | 75 / 57 | -4.2 (-7.6 to -0.8) | 81 / 114 |
| vf_pro_cut | fe_pro_cut | -0.4 (-4.4 to +3.2) | 48 / 50 | -8.7 (-12.0 to -5.4) | 46 / 115 |

## Scoring 2: binary for every run (Supported vs not)

Not Supported and Not Addressed merged in the reference and in every run. A sentence is wrong if any of its facts is not Supported.

| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | Atoms | Atom agreement | Atom AC1 | Atom MCC |
|---|---|---|---|---|---|---|---|---|---|
| ours_vote | 461 | 79.0% (75.2 to 82.7) | 0.608 (0.531 to 0.684) | 79.5% (73.1 to 86.0) | 64.5% (57.7 to 71.4) | 792 | 81.8% (78.5 to 84.9) | 0.711 (0.647 to 0.769) | 0.516 (0.446 to 0.585) |
| ours_pro | 461 | 73.1% (68.4 to 78.1) | 0.493 (0.397 to 0.595) | 74.2% (66.0 to 83.1) | 56.9% (50.0 to 64.0) | 792 | 77.0% (73.4 to 80.6) | 0.626 (0.552 to 0.697) | 0.418 (0.343 to 0.500) |
| vf_pro_cut | 461 | 68.3% (63.7 to 73.4) | 0.439 (0.338 to 0.539) | 49.7% (41.4 to 57.9) | 51.7% (43.6 to 60.4) | 792 | 74.1% (70.6 to 77.8) | 0.604 (0.535 to 0.671) | 0.253 (0.170 to 0.342) |
| fe_pro_cut | 461 | 74.2% (69.7 to 78.3) | 0.564 (0.474 to 0.651) | 47.7% (38.9 to 55.8) | 64.3% (56.2 to 72.2) | 792 | 81.8% (78.9 to 84.9) | 0.740 (0.689 to 0.790) | 0.411 (0.336 to 0.489) |

Sentence agreement by answer set:

| Run | gpt-oss-120b | deepseek-v4.1-flash |
|---|---|---|
| ours_vote | 80.0% | 78.2% |
| ours_pro | 74.5% | 72.0% |
| vf_pro_cut | 68.5% | 68.2% |
| fe_pro_cut | 75.5% | 73.2% |

Paired differences (same items, case bootstrap):

| A | B | Sentence agreement A minus B (95% CI) | Only A right / only B right | Atom agreement A minus B (95% CI) | Only A right / only B right |
|---|---|---|---|---|---|
| ours_vote | fe_pro_cut | +4.8 (-0.4 to +10.4) | 82 / 60 | +0.0 (-3.5 to +3.5) | 88 / 88 |
| ours_pro | fe_pro_cut | -1.1 (-6.9 to +4.7) | 72 / 77 | -4.8 (-8.7 to -1.2) | 79 / 117 |
| vf_pro_cut | fe_pro_cut | -5.9 (-10.5 to -1.1) | 41 / 68 | -7.7 (-11.1 to -4.4) | 46 / 107 |

## Atom verdicts by reference label

| Run | Reference Supported: flagged Not Supported | Reference Not Supported: found | Reference Not Addressed: called Supported |
|---|---|---|---|
| ours_vote | 57 of 619 | 97 of 150 | 7 of 23 |
| ours_pro | 98 of 619 | 93 of 150 | 8 of 23 |
| vf_pro_cut | 40 of 619 | 31 of 150 | 7 of 23 |
| fe_pro_cut | 45 of 619 | 55 of 150 | 4 of 23 |

FactEHR false flags (reference Supported, FactEHR Not Supported) by fact kind:

| Fact kind | Reference Supported | FactEHR flagged | VeriFact flagged | ClinicalMark vote flagged |
|---|---|---|---|---|
| judgment | 21 | 2 | 0 | 0 |
| observed | 356 | 25 | 36 | 33 |
| presupposition | 242 | 18 | 4 | 24 |
