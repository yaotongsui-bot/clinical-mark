# eICU test set: results (2026-11-17)

These are the pre-specified runs. A rerun with the case header (admission diagnosis) added to the
systems' records, decided after this scoring and listed as a deviation in `PAPER_PLAN.md`, is in
`results_eicu_dx/RESULTS.md`: the vote's lead over VeriFact is unchanged, the single-judge comparisons
move by several points.

Scored once against the frozen Claude reference (`reference/fact_gold_eicu/`, 965 fact atoms, 603
sentences, 100 cases, three answer sets) with `score_eicu.py`; all tables, CIs and paired tests are in
`SCORES.md` (numbers also in `SCORES.json`). Analysis plan as fixed in `PAPER_PLAN.md`: primary metric
sentence agreement (a sentence is wrong if any of its facts is Not Supported); 95% CIs by bootstrap over
cases. Every run has a verdict for every atom.

## Main result (all answer sets)

| System | Judge | Sentence agreement | Wrong sentences found | Flag precision | Atom agreement | Atom AC1 |
|---|---|---|---|---|---|---|
| This evaluator | cloud vote | **81.9%** (78.3-85.6) | 74.2% | 68.5% | 76.9% | 0.70 |
| This evaluator | deepseek-v4-pro | 69.0% (65.4-73.0) | 79.1% | 49.1% | 67.4% | 0.57 |
| VeriFact, cut at T | deepseek-v4-pro | 71.1% (67.1-75.6) | 22.5% | 55.4% | 67.6% | 0.60 |
| This evaluator | llama3.1:8b | 60.9% (56.9-65.1) | 73.1% | 41.6% | 62.4% | 0.51 |
| This evaluator, all to judge | llama3.1:8b | 48.9% (44.2-53.9) | 73.1% | 33.9% | 50.8% | 0.35 |
| VeriFact, cut at T | llama3.1:8b | 53.6% (49.3-57.9) | 36.8% | 28.9% | 57.3% | 0.46 |
| VeriFact, all records | llama3.1:8b | 53.2% (49.0-57.6) | 37.4% | 28.8% | 56.5% | 0.44 |

Paired, same items (sentence agreement, A minus B):

- Same local judge: evaluator vs VeriFact +7.3 points (+1.4 to +13.1).
- Same strong judge: evaluator vs VeriFact -2.2 (-7.1 to +2.7), no difference.
- Cloud vote vs VeriFact with the strong judge: +10.8 (+5.7 to +15.4).
- Vote vs a single strong judge in the evaluator: +12.9 (+9.4 to +16.3).
- Code checks (evaluator vs all-to-judge, llama): +11.9 (+7.7 to +16.2).
- Time cut in VeriFact: +0.3 (-2.1 to +2.8).

## What it shows

1. The evaluator finds most wrong statements, with every judge (73-79% of wrong sentences); VeriFact
   finds 22-37%. This holds on new data, a new database and three generators.
2. Agreement is a different matter. With a single judge the evaluator flags too much (flag precision
   34-49%): with deepseek-v4-pro, 207 Supported atoms were called Not Supported, against 80 under the
   vote. VeriFact's agreement with the strong judge comes from calling most things Supported. Only the
   vote combines high recall with acceptable precision, and only the vote beats VeriFact clearly.
3. Code checks are worth about 12 points with the local judge, as on the development set (about 10).
   Cutting VeriFact's records at T changes nothing, as on the development set.
4. The pattern is the same for each generator (per-generator tables in `SCORES.md`); the cloud vote's
   sentence agreement is 81-83% for all three.
5. Compared with the development set (atom agreement, VeriFact labels): the cloud vote dropped from 91.5%
   to 76.9%, VeriFact with the strong judge stayed at about 68% (68.3% to 67.6%). The gap between them
   shrank from about 23 to about 9 points.

## Caveats

- The reference is Claude's; the clinician check (20 cases, 199 atoms) has not started. Results may move
  once it is done.
- 54 atoms (5.6%) were labelled from the case header (APACHE admission diagnosis, unit type), which the
  generators saw but `cm/records_eicu.py` does not pass to either system; 21 more were decided by guideline
  rule 7, added while labelling. Without them the ordering is unchanged and the vote rises to 83.8% and
  84.4% sentence agreement (sensitivity tables in `SCORES.md`).
- A first look at the vote's 80 false Not Supported flags shows four recurring causes: a gap of
  several hours since the last ventilator record read as extubation (no extubation charted); "hypotension is fluctuating" read as current
  hypotension; drugs documented only in the treatment table (no administration record in eICU); and
  diagnoses that are only in the header. It also turned up at least one reference label that breaks the
  guideline's own rule 9 (magnesium 1.6 mg/dL labelled low; the fallback range starts at 1.6). The frozen
  reference is not changed; any correction goes to `reference/fact_gold_eicu/CHANGES.md` and is reported
  next to the frozen scores.
- Each sampled judge was run once; the plan's three repeats are not done. The local runs used three
  Ollama slots at once, so llama's outputs may differ slightly from single-request runs; the saved
  responses (`model_cache.jsonl`) reproduce these scores.

## Error analysis

Every false flag and miss of these runs, with causes for the cloud vote and VeriFact with deepseek-v4-pro, is in
`error_analysis/ERRORS.md` (`analyze_errors.py`, both result sets side by side). In brief: VeriFact misses
80-82% of Not Supported facts. About half of those misses are earlier values or ended states taken as current,
and a further 28 are treatment-table entries or orders taken as given. The vote's false flags come mostly from
evaluator rules: code checks testing another claim, drugs documented only in the treatment table, and the 6 h
median. In the first runs the case header also caused false flags.
