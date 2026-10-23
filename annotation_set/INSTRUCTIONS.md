# Annotation instructions

Each row of `annotations.csv` is one statement or action taken from an AI answer. Open the case's
chart in `charts/<case_id>.html` and label the row from the chart alone. Do not use outside medical
knowledge to decide what is true; decide what the record shows. Work independently of the other
annotators. Put your label in your own column (annotator_1, annotator_2 or annotator_3).

## fact rows: is the statement true for the patient at the decision time?

- supported: the records before the decision time show it is true.
- not_supported: the records before the decision time show it is false.
- not_addressed: the records do not show either way (including vague statements).

## treatment rows: did the clinicians do what the AI suggested, after the decision time?

- supported: the clinicians recorded the same treatment (same drug or treatment class, same direction:
  start / continue / stop / adjust).
- not_supported: the clinicians did something conflicting for the same goal (a different drug of the
  same class, the opposite direction, or for example extubation instead of continued ventilation).
- not_addressed: no recorded clinician action corresponds to the suggestion.

## monitoring rows: was the suggested measurement or assessment recorded after the decision time?

- supported: it was measured or charted after the decision time.
- not_addressed: it was not, or the chart cannot show it (for example "assess for causes of ...").

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
gave it: vital (must not be missed) or okay. Using the chart:

- tier_should_be: vital, okay or routine.
- ai_answer_addresses_it: yes, partly or no, judged from the AI answer shown in the row.

The last row of each case asks for vital treatments the clinicians gave that are missing from the list.
