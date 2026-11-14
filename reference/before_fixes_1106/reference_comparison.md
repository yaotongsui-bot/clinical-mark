# Models against the reference

The reference is Claude's own splitting and judgment under the same rules and the same retrieved records. It is a comparison anchor, not clinician ground truth.

Reference: 882 scored items, fact accuracy 78.5%, 91 false facts in 39 cases, treatment agreement 76.4%, key treatment recall 22.9%.

## Splitting

| Model | Items | Aligned | Precision | Recall | F1 |
|---|---|---|---|---|---|
| deepseek-v4.1-flash | 878 | 699 | 79.6% | 79.3% | 0.79 |
| glm-5.3-flash | 908 | 758 | 83.5% | 85.9% | 0.85 |
| minimax-m3.1-flash | 901 | 714 | 79.2% | 81.0% | 0.80 |
| glm-5.3 | 954 | 741 | 77.7% | 84.0% | 0.81 |
| mimo-v2.6-pro | 838 | 715 | 85.3% | 81.1% | 0.83 |
| muse-spark-open | 953 | 790 | 82.9% | 89.6% | 0.86 |
| deepseek-v4-pro_0813 | 817 | 706 | 86.4% | 80.0% | 0.83 |
| kimi-k3.1-pro | 822 | 708 | 86.1% | 80.3% | 0.83 |
| panel (3 judges) | 878 | 699 | 79.6% | 79.3% | 0.79 |

## Verdicts on aligned items (positive / negative / undetermined)

| Model | All items | Kappa | Facts | Fact kappa | Actions | Both judged by a model (n) | Agreement | Kappa |
|---|---|---|---|---|---|---|---|---|
| deepseek-v4.1-flash | 95.4% | 0.91 | 90.9% | 0.80 | 98.8% | 123 | 82.9% | 0.64 |
| glm-5.3-flash | 93.1% | 0.86 | 88.8% | 0.76 | 97.0% | 154 | 79.9% | 0.56 |
| minimax-m3.1-flash | 93.4% | 0.86 | 87.7% | 0.71 | 97.8% | 142 | 81.7% | 0.58 |
| glm-5.3 | 93.5% | 0.87 | 87.9% | 0.74 | 98.3% | 141 | 77.3% | 0.52 |
| mimo-v2.6-pro | 94.5% | 0.89 | 89.4% | 0.78 | 98.5% | 138 | 81.9% | 0.63 |
| muse-spark-open | 92.8% | 0.85 | 87.4% | 0.71 | 98.0% | 184 | 77.7% | 0.46 |
| deepseek-v4-pro_0813 | 96.6% | 0.93 | 94.6% | 0.87 | 98.0% | 120 | 92.5% | 0.76 |
| kimi-k3.1-pro | 96.8% | 0.93 | 95.5% | 0.89 | 97.7% | 135 | 92.6% | 0.79 |
| panel (3 judges) | 95.9% | 0.92 | 91.9% | 0.82 | 98.8% | 123 | 85.4% | 0.67 |

## False facts and case-level results

| Model | Reference false facts aligned | Also called false | Called false on aligned items | Same false-fact status by case | Mean case accuracy gap | Fact accuracy | Cases with false fact | Treatment agreement | Key recall |
|---|---|---|---|---|---|---|---|---|---|
| deepseek-v4.1-flash | 55 | 47 | 52 | 90.6% | 10.1% | 79.4% | 39 | 74.5% | 24.3% |
| glm-5.3-flash | 78 | 58 | 64 | 94.1% | 6.0% | 81.7% | 38 | 75.2% | 23.4% |
| minimax-m3.1-flash | 63 | 41 | 45 | 94.1% | 8.2% | 83.0% | 40 | 76.9% | 23.8% |
| glm-5.3 | 81 | 55 | 62 | 91.8% | 8.2% | 83.2% | 40 | 73.9% | 23.8% |
| mimo-v2.6-pro | 63 | 54 | 62 | 91.8% | 10.5% | 77.9% | 42 | 76.7% | 23.4% |
| muse-spark-open | 80 | 55 | 60 | 92.9% | 7.6% | 84.5% | 41 | 74.8% | 22.9% |
| deepseek-v4-pro_0813 | 47 | 42 | 45 | 91.8% | 10.0% | 83.3% | 38 | 75.3% | 23.8% |
| kimi-k3.1-pro | 49 | 48 | 51 | 95.3% | 7.1% | 83.2% | 37 | 74.4% | 22.9% |
| panel (3 judges) | 55 | 45 | 48 | 94.1% | 8.4% | 81.8% | 36 | 74.5% | 24.3% |
