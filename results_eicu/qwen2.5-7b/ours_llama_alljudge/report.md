# Evaluation of AI clinical suggestions against patient records

- Input: `eicu_triples_qwen2.5-7b.json`; 100 cases, 2.99 AI suggestions per case on average.
- Models: atomizer `deepseek-v4-pro:0813:cloud`; judge panel `llama3.1:8b-instruct-q4_K_M` (majority vote; reasoning mode: none); 173 new model calls, 0 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 26.0% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 173 |
| supported / not_supported / not_addressed / unverifiable | 77 / 95 / 1 / 0 |
| Fact accuracy = supported / (supported + not_supported) | 44.8% |
| Cases with at least one not_supported fact | 63 / 100 |
| Omitted findings: abnormalities the clinicians treated that no AI fact mentions | 0 / 0 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 51 | 43.1% | {'not_supported': 29, 'supported': 22} |
| presupposed by an action | 110 | 48.2% | {'supported': 53, 'not_supported': 57} |
| clinical judgment | 12 | 18.2% | {'not_supported': 9, 'supported': 2, 'not_addressed': 1} |
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
| E153972 | Monitor patient's hemodynamic stability closely given the fluctuating blood pressure readings. | Blood pressure readings are fluctuating. | stated outright | The records show fluctuating blood pressure readings, but the statement is about the decision time. The most recent relevant rows (R17, R18, R19) show high blood pressure readings, but they do not show a clear fluctuation. Therefore, the statement is not supported. |
| E172015 | Continue administration of intravenous fluids. | Intravenous fluids are currently being given. | presupposed by an action | The statement 'Intravenous fluids are currently being given' is not supported by the records. Although there is an ongoing administration of '1000 ML  -  KCL IN DEXTROSE-NACL 20-5-0.45 MEQ/L-%-% IV SOLN IV Continuous' (R26), it is not clear if this is an intravenous fluid. The statement is not supported by any other records. |
| E184757 | Monitor blood pressure closely due to fluctuations. | Blood pressure is fluctuating. | stated outright | The latest blood pressure measurement is 124/92 mmHg, which does not show fluctuation. However, earlier measurements (e.g. R6, R8) do show fluctuation, so the statement is not fully supported. |
| E297175 | Monitor patient's respiratory status closely due to ongoing respiratory distress. | Respiratory distress is ongoing. | stated outright | The records show that the patient's respiratory rate has been fluctuating, with values ranging from 15 to 26 inspirations per minute. While the current respiratory rate is 18 inspirations per minute, which is within the normal range, the statement that 'Respiratory distress is ongoing' is not supported by the records. The records do not indicate any ongoing respiratory distress, and the patient's  |
| E322290 | Continue anticoagulant therapy with warfarin. | Warfarin is currently being given. | presupposed by an action | The statement 'Warfarin is currently being given' is not supported by the records. Although there is a medication order for warfarin (R40), it is not an administration record, and there is no record of warfarin being administered in the 24 hours before the decision time. Therefore, the statement is not supported. |
| E383358 | Continue weaning from mechanical ventilation. | The patient is currently on mechanical ventilation. | presupposed by an action | The records show that the patient is undergoing mechanical ventilation weaning, CPAP/PEEP therapy, and tracheal suctioning, but do not show that the patient is currently on mechanical ventilation. The PEEP set is 5 cmH2O in R4 and 7 cmH2O in R16, but the most recent relevant row is R47, which shows PEEP set to 5 cmH2O. The records also show that the patient is receiving oxygen therapy, but do not  |
| E395323 | Continue vancomycin and piperacillin/tazobactam for suspected sepsis. | Vancomycin is currently being given. | presupposed by an action | The records show that vancomycin was ordered and administered, but the current administration status is not clear. R13 shows that vancomycin was documented as a treatment, but R21 shows that a different medication (Sodium Chloride) is running at decision time. There is no clear indication that vancomycin is currently being given. |
| E395323 | Continue vancomycin and piperacillin/tazobactam for suspected sepsis. | Piperacillin/tazobactam is currently being given. | presupposed by an action | The records show that piperacillin/tazobactam was ordered, but there is no administration record of it in the 24 hours before the decision time, and no 'Running at decision time' record. Therefore, the statement that it is currently being given is not supported. |
| E395323 | Continue vancomycin and piperacillin/tazobactam for suspected sepsis. | Sepsis is suspected. | clinical judgment | The records show that piperacillin/tazobactam was ordered, but there is no administration record of it in the 24 hours before the decision time. The statement is not supported by the records. |
| E405746 | Continue labetalol for hypertension management. | Labetalol is currently being given. | presupposed by an action | The records show that labetalol was ordered at 15:59 on 2099-12-31, but there is no record of it being administered within the last 24 hours. The statement that labetalol is currently being given is not supported by the records. |
| E405746 | Continue labetalol for hypertension management. | Hypertension is present. | clinical judgment | The records show that labetalol is being used to treat hypertension, but they do not show that the patient currently has hypertension. The most recent respiratory rate is 17 insp/min, which is within the normal range. |
| E490454 | Continue non-invasive ventilation with a BiPAP/CPAP mask. | The patient is currently on non-invasive ventilation with a BiPAP/CPAP mask. | presupposed by an action | The records show that the patient is currently on non-invasive ventilation with a BiPAP/CPAP mask, but the statement is not supported by the records. The records show that the patient is on non-invasive ventilation with a BiPAP/CPAP mask at 23:20, but the statement is about the decision time, which is 23:35. The records do not show that the patient is on non-invasive ventilation with a BiPAP/CPAP  |
| E521456 | Continue mechanical ventilation with tidal volume 300 mL and PEEP 5 cmH2O. | The patient is currently on mechanical ventilation. | presupposed by an action | The records show that the patient is on mechanical ventilation, but the tidal volume is 6-10 ml/kg, which is different from the 300 mL mentioned in the AI statement. Also, the records mention that the patient is on assist controlled ventilation, which is different from the volume controlled ventilation mentioned in the AI statement. |
| E521456 | Administer 10 mL of magnesium sulfate intravenously for potential delirium. | Delirium is potentially present. | clinical judgment | The records show that the patient's delirium score was No at 21:00 on 2100-01-01 and 12:00 on 2100-01-02, but the statement says that delirium is potentially present. The records do not show any administration of magnesium sulfate, which is mentioned in the original sentence. Therefore, the statement is not supported by the records. |
| E664474 | Monitor blood glucose levels closely due to persistent hyperglycemia. | Hyperglycemia is persistent. | stated outright | The statement 'Hyperglycemia is persistent' is not supported by the records. The glucose level was 137 mg/dL at 10:08, which is not high. However, the statement is not addressed by the records either, as there is no mention of hyperglycemia or any treatment for it. The records do mention glucose levels, but they are not consistently high, and there is no indication of persistent hyperglycemia. |
| E664474 | Continue non-invasive ventilation to maintain adequate oxygenation and ventilation. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records show that the patient is on non-invasive ventilation, but the most recent relevant rows (R47, R48, R49, R50) show that the patient's blood pressure is not within a normal range, which contradicts the statement that the patient is currently on non-invasive ventilation. |
| E733082 | Monitor blood glucose levels closely due to recent high readings and risk of hypoglycemia. | There is a risk of hypoglycemia. | clinical judgment | The records show recent high glucose readings, but there is no evidence that the patient is currently receiving insulin or other treatments for hypoglycemia. The medication orders for glucose and glucagon are active at decision time, but this does not necessarily mean they are being administered. |
| E733082 | Administer IV fluids to maintain adequate hydration and blood pressure support. | Hydration is inadequate. | presupposed by an action | The records show that IV fluids are being administered, but the statement 'Hydration is inadequate' is not supported by the records. The sodium and chloride levels are within normal limits, and there is no indication of dehydration or inadequate hydration. |
| E733082 | Administer IV fluids to maintain adequate hydration and blood pressure support. | Blood pressure support is needed. | presupposed by an action | The AI statement says 'blood pressure support is needed', but the records show that the patient's blood pressure has been fluctuating and is currently 104 mmHg, which is not high enough to require support. However, the records do not show any administration of blood pressure support, so the statement is not supported. |
| E826669 | Evaluate and manage electrolyte imbalances, particularly sodium and potassium. | Electrolyte imbalances are present. | presupposed by an action | The records show that the patient has been receiving various medications, including sodium chloride, amiodarone, heparin, and norepinephrine, but do not directly support the statement that electrolyte imbalances are present. The records do mention some laboratory values, such as potassium and sodium levels, but these values are not directly related to the statement. |
| E850469 | Continue aggressive fluid resuscitation to maintain adequate perfusion. | Aggressive fluid resuscitation is currently being given. | presupposed by an action | The records state that aggressive volume resuscitation is being given, but there is no administration record of it in the 24 hours before the decision time, and no 'Running at decision time' record. The statement is not supported. |
| E942382 | Monitor the patient's blood pressure and respiratory rate closely, as they have been fluctuating significantly. | Blood pressure has been fluctuating significantly. | stated outright | The records show that the patient's blood pressure has been fluctuating, but the most recent measurement (R50) shows a diastolic pressure of 69 mmHg, which is not significantly fluctuating. The statement is not supported by the records. |
| E942382 | Monitor the patient's blood pressure and respiratory rate closely, as they have been fluctuating significantly. | Respiratory rate has been fluctuating significantly. | stated outright | The respiratory rate has been fluctuating significantly, but the most recent measurement (R36) shows a respiratory rate of 18 insp/min, which is not fluctuating. |
| E942382 | Continue the administration of diltiazem to manage the patient's heart rate and rhythm. | Diltiazem is currently being given. | presupposed by an action | The records show that diltiazem was ordered and administered, but the administration record (R20) shows that it was started at 17:04, which is after the decision time. Therefore, the statement that diltiazem is currently being given is not supported. |
| E1056063 | Monitor patient's heart rate and respiratory rate closely due to variability and potential for respiratory depression. | Heart rate is variable. | stated outright | The records show variable heart rate, but the statement is about the decision time, which is 2100-01-02 10:15:00. The most recent relevant rows are R41 and R42, which show a heart rate of 108 bpm, but this is not variable. |
| E1056063 | Monitor patient's heart rate and respiratory rate closely due to variability and potential for respiratory depression. | Respiratory rate is variable. | stated outright | The statement says the respiratory rate is variable, but R13 shows a respiratory rate of 18 insp/min, which is not variable. The statement is not supported by the records. |
| E1056063 | Monitor patient's heart rate and respiratory rate closely due to variability and potential for respiratory depression. | There is potential for respiratory depression. | clinical judgment | The records show that the patient is receiving oxygen therapy via a nasal cannula, but do not indicate that the patient is receiving ventilation. The statement about potential for respiratory depression is not supported by the records. |
| E1056063 | Assess for signs of magnesium toxicity, given the recent administration of magnesium sulfate. | Magnesium sulfate was recently administered. | stated outright | The records show that magnesium sulfate was administered at 15:33, but the statement says it was recently administered. The most recent relevant records are from 15:33, and they show that magnesium sulfate was administered, but they do not show that it was administered recently. Therefore, the statement is not supported. |
| E1057910 | Continue mechanical ventilation and ensure adequate oxygenation. | The patient is currently on mechanical ventilation. | presupposed by an action | The patient is currently on mechanical ventilation, but the records show that the patient was on mechanical ventilation at some point, but the current status is not supported by the records. The record R30 shows that the patient was on mechanical ventilation at 12:00, but the current time is 05:25:00, and there is no record showing that the patient is currently on mechanical ventilation. |
| E1057967 | Monitor blood glucose levels closely given the patient's fluctuating readings and risk of sepsis. | Blood glucose readings are fluctuating. | stated outright | The records show fluctuating blood glucose levels, but the current level is 113 mg/dL, which is not rising. The patient is receiving insulin aspart, but the records do not show that it is being administered at the decision time. |
| E1057967 | Monitor blood glucose levels closely given the patient's fluctuating readings and risk of sepsis. | The patient is at risk of sepsis. | clinical judgment | The patient is being ventilated and oxygenated with a nasal cannula, which is a non-ventilator device. There is no tube device or matching setting charted after the 'O2 Delivery Device(s)' row. The patient's risk of sepsis is mentioned in the treatment documentation, but it is not directly supported by the records. |
| E1057967 | Continue pain management with PRN orders for Dilaudid IV, oxyCODONE PO, and Tylenol PO as needed. | Pain management is currently being given. | presupposed by an action | The statement that pain management is currently being given is not supported by the records. Although Dilaudid IV was given once at 08:34 on 2100-01-02 (R33), the records do not show that pain management is currently being given. The medication orders for Tylenol PO q6hr PRN (R44), oxyCODONE PO q4hr PRN (R45), and Dilaudid IV q2hr PRN (R46) are active at decision time, but this does not mean that  |
| E1064283 | Monitor blood pressure closely due to hypertension. | Hypertension is present. | stated outright | The records show that the patient has hypertension and is receiving a vasodilating agent (nicardipine) IV, but the statement 'Hypertension is present' is not supported by the records because it is a present-tense statement and the records do not show that the patient has hypertension at the decision time (2100-01-02 19:52:00). The records show that the patient has hypertension and is receiving a v |
| E1065859 | Assess for signs of hypovolemia or sepsis given the patient's hypotension and altered mental status. | Hypotension is present. | stated outright | The records show that the patient was receiving intravenous fluids and had a fluid bolus, but the statement that hypotension is present is not supported by these records. The records do not show the patient's blood pressure, which is necessary to determine if hypotension is present. |
| E1065859 | Assess for signs of hypovolemia or sepsis given the patient's hypotension and altered mental status. | Altered mental status is present. | stated outright | The statement 'Altered mental status is present' is not supported by the records. The record R16 shows 'Best Verbal Response: Confused', which indicates altered mental status, but the statement is present-tense and the records do not show that the patient's mental status was altered at the decision time. The record R16 is from 01:00 on 2100-01-02, but the decision time is 2100-01-02 20:54:00. The  |
| E1071450 | Administer intravenous potassium chloride to correct hypokalemia. | Hypokalemia is present. | presupposed by an action | The statement 'Hypokalemia is present' is not supported by the records. The most recent potassium level measurement (R30) shows a value of 2.8 mmol/L, which is below the normal range. However, the statement is not supported because the records do not show any administration of potassium chloride in the 24 hours before the decision time, and the ongoing medication orders do not include potassium. |
| E1071450 | Continue inotropic support with milrinone. | Milrinone is currently being given. | presupposed by an action | The records show that milrinone was ordered and administered, but the most recent administration record is from 2100-01-01 03:34, which is before the decision time. There is no record of milrinone being administered at the decision time. |
| E1090039 | Continue mechanical ventilation with adjusted settings to maintain adequate oxygenation and ventilation. | The patient is currently on mechanical ventilation. | presupposed by an action | The records show that the patient is on mechanical ventilation, but the most recent relevant rows (R49 and R50) show a non-invasive blood pressure of 121 mmHg and 98 mmHg, respectively, which is lower than the typical values for a patient on mechanical ventilation. Additionally, the records do not show any recent administration of mechanical ventilation. |
| E1090889 | Assess for potential causes of hypotension. | Hypotension is present. | presupposed by an action | The statement 'Hypotension is present' is not supported by the records. The PEEP setting of 5 cm H2O in record R28 does not indicate hypotension. Additionally, the recent vital signs in records R25-R27 do not show any indication of hypotension. |
| E1099398 | Patient's blood pressure is fluctuating, with systolic readings as high as 202 mmHg and diastolic as low as 60 mmHg. Consider adjusting antihypertensive therapy. | Diastolic blood pressure is as low as 60 mmHg. | stated outright | The records show that the patient's diastolic blood pressure was as low as 60 mmHg at 12:00 on 2100-01-01, but also as high as 98 mmHg at 23:09 on 2100-01-01. The statement that the diastolic blood pressure is as low as 60 mmHg is not supported by the records. |
| E1099398 | Patient's respiratory rate is within normal limits but shows variability. Monitor for any changes in respiratory status. | Respiratory rate shows variability. | stated outright | The statement 'Respiratory rate shows variability' is not supported by the records. The respiratory rate is measured at various times, but it does not show variability. The rate is 21 insp/min at 08:27, 19 insp/min at 12:00, 21 insp/min at 15:38, 22 insp/min at 19:21, and 20 insp/min at 23:09. There is no record of the respiratory rate changing or showing variability. |
| E1117947 | Continue non-invasive ventilation to support respiratory function. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records state that the patient is on non-invasive ventilation, but the most recent relevant rows show that the patient's blood pressure is fluctuating and not necessarily supported by the ventilation. The records do not show that the ventilation was discontinued or changed to invasive ventilation. |
| E1121034 | Continue mechanical ventilation with adjusted settings. | The patient is currently on mechanical ventilation. | presupposed by an action | The records show that the patient was on mechanical ventilation, but the most recent relevant rows (R9, R21, R43) do not show the current respiratory rate setting, which is necessary to support the statement. The statement is not supported by the records. |
| E1173453 | Monitor the patient's blood pressure closely due to fluctuations. | Blood pressure is fluctuating. | stated outright | The latest measurement of blood pressure is 142 mmHg systolic, which is not fluctuating. The statement is not supported by the records. |
| E1173453 | Continue antibiotic therapy with vancomycin. | Vancomycin is currently being given. | presupposed by an action | The statement says vancomycin is currently being given, but the records show that it was ordered (R13) but there is no administration record in the 24 hours before the decision time. |
| E1287791 | Continue sedation at -1 RASS score. | The patient is currently receiving sedation. | presupposed by an action | The patient is currently receiving sedation. The records show that the patient has been receiving sedation, but the most recent measurement (R50) shows a sedation score of 1, which indicates that the patient is no longer receiving sedation. Therefore, the statement is not supported. |
| E1290248 | Monitor patient's vital signs closely due to fluctuating SpO2 and pulse. | SpO2 is fluctuating. | stated outright | The most recent SpO2 measurement is 94, which does not support the statement that SpO2 is fluctuating. |
| E1290248 | Monitor patient's vital signs closely due to fluctuating SpO2 and pulse. | Pulse is fluctuating. | stated outright | The pulse is fluctuating, but the most recent measurement (R38) is 67, which is not fluctuating. The statement is not supported by the records. |
| E1496959 | Monitor blood pressure closely due to significant fluctuations. | Blood pressure has significant fluctuations. | stated outright | The statement says there are significant fluctuations, but the highest value in the 24 hours before the decision time is 232 mmHg, which is not fluctuating. |
| E1496959 | Continue anticonvulsant therapy for seizure prevention. | Anticonvulsant therapy is currently being given. | presupposed by an action | The records show that anticonvulsant therapy was ordered and documented as being given, but there is no administration record of it in the 24 hours before the decision time. The statement is not supported. |
| E1497157 | Monitor electrolyte levels and adjust magnesium infusion as needed. | Magnesium infusion is currently being given. | presupposed by an action | The records show that magnesium infusion was started at 20:00 on 2100-01-01 and continued at various rates until 10:00 on 2100-01-02. However, the statement says that magnesium infusion is currently being given, which is not supported by the records. The records do not show any administration of magnesium at the decision time of 19:30 on 2100-01-02. |
| E1592666 | Monitor blood glucose levels closely due to persistent hyperglycemia. | Hyperglycemia is persistent. | stated outright | The records show that the patient's glucose levels have been elevated, but the statement that hyperglycemia is persistent is not supported by the records. The glucose levels have fluctuated between 188 mg/dL and 256 mg/dL, and the most recent measurement is 193 mg/dL, which is still elevated but not persistently high. |
| E1619343 | Administer intravenous vancomycin for suspected infection. | Infection is suspected. | presupposed by an action | The records show that vancomycin was ordered and administered, but the statement is about suspected infection, which is not directly supported by the records. The records do mention treatment for endocrine and electrolyte correction, but this is not directly related to the statement. |
| E1636307 | Continue intravenous sedation and analgesia to maintain patient comfort. | Intravenous sedation is currently being given. | presupposed by an action | The records show that intravenous sedation was ordered (R3, R4, R5), but there is no record of it being administered in the 24 hours before the decision time. The statement is not supported by the records. |
| E1636307 | Continue intravenous sedation and analgesia to maintain patient comfort. | Intravenous analgesia is currently being given. | presupposed by an action | The records show that nalOXone, HYDROmorphone, and oxyCODONE-acetaminophen are ordered and active at decision time, but there is no record of intravenous analgesia being administered in the 24 hours before the decision time. Additionally, fentaNYL is ordered and active at decision time, but it is administered intravenously, not intravenously as analgesia. |
| E1636307 | Assess patient for signs of respiratory distress and adjust mechanical ventilation settings if necessary. | The patient is currently on mechanical ventilation. | presupposed by an action | The records show that the patient is on mechanical ventilation, but the most recent relevant rows (R9) show that the ventilation mode is assist controlled, which does not necessarily mean that the patient is on mechanical ventilation. The statement is not supported by the records. |
| E1672915 | Continue intravenous insulin to manage glucose levels. | Intravenous insulin is currently being given. | presupposed by an action | The records show that insulin lispro was ordered to be given subcutaneously at bedtime (R19), but there is no record of intravenous insulin being administered at the decision time (R10). |
| E1682105 | Continue mechanical ventilation with PEEP set at 5 cmH2O. | The patient is currently on mechanical ventilation. | presupposed by an action | The patient is currently on mechanical ventilation. The records show that the patient was on mechanical ventilation at some point, but the most recent relevant row (R50) shows a non-invasive blood pressure measurement, not a ventilator setting. Therefore, the statement is not supported. |
| E1705630 | Continue sedation at a reduced level. | Sedation is currently being given. | presupposed by an action | The AI statement 'Sedation is currently being given' is not supported by the records. Although there are ongoing orders for sedation (R10), the records do not show that sedation is being administered at the decision time. The 'Running at decision time' records (R12 and R13) are for sodium chloride administration, not sedation. |
| E1823727 | Continue IV fluids and electrolyte management. | Electrolyte management is currently being given. | presupposed by an action | The statement 'Electrolyte management is currently being given' is not supported by the records. Although there are records of ongoing administration of Sodium Chloride 0.9% 1,000 ML BAG IV CONT (R15) and ongoing orders for Sodium Chloride 0.9% 1,000 ML BAG IV PRN (R34), these do not directly support the statement that electrolyte management is being given. The records do not mention any specific, |
| E1823727 | Assess for signs of infection given leukocytosis. | Leukocytosis is present. | stated outright | The records show a recent lymphocyte count of 9%, which is higher than the previous count of 8.9%. However, the statement 'Leukocytosis is present' is not fully supported by the records, as the count is not extremely high. Additionally, the records do not show any administration of medications that would cause leukocytosis. |
| E1824650 | Wean off mechanical ventilation. | The patient is currently on mechanical ventilation. | presupposed by an action | The patient is currently on mechanical ventilation. The records show that the patient was on mechanical ventilation at 18:00 on 2100-01-01 (R13), and that the treatment documented at 04:49 on 2100-01-02 was ventilator weaning (R30). However, the records also show that the patient was switched to nasal cannula at 04:00 on 2100-01-02 (R28), and that the PEEP set was 0 cmH2O at 05:55 on 2100-01-02 (R |
| E1829278 | Monitor blood glucose levels closely due to persistent hyperglycemia. | Hyperglycemia is persistent. | stated outright | The records show that the patient's blood glucose levels have been fluctuating, with a high reading of 325 mg/dL at 09:45 on 2100-01-01 and a lower reading of 285 mg/dL at 08:45 on 2100-01-01. However, the statement 'Hyperglycemia is persistent' implies a more consistent and prolonged elevation of blood glucose levels, which is not fully supported by the records. |
| E1829278 | Continue intravenous fluid administration to maintain adequate hydration. | Intravenous fluids are currently being administered. | presupposed by an action | The records show that intravenous fluids were administered at 07:45, but there is no record of them being administered at the decision time of 08:43:00. However, there is a record of a continuous infusion of sodium chloride 0.9% IV solution at 09:30, which suggests that intravenous fluids may still be being administered. |
| E1853162 | Increase oxygen flow to 4 L/min due to elevated systolic blood pressure and respiratory rate. | Respiratory rate is elevated. | stated outright | The statement 'Respiratory rate is elevated' is not supported by the records. The most recent relevant record (R41) shows a respiratory rate of 20 insp/min, which is not elevated. However, the statement is not supported because there is no record of the patient's respiratory rate being elevated in the 24 hours before the decision time. |
| E1856821 | Monitor blood glucose levels closely due to elevated levels. | Blood glucose levels are elevated. | stated outright | The statement 'Blood glucose levels are elevated' is not supported by the records. The most recent glucose measurement (R41) shows a level of 229 mg/dL, which is elevated. However, the records also show that the patient has been receiving insulin (R2 and R3), which suggests that the elevated glucose levels may be due to the medication rather than a medical condition. Therefore, the statement is 'e |
| E2230341 | Continue Eptifibatide infusion at 20.6 ml/hour. | Eptifibatide infusion is currently being given. | presupposed by an action | The records show that Eptifibatide infusion was started at 17:58 on 2100-01-01 and at 04:24 on 2100-01-02, but the current rate is 20.6 ml/hour, which is not supported by the records. The records show that Eptifibatide was infused at 100 units/hour on 2100-01-01 and at 20.6 ml/hour on 2100-01-02, but the current rate is not supported by the records. |
| E2418055 | Monitor blood glucose levels and adjust insulin therapy as needed. | Insulin therapy is currently being given. | presupposed by an action | The records show that insulin therapy was ordered (R10) and that there is an ongoing administration of HEPARIN (PORCINE) 5,000 UNIT/ML INJECTION (R10) and SODIUM CHLORIDE 0.9 % IV (R11) at the decision time, but there is no record of insulin administration in the 24 hours before the decision time. |
| E2418055 | Administer intravenous magnesium and potassium to address electrolyte imbalances. | Electrolyte imbalances are present. | presupposed by an action | The records show that the patient's potassium level is 3.3 mEq/L, which is within the normal range. However, the statement 'Electrolyte imbalances are present' is not supported by the records, as there is no indication of electrolyte imbalances. The records do mention magnesium and potassium administration, but this does not necessarily mean that electrolyte imbalances are present. |
| E2419768 | Continue IV fluid administration to maintain hydration. | IV fluids are currently being administered. | presupposed by an action | The statement 'IV fluids are currently being administered' is not supported by the records. Although there are records of IV fluids being administered (R5 and R30), they are scheduled orders that started before the decision time, and there is no record of IV fluids being administered at the decision time. |
| E2609672 | Continue stress ulcer prophylaxis with pantoprazole. | Pantoprazole is currently being given. | presupposed by an action | The statement that Pantoprazole is currently being given is not supported by the records. The record R27 shows that Pantoprazole is scheduled to be given at 03:45, but it does not show that it has been administered. The record R27 is the most recent relevant row, and it contradicts the statement. |
| E2860378 | Continue insulin infusion to manage hyperglycemia. | Insulin infusion is currently being given. | presupposed by an action | The records show that insulin infusion was started at 16:00 on 2100-01-01 and continued with different rates until 02:30 on 2100-01-02. However, the statement says that insulin infusion is currently being given, which is not supported by the records. The records do not show any administration of insulin between 02:30 on 2100-01-02 and 14:07 on 2100-01-02, when the decision was made. |
| E2860378 | Monitor blood pressure closely due to fluctuations. | Blood pressure is fluctuating. | stated outright | The records show that the patient's blood pressure was fluctuating, but the most recent measurement (R31) is 102 mmHg, which is not high enough to support the statement that the blood pressure is fluctuating. The statement is not supported by the records. |
| E2860378 | Assess for signs of hypovolemia given low blood pressure readings. | Blood pressure is low. | stated outright | The most recent measurement of blood pressure is 102 mmHg, which is not low. However, earlier measurements were lower, so the statement is not fully supported. |
| E2879373 | Continue IV furosemide for diuretic therapy. | IV furosemide is currently being given. | presupposed by an action | The records show that IV furosemide was ordered, but there is no record of it being administered in the 24 hours before the decision time. |
| E3001552 | Administer IV furosemide to manage fluid overload and ventricular dysfunction. | Fluid overload is present. | clinical judgment | The records show fluctuations in sodium and chloride levels, but do not indicate fluid overload. The patient has been receiving sodium chloride infusions, but the records do not show any administration of diuretics, which are typically used to manage fluid overload. |
| E3027283 | Monitor pain levels and adjust ondansetron as needed. | Ondansetron is currently being given. | presupposed by an action | The statement says Ondansetron is currently being given, but the records show it was ordered (R5) and the infusion is running at decision time (R34), but there is no record of Ondansetron being administered in the 24 hours before the decision time. |
| E3035113 | Monitor blood glucose levels closely due to fluctuations and risk of hypoglycemia. | Blood glucose levels are fluctuating. | stated outright | The records show fluctuating blood glucose levels, but the statement is not supported because it requires recent administration of insulin, which is not shown in the records. The records do show high glucose levels, but the statement is not supported because it requires fluctuating levels, which is not shown in the records. The records do show high glucose levels, but the statement is not fully or |
| E3035113 | Monitor blood glucose levels closely due to fluctuations and risk of hypoglycemia. | There is a risk of hypoglycemia. | clinical judgment | The records show fluctuations in glucose levels, but the statement is about the risk of hypoglycemia. The recent glucose levels (R20, R25, R34, R36) are high, not low, so the statement is not supported. |
| E3035113 | Continue vancomycin and zosyn IV as ordered for suspected infection. | Infection is suspected. | clinical judgment | The records show that vancomycin and Zosyn IV were administered once, but there is no evidence that they are currently being given or that the infection is suspected. The administration records do not indicate ongoing treatment. |
| E3053511 | Continue midazolam for sedation. | Midazolam is currently being given. | presupposed by an action | The records show that midazolam was administered at 16:00 and 17:22, but the statement says it is currently being given. The most recent administration record is at 17:22, which is within the 24 hours before the decision time, so the statement is supported by the administration record of midazolam in the 24 hours before the decision time. However, the records also show that midazolam was given at  |
| E3110594 | Monitor patient's blood pressure closely, as it has fluctuated significantly. | Blood pressure has fluctuated significantly. | stated outright | The records show that the patient's blood pressure has fluctuated, but the most recent measurement (R46) shows a systolic pressure of 125 mmHg, which is higher than the previous measurements. The statement 'Blood pressure has fluctuated significantly' is not supported by the records, as the fluctuation is not significant in the context of the patient's overall blood pressure readings. |
| E3110594 | Continue administration of furosemide to manage fluid status. | Furosemide is currently being given. | presupposed by an action | The records show that furosemide was ordered and scheduled to be administered at 13:30, but there is no record of it being administered at that time. The statement that it is currently being given is not supported by the records. |
| E3115505 | Continue administration of intravenous methylprednisolone. | Intravenous methylprednisolone is currently being given. | presupposed by an action | The statement says that intravenous methylprednisolone is currently being given, but the records show that it was administered at 04:14, and there is a later order for Q24HR administration (R43). |
| E3124669 | Continue pain management with oral medications as needed. | Pain management with oral medications is currently being given. | presupposed by an action | The records show that the patient is receiving oral medications for pain management, but the current administration of these medications is not supported by the records. The records show that the patient is receiving bronchodilators, antibacterials, and glucocorticoids, but these medications are not directly related to pain management. The pain level has been consistently high, with a recent drop, |
| E3130379 | Continue non-invasive ventilation with BiPAP settings. | The patient is currently on non-invasive ventilation with BiPAP. | presupposed by an action | The records show that the patient is on BiPAP, but the statement says the patient is currently on non-invasive ventilation with BiPAP. The records do not show that the patient is currently on non-invasive ventilation. |
| E3148216 | Continue sedation at the RASS score of 0 to maintain patient comfort. | Sedation is currently being given. | presupposed by an action | The records show that the patient's sedation score is 0 and they are on RASS, but there is no record of sedation being administered in the 24 hours before the decision time. The statement is not supported by the records. |
| E3150018 | Continue sedative and anti-psychotic medications for pain and agitation. | Sedative medications are currently being given. | presupposed by an action | The records show that lorazepam, vanafaxine (Effexor), and haldol are being given for pain and agitation, but they do not show that sedative medications are currently being given. |
| E3150018 | Continue sedative and anti-psychotic medications for pain and agitation. | Anti-psychotic medications are currently being given. | presupposed by an action | The records show that the patient is receiving anti-psychotic and sedative medications, but they do not show that these medications are currently being given. The most recent relevant records show that the medications were ordered, but not administered. |
| E3170528 | Monitor blood pressure closely due to fluctuations. | Blood pressure is fluctuating. | stated outright | The records show that the patient's blood pressure has been fluctuating, but the most recent measurement (R43) shows a mean of 113 mmHg, which is not fluctuating. The statement is not supported by the records. |
| E3170528 | Continue intravenous fluids to maintain hydration. | Intravenous fluids are currently being given. | presupposed by an action | The records show that intravenous fluids are being administered, but the statement is not supported because the records do not show that the fluids are being given currently. The records show that the medication DOCUSATE SODIUM 100 MG PO CAPS PO BID and DOCUSATE SODIUM 50 MG/5ML PO LIQD Per NG tube BID are running at decision time, but this does not support the statement that intravenous fluids is |
| E3205786 | Continue levetiracetam for seizure prophylaxis. | Levetiracetam is currently being given. | presupposed by an action | The medication administration record for levetiracetam shows that it was scheduled to be given at 04:00, but there is no record of it being administered at the decision time of 22:25:00. Therefore, the statement that levetiracetam is currently being given is not supported. |
| E3220742 | Continue intravenous sodium chloride for fluid management. | Intravenous sodium chloride is currently being given. | presupposed by an action | The statement says that intravenous sodium chloride is currently being given, but the records show that it was administered continuously from 03:00 on 2100-01-01, which is after the decision time. However, there is also a record of a bolus administration of sodium chloride at 22:00 on 2099-12-31, which is within the 24 hours before the decision time. Therefore, the statement is not fully supported |
| E3223097 | Continue pain management with IV morphine as needed. | IV morphine is currently being given. | presupposed by an action | The statement says IV morphine is currently being given, but the most recent relevant record (R13) shows that morphine is ordered IV PRN, but it does not show that it is currently being given. There is no record of IV morphine administration in the 24 hours before the decision time. |
| E3237226 | Continue non-invasive ventilation as needed. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records show that the patient is on non-invasive ventilation, but the most recent relevant rows (R42, R43, R44, R46, R47, R48) show that the patient's blood pressure is being monitored, not that the patient is on non-invasive ventilation. Also, R37 and R40 are not recent enough to support the statement. |

## 5. Judge panel

173 items went to the judge panel. Agreement: {'1/1': 173} (split = no majority; the conservative label was used and the item needs human review).

## 6. Per-case score sheets

| Case | Facts | supported | not_supported | not_addressed | unverifiable | Treatment agreement | Vital recall | All recall |
|---|---|---|---|---|---|---|---|---|
| E153972 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E172015 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E184757 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E211144 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E284265 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E297175 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E322290 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E375854 | 0 | - | - | - | - | 0.0% | - | - |
| E383358 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 100.0% | - | - |
| E395323 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E405746 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E454584 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E467819 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E490454 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 50.0% | - | - |
| E521456 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 50.0% | - | - |
| E664474 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E733082 | 4 | 25.0% | 75.0% | 0.0% | 0.0% | 0.0% | - | - |
| E756295 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E758325 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E826669 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E850469 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E876429 | 0 | - | - | - | - | 0.0% | - | - |
| E899746 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E942382 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E962227 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E978037 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1056063 | 5 | 20.0% | 80.0% | 0.0% | 0.0% | - | - | - |
| E1057910 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1057967 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1064283 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1065859 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1068212 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071224 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071450 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1090039 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1090889 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1099398 | 7 | 71.4% | 28.6% | 0.0% | 0.0% | - | - | - |
| E1117947 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1121034 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1171473 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1173453 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1177589 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1287791 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1290248 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1449360 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1496959 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1497157 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1588473 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1592666 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | - | - |
| E1619343 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1636307 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1653043 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1672915 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1674875 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1682105 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1705630 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1739131 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1781359 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1790816 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823356 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823727 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1824650 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1829278 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1837964 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1853162 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | - | - | - |
| E1856821 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2230341 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E2309912 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2418055 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 50.0% | - | - |
| E2419768 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2558122 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2609672 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2714303 | 0 | - | - | - | - | - | - | - |
| E2725629 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2757707 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2814579 | 0 | - | - | - | - | 0.0% | - | - |
| E2860378 | 4 | 25.0% | 75.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2879373 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3001552 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 50.0% | - | - |
| E3027283 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 50.0% | - | - |
| E3033795 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3035113 | 5 | 40.0% | 60.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3053511 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3067309 | 0 | - | - | - | - | 0.0% | - | - |
| E3110594 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3111371 | 0 | - | - | - | - | - | - | - |
| E3112232 | 0 | - | - | - | - | - | - | - |
| E3115505 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3124669 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3130379 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 100.0% | - | - |
| E3148216 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3150018 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3152779 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3170528 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3178242 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3205786 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3220742 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3223097 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E3233620 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3237226 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
