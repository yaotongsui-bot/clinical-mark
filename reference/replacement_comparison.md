# Replacing glm-5.3 in the vote

Items judged by a model. References are Claude's, not clinician truth.

## Blind 20, blind verdicts

| Vote | n | Agreement | Kappa | False facts found | Flagged false | Flags right | Unanimous | Split |
|---|---|---|---|---|---|---|---|---|
| pro + minimax + glm-5.3 | 133 | 91.7% | 0.80 | 12/12 | 16 | 12 | 122 | 3 |
| pro + minimax + mimo | 133 | 89.5% | 0.76 | 12/12 | 18 | 12 | 117 | 3 |
| pro + minimax + flash | 133 | 89.5% | 0.76 | 12/12 | 17 | 12 | 110 | 2 |

## Blind 20, revised verdicts

| Vote | n | Agreement | Kappa | False facts found | Flagged false | Flags right | Unanimous | Split |
|---|---|---|---|---|---|---|---|---|
| pro + minimax + glm-5.3 | 133 | 94.0% | 0.85 | 12/12 | 16 | 12 | 122 | 3 |
| pro + minimax + mimo | 133 | 91.7% | 0.80 | 12/12 | 18 | 12 | 117 | 3 |
| pro + minimax + flash | 133 | 91.7% | 0.80 | 12/12 | 17 | 12 | 110 | 2 |

## Base 85 (reference revised after seeing earlier models)

| Vote | n | Agreement | Kappa | False facts found | Flagged false | Flags right | Unanimous | Split |
|---|---|---|---|---|---|---|---|---|
| pro + minimax + glm-5.3 | 275 | 96.4% | 0.91 | 50/51 | 50 | 50 | 259 | 3 |
| pro + minimax + mimo | 275 | 95.3% | 0.88 | 50/51 | 53 | 50 | 250 | 0 |
| pro + minimax + flash | 275 | 95.6% | 0.89 | 49/51 | 49 | 49 | 243 | 3 |

