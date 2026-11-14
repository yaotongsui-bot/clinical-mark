# VeriFact baseline vs this evaluator on the 85 cases (main comparison)

2026-11-13. Same 486 fact atoms (Claude's split standard) in every run; only the fact checking
differs. Reference: `reference/fact_gold/fact_gold_claude.csv`, Claude's labels on the full records
before T, written before any of these verdicts were opened and frozen (sha256 in
`reference/fact_gold/FROZEN.sha256`): 353 Supported, 131 Not Supported, 2 Not Addressed. Full tables
and every paired difference: `score_gold.md`.

## Ladder with the same local judge (llama3.1:8b-instruct-q4_K_M)

| Step | Run | Change | Agreement (95% CI) | AC1 | MCC | Not Supported found | False Not Supported |
|---|---|---|---|---|---|---|---|
| 0 | `vf_hybrid_nocut` | VeriFact as published (whole admission) | 59.3% (54.7-64.0) | 0.49 | -0.01 | 32/131 | 85 |
| 1 | `vf_hybrid_cut` | + records cut at T | 62.3% (57.8-66.7) | 0.54 | 0.00 | 24/131 | 64 |
| 1b | `vf_rerank_cut` | + VeriFact's reranker | 62.8% (58.2-67.5) | 0.54 | 0.02 | 28/131 | 64 |
| 2 | `vf_rules_cut` | step 1 + this evaluator's rules in VeriFact's prompt | 58.2% (53.9-62.8) | 0.45 | 0.17 | 80/131 | 149 |
| 3 | `results_ours85_llama8b_alljudge` | this evaluator's retrieval, context and prompt; every fact to the judge | 68.1% (64.2-72.2) | 0.60 | 0.23 | 45/131 | 41 |
| 4 | `results_ours85_llama8b` | + code checks, rule labels, administration guard | 78.6% (74.7-82.1) | 0.73 | 0.49 | 76/131 | 31 |

"False Not Supported": gold Supported judged Not Supported.

Paired differences (percentage points, 95% CI): time cut +3.1 (-0.6 to +6.4); reranker +0.4 (-2.3
to +3.3); rules added to VeriFact's prompt -4.1 (-10.1 to +1.9); this evaluator's retrieval and
prompt vs VeriFact (step 3 minus step 1) +5.8 (+0.8 to +10.7); code checks and guard (step 4 minus
step 3) +10.5 (+6.8 to +13.8); whole method (step 4 minus step 1) +16.3 (+11.5 to +21.0).

## Strong judges

| Run | Judge | Agreement (95% CI) | AC1 | MCC | Not Supported found |
|---|---|---|---|---|---|
| `vf_pro_cut` | VeriFact, deepseek-v4-pro (cloud), cut | 68.3% (64.2-72.8) | 0.62 | 0.08 | 15/131 |
| `vf_pro_rerank_cut` | same + reranker | 66.3% (62.1-70.8) | 0.59 | 0.06 | 15/131 |
| `results_final_claude_split` | this evaluator, three-model cloud vote | 88.1% (85.2-90.9) | 0.85 | 0.72 | 95/131 |

This evaluator minus VeriFact with a strong judge: +19.8 (+15.2 to +24.1). This evaluator with the
local 8B judge still beats VeriFact with deepseek-v4-pro: +10.3 (+5.3 to +14.6).

## By statement type (Llama 8B ladder, percent agreement)

| Group | n | Step 1 VeriFact cut | Step 2 + rules | Step 3 all to judge | Step 4 full |
|---|---|---|---|---|---|
| Ventilation and settings | 161 | 51.6% | 43.5% | 67.7% | 80.7% |
| "Currently given" treatments | 107 | 66.4% | 59.8% | 76.6% | 72.0% |
| Findings, values, other | 218 | 68.3% | 68.3% | 64.2% | 80.3% |

## Reading

- VeriFact's weakness here is Not Supported: it accepts statements the records contradict, mostly
  ventilation statements after extubation and treatments stopped before T. The time cut and the
  reranker do not change this; a stronger judge raises agreement but finds even fewer contradictions
  (15 of 131).
- Writing this evaluator's rules into VeriFact's prompt does not transfer the gain to a small model:
  it finds many more contradictions (80 vs 24) but raises 149 false ones, so agreement does not
  improve. Rules stated in a prompt are applied unreliably by an 8B model.
- This evaluator's retrieval and context (records with ids, types, "running at decision time", the
  latest oxygen device rows pinned to ventilator statements) add about 6 points over VeriFact with
  the same prompt-only judging; the code checks add about 10 more, mostly on findings and values
  (64% to 80%) and ventilation (68% to 81%).
- The administration guard costs a little on "currently given" treatments with the 8B judge (77% to
  72%): it downgrades judged statements to Not Addressed when no administration is found, which the
  reference sometimes labels Supported or Not Supported. Worth checking item by item.

