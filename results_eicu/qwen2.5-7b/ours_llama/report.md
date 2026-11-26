# Evaluation of AI clinical suggestions against patient records

- Input: `eicu_triples_qwen2.5-7b.json`; 100 cases, 2.99 AI suggestions per case on average.
- Models: atomizer `deepseek-v4-pro:0813:cloud`; judge panel `llama3.1:8b-instruct-q4_K_M` (majority vote; reasoning mode: none); 131 new model calls, 0 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 27.4% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 173 |
| supported / not_supported / not_addressed / unverifiable | 78 / 86 / 9 / 0 |
| Fact accuracy = supported / (supported + not_supported) | 47.6% |
| Cases with at least one not_supported fact | 57 / 100 |
| Omitted findings: abnormalities the clinicians treated that no AI fact mentions | 0 / 0 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 51 | 54.9% | {'not_supported': 23, 'supported': 28} |
| presupposed by an action | 110 | 47.1% | {'supported': 48, 'not_supported': 54, 'not_addressed': 8} |
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
| E153972 | Monitor patient's hemodynamic stability closely given the fluctuating blood pressure readings. | Blood pressure readings are fluctuating. | stated outright | The records show that the patient's blood pressure was fluctuating, but the most recent measurement (R50) is 123 mmHg, which is not the highest value. The statement is not supported by the records. |
| E172015 | Continue administration of intravenous fluids. | Intravenous fluids are currently being given. | presupposed by an action | The statement 'Intravenous fluids are currently being given' is not supported by the records. Although there is an ongoing administration of '1000 ML  -  KCL IN DEXTROSE-NACL 20-5-0.45 MEQ/L-%-% IV SOLN IV Continuous' (R26), it is not clear if this is an intravenous fluid. The statement is not supported by any other records. |
| E184757 | Monitor blood pressure closely due to fluctuations. | Blood pressure is fluctuating. | stated outright | The records show fluctuating blood pressure readings, but the statement is about the decision time, which is 2100-01-02 23:48:00. The most recent relevant records are R49 and R50, which show diastolic and systolic blood pressure readings of 92 mmHg and 124 mmHg, respectively. These readings do not support the statement that blood pressure is fluctuating. |
| E297175 | Monitor patient's respiratory status closely due to ongoing respiratory distress. | Respiratory distress is ongoing. | stated outright | The records show that the patient's respiratory rate has been fluctuating, with values ranging from 15 to 26 breaths per minute. While the current respiratory rate is 18 breaths per minute, which is within the normal range, the patient's respiratory distress is ongoing, as indicated by the presence of non-invasive ventilation and the administration of bronchodilators and glucocorticoids. However,  |
| E322290 | Continue anticoagulant therapy with warfarin. | Warfarin is currently being given. | presupposed by an action | The statement 'Warfarin is currently being given' is not supported by the records. Although there is a medication order for warfarin (R40), it does not show administration of the drug. The records do mention anticoagulant administration (R16, R28, R29), but this is not specific to warfarin. |
| E395323 | Continue vancomycin and piperacillin/tazobactam for suspected sepsis. | Vancomycin is currently being given. | presupposed by an action | The records show that vancomycin was ordered and administered, but the current administration status is not clear. R13 shows that vancomycin was documented as a treatment, but R21 shows that a different medication (Sodium Chloride) is running at decision time. There is no clear indication that vancomycin is currently being given. |
| E395323 | Continue vancomycin and piperacillin/tazobactam for suspected sepsis. | Sepsis is suspected. | clinical judgment | The records show that piperacillin/tazobactam was ordered, but there is no record of it being administered in the 24 hours before the decision time. Vancomycin was also ordered, but there is no record of it being administered in the 24 hours before the decision time. |
| E405746 | Continue labetalol for hypertension management. | Labetalol is currently being given. | presupposed by an action | The records show that labetalol was ordered at 15:59 on 2099-12-31, but there is no record of it being administered within the last 24 hours. The statement that labetalol is currently being given is not supported by the records. |
| E405746 | Continue labetalol for hypertension management. | Hypertension is present. | clinical judgment | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E490454 | Continue non-invasive ventilation with a BiPAP/CPAP mask. | The patient is currently on non-invasive ventilation with a BiPAP/CPAP mask. | presupposed by an action | The patient is currently on non-invasive ventilation with a BiPAP/CPAP mask. The records show that the patient has been on non-invasive ventilation with a BiPAP/CPAP mask for most of the time, but there is a record at 23:20 that shows the O2 Delivery Device is still a BiPAP mask, which suggests that the ventilation mode may have been changed. Therefore, the statement is not supported. |
| E521456 | Administer 10 mL of magnesium sulfate intravenously for potential delirium. | Delirium is potentially present. | clinical judgment | The records show that the patient's delirium score was No at 21:00 on 2100-01-01 and 12:00 on 2100-01-02, but the statement says that delirium is potentially present. The records do not show any administration of magnesium sulfate, which is mentioned in the original sentence. Therefore, the statement is not supported by the records. |
| E664474 | Continue non-invasive ventilation to maintain adequate oxygenation and ventilation. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records show that the patient is on non-invasive ventilation, but the most recent relevant rows (R47, R48, R49, R50) show that the patient's blood pressure is not within a normal range, which contradicts the statement that the patient is currently on non-invasive ventilation. |
| E733082 | Monitor blood glucose levels closely due to recent high readings and risk of hypoglycemia. | There is a risk of hypoglycemia. | clinical judgment | The records show recent high glucose readings, but there is no evidence that the patient is currently receiving insulin or other treatments for hypoglycemia. The medication orders for glucose and glucagon are active at decision time, but this does not necessarily mean they are being administered. |
| E733082 | Administer IV fluids to maintain adequate hydration and blood pressure support. | Hydration is inadequate. | presupposed by an action | The records show that IV fluids are being administered, but the statement 'Hydration is inadequate' is not supported by the records. The latest sodium level is 135 mmol/L, which is within the normal range. Additionally, the respiratory rate is fluctuating, but there is no indication of inadequate hydration. |
| E733082 | Administer IV fluids to maintain adequate hydration and blood pressure support. | Blood pressure support is needed. | presupposed by an action | The most recent blood pressure measurement before the decision time is 104 mmHg systolic, which is not high enough to require blood pressure support. However, the statement is not supported because the records do not show that the patient is receiving blood pressure support at the decision time. |
| E850469 | Continue aggressive fluid resuscitation to maintain adequate perfusion. | Aggressive fluid resuscitation is currently being given. | presupposed by an action | The records state that aggressive volume resuscitation is being given, but there is no administration record of it in the 24 hours before the decision time, and no 'Running at decision time' record. The statement is not supported. |
| E942382 | Monitor the patient's blood pressure and respiratory rate closely, as they have been fluctuating significantly. | Respiratory rate has been fluctuating significantly. | stated outright | The respiratory rate has been fluctuating significantly, but the most recent measurement at decision time (2100-01-02 15:23:00) is 18 insp/min, which is not fluctuating. The previous measurement (R35) was 12 insp/min, and the measurement before that (R34) was 23 insp/min, which is a significant fluctuation. However, the most recent measurement does not support the statement. |
| E942382 | Continue the administration of diltiazem to manage the patient's heart rate and rhythm. | Diltiazem is currently being given. | presupposed by an action | The records show that diltiazem was ordered and administered, but the administration record (R20) shows that it was started at 17:04, which is after the decision time. Therefore, the statement that diltiazem is currently being given is not supported. |
| E1056063 | Monitor patient's heart rate and respiratory rate closely due to variability and potential for respiratory depression. | Heart rate is variable. | stated outright | The statement 'Heart rate is variable' is not supported because the heart rate measurements in the records show a range of values, but none of them indicate a significant variability that would warrant a statement like this. The heart rate measurements are mostly within a normal range, with some fluctuations, but they do not suggest a variable heart rate. |
| E1056063 | Monitor patient's heart rate and respiratory rate closely due to variability and potential for respiratory depression. | Respiratory rate is variable. | stated outright | The statement says the respiratory rate is variable, but R13 shows a respiratory rate of 18 insp/min, which is not variable. The statement is not supported by the records. |
| E1056063 | Monitor patient's heart rate and respiratory rate closely due to variability and potential for respiratory depression. | There is potential for respiratory depression. | clinical judgment | The records show that the patient is receiving oxygen therapy via a nasal cannula, but do not indicate that the patient is receiving ventilation. The statement about potential for respiratory depression is not supported by the records. |
| E1056063 | Continue oxygen therapy with nasal cannula at 2 L/min to maintain adequate oxygen saturation. | Oxygen therapy with nasal cannula at 2 L/min is currently being given. | presupposed by an action | The records show that oxygen therapy with nasal cannula at 2 L/min was ordered and the flow rate was measured, but there is no record of administration or administration at the decision time. |
| E1056063 | Assess for signs of magnesium toxicity, given the recent administration of magnesium sulfate. | Magnesium sulfate was recently administered. | stated outright | The records show that magnesium sulfate was administered at 15:33, but the statement says it was recently administered. The most recent relevant records are from 15:33, and they show that magnesium sulfate was administered, but they do not show that it was administered recently. Therefore, the statement is not supported. |
| E1057967 | Monitor blood glucose levels closely given the patient's fluctuating readings and risk of sepsis. | Blood glucose readings are fluctuating. | stated outright | The records show fluctuating blood glucose levels, but the current level is 113 mg/dL (R23), which is not rising. The patient is receiving insulin aspart (R3), but the dose is not specified. The glucose levels have been fluctuating, but the current level is not the highest. |
| E1057967 | Monitor blood glucose levels closely given the patient's fluctuating readings and risk of sepsis. | The patient is at risk of sepsis. | clinical judgment | The records mention the patient's risk of sepsis, but do not show any administration of antibiotics. The patient is on oxygen therapy with a nasal cannula, which is not sufficient to address the risk of sepsis. |
| E1057967 | Continue pain management with PRN orders for Dilaudid IV, oxyCODONE PO, and Tylenol PO as needed. | Pain management is currently being given. | presupposed by an action | The statement 'Pain management is currently being given' is not supported by the records. Although Dilaudid IV was given once (R33), the records do not show that pain management is currently being given. The medication orders for Tylenol PO q6hr PRN (R44), oxyCODONE PO q4hr PRN (R45), and Dilaudid IV q2hr PRN (R46) are active at decision time, but this does not necessarily mean that painmanagement |
| E1064283 | Administer potassium chloride PO to address low potassium levels. | Potassium is low. | stated outright | Latest potassium 4.1 mmol/L at 2100-01-02 10:38:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E1065859 | Monitor blood glucose levels closely due to persistent hyperglycemia. | Hyperglycemia is present. | stated outright | Latest glucose 96 mg/dL at 2100-01-02 19:40:00 (reference 70 to 100) is normal, not consistent with 'high'. |
| E1065859 | Assess for signs of hypovolemia or sepsis given the patient's hypotension and altered mental status. | Altered mental status is present. | stated outright | The statement 'Altered mental status is present' is not supported by the records. The record R16 shows 'Best Verbal Response: Confused', which indicates altered mental status, but the statement is present-tense and the records do not show that the patient's mental status was altered at the decision time. The record R16 is from 01:00 on 2100-01-02, but the decision time is 2100-01-02 20:54:00. The  |
| E1071450 | Administer intravenous potassium chloride to correct hypokalemia. | Hypokalemia is present. | presupposed by an action | Latest potassium 4.1 mmol/L at 2100-01-01 13:50:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E1071450 | Continue inotropic support with milrinone. | Milrinone is currently being given. | presupposed by an action | The records show that milrinone was ordered and administered, but the most recent administration was 3 hours ago. The statement says it is currently being given, so it is not supported. |
| E1090889 | Assess for potential causes of hypotension. | Hypotension is present. | presupposed by an action | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1099398 | Patient's blood pressure is fluctuating, with systolic readings as high as 202 mmHg and diastolic as low as 60 mmHg. Consider adjusting antihypertensive therapy. | Diastolic blood pressure is as low as 60 mmHg. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1099398 | Patient's respiratory rate is within normal limits but shows variability. Monitor for any changes in respiratory status. | Respiratory rate is within normal limits. | stated outright | The records show that the respiratory rate has varied between 19 and 22 inspirations per minute, but none of these values are within the normal limits. The statement is not supported by the records. |
| E1117947 | Continue non-invasive ventilation to support respiratory function. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records state that the patient is on non-invasive ventilation, but the most recent relevant rows show that the patient's blood pressure is fluctuating and not necessarily supported by the ventilation. The records do not show that the ventilation was discontinued or changed to invasive ventilation. |
| E1171473 | Assess for signs of respiratory distress and adjust mechanical ventilation parameters as needed. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('Tidal Volume (set): 500 mL') was 6.8 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1173453 | Monitor the patient's blood pressure closely due to fluctuations. | Blood pressure is fluctuating. | stated outright | The records show fluctuating blood pressure readings, but the statement is about the blood pressure being fluctuating, which is not supported by the records. The records show that the blood pressure is fluctuating, but the statement is about the blood pressure being fluctuating, which is not supported by the records. |
| E1173453 | Continue antibiotic therapy with vancomycin. | Vancomycin is currently being given. | presupposed by an action | The statement says vancomycin is currently being given, but the records show that it was ordered (R13) but there is no administration record in the 24 hours before the decision time. |
| E1287791 | Continue sedation at -1 RASS score. | The patient is currently receiving sedation. | presupposed by an action | The patient is currently receiving sedation. The records show that the patient has been receiving sedation, but the most recent measurement (R50) shows a sedation score of 1, which indicates that the patient is no longer receiving sedation. Therefore, the statement is not supported. |
| E1290248 | Monitor patient's vital signs closely due to fluctuating SpO2 and pulse. | SpO2 is fluctuating. | stated outright | The most recent SpO2 measurement is 94, which does not support the statement that SpO2 is fluctuating. |
| E1290248 | Monitor patient's vital signs closely due to fluctuating SpO2 and pulse. | Pulse is fluctuating. | stated outright | The pulse is fluctuating because the values are changing rapidly, but the records show a consistent decrease in pulse rate over the past 24 hours, with the most recent value being 67. This does not support the statement that the pulse is fluctuating. |
| E1290248 | Continue intravenous fluid administration to maintain hydration. | Intravenous fluids are currently being administered. | presupposed by an action | The records mention this treatment but show no administration in the 24 h before the decision. (Panel verdict: supported.) |
| E1496959 | Monitor blood pressure closely due to significant fluctuations. | Blood pressure has significant fluctuations. | stated outright | The statement says there are significant fluctuations, but the highest value in the 24 hours before the decision time is 232 mmHg, which is not fluctuating. The statement is not supported by the records. |
| E1496959 | Continue anticonvulsant therapy for seizure prevention. | Anticonvulsant therapy is currently being given. | presupposed by an action | The records show that anticonvulsant therapy is ordered (R9, R10, R11, R12) and running at decision time (R17, R18), but there is no record of it being administered in the 24 hours before the decision time. The statement is not supported by the records. |
| E1497157 | Monitor electrolyte levels and adjust magnesium infusion as needed. | Magnesium infusion is currently being given. | presupposed by an action | The records show that magnesium infusion was started at 20:00 on 2100-01-01 and continued at various rates until 10:00 on 2100-01-02. However, the statement says that magnesium infusion is currently being given, which is not supported by the records. The records do not show any administration of magnesium at the decision time of 19:30 on 2100-01-02. |
| E1619343 | Administer intravenous vancomycin for suspected infection. | Infection is suspected. | presupposed by an action | The statement 'Infection is suspected' is not supported by the records. The records show that vancomycin was administered at 15:30, but there is no evidence of infection or suspicion of infection in the records. |
| E1636307 | Continue intravenous sedation and analgesia to maintain patient comfort. | Intravenous sedation is currently being given. | presupposed by an action | The records show that intravenous sedation was ordered (R3, R4, R5), but there is no record of it being administered in the 24 hours before the decision time. The statement is not supported by the records. |
| E1636307 | Continue intravenous sedation and analgesia to maintain patient comfort. | Intravenous analgesia is currently being given. | presupposed by an action | The records show that nalOXone, HYDROmorphone, and oxyCODONE-acetaminophen are ordered and active at decision time, but there is no record of intravenous analgesia being administered in the 24 hours before the decision time. Additionally, fentaNYL is ordered and active at decision time, but it is administered intravenously, not intravenously as analgesia. |
| E1636307 | Assess patient for signs of respiratory distress and adjust mechanical ventilation settings if necessary. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 9.7 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1672915 | Continue intravenous insulin to manage glucose levels. | Intravenous insulin is currently being given. | presupposed by an action | The records show that insulin lispro was ordered to be given subcutaneously at bedtime (R19), but there is no record of intravenous insulin being administered recently (R10 is a running order, not an administration record). |
| E1705630 | Continue sedation at a reduced level. | Sedation is currently being given. | presupposed by an action | The AI statement says 'Sedation is currently being given', but the records show that LORazepam is ordered to be given every 4 hours (R10), and sodium chloride 0.9% is being administered continuously (R12 and R13). There is no record of sedation being given at the decision time. |
| E1781359 | Continue intravenous fluid administration. | Intravenous fluids are currently being administered. | presupposed by an action | The statement that intravenous fluids are currently being administered is not supported by the records. While there are records of intravenous fluid administration (R8, R13, R20, R25, R26, R29, R45), they do not all show that the fluids are being administered at the decision time. Additionally, there are records of other medications and treatments being administered (R9, R10, R11, R12, R13, R14, R |
| E1823727 | Continue IV fluids and electrolyte management. | Electrolyte management is currently being given. | presupposed by an action | The statement 'Electrolyte management is currently being given' is not supported by the records. Although there are records of ongoing administration of Sodium Chloride 0.9% 1,000 ML BAG IV CONT (R15) and ongoing orders for Sodium Chloride 0.9% 1,000 ML BAG IV PRN (R34), these do not directly support the statement that electrolyte management is being given. The records do not mention any specific, |
| E1823727 | Assess for signs of infection given leukocytosis. | Leukocytosis is present. | stated outright | Latest WBC 8.3 K/mm3 at 2100-01-02 10:00:00 (reference 4 to 11) is normal, not consistent with 'high'. |
| E1824650 | Wean off mechanical ventilation. | The patient is currently on mechanical ventilation. | presupposed by an action | The latest record before the decision (2100-01-02 15:35:00) reads 'O2 Delivery Device(s): None (charted: RA)'. |
| E1829278 | Continue intravenous fluid administration to maintain adequate hydration. | Intravenous fluids are currently being administered. | presupposed by an action | The records show that intravenous fluids were administered at 07:45, but there is no record of them being administered at the decision time. However, there is a record of a continuous infusion of sodium chloride 0.9% IV solution at 09:30, which suggests that intravenous fluids are still being administered. |
| E1829278 | Administer intravenous Nicardipine to manage hypertension. | Hypertension is present. | presupposed by an action | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E1837964 | Continue antihypertensive therapy with metoprolol. | Metoprolol is currently being given. | presupposed by an action | The records show that Metoprolol Succinate was ordered to be given daily, but there is no record of it being administered at the decision time. The most recent administration of Metoprolol Succinate was on 2100-01-02 14:00:00, but it was given as a daily dose, not at the decision time. |
| E1853162 | Increase oxygen flow to 4 L/min due to elevated systolic blood pressure and respiratory rate. | Respiratory rate is elevated. | stated outright | Median respiratory rate over the 6 h before the decision: 20 insp/min (1 readings), normal by the rule 'tachypnea RR > 20; bradypnea RR < 12'. |
| E2230341 | Continue Eptifibatide infusion at 20.6 ml/hour. | Eptifibatide infusion is currently being given. | presupposed by an action | The records show that Eptifibatide infusion was started at 17:58 on 2100-01-01 and at 04:24 on 2100-01-02, but the current rate is 20.6 ml/hour, which is not supported by the records. The records show that Eptifibatide was infused at 100 units/hour on 2100-01-01 and at 20.6 ml/hour on 2100-01-02, but the current rate is not supported by the records. |
| E2418055 | Monitor blood glucose levels and adjust insulin therapy as needed. | Insulin therapy is currently being given. | presupposed by an action | The statement 'Insulin therapy is currently being given' is not supported by the records. The record R25 shows that insulin therapy is scheduled to be given, but it does not show that it is currently being given. The record R10 shows that HEPARIN is being administered, but it does not mention insulin therapy. |
| E2419768 | Continue IV fluid administration to maintain hydration. | IV fluids are currently being administered. | presupposed by an action | The statement 'IV fluids are currently being administered' is not supported by the records. Although there are records of IV fluids being administered (R5 and R30), they are scheduled orders that started before the decision time, and there is no record of IV fluids being administered at the decision time. |
| E2609672 | Continue stress ulcer prophylaxis with pantoprazole. | Pantoprazole is currently being given. | presupposed by an action | The statement that Pantoprazole is currently being given is not supported by the records. The record R27 shows that Pantoprazole is scheduled to be given at 03:45, but it does not show that it has been administered. Therefore, the statement is not supported. |
| E2860378 | Continue insulin infusion to manage hyperglycemia. | Insulin infusion is currently being given. | presupposed by an action | The records show that insulin infusion was started at 16:00 on 2100-01-01 and continued with different rates until 02:30 on 2100-01-02. However, the statement says that insulin infusion is currently being given, which is not supported by the records. The records do not show any administration of insulin in the 24 hours before the decision time. |
| E2860378 | Monitor blood pressure closely due to fluctuations. | Blood pressure is fluctuating. | stated outright | The records show that the patient's blood pressure was fluctuating, but the most recent measurement (R31) is 102 mmHg, which is not fluctuating. The statement is not supported by the records. |
| E2879373 | Continue IV furosemide for diuretic therapy. | IV furosemide is currently being given. | presupposed by an action | The records show that IV furosemide was ordered, but there is no record of it being administered in the 24 hours before the decision time. |
| E3001552 | Administer IV furosemide to manage fluid overload and ventricular dysfunction. | Fluid overload is present. | clinical judgment | The records show that the patient's sodium levels have been fluctuating, but there is no clear indication of fluid overload. The medication orders and administration records do not support the statement. |
| E3027283 | Monitor pain levels and adjust ondansetron as needed. | Ondansetron is currently being given. | presupposed by an action | The statement says Ondansetron is currently being given, but the records show it was ordered (R5) and the infusion is running at decision time (R34), but there is no record of Ondansetron being administered in the 24 hours before the decision time. |
| E3035113 | Monitor blood glucose levels closely due to fluctuations and risk of hypoglycemia. | Blood glucose levels are fluctuating. | stated outright | The records show fluctuating blood glucose levels, but the statement is not supported because it requires recent administration of insulin, which is not shown in the records. The records do show high glucose levels, but the statement is not supported because it requires recent administration of insulin, which is not shown in the records. The records do show high glucose levels, but the statement ' |
| E3035113 | Monitor blood glucose levels closely due to fluctuations and risk of hypoglycemia. | There is a risk of hypoglycemia. | clinical judgment | The records show fluctuations in glucose levels, but the statement is about the risk of hypoglycemia. The recent glucose levels (R20, R25, R34, R36) are high, which does not support the statement. |
| E3035113 | Continue vancomycin and zosyn IV as ordered for suspected infection. | Zosyn is currently being given. | presupposed by an action | The records mention this treatment but show no administration in the 24 h before the decision. (Panel verdict: supported.) |
| E3035113 | Continue vancomycin and zosyn IV as ordered for suspected infection. | Infection is suspected. | clinical judgment | The records show that vancomycin and Zosyn IV were administered once, but there is no evidence that they are currently being given or that the infection is suspected. The administration records do not indicate ongoing treatment. |
| E3053511 | Continue midazolam for sedation. | Midazolam is currently being given. | presupposed by an action | The records show that midazolam was administered at 16:00 and 17:22, but the statement says it is currently being given. The most recent administration record is at 17:22, which is within the 24 hours before the decision time, so the statement is supported by the administration record of midazolam in the 24 hours before the decision time. However, the records also show that midazolam was given at  |
| E3110594 | Monitor patient's blood pressure closely, as it has fluctuated significantly. | Blood pressure has fluctuated significantly. | stated outright | The records show that the patient's blood pressure has fluctuated, but the most recent measurement (R46) shows a systolic pressure of 125 mmHg, which is higher than the previous measurements. The statement 'Blood pressure has fluctuated significantly' is not supported by the records, as the fluctuation is not significant in the context of the patient's overall blood pressure readings. |
| E3110594 | Continue administration of furosemide to manage fluid status. | Furosemide is currently being given. | presupposed by an action | The records show that furosemide was ordered and scheduled to be administered at 13:30, but there is no record of it being administered at that time. The statement that it is currently being given is not supported by the records. |
| E3115505 | Continue administration of intravenous methylprednisolone. | Intravenous methylprednisolone is currently being given. | presupposed by an action | The statement says that intravenous methylprednisolone is currently being given, but the records show that it was administered at 04:14, and there is a later order for Q24HR administration (R43). |
| E3124669 | Continue pain management with oral medications as needed. | Pain management with oral medications is currently being given. | presupposed by an action | The records show that the patient is receiving oral medications for pain management, but the current administration of these medications is not supported by the records. The records show that the patient is receiving bronchodilators, antibacterials, and glucocorticoid administration, but these are not the medications being given for pain management. The current administration of oral medications,  |
| E3130379 | Continue non-invasive ventilation with BiPAP settings. | The patient is currently on non-invasive ventilation with BiPAP. | presupposed by an action | The records show that the patient is on BiPAP, but the statement is about the patient being currently on non-invasive ventilation with BiPAP. The records do not show that the patient is currently on non-invasive ventilation, only that they are on BiPAP. The statement is not supported by the records. |
| E3148216 | Continue sedation at the RASS score of 0 to maintain patient comfort. | Sedation is currently being given. | presupposed by an action | The records show that the patient's sedation score is 0 and the sedation scale is RASS, but there is no record of sedation being administered. The statement is not supported by the records. |
| E3150018 | Continue sedative and anti-psychotic medications for pain and agitation. | Sedative medications are currently being given. | presupposed by an action | The records show that lorazepam, vanafaxine (Effexor), and haldol are being given for pain and agitation, but they do not show that sedative medications are currently being given. |
| E3150018 | Continue sedative and anti-psychotic medications for pain and agitation. | Anti-psychotic medications are currently being given. | presupposed by an action | The records show that the patient is receiving anti-psychotic and sedative medications, but there is no record of administration of these medications in the 24 hours before the decision time. The 'Running at decision time' rule does not apply here because the medications are not being given now. The records do not show any administration of these medications, so the statement is not supported. |
| E3170528 | Monitor blood pressure closely due to fluctuations. | Blood pressure is fluctuating. | stated outright | The records show that the patient's blood pressure has been fluctuating, but the most recent measurement (R43) shows a mean of 113 mmHg, which is not fluctuating. The statement is not supported by the records. |
| E3170528 | Continue intravenous fluids to maintain hydration. | Intravenous fluids are currently being given. | presupposed by an action | The records show that intravenous fluids are being administered, but the statement is not supported because the records do not show that the fluids are being given currently. The records show that the medication DOCUSATE SODIUM 100 MG PO CAPS PO BID and DOCUSATE SODIUM 50 MG/5ML PO LIQD Per NG tube BID are running at decision time, but this does not support the statement that intravenous fluids is |
| E3205786 | Continue levetiracetam for seizure prophylaxis. | Levetiracetam is currently being given. | presupposed by an action | The medication administration record for levetiracetam shows that it was scheduled to be given at 04:00, but there is no record of it being administered at the decision time of 22:25:00. Therefore, the statement that levetiracetam is currently being given is not supported. |
| E3223097 | Continue pain management with IV morphine as needed. | IV morphine is currently being given. | presupposed by an action | The statement says IV morphine is currently being given, but the most recent relevant record (R13) shows that morphine is ordered IV PRN, but it does not show that it is currently being given. There is no record of IV morphine administration in the 24 hours before the decision time. |
| E3237226 | Continue non-invasive ventilation as needed. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records show that the patient is on non-invasive ventilation, but the most recent relevant rows (R46, R47, R48) contradict the statement. The statement is not supported even when earlier rows agree. |

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
| E297175 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E322290 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E375854 | 0 | - | - | - | - | 0.0% | - | - |
| E383358 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E395323 | 3 | 0.0% | 66.7% | 33.3% | 0.0% | 0.0% | - | - |
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
| E942382 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E962227 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E978037 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1056063 | 5 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E1057910 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E1057967 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1064283 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1065859 | 4 | 25.0% | 50.0% | 25.0% | 0.0% | 0.0% | - | - |
| E1068212 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071224 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071450 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1090039 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1090889 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1099398 | 7 | 71.4% | 28.6% | 0.0% | 0.0% | - | - | - |
| E1117947 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1121034 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1171473 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | - | - |
| E1173453 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1177589 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1287791 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1290248 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1449360 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1496959 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1497157 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
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
| E1781359 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1790816 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823356 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823727 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1824650 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1829278 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1837964 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1853162 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | - | - | - |
| E1856821 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2230341 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E2309912 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2418055 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 50.0% | - | - |
| E2419768 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2558122 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2609672 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2714303 | 0 | - | - | - | - | - | - | - |
| E2725629 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2757707 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2814579 | 0 | - | - | - | - | 0.0% | - | - |
| E2860378 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2879373 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3001552 | 4 | 50.0% | 25.0% | 25.0% | 0.0% | 50.0% | - | - |
| E3027283 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 50.0% | - | - |
| E3033795 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
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
| E3220742 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3223097 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E3233620 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E3237226 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
