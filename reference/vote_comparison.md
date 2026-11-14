# Votes on Claude's split

275 items judged by a model, 85 cases. The reference is Claude's and was revised after seeing earlier model disagreements, so absolute agreement leans high.

| Vote | Agreement (95% CI) | Kappa | False facts found | Flagged false | Flags right | Unanimous | Split |
|---|---|---|---|---|---|---|---|
| pro + minimax + glm-5.3 | 96.4% (94.1% to 98.4%) | 0.91 | 50/51 | 50 | 50 | 259 | 3 |
| pro + flash + mimo | 93.5% (90.3% to 96.2%) | 0.84 | 49/51 | 51 | 49 | 239 | 3 |
| pro + mimo + glm-5.3 | 94.9% (92.1% to 97.3%) | 0.87 | 50/51 | 53 | 50 | 247 | 0 |

## Differences between votes (agreement points, 95% CI)

- pro + minimax + glm-5.3 minus pro + flash + mimo: +2.9% (+0.4% to +5.8%)
- pro + minimax + glm-5.3 minus pro + mimo + glm-5.3: +1.5% (+0.0% to +3.4%)
- pro + flash + mimo minus pro + mimo + glm-5.3: -1.5% (-3.8% to +0.7%)

## Single judges, before the code guard

| Judge | Agreement | Kappa | False facts found | Flagged false | Flags right |
|---|---|---|---|---|---|
| deepseek-v4-pro:0813 | 93.8% | 0.84 | 46/52 | 52 | 46 |
| mimo-v2.6-pro | 91.3% | 0.79 | 51/52 | 69 | 51 |
| deepseek-v4.1-flash | 90.2% | 0.78 | 50/52 | 57 | 50 |
| minimax-m3.1-flash | 96.4% | 0.91 | 51/52 | 56 | 51 |
| glm-5.3 | 96.0% | 0.90 | 52/52 | 59 | 52 |
