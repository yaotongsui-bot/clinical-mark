# eICU test set: fact verdicts against the frozen reference

Runs: `results_eicu/`.

Reference: `reference/fact_gold_eicu/fact_gold_eicu_claude.frozen.csv` (checksum matches `FROZEN.sha256`): 965 fact atoms in 100 cases, 603 sentences (182 wrong: at least one Not Supported fact). Written by Claude before any test output was read; the clinician check of 20 cases is still to come.

Primary metric (PAPER_PLAN.md): sentence agreement, where a sentence is wrong if any of its facts is Not Supported. Secondary: atom-level agreement over the three labels, Gwet's AC1, MCC, and sensitivity (found) and PPV for Not Supported. 95% CIs from 1000 bootstrap resamples of cases. `unverifiable` counts as Not Addressed. Each sampled judge was run once (the plan's three repeats are not done).

## All three answer sets

| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | Atoms | Atom agreement | Atom AC1 | Atom MCC | Not Supported found | Not Supported PPV |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ours_vote | 603 | 81.9% (78.3 to 85.6) | 0.682 (0.612 to 0.753) | 74.2% (66.3 to 81.3) | 68.5% (61.0 to 75.3) | 965 | 76.9% (73.4 to 80.5) | 0.704 (0.656 to 0.754) | 0.489 (0.427 to 0.551) | 69.0% (61.0 to 76.5) | 60.8% (52.6 to 68.6) |
| ours_pro | 603 | 69.0% (65.4 to 73.0) | 0.407 (0.332 to 0.492) | 79.1% (72.2 to 85.5) | 49.1% (43.8 to 54.5) | 965 | 67.4% (63.8 to 70.9) | 0.573 (0.523 to 0.626) | 0.359 (0.309 to 0.408) | 74.5% (67.6 to 81.1) | 39.5% (34.5 to 44.6) |
| vf_pro_cut | 603 | 71.1% (67.1 to 75.6) | 0.566 (0.487 to 0.648) | 22.5% (16.1 to 29.6) | 55.4% (44.2 to 68.3) | 965 | 67.6% (63.6 to 71.4) | 0.595 (0.539 to 0.650) | 0.206 (0.144 to 0.274) | 18.5% (12.9 to 25.0) | 47.4% (36.8 to 60.3) |
| ours_llama | 603 | 60.9% (56.9 to 65.1) | 0.239 (0.155 to 0.328) | 73.1% (65.3 to 79.8) | 41.6% (36.1 to 47.0) | 965 | 62.4% (58.6 to 66.0) | 0.509 (0.455 to 0.560) | 0.249 (0.183 to 0.317) | 63.0% (54.8 to 70.5) | 32.2% (27.2 to 37.2) |
| ours_llama_alljudge | 603 | 48.9% (44.2 to 53.9) | -0.019 (-0.114 to 0.083) | 73.1% (65.8 to 80.4) | 33.9% (28.4 to 39.1) | 965 | 50.8% (46.8 to 54.9) | 0.348 (0.294 to 0.407) | 0.103 (0.033 to 0.175) | 61.5% (53.5 to 69.1) | 24.0% (19.5 to 28.3) |
| vf_llama_cut | 603 | 53.6% (49.3 to 57.9) | 0.154 (0.061 to 0.260) | 36.8% (29.6 to 43.9) | 28.9% (22.4 to 34.8) | 965 | 57.3% (53.2 to 61.6) | 0.458 (0.396 to 0.520) | 0.004 (-0.059 to 0.070) | 26.5% (19.9 to 33.6) | 18.2% (13.4 to 22.7) |
| vf_llama_nocut | 603 | 53.2% (49.0 to 57.6) | 0.145 (0.048 to 0.245) | 37.4% (29.9 to 44.3) | 28.8% (22.7 to 34.8) | 965 | 56.5% (52.4 to 60.9) | 0.442 (0.381 to 0.506) | 0.024 (-0.040 to 0.087) | 28.0% (22.2 to 34.5) | 19.1% (14.6 to 23.3) |

Coverage: every run has a verdict for every atom.

## Answers from gpt-oss-120b

| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | Atoms | Atom agreement | Atom AC1 | Atom MCC | Not Supported found | Not Supported PPV |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ours_vote | 200 | 81.0% (74.5 to 87.0) | 0.646 (0.523 to 0.764) | 71.1% (59.4 to 81.6) | 77.1% (65.8 to 86.8) | 262 | 71.0% (65.2 to 76.6) | 0.597 (0.514 to 0.678) | 0.494 (0.401 to 0.584) | 67.5% (56.4 to 77.9) | 72.0% (59.5 to 82.7) |
| ours_pro | 200 | 67.5% (60.5 to 74.6) | 0.357 (0.214 to 0.502) | 75.0% (64.1 to 85.0) | 55.3% (45.6 to 64.6) | 262 | 61.8% (55.5 to 68.2) | 0.474 (0.381 to 0.566) | 0.327 (0.226 to 0.433) | 70.0% (59.5 to 81.3) | 47.5% (38.8 to 56.2) |
| vf_pro_cut | 200 | 68.0% (61.7 to 74.5) | 0.488 (0.361 to 0.614) | 23.7% (13.7 to 34.2) | 75.0% (60.9 to 90.0) | 262 | 61.8% (55.6 to 68.6) | 0.489 (0.391 to 0.588) | 0.290 (0.206 to 0.384) | 22.5% (13.2 to 32.0) | 72.0% (58.3 to 89.7) |
| ours_llama | 200 | 56.5% (49.0 to 63.5) | 0.131 (-0.019 to 0.272) | 69.7% (59.2 to 79.0) | 45.3% (36.1 to 54.1) | 262 | 54.2% (47.6 to 60.2) | 0.372 (0.275 to 0.461) | 0.193 (0.081 to 0.293) | 62.5% (51.0 to 72.4) | 37.6% (29.4 to 45.7) |
| ours_llama_alljudge | 200 | 48.5% (41.4 to 55.6) | -0.021 (-0.161 to 0.130) | 76.3% (66.7 to 85.1) | 40.6% (32.7 to 48.3) | 262 | 43.9% (37.2 to 50.2) | 0.233 (0.141 to 0.322) | 0.055 (-0.062 to 0.162) | 67.5% (58.0 to 77.3) | 31.6% (24.3 to 38.8) |
| vf_llama_cut | 200 | 55.0% (47.8 to 61.9) | 0.165 (0.010 to 0.316) | 35.5% (25.4 to 46.2) | 39.7% (28.4 to 50.6) | 262 | 51.5% (45.0 to 58.1) | 0.350 (0.253 to 0.446) | 0.049 (-0.070 to 0.160) | 30.0% (20.9 to 39.3) | 28.9% (19.5 to 38.8) |
| vf_llama_nocut | 200 | 54.0% (46.5 to 61.3) | 0.130 (-0.024 to 0.283) | 39.5% (28.8 to 50.0) | 39.5% (28.7 to 50.0) | 262 | 50.0% (44.2 to 56.4) | 0.322 (0.237 to 0.417) | 0.050 (-0.058 to 0.162) | 31.2% (22.4 to 41.1) | 27.8% (19.4 to 36.8) |

## Answers from deepseek-v4.1-flash

| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | Atoms | Atom agreement | Atom AC1 | Atom MCC | Not Supported found | Not Supported PPV |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ours_vote | 261 | 82.8% (78.0 to 87.5) | 0.720 (0.632 to 0.804) | 77.6% (65.6 to 88.5) | 58.4% (47.3 to 68.8) | 530 | 80.2% (76.1 to 84.2) | 0.764 (0.709 to 0.816) | 0.414 (0.318 to 0.504) | 65.7% (53.7 to 78.6) | 48.4% (38.2 to 58.5) |
| ours_pro | 261 | 64.4% (58.8 to 70.2) | 0.338 (0.218 to 0.465) | 82.8% (71.4 to 91.9) | 36.6% (28.4 to 45.5) | 530 | 67.9% (63.4 to 72.4) | 0.601 (0.538 to 0.662) | 0.295 (0.214 to 0.376) | 74.3% (62.5 to 85.5) | 27.4% (21.1 to 34.0) |
| vf_pro_cut | 261 | 73.9% (68.8 to 79.1) | 0.628 (0.537 to 0.715) | 24.1% (12.0 to 36.6) | 36.8% (19.3 to 55.8) | 530 | 70.2% (65.5 to 74.6) | 0.645 (0.580 to 0.705) | 0.100 (0.027 to 0.182) | 14.3% (6.2 to 24.6) | 24.4% (11.3 to 40.0) |
| ours_llama | 261 | 64.8% (58.9 to 71.1) | 0.349 (0.221 to 0.475) | 81.0% (70.0 to 91.2) | 36.7% (28.4 to 46.3) | 530 | 68.3% (63.5 to 72.8) | 0.611 (0.544 to 0.671) | 0.222 (0.136 to 0.313) | 61.4% (50.0 to 73.8) | 25.0% (18.7 to 32.3) |
| ours_llama_alljudge | 261 | 46.7% (40.5 to 53.5) | -0.045 (-0.175 to 0.096) | 74.1% (61.2 to 85.5) | 25.7% (19.0 to 33.1) | 530 | 54.0% (48.9 to 59.2) | 0.416 (0.322 to 0.487) | 0.056 (-0.036 to 0.143) | 54.3% (42.2 to 66.3) | 15.4% (10.4 to 20.4) |
| vf_llama_cut | 261 | 52.5% (46.4 to 59.1) | 0.119 (-0.021 to 0.266) | 55.2% (42.9 to 67.3) | 24.6% (17.4 to 33.0) | 530 | 61.9% (56.8 to 67.3) | 0.533 (0.461 to 0.606) | 0.013 (-0.063 to 0.104) | 31.4% (20.8 to 44.0) | 13.2% (8.5 to 18.8) |
| vf_llama_nocut | 261 | 52.1% (46.3 to 58.3) | 0.124 (-0.006 to 0.259) | 48.3% (35.4 to 60.4) | 22.8% (16.0 to 31.0) | 530 | 60.4% (55.1 to 66.1) | 0.510 (0.434 to 0.588) | 0.015 (-0.057 to 0.097) | 31.4% (20.5 to 43.8) | 13.6% (8.7 to 19.3) |

