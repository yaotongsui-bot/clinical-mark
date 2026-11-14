# Split standard, base answers

85 cases, 947 atoms: 486 facts, 441 actions, 20 goals. Written by Claude and checked against eight models' splits; not reviewed by a clinician.

## Rules used

1. One atom per independently checkable target. A listed item is its own atom ("AST, ALT, alkaline phosphatase" gives three).
2. A general word followed by "including" is replaced by the items listed.
3. Assessing and managing are separate actions, because code checks them on different tracks. Two words for one check stay together ("assess and monitor").
4. Each ventilator, PCA or CRRT setting is its own fact, so each value can be checked. Settings named inside "continue ventilation" stay facts, not extra actions.
5. "Continue X" also gives the fact that X is under way. A stated order or device is a fact.
6. A purpose with no target of its own is not an atom ("for blood pressure control"). A named target stays a goal ("maintain SpO2 above 85%").
7. Conditions and things to look for are not facts, as in the atomizer prompt.

## Models against the standard

| Model | Atoms | Matched | Precision | Recall | F1 | Facts found | Actions found | Sentences split the same |
|---|---|---|---|---|---|---|---|---|
| muse-spark-open | 967 | 846 | 87.5% | 89.3% | 0.88 | 85.2% | 95.5% | 63.5% |
| glm-5.3-flash | 924 | 816 | 88.3% | 86.2% | 0.87 | 77.8% | 95.9% | 59.2% |
| kimi-k3.1-pro | 839 | 758 | 90.3% | 80.0% | 0.85 | 66.3% | 95.0% | 61.6% |
| mimo-v2.6-pro | 859 | 766 | 89.2% | 80.9% | 0.85 | 66.0% | 97.3% | 56.9% |
| deepseek-v4-pro_0813 | 833 | 745 | 89.4% | 78.7% | 0.84 | 62.8% | 96.6% | 55.7% |
| glm-5.3 | 968 | 797 | 82.3% | 84.2% | 0.83 | 74.1% | 96.4% | 47.5% |
| deepseek-v4.1-flash | 893 | 752 | 84.2% | 79.4% | 0.82 | 64.2% | 96.6% | 47.5% |
| minimax-m3.1-flash | 916 | 758 | 82.8% | 80.0% | 0.81 | 65.6% | 96.6% | 49.8% |