## Administration guard, checked item by item

The guard turns a judged "being given" Not Supported into Not Addressed unless a cited record shows
the treatment withheld or stopped. In the two evaluator runs it fired 14 times and never corrected an
error against the reference: 6 times it turned a wrong Not Supported (reference Supported) into Not
Addressed, still wrong; 8 times it turned a correct Not Supported into Not Addressed.

Two defects explained 3 of the 8, both fixed (tests in `tests/test_all_judge.py`):

- `rules/treatments.json`: the routine-care pattern `nasal` also matched "nasal cannula", so
  "receiving oxygen via nasal cannula" was not recognised as oxygen and an O2 device "None" row did
  not count as oxygen off. Now `nasal(?! cannula)`. A side effect: the safety net no longer adds a
  duplicate "receiving supplemental oxygen" premise in 3 cases, so the fixed runs have 483 atoms.
- `cm/ground.py`: a rate infusion of the drug that ended before T, with none running at T, now
  counts as evidence it was stopped (an insulin drip ended two hours before T).

Rescored from cached verdicts (12 new model calls), on the 483 shared atoms: cloud vote 88.0% to
88.8% (3 guard errors and 1 other item fixed, none broken; `results_final_claude_split_guardfix`);
Llama 8B 78.7% unchanged (`results_ours85_llama8b_guardfix`). These fixes were made after seeing
the reference, so the frozen pre-fix numbers above remain the main result.

What is left is mostly a difference in definitions, not a bug. Of 11 reference Not Supported atoms
the fixed cloud run leaves unscored, 6 are "being given" statements where only an order, a catheter
or a past dose exists (the evaluator: an order alone is Not Addressed; VeriFact's definition and the
reference: addressed but not supported is Not Supported), and 3 are vague statements the evaluator
labels unverifiable by rule ("SpO2 is borderline", "sedation is fluctuating") while the reference
judges them against the latest values. These cost the evaluator points under VeriFact's definitions,
so on this point the reference does not favour it.

## Aligning this evaluator's labels with VeriFact (`--labels verifact`)

After the guard check, the evaluator was given VeriFact's three labels and definitions
(`prompts/fact_judge_vf.txt`; no `unverifiable`; a treatment the records mention but do not show
given is Not Supported). Rescored on the 483 atoms shared with the guard-fixed runs (post-hoc, like
the guard fixes):

| Run | Judge | Own labels (guard-fixed) | VeriFact labels | Difference (95% CI) | Not Supported found | False Not Supported |
|---|---|---|---|---|---|---|
| full evaluator | cloud vote | 88.8% | **91.5%** (89.0-93.8) | +2.7 (+1.0 to +4.3) | 97 -> 108 of 130 | 7 -> 13 |
| full evaluator | Llama 8B | 78.7% | 75.8% (71.8-79.5) | -2.9 (-6.0 to +0.2) | 76 -> 87 | 31 -> 70 |
| all to judge | Llama 8B | 68.1% | 64.4% (60.0-68.7) | -3.7 (-8.1 to +0.8) | 45 -> 77 | 41 -> 117 |

With strong judges the aligned definitions help (AC1 0.86 to 0.89, MCC 0.73 to 0.79). With the 8B
judge they hurt: the stricter wording ("supports only in part is Not Supported", qualifiers judged
against values) makes it reject statements its own reasons support ("the records show magnesium
sulfate was administered, but the statement says it has been administered"). The new false Not
Supported verdicts all come from the judge, none from the guard. This repeats the step 2 finding:
an 8B model applies stricter prompt rules unreliably.

Against VeriFact with matched judges, the aligned evaluator stays ahead: Llama 8B 75.8% vs VeriFact
62.3% (+13.5, 95% CI +8.3 to +18.2); cloud vote 91.5% vs VeriFact with deepseek-v4-pro 68.3% (+23.2,
+18.8 to +27.5).

Recommended configuration: VeriFact labels with the cloud vote (`--labels verifact`); this
project's own labels if only a small local judge is available.

## Limits (state these with the numbers)

1. The reference is Claude's, not clinicians'. Its rules (latest state wins, a setting is current only
   under the current device, an order is not an administration) resemble rules Claude earlier wrote
   into this evaluator, so the reference may favour it. Step 2 shows that writing the same rules into
   VeriFact's prompt does not by itself reproduce the agreement, which argues against a pure
   definition effect, but the reference's agreement with clinicians is unknown.
2. 58 atoms in 9 cases were not blind (Claude had seen an earlier verdict); excluding them changes
   nothing material (88.3% vs 67.3% for the two strong-judge runs on the 428 unseen atoms).
3. Runs use Claude's split, not VeriFact's own decomposition (end-to-end comparison deferred).
4. Only 2 gold Not Addressed atoms: metrics for that label are not meaningful.
5. One sample per run; VeriFact's judge samples at temperature 0.1, this evaluator decodes greedily.
