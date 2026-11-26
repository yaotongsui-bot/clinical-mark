# Judges on the same atoms

167 model-judged items of deepseek-v4-pro:0813's split, 167 with a reference label (20 carried from identical wording, the rest labelled blind). 95% intervals: bootstrap by case.

| Design | n | Agreement (95% CI) | Kappa | False facts found | Flagged false | Flags right | Extra calls |
|---|---|---|---|---|---|---|---|
| deepseek-v4-pro_0813 | 167 | 85.6% (78.8% to 91.6%) | 0.62 | 8/13 | 12 | 8 | 0 |
| kimi-k3.1-pro | 167 | 89.2% (84.1% to 93.7%) | 0.70 | 9/13 | 14 | 9 | 0 |
| deepseek-v4.1-flash | 167 | 80.8% (73.9% to 86.9%) | 0.55 | 9/13 | 15 | 9 | 0 |
| mimo-v2.6-pro | 167 | 81.4% (74.1% to 87.8%) | 0.57 | 11/13 | 20 | 11 | 0 |
| pro; kimi rechecks its 'not supported' | 167 | 85.0% (78.0% to 91.3%) | 0.59 | 6/13 | 9 | 6 | 12 |
| flash; pro rechecks its non-positive | 167 | 85.6% (78.8% to 91.6%) | 0.62 | 8/13 | 12 | 8 | 54 |
| flash; kimi rechecks its non-positive | 167 | 88.6% (83.5% to 93.2%) | 0.68 | 8/13 | 13 | 8 | 54 |
| pro + flash; kimi on disagreement | 167 | 85.0% (78.4% to 91.0%) | 0.62 | 8/13 | 13 | 8 | 15 |
| chosen vote: pro, flash, mimo | 167 | 83.8% (77.5% to 89.8%) | 0.61 | 10/13 | 16 | 10 | 0 |
