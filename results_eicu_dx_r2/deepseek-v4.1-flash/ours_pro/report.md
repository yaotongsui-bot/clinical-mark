# Evaluation of AI clinical suggestions against patient records

- Input: `eicu_triples_deepseek-v4.1-flash.json`; 100 cases, 3.0 AI suggestions per case on average.
- Models: atomizer `deepseek-v4-pro:0813:cloud`; judge panel `deepseek-v4-pro:0813:cloud` (majority vote; reasoning mode: none); 287 new model calls, 0 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 18.0% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 530 |
| supported / not_supported / not_addressed / unverifiable | 414 / 99 / 17 / 0 |
| Fact accuracy = supported / (supported + not_supported) | 80.7% |
| Cases with at least one not_supported fact | 60 / 100 |
| Omitted findings: abnormalities the clinicians treated that no AI fact mentions | 0 / 0 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 344 | 84.1% | {'supported': 285, 'not_supported': 54, 'not_addressed': 5} |
| presupposed by an action | 169 | 71.5% | {'supported': 113, 'not_supported': 45, 'not_addressed': 11} |
| clinical judgment | 17 | 100.0% | {'supported': 16, 'not_addressed': 1} |
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
| E184757 | Continue scheduled piperacillin-tazobactam 3-0.375 g IV every 8 hours for ongoing infection treatment. | Piperacillin-tazobactam is currently being given. | presupposed by an action | The only record of piperacillin-tazobactam is an administration that started on 2099-12-19, which is more than 24 hours before the decision time of 2100-01-02 23:48. There is no administration record within the 24 hours prior to the decision time to support that it is currently being given. |
| E284265 | Continue diltiazem infusion for rate control of atrial arrhythmia. | Diltiazem infusion is currently being given. | presupposed by an action | The only diltiazem administration record is an infusion that ran from 2100-01-01 21:00 to 2100-01-02 05:00, which ended more than 13 hours before the decision time of 2100-01-02 18:11. No record shows diltiazem being given within 24 hours before the decision time. |
| E297175 | Continue non-invasive ventilation with FiO2 40% and PEEP 5 cmH2O, monitoring oxygenation and respiratory status. | FiO2 is 40%. | stated outright | The most recent FiO2 measurement before the decision time is 45% (R40), not 40%. Earlier records show 40%, but the latest value contradicts the statement. |
| E322290 | Monitor blood pressure and heart rate closely given recent systolic blood pressure of 91 mmHg and tachycardia. | Tachycardia is present. | stated outright | 0 of 16 heart rate values in the 24 h before the decision were high. |
| E375854 | Assess and manage ongoing hypotension with persistent tachycardia in the setting of GI bleeding and dropping hemoglobin. | Hypotension is present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E375854 | Assess and manage ongoing hypotension with persistent tachycardia in the setting of GI bleeding and dropping hemoglobin. | Tachycardia is present. | stated outright | Median heart rate over the 6 h before the decision: 88.5 bpm (6 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E375854 | Continue monitoring oxygen saturation and administer supplemental oxygen as needed given O2 saturation 94% on 3 L/min nasal cannula. | The patient is on 3 L/min nasal cannula. | stated outright | The records document oxygen therapy via nasal cannula at 30-40% (R35, R36), but do not specify a flow rate of 3 L/min. The statement's specific flow rate is not supported by the available records. |
| E405746 | Monitor oxygen saturation and respiratory status given intermittent desaturation to 91% and 93% in the prior 24 hours. | Desaturation is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no. |
| E454584 | Assess and manage sedation and delirium, considering the patient's fluctuating RASS and CAM-ICU positive status. | RASS is fluctuating. | stated outright | The records contain multiple RASS entries, but none include a numerical score or value. Without recorded RASS values, the claim that the RASS is 'fluctuating' cannot be verified or supported. |
| E454584 | Assess and manage sedation and delirium, considering the patient's fluctuating RASS and CAM-ICU positive status. | CAM-ICU is positive. | stated outright | The records mention CAM-ICU assessments but do not provide a result or score indicating a positive status. The rows only list the scale used, not the outcome, so the statement that CAM-ICU is positive is not supported. |
| E467819 | Continue nicardipine infusion for blood pressure control in intracranial hemorrhage. | Nicardipine infusion is currently being given. | presupposed by an action | The most recent nicardipine administration record (R50) shows an infusion that ended at 00:00 on 2100-01-02, which is more than 1.5 hours before the decision time of 01:43. There is no record of a nicardipine infusion running at the decision time. |
| E490454 | Continue non-invasive ventilation with BiPAP mask given recurrent hypoxemia (SpO2 91% at 23:20) after weaning to nasal cannula. | Recurrent hypoxemia is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E490454 | Assess for possible causes of worsening hypoxemia, including bronchospasm, fluid overload, or mucus plugging, and consider need for bronchodilator therapy or diuresis. | Worsening hypoxemia is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E521456 | Monitor blood glucose closely and continue insulin sliding scale to maintain glycemic control, given recent hypoglycemia and hyperglycemia. | Insulin sliding scale is currently being given. | presupposed by an action | The only record mentioning insulin sliding scale is a treatment documentation from 2100-01-01 20:30, which is over 22 hours before the decision time. There is no administration record of insulin sliding scale within the 24 hours before 2100-01-02 18:57, so the statement that it is currently being given is not supported. |
| E521456 | Monitor blood glucose closely and continue insulin sliding scale to maintain glycemic control, given recent hypoglycemia and hyperglycemia. | Recent hypoglycemia is present. | stated outright | 0 of 1 glucose values in the 24 h before the decision were low. |
| E521456 | Monitor blood glucose closely and continue insulin sliding scale to maintain glycemic control, given recent hypoglycemia and hyperglycemia. | Recent hyperglycemia is present. | stated outright | 0 of 1 glucose values in the 24 h before the decision were high. |
| E664474 | Monitor oxygen saturation and respiratory rate closely given persistent tachypnea and oxygen requirement. | Tachypnea is persistent. | stated outright | Median respiratory rate over the 6 h before the decision: 19 insp/min (5 readings), normal by the rule 'tachypnea RR > 20; bradypnea RR < 12'. |
| E733082 | Monitor vital signs and oxygen saturation closely given persistent tachycardia and borderline oxygen saturation. | Oxygen saturation is borderline. | stated outright | The most recent oxygen saturation values before the decision time are 94% (R47, R49) and 96% (R48, R50), which are below the normal range and not merely borderline. The statement that saturation is borderline is not supported by these recorded values. |
| E850469 | Continue scheduled broad-spectrum antibiotics (ZOSYN and VANCOMYCIN) for sepsis. | VANCOMYCIN is currently being given. | presupposed by an action | The most recent vancomycin administration record (R20) ended at 15:18 on 2100-01-01, which is more than 24 hours before the decision time of 13:47 on 2100-01-02. R28 is a 'Running at decision time' record for a scheduled order started on 2100-01-01, but it does not indicate administration within the 24 hours prior to the decision time. |
| E876429 | Continue mechanical ventilation with current settings (FiO2 40%, PEEP 5 cmH2O, PSV 10 cmH2O) and monitor oxygenation and respiratory status. | The patient is currently on mechanical ventilation. | stated outright | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 8.4 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E876429 | Continue vasopressor and sedative infusions (epinephrine, norepinephrine, phenylephrine, propofol) and monitor hemodynamics and sedation. | Phenylephrine is currently being given. | stated outright | Phenylephrine appears in the records, but the most recent administration record (R44) shows an infusion that ended at 13:00 on 2100-01-02, over 6 hours before the decision time of 19:53. There is no record of phenylephrine being administered within 24 hours of the decision time. |
| E942382 | Continue diltiazem infusion for rate control of atrial arrhythmia. | Diltiazem infusion is currently being given. | presupposed by an action | The only record of diltiazem administration is an infusion that started and ended at 17:04 on 2100-01-01, which is more than 24 hours before the decision time of 15:23 on 2100-01-02. There is no record of a diltiazem infusion running at the decision time. |
| E942382 | Monitor heart rate and blood pressure closely given bradycardia and intermittent hypotension. | Intermittent hypotension is present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1056063 | Continue continuous pulse oximetry and vital sign monitoring in the ICU, with attention to intermittent oxygen desaturation and tachycardia. | Intermittent oxygen desaturation is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no. |
| E1056063 | Reassess neurologic status and GCS, and continue psychiatric consultation follow-up for substance overdose management. | Psychiatric consultation is currently ongoing. | presupposed by an action | The records document a Psychiatry consultation was requested on 2100-01-01 at 10:33, but there is no record of an ongoing or active psychiatric consultation at the decision time of 2100-01-02 10:15. |
| E1057910 | Continue mechanical ventilation with FiO2 0.4 and monitor oxygenation, as the patient remains intubated with GCS 3 and RASS -4. | RASS is -4. | stated outright | The records mention RASS but do not provide a numeric score. The most recent RASS entry (R45) only lists the scale name, not a value of -4, so the statement cannot be supported. |
| E1057910 | Monitor blood pressure and titrate vasopressor support as needed, given recent hypotension and current norepinephrine use. | Norepinephrine is currently being given. | stated outright | The records show a norepinephrine drip that ended on 2100-01-01 at 15:32 (R1) and a treatment note from 07:10 (R12), but no administration of norepinephrine within 24 hours before the decision time of 2100-01-02 05:25. Therefore, the statement that it is currently being given is not supported. |
| E1064283 | Continue scheduled prednisone and pyridostigmine therapy for myasthenia gravis. | Pyridostigmine is currently being given. | presupposed by an action | The records mention pyridostigmine only as a documented treatment (R39), but there is no medication order or administration record showing it was given in the 24 hours before the decision time. |
| E1064283 | Assess for need to intensify antihypertensive therapy given persistent systolic blood pressure >190 mmHg. | Systolic blood pressure is persistently greater than 190 mmHg. | stated outright | No recorded systolic BP matches the stated 190; values in the 24 h before the decision ranged 121 to 217 mmHg (latest 194). |
| E1068212 | Continue monitoring heart rate and blood pressure, given persistent tachycardia (HR 112-130 bpm) and low diastolic pressures. | Diastolic blood pressure is low. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1071450 | Continue monitoring hemodynamic status, including pulmonary artery pressures and cardiac output, given recent elevated PA mean and heart rate. | PA mean is elevated. | stated outright | The most recent PA Mean value before the decision time is 25 mmHg (R50), which is within the normal range (typically 10-20 mmHg), not elevated. While some earlier values were elevated, the latest measurement does not support the statement that PA mean is currently elevated. |
| E1090039 | Monitor hemodynamic status and response to vasoactive infusions (norepinephrine, dopamine) given recent hypotension. | Hypotension was recently present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1117947 | Continue non-invasive ventilation with close monitoring of oxygenation and respiratory status. | The patient is currently on non-invasive ventilation. | presupposed by an action | The only record mentioning non-invasive ventilation is R31, which documents it as a treatment at 07:31 on 2100-01-01, over 23 hours before the decision time. There is no administration or ongoing-use record within 24 hours of the decision time to support the present-tense claim. |
| E1117947 | Monitor blood pressure and heart rate closely due to hypotension and tachycardia. | Hypotension is present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no. |
| E1117947 | Monitor blood pressure and heart rate closely due to hypotension and tachycardia. | Tachycardia is present. | stated outright | Median heart rate over the 6 h before the decision: 81 bpm (6 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E1171473 | Continue mechanical ventilation with current settings, monitoring oxygenation and ventilation. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('Tidal Volume (set): 500 mL') was 6.8 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1173453 | Assess for infection and continue antibiotic therapy given leukocytosis (WBC 21.14) and recent vancomycin. | Vancomycin was recently given. | presupposed by an action | The records mention vancomycin only as a documented treatment on 2100-01-01 at 13:12, but there is no administration record (e.g., MAR Administered or Given) within the 24 hours before the decision time to confirm it was recently given. |
| E1177589 | Continue supplemental oxygen via nasal cannula as needed to maintain oxygen saturation, with weaning as tolerated. | Supplemental oxygen via nasal cannula is currently being given. | presupposed by an action | The most recent O2 delivery device record (R13) at 10:15 on 2100-01-01 shows nasal cannula, but there is no record of oxygen administration or device use within 24 hours before the decision time on 2100-01-02. The latest oxygen flow record is from 2100-01-01 15:00, and the latest saturation record at 2100-01-02 06:00 shows 98% on 21% O2, suggesting no supplemental oxygen is currently being given. |
| E1287791 | Continue mannitol infusion for elevated intracranial pressure management in the setting of ICH/cerebral infarct. | Mannitol infusion is currently being given. | presupposed by an action | The records mention mannitol as a continuous infusion in a treatment note (R16), but there is no medication administration record showing mannitol was actually given or running at the decision time. An order or note alone does not confirm current administration. |
| E1287791 | Monitor blood pressure closely given recent systolic readings ranging from 107 to 185 mmHg and mean arterial pressure as low as 71 mmHg. | Mean arterial pressure is as low as 71 mmHg. | stated outright | 0 of 24 mean arterial pressure values in the 24 h before the decision were low. |
| E1287791 | Assess and manage fever with temperature 100.8 F, including evaluation for infection. | Temperature is 100.8 F. | stated outright | Median temperature over the 6 h before the decision: 100.4 F (2 readings), normal by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. |
| E1449360 | Monitor blood pressure closely, given persistent diastolic hypertension (diastolic 86-97 mmHg) over the past 24 hours. | Persistent diastolic hypertension is present. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E1588473 | Continue supplemental oxygen via nasal cannula and monitor oxygen saturation, given recurrent desaturations to 88-91% on room air. | Supplemental oxygen via nasal cannula is currently being given. | presupposed by an action | The most recent O2 delivery device record before the decision time (R50, at 12:29) shows 'None (Room air)', indicating the patient is not currently on supplemental oxygen via nasal cannula. |
| E1619343 | Continue insulin infusion and monitor glucose closely as glucose has risen to 218 mg/dL. | Insulin infusion is currently being given. | presupposed by an action | The records mention insulin as a continuous infusion in a treatment documentation note (R24), but there is no administration record of insulin being given at or within 24 hours before the decision time. The only running medications at decision time are normal saline, ondansetron, vancomycin, and metoclopramide. |
| E1636307 | Continue mechanical ventilation with current settings (FiO2 30%, PEEP 5 cmH2O, set RR 12) and monitor respiratory status. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 9.7 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1636307 | Continue mechanical ventilation with current settings (FiO2 30%, PEEP 5 cmH2O, set RR 12) and monitor respiratory status. | FiO2 is 30%. | stated outright | The most recent records before the decision time show the patient was switched from an inspired O2 fraction of 30% to an O2 delivery of 4 L/min (R49, R50), indicating the FiO2 is no longer 30%. |
| E1653043 | Continue monitoring anticoagulation with serial PTT/INR given supratherapeutic PTT levels (159.3 s, 97.8 s, 95.4 s) on heparin and warfarin therapy. | Heparin therapy is currently being given. | presupposed by an action | The records document heparin therapy (R32) but do not show an administration of heparin within the 24 hours before the decision time. The only running medication at decision time is sodium chloride (R45), so the statement that heparin is currently being given is not supported. |
| E1653043 | Continue monitoring anticoagulation with serial PTT/INR given supratherapeutic PTT levels (159.3 s, 97.8 s, 95.4 s) on heparin and warfarin therapy. | Warfarin therapy is currently being given. | presupposed by an action | The records show a warfarin administration on 2100-01-01 at 22:00 and a treatment documentation for coumadin on 2100-01-02 at 07:45, but no administration record within 24 hours before the decision time of 2100-01-02 21:32. Therefore, the statement that warfarin is currently being given is not supported. |
| E1672915 | Assess and manage pain and agitation with as-needed opioid and sedative therapy per existing orders. | Sedative orders are active. | presupposed by an action | The records show multiple one-time administrations of the sedative lorazepam, but no active sedative order is present. The only active medication orders are for labetalol, acetaminophen, morphine, and others, none of which are sedatives. |
| E1674875 | Continue monitoring oxygenation and respiratory status given persistent hypoxemia and hypercapnia on supplemental oxygen. | Hypoxemia is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E1674875 | Assess and manage hypotension with mean arterial pressure in the 40s-70s mmHg range. | Mean arterial pressure is in the 40s-70s mmHg range. | stated outright | Median mean arterial pressure over the 6 h before the decision: 65 mmHg (6 readings), normal by the rule 'hypotension MAP < 65'. |
| E1674875 | Assess and manage hypotension with mean arterial pressure in the 40s-70s mmHg range. | Hypotension is present. | presupposed by an action | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1682105 | Assess and manage hypotension with intravenous fluids as needed. | Hypotension is present. | presupposed by an action | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1739131 | Continue monitoring vital signs and oxygen saturation on room air, given stable GCS and hemodynamics. | Hemodynamics are stable. | stated outright | 'cardiovascular status normal' holds when any component is normal. heart rate: yes; systolic BP: no; mean arterial pressure: yes. |
| E1739131 | Maintain current IV fluid infusion at 100 mL/hour. | IV fluid infusion is currently running at 100 mL/hour. | presupposed by an action | The most recent relevant record, R19, shows an IV fluid infusion running at 100 ml/hour, but it started at 10:06 on 2100-01-01, which is over 23 hours before the decision time of 09:51 on 2100-01-02. There is no administration record within the 24 hours prior to the decision time to confirm the infusion is currently running. |
| E1781359 | Continue scheduled antibiotic therapy with piperacillin-tazobactam and vancomycin for sepsis treatment. | Piperacillin-tazobactam is currently being given. | presupposed by an action | The records show a piperacillin-tazobactam administration that started at 23:00 on 2100-01-01, which is more than 24 hours before the decision time of 19:47 on 2100-01-02. There is no administration record for piperacillin-tazobactam within the 24 hours preceding the decision time, so the statement that it is currently being given is not supported. |
| E1823727 | Continue hemodialysis as documented for renal failure. | Hemodialysis is currently being given. | presupposed by an action | The records document hemodialysis as a treatment (R35, R42, R47), but there is no administration record of hemodialysis in the 24 hours before the decision time. The most recent documentation is from 08:42 on 2100-01-02, which does not confirm it is currently being given. |
| E1823727 | Monitor potassium level given hyperkalemia. | Hyperkalemia is present. | stated outright | Latest potassium 5.1 mmol/L at 2100-01-02 10:00:00 (reference 3.3 to 5.1) is normal, not consistent with 'high'. |
| E1824650 | Continue scheduled aspirin, metoprolol, famotidine, docusate, and potassium chloride as ordered. | Potassium chloride is currently being given. | presupposed by an action | The records show a potassium chloride IV order that was stopped before the decision time (R10), a one-minute IV administration the previous day (R31), and a PO potassium chloride order running at decision time (R45), but no IV potassium chloride administration in the 24 hours before the decision time. |
| E1824650 | Monitor blood glucose and administer sliding-scale insulin as ordered. | Sliding-scale insulin orders are active. | presupposed by an action | The records show an active scheduled order for regular insulin subcutaneous QID AC (R49), but no sliding-scale insulin order is present. The statement specifically claims sliding-scale insulin orders are active, which is not documented. |
| E1824650 | Assess readiness for ICU discharge given stable vitals, GCS 15, and room air. | Vitals are stable. | stated outright | 'vital signs normal' holds when any component is normal. heart rate: yes; systolic BP: yes; mean arterial pressure: yes; respiratory rate: no; SpO2: yes; temperature: yes. |
| E1824650 | Assess readiness for ICU discharge given stable vitals, GCS 15, and room air. | The patient is on room air. | stated outright | The records show the patient was on mechanical ventilation and oxygen therapy, with a PEEP setting of 0 cmH2O at 05:55, but there is no documentation of the patient being on room air. The most recent respiratory records indicate ventilator weaning and oxygen therapy, not room air. |
| E1829278 | Continue nicardipine infusion for blood pressure control, as it was running at 7.5 mg/hour at the decision point. | Nicardipine infusion is currently running. | presupposed by an action | The nicardipine infusion record (R36) shows it ran from 03:00 to 08:24, ending 19 minutes before the decision time of 08:43. There is no record of it running at the decision time, so the statement that it is currently running is not supported. |
| E1829278 | Continue nicardipine infusion for blood pressure control, as it was running at 7.5 mg/hour at the decision point. | Nicardipine infusion was running at 7.5 mg/hour. | stated outright | The nicardipine infusion at 7.5 mg/hour ended at 08:24, before the decision time of 08:43, and no record shows it running at the decision time. |
| E1829278 | Monitor neurological status with Glasgow Coma Scale, which was 9 at 03:00 and improved from 11 earlier. | Glasgow Coma Scale improved from 11 earlier. | stated outright | The GCS was 9 at 08:00 (R8), improved to 11 at 15:27 (R33), but then dropped back to 9 at 03:00 (R43). The statement that it 'improved from 11 earlier' is contradicted by the most recent value of 9. |
| E1856821 | Continue norepinephrine infusion for shock, with dose titration to maintain adequate mean arterial pressure. | Norepinephrine infusion is currently being given. | presupposed by an action | The most recent norepinephrine infusion record (R41) ended at 14:11 on 2100-01-02, over 4 hours before the decision time of 18:36. There is no administration record showing the infusion was running at the decision time. |
| E2230341 | Continue eptifibatide infusion as ordered. | Eptifibatide infusion is currently being given. | presupposed by an action | The records show eptifibatide infusions that ended at 00:24 and 09:05 on 2100-01-02, and a brief infusion at 05:00. There is no administration record of eptifibatide in the 24 hours before the decision time of 14:38, so the statement that it is currently being given is not supported. |
| E2309912 | Monitor blood pressure and heart rate closely given persistent hypertension and tachycardia, with PRN antihypertensives available. | Hypertension is persistent. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E2309912 | Monitor blood pressure and heart rate closely given persistent hypertension and tachycardia, with PRN antihypertensives available. | Tachycardia is persistent. | stated outright | Median heart rate over the 6 h before the decision: 83.5 bpm (12 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E2558122 | Assess and manage hypoxemia with escalating oxygen support, including consideration of noninvasive ventilation, given SpO2 90–92% on oxymask and prior BiPAP use. | Hypoxemia is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no. |
| E2609672 | Monitor blood glucose with finger-stick checks given recent hypoglycemia and glucose variability. | Recent hypoglycemia is present. | stated outright | 0 of 2 glucose values in the 24 h before the decision were low. |
| E2714303 | Continue levetiracetam and phenytoin anticonvulsant therapy for seizure management. | Levetiracetam is currently being given. | presupposed by an action | The records document levetiracetam as a treatment for seizure therapy, but there is no administration record showing it was given in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E2714303 | Continue levetiracetam and phenytoin anticonvulsant therapy for seizure management. | Phenytoin is currently being given. | presupposed by an action | The records document phenytoin as a treatment for seizure therapy, but there is no administration record showing it was given within 24 hours before the decision time. A treatment documentation alone does not confirm current administration. |
| E2714303 | Assess and manage fever with temperature 101.7°F and tachycardia. | Temperature is 101.7°F. | stated outright | Median temperature over the 6 h before the decision: 99.15 F (2 readings), normal by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. |
| E2814579 | Monitor blood glucose and continue insulin infusion to maintain glycemic control. | Insulin infusion is currently being given. | presupposed by an action | The only insulin administration record is an infusion at 13:00 on 2100-01-02, which is more than 24 hours before the decision time of 22:47 on 2100-01-02. There is no record of insulin being given within the 24 hours before the decision time. |
| E2879373 | Monitor blood pressure closely due to wide pulse pressure and diastolic pressures as low as 30 mmHg. | Pulse pressure is wide. | stated outright | Median heart rate over the 6 h before the decision: 86 bpm (6 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E2879373 | Continue non-invasive ventilation with FiO2 40% and monitor respiratory status, given persistent hypercapnia and bicarbonate elevation. | The patient is currently on non-invasive ventilation (BiPAP/CPAP). | presupposed by an action | The only record mentioning non-invasive ventilation is R23, a treatment documentation from 2100-01-01 10:19, which is over 23 hours before the decision time. There is no administration or 'Running at decision time' record for NIV within 24 hours before 2100-01-02 09:35, so the statement that the patient is currently on NIV is not supported. |
| E3027283 | Monitor serum sodium closely and reassess diuretic strategy given severe hyponatremia (Na 120 mmol/L) and hypervolemic heart failure. | Hypervolemic heart failure is present. | stated outright | The records mention congestive heart failure (CHF) as an admission diagnosis, but they do not document hypervolemia or any findings (e.g., edema, fluid overload) that would support the specific claim of 'hypervolemic heart failure'. |
| E3035113 | Monitor blood glucose given recent hyperglycemia and hypoglycemia. | Recent hypoglycemia is present. | stated outright | 0 of 1 glucose values in the 24 h before the decision were low. |
| E3035113 | Assess and manage hypokalemia (potassium 3.4 mmol/L). | Hypokalemia is present. | stated outright | Latest potassium 3.4 mmol/L at 2100-01-02 09:39:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E3053511 | Continue monitoring respiratory status and oxygenation given persistent tachypnea and intermittent hypoxemia. | Intermittent hypoxemia is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E3053511 | Continue antibiotic therapy with vancomycin and piperacillin/tazobactam as documented, with monitoring of vancomycin trough. | Vancomycin is currently being given. | presupposed by an action | The records document vancomycin as a treatment (R10, R37) and show a vancomycin trough level (R36), but there is no medication administration record for vancomycin within 24 hours of the decision time. Therefore, the statement that it is currently being given is not supported. |
| E3053511 | Continue antibiotic therapy with vancomycin and piperacillin/tazobactam as documented, with monitoring of vancomycin trough. | Piperacillin/tazobactam is currently being given. | presupposed by an action | The records document piperacillin/tazobactam as a treatment (R9, R35), but there is no medication administration record showing it was given in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E3111371 | Monitor vital signs and CIWA/withdrawal scores closely given fluctuating hypertension, tachycardia, tachypnea, and sedation scores. | Hypertension is fluctuating. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E3111371 | Monitor vital signs and CIWA/withdrawal scores closely given fluctuating hypertension, tachycardia, tachypnea, and sedation scores. | Tachycardia is fluctuating. | stated outright | Median heart rate over the 6 h before the decision: 96 bpm (5 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E3111371 | Monitor vital signs and CIWA/withdrawal scores closely given fluctuating hypertension, tachycardia, tachypnea, and sedation scores. | Tachypnea is fluctuating. | stated outright | Median respiratory rate over the 6 h before the decision: 19 insp/min (5 readings), normal by the rule 'tachypnea RR > 20; bradypnea RR < 12'. |
| E3124669 | Monitor serum potassium and replete as needed, given persistent hypokalemia (3.3 mmol/L at 20:00 on 2100-01-01). | Hypokalemia is present. | stated outright | Latest potassium 3.3 mmol/L at 2100-01-01 20:00:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E3130379 | Obtain repeat arterial blood gas to reassess hypercapnia and acid-base status. | Acid-base status is abnormal. | presupposed by an action | The most recent arterial blood gas (R47) shows a pH of 7.35, which is within the normal range (7.35-7.45), and a base excess of 8 (R43), which is mildly elevated but does not indicate a clinically significant acid-base abnormality. The earlier pH of 7.36 (R4) is also normal. |
| E3148216 | Monitor oxygen saturation and respiratory status closely given declining SpO2 and increased oxygen requirement. | SpO2 is declining. | stated outright | 0 of 23 SpO2 values in the 24 h before the decision were low. |
| E3148216 | Monitor oxygen saturation and respiratory status closely given declining SpO2 and increased oxygen requirement. | Oxygen requirement is increased. | stated outright | The oxygen flow rate decreased from 4 L/min to 2 L/min at 12:18 and remained at 2 L/min, while SpO2 declined to 91-94% in the hours before the decision time. The records do not show an increased oxygen requirement; instead, the requirement was reduced. |
| E3148216 | Assess for possible infection or other cause of fever and respiratory changes. | Fever is present. | presupposed by an action | Median temperature over the 6 h before the decision: 99.9 F (1 readings), normal by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. |
| E3170528 | Continue stress ulcer prophylaxis with pantoprazole as ordered. | Pantoprazole is currently being given. | presupposed by an action | The records show a pantoprazole order and a prior IV administration on 2100-01-01, but no administration within 24 hours before the decision time of 2100-01-02 03:39. The most recent administration ended at 14:10 on the previous day, so the statement that it is 'currently being given' is not supported. |
| E3178242 | Assess and manage worsening hypoxemia and tachypnea on 2 L/min nasal cannula, with SpO2 93% and pO2 85 mmHg, considering escalation of respiratory support. | Hypoxemia is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E3220742 | Continue levetiracetam for seizure prophylaxis/therapy as ordered. | Levetiracetam is currently being given. | presupposed by an action | The records show a levetiracetam administration on 2100-01-01 at 05:00 (R31) and treatment documentation (R18, R42), but no administration within 24 hours before the decision time of 2100-01-02 02:33. Therefore, the statement that it is 'currently being given' is not supported. |
| E3223097 | Monitor serum potassium and treat hyperkalemia as indicated. | Hyperkalemia is present. | presupposed by an action | Latest potassium 4.2 mmol/L at 2100-01-02 08:10:00 (reference 3.3 to 5.1) is normal, not consistent with 'high'. |
| E3223097 | Monitor blood pressure and hemoglobin for ongoing bleeding and hemodynamic instability. | Ongoing bleeding is present. | stated outright | The records show an admission diagnosis of upper GI bleeding and treatments for it (blood products, octreotide), but no direct evidence of ongoing bleeding at the decision time. The most recent relevant records document treatment, not active bleeding. |
| E3233620 | Continue scheduled esomeprazole for stress ulcer prophylaxis. | Scheduled esomeprazole is currently being given. | presupposed by an action | The only administration record for esomeprazole (R22) is from 2100-01-01 15:00, which is more than 24 hours before the decision time of 2100-01-02 13:57. There is no record of esomeprazole being administered within the 24 hours prior to the decision time, so the statement that it is 'currently being given' is not supported. |
| E3233620 | Monitor vital signs and oxygen saturation closely given diminished breath sounds and borderline oxygenation. | Oxygenation is borderline. | stated outright | 'oxygenation abnormal' holds when any component is abnormal. SpO2: no. |

## 5. Judge panel

287 items went to the judge panel. Agreement: {'1/1': 287} (split = no majority; the conservative label was used and the item needs human review).

## 6. Per-case score sheets

| Case | Facts | supported | not_supported | not_addressed | unverifiable | Treatment agreement | Vital recall | All recall |
|---|---|---|---|---|---|---|---|---|
| E153972 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E172015 | 9 | 88.9% | 11.1% | 0.0% | 0.0% | - | - | - |
| E184757 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 0.0% | - | - |
| E211144 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E284265 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E297175 | 5 | 60.0% | 20.0% | 20.0% | 0.0% | 33.3% | - | - |
| E322290 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E375854 | 8 | 62.5% | 37.5% | 0.0% | 0.0% | - | - | - |
| E383358 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E395323 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E405746 | 7 | 85.7% | 14.3% | 0.0% | 0.0% | - | - | - |
| E454584 | 9 | 77.8% | 22.2% | 0.0% | 0.0% | 33.3% | - | - |
| E467819 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E490454 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 100.0% | - | - |
| E521456 | 6 | 50.0% | 50.0% | 0.0% | 0.0% | 25.0% | - | - |
| E664474 | 7 | 71.4% | 14.3% | 14.3% | 0.0% | 0.0% | - | - |
| E733082 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E756295 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 33.3% | - | - |
| E758325 | 9 | 100.0% | 0.0% | 0.0% | 0.0% | 66.7% | - | - |
| E826669 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E850469 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 0.0% | - | - |
| E876429 | 8 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E899746 | 8 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E942382 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E962227 | 7 | 85.7% | 0.0% | 14.3% | 0.0% | 0.0% | - | - |
| E978037 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1056063 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | - | - | - |
| E1057910 | 9 | 55.6% | 22.2% | 22.2% | 0.0% | 0.0% | - | - |
| E1057967 | 7 | 85.7% | 0.0% | 14.3% | 0.0% | - | - | - |
| E1064283 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1065859 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1068212 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1071224 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071450 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1090039 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 100.0% | - | - |
| E1090889 | 8 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1099398 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1117947 | 4 | 25.0% | 75.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1121034 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 33.3% | - | - |
| E1171473 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1173453 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1177589 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | - | - | - |
| E1287791 | 6 | 33.3% | 50.0% | 16.7% | 0.0% | - | - | - |
| E1290248 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1449360 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | - | - | - |
| E1496959 | 7 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1497157 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1588473 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1592666 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1619343 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1636307 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1653043 | 8 | 62.5% | 25.0% | 12.5% | 0.0% | - | - | - |
| E1672915 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1674875 | 8 | 62.5% | 37.5% | 0.0% | 0.0% | 0.0% | - | - |
| E1682105 | 4 | 50.0% | 25.0% | 25.0% | 0.0% | 0.0% | - | - |
| E1705630 | 7 | 85.7% | 0.0% | 14.3% | 0.0% | - | - | - |
| E1739131 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1781359 | 9 | 88.9% | 11.1% | 0.0% | 0.0% | 33.3% | - | - |
| E1790816 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823356 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823727 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1824650 | 9 | 55.6% | 44.4% | 0.0% | 0.0% | 0.0% | - | - |
| E1829278 | 6 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1837964 | 11 | 100.0% | 0.0% | 0.0% | 0.0% | 10.0% | - | - |
| E1853162 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1856821 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2230341 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E2309912 | 4 | 25.0% | 50.0% | 25.0% | 0.0% | - | - | - |
| E2418055 | 8 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E2419768 | 6 | 66.7% | 0.0% | 33.3% | 0.0% | 0.0% | - | - |
| E2558122 | 7 | 85.7% | 14.3% | 0.0% | 0.0% | 0.0% | - | - |
| E2609672 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2714303 | 6 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2725629 | 4 | 75.0% | 0.0% | 25.0% | 0.0% | 0.0% | - | - |
| E2757707 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2814579 | 7 | 71.4% | 14.3% | 14.3% | 0.0% | 66.7% | - | - |
| E2860378 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E2879373 | 7 | 71.4% | 28.6% | 0.0% | 0.0% | 100.0% | - | - |
| E3001552 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3027283 | 5 | 60.0% | 20.0% | 20.0% | 0.0% | 100.0% | - | - |
| E3033795 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3035113 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3053511 | 6 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3067309 | 7 | 100.0% | 0.0% | 0.0% | 0.0% | 25.0% | - | - |
| E3110594 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E3111371 | 5 | 40.0% | 60.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3112232 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3115505 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3124669 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3130379 | 9 | 88.9% | 11.1% | 0.0% | 0.0% | 50.0% | - | - |
| E3148216 | 4 | 25.0% | 75.0% | 0.0% | 0.0% | - | - | - |
| E3150018 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E3152779 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E3170528 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3178242 | 6 | 66.7% | 16.7% | 16.7% | 0.0% | - | - | - |
| E3205786 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3220742 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3223097 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3233620 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3237226 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
