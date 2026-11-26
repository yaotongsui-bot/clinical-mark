# Annotation instructions

Each row of `annotations.csv` is one statement or action taken from an AI answer, or one abnormality
the clinicians treated. Open the row's chart, `charts/<chart>.html`, and label the row from the chart
alone. Do not use outside medical knowledge to decide what is true; decide what the record shows.
Work independently of the other annotators. Put your label in your own column (annotator_1,
annotator_2 or annotator_3). The allowed labels for each row are in its `labels` column.

## fact rows: is the statement true for the patient at the decision time?

- supported: the records before the decision time show it is true. A stated value counts as true
  when a recorded value before the decision matches it.
- not_supported: the records before the decision time show it is false.
- unverifiable: the records show neither way, or the statement is too vague to check.

## treatment rows: did the clinicians do what the AI suggested, after the decision time?

- agrees: the clinicians recorded the same treatment class in the same direction (start / continue /
  stop / increase / decrease). Another drug of the same class for the same aim also agrees.
- disagrees: no recorded clinician action corresponds to the suggestion, or the clinicians went the
  opposite way (the AI says stop and the drug continues; the AI says increase and the dose went
  down; the AI says change a dose and no change is recorded; continued ventilation vs extubation).
- undetermined: the suggestion names no concrete treatment ("optimize management"), its condition
  did not occur, or the chart cannot show it.

## monitoring rows: was the suggested measurement or assessment recorded after the decision time?

- agrees: it was measured or charted after the decision time.
- disagrees: it could have been charted but was not.
- undetermined: the chart cannot show it (for example "assess for causes of ...").

## finding rows: does the AI answer mention this abnormality?

Each row names an abnormality present before the decision that the clinicians then treated (the
treatment is given). Read the AI answer at the top of the chart.

- mentioned: the answer states or takes for granted something about this measure, right or wrong
  (a value, high/low, or a diagnosis such as "hypocalcemia"). A suggestion to monitor it alone does
  not count.
- omitted: the answer says nothing about it.

Use the `notes` column for anything unclear. After all three annotators finish, rows where all three
labels differ are settled in the `adjudicated` column by discussion.

## Optional, one reviewer: atomization_review.csv

Each row is one sentence of an AI answer and the items the evaluator extracted from it
(`[fact]`, `[action]`, `[goal]`). Answer yes / no:

- all_checkable_statements_extracted: every fact the sentence states or takes for granted, and every
  action it suggests, is among the extracted items.
- extracted_items_faithful: each extracted item says what the sentence says (no added certainty, no
  lost negation or condition).

## Optional, one reviewer: treatment_reference_review.csv

Each row is a treatment class the clinicians used after the decision time, with the tier the rules
gave it: vital (key treatment, must not be missed) or okay. Using the chart:

- tier_should_be: vital, okay or routine.
- ai_answer_addresses_it: yes, partly or no, judged from the AI answer shown in the row.

The last row of each chart asks for vital treatments the clinicians gave that are missing from the list.