## Answers from qwen2.5-7b

| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | Atoms | Atom agreement | Atom AC1 | Atom MCC | Not Supported found | Not Supported PPV |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ours_vote | 142 | 81.7% (75.0 to 88.4) | 0.666 (0.535 to 0.796) | 75.0% (63.2 to 86.3) | 72.0% (58.0 to 85.2) | 173 | 75.7% (69.3 to 82.7) | 0.672 (0.577 to 0.770) | 0.538 (0.429 to 0.658) | 76.0% (64.1 to 86.8) | 66.7% (50.7 to 81.7) |
| ours_pro | 142 | 79.6% (72.5 to 86.0) | 0.615 (0.477 to 0.743) | 81.2% (70.8 to 91.8) | 66.1% (53.0 to 78.7) | 173 | 74.0% (67.0 to 80.7) | 0.649 (0.553 to 0.749) | 0.513 (0.407 to 0.627) | 82.0% (71.8 to 92.3) | 59.4% (45.8 to 72.3) |
| vf_pro_cut | 142 | 70.4% (63.5 to 78.5) | 0.556 (0.412 to 0.693) | 18.8% (8.0 to 32.6) | 75.0% (45.4 to 100.0) | 173 | 68.2% (61.5 to 75.3) | 0.596 (0.504 to 0.697) | 0.321 (0.195 to 0.450) | 18.0% (7.4 to 31.6) | 75.0% (45.4 to 100.0) |
| ours_llama | 142 | 59.9% (51.1 to 68.6) | 0.211 (0.044 to 0.392) | 68.8% (53.4 to 82.7) | 44.0% (31.8 to 56.1) | 173 | 56.6% (48.6 to 64.5) | 0.406 (0.291 to 0.521) | 0.246 (0.117 to 0.366) | 66.0% (51.0 to 79.0) | 38.4% (26.4 to 51.1) |
| ours_llama_alljudge | 142 | 53.5% (45.6 to 61.4) | 0.077 (-0.082 to 0.244) | 66.7% (52.2 to 80.0) | 39.0% (28.4 to 50.0) | 173 | 51.4% (43.4 to 59.8) | 0.342 (0.226 to 0.461) | 0.135 (0.000 to 0.270) | 62.0% (46.8 to 74.6) | 32.6% (22.1 to 42.9) |
| vf_llama_cut | 142 | 53.5% (46.3 to 61.4) | 0.211 (0.042 to 0.391) | 16.7% (6.7 to 27.5) | 23.5% (9.1 to 40.5) | 173 | 52.0% (45.8 to 59.6) | 0.385 (0.287 to 0.498) | -0.085 (-0.195 to 0.033) | 14.0% (4.4 to 23.4) | 16.7% (5.1 to 29.5) |
| vf_llama_nocut | 142 | 54.2% (46.5 to 61.8) | 0.212 (0.039 to 0.385) | 20.8% (10.3 to 31.1) | 27.0% (12.1 to 42.9) | 173 | 54.3% (48.3 to 61.0) | 0.410 (0.320 to 0.505) | -0.005 (-0.139 to 0.131) | 18.0% (7.9 to 27.4) | 22.0% (9.3 to 36.1) |

