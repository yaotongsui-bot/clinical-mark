# Evaluation of AI clinical suggestions against patient records

- Input: `eicu_triples_deepseek-v4.1-flash.json`; 100 cases, 3.0 AI suggestions per case on average.
- Models: atomizer `deepseek-v4-pro:0813:cloud`; judge panel `deepseek-v4-pro:0813:cloud` (majority vote; reasoning mode: none); 287 new model calls, 0 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 17.7% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 530 |
| supported / not_supported / not_addressed / unverifiable | 401 / 115 / 14 / 0 |
| Fact accuracy = supported / (supported + not_supported) | 77.7% |
| Cases with at least one not_supported fact | 63 / 100 |
| Omitted findings: abnormalities the clinicians treated that no AI fact mentions | 0 / 0 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 344 | 82.6% | {'supported': 280, 'not_supported': 59, 'not_addressed': 5} |
| presupposed by an action | 169 | 65.8% | {'supported': 106, 'not_supported': 55, 'not_addressed': 8} |
| clinical judgment | 17 | 93.8% | {'not_supported': 1, 'supported': 15, 'not_addressed': 1} |
| vague | 0 | - | {} |

## 2. How close is the AI to what clinicians did?

Target (same class, or the drug the AI named) and direction (continue / stop / adjust) are decided by code; suggestions the rule file cannot classify go to the judge panel.

| Metric | Value |
|---|---|
| Treatment action atoms | 261 |
| Labels | {'not_done': 128, 'unobservable': 27, 'match': 21, 'vague_target': 48, 'condition_not_met': 37} |
| Agreement (strict) = match / (match + partial_match + not_done) | 14.1% |
| Agreement (lenient) = (match + partial_match) / same | 14.1% |

