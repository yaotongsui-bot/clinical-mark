# Fact verdicts on the 85 cases against the reference

Reference: `reference/fact_gold/fact_gold_claude.csv` (486 fact atoms). Metrics as in VeriFact's irr_metrics; 95% CIs from 1000 bootstrap resamples of atoms.

## vf_hybrid_nocut

- Scored 486 of 486 reference atoms; missing in the run: 0; `unverifiable` counted as not addressed: 0.

| Percent agreement | Gwet's AC1 | MCC | Binarized agreement | Binarized AC1 |
|---|---|---|---|---|
| 59.3% (54.7 to 64.0) | 0.490 (0.428 to 0.556) | -0.009 (-0.090 to 0.084) | 59.7% (55.3 to 64.4) | 0.333 (0.237 to 0.429) |

| Reference \ run | Supported | Not Supported | Not Addressed | Sensitivity | PPV |
|---|---|---|---|---|---|
| Supported | 256 | 85 | 12 | 72.5% | 72.1% |
| Not Supported | 98 | 32 | 1 | 24.4% | 27.1% |
| Not Addressed | 1 | 1 | 0 | 0.0% | 0.0% |

## vf_hybrid_cut

- Scored 486 of 486 reference atoms; missing in the run: 0; `unverifiable` counted as not addressed: 0.

| Percent agreement | Gwet's AC1 | MCC | Binarized agreement | Binarized AC1 |
|---|---|---|---|---|
| 62.3% (57.8 to 66.7) | 0.537 (0.471 to 0.598) | 0.000 (-0.085 to 0.085) | 62.8% (58.2 to 67.3) | 0.412 (0.317 to 0.501) |

| Reference \ run | Supported | Not Supported | Not Addressed | Sensitivity | PPV |
|---|---|---|---|---|---|
| Supported | 278 | 64 | 11 | 78.8% | 72.4% |
| Not Supported | 106 | 24 | 1 | 18.3% | 27.0% |
| Not Addressed | 0 | 1 | 1 | 50.0% | 7.7% |

## vf_rerank_cut

- Scored 486 of 486 reference atoms; missing in the run: 0; `unverifiable` counted as not addressed: 0.

| Percent agreement | Gwet's AC1 | MCC | Binarized agreement | Binarized AC1 |
|---|---|---|---|---|
| 62.8% (58.2 to 67.5) | 0.541 (0.479 to 0.605) | 0.022 (-0.071 to 0.115) | 63.2% (58.6 to 67.9) | 0.413 (0.321 to 0.504) |

| Reference \ run | Supported | Not Supported | Not Addressed | Sensitivity | PPV |
|---|---|---|---|---|---|
| Supported | 276 | 69 | 8 | 78.2% | 73.0% |
| Not Supported | 102 | 28 | 1 | 21.4% | 28.6% |
| Not Addressed | 0 | 1 | 1 | 50.0% | 10.0% |

## vf_rules_cut

- Scored 486 of 486 reference atoms; missing in the run: 0; `unverifiable` counted as not addressed: 0.

| Percent agreement | Gwet's AC1 | MCC | Binarized agreement | Binarized AC1 |
|---|---|---|---|---|
| 58.2% (53.9 to 62.8) | 0.454 (0.237 to 0.514) | 0.167 (0.079 to 0.252) | 58.6% (54.1 to 63.2) | 0.221 (0.129 to 0.319) |

| Reference \ run | Supported | Not Supported | Not Addressed | Sensitivity | PPV |
|---|---|---|---|---|---|
| Supported | 203 | 149 | 1 | 57.5% | 79.9% |
| Not Supported | 51 | 80 | 0 | 61.1% | 34.6% |
| Not Addressed | 0 | 2 | 0 | 0.0% | 0.0% |

## results_ours85_llama8b_alljudge

- Scored 486 of 486 reference atoms; missing in the run: 0; `unverifiable` counted as not addressed: 0.

| Percent agreement | Gwet's AC1 | MCC | Binarized agreement | Binarized AC1 |
|---|---|---|---|---|
| 68.1% (64.2 to 72.2) | 0.600 (0.545 to 0.659) | 0.227 (0.141 to 0.308) | 70.2% (66.3 to 74.3) | 0.512 (0.435 to 0.592) |

