# Three-model vote on Claude's split

Atoms: reference/split_standard.csv. Judges: deepseek-v4-pro:0813, deepseek-v4.1-flash, mimo-v2.6-pro. Reference verdicts are Claude's and were revised once after seeing earlier model disagreements, so agreement may lean high.

| Items | n | Agreement (95% CI) | Kappa | False facts found | Flagged false | Flags right |
|---|---|---|---|---|---|---|
| All | 927 | 98.1% (97.2% to 98.9%) | 0.96 | 186/188 | 188 | 186 |
| Facts | 486 | 96.3% (94.5% to 97.9%) | 0.92 | 101/103 | 103 | 101 |
| Actions | 441 | 100.0% (100.0% to 100.0%) | 1.00 | 85/85 | 85 | 85 |
| Judged by the vote | 275 | 93.5% (90.3% to 96.2%) | 0.84 | 49/51 | 51 | 49 |

Vote on judged items: {'3/3': 239, '2/3': 33, 'split': 3}.

| Result | Vote | Reference |
|---|---|---|
| Fact accuracy | 77.0% | 77.4% |
| False facts | 103 | 103 |
| Cases with a false fact | 43 | 42 |
| Treatment agreement | 77.8% | 77.8% |
| Key treatment recall | 23.8% | 23.8% |
