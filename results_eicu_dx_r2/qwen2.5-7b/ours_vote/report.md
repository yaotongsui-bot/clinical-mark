# Evaluation of AI clinical suggestions against patient records

- Input: `eicu_triples_qwen2.5-7b.json`; 100 cases, 2.99 AI suggestions per case on average.
- Models: atomizer `deepseek-v4-pro:0813:cloud`; judge panel `deepseek-v4-pro:0813:cloud`, `minimax-m3.1-flash:cloud`, `glm-5.3:cloud` (majority vote; reasoning mode: none); 396 new model calls, 130 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 27.7% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 173 |
| supported / not_supported / not_addressed / unverifiable | 104 / 58 / 11 / 0 |
| Fact accuracy = supported / (supported + not_supported) | 64.2% |
| Cases with at least one not_supported fact | 44 / 100 |
| Omitted findings: abnormalities the clinicians treated that no AI fact mentions | 0 / 0 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 51 | 82.4% | {'supported': 42, 'not_supported': 9} |
| presupposed by an action | 110 | 55.4% | {'supported': 56, 'not_supported': 45, 'not_addressed': 9} |
| clinical judgment | 12 | 60.0% | {'supported': 6, 'not_supported': 4, 'not_addressed': 2} |
| vague | 0 | - | {} |

## 2. How close is the AI to what clinicians did?

Target (same class, or the drug the AI named) and direction (continue / stop / adjust) are decided by code; suggestions the rule file cannot classify go to the judge panel.

| Metric | Value |
|---|---|
| Treatment action atoms | 217 |
| Labels | {'not_done': 100, 'condition_not_met': 69, 'vague_target': 18, 'match': 16, 'unobservable': 14} |
| Agreement (strict) = match / (match + partial_match + not_done) | 13.8% |
| Agreement (lenient) = (match + partial_match) / same | 13.8% |

Monitoring/assessment atoms: 209 (reported separately, not part of agreement): {'performed': 124, 'not_performed': 31, 'unobservable': 54}; performed rate among observable items 80.0%. 2 'goal' atoms with no concrete action are not scored.

## 3. What did the AI miss?

Omitted treatments: 0 of the 0 treatment classes the clinicians used (0 of 0 vital). Recall below is the share not omitted.

Vital = a class the rule file marks vital, or one whose indication was present at the decision time (for example low potassium followed by potassium chloride). Other non-routine classes are okay.

| Recall | All suggestions (micro / per-case) | First 3 suggestions only (micro / per-case) |
|---|---|---|
| vital (0/0) | - / - | - / - |
| okay (0/0) | - / - | - / - |
| all (0/0) | - / - | - / - |

0 clinician actions answered an abnormality present at the decision time; the AI missed 0 of them. Most often missed vital classes: 

### Problem-linked omissions

| Case | Clinicians gave | Indication at the decision time | AI suggestions |
|---|---|---|---|

## 4. not_supported facts