## Sensitivity: without the 54 atoms whose reference evidence is the admission diagnosis or unit type (case header, not in the systems' records)

| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | Atoms | Atom agreement | Atom AC1 | Atom MCC | Not Supported found | Not Supported PPV |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ours_vote | 588 | 83.8% (80.5 to 87.5) | 0.720 (0.659 to 0.788) | 74.9% (66.9 to 82.2) | 72.0% (64.6 to 79.0) | 911 | 79.9% (76.4 to 83.3) | 0.745 (0.696 to 0.793) | 0.534 (0.469 to 0.600) | 69.8% (61.7 to 77.1) | 65.0% (56.9 to 73.0) |
| ours_pro | 588 | 71.3% (67.5 to 75.4) | 0.458 (0.380 to 0.546) | 78.3% (71.3 to 84.9) | 51.1% (45.3 to 57.4) | 911 | 69.4% (65.9 to 73.0) | 0.601 (0.550 to 0.654) | 0.383 (0.328 to 0.439) | 74.0% (66.8 to 81.0) | 42.0% (36.4 to 47.7) |
| vf_pro_cut | 588 | 71.8% (67.6 to 76.4) | 0.577 (0.493 to 0.661) | 23.4% (16.8 to 30.6) | 56.2% (45.1 to 68.4) | 911 | 69.9% (65.9 to 73.9) | 0.628 (0.571 to 0.682) | 0.238 (0.171 to 0.310) | 19.3% (13.6 to 26.1) | 48.1% (37.5 to 61.0) |
| ours_llama | 588 | 62.2% (58.0 to 66.8) | 0.276 (0.185 to 0.368) | 69.7% (61.3 to 76.9) | 41.9% (35.7 to 48.2) | 911 | 64.7% (60.6 to 68.3) | 0.541 (0.484 to 0.593) | 0.273 (0.203 to 0.345) | 62.0% (53.7 to 70.0) | 34.4% (28.8 to 40.5) |
| ours_llama_alljudge | 588 | 49.5% (44.7 to 54.7) | -0.004 (-0.100 to 0.101) | 70.3% (62.4 to 77.9) | 33.4% (27.7 to 39.1) | 911 | 52.3% (48.3 to 56.5) | 0.369 (0.313 to 0.431) | 0.114 (0.043 to 0.187) | 60.4% (52.5 to 68.3) | 24.7% (20.0 to 29.4) |
| vf_llama_cut | 588 | 55.1% (50.9 to 59.5) | 0.207 (0.109 to 0.310) | 31.4% (24.3 to 38.4) | 27.6% (21.1 to 34.4) | 911 | 59.1% (55.0 to 63.4) | 0.484 (0.423 to 0.547) | 0.010 (-0.053 to 0.076) | 24.0% (17.5 to 31.0) | 18.3% (13.2 to 23.1) |
| vf_llama_nocut | 588 | 54.3% (50.1 to 58.7) | 0.186 (0.088 to 0.287) | 32.0% (25.0 to 39.0) | 27.2% (20.8 to 33.6) | 911 | 58.1% (54.0 to 62.4) | 0.467 (0.405 to 0.531) | 0.026 (-0.042 to 0.093) | 25.5% (19.8 to 32.4) | 19.0% (14.4 to 23.7) |

## Sensitivity: also without the 21 atoms decided by guideline rule 7 (intermittent drugs documented in the treatment table count as given)

