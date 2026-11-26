# eICU test set: fact verdicts against the frozen reference

Runs: `results_eicu_dx/`.

Reference: `reference/fact_gold_eicu/fact_gold_eicu_claude.frozen.csv` (checksum matches `FROZEN.sha256`): 965 fact atoms in 100 cases, 603 sentences (182 wrong: at least one Not Supported fact). Written by Claude before any test output was read; the clinician check of 20 cases is still to come.

Primary metric (PAPER_PLAN.md): sentence agreement, where a sentence is wrong if any of its facts is Not Supported. Secondary: atom-level agreement over the three labels, Gwet's AC1, MCC, and sensitivity (found) and PPV for Not Supported. 95% CIs from 1000 bootstrap resamples of cases. `unverifiable` counts as Not Addressed. Each sampled judge was run once (the plan's three repeats are not done).

## All three answer sets

| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | Atoms | Atom agreement | Atom AC1 | Atom MCC | Not Supported found | Not Supported PPV |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ours_vote | 603 | 81.8% (78.1 to 85.1) | 0.684 (0.617 to 0.746) | 70.3% (62.8 to 77.5) | 69.6% (61.9 to 76.7) | 965 | 79.0% (75.8 to 82.0) | 0.735 (0.691 to 0.777) | 0.496 (0.434 to 0.554) | 64.5% (57.3 to 71.6) | 62.3% (54.5 to 70.0) |
| ours_pro | 603 | 75.1% (71.3 to 79.0) | 0.555 (0.480 to 0.635) | 67.6% (58.9 to 75.8) | 57.5% (51.4 to 64.4) | 965 | 74.5% (71.2 to 77.9) | 0.676 (0.629 to 0.724) | 0.408 (0.348 to 0.469) | 62.5% (54.5 to 70.9) | 49.4% (43.5 to 55.7) |
| vf_pro_cut | 603 | 71.0% (66.9 to 75.3) | 0.560 (0.478 to 0.640) | 24.2% (17.8 to 31.3) | 54.3% (43.6 to 65.6) | 965 | 70.4% (66.8 to 73.9) | 0.634 (0.583 to 0.683) | 0.241 (0.175 to 0.307) | 20.5% (14.8 to 27.3) | 47.7% (36.7 to 59.7) |
| ours_llama | 603 | 61.7% (57.3 to 66.3) | 0.259 (0.169 to 0.352) | 72.0% (63.4 to 79.3) | 42.1% (36.2 to 47.9) | 965 | 63.8% (60.1 to 67.5) | 0.530 (0.476 to 0.582) | 0.264 (0.198 to 0.331) | 63.5% (55.3 to 70.9) | 33.6% (28.1 to 39.4) |
| ours_llama_alljudge | 603 | 46.8% (42.0 to 51.7) | -0.063 (-0.156 to 0.039) | 71.4% (64.1 to 78.5) | 32.6% (27.4 to 38.0) | 965 | 50.2% (46.2 to 54.2) | 0.340 (0.285 to 0.398) | 0.094 (0.029 to 0.160) | 61.5% (53.8 to 69.0) | 23.6% (19.3 to 27.9) |
| vf_llama_cut | 603 | 56.1% (52.0 to 60.5) | 0.229 (0.138 to 0.327) | 30.8% (24.7 to 37.2) | 28.7% (22.4 to 35.1) | 965 | 61.1% (57.4 to 65.3) | 0.515 (0.460 to 0.574) | 0.027 (-0.037 to 0.088) | 22.0% (16.5 to 28.1) | 18.3% (13.3 to 23.4) |
| vf_llama_nocut | 603 | 54.4% (50.2 to 58.8) | 0.192 (0.095 to 0.298) | 30.8% (23.5 to 38.1) | 27.3% (21.3 to 33.3) | 965 | 59.2% (55.3 to 63.2) | 0.484 (0.428 to 0.542) | 0.028 (-0.032 to 0.089) | 24.5% (18.9 to 30.7) | 18.8% (14.4 to 23.1) |

Coverage: every run has a verdict for every atom.

## Answers from gpt-oss-120b

| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | Atoms | Atom agreement | Atom AC1 | Atom MCC | Not Supported found | Not Supported PPV |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ours_vote | 200 | 81.5% (75.8 to 86.9) | 0.656 (0.549 to 0.759) | 71.1% (59.7 to 81.5) | 78.3% (67.1 to 87.7) | 262 | 74.8% (69.3 to 80.2) | 0.655 (0.575 to 0.731) | 0.536 (0.438 to 0.631) | 67.5% (56.9 to 78.4) | 75.0% (62.7 to 86.0) |
| ours_pro | 200 | 74.0% (67.6 to 80.6) | 0.506 (0.380 to 0.637) | 67.1% (55.7 to 78.5) | 65.4% (54.3 to 76.6) | 262 | 69.1% (63.1 to 75.3) | 0.578 (0.492 to 0.665) | 0.423 (0.318 to 0.536) | 62.5% (50.0 to 74.2) | 60.2% (49.3 to 71.8) |
| vf_pro_cut | 200 | 68.0% (62.0 to 74.4) | 0.484 (0.358 to 0.609) | 25.0% (15.4 to 34.9) | 73.1% (58.6 to 87.5) | 262 | 66.4% (61.1 to 71.9) | 0.556 (0.474 to 0.638) | 0.354 (0.277 to 0.433) | 25.0% (15.6 to 34.5) | 71.4% (57.1 to 86.2) |
| ours_llama | 200 | 62.0% (55.3 to 68.1) | 0.245 (0.110 to 0.376) | 71.1% (60.0 to 80.0) | 50.0% (40.4 to 59.0) | 262 | 58.4% (52.2 to 64.2) | 0.430 (0.340 to 0.517) | 0.257 (0.158 to 0.352) | 65.0% (53.8 to 75.0) | 42.6% (34.2 to 50.5) |
| ours_llama_alljudge | 200 | 50.5% (43.9 to 57.7) | 0.014 (-0.117 to 0.163) | 75.0% (65.7 to 83.5) | 41.6% (33.3 to 50.0) | 262 | 48.1% (42.2 to 54.1) | 0.291 (0.210 to 0.379) | 0.116 (0.012 to 0.215) | 68.8% (58.2 to 77.6) | 33.7% (26.2 to 41.9) |
| vf_llama_cut | 200 | 55.5% (48.5 to 62.4) | 0.210 (0.058 to 0.359) | 26.3% (16.7 to 37.0) | 37.7% (26.2 to 49.2) | 262 | 55.3% (49.2 to 61.8) | 0.411 (0.323 to 0.506) | 0.081 (-0.041 to 0.202) | 23.8% (14.5 to 34.4) | 28.8% (17.7 to 41.5) |
| vf_llama_nocut | 200 | 54.0% (46.7 to 61.6) | 0.147 (-0.007 to 0.319) | 34.2% (23.1 to 44.9) | 38.2% (26.9 to 49.2) | 262 | 53.1% (47.2 to 59.8) | 0.371 (0.284 to 0.468) | 0.077 (-0.038 to 0.197) | 30.0% (19.8 to 41.1) | 29.3% (19.4 to 39.4) |

## Answers from deepseek-v4.1-flash

| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | Atoms | Atom agreement | Atom AC1 | Atom MCC | Not Supported found | Not Supported PPV |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ours_vote | 261 | 83.5% (78.8 to 88.1) | 0.738 (0.652 to 0.817) | 74.1% (61.2 to 85.7) | 60.6% (48.6 to 71.2) | 530 | 82.8% (79.0 to 86.2) | 0.799 (0.751 to 0.842) | 0.422 (0.323 to 0.515) | 61.4% (50.0 to 73.5) | 50.0% (38.7 to 60.8) |
| ours_pro | 261 | 76.2% (70.7 to 81.8) | 0.604 (0.508 to 0.712) | 70.7% (57.4 to 81.9) | 47.7% (36.1 to 58.7) | 530 | 78.3% (74.2 to 82.0) | 0.742 (0.688 to 0.791) | 0.342 (0.250 to 0.432) | 61.4% (50.0 to 71.9) | 37.4% (28.7 to 46.8) |
| vf_pro_cut | 261 | 73.2% (68.0 to 78.5) | 0.614 (0.521 to 0.702) | 24.1% (12.1 to 37.3) | 35.0% (18.4 to 52.6) | 530 | 72.8% (68.6 to 76.9) | 0.680 (0.623 to 0.733) | 0.116 (0.039 to 0.200) | 15.7% (6.9 to 26.6) | 25.6% (12.8 to 41.5) |
| ours_llama | 261 | 64.0% (57.6 to 70.8) | 0.337 (0.203 to 0.479) | 77.6% (64.8 to 88.5) | 35.7% (27.3 to 45.3) | 530 | 69.2% (64.5 to 73.8) | 0.624 (0.560 to 0.684) | 0.223 (0.133 to 0.316) | 60.0% (48.5 to 71.6) | 25.1% (18.6 to 32.9) |
| ours_llama_alljudge | 261 | 44.8% (38.4 to 51.0) | -0.088 (-0.216 to 0.048) | 74.1% (60.7 to 85.5) | 25.0% (18.7 to 31.9) | 530 | 53.2% (48.3 to 58.4) | 0.405 (0.200 to 0.476) | 0.057 (-0.038 to 0.141) | 55.7% (42.3 to 67.2) | 15.4% (10.4 to 20.2) |
| vf_llama_cut | 261 | 57.5% (51.2 to 63.6) | 0.243 (0.111 to 0.378) | 50.0% (37.5 to 63.3) | 26.1% (18.5 to 35.3) | 530 | 66.0% (61.6 to 70.9) | 0.592 (0.531 to 0.657) | 0.018 (-0.053 to 0.096) | 25.7% (16.7 to 35.4) | 12.9% (8.2 to 18.5) |
| vf_llama_nocut | 261 | 54.8% (49.0 to 60.6) | 0.202 (0.077 to 0.328) | 41.4% (29.8 to 53.4) | 22.2% (14.8 to 31.0) | 530 | 63.8% (59.2 to 68.7) | 0.559 (0.495 to 0.627) | 0.022 (-0.049 to 0.100) | 28.6% (18.3 to 39.7) | 13.6% (8.6 to 19.0) |

