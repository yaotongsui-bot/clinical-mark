# eICU test set: spread over repeats

Repeats: `results_eicu_dx`, `results_eicu_dx_r2`, `results_eicu_dx_r3` (repeat 1 first). Same atoms, records, retrieval and judge settings; each repeat shifts the seed of every model request (`CLINICAL_MARK_REPEAT`), so every request is sent again. Judges at temperature 0 (all of the evaluator's) repeat only the serving's own variation; VeriFact's judge samples at temperature 0.1. Frozen reference, 965 atoms, 603 sentences. CIs: 1000 case bootstraps of the 3-repeat mean.

## Agreement per repeat

| Run | Sentence agreement by repeat | Mean (95% CI) | Range | Atom agreement by repeat | Mean | Not Supported found, mean | Atoms with any changed verdict | Sentences with any changed verdict |
|---|---|---|---|---|---|---|---|---|
| ours_vote | 81.8 / 82.6 / 82.6 | 82.3% (79.1 to 85.3) | 0.8 | 79.0 / 80.2 / 80.0 | 79.7% | 67.0% | 51 (5.3%) | 46 (7.6%) |
| ours_pro | 75.1 / 76.0 / 76.6 | 75.9% (72.4 to 79.3) | 1.5 | 74.5 / 76.5 / 76.7 | 75.9% | 66.7% | 125 (13.0%) | 99 (16.4%) |
| vf_pro_cut | 71.0 / 71.3 / 71.0 | 71.1% (67.1 to 75.4) | 0.3 | 70.4 / 70.4 / 70.2 | 70.3% | 20.2% | 48 (5.0%) | 32 (5.3%) |
| ours_llama | 61.7 / 60.9 / 60.2 | 60.9% (56.7 to 65.1) | 1.5 | 63.8 / 63.2 / 63.5 | 63.5% | 62.5% | 36 (3.7%) | 27 (4.5%) |
| ours_llama_alljudge | 46.8 / 47.3 / 46.8 | 46.9% (42.2 to 51.9) | 0.5 | 50.2 / 50.2 / 49.5 | 49.9% | 60.0% | 56 (5.8%) | 34 (5.6%) |
| vf_llama_cut | 56.1 / 56.6 / 56.6 | 56.4% (52.4 to 60.7) | 0.5 | 61.1 / 61.6 / 61.3 | 61.3% | 23.0% | 43 (4.5%) | 29 (4.8%) |
| vf_llama_nocut | 54.4 / 55.2 / 55.9 | 55.2% (51.1 to 59.4) | 1.5 | 59.2 / 59.8 / 59.9 | 59.6% | 26.5% | 49 (5.1%) | 30 (5.0%) |

## Method comparisons over repeats (sentence agreement, A minus B)

| A | B | By repeat | Mean of repeats (95% CI) |
|---|---|---|---|
| ours_pro | vf_pro_cut | +4.1 / +4.6 / +5.6 | +4.8 (+0.3 to +9.2) |
| ours_llama | vf_llama_cut | +5.6 / +4.3 / +3.6 | +4.5 (-1.3 to +10.1) |
| ours_vote | vf_pro_cut | +10.8 / +11.3 / +11.6 | +11.2 (+6.7 to +15.6) |
| ours_llama | ours_llama_alljudge | +14.9 / +13.6 / +13.4 | +14.0 (+9.5 to +18.1) |
| ours_llama_alljudge | vf_llama_cut | -9.3 / -9.3 / -9.8 | -9.5 (-15.9 to -3.7) |
| vf_llama_cut | vf_llama_nocut | +1.7 / +1.3 / +0.7 | +1.2 (-1.5 to +4.0) |
| ours_vote | ours_pro | +6.6 / +6.6 / +6.0 | +6.4 (+4.4 to +8.6) |
| ours_pro | ours_llama | +13.4 / +15.1 / +16.4 | +15.0 (+10.4 to +19.7) |

Runs:

- `ours_vote`: Evaluator, cloud vote (deepseek-v4-pro, minimax-m3.1-flash, glm-5.3)
- `ours_pro`: Evaluator, deepseek-v4-pro judge
- `vf_pro_cut`: VeriFact, deepseek-v4-pro judge, records cut at T
- `ours_llama`: Evaluator, llama3.1:8b judge
- `ours_llama_alljudge`: Evaluator, llama3.1:8b judge, every fact to the judge (no code checks)
- `vf_llama_cut`: VeriFact, llama3.1:8b judge, records cut at T
- `vf_llama_nocut`: VeriFact, llama3.1:8b judge, all records (as published)
