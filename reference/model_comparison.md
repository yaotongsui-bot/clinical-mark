# Model comparison

Each model split the frozen answers and was the only judge; the code rules are the same.

## Answer set base

| Model | Items | Facts | Actions | Goals | Fact accuracy | Cases with false fact | Treatment agreement | Key treatments mentioned | Facts omitted | Judged by a model |
|---|---|---|---|---|---|---|---|---|---|---|
| deepseek-v4.1-flash | 893 | 374 | 504 | 15 | 79.4% | 45.9% | 74.5% | 24.3% | 133 | 188 |
| glm-5.3-flash | 924 | 456 | 452 | 16 | 81.7% | 44.7% | 75.2% | 23.4% | 133 | 245 |
| minimax-m3.1-flash | 916 | 409 | 492 | 15 | 83.0% | 47.1% | 76.9% | 23.8% | 133 | 222 |
| glm-5.3 | 968 | 462 | 492 | 14 | 83.2% | 47.1% | 73.9% | 23.8% | 133 | 256 |
| mimo-v2.6-pro | 859 | 367 | 471 | 21 | 77.9% | 49.4% | 76.7% | 23.4% | 133 | 184 |
| muse-spark-open | 967 | 477 | 476 | 14 | 84.5% | 48.2% | 74.8% | 22.9% | 133 | 279 |
| deepseek-v4-pro_0813 | 833 | 352 | 465 | 16 | 83.3% | 44.7% | 75.3% | 23.8% | 133 | 167 |
| kimi-k3.1-pro | 839 | 350 | 472 | 17 | 83.2% | 43.5% | 74.4% | 22.9% | 133 | 172 |

Pairwise means over 28 model pairs: item F1 0.84, verdict agreement on shared items 96.1%, Cohen's kappa 0.92; on items both judged by a model (code rules left out) 85.9%, kappa 0.65.

| Model | Mean item F1 with the others | Mean verdict agreement | Mean kappa |
|---|---|---|---|
| deepseek-v4.1-flash | 0.82 | 96.0% | 0.92 |
| glm-5.3-flash | 0.84 | 96.3% | 0.92 |
| minimax-m3.1-flash | 0.82 | 96.1% | 0.92 |
| glm-5.3 | 0.83 | 96.0% | 0.92 |
| mimo-v2.6-pro | 0.84 | 96.2% | 0.92 |
| muse-spark-open | 0.83 | 96.0% | 0.92 |
| deepseek-v4-pro_0813 | 0.86 | 96.2% | 0.92 |
| kimi-k3.1-pro | 0.86 | 96.5% | 0.93 |

## Answer set s1

| Model | Items | Facts | Actions | Goals | Fact accuracy | Cases with false fact | Treatment agreement | Key treatments mentioned | Facts omitted | Judged by a model |
|---|---|---|---|---|---|---|---|---|---|---|
| deepseek-v4.1-flash | 3442 | 1222 | 2141 | 79 | 86.1% | 68.2% | 63.9% | 49.5% | 77 | 557 |
| glm-5.3-flash | 3505 | 1323 | 2090 | 92 | 87.6% | 68.2% | 64.2% | 50.0% | 75 | 664 |
| minimax-m3.1-flash | 3415 | 1193 | 2114 | 108 | 87.0% | 70.6% | 64.1% | 49.5% | 77 | 525 |
| glm-5.3 | 3713 | 1443 | 2167 | 103 | 88.6% | 64.7% | 63.9% | 50.0% | 73 | 736 |
| mimo-v2.6-pro | 3358 | 1224 | 2055 | 79 | 85.6% | 72.9% | 63.9% | 50.0% | 77 | 527 |
| muse-spark-open | 3538 | 1355 | 2101 | 82 | 88.2% | 65.9% | 63.8% | 49.1% | 76 | 690 |
| deepseek-v4-pro_0813 | 3348 | 1236 | 2053 | 59 | 87.4% | 71.8% | 63.8% | 49.5% | 78 | 607 |
| kimi-k3.1-pro | 3559 | 1320 | 2161 | 78 | 88.8% | 65.9% | 62.4% | 49.5% | 77 | 659 |

Pairwise means over 28 model pairs: item F1 0.81, verdict agreement on shared items 96.2%, Cohen's kappa 0.93; on items both judged by a model (code rules left out) 83.5%, kappa 0.65.

| Model | Mean item F1 with the others | Mean verdict agreement | Mean kappa |
|---|---|---|---|
| deepseek-v4.1-flash | 0.81 | 96.1% | 0.93 |
| glm-5.3-flash | 0.82 | 96.6% | 0.94 |
| minimax-m3.1-flash | 0.79 | 96.0% | 0.93 |
| glm-5.3 | 0.81 | 95.9% | 0.92 |
| mimo-v2.6-pro | 0.81 | 96.2% | 0.93 |
| muse-spark-open | 0.81 | 96.3% | 0.93 |
| deepseek-v4-pro_0813 | 0.82 | 96.4% | 0.93 |
| kimi-k3.1-pro | 0.82 | 96.3% | 0.93 |