| Case | AI sentence | Atomic fact | Kind | Evidence |
|---|---|---|---|---|
| E297175 | Monitor patient's respiratory status closely due to ongoing respiratory distress. | Respiratory distress is ongoing. | stated outright | The records show respiratory rates ranging from 15 to 26 breaths per minute, with the most recent value at 21:00 being 23. While there is evidence of respiratory treatments (bronchodilators, non-invasive ventilation), the recorded respiratory rates do not consistently indicate ongoing distress, and no record explicitly states 'respiratory distress' is ongoing. |
| E395323 | Continue vancomycin and piperacillin/tazobactam for suspected sepsis. | Vancomycin is currently being given. | presupposed by an action | The records document vancomycin as a treatment (R14), but there is no medication administration record showing it was given within 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E395323 | Continue vancomycin and piperacillin/tazobactam for suspected sepsis. | Piperacillin/tazobactam is currently being given. | presupposed by an action | The records mention piperacillin/tazobactam only as a documented treatment (R13), but there is no medication order or administration record showing it was given within 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E405746 | Continue labetalol for hypertension management. | Labetalol is currently being given. | presupposed by an action | The records show an active PRN order for labetalol (R10) and a treatment documentation mentioning labetalol (R34), but there is no administration record of labetalol being given in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E405746 | Continue labetalol for hypertension management. | Hypertension is present. | clinical judgment | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E467819 | Continue monitoring blood pressure and adjust nicardipine infusion as needed. | Nicardipine infusion is currently being given. | presupposed by an action | The most recent nicardipine administration record (R50) shows an infusion that ended at 00:00 on 2100-01-02, which is over an hour before the decision time of 01:43. There is no record of a nicardipine infusion running at the decision time. |
| E467819 | Administer oral enalapril as ordered. | Oral enalapril is ordered. | presupposed by an action | The records document enalapril as a treatment for hypertension, but there is no medication order for oral enalapril. The statement that it is 'ordered' is therefore not supported. |
| E521456 | Continue mechanical ventilation with tidal volume 300 mL and PEEP 5 cmH2O. | PEEP is 5 cmH2O. | stated outright | The most recent PEEP records before the decision time show a setting of 7 cmH2O (R45, R46, R47), not 5 cmH2O. The patient remains on a ventilator (R51, R52), so the statement about PEEP being 5 is contradicted by the latest values. |
| E521456 | Administer 10 mL of magnesium sulfate intravenously for potential delirium. | Delirium is potentially present. | clinical judgment | The records include CAM-ICU delirium assessments at 21:00, 22:00, and 12:00, all with a Delirium Score of 'No', which directly contradicts the statement that delirium is potentially present. |
| E664474 | Continue non-invasive ventilation to maintain adequate oxygenation and ventilation. | The patient is currently on non-invasive ventilation. | presupposed by an action | The only non-invasive ventilation record is a treatment documentation entry from 2100-01-01 10:32 (~13.5 h before the decision time); there is no administration or 'running at decision time' record confirming NIV is currently in use at 2100-01-02 00:05. |
| E733082 | Monitor blood glucose levels closely due to recent high readings and risk of hypoglycemia. | There is a risk of hypoglycemia. | clinical judgment | The records show multiple glucose measurements, all of which are elevated (153-216 mg/dL), not low. There is no evidence of hypoglycemia or a risk of it; the data actually indicates hyperglycemia. |
| E733082 | Administer IV fluids to maintain adequate hydration and blood pressure support. | Hydration is inadequate. | presupposed by an action | The records show multiple administrations of IV fluids (sodium chloride) including a running infusion at the decision time, indicating hydration was being actively provided, so the statement that hydration is inadequate is not supported. |
| E733082 | Administer IV fluids to maintain adequate hydration and blood pressure support. | Blood pressure support is needed. | presupposed by an action | The most recent blood pressure readings before the decision time are 104, 121, and 120 mmHg systolic, which are within normal limits and do not indicate a need for blood pressure support. |
| E850469 | Continue aggressive fluid resuscitation to maintain adequate perfusion. | Aggressive fluid resuscitation is currently being given. | presupposed by an action | The records show a single 1000 mL normal saline bolus given on 2100-01-01 at 12:27 and a treatment note for aggressive volume resuscitation at 14:20, but no fluid administration is documented in the 24 hours before the decision time of 2100-01-02 13:47. Therefore, the statement that aggressive fluid resuscitation is currently being given is not supported. |
| E1056063 | Continue oxygen therapy with nasal cannula at 2 L/min to maintain adequate oxygen saturation. | Oxygen therapy with nasal cannula at 2 L/min is currently being given. | presupposed by an action | The records document oxygen therapy via nasal cannula (R6) and O2 flow of 2 L/min at several times on 2100-01-01, but the most recent O2 flow record is from 17:00 on 2100-01-01, more than 24 hours before the decision time. No administration or flow record within 24 hours before 2100-01-02 10:15 confirms current delivery at 2 L/min. |
| E1064283 | Administer potassium chloride PO to address low potassium levels. | Potassium is low. | stated outright | Latest potassium 4.1 mmol/L at 2100-01-02 10:38:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E1065859 | Monitor blood glucose levels closely due to persistent hyperglycemia. | Hyperglycemia is present. | stated outright | Latest glucose 96 mg/dL at 2100-01-02 19:40:00 (reference 70 to 100) is normal, not consistent with 'high'. |
| E1065859 | Continue intravenous fluid administration to maintain adequate blood pressure and volume status. | Intravenous fluids are currently being given. | presupposed by an action | The most recent IV fluid administration (R11) ended at 00:28 on 2100-01-02, over 20 hours before the decision time of 20:54. While treatment documentation (R12, R13) mentions IV fluid administration, there is no record of an infusion running at the decision time, so the statement that fluids are currently being given is not supported. |
| E1068212 | Continue pericardial drainage catheter monitoring. | Pericardial drainage catheter monitoring is currently being performed. | presupposed by an action | The records document placement of a pericardial drainage catheter (R16), but there is no record of ongoing monitoring of that catheter at or near the decision time. The statement that monitoring is currently being performed is therefore not supported. |
| E1071450 | Administer intravenous potassium chloride to correct hypokalemia. | Hypokalemia is present. | presupposed by an action | Latest potassium 4.1 mmol/L at 2100-01-01 13:50:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E1071450 | Continue inotropic support with milrinone. | Milrinone is currently being given. | presupposed by an action | The records mention milrinone only as a treatment documented at 03:34 on 2100-01-01, which is after the decision time of 02:03. There is no administration record of milrinone in the 24 hours before the decision time, so the statement that it is currently being given is not supported. |
| E1071450 | Continue inotropic support with milrinone. | The patient is currently receiving milrinone. | presupposed by an action | The records mention milrinone only as a documented treatment for shock (R28), but there is no medication order or administration record showing that milrinone was being given at the decision time. |
| E1090889 | Assess for potential causes of hypotension. | Hypotension is present. | presupposed by an action | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1099398 | Patient's blood pressure is fluctuating, with systolic readings as high as 202 mmHg and diastolic as low as 60 mmHg. Consider adjusting antihypertensive therapy. | Diastolic blood pressure is as low as 60 mmHg. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1117947 | Continue non-invasive ventilation to support respiratory function. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records contain a treatment documentation for non-invasive ventilation (R31), but it is dated 2100-01-01 07:31, which is over 23 hours before the decision time of 2100-01-02 06:58. There is no administration or 'Running at decision time' record for non-invasive ventilation within the 24 hours before the decision time to support the statement that the patient is currently on it. |
| E1171473 | Assess for signs of respiratory distress and adjust mechanical ventilation parameters as needed. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('Tidal Volume (set): 500 mL') was 6.8 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1173453 | Continue antibiotic therapy with vancomycin. | Vancomycin is currently being given. | presupposed by an action | The records document vancomycin as a treatment (R15), but there is no administration record (e.g., MAR Administered, Given, or Running at decision time) within the 24 hours before the decision time to support that it is currently being given. |
| E1177589 | Continue oxygen therapy with 2 L/min nasal cannula. | Oxygen therapy with 2 L/min nasal cannula is currently being given. | presupposed by an action | The most recent oxygen delivery record before the decision time (R48, 2100-01-02 06:00) shows an O2 L/% of 21, which corresponds to room air, not 2 L/min via nasal cannula. Earlier records from the previous day show 2 L/min, but the latest data contradicts the statement that it is currently being given. |
| E1287791 | Continue sedation at -1 RASS score. | The patient is currently receiving sedation. | presupposed by an action | The records show an active PRN order for lorazepam (a sedative) but no administration record within 24 hours before the decision time. The RASS scores indicate the patient is sedated (e.g., -1, -4), but these are measurements of sedation level, not evidence that a sedative medication was administered. Therefore, the statement that the patient is 'currently receiving sedation' is not supported by administration records. |
| E1290248 | Continue intravenous fluid administration to maintain hydration. | Intravenous fluids are currently being administered. | presupposed by an action | The records contain orders for intravenous sodium chloride (R17, R18) and documentation of intravenous fluid administration (R38, R39), but no administration record within 24 hours before the decision time or a 'Running at decision time' record for IV fluids. The only running medication is pantoprazole (R1), so current IV fluid administration is not confirmed. |
| E1496959 | Continue anticonvulsant therapy for seizure prevention. | Anticonvulsant therapy is currently being given. | presupposed by an action | The records document 'anticonvulsant' as a treatment category, but there is no medication order or administration record for a specific anticonvulsant drug at or before the decision time. Therefore, the statement that anticonvulsant therapy is currently being given is not supported by the records. |
| E1619343 | Administer intravenous vancomycin for suspected infection. | Infection is suspected. | presupposed by an action | The records show normal temperatures (98.0-98.8 F) before the decision time and only a mild elevation (100.9 F) after it. There is no documented diagnosis of infection, elevated white blood cell count in blood, or other direct evidence of infection in the supplied records. |
| E1636307 | Continue intravenous sedation and analgesia to maintain patient comfort. | Intravenous sedation is currently being given. | presupposed by an action | The only intravenous sedation administration record is propofol from 2100-01-01 02:15 to 17:08, which ended more than 24 hours before the decision time of 2100-01-02 00:42. No sedation administration is documented in the 24 hours before the decision time, so the statement that it is currently being given is not supported. |
| E1636307 | Continue intravenous sedation and analgesia to maintain patient comfort. | Intravenous analgesia is currently being given. | presupposed by an action | The records show orders for intravenous analgesics (HYDROmorphone, fentaNYL) and a documented narcotic analgesic treatment, but no administration of an intravenous analgesic within 24 hours before the decision time. The only intravenous analgesic administration (propofol) is a sedative, not an analgesic, and it ended at 17:08 on 2100-01-01, more than 7 hours before the decision time. |
| E1636307 | Assess patient for signs of respiratory distress and adjust mechanical ventilation settings if necessary. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 9.7 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1672915 | Continue intravenous insulin to manage glucose levels. | Intravenous insulin is currently being given. | presupposed by an action | The records show insulin lispro being administered subcutaneously (R20, R36), but there is no record of intravenous insulin administration. The statement specifically claims intravenous insulin is being given, which is not supported by the available records. |
| E1674875 | Continue intravenous sodium chloride to maintain fluid balance. | Intravenous sodium chloride is currently being given. | presupposed by an action | The most recent sodium chloride administration record (R49) shows an infusion that ended at 19:01 on 2100-01-02, over an hour before the decision time of 20:48. There is no record of sodium chloride being administered or running at the decision time. |
| E1705630 | Continue sedation at a reduced level. | Sedation is currently being given. | presupposed by an action | The records contain orders for lorazepam (a sedative) and documentation of sedative agents, but no administration of a sedative is recorded in the 24 hours before the decision time. The only administrations are haloperidol (over 24 hours prior), labetalol, and non-sedative medications. |
| E1739131 | Continue pain management with hydromorphone as needed. | Hydromorphone is currently being given. | presupposed by an action | The records show hydromorphone was administered at 06:59, 07:58, and 10:28 on 2100-01-01, but the decision time is 09:51 on 2100-01-02, more than 24 hours later. No administration record exists within 24 hours before the decision time, so the statement that it is currently being given is not supported. |
| E1790816 | Continue nitroglycerin infusion. | Nitroglycerin infusion is currently being given. | presupposed by an action | The nitroglycerin infusion record (R10) shows it ran from 2100-01-01 20:53 to 2100-01-02 15:12, which ended before the decision time of 2100-01-02 20:23. There is no administration record of nitroglycerin within 24 hours before the decision time or a 'Running at decision time' record for it. |
| E1823727 | Continue IV fluids and electrolyte management. | Electrolyte management is currently being given. | presupposed by an action | The records show administration of IV fluids (sodium chloride) and medications like insulin and dextrose, but there is no administration of any specific electrolyte replacement (e.g., potassium, magnesium, calcium) in the 24 hours before the decision time. The statement that 'electrolyte management is currently being given' is therefore not supported by the records. |
| E1823727 | Assess for signs of infection given leukocytosis. | Leukocytosis is present. | stated outright | Latest WBC 8.3 K/mm3 at 2100-01-02 10:00:00 (reference 4 to 11) is normal, not consistent with 'high'. |
| E1824650 | Wean off mechanical ventilation. | The patient is currently on mechanical ventilation. | presupposed by an action | The latest record before the decision (2100-01-02 15:35:00) reads 'O2 Delivery Device(s): None (charted: RA)'. |
| E1829278 | Administer intravenous Nicardipine to manage hypertension. | Hypertension is present. | presupposed by an action | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E1853162 | Increase oxygen flow to 4 L/min due to elevated systolic blood pressure and respiratory rate. | Respiratory rate is elevated. | stated outright | Median respiratory rate over the 6 h before the decision: 20 insp/min (1 readings), normal by the rule 'tachypnea RR > 20; bradypnea RR < 12'. |
| E1856821 | Continue norepinephrine infusion to maintain hemodynamic stability. | Norepinephrine infusion is currently being given. | presupposed by an action | The records show norepinephrine infusions that ended at 14:11 on 2100-01-02, but no administration record within 24 hours before the decision time of 18:36 on 2100-01-01. The most recent infusion (R41) ended before the decision time, so the statement that it is currently being given is not supported. |
| E2230341 | Continue Eptifibatide infusion at 20.6 ml/hour. | Eptifibatide infusion is currently being given. | presupposed by an action | The records show an Eptifibatide infusion that started on 2100-01-01 at 17:58 and ended on 2100-01-02 at 00:24, and another that started at 04:24 and ended at 09:05. There is no administration record of Eptifibatide in the 24 hours before the decision time of 2100-01-02 14:38:00, so the statement that it is currently being given is not supported. |
| E2860378 | Continue insulin infusion to manage hyperglycemia. | Insulin infusion is currently being given. | presupposed by an action | The most recent insulin administration record (R46) shows an infusion that ended at 02:30 on 2100-01-02, which is over 11 hours before the decision time of 14:07. There is no record of insulin being administered within the 24 hours prior to the decision time, so the statement that it is currently being given is not supported. |
| E2879373 | Continue IV furosemide for diuretic therapy. | IV furosemide is currently being given. | presupposed by an action | The records mention IV furosemide only as a documented treatment at 10:19 on 2100-01-01, which is after the decision time of 09:35. There is no administration record of IV furosemide in the 24 hours before the decision time, so the statement that it is currently being given is not supported. |
| E3001552 | Monitor heart rate and blood pressure closely due to fluctuations. | Heart rate and blood pressure have been fluctuating. | stated outright | The records contain only heart rate measurements and no blood pressure readings. While the heart rate values do fluctuate over time, the statement claims both heart rate and blood pressure have been fluctuating, and the absence of any blood pressure data means the statement is only partially supported. |
| E3027283 | Monitor pain levels and adjust ondansetron as needed. | Ondansetron is currently being given. | presupposed by an action | The records contain an active PRN order for ondansetron (R7), but there is no administration record showing it was given in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E3035113 | Continue vancomycin and zosyn IV as ordered for suspected infection. | Zosyn is currently being given. | presupposed by an action | The only Zosyn record is a one-time dose given on 2100-01-01 at 10:16, more than 24 hours before the decision time of 2100-01-02 11:08. There is no administration or running record for Zosyn in the 24 hours before the decision time, so it is not currently being given. |
| E3035113 | Continue vancomycin and zosyn IV as ordered for suspected infection. | Infection is suspected. | clinical judgment | The records show administration of vancomycin and Zosyn, which are antibiotics, but the admission diagnosis is emphysema/bronchitis, not an infection. There is no recorded diagnosis or clinical finding that directly states or supports the suspicion of an infection. |
| E3124669 | Continue pain management with oral medications as needed. | Pain management with oral medications is currently being given. | presupposed by an action | The records document pulmonary medications (antibacterials, bronchodilators, glucocorticoids) but no oral pain medications are ordered or administered. Pain levels are recorded, but no pain management medication is mentioned. |
| E3148216 | Monitor the patient's oxygen saturation closely, as it has fluctuated between 94% and 100%. | Oxygen saturation has fluctuated between 94% and 100%. | stated outright | The statement claims oxygen saturation fluctuated between 94% and 100%, but the records show values as low as 91% (R47) and 92% (R46) before the decision time, so the stated range is inaccurate. |
| E3148216 | Continue sedation at the RASS score of 0 to maintain patient comfort. | Sedation is currently being given. | presupposed by an action | The records mention sedation only as a RASS score of 0, which indicates the patient is alert and calm, not that a sedative medication is currently being administered. There is no order or administration record for any sedative drug. |
| E3170528 | Continue intravenous fluids to maintain hydration. | Intravenous fluids are currently being given. | presupposed by an action | The only intravenous fluid administration record, R22 (Potassium Chloride in NaCl IV Continuous), ended at 2100-01-02 01:40, which is before the decision time of 03:39. No other IV fluid administration is documented as running or given within the 24 hours prior to the decision time. |
| E3223097 | Continue pain management with IV morphine as needed. | IV morphine is currently being given. | presupposed by an action | The records contain an active order for IV morphine (R15), but no administration record of morphine within the 24 hours before the decision time. Therefore, the statement that IV morphine is currently being given is not supported. |

