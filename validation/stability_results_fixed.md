# Test-retest stability: `results_fixed` vs `retest_fixed`

The second run has its own judge cache, filled when it was first run with an empty judge cache;
the atomizer output is shared. The comparison is between two independent judge runs under fixed
settings: it shows repeatability, not correctness.

- Items compared: 481 (only in first: 0, only in second: 0)

| Stratum | n | Identical labels | Gwet's AC1 |
|---|---|---|---|
| all items | 481 | 100.0% | 1.00 |
| method = deterministic | 52 | 100.0% | 1.00 |
| method = llm_panel | 29 | 100.0% | 1.00 |
| method = rule | 400 | 100.0% | 1.00 |
| item type = fact | 87 | 100.0% | 1.00 |
| item type = monitoring | 280 | 100.0% | 1.00 |
| item type = treatment | 114 | 100.0% | 1.00 |

## Items whose label changed

| Item | Method | First | Second |
|---|---|---|---|

Changes by method: {}
