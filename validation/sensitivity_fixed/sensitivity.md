# Fact-judge sensitivity analysis

- 28 facts judged by the panel in `results_fixed`; reference: panel verdicts in results_fixed.
- Labels: supported, not_supported, not_addressed.

| Retrieval | N | Judge | Reasoning | Percent agreement | Gwet's AC1 | MCC | Labels |
|---|---|---|---|---|---|---|---|
| bm25 | 50 | gemma4:12b | no | 75.0% | 0.69 | 0.43 | {'not_addressed': 10, 'supported': 18} |
| bm25 | 50 | llama3.1:8b-instruct-q4_K_M | no | 89.3% | 0.87 | 0.67 | {'not_addressed': 6, 'supported': 22} |
| bm25 | 50 | qwen2.5:14b | no | 89.3% | 0.87 | 0.65 | {'not_supported': 1, 'not_addressed': 4, 'supported': 23} |
| dense | 50 | gemma4:12b | no | 82.1% | 0.78 | 0.58 | {'not_addressed': 8, 'supported': 19, 'not_supported': 1} |
| dense | 50 | llama3.1:8b-instruct-q4_K_M | no | 82.1% | 0.78 | 0.55 | {'not_addressed': 6, 'supported': 20, 'not_supported': 2} |
| dense | 50 | qwen2.5:14b | no | 89.3% | 0.87 | 0.70 | {'not_supported': 3, 'supported': 22, 'not_addressed': 3} |
| hybrid | 10 | gemma4:12b | no | 67.9% | 0.59 | 0.37 | {'not_addressed': 10, 'supported': 16, 'not_supported': 2} |
| hybrid | 10 | llama3.1:8b-instruct-q4_K_M | no | 89.3% | 0.87 | 0.69 | {'not_addressed': 4, 'supported': 22, 'not_supported': 2} |
| hybrid | 10 | qwen2.5:14b | no | 85.7% | 0.83 | 0.61 | {'not_addressed': 5, 'supported': 21, 'not_supported': 2} |
| hybrid | 25 | gemma4:12b | no | 78.6% | 0.74 | 0.48 | {'not_addressed': 9, 'supported': 19} |
| hybrid | 25 | llama3.1:8b-instruct-q4_K_M | no | 89.3% | 0.87 | 0.67 | {'not_addressed': 6, 'supported': 22} |
| hybrid | 25 | qwen2.5:14b | no | 92.9% | 0.92 | 0.76 | {'not_addressed': 5, 'supported': 23} |
| hybrid | 50 | gemma4:12b | no | 85.7% | 0.82 | 0.65 | {'not_addressed': 6, 'supported': 20, 'not_supported': 2} |
| hybrid | 50 | gemma4:12b | yes | 85.7% | 0.82 | 0.68 | {'not_addressed': 9, 'supported': 19} |
| hybrid | 50 | llama3.1:8b-instruct-q4_K_M | no | 92.9% | 0.92 | 0.76 | {'not_addressed': 5, 'supported': 23} |
| hybrid | 50 | qwen2.5:14b | no | 89.3% | 0.87 | 0.70 | {'not_supported': 3, 'supported': 22, 'not_addressed': 3} |
| hybrid | 100 | gemma4:12b | no | 85.7% | 0.82 | 0.65 | {'not_addressed': 6, 'supported': 20, 'not_supported': 2} |
| hybrid | 100 | llama3.1:8b-instruct-q4_K_M | no | 96.4% | 0.96 | 0.88 | {'not_addressed': 4, 'supported': 24} |
| hybrid | 100 | qwen2.5:14b | no | 89.3% | 0.87 | 0.71 | {'not_addressed': 5, 'supported': 21, 'not_supported': 2} |
