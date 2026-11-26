# Pooled samples

1000 bootstrap resamples of cases (all samples share the resampled case set).

| Metric | Pooled samples (3, 95% CI) | results_open_deepseek_s1 | results_open_deepseek_s2 | results_open_deepseek_s3 | Baseline results_deepseek (95% CI) |
|---|---|---|---|---|---|
| AI suggestions per case | 10.00 (10.00 to 10.00) | 10.00 | 10.00 | 10.00 | 3.00 (3.00 to 3.00) |
| Fact accuracy | 79.6% (76.8% to 82.4%) | 78.8% | 79.9% | 80.2% | 76.6% (71.2% to 81.7%) |
| not_supported facts per case | 1.44 (1.20 to 1.69) | 1.48 | 1.40 | 1.44 | 0.73 (0.54 to 0.94) |
| Cases with a not_supported fact | 71.8% (64.7% to 78.8%) | 69.4% | 72.9% | 72.9% | 51.8% (41.2% to 62.4%) |
| Treatment agreement (strict) | 59.2% (53.0% to 64.6%) | 60.2% | 55.9% | 61.5% | 75.0% (66.7% to 83.0%) |
| Treatment agreement (partial counts as agreeing) | 64.2% (57.7% to 70.0%) | 64.9% | 61.2% | 66.7% | 77.1% (69.0% to 84.7%) |
| Vital recall | 46.4% (40.7% to 52.7%) | 46.7% | 44.4% | 48.1% | 22.9% (18.6% to 26.9%) |
| Vital recall, first 3 suggestions | 27.1% (23.4% to 31.3%) | 26.2% | 25.2% | 29.9% | 22.9% (18.6% to 26.9%) |
| All recall | 34.6% (31.1% to 38.0%) | 35.9% | 32.0% | 35.9% | 16.4% (14.2% to 18.5%) |
| All recall, first 3 suggestions | 13.5% (11.6% to 15.4%) | 13.6% | 12.8% | 14.1% | 16.4% (14.2% to 18.5%) |
