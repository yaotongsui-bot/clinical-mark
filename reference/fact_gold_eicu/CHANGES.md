# Changes to the eICU test reference after freezing

The reference was frozen on 2026-11-17 (checksums in `FROZEN.sha256`; frozen copy
`fact_gold_eicu_claude.frozen.csv`). No system output on the test cases had been opened before the
freeze. Any label changed after this point is listed here with the date, the key, the old and new
label, and the reason; scores are reported against both the frozen and the changed reference.

No changes yet.

## Doubts noted during the error analysis (2026-11-17; no label changed)

Found while coding the causes of the vote's and VeriFact's errors (`error_analysis/ERRORS.md`). Re-reading the
records suggests these frozen labels are wrong or arguable. They stay unchanged until they are decided with the
clinician check; if any is changed, it will be listed above with scores against both references.

| Key | Frozen label | What the records show |
|---|---|---|
| `deepseek-v4.1-flash\|E172015A2::07` ("MAP has fluctuated (58-112 mmHg)") | Not Supported ("no MAP charted") | 46 "MAP (mmHg)" rows from 01-01 23:36 to 01-02 23:00, 58 to 112 |
| `deepseek-v4.1-flash\|E172015A3::11` ("Hypomagnesemia is present") | Supported | Magnesium 1.6 mg/dL is inside rule 9's fallback range 1.6-2.6 |
| `deepseek-v4.1-flash\|E297175A1::03` ("FiO2 is 40%") | Supported (40% called latest) | Lab FiO2 45 at 01-01 13:16, later than the monitoring 40% at 02:13 |
| `qwen2.5-7b\|E521456A3::08` ("Delirium is potentially present") | Not Addressed ("no delirium assessment") | CAM-ICU "No" charted at 01-01 21:00, 22:00 and 01-02 12:00 |
| `qwen2.5-7b\|E1290248A1::02` ("SpO2 is fluctuating") | Not Supported (low values read as artefact) | SpO2 0-10 and 80 earlier, 99-100 then 94; whether the drops are artefacts is a judgement |
