## Reading

Numbers are given as first runs / with case header. Causes were coded by Claude for every false flag and miss of
the cloud vote and of VeriFact with deepseek-v4-pro (392 atom-run pairs on 307 atoms), from the atom, the
reference evidence and note, and the system's stated reason. The case records were opened where these did not
settle it (cases E172015, E297175, E454584, E521456). There is one cause per atom and run. Where the two
result sets gave different reasons, the cause fits the header run and the note says so. A single coder from the
model family that wrote the reference did this coding; no second coder has checked it.

**How the errors split.** VeriFact errs by missing: 163 / 159 of the 200 Not Supported facts (80-82%), against
41 / 45 false flags (5-6% of the rest). The vote misses 62 / 71 (31-36%) and false-flags 89 / 78 (10-12%).
Almost every vote miss is also a VeriFact miss (55 of 62, 65 of 71). VeriFact's errors recur across repeats
more often than the vote's: 93% against 79% of header-run errors recur in the same direction in all three repeats.

**VeriFact's misses come from reading the record as a history, not as a state at T.**

- An earlier value or an ended state accepted for a statement about the present: 86 / 83 misses, about half.
  Examples: hyperkalemia from potassium 6.3-6.9 hours earlier when the latest value is 4.2 (E3223097); infusions
  that stopped before T; BiPAP or ventilator settings charted before the patient moved to nasal cannula or
  high-flow oxygen.
- A treatment-table entry, an order or a placement taken as the treatment being given: 28 / 28. Examples:
  "milrinone" in the treatment table read as a running infusion, PRN orders read as given, and a pericardial
  drain placement read as a drain in place.
- Not Addressed for a statement the records address without showing (the reference's Not Supported): 18 / 19.
  Unchecked qualifiers ("active", "ongoing", "broad-spectrum", "variability"): 15 / 14. Retrieval that
  returned no relevant rows, for example "no blood pressure values" when only respiratory rate rows came back:
  13 / 13.
- By fact kind, VeriFact misses 83-84% of Not Supported presuppositions ("X is currently being given", "the
  patient is on ventilation"), against 22-31% for the vote. By topic it misses 88-93% of Not Supported
  ventilation and oxygen facts.

**VeriFact's few false flags** come mostly from comparing a stated range with every value in the record rather
than the recent ones: 21 / 21, for example "SBP 150-170s" rejected because of a 124 earlier in the stay.
Strict qualifiers ("persistent" read as every value elevated) account for 8 / 10, and missed rows for 8 / 9.

**The vote's false flags come from rules more than from judges.**

- The code check tested another claim: 19 / 19. "Fluctuating" or "intermittent" hypertension, tachycardia or
  hypoxemia was checked as the current state, and "MAP as low as 71" as "MAP is low". Diastolic pressure is
  not checked for "diastolic hypertension", and fingerstick glucose is not counted as glucose.
- A treatment documented in the treatment table within 24 h (guideline rule 7), or under an active scheduled
  order, was rejected for lack of an administration row, which eICU does not have: 18 / 23. Rule-7 facts are
  48% / 67% false-flagged by the vote.
- A different summary of the same values (6 h median against the latest value, or a code threshold such as
  SpO2 90%): 10 / 10. A ventilator charting gap read as extubation: 5 / 5.
- Judgement statements ("risk of", "possible", "is needed") that the reference leaves Not Addressed but the
  judges rejected against values: 6 / 8.
- Diagnoses only in the case header: 11 / 0. The header removes these.
- In the first runs, 6 false flags carry a vote reason about another statement, for example a reason about
  borderline glucose for "Sepsis is present" (E1829278). The header run has none. This was not traced to its
  source and needs a check of the judge prompt and the cached responses.

**The vote's misses** are mostly judged facts (44 / 53 of 62 / 71). An earlier value or ended state accounts for
20 / 27: the judges accept earlier device rows or ended infusions (15 / 22), and the code's value check accepts an
earlier matching value instead of the latest (5 / 5). The administration guard turns a judged "supported" into
Not Addressed for a statement the reference calls Not Supported (6 / 8). For code-checked facts, a 6 h median or
a 24 h count stands in for the latest value (7 / 7).

**Shared errors.** Most errors both systems make are the same misreading: an earlier value or ended state (18 /
23 shared misses) and documentation taken as given (5 / 7). The vote avoids most of VeriFact's misses through
code checks and the "running at decision time" rows. What remains is mostly judged facts about devices and
infusions whose stop the records show only indirectly (a later device row, a rate of 0, no charting for over 4 h).

**Reference labels in doubt.** Five atoms look wrongly or arguably labelled on re-reading:
`E172015A2::07` (MAP 58-112 is charted), `E172015A3::11` (magnesium 1.6 against the 1.6-2.6 range of rule 9),
`E297175A1::03` (a lab FiO2 of 45% is later than the 40% called latest), `E521456A3::08` (CAM-ICU "No" is
charted three times) and `E1290248A1::02` (SpO2 drops read as artefact). They are listed in
`reference/fact_gold_eicu/CHANGES.md`; the frozen reference is unchanged. Together they account for 5 / 5 vote
errors and 3 / 3 VeriFact errors.

**What this means for the comparison.** VeriFact's deficit is structural: it misses state changes and treats
documentation as administration, and these errors recur across repeats. Many of the vote's false flags come from
fixable evaluator rules: code checks that test a different claim, the 6 h median, the treatment-table rule and
the ventilator gap. These four causes account for 63 / 68 of its 151 / 149 errors (about 42-46%). They were found
on the test set, so any fix needs a new test set before it can be claimed.