| Run | Sentences | Sentence agreement | Sentence AC1 | Wrong sentences found | Flag precision | Atoms | Atom agreement | Atom AC1 | Atom MCC | Not Supported found | Not Supported PPV |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ours_vote | 576 | 84.4% (81.1 to 87.9) | 0.729 (0.666 to 0.795) | 74.9% (66.9 to 82.2) | 74.0% (66.5 to 81.6) | 890 | 81.2% (77.8 to 84.7) | 0.762 (0.716 to 0.809) | 0.559 (0.493 to 0.625) | 69.8% (61.7 to 77.1) | 68.4% (60.4 to 76.3) |
| ours_pro | 576 | 71.7% (67.9 to 75.9) | 0.465 (0.387 to 0.556) | 78.3% (71.3 to 84.9) | 52.3% (46.3 to 58.7) | 890 | 70.6% (67.1 to 74.3) | 0.617 (0.566 to 0.670) | 0.400 (0.348 to 0.454) | 74.0% (66.8 to 81.0) | 43.7% (37.8 to 49.5) |
| vf_pro_cut | 576 | 71.4% (67.1 to 75.9) | 0.568 (0.486 to 0.649) | 23.4% (16.8 to 30.6) | 56.9% (45.3 to 69.2) | 890 | 69.3% (65.2 to 73.3) | 0.619 (0.561 to 0.675) | 0.236 (0.168 to 0.308) | 19.3% (13.6 to 26.1) | 48.7% (37.7 to 61.6) |
| ours_llama | 576 | 63.2% (58.7 to 67.7) | 0.295 (0.203 to 0.388) | 69.7% (61.3 to 76.9) | 43.4% (37.3 to 49.8) | 890 | 66.1% (62.1 to 69.8) | 0.560 (0.503 to 0.611) | 0.291 (0.222 to 0.362) | 62.0% (53.7 to 70.0) | 36.2% (30.2 to 42.4) |
| ours_llama_alljudge | 576 | 50.2% (45.5 to 55.5) | 0.009 (-0.086 to 0.115) | 70.3% (62.4 to 77.9) | 34.4% (28.8 to 40.1) | 890 | 53.0% (49.1 to 57.5) | 0.380 (0.325 to 0.442) | 0.123 (0.053 to 0.196) | 60.4% (52.5 to 68.3) | 25.6% (20.8 to 30.5) |
| vf_llama_cut | 576 | 54.3% (50.2 to 58.7) | 0.188 (0.090 to 0.289) | 31.4% (24.3 to 38.4) | 27.8% (21.3 to 34.5) | 890 | 58.2% (54.0 to 62.5) | 0.472 (0.409 to 0.534) | 0.004 (-0.060 to 0.070) | 24.0% (17.5 to 31.0) | 18.3% (13.3 to 23.2) |
| vf_llama_nocut | 576 | 53.6% (49.5 to 58.1) | 0.170 (0.072 to 0.272) | 32.0% (25.0 to 39.0) | 27.5% (21.2 to 33.9) | 890 | 57.3% (53.1 to 61.8) | 0.455 (0.392 to 0.521) | 0.021 (-0.047 to 0.086) | 25.5% (19.8 to 32.4) | 19.1% (14.5 to 23.8) |

## Paired differences, all answer sets (same items, case bootstrap)

| A | B | Sentence agreement A minus B (95% CI) | Only A right / only B right | Atom agreement A minus B (95% CI) | Only A right / only B right |
|---|---|---|---|---|---|
| ours_pro | vf_pro_cut | -2.2 (-7.1 to +2.7) | 123 / 136 | -0.2 (-4.7 to +4.5) | 189 / 191 |
| ours_llama | vf_llama_cut | +7.3 (+1.4 to +13.1) | 156 / 112 | +5.1 (-0.1 to +10.2) | 230 / 181 |
| ours_vote | vf_pro_cut | +10.8 (+5.7 to +15.4) | 123 / 58 | +9.3 (+5.0 to +13.5) | 184 / 94 |
| ours_llama | ours_llama_alljudge | +11.9 (+7.7 to +16.2) | 102 / 30 | +11.6 (+8.2 to +15.0) | 173 / 61 |
| ours_llama_alljudge | vf_llama_cut | -4.6 (-10.9 to +1.1) | 109 / 137 | -6.5 (-11.9 to -1.4) | 152 / 215 |
| vf_llama_cut | vf_llama_nocut | +0.3 (-2.1 to +2.8) | 37 / 35 | +0.8 (-1.1 to +3.1) | 60 / 52 |
| ours_vote | ours_pro | +12.9 (+9.4 to +16.3) | 99 / 21 | +9.5 (+6.7 to +12.2) | 117 / 25 |
| ours_pro | ours_llama | +8.1 (+3.5 to +12.7) | 102 / 53 | +5.0 (+1.3 to +8.4) | 124 / 76 |

Runs:

- `ours_vote`: Evaluator, cloud vote (deepseek-v4-pro, minimax-m3.1-flash, glm-5.3)
- `ours_pro`: Evaluator, deepseek-v4-pro judge
- `vf_pro_cut`: VeriFact, deepseek-v4-pro judge, records cut at T
- `ours_llama`: Evaluator, llama3.1:8b judge
- `ours_llama_alljudge`: Evaluator, llama3.1:8b judge, every fact to the judge (no code checks)
- `vf_llama_cut`: VeriFact, llama3.1:8b judge, records cut at T
- `vf_llama_nocut`: VeriFact, llama3.1:8b judge, all records (as published)
