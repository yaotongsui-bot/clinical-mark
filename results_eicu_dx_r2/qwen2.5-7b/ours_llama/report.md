# Evaluation of AI clinical suggestions against patient records

- Input: `eicu_triples_qwen2.5-7b.json`; 100 cases, 2.99 AI suggestions per case on average.
- Models: atomizer `deepseek-v4-pro:0813:cloud`; judge panel `llama3.1:8b-instruct-q4_K_M` (majority vote; reasoning mode: none); 131 new model calls, 0 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 27.2% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 173 |
| supported / not_supported / not_addressed / unverifiable | 75 / 90 / 8 / 0 |
| Fact accuracy = supported / (supported + not_supported) | 45.5% |
| Cases with at least one not_supported fact | 57 / 100 |
| Omitted findings: abnormalities the clinicians treated that no AI fact mentions | 0 / 0 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 51 | 52.9% | {'not_supported': 24, 'supported': 27} |
| presupposed by an action | 110 | 44.7% | {'supported': 46, 'not_supported': 57, 'not_addressed': 7} |
| clinical judgment | 12 | 18.2% | {'supported': 2, 'not_supported': 9, 'not_addressed': 1} |
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
| E153972 | Monitor patient's hemodynamic stability closely given the fluctuating blood pressure readings. | Blood pressure readings are fluctuating. | stated outright | The records show fluctuating blood pressure readings, but the most recent reading is 123 mmHg, which is not the highest value. The statement requires the latest value to be the highest for 'rising'. |
| E172015 | Continue administration of intravenous fluids. | Intravenous fluids are currently being given. | presupposed by an action | The statement 'Intravenous fluids are currently being given' is not supported by the records. Although there is an ongoing administration of '1000 ML  -  KCL IN DEXTROSE-NACL 20-5-0.45 MEQ/L-%-% IV SOLN IV Continuous' (R26), it is not clear if this is an intravenous fluid. The statement is not supported by any other records. |
| E184757 | Monitor blood pressure closely due to fluctuations. | Blood pressure is fluctuating. | stated outright | The statement 'Blood pressure is fluctuating' is not supported by the records. The records show that the blood pressure is fluctuating, but the most recent measurement (R18) shows a systolic pressure of 167 mmHg, which is higher than the previous measurements. The statement is not supported because it is based on a single measurement, and the records do not show a consistent pattern of fluctuation |
| E297175 | Monitor patient's respiratory status closely due to ongoing respiratory distress. | Respiratory distress is ongoing. | stated outright | The records show that the patient is receiving medication for respiratory distress, but the respiratory rate is not consistently high. The statement is not supported by the records, as the respiratory rate is not always elevated. |
| E297175 | Continue administration of bronchodilators as ordered. | Bronchodilators are currently being given. | presupposed by an action | The records show that bronchodilators are being administered, but the most recent relevant rows (R1 and R2) show that they are being administered as scheduled orders, and the ongoing_at_decision field is true. However, the statement is about the decision time, and the records do not show that the bronchodilators were administered at the decision time. Therefore, the statement is not supported. |
| E322290 | Continue anticoagulant therapy with warfarin. | Warfarin is currently being given. | presupposed by an action | The statement 'Warfarin is currently being given' is not supported by the records. Although there is a medication order for warfarin (R41), it does not show administration of the drug. The records do mention anticoagulant administration (R17, R29, R30), but this is not specific to warfarin. |
| E395323 | Continue vancomycin and piperacillin/tazobactam for suspected sepsis. | Vancomycin is currently being given. | presupposed by an action | The records show that vancomycin was ordered and documented as being given, but there is no administration record of it in the 24 hours before the decision time. The statement is not supported by the records. |
| E395323 | Continue vancomycin and piperacillin/tazobactam for suspected sepsis. | Piperacillin/tazobactam is currently being given. | presupposed by an action | The records show that piperacillin/tazobactam was ordered, but there is no administration record of it in the 24 hours before the decision time. The statement is not supported by the records. |
| E405746 | Continue labetalol for hypertension management. | Labetalol is currently being given. | presupposed by an action | The statement that labetalol is currently being given is not supported by the records. Although there is an order for labetalol (R10), there is no administration record of it in the 24 hours before the decision time, and no 'Running at decision time' record. The order for labetalol was placed at 15:59 on 2099-12-31, but there is no record of it being administered until R22, which is after the 'O2' |
| E405746 | Continue labetalol for hypertension management. | Hypertension is present. | clinical judgment | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E490454 | Continue non-invasive ventilation with a BiPAP/CPAP mask. | The patient is currently on non-invasive ventilation with a BiPAP/CPAP mask. | presupposed by an action | The records show that the patient is on non-invasive ventilation with a face mask, but the statement specifies a BiPAP/CPAP mask. The records do not show that the patient is on a BiPAP/CPAP mask, so the statement is not supported. |
| E521456 | Administer 10 mL of magnesium sulfate intravenously for potential delirium. | Delirium is potentially present. | clinical judgment | The records show that the patient's delirium score was No at 21:00 on 2100-01-01 and 12:00 on 2100-01-02, but the statement 'Delirium is potentially present' is not supported by these records. The records do not show any administration of magnesium sulfate intravenously for potential delirium. |
| E664474 | Continue non-invasive ventilation to maintain adequate oxygenation and ventilation. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records state that the patient is on non-invasive ventilation, but the most recent relevant rows (R30) show that the patient is on non-invasive ventilation, but the blood pressure measurements do not support the statement that the patient is currently on non-invasive ventilation. |
| E733082 | Monitor blood glucose levels closely due to recent high readings and risk of hypoglycemia. | There is a risk of hypoglycemia. | clinical judgment | The records show recent high glucose readings, but there is no evidence that the patient is currently receiving insulin or other treatments for hypoglycemia. The medication orders for glucose and glucagon are active at decision time, but this does not necessarily mean they are being administered. |
| E733082 | Administer IV fluids to maintain adequate hydration and blood pressure support. | Hydration is inadequate. | presupposed by an action | The patient is receiving IV fluids, but the records do not show that the hydration is inadequate. The sodium levels are within a normal range, and the chloride levels are also within a normal range. The respiratory rate is fluctuating, but it is not consistently high or low. |
| E733082 | Administer IV fluids to maintain adequate hydration and blood pressure support. | Blood pressure support is needed. | presupposed by an action | The AI statement says 'blood pressure support is needed', but the most recent relevant record (R48) shows a systolic blood pressure of 104 mmHg, which is not high enough to require support. However, the record does not contradict the statement either, so it is not_supported. |
| E850469 | Continue aggressive fluid resuscitation to maintain adequate perfusion. | Aggressive fluid resuscitation is currently being given. | presupposed by an action | The records show that aggressive fluid resuscitation was ordered, but there is no evidence that it was administered at the decision time. The most recent administration record of sodium chloride 0.9% 1000 ML PB IV is from 12:27, which is before the decision time. |
| E942382 | Monitor the patient's blood pressure and respiratory rate closely, as they have been fluctuating significantly. | Blood pressure has been fluctuating significantly. | stated outright | The records show that the patient's blood pressure has been fluctuating, but the most recent measurement (R50) shows a diastolic pressure of 69 mmHg, which is not significantly fluctuating. The statement is not supported by the records. |
| E942382 | Monitor the patient's blood pressure and respiratory rate closely, as they have been fluctuating significantly. | Respiratory rate has been fluctuating significantly. | stated outright | The respiratory rate has been fluctuating significantly, but the most recent measurement (R36) shows a respiratory rate of 18 insp/min, which is not fluctuating. |
| E942382 | Continue the administration of diltiazem to manage the patient's heart rate and rhythm. | Diltiazem is currently being given. | presupposed by an action | The records show that diltiazem was ordered and administered, but the administration record (R20) is from 17:04, which is after the decision time. Therefore, the statement that diltiazem is currently being given is not supported. |
| E1056063 | Monitor patient's heart rate and respiratory rate closely due to variability and potential for respiratory depression. | Heart rate is variable. | stated outright | The records show variable heart rate, but the statement is about the decision time. The most recent relevant rows are R12 and R13, which show a heart rate of 107 bpm and 112 bpm, respectively. These values are not variable, so the statement is not supported. |
| E1056063 | Monitor patient's heart rate and respiratory rate closely due to variability and potential for respiratory depression. | Respiratory rate is variable. | stated outright | The statement says the respiratory rate is variable, but R13 shows a respiratory rate of 18 insp/min, which is not variable. The statement is not supported by the records. |
| E1056063 | Monitor patient's heart rate and respiratory rate closely due to variability and potential for respiratory depression. | There is potential for respiratory depression. | clinical judgment | The statement 'There is potential for respiratory depression' is not supported by the records. The patient is on nasal cannula oxygen therapy, which does not indicate a high risk of respiratory depression. However, the patient's respiratory rate has been variable, which may indicate a potential for respiratory depression. The records do not provide enough information to fully support the statement |
| E1056063 | Assess for signs of magnesium toxicity, given the recent administration of magnesium sulfate. | Magnesium sulfate was recently administered. | stated outright | The statement that magnesium sulfate was recently administered is not supported by the records. Although magnesium sulfate was administered at 15:33 on 2100-01-01 (R31), the records do not show that it was administered recently. The most recent measurement of magnesium level is from 08:05 on 2100-01-02 (R44), which shows a level of 2.1 mg/dL, indicating that the magnesium sulfate was administered  |
| E1057967 | Monitor blood glucose levels closely given the patient's fluctuating readings and risk of sepsis. | The patient is at risk of sepsis. | clinical judgment | The patient's admission diagnosis is sepsis, but the records do not show that the patient is currently at risk of sepsis. The patient's respiratory rate is fluctuating, but it is not rising. |
| E1057967 | Continue pain management with PRN orders for Dilaudid IV, oxyCODONE PO, and Tylenol PO as needed. | Pain management is currently being given. | presupposed by an action | The records show that Dilaudid IV, oxyCODONE PO, and Tylenol PO were ordered and scheduled for administration, but only Dilaudid IV was actually administered (R36). The orders for oxyCODONE PO and Tylenol PO are still active (R44 and R45), but no administration records for these medications are present in the records. Therefore, the statement that pain management is currently being given is not su |
| E1064283 | Administer potassium chloride PO to address low potassium levels. | Potassium is low. | stated outright | Latest potassium 4.1 mmol/L at 2100-01-02 10:38:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E1065859 | Monitor blood glucose levels closely due to persistent hyperglycemia. | Hyperglycemia is present. | stated outright | Latest glucose 96 mg/dL at 2100-01-02 19:40:00 (reference 70 to 100) is normal, not consistent with 'high'. |
| E1065859 | Assess for signs of hypovolemia or sepsis given the patient's hypotension and altered mental status. | Altered mental status is present. | stated outright | The records show that the patient's best verbal response is Confused, but this does not necessarily indicate altered mental status. Altered mental status is a broader term that can encompass a range of cognitive and behavioral changes, and Confused is just one possible manifestation of it. Furthermore, the records do not provide any information about the patient's mental status prior to the Confus |
| E1071450 | Administer intravenous potassium chloride to correct hypokalemia. | Hypokalemia is present. | presupposed by an action | Latest potassium 4.1 mmol/L at 2100-01-01 13:50:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E1071450 | Continue inotropic support with milrinone. | Milrinone is currently being given. | presupposed by an action | The records state that the patient is receiving milrinone as an inotropic agent, but there is no record of milrinone being administered in the 24 hours before the decision time. The 'Running at decision time' record for milrinone is not sufficient to support the statement, as it only indicates that the order is active at the decision time, not that the medication has been administered. |
| E1090889 | Assess for potential causes of hypotension. | Hypotension is present. | presupposed by an action | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1099398 | Patient's blood pressure is fluctuating, with systolic readings as high as 202 mmHg and diastolic as low as 60 mmHg. Consider adjusting antihypertensive therapy. | Diastolic blood pressure is as low as 60 mmHg. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1099398 | Patient's respiratory rate is within normal limits but shows variability. Monitor for any changes in respiratory status. | Respiratory rate is within normal limits. | stated outright | The records show that the patient's respiratory rate has varied between 19 and 22 inspirations per minute, but none of these values are within the normal range. The statement is not supported by the records. |
| E1099398 | Patient's respiratory rate is within normal limits but shows variability. Monitor for any changes in respiratory status. | Respiratory rate shows variability. | stated outright | The records show that the patient's respiratory rate has varied between 19 and 22 inspirations per minute, but the statement says it shows variability. The records do not support the statement. |
| E1117947 | Continue non-invasive ventilation to support respiratory function. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records show that the patient is on non-invasive ventilation, but the most recent relevant rows (R31) do not show that it is currently being administered. The statement is not supported by the records. |
| E1171473 | Assess for signs of respiratory distress and adjust mechanical ventilation parameters as needed. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('Tidal Volume (set): 500 mL') was 6.8 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1173453 | Monitor the patient's blood pressure closely due to fluctuations. | Blood pressure is fluctuating. | stated outright | The blood pressure readings show fluctuations, but the statement is not supported because the readings do not show a consistent trend of increasing or decreasing. The readings are fluctuating, but not in a way that would be described as 'rising'. |
| E1173453 | Continue antibiotic therapy with vancomycin. | Vancomycin is currently being given. | presupposed by an action | The records show that vancomycin was ordered, but there is no administration record of it in the 24 hours before the decision time. |
| E1287791 | Continue sedation at -1 RASS score. | The patient is currently receiving sedation. | presupposed by an action | The patient is currently receiving sedation. The records show that lorazepam was ordered (R1) and the patient's RASS score was -4 (R7) and RASS (R8), but there is no record of sedation administration in the 24 hours before the decision time. |
| E1290248 | Monitor patient's vital signs closely due to fluctuating SpO2 and pulse. | SpO2 is fluctuating. | stated outright | The statement says SpO2 is fluctuating, but the most recent measurement (R50) shows a value of 94, which is not fluctuating. The previous measurements (R49 and R48) show values of 100, which is also not fluctuating. Therefore, the statement is not supported by the records. |
| E1290248 | Monitor patient's vital signs closely due to fluctuating SpO2 and pulse. | Pulse is fluctuating. | stated outright | The pulse is fluctuating because the values are changing rapidly, but the records show a consistent decrease in pulse rate over the past few hours, with the most recent value being 67. This does not support the statement that the pulse is fluctuating. |
| E1290248 | Continue intravenous fluid administration to maintain hydration. | Intravenous fluids are currently being administered. | presupposed by an action | The records mention this treatment but show no administration in the 24 h before the decision. (Panel verdict: supported.) |
| E1496959 | Monitor blood pressure closely due to significant fluctuations. | Blood pressure has significant fluctuations. | stated outright | The statement says there are significant fluctuations, but the records show a single high reading (232 mmHg) followed by a return to normal. There is no evidence of fluctuations. |
| E1496959 | Continue anticonvulsant therapy for seizure prevention. | Anticonvulsant therapy is currently being given. | presupposed by an action | The records show that anticonvulsant therapy is ordered (R10, R11, R12, R13), but there is no administration record of it in the 24 hours before the decision time. R27 and R36 also mention anticonvulsant therapy, but they are treatment documentation records, not administration records. |
| E1497157 | Monitor electrolyte levels and adjust magnesium infusion as needed. | Magnesium infusion is currently being given. | presupposed by an action | The records show that magnesium infusion was started at 20:00 on 2100-01-01 and continued at various rates until 10:00 on 2100-01-02. However, the statement says that magnesium infusion is currently being given, which is not supported by the records. The records do not show any administration of magnesium at the decision time of 19:30 on 2100-01-02. |
| E1497157 | Continue intravenous fluids to maintain hydration. | Intravenous fluids are currently being given. | presupposed by an action | The records show that intravenous fluids were ordered and administered at 15:45 on 2100-01-01 and are still running at decision time. However, they do not show that the fluids are currently being given. |
| E1619343 | Administer intravenous vancomycin for suspected infection. | Infection is suspected. | presupposed by an action | The statement 'Infection is suspected' is not supported by the records. The records show that vancomycin was administered at 15:30, but there is no evidence of infection or infection suspicion in the records. |
| E1636307 | Continue intravenous sedation and analgesia to maintain patient comfort. | Intravenous sedation is currently being given. | presupposed by an action | The records show that the patient is receiving intravenous sedation, but the most recent administration record is from 02:15, which is more than 24 hours before the decision time. The statement is not supported by the records. |
| E1636307 | Continue intravenous sedation and analgesia to maintain patient comfort. | Intravenous analgesia is currently being given. | presupposed by an action | The records show that nalOXone, HYDROmorphone, and analgesics are ordered and active at decision time, but there is no record of intravenous analgesia being administered in the 24 hours before the decision time. The statement is not supported by the records. |
| E1636307 | Assess patient for signs of respiratory distress and adjust mechanical ventilation settings if necessary. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 9.7 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1672915 | Continue intravenous insulin to manage glucose levels. | Intravenous insulin is currently being given. | presupposed by an action | The records show that insulin lispro was ordered to be given subcutaneously at bedtime, but there is no record of intravenous insulin being administered. The statement is not supported by the records. |
| E1705630 | Continue sedation at a reduced level. | Sedation is currently being given. | presupposed by an action | The AI statement 'Sedation is currently being given' is not supported by the records. Although there are ongoing orders for sedation (R9), the most recent administration records (R11 and R12) show that sodium chloride 0.9% is being administered continuously, not sedation. The sedation scale measurements (R14, R19, R22, R23, R27, R29, R32, R34, R37, R39, R41, R42, R44, R47) do not indicate that sed |
| E1823727 | Continue IV fluids and electrolyte management. | Electrolyte management is currently being given. | presupposed by an action | The records show that electrolyte management is being given, but the administration records do not support this statement. The medication orders for IV fluids and electrolyte management are active at decision time, but there is no record of administration of these medications in the 24 hours before the decision time. |
| E1823727 | Assess for signs of infection given leukocytosis. | Leukocytosis is present. | stated outright | Latest WBC 8.3 K/mm3 at 2100-01-02 10:00:00 (reference 4 to 11) is normal, not consistent with 'high'. |
| E1824650 | Wean off mechanical ventilation. | The patient is currently on mechanical ventilation. | presupposed by an action | The latest record before the decision (2100-01-02 15:35:00) reads 'O2 Delivery Device(s): None (charted: RA)'. |
| E1829278 | Continue intravenous fluid administration to maintain adequate hydration. | Intravenous fluids are currently being administered. | presupposed by an action | The records show that intravenous fluids were administered at 07:45 and are currently being administered, but there is no record of the current administration of intravenous fluids at the decision time. |
| E1829278 | Administer intravenous Nicardipine to manage hypertension. | Hypertension is present. | presupposed by an action | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E1853162 | Increase oxygen flow to 4 L/min due to elevated systolic blood pressure and respiratory rate. | Respiratory rate is elevated. | stated outright | Median respiratory rate over the 6 h before the decision: 20 insp/min (1 readings), normal by the rule 'tachypnea RR > 20; bradypnea RR < 12'. |
| E2230341 | Continue Eptifibatide infusion at 20.6 ml/hour. | Eptifibatide infusion is currently being given. | presupposed by an action | The statement says Eptifibatide infusion is currently being given, but the records show that it was given at 100 ml/hour from 2100-01-01 17:58:00 to 2100-01-02 00:24:00 (R26) and at 20.6 ml/hour from 2100-01-02 05:00:00 to 2100-01-02 05:00:00 (R43). The current administration is not supported by the records. |
| E2418055 | Monitor blood glucose levels and adjust insulin therapy as needed. | Insulin therapy is currently being given. | presupposed by an action | The records show that insulin was ordered, but there is no record of insulin being administered in the 24 hours before the decision time. The statement is not supported by the records. |
| E2609672 | Continue stress ulcer prophylaxis with pantoprazole. | Pantoprazole is currently being given. | presupposed by an action | The records show that pantoprazole was ordered and scheduled to be administered at decision time, but there is no record of it being administered in the 24 hours before the decision time. The statement is not supported by the records. |
| E2757707 | Continue intravenous insulin infusion. | Intravenous insulin infusion is currently being given. | presupposed by an action | The records show that insulin infusion was started at 21:15, but there is no record of it being administered at the decision time (23:07). |
| E2860378 | Continue insulin infusion to manage hyperglycemia. | Insulin infusion is currently being given. | presupposed by an action | The records show that insulin infusion was started at 16:00 on 2100-01-01 and continued with different rates until 18:00 on 2100-01-01 and then again from 02:30 on 2100-01-02. However, the statement says that insulin infusion is currently being given, which is not supported by the records. The most recent administration of insulin was at 02:30 on 2100-01-02, but the statement implies that it is at |
| E2860378 | Monitor blood pressure closely due to fluctuations. | Blood pressure is fluctuating. | stated outright | The records show that the patient's blood pressure was fluctuating, but the most recent measurement (R31) shows a systolic pressure of 102 mmHg, which is not fluctuating. The statement is not supported by the records. |
| E2879373 | Continue IV furosemide for diuretic therapy. | IV furosemide is currently being given. | presupposed by an action | The records show that IV furosemide was ordered, but there is no record of it being administered in the 24 hours before the decision time. |
| E3001552 | Administer IV furosemide to manage fluid overload and ventricular dysfunction. | Fluid overload is present. | clinical judgment | The patient's age and gender are mentioned in R34, but there is no direct evidence of fluid overload. The sodium and chloride levels in R35, R36, R38, R39, R40, R49, and R50 are within normal limits, and there is no indication of fluid overload. The treatment documented in R37 and R41 mentions ventilation and oxygenation, but not fluid overload. The ongoing medication administration in R38, R43, R |
| E3001552 | Administer IV furosemide to manage fluid overload and ventricular dysfunction. | Ventricular dysfunction is present. | clinical judgment | The records state that the patient has ventricular dysfunction, but the current temperature is 98.4 F, which is not indicative of ventricular dysfunction. The records also mention IV furosemide, which is a treatment for fluid overload and ventricular dysfunction, but it does not directly support the statement. |
| E3027283 | Continue non-invasive ventilation with face mask. | The patient is currently on non-invasive ventilation with face mask. | presupposed by an action | The records show that the patient is on non-invasive ventilation with a face mask, but there is no record of administration of the ventilation within the last 24 hours. The statement is not supported by the records. |
| E3027283 | Monitor pain levels and adjust ondansetron as needed. | Ondansetron is currently being given. | presupposed by an action | The medication order for ondansetron shows that it was ordered, but there is no administration record of it in the 24 hours before the decision time. The statement is not supported by the records. |
| E3033795 | Administer furosemide as ordered to manage fluid balance. | Furosemide is ordered. | presupposed by an action | The records show that furosemide was ordered, but there is no record of it being administered. The statement is not supported because it requires administration, not just ordering. |
| E3035113 | Monitor blood glucose levels closely due to fluctuations and risk of hypoglycemia. | Blood glucose levels are fluctuating. | stated outright | The records show fluctuating blood glucose levels, but the most recent measurement (R36) is 70 mg/dL, which is not fluctuating. The AI statement is not supported by the records. |
| E3035113 | Monitor blood glucose levels closely due to fluctuations and risk of hypoglycemia. | There is a risk of hypoglycemia. | clinical judgment | The records show fluctuations in glucose levels, but the statement is about the risk of hypoglycemia. The high glucose levels in R21, R26, R35, and R37 do not support the statement. |
| E3035113 | Continue vancomycin and zosyn IV as ordered for suspected infection. | Zosyn is currently being given. | presupposed by an action | The records mention this treatment but show no administration in the 24 h before the decision. (Panel verdict: supported.) |
| E3035113 | Continue vancomycin and zosyn IV as ordered for suspected infection. | Infection is suspected. | clinical judgment | The records show that vancomycin and Zosyn IV were administered at 10:15 and 10:16, respectively, but the statement says they should be continued as ordered for suspected infection. This suggests that the infection is not supported by the records, as the medications were only administered once and not as part of an ongoing treatment plan. |
| E3053511 | Continue midazolam for sedation. | Midazolam is currently being given. | presupposed by an action | The records show that midazolam was administered at 16:00, but the current administration of midazolam is not supported by the records. The most recent administration of midazolam was at 17:22, which is after the decision time. Therefore, the statement that midazolam is currently being given is not supported by the records. |
| E3110594 | Monitor patient's blood pressure closely, as it has fluctuated significantly. | Blood pressure has fluctuated significantly. | stated outright | The records show that the patient's blood pressure has fluctuated, but the statement says it has fluctuated significantly. The records do not show a significant fluctuation. |
| E3110594 | Continue administration of furosemide to manage fluid status. | Furosemide is currently being given. | presupposed by an action | The records show that furosemide was ordered and scheduled to be administered at 13:30, but there is no record of it being administered at that time. The statement that it is currently being given is not supported by the records. |
| E3115505 | Continue administration of intravenous methylprednisolone. | Intravenous methylprednisolone is currently being given. | presupposed by an action | The records show that methylprednisolone was ordered at 04:14, but there is no administration record of it in the 24 hours before the decision time. The statement is not supported by the records. |
| E3124669 | Continue pain management with oral medications as needed. | Pain management with oral medications is currently being given. | presupposed by an action | The records show that the patient is receiving oral medications for pain management, but the current administration of these medications is not supported by the records. The most recent administration records are from 21:56, which is before the decision time of 03:21:00. Therefore, the statement that pain management with oral medications is currently being given is not supported by the records. |
| E3130379 | Continue non-invasive ventilation with BiPAP settings. | The patient is currently on non-invasive ventilation with BiPAP. | presupposed by an action | The records show that the patient is on BiPAP, but the most recent relevant rows do not show administration of BiPAP in the 24 hours before the decision time. The 'Running at decision time' record is not present. |
| E3148216 | Continue sedation at the RASS score of 0 to maintain patient comfort. | Sedation is currently being given. | presupposed by an action | The records show that the patient's sedation score is 0 and the respiratory rate is 12/min, but there is no record of sedation being administered. The statement is not supported by the records. |
| E3150018 | Continue sedative and anti-psychotic medications for pain and agitation. | Sedative medications are currently being given. | presupposed by an action | The records show that sedative medications were ordered and administered, but the statement says they are currently being given. The most recent administration record is from 00:06, which is before the decision time of 23:33. Therefore, the statement is not supported. |
| E3150018 | Continue sedative and anti-psychotic medications for pain and agitation. | Anti-psychotic medications are currently being given. | presupposed by an action | The records show that the patient is receiving anti-psychotic, sedative, and antidepressant medications for pain and agitation, but they do not show that these medications are currently being given. The most recent relevant records show that the medications were ordered at 00:06, but there is no record of administration at the decision time. |
| E3170528 | Monitor blood pressure closely due to fluctuations. | Blood pressure is fluctuating. | stated outright | The records show that the patient's blood pressure has been fluctuating, but the most recent measurement (R43) shows a mean of 113 mmHg, which is not fluctuating. The statement is not supported by the records. |
| E3170528 | Continue intravenous fluids to maintain hydration. | Intravenous fluids are currently being given. | presupposed by an action | The records show that intravenous fluids are being administered, but the statement is not supported because the records do not show that the fluids are being given currently. The records show that the medication DOCUSATE SODIUM 100 MG PO CAPS PO BID and DOCUSATE SODIUM 50 MG/5ML PO LIQD Per NG tube BID are running at decision time, but this does not necessarily mean that intravenous fluids are the |
| E3205786 | Continue levetiracetam for seizure prophylaxis. | Levetiracetam is currently being given. | presupposed by an action | The statement that Levetiracetam is currently being given is not supported by the records. Although there is a medication administration record for Levetiracetam (R38), it is a scheduled order that started at 04:00, and the decision time is 22:25. There is no record of Levetiracetam being administered at the decision time. |
| E3220742 | Continue intravenous sodium chloride for fluid management. | Intravenous sodium chloride is currently being given. | presupposed by an action | The statement says that intravenous sodium chloride is currently being given, but the records show that it was administered at 22:00 on 2099-12-31 and again at 03:00 on 2100-01-01. This does not support the statement that it is currently being given. |
| E3223097 | Continue pain management with IV morphine as needed. | IV morphine is currently being given. | presupposed by an action | The records show that morphine was ordered and administered at various times, but there is no record of it being given at the decision time. The statement is not supported by the records. |
| E3237226 | Continue non-invasive ventilation as needed. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records show that the patient was on non-invasive ventilation, but the most recent relevant rows (R46, R47, R48) show a different blood pressure reading, which contradicts the statement. Also, the records do not show any administration of non-invasive ventilation in the 24 hours before the decision time. |