## Answers from qwen2.5-7b

| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | Atoms | Atom agreement | Atom AC1 | Atom MCC | Not Supported found | Not Supported PPV |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ours_vote | 142 | 78.9% (71.3 to 85.8) | 0.624 (0.484 to 0.758) | 64.6% (50.0 to 77.8) | 70.5% (55.0 to 84.1) | 173 | 73.4% (67.1 to 79.3) | 0.644 (0.556 to 0.734) | 0.474 (0.360 to 0.589) | 64.0% (50.0 to 76.7) | 65.3% (49.0 to 79.6) |
| ours_pro | 142 | 74.6% (67.2 to 81.8) | 0.537 (0.391 to 0.678) | 64.6% (49.1 to 77.8) | 62.0% (47.4 to 75.5) | 173 | 71.1% (64.2 to 77.2) | 0.613 (0.515 to 0.702) | 0.431 (0.311 to 0.543) | 64.0% (50.0 to 77.2) | 58.2% (42.9 to 72.7) |
| vf_pro_cut | 142 | 71.1% (63.8 to 79.3) | 0.559 (0.417 to 0.701) | 22.9% (11.3 to 36.4) | 73.3% (46.2 to 94.7) | 173 | 68.8% (62.0 to 75.9) | 0.603 (0.511 to 0.704) | 0.329 (0.192 to 0.466) | 20.0% (9.7 to 33.9) | 66.7% (38.5 to 90.5) |
| ours_llama | 142 | 57.0% (49.3 to 65.5) | 0.153 (0.001 to 0.329) | 66.7% (51.0 to 80.0) | 41.6% (29.9 to 52.7) | 173 | 55.5% (47.2 to 63.3) | 0.391 (0.269 to 0.507) | 0.225 (0.097 to 0.348) | 66.0% (50.0 to 79.3) | 37.1% (26.3 to 48.3) |
| ours_llama_alljudge | 142 | 45.1% (36.9 to 53.4) | -0.098 (-0.258 to 0.073) | 62.5% (48.8 to 75.6) | 33.3% (23.3 to 42.7) | 173 | 43.9% (36.3 to 51.9) | 0.239 (0.127 to 0.354) | 0.015 (-0.118 to 0.142) | 58.0% (43.7 to 70.6) | 27.9% (18.6 to 37.2) |
| vf_llama_cut | 142 | 54.2% (46.8 to 62.6) | 0.235 (0.057 to 0.421) | 14.6% (4.8 to 24.5) | 22.6% (7.1 to 40.6) | 173 | 54.9% (48.0 to 62.6) | 0.424 (0.323 to 0.537) | -0.024 (-0.149 to 0.114) | 14.0% (4.4 to 23.4) | 19.4% (6.1 to 35.0) |
| vf_llama_nocut | 142 | 54.2% (46.0 to 62.7) | 0.243 (0.060 to 0.419) | 12.5% (4.3 to 21.2) | 20.7% (6.7 to 38.5) | 173 | 54.3% (47.7 to 61.7) | 0.417 (0.312 to 0.524) | -0.039 (-0.155 to 0.084) | 10.0% (2.5 to 17.9) | 16.1% (3.7 to 31.0) |

