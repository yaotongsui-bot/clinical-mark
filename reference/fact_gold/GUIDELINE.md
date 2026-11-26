# Fact gold standard for the 85 base cases: labelling guideline

Written 2026-11-13 by Claude (claude-opus-5-5) before labelling. The gold standard is Claude's
judgement, not a clinician's. It exists to compare the VeriFact baseline and this evaluator on equal
terms, so it must not depend on either system.

## Items

The 486 fact atoms of Claude's split standard (`reference/split_standard.csv`, kind = fact) for the
frozen deepseek answers (`input/mimic_triples_deepseek.json`). The atom text is judged; its source
sentence is shown only for context.

## Evidence

- All records of the current hospital admission that were known before the decision time T (event
  time before T and, where recorded, entry time before T; infusions and procedures running at T are
  kept with their start time, item and rate). This is the record set the AI's statement is about.
- The whole record set, not a retrieved subset. `build_sheets.py` writes one sheet per case that
  lists every record type in a condensed form (latest values, last-24-hour ranges, running and given
  treatments, orders, microbiology, procedures); `records/<case>.tsv` holds every row for search.
- Records after T are not evidence. Neither system's verdicts, retrieved records or reasons are
  opened while labelling.

## Labels (VeriFact's definitions)

- **Supported**: the records fully support the statement.
- **Not Supported**: the records address the statement but do not support it, support it only in
  part, or contradict it.
- **Not Addressed**: the records do not mention the subject of the statement.

## How statements are read

1. Present tense ("is", "currently", "ongoing") describes the patient at T and is judged on the most
   recent relevant records before T. If the most recent records contradict it, the label is Not
   Supported even when earlier records agree. "Recent" means within the 24 hours before T.
2. A treatment "currently being given / infused / on X":
   - continuous infusion: Supported if running at T; Not Supported if the records show it ended
     before T and it is not running at T, or if it runs at a different rate than stated;
   - intermittent or scheduled drug: Supported if administered in the 24 hours before T;
   - an order alone, without administration, is Not Supported for "being given" (the drug is
     addressed but not shown as given), and Supported for "is ordered";
   - oxygen and devices: judged on the latest device and flow entries before T.
3. Mechanical ventilation and its settings: Supported if invasive ventilation is charted in the
   latest entries before T (ventilator mode or settings, endotracheal tube) with no later
   extubation or non-invasive device; each stated setting must match the latest charted value.
4. Numbers must match a recorded value at the relevant time within the stated precision (0.05
   matches 0.050004). A stated range must cover the recorded values it describes.
5. Findings ("hypokalemia", "WBC is elevated", "tachypnea"): judged on the most recent values,
   against the record's reference range when it has one, otherwise the usual adult range. Qualifiers
   count: "markedly" needs a large deviation, "borderline" and "low-normal" need values near the
   limit. A finding that the records neither measure nor mention is Not Addressed.
6. Diagnoses, history and judgements ("history of CHF", "antibiotics are needed") are Supported
   only when the records state them; a diagnosis is not inferred from a drug or a single value. If
   the records do not mention them, Not Addressed.
7. Alarm limits and device settings are records like any other; an alarm limit is not a measurement.

## Rules added while labelling (applied to every case)

8. A device or ventilator setting is current only if it was charted under the device in use at T.
   After extubation or a change of oxygen device, earlier ventilator settings (mode, PEEP, FiO2, rate,
   tidal volume) are Not Supported for a present-tense statement.
9. A reference range applies to its specimen: a venous pO2 is not judged against the arterial range.
10. A stated range ("FiO2 50-60%") is Supported when the latest value lies in it.
11. Calculated total CO2 from a blood gas counts as a bicarbonate value.
12. "Rising" needs the latest value to be the highest of the recent series.
13. "Repletion is active" or "X is ordered" is Supported by an active order; "being given" needs an
    administration or a running infusion (rule 2).
14. Past tense ("was recently on 2 L/min") is judged on the 24 hours before T.

## Output

`fact_gold_claude.csv`: atom_id, case_id, text, label, evidence (record times and values), note,
seen_before (1 if Claude had seen any system's verdict for this atom or case earlier in the
conversation, so the item may not be blind). Frozen once complete; changes after scoring are listed
in `CHANGES.md` with the reason.