## 5. Judge panel

131 items went to the judge panel. Agreement: {'1/1': 131} (split = no majority; the conservative label was used and the item needs human review).

## 6. Per-case score sheets

| Case | Facts | supported | not_supported | not_addressed | unverifiable | Treatment agreement | Vital recall | All recall |
|---|---|---|---|---|---|---|---|---|
| E153972 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E172015 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E184757 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E211144 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E284265 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E297175 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E322290 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E375854 | 0 | - | - | - | - | 0.0% | - | - |
| E383358 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E395323 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E405746 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E454584 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E467819 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E490454 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 50.0% | - | - |
| E521456 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 50.0% | - | - |
| E664474 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E733082 | 4 | 25.0% | 75.0% | 0.0% | 0.0% | 0.0% | - | - |
| E756295 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E758325 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E826669 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E850469 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E876429 | 0 | - | - | - | - | 0.0% | - | - |
| E899746 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E942382 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E962227 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E978037 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1056063 | 5 | 0.0% | 80.0% | 20.0% | 0.0% | - | - | - |
| E1057910 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E1057967 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1064283 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1065859 | 4 | 25.0% | 50.0% | 25.0% | 0.0% | 0.0% | - | - |
| E1068212 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071224 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071450 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1090039 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1090889 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1099398 | 7 | 57.1% | 42.9% | 0.0% | 0.0% | - | - | - |
| E1117947 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1121034 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1171473 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | - | - |
| E1173453 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1177589 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1287791 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1290248 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1449360 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1496959 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1497157 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1588473 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1592666 | 2 | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | - | - |
| E1619343 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1636307 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1653043 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1672915 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1674875 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1682105 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
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
| E1856821 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2230341 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E2309912 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2418055 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 50.0% | - | - |
| E2419768 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2558122 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2609672 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2714303 | 0 | - | - | - | - | - | - | - |
| E2725629 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2757707 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2814579 | 0 | - | - | - | - | 0.0% | - | - |
| E2860378 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2879373 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3001552 | 4 | 25.0% | 50.0% | 25.0% | 0.0% | 50.0% | - | - |
| E3027283 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 50.0% | - | - |
| E3033795 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3035113 | 5 | 20.0% | 80.0% | 0.0% | 0.0% | 0.0% | - | - |
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
| E3152779 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E3170528 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3178242 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3205786 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3220742 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3223097 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E3233620 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E3237226 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
