# Run comparison: `results_fixed` -> `results_cloud`

| Metric | results_fixed | results_cloud |
|---|---|---|
| Fact atoms | 87 | 121 |
| supported / not_supported / not_addressed / unverifiable | 57 / 18 / 5 / 7 | 67 / 31 / 13 / 10 |
| Fact accuracy | 76.0% | 68.4% |
| Cases with a not_supported fact | 17 | 28 |
| Treatment agreement (strict) | 81.9% | 81.7% |
| Monitoring performed rate | 78.7% | 78.4% |
| Vital recall | 19.6% | 21.0% |
| All recall | 12.8% | 15.7% |

## Cases whose AI answer changed

0 of 85 AI answers changed. The generator is not fully reproducible even with an identical prompt (2 of 4 old prompts reproduced the old answer), so changes in single cases cannot all be attributed to the input repair; compare the aggregate metrics.

| Case | Before | After | not_supported before -> after |
|---|---|---|---|