## 5. Judge panel

131 items went to the judge panel. Agreement: {'3/3': 103, '2/3': 28} (split = no majority; the conservative label was used and the item needs human review).

## 6. Per-case score sheets

| Case | Facts | supported | not_supported | not_addressed | unverifiable | Treatment agreement | Vital recall | All recall |
|---|---|---|---|---|---|---|---|---|
| E153972 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E172015 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E184757 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E211144 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E284265 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E297175 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E322290 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E375854 | 0 | - | - | - | - | 0.0% | - | - |
| E383358 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E395323 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E405746 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E454584 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E467819 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E490454 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E521456 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 50.0% | - | - |
| E664474 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E733082 | 4 | 25.0% | 75.0% | 0.0% | 0.0% | 0.0% | - | - |
| E756295 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E758325 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E826669 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E850469 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E876429 | 0 | - | - | - | - | 0.0% | - | - |
| E899746 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E942382 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E962227 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E978037 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1056063 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | - | - | - |
| E1057910 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E1057967 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1064283 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1065859 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1068212 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071224 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071450 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1090039 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1090889 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1099398 | 7 | 85.7% | 14.3% | 0.0% | 0.0% | - | - | - |
| E1117947 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1121034 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1171473 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | - | - |
| E1173453 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1177589 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E1287791 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1290248 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1449360 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1496959 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1497157 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1588473 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1592666 | 2 | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | - | - |
| E1619343 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1636307 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1653043 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1672915 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1674875 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1682105 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1705630 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1739131 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E1781359 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1790816 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823356 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823727 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1824650 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1829278 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1837964 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1853162 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | - | - | - |
| E1856821 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2230341 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E2309912 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2418055 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 50.0% | - | - |
| E2419768 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2558122 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2609672 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2714303 | 0 | - | - | - | - | - | - | - |
| E2725629 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2757707 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2814579 | 0 | - | - | - | - | 0.0% | - | - |
| E2860378 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2879373 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3001552 | 4 | 25.0% | 25.0% | 50.0% | 0.0% | 50.0% | - | - |
| E3027283 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 50.0% | - | - |
| E3033795 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3035113 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3053511 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3067309 | 0 | - | - | - | - | 0.0% | - | - |
| E3110594 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3111371 | 0 | - | - | - | - | - | - | - |
| E3112232 | 0 | - | - | - | - | - | - | - |
| E3115505 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3124669 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3130379 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E3148216 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3150018 | 2 | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | - | - |
| E3152779 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E3170528 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3178242 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3205786 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3220742 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3223097 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E3233620 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E3237226 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | - | - | - |
