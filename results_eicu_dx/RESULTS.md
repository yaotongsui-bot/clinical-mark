# eICU test set with the case header in the records (2026-11-17)

Rerun of all 21 setups after the adapter change listed in `PAPER_PLAN.md` ("Deviations"): the systems now
also see the case header (ICU unit, sex and age, APACHE admission diagnosis) as three rows at unit
admission, as the generators and the test reference did. Same atoms, judges and settings; the first runs'
saved responses answered every request that did not change. Scored against the same frozen reference
with `score_eicu.py`; full tables in `SCORES.md`. The pre-specified analysis remains `results_eicu/`.

## First runs and rerun side by side (all answer sets)

| Run | Sentence agreement, first | Sentence agreement, with header | Atom agreement, first | Atom agreement, with header | Wrong sentences found, with header |
|---|---|---|---|---|---|
| Evaluator, cloud vote | 81.9% | 81.8% (78.1-85.1) | 76.9% | 79.0% | 70.3% |
| Evaluator, deepseek-v4-pro | 69.0% | 75.1% (71.3-79.0) | 67.4% | 74.5% | 67.6% |
| VeriFact cut at T, deepseek-v4-pro | 71.1% | 71.0% (66.9-75.3) | 67.6% | 70.4% | 24.2% |
| Evaluator, llama3.1:8b | 60.9% | 61.7% (57.3-66.3) | 62.4% | 63.8% | 72.0% |
| Evaluator all to judge, llama3.1:8b | 48.9% | 46.8% (42.0-51.7) | 50.8% | 50.2% | 71.4% |
| VeriFact cut at T, llama3.1:8b | 53.6% | 56.1% (52.0-60.5) | 57.3% | 61.1% | 30.8% |
| VeriFact all records, llama3.1:8b | 53.2% | 54.4% (50.2-58.8) | 56.5% | 59.2% | 30.8% |

Paired sentence agreement in the rerun (first runs in brackets):

- Cloud vote vs VeriFact with the strong judge: +10.8 (+6.1 to +14.9) [+10.8].
- Same strong judge, evaluator vs VeriFact: +4.1 (-0.0 to +8.4) [-2.2].
- Same local judge, evaluator vs VeriFact: +5.6 (-0.7 to +11.6) [+7.3, +1.4 to +13.1].
- Code checks (llama): +14.9 (+10.6 to +19.4) [+11.9].
- Vote vs single strong judge: +6.6 (+4.1 to +9.2) [+12.9].

## Where the changes come from

| Run | 54 header atoms right, first to rerun | Other 911 atoms: verdicts that changed | Other atoms right, first to rerun |
|---|---|---|---|
| Cloud vote | 14 to 48 | 34 | 728 to 714 |
| Evaluator, deepseek-v4-pro | 18 to 45 | 117 | 632 to 674 |
| VeriFact, deepseek-v4-pro | 15 to 45 | 30 | 637 to 634 |
| Evaluator, llama | 13 to 24 | 59 | 589 to 592 |
| Evaluator all to judge, llama | 14 to 24 | 82 | 476 to 460 |
| VeriFact cut, llama | 15 to 47 | 51 | 538 to 543 |
| VeriFact all records, llama | 16 to 42 | 48 | 529 to 529 |

- With the header, every system gets most diagnosis claims right (the llama judge inside the evaluator
  least often, 24 of 54).
- On the other 911 atoms nothing about the evidence changed, yet verdicts moved: three added rows shift
  retrieval and the judges' context. The single strong judge in the evaluator changed 117 verdicts (13%),
  the vote 34 (4%). Most of that run's gain (+42 of +69 atoms) is this movement, not the header.

## What it means

1. The headline result holds: the cloud vote beats VeriFact with the same strong judge by about 11
   points of sentence agreement in both runs, and the evaluator finds 68-72% of wrong sentences against
   VeriFact's 24-31%.
2. Comparisons between single judges are sensitive to the records they are given: the same-judge
   differences moved by 2 to 6 points between two runs that differ by three rows per case. The repeats
   below show that this is not run-to-run noise: within one configuration they hold within 1-2 points.
