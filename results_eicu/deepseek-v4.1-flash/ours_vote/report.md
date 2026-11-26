# Evaluation of AI clinical suggestions against patient records

- Input: `eicu_triples_deepseek-v4.1-flash.json`; 100 cases, 3.0 AI suggestions per case on average.
- Models: atomizer `deepseek-v4-pro:0813:cloud`; judge panel `deepseek-v4-pro:0813:cloud`, `minimax-m3.1-flash:cloud`, `glm-5.3:cloud` (majority vote; reasoning mode: none); 862 new model calls, 0 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 19.6% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 530 |
| supported / not_supported / not_addressed / unverifiable | 400 / 95 / 35 / 0 |
| Fact accuracy = supported / (supported + not_supported) | 80.8% |
| Cases with at least one not_supported fact | 56 / 100 |
| Omitted findings: abnormalities the clinicians treated that no AI fact mentions | 0 / 0 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 344 | 82.4% | {'supported': 277, 'not_supported': 59, 'not_addressed': 8} |
| presupposed by an action | 169 | 78.1% | {'supported': 118, 'not_supported': 33, 'not_addressed': 18} |
| clinical judgment | 17 | 62.5% | {'not_supported': 3, 'not_addressed': 9, 'supported': 5} |
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
| E184757 | Continue scheduled piperacillin-tazobactam 3-0.375 g IV every 8 hours for ongoing infection treatment. | Ongoing infection treatment is needed. | clinical judgment | The records show a piperacillin-tazobactam administration running at decision time on 2099-12-19 (R3), but no administration of this antibiotic within 24 hours before the decision time of 2100-01-02 23:48. The statement that ongoing infection treatment is needed is therefore not supported by recent administration records. |
| E284265 | Continue diltiazem infusion for rate control of atrial arrhythmia. | Diltiazem infusion is currently being given. | presupposed by an action | The only administration record for diltiazem is an infusion that ran from 2100-01-01 21:00 to 2100-01-02 05:00, which ended over 13 hours before the decision time of 2100-01-02 18:11. Therefore, it is not currently being given. |
| E284265 | Continue diltiazem infusion for rate control of atrial arrhythmia. | Atrial arrhythmia is present. | presupposed by an action | The records document arrhythmias and treatment with diltiazem, but they do not specifically identify the arrhythmia as atrial. |
| E297175 | Continue non-invasive ventilation with FiO2 40% and PEEP 5 cmH2O, monitoring oxygenation and respiratory status. | FiO2 is 40%. | stated outright | The most recent FiO2 measurement before the decision time is 45% (R40), not 40%. Earlier records show 40%, but the latest value contradicts the statement. |
| E322290 | Monitor blood pressure and heart rate closely given recent systolic blood pressure of 91 mmHg and tachycardia. | Tachycardia is present. | stated outright | 0 of 16 heart rate values in the 24 h before the decision were high. |
| E375854 | Assess and manage ongoing hypotension with persistent tachycardia in the setting of GI bleeding and dropping hemoglobin. | Hypotension is present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E375854 | Assess and manage ongoing hypotension with persistent tachycardia in the setting of GI bleeding and dropping hemoglobin. | Tachycardia is present. | stated outright | Median heart rate over the 6 h before the decision: 88.5 bpm (6 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E375854 | Assess and manage ongoing hypotension with persistent tachycardia in the setting of GI bleeding and dropping hemoglobin. | GI bleeding is present. | stated outright | The records document a 'bleeding scan' (R33) and gastroenterology consultations, but they do not contain a diagnosis of GI bleeding or any direct evidence such as hematemesis, melena, or a positive scan result. Therefore, the presence of GI bleeding is not confirmed. |
| E375854 | Order serial hemoglobin/hematocrit checks and consider blood product transfusion given hemoglobin 7.8 g/dL and active GI bleed. | Active GI bleed is present. | stated outright | The records document a 'bleeding scan' (R36), which suggests investigation for bleeding, but they do not contain a diagnosis or direct evidence confirming an active GI bleed. Therefore, the statement is addressed but not supported. |
| E375854 | Continue monitoring oxygen saturation and administer supplemental oxygen as needed given O2 saturation 94% on 3 L/min nasal cannula. | The patient is on 3 L/min nasal cannula. | stated outright | The records document nasal cannula oxygen therapy at 30-40% on 2100-01-01, but there is no record of the specific 3 L/min flow rate at the decision time on 2100-01-02. |
| E405746 | Monitor oxygen saturation and respiratory status given intermittent desaturation to 91% and 93% in the prior 24 hours. | Desaturation is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no. |
| E454584 | Assess and manage sedation and delirium, considering the patient's fluctuating RASS and CAM-ICU positive status. | RASS is fluctuating. | stated outright | The records contain multiple RASS entries, but none include a numerical score or value. Without any recorded RASS values, the claim that the RASS is 'fluctuating' cannot be supported. |
| E454584 | Assess and manage sedation and delirium, considering the patient's fluctuating RASS and CAM-ICU positive status. | CAM-ICU is positive. | stated outright | The records mention CAM-ICU assessments but do not record a positive result. The rows only list the scale name 'CAM-ICU' without a score or positive/negative designation, so the statement that CAM-ICU is positive is not supported. |
| E467819 | Continue nicardipine infusion for blood pressure control in intracranial hemorrhage. | Nicardipine infusion is currently being given. | presupposed by an action | The most recent nicardipine administration record (R50) ended at 00:00 on 2100-01-02, which is more than 24 hours before the decision time of 01:43 on 2100-01-02. No administration record exists within the 24 hours prior to the decision time. |
| E490454 | Continue non-invasive ventilation with BiPAP mask given recurrent hypoxemia (SpO2 91% at 23:20) after weaning to nasal cannula. | Recurrent hypoxemia is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E490454 | Assess for possible causes of worsening hypoxemia, including bronchospasm, fluid overload, or mucus plugging, and consider need for bronchodilator therapy or diuresis. | Worsening hypoxemia is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E521456 | Monitor blood glucose closely and continue insulin sliding scale to maintain glycemic control, given recent hypoglycemia and hyperglycemia. | Recent hypoglycemia is present. | stated outright | 0 of 1 glucose values in the 24 h before the decision were low. |
| E521456 | Monitor blood glucose closely and continue insulin sliding scale to maintain glycemic control, given recent hypoglycemia and hyperglycemia. | Recent hyperglycemia is present. | stated outright | 0 of 1 glucose values in the 24 h before the decision were high. |
| E664474 | Monitor oxygen saturation and respiratory rate closely given persistent tachypnea and oxygen requirement. | Tachypnea is persistent. | stated outright | Median respiratory rate over the 6 h before the decision: 19 insp/min (5 readings), normal by the rule 'tachypnea RR > 20; bradypnea RR < 12'. |
| E876429 | Continue mechanical ventilation with current settings (FiO2 40%, PEEP 5 cmH2O, PSV 10 cmH2O) and monitor oxygenation and respiratory status. | The patient is currently on mechanical ventilation. | stated outright | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 8.4 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E876429 | Continue vasopressor and sedative infusions (epinephrine, norepinephrine, phenylephrine, propofol) and monitor hemodynamics and sedation. | Phenylephrine is currently being given. | stated outright | The records show phenylephrine was infused from 01:00 to 13:00 on 2100-01-02, but the most recent administration record (R44) indicates the infusion ended at 13:00, which is 8 hours before the decision time of 21:00. Therefore, the statement that phenylephrine is currently being given is not supported. |
| E942382 | Continue diltiazem infusion for rate control of atrial arrhythmia. | Diltiazem infusion is currently being given. | presupposed by an action | The records show a diltiazem infusion documented at 17:04 on 2100-01-01, but no administration record within 24 hours before the decision time (2100-01-02 21:00) or a 'Running at decision time' record for diltiazem. Therefore, the statement that the patient is currently receiving diltiazem is not supported. |
| E942382 | Continue diltiazem infusion for rate control of atrial arrhythmia. | Atrial arrhythmia is present. | stated outright | The records document diltiazem as a treatment, but there is no administration record showing it was given in the 24 hours before the decision time. The heart rate measurements show a decline, but lab values do not prove drug administration. |
| E942382 | Monitor heart rate and blood pressure closely given bradycardia and intermittent hypotension. | Intermittent hypotension is present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1056063 | Continue continuous pulse oximetry and vital sign monitoring in the ICU, with attention to intermittent oxygen desaturation and tachycardia. | Intermittent oxygen desaturation is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no. |
| E1056063 | Reassess neurologic status and GCS, and continue psychiatric consultation follow-up for substance overdose management. | Psychiatric consultation is currently ongoing. | presupposed by an action | The records show a psychiatry consultation was documented on 2100-01-01 at 10:33, but there is no record of an ongoing psychiatric consultation at the decision time of 2100-01-02. |
| E1057910 | Continue mechanical ventilation with FiO2 0.4 and monitor oxygenation, as the patient remains intubated with GCS 3 and RASS -4. | RASS is -4. | stated outright | The statement claims the patient is currently receiving mechanical ventilation, but the records show no ventilator settings, tube device, or administration of ventilation. The most recent respiratory rate is 16, and there is no evidence of mechanical ventilation support. |
| E1057910 | Monitor blood pressure and titrate vasopressor support as needed, given recent hypotension and current norepinephrine use. | Norepinephrine is currently being given. | stated outright | The only norepinephrine record is an administration from 2100-01-01 03:47 to 15:32, which ended more than 24 hours before the decision time of 2100-01-02 21:00. There is no record of norepinephrine being given or running at the decision time. |
| E1064283 | Continue scheduled prednisone and pyridostigmine therapy for myasthenia gravis. | Pyridostigmine is currently being given. | presupposed by an action | The records document a treatment for 'reversal of neuromuscular blockade / pyridostigmine' (R39), but there is no administration record of pyridostigmine being given in the 24 hours before the decision time. The statement that the patient is 'currently receiving' pyridostigmine is therefore not supported by the available records. |
| E1064283 | Assess for need to intensify antihypertensive therapy given persistent systolic blood pressure >190 mmHg. | Systolic blood pressure is persistently greater than 190 mmHg. | stated outright | No recorded systolic BP matches the stated 190; values in the 24 h before the decision ranged 121 to 217 mmHg (latest 194). |
| E1068212 | Continue monitoring heart rate and blood pressure, given persistent tachycardia (HR 112-130 bpm) and low diastolic pressures. | Diastolic blood pressure is low. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1090039 | Monitor hemodynamic status and response to vasoactive infusions (norepinephrine, dopamine) given recent hypotension. | Hypotension was recently present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1117947 | Monitor blood pressure and heart rate closely due to hypotension and tachycardia. | Hypotension is present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no. |
| E1117947 | Monitor blood pressure and heart rate closely due to hypotension and tachycardia. | Tachycardia is present. | stated outright | Median heart rate over the 6 h before the decision: 81 bpm (6 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E1171473 | Continue mechanical ventilation with current settings, monitoring oxygenation and ventilation. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('Tidal Volume (set): 500 mL') was 6.8 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1177589 | Continue supplemental oxygen via nasal cannula as needed to maintain oxygen saturation, with weaning as tolerated. | Supplemental oxygen via nasal cannula is currently being given. | presupposed by an action | The records show nasal cannula use on 2100-01-01, but the most recent oxygen delivery device entry (R13) is from 10:15 on that day. There is no record of nasal cannula use or oxygen administration on 2100-01-02, the day of the decision time, so the statement that the patient is currently receiving supplemental oxygen via nasal cannula is not supported. |
| E1287791 | Continue mannitol infusion for elevated intracranial pressure management in the setting of ICH/cerebral infarct. | Mannitol infusion is currently being given. | presupposed by an action | The records document a treatment note for 'mannitol / continuous infusion' but do not contain any medication administration record showing mannitol was actually given within the 24 hours before the decision time. |
| E1287791 | Monitor blood pressure closely given recent systolic readings ranging from 107 to 185 mmHg and mean arterial pressure as low as 71 mmHg. | Mean arterial pressure is as low as 71 mmHg. | stated outright | 0 of 24 mean arterial pressure values in the 24 h before the decision were low. |
| E1287791 | Assess and manage fever with temperature 100.8 F, including evaluation for infection. | Temperature is 100.8 F. | stated outright | Median temperature over the 6 h before the decision: 100.4 F (2 readings), normal by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. |
| E1290248 | Monitor hemoglobin and hematocrit given declining trend (Hgb 7.9 to 7.1 g/dL) and ongoing GI bleeding risk. | Ongoing GI bleeding risk is present. | clinical judgment | The records show a continuous pantoprazole infusion running at the decision time (R1), but no administration of octreotide is documented. The statement claims the patient is receiving octreotide, which is not supported by the available records. |
| E1290248 | Assess need for blood product transfusion given hemoglobin 7.1 g/dL and active GI bleeding. | Active GI bleeding is present. | stated outright | The records document blood product administration (R36) and platelet counts of 127 and 117 x10^3/uL (R45, R50), but they do not mention active GI bleeding or a hemoglobin of 7.1 g/dL. The statement's claim of active bleeding and specific hemoglobin value is not supported by the provided data. |
| E1449360 | Monitor blood pressure closely, given persistent diastolic hypertension (diastolic 86-97 mmHg) over the past 24 hours. | Persistent diastolic hypertension is present. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E1588473 | Continue supplemental oxygen via nasal cannula and monitor oxygen saturation, given recurrent desaturations to 88-91% on room air. | Supplemental oxygen via nasal cannula is currently being given. | presupposed by an action | The most recent O2 Delivery Device record before the decision time (R50, 12:29) shows 'None (Room air)', not a nasal cannula. Therefore, the statement that the patient is currently on supplemental oxygen via nasal cannula is contradicted by the latest charting. |
| E1619343 | Continue insulin infusion and monitor glucose closely as glucose has risen to 218 mg/dL. | Insulin infusion is currently being given. | presupposed by an action | The records document a continuous insulin infusion (R22), but the most recent glucose before the decision time is 218 mg/dL (R48), not 180 mg/dL as stated. The statement is therefore not supported by the latest recorded value. |
| E1636307 | Continue mechanical ventilation with current settings (FiO2 30%, PEEP 5 cmH2O, set RR 12) and monitor respiratory status. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 9.7 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1636307 | Continue mechanical ventilation with current settings (FiO2 30%, PEEP 5 cmH2O, set RR 12) and monitor respiratory status. | FiO2 is 30%. | stated outright | The statement claims the patient is on FiO2 30%, but the most recent oxygen delivery records (R49, R50) show 'O2 L/%: 4', indicating a nasal cannula at 4 L/min, not a ventilator with 30% FiO2. No ventilator setting or tube device is charted after these rows. |
| E1653043 | Continue monitoring anticoagulation with serial PTT/INR given supratherapeutic PTT levels (159.3 s, 97.8 s, 95.4 s) on heparin and warfarin therapy. | Heparin therapy is currently being given. | presupposed by an action | The records document anticoagulant administration with conventional heparin therapy and coumadin, but there is no administration record of heparin in the 24 hours before the decision time. The only anticoagulant administration record is for warfarin (R7), so the statement that the patient is currently receiving heparin is not supported. |
| E1672915 | Assess and manage pain and agitation with as-needed opioid and sedative therapy per existing orders. | Sedative orders are active. | presupposed by an action | The records show multiple administrations of lorazepam, but the last dose was given at 21:45 on 2100-01-01, which is more than 24 hours before the decision time of 2100-01-02 19:54. There is no administration of lorazepam within the 24 hours prior to the decision time. |
| E1674875 | Continue monitoring oxygenation and respiratory status given persistent hypoxemia and hypercapnia on supplemental oxygen. | Hypoxemia is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E1674875 | Assess and manage hypotension with mean arterial pressure in the 40s-70s mmHg range. | Mean arterial pressure is in the 40s-70s mmHg range. | stated outright | Median mean arterial pressure over the 6 h before the decision: 65 mmHg (6 readings), normal by the rule 'hypotension MAP < 65'. |
| E1674875 | Assess and manage hypotension with mean arterial pressure in the 40s-70s mmHg range. | Hypotension is present. | presupposed by an action | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1682105 | Assess and manage hypotension with intravenous fluids as needed. | Hypotension is present. | presupposed by an action | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1739131 | Continue monitoring vital signs and oxygen saturation on room air, given stable GCS and hemodynamics. | Hemodynamics are stable. | stated outright | 'cardiovascular status normal' holds when any component is normal. heart rate: yes; systolic BP: no; mean arterial pressure: yes. |
| E1823727 | Monitor hemoglobin and hematocrit given anemia and bleeding risk. | Bleeding risk is present. | stated outright | The statement claims the patient is currently bleeding, but the records show no active bleeding event. Hemoglobin values are low (7.3, 8.7, 8.5 gm/dL) but do not directly document active bleeding, and no bleeding source or event is recorded. |
| E1823727 | Monitor potassium level given hyperkalemia. | Hyperkalemia is present. | stated outright | Latest potassium 5.1 mmol/L at 2100-01-02 10:00:00 (reference 3.3 to 5.1) is normal, not consistent with 'high'. |
| E1824650 | Monitor blood glucose and administer sliding-scale insulin as ordered. | Sliding-scale insulin orders are active. | presupposed by an action | The records show an active order for subcutaneous insulin (R49) but no administration record of insulin in the 24 hours before the decision time; the prior IV insulin infusion (R22) ended at 14:30 on 2100-01-02, before the decision time. |
| E1824650 | Assess readiness for ICU discharge given stable vitals, GCS 15, and room air. | Vitals are stable. | stated outright | 'vital signs normal' holds when any component is normal. heart rate: yes; systolic BP: yes; mean arterial pressure: yes; respiratory rate: no; SpO2: yes; temperature: yes. |
| E1824650 | Assess readiness for ICU discharge given stable vitals, GCS 15, and room air. | The patient is on room air. | stated outright | The most recent ventilator setting shows PEEP set to 0 cmH2O at 05:55, and the latest respiratory rate is 21, which does not indicate stable weaning. The records do not show a GCS of 15 or readiness for ICU discharge. |
| E1829278 | Continue nicardipine infusion for blood pressure control, as it was running at 7.5 mg/hour at the decision point. | Nicardipine infusion is currently running. | presupposed by an action | The records show a Nicardipine infusion at 7.5 mg/hour that ended at 08:24 on 2100-01-02, but no administration is documented in the 24 hours before the decision time of 2100-01-02 21:00. Therefore, the statement that the patient is currently receiving Nicardipine is not supported. |
| E1829278 | Continue nicardipine infusion for blood pressure control, as it was running at 7.5 mg/hour at the decision point. | Nicardipine infusion was running at 7.5 mg/hour. | stated outright | The records show a Nicardipine infusion at 7.5 mg/hour from 03:00 to 08:24 on 2100-01-02, but no administration record within 24 hours before the decision time (2100-01-02 21:00) indicates it was running at the decision time. The infusion ended at 08:24, so the statement that it is currently running is not supported. |
| E1829278 | Monitor neurological status with Glasgow Coma Scale, which was 9 at 03:00 and improved from 11 earlier. | Glasgow Coma Scale improved from 11 earlier. | stated outright | The statement claims the Glasgow Coma Scale was 9 at 03:00 and improved from 11 earlier. The records show GCS Total of 9 at 03:00 (R42), but the earlier value at 15:27 was 11 (R32), so the statement that it improved from 11 is contradicted; it actually decreased from 11 to 9. |
| E1856821 | Continue norepinephrine infusion for shock, with dose titration to maintain adequate mean arterial pressure. | Norepinephrine infusion is currently being given. | presupposed by an action | The most recent norepinephrine infusion ran from 13:16 to 14:11 on 2100-01-02 and had ended before the decision time of 18:36, with no record showing it was running then. |
| E2230341 | Continue eptifibatide infusion as ordered. | Eptifibatide infusion is currently being given. | presupposed by an action | Eptifibatide infusions are documented, but the latest infusion ended at 09:05 on 2100-01-02, before the 14:38 decision time. No record shows it was still running or administered in the 24 hours before the decision time. |
| E2309912 | Continue lorazepam as needed for alcohol withdrawal, with monitoring of sedation and respiratory status. | Alcohol withdrawal is present. | presupposed by an action | The most recent respiratory rate before the decision time is 31 insp/min (R50), which is elevated, not normal. Earlier values fluctuate between 20 and 31, so the statement that the respiratory rate is normal is not supported. |
| E2309912 | Monitor blood pressure and heart rate closely given persistent hypertension and tachycardia, with PRN antihypertensives available. | Hypertension is persistent. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E2309912 | Monitor blood pressure and heart rate closely given persistent hypertension and tachycardia, with PRN antihypertensives available. | Tachycardia is persistent. | stated outright | Median heart rate over the 6 h before the decision: 83.5 bpm (12 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E2418055 | Continue EEG monitoring for seizure activity in a patient with persistently low Glasgow Coma Scale. | EEG monitoring is currently being performed. | presupposed by an action | EEG monitoring is documented as a treatment, but the record is not an administration or “running at decision time” record confirming that monitoring is currently being performed. |
| E2419768 | Continue scheduled ceftriaxone (Rocephin) IV daily for bacterial pneumonia. | Bacterial pneumonia is present. | clinical judgment | The records show ceftriaxone administration and respiratory findings, but they do not state or directly establish a diagnosis of bacterial pneumonia. |
| E2558122 | Assess and manage hypoxemia with escalating oxygen support, including consideration of noninvasive ventilation, given SpO2 90–92% on oxymask and prior BiPAP use. | Hypoxemia is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no. |
| E2609672 | Monitor blood glucose with finger-stick checks given recent hypoglycemia and glucose variability. | Recent hypoglycemia is present. | stated outright | 0 of 2 glucose values in the 24 h before the decision were low. |
| E2714303 | Continue levetiracetam and phenytoin anticonvulsant therapy for seizure management. | Levetiracetam is currently being given. | presupposed by an action | The records document levetiracetam and phenytoin as seizure therapy treatments, but there is no administration record for either drug in the 24 hours before the decision time. The statement that the patient is currently receiving these anticonvulsants is therefore not supported. |
| E2714303 | Continue levetiracetam and phenytoin anticonvulsant therapy for seizure management. | Phenytoin is currently being given. | presupposed by an action | The records document phenytoin as a seizure therapy/anticonvulsant (R35) and show phenytoin levels, but there is no administration record of phenytoin in the 24 hours before the decision time, so the statement that the patient is currently receiving phenytoin is not supported. |
| E2714303 | Assess and manage fever with temperature 101.7°F and tachycardia. | Temperature is 101.7°F. | stated outright | Median temperature over the 6 h before the decision: 99.15 F (2 readings), normal by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. |
| E2725629 | Monitor heart rate and blood pressure closely given the history of tachyarrhythmia and hypotension. | There is a history of tachyarrhythmia. | stated outright | The records show a history of tachyarrhythmia with heart rates up to 154 bpm on 2100-01-01, but the most recent heart rate at 20:30 on 2100-01-02 is 79 bpm, which is normal. The statement implies ongoing tachyarrhythmia, which is not supported by the latest measurements. |
| E2879373 | Monitor blood pressure closely due to wide pulse pressure and diastolic pressures as low as 30 mmHg. | Pulse pressure is wide. | stated outright | Median heart rate over the 6 h before the decision: 86 bpm (6 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E3035113 | Monitor blood glucose given recent hyperglycemia and hypoglycemia. | Recent hypoglycemia is present. | stated outright | 0 of 1 glucose values in the 24 h before the decision were low. |
| E3035113 | Assess and manage hypokalemia (potassium 3.4 mmol/L). | Hypokalemia is present. | stated outright | Latest potassium 3.4 mmol/L at 2100-01-02 09:39:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E3053511 | Continue monitoring respiratory status and oxygenation given persistent tachypnea and intermittent hypoxemia. | Intermittent hypoxemia is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E3053511 | Continue antibiotic therapy with vancomycin and piperacillin/tazobactam as documented, with monitoring of vancomycin trough. | Vancomycin is currently being given. | presupposed by an action | Vancomycin appears in treatment documentation and a trough was measured, but there is no administration record or running infusion within 24 hours of the decision time to show it is currently being given. |
| E3053511 | Continue antibiotic therapy with vancomycin and piperacillin/tazobactam as documented, with monitoring of vancomycin trough. | Piperacillin/tazobactam is currently being given. | presupposed by an action | The records document treatments for piperacillin/tazobactam and vancomycin, and a vancomycin trough level, but they do not show an administration record for either antibiotic within the 24 hours before the decision time. Therefore, the statement that the patient is currently receiving these antibiotics is not supported. |
| E3111371 | Monitor vital signs and CIWA/withdrawal scores closely given fluctuating hypertension, tachycardia, tachypnea, and sedation scores. | Hypertension is fluctuating. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E3111371 | Monitor vital signs and CIWA/withdrawal scores closely given fluctuating hypertension, tachycardia, tachypnea, and sedation scores. | Tachycardia is fluctuating. | stated outright | Median heart rate over the 6 h before the decision: 96 bpm (5 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E3111371 | Monitor vital signs and CIWA/withdrawal scores closely given fluctuating hypertension, tachycardia, tachypnea, and sedation scores. | Tachypnea is fluctuating. | stated outright | Median respiratory rate over the 6 h before the decision: 19 insp/min (5 readings), normal by the rule 'tachypnea RR > 20; bradypnea RR < 12'. |
| E3124669 | Monitor serum potassium and replete as needed, given persistent hypokalemia (3.3 mmol/L at 20:00 on 2100-01-01). | Hypokalemia is present. | stated outright | Latest potassium 3.3 mmol/L at 2100-01-01 20:00:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E3130379 | Continue BiPAP support with current settings (FiO2 30%, PEEP 8 cmH2O) and monitor oxygenation and ventilation, given persistent hypercapnia (pCO2 61 mmHg) and borderline oxygen saturation. | FiO2 is 30%. | stated outright | The most recent O2 Delivery Device record at 13:00 shows a nasal cannula, not BiPAP, and no later BiPAP setting is charted. The statement claims the patient is currently on BiPAP, which is contradicted by the latest device record. |
| E3130379 | Continue BiPAP support with current settings (FiO2 30%, PEEP 8 cmH2O) and monitor oxygenation and ventilation, given persistent hypercapnia (pCO2 61 mmHg) and borderline oxygen saturation. | PEEP is 8 cmH2O. | stated outright | The statement says the patient is on BiPAP with FiO2 30% and PEEP 8 cmH2O, but the most recent device record (R52) shows a nasal cannula, indicating BiPAP was discontinued before the decision time. |
| E3148216 | Monitor oxygen saturation and respiratory status closely given declining SpO2 and increased oxygen requirement. | SpO2 is declining. | stated outright | 0 of 23 SpO2 values in the 24 h before the decision were low. |
| E3148216 | Monitor oxygen saturation and respiratory status closely given declining SpO2 and increased oxygen requirement. | Oxygen requirement is increased. | stated outright | The most recent oxygen saturation values before the decision time show a decline to 92% and 91%, with the latest at 94%, which does not support the statement that oxygen requirement is increased; the values are not consistently rising and the latest is not the highest. |
| E3148216 | Assess for possible infection or other cause of fever and respiratory changes. | Fever is present. | presupposed by an action | Median temperature over the 6 h before the decision: 99.9 F (1 readings), normal by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. |
| E3178242 | Assess and manage worsening hypoxemia and tachypnea on 2 L/min nasal cannula, with SpO2 93% and pO2 85 mmHg, considering escalation of respiratory support. | Hypoxemia is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E3223097 | Monitor serum potassium and treat hyperkalemia as indicated. | Hyperkalemia is present. | presupposed by an action | Latest potassium 4.2 mmol/L at 2100-01-02 08:10:00 (reference 3.3 to 5.1) is normal, not consistent with 'high'. |
| E3223097 | Monitor blood pressure and hemoglobin for ongoing bleeding and hemodynamic instability. | Ongoing bleeding is present. | stated outright | The platelet count dropped from 164 k/uL at 01:59 to 82 k/uL at 08:10, which is a decrease, not an increase. The records do not show a rising platelet count. |
| E3233620 | Monitor vital signs and oxygen saturation closely given diminished breath sounds and borderline oxygenation. | Oxygenation is borderline. | stated outright | 'oxygenation abnormal' holds when any component is abnormal. SpO2: no. |
| E3237226 | Continue supplemental oxygen therapy via nasal cannula at 3 L/min to maintain oxygen saturation. | Supplemental oxygen therapy via nasal cannula is currently being given. | presupposed by an action | The most recent O2 Flow record before the decision time is 3 L/min (R33), not 2 L/min as stated. The statement is therefore contradicted by the latest measurement. |

## 5. Judge panel

287 items went to the judge panel. Agreement: {'3/3': 174, '2/3': 112, 'split': 1} (split = no majority; the conservative label was used and the item needs human review).

## 6. Per-case score sheets

| Case | Facts | supported | not_supported | not_addressed | unverifiable | Treatment agreement | Vital recall | All recall |
|---|---|---|---|---|---|---|---|---|
| E153972 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E172015 | 9 | 88.9% | 11.1% | 0.0% | 0.0% | - | - | - |
| E184757 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 0.0% | - | - |
| E211144 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E284265 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E297175 | 5 | 60.0% | 20.0% | 20.0% | 0.0% | 33.3% | - | - |
| E322290 | 5 | 60.0% | 20.0% | 20.0% | 0.0% | 0.0% | - | - |
| E375854 | 8 | 37.5% | 62.5% | 0.0% | 0.0% | - | - | - |
| E383358 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E395323 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E405746 | 7 | 85.7% | 14.3% | 0.0% | 0.0% | - | - | - |
| E454584 | 9 | 77.8% | 22.2% | 0.0% | 0.0% | 33.3% | - | - |
| E467819 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | - | - |
| E490454 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 100.0% | - | - |
| E521456 | 6 | 50.0% | 33.3% | 16.7% | 0.0% | 25.0% | - | - |
| E664474 | 7 | 57.1% | 14.3% | 28.6% | 0.0% | 0.0% | - | - |
| E733082 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E756295 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 33.3% | - | - |
| E758325 | 9 | 100.0% | 0.0% | 0.0% | 0.0% | 66.7% | - | - |
| E826669 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E850469 | 6 | 83.3% | 0.0% | 16.7% | 0.0% | 0.0% | - | - |
| E876429 | 8 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E899746 | 8 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E942382 | 4 | 25.0% | 75.0% | 0.0% | 0.0% | 0.0% | - | - |
| E962227 | 7 | 85.7% | 0.0% | 14.3% | 0.0% | 0.0% | - | - |
| E978037 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1056063 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | - | - | - |
| E1057910 | 9 | 55.6% | 22.2% | 22.2% | 0.0% | 0.0% | - | - |
| E1057967 | 7 | 85.7% | 0.0% | 14.3% | 0.0% | - | - | - |
| E1064283 | 6 | 50.0% | 33.3% | 16.7% | 0.0% | 0.0% | - | - |
| E1065859 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1068212 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1071224 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071450 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1090039 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 100.0% | - | - |
| E1090889 | 8 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1099398 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1117947 | 4 | 25.0% | 50.0% | 25.0% | 0.0% | 50.0% | - | - |
| E1121034 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 33.3% | - | - |
| E1171473 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1173453 | 6 | 83.3% | 0.0% | 16.7% | 0.0% | 0.0% | - | - |
| E1177589 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | - | - | - |
| E1287791 | 6 | 33.3% | 50.0% | 16.7% | 0.0% | - | - | - |
| E1290248 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1449360 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | - | - | - |
| E1496959 | 7 | 85.7% | 0.0% | 14.3% | 0.0% | 0.0% | - | - |
| E1497157 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1588473 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1592666 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1619343 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1636307 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1653043 | 8 | 75.0% | 12.5% | 12.5% | 0.0% | - | - | - |
| E1672915 | 6 | 66.7% | 16.7% | 16.7% | 0.0% | 0.0% | - | - |
| E1674875 | 8 | 50.0% | 37.5% | 12.5% | 0.0% | 0.0% | - | - |
| E1682105 | 4 | 50.0% | 25.0% | 25.0% | 0.0% | 0.0% | - | - |
| E1705630 | 7 | 85.7% | 0.0% | 14.3% | 0.0% | - | - | - |
| E1739131 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1781359 | 9 | 88.9% | 0.0% | 11.1% | 0.0% | 33.3% | - | - |
| E1790816 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823356 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823727 | 5 | 40.0% | 40.0% | 20.0% | 0.0% | 0.0% | - | - |
| E1824650 | 9 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1829278 | 6 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1837964 | 11 | 100.0% | 0.0% | 0.0% | 0.0% | 10.0% | - | - |
| E1853162 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1856821 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2230341 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E2309912 | 4 | 0.0% | 75.0% | 25.0% | 0.0% | - | - | - |
| E2418055 | 8 | 87.5% | 12.5% | 0.0% | 0.0% | 50.0% | - | - |
| E2419768 | 6 | 50.0% | 16.7% | 33.3% | 0.0% | 0.0% | - | - |
| E2558122 | 7 | 85.7% | 14.3% | 0.0% | 0.0% | 0.0% | - | - |
| E2609672 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2714303 | 6 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2725629 | 4 | 50.0% | 25.0% | 25.0% | 0.0% | 0.0% | - | - |
| E2757707 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2814579 | 7 | 85.7% | 0.0% | 14.3% | 0.0% | 66.7% | - | - |
| E2860378 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E2879373 | 7 | 57.1% | 14.3% | 28.6% | 0.0% | 100.0% | - | - |
| E3001552 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3027283 | 5 | 60.0% | 0.0% | 40.0% | 0.0% | 100.0% | - | - |
| E3033795 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3035113 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3053511 | 6 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3067309 | 7 | 100.0% | 0.0% | 0.0% | 0.0% | 25.0% | - | - |
| E3110594 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E3111371 | 5 | 40.0% | 60.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3112232 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3115505 | 5 | 80.0% | 0.0% | 20.0% | 0.0% | 0.0% | - | - |
| E3124669 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3130379 | 9 | 77.8% | 22.2% | 0.0% | 0.0% | 50.0% | - | - |
| E3148216 | 4 | 25.0% | 75.0% | 0.0% | 0.0% | - | - | - |
| E3150018 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E3152779 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E3170528 | 4 | 75.0% | 0.0% | 25.0% | 0.0% | 0.0% | - | - |
| E3178242 | 6 | 66.7% | 16.7% | 16.7% | 0.0% | - | - | - |
| E3205786 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3220742 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3223097 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3233620 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3237226 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
