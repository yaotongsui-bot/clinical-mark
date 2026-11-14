# Splitting prompts against the standards

Standards: Claude's split of the 85 base cases and of the 20 blind cases. Matching is by wording, so absolute numbers lean low.

| Group | Model | Prompt | Atoms | Precision | Recall | F1 | Facts found | Actions found |
|---|---|---|---|---|---|---|---|---|
| base | standard | - | 947 | | | | | |
| base | deepseek-v4-pro:0813 | current | 833 | 89.4% | 78.7% | 0.837 | 62.8% | 96.6% |
| base | deepseek-v4-pro:0813 | v2 | 976 | 90.6% | 93.3% | 0.919 | 91.6% | 95.7% |
| base | muse-spark-open | current | 967 | 87.5% | 89.3% | 0.884 | 85.2% | 95.5% |
| base | muse-spark-open | v2 | 1022 | 86.4% | 93.2% | 0.897 | 92.8% | 94.8% |
| blind20 | standard | - | 801 | | | | | |
| blind20 | deepseek-v4-pro:0813 | current | 729 | 92.2% | 83.9% | 0.878 | 76.0% | 91.0% |
| blind20 | deepseek-v4-pro:0813 | v2 | 788 | 91.5% | 90.0% | 0.907 | 85.7% | 93.7% |
| blind20 | muse-spark-open | current | 774 | 90.7% | 87.6% | 0.891 | 82.4% | 92.1% |
| blind20 | muse-spark-open | v2 | 827 | 88.9% | 91.8% | 0.903 | 90.3% | 93.4% |