| Reference \ run | Supported | Not Supported | Not Addressed | Sensitivity | PPV |
|---|---|---|---|---|---|
| Supported | 285 | 41 | 27 | 80.7% | 78.7% |
| Not Supported | 77 | 45 | 9 | 34.4% | 51.7% |
| Not Addressed | 0 | 1 | 1 | 50.0% | 2.7% |

## results_ours85_llama8b

- Scored 486 of 486 reference atoms; missing in the run: 0; `unverifiable` counted as not addressed: 13.

| Percent agreement | Gwet's AC1 | MCC | Binarized agreement | Binarized AC1 |
|---|---|---|---|---|
| 78.6% (74.7 to 82.1) | 0.730 (0.679 to 0.777) | 0.491 (0.406 to 0.564) | 80.5% (76.7 to 83.8) | 0.674 (0.608 to 0.737) |

| Reference \ run | Supported | Not Supported | Not Addressed | Sensitivity | PPV |
|---|---|---|---|---|---|
| Supported | 304 | 31 | 18 | 86.1% | 86.9% |
| Not Supported | 46 | 76 | 9 | 58.0% | 71.0% |
| Not Addressed | 0 | 0 | 2 | 100.0% | 6.9% |

## vf_pro_cut

- Scored 486 of 486 reference atoms; missing in the run: 0; `unverifiable` counted as not addressed: 0.

| Percent agreement | Gwet's AC1 | MCC | Binarized agreement | Binarized AC1 |
|---|---|---|---|---|
| 68.3% (64.2 to 72.8) | 0.622 (0.565 to 0.680) | 0.078 (-0.005 to 0.159) | 69.1% (65.0 to 73.3) | 0.550 (0.473 to 0.627) |

| Reference \ run | Supported | Not Supported | Not Addressed | Sensitivity | PPV |
|---|---|---|---|---|---|
| Supported | 316 | 19 | 18 | 89.5% | 73.7% |
| Not Supported | 112 | 15 | 4 | 11.5% | 44.1% |
| Not Addressed | 1 | 0 | 1 | 50.0% | 4.3% |

## vf_pro_rerank_cut

- Scored 486 of 486 reference atoms; missing in the run: 0; `unverifiable` counted as not addressed: 0.

| Percent agreement | Gwet's AC1 | MCC | Binarized agreement | Binarized AC1 |
|---|---|---|---|---|
| 66.3% (62.1 to 70.8) | 0.592 (0.533 to 0.653) | 0.062 (-0.014 to 0.141) | 68.3% (64.2 to 72.6) | 0.524 (0.447 to 0.607) |

| Reference \ run | Supported | Not Supported | Not Addressed | Sensitivity | PPV |
|---|---|---|---|---|---|
| Supported | 306 | 30 | 17 | 86.7% | 74.1% |
| Not Supported | 106 | 15 | 10 | 11.5% | 33.3% |
| Not Addressed | 1 | 0 | 1 | 50.0% | 3.6% |

## results_final_claude_split

- Scored 486 of 486 reference atoms; missing in the run: 0; `unverifiable` counted as not addressed: 13.

| Percent agreement | Gwet's AC1 | MCC | Binarized agreement | Binarized AC1 |
|---|---|---|---|---|
| 88.1% (85.2 to 90.9) | 0.850 (0.812 to 0.886) | 0.719 (0.653 to 0.781) | 90.9% (88.5 to 93.2) | 0.850 (0.806 to 0.891) |

| Reference \ run | Supported | Not Supported | Not Addressed | Sensitivity | PPV |
|---|---|---|---|---|---|
| Supported | 331 | 7 | 15 | 93.8% | 93.8% |
| Not Supported | 22 | 95 | 14 | 72.5% | 93.1% |
| Not Addressed | 0 | 0 | 2 | 100.0% | 6.5% |

## Paired differences in percent agreement (same atoms)

