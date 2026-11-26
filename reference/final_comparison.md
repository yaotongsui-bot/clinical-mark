# Three-model vote on Claude's split

Atoms: reference/split_standard.csv. Judges: deepseek-v4-pro:0813, deepseek-v4.1-flash, mimo-v2.6-pro. Reference verdicts are Claude's and were revised once after seeing earlier model disagreements, so agreement may lean high.

| Items | n | Agreement (95% CI) | Kappa | False facts found | Flagged false | Flags right |
|---|---|---|---|---|---|---|
| All | 927 | 98.9% (98.3% to 99.5%) | 0.98 | 187/188 | 187 | 187 |
| Facts | 486 | 97.9% (96.7% to 99.0%) | 0.95 | 102/103 | 102 | 102 |
| Actions | 441 | 100.0% (100.0% to 100.0%) | 1.00 | 85/85 | 85 | 85 |
| Judged by the vote | 275 | 96.4% (94.1% to 98.4%) | 0.91 | 50/51 | 50 | 50 |

Vote on judged items: {'3/3': 259, '2/3': 13, 'split': 3}.

| Result | Vote | Reference |
|---|---|---|
| Fact accuracy | 77.6% | 77.4% |
| False facts | 102 | 103 |
| Cases with a false fact | 42 | 42 |
| Treatment agreement | 77.8% | 77.8% |
| Key treatment recall | 23.8% | 23.8% |
