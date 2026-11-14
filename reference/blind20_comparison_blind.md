# Blind test: 20 up-to-10-claim cases

Claude wrote the split and the verdicts before any model judged these items. The judges are deepseek-v4-pro:0813, minimax-m3.1-flash and glm-5.3. Not clinician truth.

| Items | n | Agreement (95% CI by case) | Kappa | False facts found | Flagged false | Flags right |
|---|---|---|---|---|---|---|
| All | 787 | 98.6% | 0.97 | 104/104 | 108 | 104 |
| Facts | 329 | 96.7% | 0.89 | 31/31 | 35 | 31 |
| Actions | 458 | 100.0% | 1.00 | 73/73 | 73 | 73 |
| Judged by the vote | 133 | 91.7% (87.5% to 95.5%) | 0.80 | 12/12 | 16 | 12 |

## Single judges, before the code guard

| Judge | n | Agreement | Kappa | False facts found | Flagged false | Flags right |
|---|---|---|---|---|---|---|
| deepseek-v4-pro:0813 | 133 | 88.0% | 0.72 | 12/12 | 22 | 12 |
| minimax-m3.1-flash | 133 | 89.5% | 0.75 | 12/12 | 23 | 12 |
| glm-5.3 | 126 | 91.3% | 0.79 | 12/12 | 20 | 12 |

Unanimous 122, two to one 8, split 3.
