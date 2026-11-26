# Fact reference for the eICU test set: labelling guideline

Written 2026-11-17, before any label and before any system output on the test cases was opened. The
reference is Claude's judgement; a clinician sample (`sample.json`, field `clinician_cases`) will check
it. It follows the development-set guideline (`reference/fact_gold/GUIDELINE.md`, rules 1-14) with
the eICU notes below.

## Items

Fact atoms of the evaluator's split (`results_eicu/<generator>/ours_vote/atoms`, plus the safety-net
premises), for the three answer sets (gpt-oss-120b, deepseek-v4.1-flash, qwen2.5-7b), in the cases
drawn in `sample.json`. Collected by `collect_atoms.py`, which never opens a verdict. Keys are
`generator|atom_id`, because the three answer sets share case ids. All atoms of one case are labelled
together, against one reading of that case's records.

## Evidence

- Every eICU record of the hospital stay known before T = unit admission + 24 h (event offset and,
  where the table has one, entry offset before T), as built by `cm/records_eicu.py`.
- `sheets/<case>.txt` lists every record type in condensed form; `records/<case>.tsv` holds every row
  for search (`peek.py`).
- No system output on test cases is opened while labelling: not `results_eicu/*/*/cases`,
  `verdicts.csv`, reports or logs beyond completion lines.

## Labels and reading rules

VeriFact's three labels and the development-set rules 1-14 apply unchanged (present tense means the
state at T, judged on the latest records; a setting is current only under the device in use at T; an
order is not an administration; findings judged on the latest values and the record's or the usual
adult range; qualifiers count; diagnoses and history only when stated).

## eICU notes

1. eICU has no medication administration record. A scheduled (non-PRN) order active at T is the
   record of the drug being given, so "currently receiving X" is Supported by it; a one-time order
   counts as a dose at its start; a PRN order shows only that the drug may be given. These are shown in
   the sheets as "Running at decision time (scheduled order ...)", "Given once" and "Order ... PRN".
2. Infusions are charted about hourly with the current rate. An infusion runs at T if its last rate
   before T is above 0 and was charted within 4 h of T; a rate of 0 means it was stopped.
3. Oxygen devices are free text in eICU; the sheets show the mapped device and the charted text
   ("Nasal cannula (charted: NC)"). Judge on the charted text when the mapping is doubtful.
4. Dates are synthetic (2100-01-01 is the day of unit admission); times of day are real.
5. Reference ranges: eICU labs have none; use the usual adult ranges (as in `rules/measures.json`
   fallback ranges) and unit-appropriate ranges for ionized calcium.
6. "Treatment documented: ..." rows (the eICU treatment table) record that a therapy was charted at
   that time; they support "X was given or started" at that time, not that X runs at T.

## Rules added while labelling (applied to every case)

Written down as they came up and applied back to the cases already labelled. Notes in `labels.txt`
name the rule where it decided the label.

7. Intermittent drugs and therapies (antibiotics, anticonvulsants, IV diuretic doses, hemodialysis,
   and similar) documented in the treatment table within the 24 hours before T support "currently
   being given" (development rule 2 with eICU note 6). Continuous infusions, drips and devices
   (drains, compression boots, EEG monitoring) need a running infusion row or a later record at T; a
   documentation row alone is Not Supported for "running" or "in place".
8. When infusion rows exist, they decide: an explicit rate of 0, or a last rate older than 4 hours
   with no active order, is Not Supported. An active scheduled order without any rate rows counts as
   given (eICU note 1).
9. Reference ranges follow the `rules/measures.json` fallback bounds, as on the development set:
   potassium 3.3-5.1 (3.3 and 5.1 are in range); glucose 70-100 (above 100 is hyperglycaemia; 70 is
   not hypoglycaemia). Blood pressure: hypertension needs SBP >= 140 or DBP >= 90 on the latest
   reading; hypotension needs SBP < 90 or MAP < 65 (MAP calculated from SBP and DBP when not charted).
10. A range stated as the present value ("SBP is 88-99") is Supported when the latest value lies in
    it (development rule 10); a range describing a period ("has fluctuated between 94% and 100%")
    must cover the recorded values of that period (development rule 4).
11. Qualifiers decide: "broad-spectrum", "as-needed", "bolus", "infusion", "via nasal cannula",
    "active" or "ongoing" bleeding, "tachy-" arrhythmia and "hypervolemic" are Not Supported when the
    records support the core but not the qualifier. A flow rate without a charted device does not
    support "nasal cannula".
12. "Risk of X" is Supported when X itself is documented (diagnosis or values) and Not Addressed when
    it is not. Judgements ("X is needed", "refractory", "possible", "suspected infection", "uremia",
    "fluid overload") are Not Addressed unless stated. A treatment-table problem category (for example
    "shock | vasopressors", "ventricular dysfunction | inotropic agent") counts as a statement of that
    problem; a category name such as "pain / agitation / altered mentation" is not a finding.
13. Oxygen and ventilation follow the latest device or flow entry: a later nasal cannula, room air,
    high-flow rate or FiO2 21% ends BiPAP, NIV or ventilator claims and their settings (development
    rule 8). Without a later entry, the last device or flow entry in the 24 hours before T stands if
    nothing contradicts it; an entry older than 24 hours does not show oxygen at T.

## Output

`labels.txt` lines: `key|S/NS/NA|evidence|note`. Rules 7-13 under "Rules added while labelling" above
were added during labelling. `finalize.py` checks coverage of the sampled atoms
and writes `fact_gold_eicu_claude.csv`, which is then frozen by checksum. Changes after scoring go to
`CHANGES.md` with the reason.