3. The code checks' contribution (about 12-15 points with the local judge) holds in both runs.

## Three repeats (with the header; `REPEATS.md`, `score_repeats.py`)

Repeats 2 and 3 (`results_eicu_dx_r2/`, `results_eicu_dx_r3/`) send every model request again with a
shifted seed (`CLINICAL_MARK_REPEAT`); records, retrieval, prompts and temperature are unchanged. The
evaluator's judges run at temperature 0, so their repeats show the serving's own variation; VeriFact's
judge samples at 0.1. The local runs shared three Ollama slots.

| Run | Sentence agreement, repeats 1 / 2 / 3 | Mean (95% CI) | Atoms with a verdict that changed in some repeat |
|---|---|---|---|
| Evaluator, cloud vote | 81.8 / 82.6 / 82.6 | **82.3%** (79.1-85.3) | 5.3% |
| Evaluator, deepseek-v4-pro | 75.1 / 76.0 / 76.6 | 75.9% (72.4-79.3) | 13.0% |
| VeriFact cut at T, deepseek-v4-pro | 71.0 / 71.3 / 71.0 | 71.1% (67.1-75.4) | 5.0% |
| Evaluator, llama3.1:8b | 61.7 / 60.9 / 60.2 | 60.9% (56.7-65.1) | 3.7% |
| VeriFact cut at T, llama3.1:8b | 56.1 / 56.6 / 56.6 | 56.4% (52.4-60.7) | 4.5% |
| VeriFact all records, llama3.1:8b | 54.4 / 55.2 / 55.9 | 55.2% (51.1-59.4) | 5.1% |
| Evaluator all to judge, llama3.1:8b | 46.8 / 47.3 / 46.8 | 46.9% (42.2-51.9) | 5.8% |

Method comparisons, sentence agreement A minus B, mean of the three repeats (95% CI; per repeat):

- Cloud vote vs VeriFact with the strong judge: **+11.2** (+6.7 to +15.6; +10.8 / +11.3 / +11.6).
- Same strong judge, evaluator vs VeriFact: +4.8 (+0.3 to +9.2; +4.1 / +4.6 / +5.6).
- Same local judge, evaluator vs VeriFact: +4.5 (-1.3 to +10.1; +5.6 / +4.3 / +3.6), not significant.
- Code checks (llama, evaluator vs all to judge): +14.0 (+9.5 to +18.1).
- All to judge vs VeriFact, llama: -9.5 (-15.9 to -3.7): the evaluator's retrieval and prompt without its
  code checks do worse than VeriFact.
- Vote vs single strong judge: +6.4 (+4.4 to +8.6). VeriFact's time cut: +1.2 (-1.5 to +4.0).

What the repeats add:

1. Every setup's sentence agreement stays within 1.5 points over three repeats, although individual
   verdicts move (13% of atoms for the single deepseek-v4-pro judge even at temperature 0, 4-6% for the
   others). Flips in both directions cancel out at this sample size.
2. The vote's lead over VeriFact (+11 points) and the code checks' contribution (+14) are stable and
   clearly above zero. The same-judge advantage of the evaluator is smaller, about 4.5-5 points, and
   only borderline (strong judge) or not significant (local judge).
3. The larger swings seen between the first runs and the header rerun therefore come from what the
   judges are shown, not from repeat noise: same-judge results depend on the retrieved context.

## Error analysis

Every false flag and miss of these runs, with causes for the cloud vote and VeriFact with deepseek-v4-pro, is in
`error_analysis/ERRORS.md` (`analyze_errors.py`, both result sets side by side). In brief: VeriFact misses
80-82% of Not Supported facts. About half of those misses are earlier values or ended states taken as current,
and a further 28 are treatment-table entries or orders taken as given. The vote's false flags come mostly from
evaluator rules: code checks testing another claim, drugs documented only in the treatment table, and the 6 h
median. In the first runs the case header also caused false flags.