## Sensitivity: without the 54 atoms whose reference evidence is the admission diagnosis or unit type (case header, not in the systems' records)

| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | Atoms | Atom agreement | Atom AC1 | Atom MCC | Not Supported found | Not Supported PPV |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ours_vote | 588 | 82.0% (78.2 to 85.2) | 0.689 (0.620 to 0.753) | 70.9% (63.1 to 77.8) | 69.3% (61.2 to 76.7) | 911 | 78.4% (75.0 to 81.6) | 0.726 (0.679 to 0.770) | 0.493 (0.430 to 0.555) | 65.1% (57.7 to 72.7) | 61.9% (53.6 to 69.9) |
| ours_pro | 588 | 75.7% (71.8 to 79.8) | 0.565 (0.493 to 0.646) | 69.1% (60.2 to 77.4) | 57.6% (51.2 to 64.7) | 911 | 74.0% (70.4 to 77.4) | 0.668 (0.616 to 0.716) | 0.412 (0.349 to 0.475) | 64.1% (55.6 to 72.4) | 49.4% (43.5 to 55.9) |
| vf_pro_cut | 588 | 71.3% (67.1 to 75.7) | 0.565 (0.481 to 0.649) | 24.6% (18.2 to 31.7) | 53.8% (43.0 to 65.1) | 911 | 69.6% (65.7 to 73.5) | 0.622 (0.567 to 0.676) | 0.238 (0.174 to 0.306) | 20.8% (15.1 to 27.8) | 47.1% (36.1 to 59.4) |
| ours_llama | 588 | 62.6% (57.9 to 67.1) | 0.286 (0.184 to 0.379) | 68.6% (60.1 to 76.5) | 42.1% (35.5 to 48.6) | 911 | 65.0% (61.0 to 68.7) | 0.545 (0.489 to 0.598) | 0.276 (0.207 to 0.345) | 62.5% (54.2 to 70.4) | 35.0% (29.1 to 41.1) |
| ours_llama_alljudge | 588 | 46.9% (42.2 to 52.2) | -0.058 (-0.153 to 0.048) | 69.1% (61.2 to 76.7) | 31.9% (26.5 to 37.6) | 911 | 50.5% (46.4 to 54.7) | 0.345 (0.287 to 0.404) | 0.094 (0.026 to 0.161) | 60.4% (52.7 to 67.9) | 23.9% (19.2 to 28.5) |
| vf_llama_cut | 588 | 55.4% (51.3 to 59.9) | 0.222 (0.127 to 0.322) | 29.1% (22.7 to 35.8) | 27.0% (20.5 to 33.7) | 911 | 59.6% (55.8 to 64.0) | 0.493 (0.437 to 0.555) | 0.005 (-0.055 to 0.068) | 20.3% (15.0 to 26.3) | 16.7% (12.2 to 21.4) |
| vf_llama_nocut | 588 | 54.4% (49.9 to 59.2) | 0.199 (0.094 to 0.304) | 29.1% (21.8 to 36.5) | 26.2% (19.8 to 32.8) | 911 | 58.1% (54.0 to 62.5) | 0.468 (0.407 to 0.532) | 0.014 (-0.048 to 0.078) | 23.4% (17.8 to 29.5) | 18.1% (13.8 to 22.5) |

## Sensitivity: also without the 21 atoms decided by guideline rule 7 (intermittent drugs documented in the treatment table count as given)

| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | Atoms | Atom agreement | Atom AC1 | Atom MCC | Not Supported found | Not Supported PPV |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ours_vote | 576 | 83.2% (79.5 to 86.6) | 0.710 (0.640 to 0.775) | 70.9% (63.1 to 77.8) | 72.9% (65.2 to 80.9) | 890 | 80.0% (76.6 to 83.2) | 0.747 (0.701 to 0.792) | 0.524 (0.461 to 0.581) | 65.1% (57.7 to 72.7) | 66.5% (58.6 to 74.4) |
| ours_pro | 576 | 77.6% (73.9 to 81.4) | 0.602 (0.530 to 0.677) | 69.1% (60.2 to 77.4) | 61.7% (55.4 to 68.8) | 890 | 75.6% (72.2 to 79.0) | 0.689 (0.642 to 0.736) | 0.440 (0.378 to 0.502) | 64.1% (55.6 to 72.4) | 53.5% (47.5 to 59.9) |
| vf_pro_cut | 576 | 70.8% (66.6 to 75.4) | 0.557 (0.473 to 0.641) | 24.0% (17.8 to 31.2) | 54.5% (43.4 to 66.7) | 890 | 69.4% (65.4 to 73.4) | 0.620 (0.562 to 0.675) | 0.242 (0.177 to 0.311) | 20.8% (15.1 to 27.8) | 48.8% (37.9 to 61.0) |
| ours_llama | 576 | 63.2% (58.5 to 67.7) | 0.296 (0.196 to 0.392) | 68.6% (60.1 to 76.5) | 43.3% (36.7 to 50.0) | 890 | 66.3% (62.4 to 70.0) | 0.563 (0.506 to 0.616) | 0.294 (0.224 to 0.362) | 62.5% (54.2 to 70.4) | 36.6% (30.3 to 42.8) |
| ours_llama_alljudge | 576 | 47.2% (42.4 to 52.5) | -0.053 (-0.150 to 0.057) | 69.1% (61.2 to 76.7) | 32.6% (27.2 to 38.2) | 890 | 51.0% (46.8 to 55.2) | 0.351 (0.291 to 0.411) | 0.100 (0.033 to 0.168) | 60.4% (52.7 to 67.9) | 24.6% (20.0 to 29.5) |
| vf_llama_cut | 576 | 54.9% (50.9 to 59.2) | 0.207 (0.110 to 0.310) | 29.1% (22.7 to 35.8) | 27.3% (20.7 to 34.2) | 890 | 58.9% (55.0 to 63.3) | 0.483 (0.425 to 0.547) | 0.001 (-0.060 to 0.063) | 20.3% (15.0 to 26.3) | 16.9% (12.3 to 21.6) |
| vf_llama_nocut | 576 | 53.8% (49.3 to 58.6) | 0.183 (0.080 to 0.288) | 29.1% (21.8 to 36.5) | 26.4% (20.2 to 33.0) | 890 | 57.3% (53.3 to 61.9) | 0.457 (0.395 to 0.524) | 0.009 (-0.054 to 0.075) | 23.4% (17.8 to 29.5) | 18.3% (13.8 to 22.5) |

## Paired differences, all answer sets (same items, case bootstrap)

| A | B | Sentence agreement A minus B (95% CI) | Only A right / only B right | Atom agreement A minus B (95% CI) | Only A right / only B right |
|---|---|---|---|---|---|
| ours_pro | vf_pro_cut | +4.1 (-0.0 to +8.4) | 105 / 80 | +4.1 (+0.4 to +7.8) | 162 / 122 |
| ours_llama | vf_llama_cut | +5.6 (-0.7 to +11.6) | 158 / 124 | +2.7 (-2.6 to +7.8) | 225 / 199 |
| ours_vote | vf_pro_cut | +10.8 (+6.1 to +14.9) | 114 / 49 | +8.6 (+4.8 to +12.5) | 169 / 86 |
| ours_llama | ours_llama_alljudge | +14.9 (+10.6 to +19.4) | 113 / 23 | +13.7 (+10.2 to +17.3) | 179 / 47 |
| ours_llama_alljudge | vf_llama_cut | -9.3 (-15.5 to -3.4) | 107 / 163 | -11.0 (-15.9 to -6.6) | 140 / 246 |
| vf_llama_cut | vf_llama_nocut | +1.7 (-1.4 to +4.6) | 48 / 38 | +2.0 (-0.3 to +4.3) | 77 / 58 |
| ours_vote | ours_pro | +6.6 (+4.1 to +9.2) | 52 / 12 | +4.5 (+2.9 to +6.1) | 56 / 13 |
| ours_pro | ours_llama | +13.4 (+8.6 to +18.7) | 125 / 44 | +10.7 (+6.8 to +14.9) | 157 / 54 |

Runs:

- `ours_vote`: Evaluator, cloud vote (deepseek-v4-pro, minimax-m3.1-flash, glm-5.3)
- `ours_pro`: Evaluator, deepseek-v4-pro judge
- `vf_pro_cut`: VeriFact, deepseek-v4-pro judge, records cut at T
- `ours_llama`: Evaluator, llama3.1:8b judge
- `ours_llama_alljudge`: Evaluator, llama3.1:8b judge, every fact to the judge (no code checks)
- `vf_llama_cut`: VeriFact, llama3.1:8b judge, records cut at T
- `vf_llama_nocut`: VeriFact, llama3.1:8b judge, all records (as published)