## Answer set s2

| Model | Items | Facts | Actions | Goals | Fact accuracy | Cases with false fact | Treatment agreement | Key treatments mentioned | Facts omitted | Judged by a model |
|---|---|---|---|---|---|---|---|---|---|---|
| deepseek-v4.1-flash | 3378 | 1212 | 2077 | 89 | 85.6% | 80.0% | 64.0% | 49.1% | 69 | 525 |
| glm-5.3-flash | 3467 | 1333 | 2026 | 108 | 89.4% | 69.4% | 64.6% | 50.9% | 65 | 661 |
| minimax-m3.1-flash | 3386 | 1233 | 2019 | 134 | 88.8% | 68.2% | 65.9% | 51.4% | 69 | 527 |
| glm-5.3 | 3618 | 1402 | 2093 | 123 | 89.3% | 62.4% | 64.2% | 49.1% | 68 | 712 |
| mimo-v2.6-pro | 3302 | 1176 | 2017 | 109 | 86.3% | 78.8% | 65.4% | 50.5% | 68 | 501 |
| muse-spark-open | 3404 | 1311 | 2006 | 87 | 88.9% | 68.2% | 65.8% | 49.1% | 67 | 647 |
| deepseek-v4-pro_0813 | 3326 | 1235 | 2024 | 67 | 86.6% | 77.6% | 64.1% | 49.1% | 68 | 580 |
| kimi-k3.1-pro | 3550 | 1343 | 2117 | 90 | 89.6% | 69.4% | 64.6% | 50.0% | 68 | 658 |

Pairwise means over 28 model pairs: item F1 0.81, verdict agreement on shared items 95.7%, Cohen's kappa 0.92; on items both judged by a model (code rules left out) 81.1%, kappa 0.60.

| Model | Mean item F1 with the others | Mean verdict agreement | Mean kappa |
|---|---|---|---|
| deepseek-v4.1-flash | 0.81 | 95.5% | 0.92 |
| glm-5.3-flash | 0.82 | 96.0% | 0.93 |
| minimax-m3.1-flash | 0.79 | 95.3% | 0.91 |
| glm-5.3 | 0.81 | 95.7% | 0.92 |
| mimo-v2.6-pro | 0.81 | 95.7% | 0.92 |
| muse-spark-open | 0.81 | 95.8% | 0.92 |
| deepseek-v4-pro_0813 | 0.82 | 95.8% | 0.92 |
| kimi-k3.1-pro | 0.81 | 96.0% | 0.93 |

## Answer set s3

| Model | Items | Facts | Actions | Goals | Fact accuracy | Cases with false fact | Treatment agreement | Key treatments mentioned | Facts omitted | Judged by a model |
|---|---|---|---|---|---|---|---|---|---|---|
| deepseek-v4.1-flash | 3501 | 1331 | 2088 | 82 | 87.4% | 77.6% | 68.3% | 52.3% | 70 | 579 |
| glm-5.3-flash | 3544 | 1410 | 2035 | 99 | 88.8% | 74.1% | 67.6% | 54.7% | 71 | 697 |
| minimax-m3.1-flash | 3437 | 1313 | 1992 | 132 | 89.2% | 70.6% | 68.6% | 55.1% | 71 | 551 |
| glm-5.3 | 3713 | 1511 | 2099 | 103 | 89.0% | 77.6% | 68.1% | 52.8% | 72 | 760 |
| mimo-v2.6-pro | 3401 | 1294 | 2003 | 104 | 86.9% | 81.2% | 67.2% | 53.3% | 70 | 565 |
| muse-spark-open | 3407 | 1387 | 1944 | 76 | 89.2% | 74.1% | 67.9% | 53.7% | 70 | 661 |
| deepseek-v4-pro_0813 | 3373 | 1295 | 2010 | 68 | 87.9% | 76.5% | 67.1% | 53.3% | 70 | 609 |
| kimi-k3.1-pro | 3622 | 1425 | 2104 | 93 | 89.7% | 74.1% | 67.2% | 53.7% | 70 | 696 |

Pairwise means over 28 model pairs: item F1 0.80, verdict agreement on shared items 95.8%, Cohen's kappa 0.92; on items both judged by a model (code rules left out) 81.5%, kappa 0.59.

| Model | Mean item F1 with the others | Mean verdict agreement | Mean kappa |
|---|---|---|---|
| deepseek-v4.1-flash | 0.80 | 96.0% | 0.92 |
| glm-5.3-flash | 0.81 | 96.1% | 0.93 |
| minimax-m3.1-flash | 0.79 | 95.4% | 0.91 |
| glm-5.3 | 0.80 | 95.7% | 0.92 |
| mimo-v2.6-pro | 0.80 | 95.8% | 0.92 |
| muse-spark-open | 0.80 | 95.6% | 0.92 |
| deepseek-v4-pro_0813 | 0.81 | 95.7% | 0.92 |
| kimi-k3.1-pro | 0.80 | 95.9% | 0.92 |