Monitoring/assessment atoms: 331 (reported separately, not part of agreement): {'not_performed': 57, 'performed': 201, 'unobservable': 73}; performed rate among observable items 77.9%. 12 'goal' atoms with no concrete action are not scored.

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
| E172015 | Repeat serum magnesium level given hypomagnesemia (1.1 mg/dL) and recent increase to 1.6 mg/dL, to guide further replacement. | Hypomagnesemia is present. | stated outright | Latest magnesium 1.6 mg/dL at 2100-01-02 21:06:00 (reference 1.6 to 2.6) is normal, not consistent with 'low'. |
| E184757 | Continue scheduled piperacillin-tazobactam 3-0.375 g IV every 8 hours for ongoing infection treatment. | Piperacillin-tazobactam is currently being given. | presupposed by an action | The only record of piperacillin-tazobactam is an administration that started on 2099-12-19 at 21:00, which is more than 24 hours before the decision time of 2100-01-01 23:48. There is no administration record within the 24 hours prior to the decision time to support that it is currently being given. |
| E184757 | Continue scheduled piperacillin-tazobactam 3-0.375 g IV every 8 hours for ongoing infection treatment. | Ongoing infection treatment is needed. | clinical judgment | The records show an admission diagnosis of fistula/abscess and a piperacillin-tazobactam administration running at decision time, but they do not contain any current evidence of an ongoing infection or a stated need for continued treatment. The statement that ongoing infection treatment is needed is not directly supported by the available data. |
| E284265 | Continue diltiazem infusion for rate control of atrial arrhythmia. | Diltiazem infusion is currently being given. | presupposed by an action | The only diltiazem administration record is an infusion that started at 2100-01-01 21:00, which is after the decision time of 2100-01-01 18:11. No administration of diltiazem is documented in the 24 hours before the decision time. |
| E297175 | Continue non-invasive ventilation with FiO2 40% and PEEP 5 cmH2O, monitoring oxygenation and respiratory status. | FiO2 is 40%. | stated outright | The most recent FiO2 measurement before the decision time is 45% (R40), not 40%. Although earlier records show 40%, the latest value contradicts the statement. |
| E322290 | Monitor blood pressure and heart rate closely given recent systolic blood pressure of 91 mmHg and tachycardia. | Tachycardia is present. | stated outright | 0 of 16 heart rate values in the 24 h before the decision were high. |
| E375854 | Assess and manage ongoing hypotension with persistent tachycardia in the setting of GI bleeding and dropping hemoglobin. | Hypotension is present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E375854 | Assess and manage ongoing hypotension with persistent tachycardia in the setting of GI bleeding and dropping hemoglobin. | Tachycardia is present. | stated outright | Median heart rate over the 6 h before the decision: 88.5 bpm (6 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E375854 | Continue monitoring oxygen saturation and administer supplemental oxygen as needed given O2 saturation 94% on 3 L/min nasal cannula. | The patient is on 3 L/min nasal cannula. | stated outright | The records document nasal cannula oxygen therapy at 30-40% (R35, R36), but do not specify a flow rate of 3 L/min. The statement's specific flow rate is not supported by the available documentation. |
| E405746 | Assess for bleeding and monitor hemoglobin/hematocrit given anemia with hemoglobin 7.7–8.5 g/dL and low fibrinogen. | Fibrinogen is low. | stated outright | The most recent fibrinogen values before the decision time are 475 mg/dl (R13) and 341 mg/dl (R31), which are within or above the normal range, not low. Low values appear only after the decision time. |
| E405746 | Monitor oxygen saturation and respiratory status given intermittent desaturation to 91% and 93% in the prior 24 hours. | Desaturation is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no. |
| E454584 | Assess and manage sedation and delirium, considering the patient's fluctuating RASS and CAM-ICU positive status. | RASS is fluctuating. | stated outright | The records contain multiple RASS entries, but none include a numerical score or value. Without recorded RASS values, the claim that the RASS is 'fluctuating' cannot be supported. |
| E454584 | Assess and manage sedation and delirium, considering the patient's fluctuating RASS and CAM-ICU positive status. | CAM-ICU is positive. | stated outright | The records contain multiple CAM-ICU assessments, but none of them document a positive result. The rows only list the scale name 'CAM-ICU' without a score or positive/negative indication, so the statement that CAM-ICU is positive is not supported. |
| E467819 | Continue nicardipine infusion for blood pressure control in intracranial hemorrhage. | Nicardipine infusion is currently being given. | presupposed by an action | The most recent nicardipine administration record (R50) shows an infusion that ended at 00:00 on 2100-01-02, which is more than 24 hours before the decision time of 01:43 on 2100-01-02. There is no record of a nicardipine infusion running at or within 24 hours before the decision time. |
| E490454 | Continue non-invasive ventilation with BiPAP mask given recurrent hypoxemia (SpO2 91% at 23:20) after weaning to nasal cannula. | Recurrent hypoxemia is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E490454 | Assess for possible causes of worsening hypoxemia, including bronchospasm, fluid overload, or mucus plugging, and consider need for bronchodilator therapy or diuresis. | Worsening hypoxemia is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E521456 | Monitor blood glucose closely and continue insulin sliding scale to maintain glycemic control, given recent hypoglycemia and hyperglycemia. | Insulin sliding scale is currently being given. | presupposed by an action | The only record mentioning insulin sliding scale is a treatment documentation from 2100-01-01 20:30, which is over 22 hours before the decision time of 2100-01-02 18:57. There is no administration record of insulin sliding scale within the 24 hours prior to the decision time, so the statement that it is currently being given is not supported. |
| E521456 | Monitor blood glucose closely and continue insulin sliding scale to maintain glycemic control, given recent hypoglycemia and hyperglycemia. | Recent hypoglycemia is present. | stated outright | 0 of 1 glucose values in the 24 h before the decision were low. |
| E521456 | Monitor blood glucose closely and continue insulin sliding scale to maintain glycemic control, given recent hypoglycemia and hyperglycemia. | Recent hyperglycemia is present. | stated outright | 0 of 1 glucose values in the 24 h before the decision were high. |
| E664474 | Continue non-invasive ventilation with pressure support 15 cmH2O and PEEP 5 cmH2O, as documented at 15:07. | The patient is currently on non-invasive ventilation. | presupposed by an action | The only record mentioning non-invasive ventilation is a treatment documentation at 10:32 on 2100-01-01, which is over 13 hours before the decision time of 00:05 on 2100-01-02. There is no administration or 'Running at decision time' record for non-invasive ventilation within the 24 hours before the decision time, so the statement that the patient is currently on it is not supported. |
| E664474 | Monitor oxygen saturation and respiratory rate closely given persistent tachypnea and oxygen requirement. | Tachypnea is persistent. | stated outright | Median respiratory rate over the 6 h before the decision: 19 insp/min (5 readings), normal by the rule 'tachypnea RR > 20; bradypnea RR < 12'. |
| E733082 | Continue scheduled IV antibiotics (Zosyn and vancomycin) and levofloxacin as ordered. | Levofloxacin is currently being given. | presupposed by an action | The records show a levofloxacin administration that started at 15:00 on 2100-01-01, but the decision time is 06:09 on 2100-01-01, which is before that administration. There is no record of levofloxacin being given in the 24 hours before the decision time. |
| E733082 | Monitor vital signs and oxygen saturation closely given persistent tachycardia and borderline oxygen saturation. | Oxygen saturation is borderline. | stated outright | The most recent oxygen saturation values before the decision time are 94% and 96%, which are not borderline but rather low-normal to mildly low. The statement 'borderline' is not supported by these latest readings. |
| E826669 | Continue norepinephrine infusion for hemodynamic support, titrating to maintain adequate mean arterial pressure. | Norepinephrine infusion is currently being given. | presupposed by an action | The records show a norepinephrine infusion was started at 2100-01-01 17:48, which is after the decision time of 2100-01-01 00:46. There is no administration record of norepinephrine in the 24 hours before the decision time, so the statement that it is currently being given is not supported. |
| E850469 | Continue scheduled broad-spectrum antibiotics (ZOSYN and VANCOMYCIN) for sepsis. | VANCOMYCIN is currently being given. | presupposed by an action | The records show a vancomycin administration on 2100-01-01 from 14:33 to 15:18 and a 'Running at decision time' record for vancomycin at 15:30 on 2100-01-01, but no administration or running record within 24 hours before the decision time of 2100-01-02 13:47. Therefore, the statement that vancomycin is currently being given is not supported. |
| E876429 | Continue mechanical ventilation with current settings (FiO2 40%, PEEP 5 cmH2O, PSV 10 cmH2O) and monitor oxygenation and respiratory status. | The patient is currently on mechanical ventilation. | stated outright | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 8.4 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E876429 | Continue vasopressor and sedative infusions (epinephrine, norepinephrine, phenylephrine, propofol) and monitor hemodynamics and sedation. | Phenylephrine is currently being given. | stated outright | Phenylephrine appears in the records, but the only administration records are infusions that started on 2100-01-02 at 01:00 and ended at 13:00, which is before the decision time of 2100-01-01 19:53:00. There is no record of phenylephrine being administered or running at the decision time. |
| E942382 | Continue diltiazem infusion for rate control of atrial arrhythmia. | Diltiazem infusion is currently being given. | presupposed by an action | The records mention diltiazem as a documented treatment (R16) and show an infusion that started and ended at 17:04 on 2100-01-01 (R20), but there is no administration record within 24 hours before the decision time of 2100-01-02 15:23:00. Therefore, the statement that it is currently being given is not supported. |
| E942382 | Monitor heart rate and blood pressure closely given bradycardia and intermittent hypotension. | Intermittent hypotension is present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1056063 | Continue continuous pulse oximetry and vital sign monitoring in the ICU, with attention to intermittent oxygen desaturation and tachycardia. | Intermittent oxygen desaturation is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no. |
| E1056063 | Reassess neurologic status and GCS, and continue psychiatric consultation follow-up for substance overdose management. | Psychiatric consultation is currently ongoing. | presupposed by an action | The records document a Psychiatry consultation was requested or documented on 2100-01-01 at 10:33, but there is no record indicating the consultation is currently ongoing at the decision time of 2100-01-02 10:15. |
| E1057910 | Continue mechanical ventilation with FiO2 0.4 and monitor oxygenation, as the patient remains intubated with GCS 3 and RASS -4. | RASS is -4. | stated outright | The records mention RASS multiple times but only as a label 'Sedation Scale/Score/Goal Sedation Scale: RASS' without any score value. No record shows a RASS score of -4, so the statement is not supported. |
| E1057910 | Monitor blood pressure and titrate vasopressor support as needed, given recent hypotension and current norepinephrine use. | Norepinephrine is currently being given. | stated outright | The only norepinephrine administration record (R1) ended on 2100-01-01 at 15:32, which is more than 24 hours before the decision time of 2100-01-02 05:25. A treatment note (R12) mentions norepinephrine use, but there is no administration record showing it was being given at or near the decision time. |
| E1057967 | Continue supplemental oxygen via nasal cannula to maintain oxygen saturation, given intermittent desaturations to 89-92%. | Supplemental oxygen via nasal cannula is currently being given. | presupposed by an action | The only record mentioning nasal cannula oxygen therapy is R8, which is documented after the decision time (22:06 vs 21:51). There is no administration or device record showing nasal cannula oxygen was being given at the decision time. |
| E1064283 | Continue scheduled prednisone and pyridostigmine therapy for myasthenia gravis. | Pyridostigmine is currently being given. | presupposed by an action | The records mention pyridostigmine only as a documented treatment for neuromyopathy therapy, but there is no medication administration record showing it was given in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E1064283 | Assess for need to intensify antihypertensive therapy given persistent systolic blood pressure >190 mmHg. | Systolic blood pressure is persistently greater than 190 mmHg. | stated outright | No recorded systolic BP matches the stated 190; values in the 24 h before the decision ranged 121 to 217 mmHg (latest 194). |
| E1068212 | Continue monitoring heart rate and blood pressure, given persistent tachycardia (HR 112-130 bpm) and low diastolic pressures. | Diastolic blood pressure is low. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1071224 | Continue heparin infusion at 1300 units/hour, as it is running at the decision point. | Heparin infusion is currently running. | presupposed by an action | The records show a heparin infusion from 2099-12-30 to 2100-01-01 23:00, then a new infusion at 22 units/hour starting 2100-01-01 23:00, and finally a 'Running at decision time' heparin infusion at 1300 units/hour starting 2100-01-02 12:00. However, the decision time is 2100-01-01 16:46, at which point the only active heparin infusion is the one at 22 units/hour, not 1300 units/hour. |
| E1071450 | Continue monitoring hemodynamic status, including pulmonary artery pressures and cardiac output, given recent elevated PA mean and heart rate. | PA mean is elevated. | stated outright | The most recent PA Mean before the decision time is 25 mmHg (R50), which is within the normal range (10-20 mmHg is typical, but 25 is borderline high). However, the statement says 'elevated' and the latest value is not clearly elevated compared to earlier values like 31 or 34. The most recent value does not support the claim of current elevation. |
| E1090039 | Monitor hemodynamic status and response to vasoactive infusions (norepinephrine, dopamine) given recent hypotension. | Norepinephrine is currently being given. | presupposed by an action | The records show a norepinephrine infusion was started on 2100-01-02 at 11:15, but the decision time is 2100-01-01 23:43:00, which is before that administration. No norepinephrine administration is documented in the 24 hours before the decision time. |
| E1090039 | Monitor hemodynamic status and response to vasoactive infusions (norepinephrine, dopamine) given recent hypotension. | Hypotension was recently present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1117947 | Continue non-invasive ventilation with close monitoring of oxygenation and respiratory status. | The patient is currently on non-invasive ventilation. | presupposed by an action | The only record mentioning non-invasive ventilation is R31, which documents it as a treatment at 07:31, after the decision time of 06:58. There is no record showing the patient was on non-invasive ventilation at or before the decision time. |
| E1117947 | Monitor blood pressure and heart rate closely due to hypotension and tachycardia. | Hypotension is present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no. |
| E1117947 | Monitor blood pressure and heart rate closely due to hypotension and tachycardia. | Tachycardia is present. | stated outright | Median heart rate over the 6 h before the decision: 81 bpm (6 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E1171473 | Continue mechanical ventilation with current settings, monitoring oxygenation and ventilation. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('Tidal Volume (set): 500 mL') was 6.8 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1173453 | Assess for infection and continue antibiotic therapy given leukocytosis (WBC 21.14) and recent vancomycin. | Vancomycin was recently given. | presupposed by an action | The records only document vancomycin as a treatment (R17), but there is no administration record (e.g., MAR Administered or Given) within the 24 hours before the decision time to confirm it was recently given. |
| E1287791 | Continue mannitol infusion for elevated intracranial pressure management in the setting of ICH/cerebral infarct. | Mannitol infusion is currently being given. | presupposed by an action | The records mention mannitol as a continuous infusion in a treatment documentation note (R16), but there is no medication administration record showing mannitol was actually given or running at the decision time. Therefore, the statement that it is currently being given is not supported. |
| E1287791 | Monitor blood pressure closely given recent systolic readings ranging from 107 to 185 mmHg and mean arterial pressure as low as 71 mmHg. | Mean arterial pressure is as low as 71 mmHg. | stated outright | 0 of 24 mean arterial pressure values in the 24 h before the decision were low. |
| E1287791 | Assess and manage fever with temperature 100.8 F, including evaluation for infection. | Temperature is 100.8 F. | stated outright | Median temperature over the 6 h before the decision: 100.4 F (2 readings), normal by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. |
| E1449360 | Monitor blood pressure closely, given persistent diastolic hypertension (diastolic 86-97 mmHg) over the past 24 hours. | Persistent diastolic hypertension is present. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E1449360 | Assess for magnesium toxicity by monitoring deep tendon reflexes, respiratory rate, and oxygen saturation, as magnesium is being infused. | Magnesium is being infused. | stated outright | The records show magnesium infusions starting at 13:00 on 2100-01-01, but the decision time is 06:16 on 2100-01-01. The most recent relevant record before the decision time is a treatment documentation note (R29) at 07:41, which is after the decision time, and there is no administration record of magnesium in the 24 hours before 06:16. Therefore, the statement that magnesium is being infused at the decision time is not supported. |
| E1588473 | Continue supplemental oxygen via nasal cannula and monitor oxygen saturation, given recurrent desaturations to 88-91% on room air. | Supplemental oxygen via nasal cannula is currently being given. | presupposed by an action | The most recent O2 delivery device record before the decision time (R50, 12:29) shows 'None (Room air)', indicating the patient is not currently on nasal cannula oxygen. |
| E1619343 | Continue insulin infusion and monitor glucose closely as glucose has risen to 218 mg/dL. | Insulin infusion is currently being given. | presupposed by an action | The records mention insulin as a continuous infusion in a treatment documentation note (R24), but there is no administration record of insulin within the 24 hours before the decision time. The only running medications at the decision time are normal saline, ondansetron, vancomycin, and metoclopramide. |
| E1636307 | Continue mechanical ventilation with current settings (FiO2 30%, PEEP 5 cmH2O, set RR 12) and monitor respiratory status. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 9.7 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1636307 | Continue mechanical ventilation with current settings (FiO2 30%, PEEP 5 cmH2O, set RR 12) and monitor respiratory status. | FiO2 is 30%. | stated outright | The most recent relevant record before the decision time (R50 at 23:40) shows an O2 flow of 4 L/min, not an FiO2 of 30%. Earlier records show FiO2 30%, but the latest data contradicts the stated current setting. |
| E1653043 | Continue monitoring anticoagulation with serial PTT/INR given supratherapeutic PTT levels (159.3 s, 97.8 s, 95.4 s) on heparin and warfarin therapy. | Heparin therapy is currently being given. | presupposed by an action | The records document heparin therapy as a treatment (R32), but there is no administration record of heparin in the 24 hours before the decision time. The only running medication at decision time is sodium chloride (R45), so the statement that heparin is currently being given is not supported. |
| E1653043 | Continue monitoring anticoagulation with serial PTT/INR given supratherapeutic PTT levels (159.3 s, 97.8 s, 95.4 s) on heparin and warfarin therapy. | Warfarin therapy is currently being given. | presupposed by an action | The records show a warfarin administration on 2100-01-01 at 22:00 and a treatment documentation for coumadin on 2100-01-02 at 07:45, but there is no administration record of warfarin within the 24 hours before the decision time of 2100-01-02 21:32. Therefore, the statement that warfarin is currently being given is not supported. |
| E1672915 | Continue scheduled broad-spectrum antibiotics (piperacillin-tazobactam) for sepsis of unknown source. | Piperacillin-tazobactam is currently being given. | presupposed by an action | The only record mentioning piperacillin-tazobactam is R24, which shows a scheduled order started on 2100-01-02 at 00:00, not an administration within 24 hours before the decision time of 2100-01-02 19:54. No administration record confirms it is currently being given. |
| E1672915 | Assess and manage pain and agitation with as-needed opioid and sedative therapy per existing orders. | Sedative orders are active. | presupposed by an action | The records show multiple one-time administrations of the sedative lorazepam, but no active sedative order is present. The only active orders are for labetalol, acetaminophen, morphine, and other non-sedative medications. |
| E1674875 | Continue monitoring oxygenation and respiratory status given persistent hypoxemia and hypercapnia on supplemental oxygen. | Hypoxemia is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E1674875 | Assess and manage hypotension with mean arterial pressure in the 40s-70s mmHg range. | Mean arterial pressure is in the 40s-70s mmHg range. | stated outright | Median mean arterial pressure over the 6 h before the decision: 65 mmHg (6 readings), normal by the rule 'hypotension MAP < 65'. |
| E1674875 | Assess and manage hypotension with mean arterial pressure in the 40s-70s mmHg range. | Hypotension is present. | presupposed by an action | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1682105 | Assess and manage hypotension with intravenous fluids as needed. | Hypotension is present. | presupposed by an action | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1739131 | Continue monitoring vital signs and oxygen saturation on room air, given stable GCS and hemodynamics. | Hemodynamics are stable. | stated outright | 'cardiovascular status normal' holds when any component is normal. heart rate: yes; systolic BP: no; mean arterial pressure: yes. |
| E1739131 | Maintain current IV fluid infusion at 100 mL/hour. | IV fluid infusion is currently running at 100 mL/hour. | presupposed by an action | The records show an IV fluid infusion (Lactated Ringer's) running at decision time, but the only rate documented is 100 ml/hour in R19, which started at 10:06, after the decision time of 09:51. R13 shows a sodium chloride infusion running from 08:01 to 10:33, but no rate is specified. Therefore, the statement that the infusion is currently running at 100 mL/hour is not supported by the records at the decision time. |
| E1781359 | Continue scheduled antibiotic therapy with piperacillin-tazobactam and vancomycin for sepsis treatment. | Piperacillin-tazobactam is currently being given. | presupposed by an action | The records show a piperacillin-tazobactam administration that started at 23:00 on 2100-01-01, which is after the decision time of 19:47 on 2100-01-01. There is no administration record of piperacillin-tazobactam in the 24 hours before the decision time. |
| E1781359 | Continue scheduled antibiotic therapy with piperacillin-tazobactam and vancomycin for sepsis treatment. | Vancomycin is currently being given. | presupposed by an action | The records show a one-time vancomycin dose on 2100-01-01 at 16:45 (R10) and a scheduled vancomycin order that started running on 2100-01-02 at 06:00 (R39), but no administration of vancomycin within the 24 hours before the decision time of 2100-01-02 19:47. Therefore, the statement that vancomycin is currently being given is not supported. |
| E1823727 | Continue hemodialysis as documented for renal failure. | Hemodialysis is currently being given. | presupposed by an action | The records document hemodialysis as a treatment (R35, R42, R47), but there is no administration record showing hemodialysis was being given at the decision time of 2100-01-01 14:58:00. The documentation entries are after the decision time and do not confirm ongoing administration. |
| E1823727 | Monitor potassium level given hyperkalemia. | Hyperkalemia is present. | stated outright | Latest potassium 5.1 mmol/L at 2100-01-02 10:00:00 (reference 3.3 to 5.1) is normal, not consistent with 'high'. |
| E1824650 | Continue scheduled aspirin, metoprolol, famotidine, docusate, and potassium chloride as ordered. | Potassium chloride is currently being given. | presupposed by an action | The statement claims potassium chloride is currently being given, but the most recent administration record (R45) is an oral scheduled order that started at 14:00, not an active IV infusion at the decision time. The only IV administration (R31) occurred over 21 hours before the decision time and was a one-time dose, not ongoing. |
| E1824650 | Monitor blood glucose and administer sliding-scale insulin as ordered. | Sliding-scale insulin orders are active. | presupposed by an action | The records show an active scheduled insulin order (R49), but no sliding-scale insulin order is present. The statement specifically claims sliding-scale insulin orders are active, which is not documented. |
| E1824650 | Assess readiness for ICU discharge given stable vitals, GCS 15, and room air. | Vitals are stable. | stated outright | 'vital signs normal' holds when any component is normal. heart rate: yes; systolic BP: yes; mean arterial pressure: yes; respiratory rate: no; SpO2: yes; temperature: yes. |
| E1824650 | Assess readiness for ICU discharge given stable vitals, GCS 15, and room air. | GCS is 15. | stated outright | The most recent GCS record before the decision time (2100-01-01 17:48) is R17 at 18:00, which shows a GCS of 12, not 15. Later records show GCS 15, but they are after the decision time. |
| E1824650 | Assess readiness for ICU discharge given stable vitals, GCS 15, and room air. | The patient is on room air. | stated outright | The records show the patient was on mechanical ventilation (R23) with PEEP set at 5 cmH2O (R27) and later ventilator weaning and oxygen therapy (R33, R34). There is no record of the patient being on room air; instead, the most recent relevant data indicates ventilator support, contradicting the statement. |
| E1829278 | Continue nicardipine infusion for blood pressure control, as it was running at 7.5 mg/hour at the decision point. | Nicardipine infusion is currently running. | presupposed by an action | The nicardipine infusion record (R36) shows it ran from 03:00 to 08:24 on 2100-01-02, ending 19 minutes before the decision time of 08:43. There is no record of it running at the decision time, so the statement that it is currently running is not supported. |
| E1829278 | Monitor neurological status with Glasgow Coma Scale, which was 9 at 03:00 and improved from 11 earlier. | Glasgow Coma Scale improved from 11 earlier. | stated outright | The records show GCS was 9 at 08:00 (R8), improved to 11 at 15:27 (R33), then dropped back to 9 at 03:00 (R43). The statement claims improvement from 11 earlier, but the most recent value is 9, indicating a decline rather than improvement. |
| E1856821 | Continue norepinephrine infusion for shock, with dose titration to maintain adequate mean arterial pressure. | Norepinephrine infusion is currently being given. | presupposed by an action | The records show norepinephrine infusions that ended at 14:11 on 2100-01-02, but no administration record within 24 hours before the decision time of 18:36 on 2100-01-01. The most recent infusion (R41) ended before the decision time, so the statement that it is currently being given is not supported. |
| E2230341 | Continue eptifibatide infusion as ordered. | Eptifibatide infusion is currently being given. | presupposed by an action | The records show an Eptifibatide infusion from 2100-01-01 17:58 to 2100-01-02 00:24, which ended before the decision time of 2100-01-02 14:38. There is no administration record of Eptifibatide within 24 hours before the decision time, so the statement that it is currently being given is not supported. |
| E2309912 | Continue lorazepam as needed for alcohol withdrawal, with monitoring of sedation and respiratory status. | Lorazepam is currently being given. | presupposed by an action | The records show an active PRN order for Ativan (lorazepam) and a 'Running at decision time' administration record for Ativan IV, but the administration record is dated 2100-01-01 12:41, which is over 24 hours before the decision time of 2100-01-02 11:55. There is no administration of lorazepam within the 24 hours preceding the decision time. |
| E2309912 | Monitor blood pressure and heart rate closely given persistent hypertension and tachycardia, with PRN antihypertensives available. | Hypertension is persistent. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E2309912 | Monitor blood pressure and heart rate closely given persistent hypertension and tachycardia, with PRN antihypertensives available. | Tachycardia is persistent. | stated outright | Median heart rate over the 6 h before the decision: 83.5 bpm (12 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E2418055 | Continue EEG monitoring for seizure activity in a patient with persistently low Glasgow Coma Scale. | EEG monitoring is currently being performed. | presupposed by an action | The records document EEG monitoring as a treatment on 2100-01-01 at 01:48, but there is no administration or ongoing record showing EEG monitoring is currently being performed at the decision time of 2100-01-02 01:07. |
| E2558122 | Assess and manage hypoxemia with escalating oxygen support, including consideration of noninvasive ventilation, given SpO2 90–92% on oxymask and prior BiPAP use. | Hypoxemia is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no. |
| E2609672 | Monitor blood glucose with finger-stick checks given recent hypoglycemia and glucose variability. | Recent hypoglycemia is present. | stated outright | 0 of 2 glucose values in the 24 h before the decision were low. |
| E2714303 | Continue levetiracetam and phenytoin anticonvulsant therapy for seizure management. | Levetiracetam is currently being given. | presupposed by an action | The records document levetiracetam as a treatment for seizure therapy, but there is no administration record showing it was given within 24 hours before the decision time. A treatment documentation entry does not confirm current administration. |
| E2714303 | Continue levetiracetam and phenytoin anticonvulsant therapy for seizure management. | Phenytoin is currently being given. | presupposed by an action | The records document phenytoin as a treatment for seizure therapy, but there is no administration record showing phenytoin was given in the 24 hours before the decision time. A treatment documentation alone does not confirm current administration. |
| E2714303 | Assess and manage fever with temperature 101.7°F and tachycardia. | Temperature is 101.7°F. | stated outright | Median temperature over the 6 h before the decision: 99.15 F (2 readings), normal by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. |
| E2814579 | Monitor arterial blood pressure and central venous pressure closely, with vasoactive infusions available, to maintain adequate perfusion given low cardiac index and prior hypotension. | Vasoactive infusions are available. | stated outright | The records show vasoactive infusions (Dobutamine and Norepinephrine) were administered at 13:00 on 2100-01-02, but there is no record of them running at the decision time of 22:47 on 2100-01-01. The statement is about availability at the decision time, which is not supported by the later administration records. |
| E2814579 | Monitor blood glucose and continue insulin infusion to maintain glycemic control. | Insulin infusion is currently being given. | presupposed by an action | The only insulin administration record is an infusion at 13:00 on 2100-01-02, which is more than 24 hours before the decision time of 22:47 on 2100-01-01. No insulin administration is documented within the 24 hours prior to the decision time. |
| E2879373 | Monitor blood pressure closely due to wide pulse pressure and diastolic pressures as low as 30 mmHg. | Pulse pressure is wide. | stated outright | Median heart rate over the 6 h before the decision: 86 bpm (6 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E2879373 | Continue non-invasive ventilation with FiO2 40% and monitor respiratory status, given persistent hypercapnia and bicarbonate elevation. | The patient is currently on non-invasive ventilation (BiPAP/CPAP). | presupposed by an action | The only record mentioning non-invasive ventilation is R23, which documents it at 10:19 on 2100-01-01, after the decision time of 09:35. There is no record of non-invasive ventilation being administered at or before the decision time. |
| E3001552 | Reassess oxygenation and respiratory status on current oxygen support. | The patient is currently on oxygen support. | presupposed by an action | The records show oxygen therapy and ventilation documented after the decision time (09:39), with the earliest evidence of oxygen support at 10:15 (R40). There is no record of oxygen support at or before the decision time, so the statement that the patient is currently on oxygen support is not supported by the records. |
| E3027283 | Monitor serum sodium closely and reassess diuretic strategy given severe hyponatremia (Na 120 mmol/L) and hypervolemic heart failure. | Hypervolemic heart failure is present. | stated outright | The records show an admission diagnosis of congestive heart failure (CHF), but do not document hypervolemia or fluid overload. The term 'hypervolemic' is not mentioned, and no physical exam findings, weights, or fluid balance data are provided to support that specific qualifier. |
| E3035113 | Continue scheduled amiodarone therapy. | Amiodarone is currently being given. | presupposed by an action | The only record of amiodarone is R17, which shows a scheduled order started on 2100-01-01 at 14:00 and marked 'Running at decision time'. However, the decision time is 2100-01-02 11:08:00, over 21 hours later, and there is no administration record of amiodarone within the 24 hours before the decision time. |
| E3035113 | Monitor blood glucose given recent hyperglycemia and hypoglycemia. | Recent hypoglycemia is present. | stated outright | 0 of 1 glucose values in the 24 h before the decision were low. |
| E3035113 | Assess and manage hypokalemia (potassium 3.4 mmol/L). | Hypokalemia is present. | stated outright | Latest potassium 3.4 mmol/L at 2100-01-02 09:39:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E3053511 | Continue monitoring respiratory status and oxygenation given persistent tachypnea and intermittent hypoxemia. | Intermittent hypoxemia is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E3053511 | Continue antibiotic therapy with vancomycin and piperacillin/tazobactam as documented, with monitoring of vancomycin trough. | Vancomycin is currently being given. | presupposed by an action | The records mention vancomycin as a documented treatment and a trough level, but there is no administration record of vancomycin in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E3053511 | Continue antibiotic therapy with vancomycin and piperacillin/tazobactam as documented, with monitoring of vancomycin trough. | Piperacillin/tazobactam is currently being given. | presupposed by an action | The records document piperacillin/tazobactam as a treatment (R9, R35), but there is no medication administration record showing it was given in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E3111371 | Monitor vital signs and CIWA/withdrawal scores closely given fluctuating hypertension, tachycardia, tachypnea, and sedation scores. | Hypertension is fluctuating. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E3111371 | Monitor vital signs and CIWA/withdrawal scores closely given fluctuating hypertension, tachycardia, tachypnea, and sedation scores. | Tachycardia is fluctuating. | stated outright | Median heart rate over the 6 h before the decision: 96 bpm (5 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E3111371 | Monitor vital signs and CIWA/withdrawal scores closely given fluctuating hypertension, tachycardia, tachypnea, and sedation scores. | Tachypnea is fluctuating. | stated outright | Median respiratory rate over the 6 h before the decision: 19 insp/min (5 readings), normal by the rule 'tachypnea RR > 20; bradypnea RR < 12'. |
| E3124669 | Monitor serum potassium and replete as needed, given persistent hypokalemia (3.3 mmol/L at 20:00 on 2100-01-01). | Hypokalemia is present. | stated outright | Latest potassium 3.3 mmol/L at 2100-01-01 20:00:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E3130379 | Continue BiPAP support with current settings (FiO2 30%, PEEP 8 cmH2O) and monitor oxygenation and ventilation, given persistent hypercapnia (pCO2 61 mmHg) and borderline oxygen saturation. | FiO2 is 30%. | stated outright | The most recent record before the decision time (R52) shows the patient on a nasal cannula, not BiPAP, and no FiO2 of 30% is charted after that. Earlier records show FiO2 30% while on BiPAP, but the current device contradicts the statement. |
| E3130379 | Continue BiPAP support with current settings (FiO2 30%, PEEP 8 cmH2O) and monitor oxygenation and ventilation, given persistent hypercapnia (pCO2 61 mmHg) and borderline oxygen saturation. | PEEP is 8 cmH2O. | stated outright | The most recent relevant record R52 shows the oxygen delivery device is a nasal cannula, not BiPAP, and no PEEP setting is charted after that, so the statement that PEEP is 8 cmH2O is not supported at the decision time. |
| E3148216 | Monitor oxygen saturation and respiratory status closely given declining SpO2 and increased oxygen requirement. | SpO2 is declining. | stated outright | 0 of 23 SpO2 values in the 24 h before the decision were low. |
| E3148216 | Monitor oxygen saturation and respiratory status closely given declining SpO2 and increased oxygen requirement. | Oxygen requirement is increased. | stated outright | The records show oxygen therapy was documented at <40% and the O2 flow rate decreased from 4 L to 2 L around 12:18, indicating a reduction, not an increase, in oxygen requirement. SpO2 values also declined later, but the oxygen delivery setting itself was lowered. |
| E3148216 | Assess for possible infection or other cause of fever and respiratory changes. | Fever is present. | presupposed by an action | Median temperature over the 6 h before the decision: 99.9 F (1 readings), normal by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. |
| E3148216 | Assess for possible infection or other cause of fever and respiratory changes. | Respiratory changes are present. | presupposed by an action | The statement 'Respiratory changes are present' is not supported by the records. Respiratory rates before the decision time fluctuate between 11 and 20 breaths per minute, which is within normal limits and does not indicate a significant change. The records do not document any respiratory changes or abnormalities. |
| E3178242 | Assess and manage worsening hypoxemia and tachypnea on 2 L/min nasal cannula, with SpO2 93% and pO2 85 mmHg, considering escalation of respiratory support. | Hypoxemia is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E3220742 | Continue levetiracetam for seizure prophylaxis/therapy as ordered. | Levetiracetam is currently being given. | presupposed by an action | The records show a levetiracetam administration (R31) that ended at 11:47 on 2100-01-01, which is more than 24 hours before the decision time of 02:33 on 2100-01-02. While treatment documentation (R18, R42) mentions levetiracetam, there is no administration record within the 24 hours prior to the decision time to support the statement that it is 'currently being given'. |
| E3223097 | Monitor serum potassium and treat hyperkalemia as indicated. | Hyperkalemia is present. | presupposed by an action | Latest potassium 4.2 mmol/L at 2100-01-02 08:10:00 (reference 3.3 to 5.1) is normal, not consistent with 'high'. |
| E3223097 | Monitor blood pressure and hemoglobin for ongoing bleeding and hemodynamic instability. | Ongoing bleeding is present. | stated outright | The records show an admission diagnosis of upper GI bleeding and treatments for bleeding (blood product administration), but no record documents ongoing bleeding at the decision time. The diagnosis and treatments indicate bleeding was present at admission, not that it is ongoing. |
| E3233620 | Continue scheduled esomeprazole for stress ulcer prophylaxis. | Scheduled esomeprazole is currently being given. | presupposed by an action | The only esomeprazole administration record (R22) is from 2100-01-01 15:00, which is more than 24 hours before the decision time of 2100-01-02 13:57. There is no administration record within the 24 hours prior to the decision time, so the statement that it is 'currently being given' is not supported. |
| E3233620 | Monitor vital signs and oxygen saturation closely given diminished breath sounds and borderline oxygenation. | Oxygenation is borderline. | stated outright | 'oxygenation abnormal' holds when any component is abnormal. SpO2: no. |

## 5. Judge panel

287 items went to the judge panel. Agreement: {'1/1': 287} (split = no majority; the conservative label was used and the item needs human review).

## 6. Per-case score sheets

| Case | Facts | supported | not_supported | not_addressed | unverifiable | Treatment agreement | Vital recall | All recall |
|---|---|---|---|---|---|---|---|---|
| E153972 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E172015 | 9 | 88.9% | 11.1% | 0.0% | 0.0% | - | - | - |
| E184757 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E211144 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E284265 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E297175 | 5 | 60.0% | 20.0% | 20.0% | 0.0% | 33.3% | - | - |
| E322290 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E375854 | 8 | 62.5% | 37.5% | 0.0% | 0.0% | - | - | - |
| E383358 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E395323 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E405746 | 7 | 71.4% | 28.6% | 0.0% | 0.0% | - | - | - |
| E454584 | 9 | 77.8% | 22.2% | 0.0% | 0.0% | 33.3% | - | - |
| E467819 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E490454 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 100.0% | - | - |
| E521456 | 6 | 50.0% | 50.0% | 0.0% | 0.0% | 25.0% | - | - |
| E664474 | 7 | 71.4% | 28.6% | 0.0% | 0.0% | 0.0% | - | - |
| E733082 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E756295 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 33.3% | - | - |
| E758325 | 9 | 100.0% | 0.0% | 0.0% | 0.0% | 66.7% | - | - |
| E826669 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E850469 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 0.0% | - | - |
| E876429 | 8 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E899746 | 8 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E942382 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E962227 | 7 | 85.7% | 0.0% | 14.3% | 0.0% | 0.0% | - | - |
| E978037 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1056063 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | - | - | - |
| E1057910 | 9 | 55.6% | 22.2% | 22.2% | 0.0% | 0.0% | - | - |
| E1057967 | 7 | 85.7% | 14.3% | 0.0% | 0.0% | - | - | - |
| E1064283 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1065859 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1068212 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1071224 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071450 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1090039 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 100.0% | - | - |
| E1090889 | 8 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1099398 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1117947 | 4 | 25.0% | 75.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1121034 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 33.3% | - | - |
| E1171473 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1173453 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1177589 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1287791 | 6 | 33.3% | 50.0% | 16.7% | 0.0% | - | - | - |
| E1290248 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1449360 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | - | - | - |
| E1496959 | 7 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1497157 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1588473 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1592666 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1619343 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1636307 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1653043 | 8 | 62.5% | 25.0% | 12.5% | 0.0% | - | - | - |
| E1672915 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1674875 | 8 | 62.5% | 37.5% | 0.0% | 0.0% | 0.0% | - | - |
| E1682105 | 4 | 50.0% | 25.0% | 25.0% | 0.0% | 0.0% | - | - |
| E1705630 | 7 | 85.7% | 0.0% | 14.3% | 0.0% | - | - | - |
| E1739131 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1781359 | 9 | 77.8% | 22.2% | 0.0% | 0.0% | 33.3% | - | - |
| E1790816 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823356 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823727 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1824650 | 9 | 44.4% | 55.6% | 0.0% | 0.0% | 0.0% | - | - |
| E1829278 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1837964 | 11 | 100.0% | 0.0% | 0.0% | 0.0% | 10.0% | - | - |
| E1853162 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1856821 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2230341 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E2309912 | 4 | 25.0% | 75.0% | 0.0% | 0.0% | - | - | - |
| E2418055 | 8 | 87.5% | 12.5% | 0.0% | 0.0% | 50.0% | - | - |
| E2419768 | 6 | 66.7% | 0.0% | 33.3% | 0.0% | 0.0% | - | - |
| E2558122 | 7 | 85.7% | 14.3% | 0.0% | 0.0% | 0.0% | - | - |
| E2609672 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2714303 | 6 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2725629 | 4 | 75.0% | 0.0% | 25.0% | 0.0% | 0.0% | - | - |
| E2757707 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2814579 | 7 | 57.1% | 28.6% | 14.3% | 0.0% | 66.7% | - | - |
| E2860378 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E2879373 | 7 | 71.4% | 28.6% | 0.0% | 0.0% | 100.0% | - | - |
| E3001552 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3027283 | 5 | 60.0% | 20.0% | 20.0% | 0.0% | 100.0% | - | - |
| E3033795 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3035113 | 5 | 40.0% | 60.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3053511 | 6 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3067309 | 7 | 100.0% | 0.0% | 0.0% | 0.0% | 25.0% | - | - |
| E3110594 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E3111371 | 5 | 40.0% | 60.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3112232 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3115505 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3124669 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3130379 | 9 | 77.8% | 22.2% | 0.0% | 0.0% | 50.0% | - | - |
| E3148216 | 4 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E3150018 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E3152779 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E3170528 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3178242 | 6 | 66.7% | 16.7% | 16.7% | 0.0% | - | - | - |
| E3205786 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3220742 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3223097 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3233620 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3237226 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
