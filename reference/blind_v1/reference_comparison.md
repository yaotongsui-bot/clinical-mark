# Models against the reference

The reference is Claude's own splitting and judgment under the same rules and the same retrieved records. It is a comparison anchor, not clinician ground truth.

Reference: 882 scored items, fact accuracy 85.9%, 59 false facts in 36 cases, treatment agreement 75.3%, key treatment recall 22.9%.

## Splitting

| Model | Items | Aligned | Precision | Recall | F1 |
|---|---|---|---|---|---|
| deepseek-v4.1-flash | 878 | 699 | 79.6% | 79.3% | 0.79 |
| glm-5.3-flash | 908 | 758 | 83.5% | 85.9% | 0.85 |
| minimax-m3.1-flash | 901 | 714 | 79.2% | 81.0% | 0.80 |
| glm-5.3 | 954 | 741 | 77.7% | 84.0% | 0.81 |
| mimo-v2.6-pro | 838 | 715 | 85.3% | 81.1% | 0.83 |
| muse-spark-open | 953 | 789 | 82.8% | 89.5% | 0.86 |
| deepseek-v4-pro_0813 | 817 | 706 | 86.4% | 80.0% | 0.83 |
| kimi-k3.1-pro | 822 | 709 | 86.3% | 80.4% | 0.83 |
| panel (3 judges) | 878 | 699 | 79.6% | 79.3% | 0.79 |

## Verdicts on aligned items (positive / negative / undetermined)

| Model | All items | Kappa | Facts | Fact kappa | Actions | Both judged by a model (n) | Agreement | Kappa |
|---|---|---|---|---|---|---|---|---|
| deepseek-v4.1-flash | 93.6% | 0.87 | 87.9% | 0.73 | 97.8% | 123 | 78.0% | 0.51 |
| glm-5.3-flash | 93.3% | 0.86 | 89.6% | 0.76 | 96.5% | 154 | 85.1% | 0.61 |
| minimax-m3.1-flash | 93.6% | 0.86 | 88.7% | 0.70 | 97.3% | 142 | 85.2% | 0.58 |
| glm-5.3 | 94.2% | 0.88 | 90.0% | 0.77 | 97.8% | 141 | 84.4% | 0.56 |
| mimo-v2.6-pro | 93.1% | 0.86 | 87.4% | 0.73 | 97.5% | 138 | 76.8% | 0.48 |
| muse-spark-open | 93.5% | 0.86 | 89.5% | 0.74 | 97.5% | 185 | 82.7% | 0.48 |
| deepseek-v4-pro_0813 | 95.5% | 0.91 | 93.3% | 0.84 | 97.1% | 120 | 90.0% | 0.70 |
| kimi-k3.1-pro | 96.1% | 0.92 | 93.9% | 0.85 | 97.7% | 135 | 88.9% | 0.69 |
| panel (3 judges) | 94.4% | 0.89 | 89.9% | 0.77 | 97.8% | 123 | 82.9% | 0.58 |

## False facts and case-level results

| Model | Reference false facts aligned | Also called false | Called false on aligned items | Same false-fact status by case | Mean case accuracy gap | Fact accuracy | Cases with false fact | Treatment agreement | Key recall |
|---|---|---|---|---|---|---|---|---|---|
| deepseek-v4.1-flash | 45 | 41 | 52 | 89.4% | 11.5% | 79.4% | 39 | 74.5% | 24.3% |
| glm-5.3-flash | 55 | 52 | 64 | 92.9% | 6.7% | 81.7% | 38 | 75.2% | 23.4% |
| minimax-m3.1-flash | 42 | 35 | 45 | 95.3% | 7.5% | 83.0% | 40 | 76.9% | 23.8% |
| glm-5.3 | 54 | 51 | 62 | 90.6% | 5.7% | 83.2% | 40 | 73.9% | 23.8% |
| mimo-v2.6-pro | 47 | 45 | 62 | 90.6% | 12.3% | 77.9% | 42 | 76.7% | 23.4% |
| muse-spark-open | 55 | 53 | 60 | 94.1% | 5.0% | 84.5% | 41 | 74.8% | 22.9% |
| deepseek-v4-pro_0813 | 46 | 41 | 45 | 92.9% | 8.0% | 83.3% | 38 | 75.3% | 23.8% |
| kimi-k3.1-pro | 46 | 45 | 51 | 94.1% | 6.3% | 83.2% | 37 | 74.4% | 22.9% |
| panel (3 judges) | 45 | 42 | 48 | 92.9% | 8.9% | 81.8% | 36 | 74.5% | 24.3% |