| Run A | Run B | A minus B (95% CI) | Only A right | Only B right |
|---|---|---|---|---|
| vf_hybrid_nocut | vf_hybrid_cut | -3.1 (-6.4 to +0.6) | 31 | 46 |
| vf_hybrid_nocut | vf_rerank_cut | -3.5 (-6.8 to +0.0) | 28 | 45 |
| vf_hybrid_nocut | vf_rules_cut | +1.0 (-4.5 to +7.4) | 104 | 99 |
| vf_hybrid_nocut | results_ours85_llama8b_alljudge | -8.8 (-13.6 to -3.7) | 60 | 103 |
| vf_hybrid_nocut | results_ours85_llama8b | -19.3 (-24.3 to -14.0) | 45 | 139 |
| vf_hybrid_nocut | vf_pro_cut | -9.1 (-13.2 to -4.3) | 41 | 85 |
| vf_hybrid_nocut | vf_pro_rerank_cut | -7.0 (-11.3 to -2.7) | 45 | 79 |
| vf_hybrid_nocut | results_final_claude_split | -28.8 (-33.8 to -23.5) | 24 | 164 |
| vf_hybrid_cut | vf_rerank_cut | -0.4 (-3.3 to +2.3) | 22 | 24 |
| vf_hybrid_cut | vf_rules_cut | +4.1 (-1.9 to +10.1) | 103 | 83 |
| vf_hybrid_cut | results_ours85_llama8b_alljudge | -5.8 (-10.7 to -0.8) | 54 | 82 |
| vf_hybrid_cut | results_ours85_llama8b | -16.3 (-21.0 to -11.5) | 36 | 115 |
| vf_hybrid_cut | vf_pro_cut | -6.0 (-9.9 to -1.9) | 37 | 66 |
| vf_hybrid_cut | vf_pro_rerank_cut | -3.9 (-8.2 to +0.0) | 44 | 63 |
| vf_hybrid_cut | results_final_claude_split | -25.7 (-30.5 to -20.8) | 21 | 146 |
| vf_rerank_cut | vf_rules_cut | +4.5 (-1.2 to +10.9) | 106 | 84 |
| vf_rerank_cut | results_ours85_llama8b_alljudge | -5.3 (-10.1 to -0.4) | 58 | 84 |
| vf_rerank_cut | results_ours85_llama8b | -15.8 (-20.6 to -10.5) | 41 | 118 |
| vf_rerank_cut | vf_pro_cut | -5.6 (-9.9 to -1.2) | 39 | 66 |
| vf_rerank_cut | vf_pro_rerank_cut | -3.5 (-7.8 to +0.6) | 44 | 61 |
| vf_rerank_cut | results_final_claude_split | -25.3 (-29.8 to -20.2) | 21 | 144 |
| vf_rules_cut | results_ours85_llama8b_alljudge | -9.9 (-15.4 to -4.3) | 66 | 114 |
| vf_rules_cut | results_ours85_llama8b | -20.4 (-24.7 to -15.2) | 35 | 134 |
| vf_rules_cut | vf_pro_cut | -10.1 (-16.5 to -3.9) | 89 | 138 |
| vf_rules_cut | vf_pro_rerank_cut | -8.0 (-14.4 to -2.1) | 94 | 133 |
| vf_rules_cut | results_final_claude_split | -29.8 (-34.6 to -24.7) | 25 | 170 |
| results_ours85_llama8b_alljudge | results_ours85_llama8b | -10.5 (-13.8 to -6.8) | 16 | 67 |
| results_ours85_llama8b_alljudge | vf_pro_cut | -0.2 (-4.5 to +4.3) | 60 | 61 |
| results_ours85_llama8b_alljudge | vf_pro_rerank_cut | +1.9 (-2.3 to +6.0) | 64 | 55 |
| results_ours85_llama8b_alljudge | results_final_claude_split | -20.0 (-24.3 to -15.6) | 20 | 117 |
| results_ours85_llama8b | vf_pro_cut | +10.3 (+5.3 to +14.6) | 96 | 46 |
| results_ours85_llama8b | vf_pro_rerank_cut | +12.3 (+7.4 to +16.9) | 104 | 44 |
| results_ours85_llama8b | results_final_claude_split | -9.5 (-12.1 to -6.8) | 5 | 51 |
| vf_pro_cut | vf_pro_rerank_cut | +2.1 (+0.0 to +3.9) | 18 | 8 |
| vf_pro_cut | results_final_claude_split | -19.8 (-24.1 to -15.2) | 20 | 116 |
| vf_pro_rerank_cut | results_final_claude_split | -21.8 (-26.1 to -17.1) | 21 | 127 |
