# Evaluation of AI clinical suggestions against patient records

- Input: `eicu_triples_deepseek-v4.1-flash.json`; 100 cases, 3.0 AI suggestions per case on average.
- Models: atomizer `deepseek-v4-pro:0813:cloud`; judge panel `deepseek-v4-pro:0813:cloud` (majority vote; reasoning mode: none); 228 new model calls, 59 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 17.8% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 530 |
| supported / not_supported / not_addressed / unverifiable | 400 / 115 / 15 / 0 |
| Fact accuracy = supported / (supported + not_supported) | 77.7% |
| Cases with at least one not_supported fact | 61 / 100 |
| Omitted findings: abnormalities the clinicians treated that no AI fact mentions | 0 / 0 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 344 | 77.1% | {'supported': 262, 'not_supported': 78, 'not_addressed': 4} |
| presupposed by an action | 169 | 77.2% | {'supported': 122, 'not_addressed': 11, 'not_supported': 36} |
| clinical judgment | 17 | 94.1% | {'supported': 16, 'not_supported': 1} |
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
| E184757 | Monitor blood pressure closely given intermittent hypertension and PRN labetalol order. | A PRN labetalol order is active. | stated outright | The records contain an active PRN order for labetalol (R49), but the statement claims a PRN labetalol order is active. The order is for IV labetalol, not oral, and the statement does not specify route; however, the order is active at decision time, so it supports the claim of an active PRN labetalol order. |
| E297175 | Continue non-invasive ventilation with FiO2 40% and PEEP 5 cmH2O, monitoring oxygenation and respiratory status. | FiO2 is 40%. | stated outright | The statement claims FiO2 is 40%, but the most recent FiO2 measurement before the decision time is 45% (R40), and earlier values include 40% (R11, R17, R35). The latest value contradicts the stated 40%. |
| E322290 | Monitor blood pressure and heart rate closely given recent systolic blood pressure of 91 mmHg and tachycardia. | Tachycardia is present. | stated outright | 0 of 16 heart rate values in the 24 h before the decision were high. |
| E375854 | Assess and manage ongoing hypotension with persistent tachycardia in the setting of GI bleeding and dropping hemoglobin. | Hypotension is present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E375854 | Assess and manage ongoing hypotension with persistent tachycardia in the setting of GI bleeding and dropping hemoglobin. | Tachycardia is present. | stated outright | Median heart rate over the 6 h before the decision: 88.5 bpm (6 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E375854 | Continue monitoring oxygen saturation and administer supplemental oxygen as needed given O2 saturation 94% on 3 L/min nasal cannula. | The patient is on 3 L/min nasal cannula. | stated outright | The records document nasal cannula oxygen therapy at 30-40%, but do not specify a flow rate of 3 L/min. |
| E405746 | Monitor oxygen saturation and respiratory status given intermittent desaturation to 91% and 93% in the prior 24 hours. | Oxygen saturation was 91% in the prior 24 hours. | stated outright | The records show O2 saturation values of 93% and 91% on 2100-01-01, which are below the normal range and indicate desaturation, but the statement's claim of 'intermittent desaturation' is not fully supported as the values recovered to 96% by 13:00 and remained above 95% thereafter. |
| E405746 | Monitor oxygen saturation and respiratory status given intermittent desaturation to 91% and 93% in the prior 24 hours. | Oxygen saturation was 93% in the prior 24 hours. | stated outright | The records show O2 saturation values of 93% and 91% on 2100-01-01, which are below the normal range and indicate desaturation, but the statement claims 'no desaturation' in the prior 24 hours. |
| E405746 | Monitor oxygen saturation and respiratory status given intermittent desaturation to 91% and 93% in the prior 24 hours. | Desaturation is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no. |
| E454584 | Monitor blood glucose and administer sliding-scale insulin as ordered, given recent glucose variability. | Insulin orders are active. | stated outright | The records show a NovoLOG Flexpen order running at decision time (R14) and treatment documentation of sliding scale insulin administration (R20, R21), but no active insulin order is explicitly recorded. The statement that 'Insulin orders are active' is therefore not fully supported by the supplied records. |
| E454584 | Assess and manage sedation and delirium, considering the patient's fluctuating RASS and CAM-ICU positive status. | RASS is fluctuating. | stated outright | The records contain multiple 'Sedation Scale/Score/Goal Sedation Scale: RASS' entries, but none of them include an actual RASS score value. Therefore, the claim that the patient's RASS is fluctuating cannot be verified or supported by the provided data. |
| E454584 | Assess and manage sedation and delirium, considering the patient's fluctuating RASS and CAM-ICU positive status. | CAM-ICU is positive. | stated outright | The records show multiple CAM-ICU assessments, but none of them record a positive result; they only list the scale name without a score. The sedation scores are RASS values, not CAM-ICU results. |
| E467819 | Continue nicardipine infusion for blood pressure control in intracranial hemorrhage. | Nicardipine infusion is currently being given. | presupposed by an action | The most recent Nicardipine administration record (R50) ended at 00:00 on 2100-01-02, which is 21 hours before the decision time of 21:00 on 2100-01-02. There is no administration record within the 24 hours before the decision time, so the statement that the patient is currently receiving Nicardipine is not supported. |
| E490454 | Continue non-invasive ventilation with BiPAP mask given recurrent hypoxemia (SpO2 91% at 23:20) after weaning to nasal cannula. | Recurrent hypoxemia is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E490454 | Assess for possible causes of worsening hypoxemia, including bronchospasm, fluid overload, or mucus plugging, and consider need for bronchodilator therapy or diuresis. | Worsening hypoxemia is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E521456 | Monitor blood glucose closely and continue insulin sliding scale to maintain glycemic control, given recent hypoglycemia and hyperglycemia. | Insulin sliding scale is currently being given. | presupposed by an action | The records show a treatment documentation for sliding scale insulin administration at 20:30 on 2100-01-01, but no administration record within 24 hours before the decision time of 2100-01-02 21:00. The most recent glucose values are not hypoglycemic, so the statement about recent hypoglycemia is not supported. |
| E521456 | Monitor blood glucose closely and continue insulin sliding scale to maintain glycemic control, given recent hypoglycemia and hyperglycemia. | Recent hypoglycemia is present. | stated outright | 0 of 1 glucose values in the 24 h before the decision were low. |
| E521456 | Monitor blood glucose closely and continue insulin sliding scale to maintain glycemic control, given recent hypoglycemia and hyperglycemia. | Recent hyperglycemia is present. | stated outright | 0 of 1 glucose values in the 24 h before the decision were high. |
| E664474 | Continue non-invasive ventilation with pressure support 15 cmH2O and PEEP 5 cmH2O, as documented at 15:07. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records document non-invasive ventilation at 10:32, but there is no record of pressure support 15 cmH2O or PEEP 5 cmH2O, nor any ventilator settings at the decision time. |
| E664474 | Continue non-invasive ventilation with pressure support 15 cmH2O and PEEP 5 cmH2O, as documented at 15:07. | Pressure support is 15 cmH2O. | stated outright | The statement claims pressure support is 15 cmH2O, but the only record of pressure support (R36) is from 2100-01-01 at 15:07, which is over 30 hours before the decision time of 2100-01-02 at 21:00. No recent pressure support value is documented to support the present-tense claim. |
| E664474 | Monitor oxygen saturation and respiratory rate closely given persistent tachypnea and oxygen requirement. | Tachypnea is persistent. | stated outright | Median respiratory rate over the 6 h before the decision: 19 insp/min (5 readings), normal by the rule 'tachypnea RR > 20; bradypnea RR < 12'. |
| E664474 | Monitor oxygen saturation and respiratory rate closely given persistent tachypnea and oxygen requirement. | Oxygen requirement is present. | stated outright | The records show oxygen saturation values ranging from 88% to 100% and oxygen flow rates from 2 to 35 L/min, but they do not contain any statement about the patient's oxygen requirement or a diagnosis of hypoxemia. The statement is not supported by the recorded measurements alone. |
| E733082 | Monitor vital signs and oxygen saturation closely given persistent tachycardia and borderline oxygen saturation. | Oxygen saturation is borderline. | stated outright | The most recent oxygen saturation values before the decision time are 94% (R47, R49), which is below the normal range and not borderline. The statement 'borderline oxygen saturation' is not supported by the recorded values. |
| E876429 | Continue mechanical ventilation with current settings (FiO2 40%, PEEP 5 cmH2O, PSV 10 cmH2O) and monitor oxygenation and respiratory status. | The patient is currently on mechanical ventilation. | stated outright | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 8.4 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E876429 | Continue mechanical ventilation with current settings (FiO2 40%, PEEP 5 cmH2O, PSV 10 cmH2O) and monitor oxygenation and respiratory status. | PSV is 10 cmH2O. | stated outright | The records show PSV Level of 10 cmH2O at multiple times, but the statement claims PSV is 10 cmH2O. The most recent PSV Level before the decision time is 10 cmH2O, which supports the statement. However, the statement also mentions 'Continue mechanical ventilation' and 'PSV is 10 cmH2O', but the records do not show a 'Running at decision time' record for PSV, and the most recent PSV Level is at 11:30, which is before the decision time of 21:00. The statement is not supported because there is no administration record of PSV in the 24 hours before the decision time, and the records do not show a 'Running at decision time' record for PSV. |
| E876429 | Continue vasopressor and sedative infusions (epinephrine, norepinephrine, phenylephrine, propofol) and monitor hemodynamics and sedation. | Phenylephrine is currently being given. | stated outright | Phenylephrine appears in the records, but the most recent administration (R44) ended at 13:00 on 2100-01-02, which is more than 24 hours before the decision time of 2100-01-02 19:53. There is no record of phenylephrine being given at or near the decision time. |
| E899746 | Continue supplemental oxygen and monitor oxygen saturation, as oxygen flow has escalated to 8-10 L/min with saturations 92-94%. | Oxygen flow has escalated to 8-10 L/min. | stated outright | The statement claims oxygen flow has escalated to 8-10 L/min with saturations 92-94%. Records show flow reached 10 L/min at 22:40 (R46) but then decreased to 8 L/min at 00:00 (R49), and saturations were 92-94% at 22:40-23:00 (R47, R48) but 93% at 00:00 (R50). The flow is not currently 8-10 L/min as it has decreased, and the saturation range is not consistently 92-94%. |
| E942382 | Continue diltiazem infusion for rate control of atrial arrhythmia. | Diltiazem infusion is currently being given. | presupposed by an action | The only diltiazem administration record is an infusion that started and ended at 17:04 on 2100-01-01, which is more than 24 hours before the decision time of 2100-01-02 15:23. There is no record of a diltiazem infusion running at the decision time. |
| E942382 | Monitor heart rate and blood pressure closely given bradycardia and intermittent hypotension. | Intermittent hypotension is present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E962227 | Continue monitoring blood pressure closely given persistent hypertension (e.g., 173/85 mmHg at 20:00) and active antihypertensive orders. | Antihypertensive orders are active. | stated outright | The records show a treatment documentation for hypertension with IV hydralazine (R43), but no administration record of hydralazine in the 24 hours before the decision time. The active order for hydrALAZINE IV q6hr PRN (R12) indicates it was ordered, not given. |
| E1056063 | Continue continuous pulse oximetry and vital sign monitoring in the ICU, with attention to intermittent oxygen desaturation and tachycardia. | Intermittent oxygen desaturation is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no. |
| E1056063 | Reassess neurologic status and GCS, and continue psychiatric consultation follow-up for substance overdose management. | Psychiatric consultation is currently ongoing. | presupposed by an action | The records document a psychiatry consultation at 10:33, but there is no evidence that the consultation is currently ongoing at the decision time. |
| E1057910 | Continue mechanical ventilation with FiO2 0.4 and monitor oxygenation, as the patient remains intubated with GCS 3 and RASS -4. | FiO2 is 0.4. | stated outright | The most recent FiO2 record before the decision time is R50, which shows 0.4, not 0.5 as stated. Earlier records show 0.5, but the latest value contradicts the statement. |
| E1057910 | Continue mechanical ventilation with FiO2 0.4 and monitor oxygenation, as the patient remains intubated with GCS 3 and RASS -4. | GCS is 3. | stated outright | The statement claims the patient is intubated, but the records contain no mention of intubation, mechanical ventilation, or an endotracheal tube. The GCS and RASS scores do not directly show intubation. |
| E1057910 | Continue mechanical ventilation with FiO2 0.4 and monitor oxygenation, as the patient remains intubated with GCS 3 and RASS -4. | RASS is -4. | stated outright | The records contain multiple 'Sedation Scale/Score/Goal Sedation Scale: RASS' entries, but none of them include a numeric score. Therefore, the specific claim of a RASS score of -4 is not supported by the available data. |
| E1057910 | Monitor blood pressure and titrate vasopressor support as needed, given recent hypotension and current norepinephrine use. | Norepinephrine is currently being given. | stated outright | The only norepinephrine administration record (R1) ended at 15:32 on 2100-01-01, more than 24 hours before the decision time of 2100-01-02 05:25. R12 documents treatment with norepinephrine but does not show ongoing administration at the decision time. |
| E1064283 | Continue scheduled prednisone and pyridostigmine therapy for myasthenia gravis. | Pyridostigmine is currently being given. | presupposed by an action | The records mention pyridostigmine only as a documented treatment (R39), but there is no administration record showing it was given in the 24 hours before the decision time. |
| E1064283 | Assess for need to intensify antihypertensive therapy given persistent systolic blood pressure >190 mmHg. | Systolic blood pressure is persistently greater than 190 mmHg. | stated outright | No recorded systolic BP matches the stated 190; values in the 24 h before the decision ranged 121 to 217 mmHg (latest 194). |
| E1068212 | Continue monitoring heart rate and blood pressure, given persistent tachycardia (HR 112-130 bpm) and low diastolic pressures. | Diastolic blood pressure is low. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1071450 | Continue monitoring hemodynamic status, including pulmonary artery pressures and cardiac output, given recent elevated PA mean and heart rate. | PA mean is elevated. | stated outright | The most recent PA Mean before the decision time is 25 mmHg (R50), which is not elevated. Earlier values were higher, but the latest reading does not support the statement that the PA mean is currently elevated. |
| E1090039 | Monitor hemodynamic status and response to vasoactive infusions (norepinephrine, dopamine) given recent hypotension. | Hypotension was recently present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1090889 | Continue mechanical ventilation with current settings (FiO2 35%, PEEP 5 cmH2O, tidal volume 450 mL, set rate 16/min) and monitor oxygenation and respiratory status. | FiO2 is 35%. | stated outright | The records show an inspired O2 fraction of 35% and a set respiratory rate of 16, but they do not mention PEEP, tidal volume, or pressure support. The statement claims specific ventilator settings that are not fully documented. |
| E1117947 | Monitor blood pressure and heart rate closely due to hypotension and tachycardia. | Hypotension is present. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no. |
| E1117947 | Monitor blood pressure and heart rate closely due to hypotension and tachycardia. | Tachycardia is present. | stated outright | Median heart rate over the 6 h before the decision: 81 bpm (6 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E1171473 | Continue mechanical ventilation with current settings, monitoring oxygenation and ventilation. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('Tidal Volume (set): 500 mL') was 6.8 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1173453 | Assess for infection and continue antibiotic therapy given leukocytosis (WBC 21.14) and recent vancomycin. | Vancomycin was recently given. | presupposed by an action | The records only document vancomycin as a treatment at 13:12 on 2100-01-01, which is over 24 hours before the decision time of 2100-01-02 13:06. There is no administration record of vancomycin within the 24 hours prior to the decision time. |
| E1287791 | Continue mannitol infusion for elevated intracranial pressure management in the setting of ICH/cerebral infarct. | Mannitol infusion is currently being given. | presupposed by an action | The records mention mannitol as a continuous infusion in a treatment documentation note (R16), but there is no administration record showing mannitol was actually given or running at the decision time. Therefore, the statement that mannitol is currently being given is not supported. |
| E1287791 | Continue mannitol infusion for elevated intracranial pressure management in the setting of ICH/cerebral infarct. | Intracranial pressure is elevated. | clinical judgment | The statement claims intracranial pressure is elevated, but the records contain only non-invasive blood pressure measurements and no intracranial pressure values. The highest systolic blood pressure (185 mmHg at R19) does not directly demonstrate elevated intracranial pressure. |
| E1287791 | Monitor blood pressure closely given recent systolic readings ranging from 107 to 185 mmHg and mean arterial pressure as low as 71 mmHg. | Recent systolic blood pressure readings range from 107 to 185 mmHg. | stated outright | The statement claims systolic blood pressure ranged from 107 to 185 mmHg, but the records show a systolic of 185 mmHg at 02:15 (R20) and 107 mmHg at 17:00 (R48), with later readings of 114 and 113 mmHg, so the range is not fully supported. |
| E1287791 | Monitor blood pressure closely given recent systolic readings ranging from 107 to 185 mmHg and mean arterial pressure as low as 71 mmHg. | Mean arterial pressure is as low as 71 mmHg. | stated outright | 0 of 24 mean arterial pressure values in the 24 h before the decision were low. |
| E1287791 | Assess and manage fever with temperature 100.8 F, including evaluation for infection. | Temperature is 100.8 F. | stated outright | Median temperature over the 6 h before the decision: 100.4 F (2 readings), normal by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. |
| E1449360 | Monitor blood pressure closely, given persistent diastolic hypertension (diastolic 86-97 mmHg) over the past 24 hours. | Persistent diastolic hypertension is present. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E1588473 | Continue supplemental oxygen via nasal cannula and monitor oxygen saturation, given recurrent desaturations to 88-91% on room air. | Supplemental oxygen via nasal cannula is currently being given. | presupposed by an action | The most recent record before the decision time (R50) shows the patient is on room air, not nasal cannula. The statement claims the patient is currently receiving supplemental oxygen via nasal cannula, which is contradicted by the latest device record. |
| E1588473 | Assess and manage pain, as pain level was documented at 6/10 earlier in the ICU stay. | Pain level was documented at 6/10 earlier in the ICU stay. | stated outright | The records show a pain level of 0 at 17:00 on 2100-01-01 and a pain level of 6 at 02:00 on 2100-01-02. The statement claims a pain level of 6/10 was documented 'earlier in the ICU stay', but the most recent pain documentation before the decision time is 0/10, and the 6/10 occurred after the decision time. |
| E1619343 | Continue insulin infusion and monitor glucose closely as glucose has risen to 218 mg/dL. | Insulin infusion is currently being given. | presupposed by an action | The records document a continuous insulin infusion treatment at 06:48, but there is no administration record of insulin within the 24 hours before the decision time (2100-01-02). The most recent glucose value (R48) is 218 mg/dL, which does not support the claim that glucose has risen to 218 mg/dL as it is lower than several earlier values. |
| E1636307 | Continue mechanical ventilation with current settings (FiO2 30%, PEEP 5 cmH2O, set RR 12) and monitor respiratory status. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 9.7 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1636307 | Continue mechanical ventilation with current settings (FiO2 30%, PEEP 5 cmH2O, set RR 12) and monitor respiratory status. | FiO2 is 30%. | stated outright | The most recent Inspired O2 Fraction records show 30%, not 50%. The statement claims FiO2 is 50%, which is contradicted by the latest measurements. |
| E1653043 | Continue monitoring anticoagulation with serial PTT/INR given supratherapeutic PTT levels (159.3 s, 97.8 s, 95.4 s) on heparin and warfarin therapy. | Heparin therapy is currently being given. | presupposed by an action | The records document 'conventional heparin therapy / intravenous' (R32), but there is no administration record of heparin within 24 hours before the decision time. The documentation alone does not confirm that heparin is currently being given. |
| E1653043 | Continue monitoring anticoagulation with serial PTT/INR given supratherapeutic PTT levels (159.3 s, 97.8 s, 95.4 s) on heparin and warfarin therapy. | Warfarin therapy is currently being given. | presupposed by an action | The only warfarin administration record (R8) is dated 2100-01-01 22:00, which is over 24 hours before the decision time of 2100-01-02 21:00. There is no record of warfarin being administered within the 24 hours prior to the decision time. |
| E1672915 | Assess and manage pain and agitation with as-needed opioid and sedative therapy per existing orders. | Sedative orders are active. | presupposed by an action | The records show multiple administrations of lorazepam (a sedative), but no active sedative order is present at the decision time. The only active medication orders are for labetalol, acetaminophen, insulin, aspirin, piperacillin-tazobactam, enoxaparin, famotidine, heparin, and morphine, none of which are sedatives. |
| E1674875 | Continue monitoring oxygenation and respiratory status given persistent hypoxemia and hypercapnia on supplemental oxygen. | Hypoxemia is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E1674875 | Assess and manage hypotension with mean arterial pressure in the 40s-70s mmHg range. | Mean arterial pressure is in the 40s-70s mmHg range. | stated outright | Median mean arterial pressure over the 6 h before the decision: 65 mmHg (6 readings), normal by the rule 'hypotension MAP < 65'. |
| E1674875 | Continue scheduled bronchodilator and corticosteroid therapy for ARDS management. | Bronchodilator therapy is currently scheduled. | presupposed by an action | The records show PRN orders for albuterol (R4, R9) and an administration of ipratropium-albuterol that ended at 05:29 (R19), but no scheduled bronchodilator order or administration is active at the decision time. The only running bronchodilator is ipratropium (R28), which is not scheduled as a combined therapy. |
| E1674875 | Assess and manage hypotension with mean arterial pressure in the 40s-70s mmHg range. | Hypotension is present. | presupposed by an action | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1682105 | Assess and manage hypotension with intravenous fluids as needed. | Hypotension is present. | presupposed by an action | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1705630 | Monitor blood pressure closely given persistent hypertension (systolic 150-170s, diastolic 90-106) and PRN labetalol ordered. | PRN labetalol is ordered. | stated outright | The records show labetalol was given once at 17:20 and 20:05, and an order for PRN labetalol every 6 hours is active, but there is no administration record within 24 hours before the decision time (2100-01-02) to support the statement that the patient is currently receiving labetalol. |
| E1705630 | Continue supplemental oxygen at 2 L/min to maintain oxygen saturation above 92%. | Supplemental oxygen is currently being given. | presupposed by an action | The most recent oxygen saturation reading before the decision time is 94% (R50), which is above 92%, so the statement that oxygen is being given to maintain saturation above 92% is not supported by the records. |
| E1739131 | Continue monitoring vital signs and oxygen saturation on room air, given stable GCS and hemodynamics. | Hemodynamics are stable. | stated outright | 'cardiovascular status normal' holds when any component is normal. heart rate: yes; systolic BP: no; mean arterial pressure: yes. |
| E1823727 | Continue hemodialysis as documented for renal failure. | Hemodialysis is currently being given. | presupposed by an action | The records document hemodialysis as a treatment at 15:00, 21:58, and 08:42, but none of these are administration records showing it was actively being given at the decision time of 14:58. The most recent documentation (R47) is from 08:42, over six hours earlier, so the present-tense statement is not supported. |
| E1823727 | Monitor potassium level given hyperkalemia. | Hyperkalemia is present. | stated outright | Latest potassium 5.1 mmol/L at 2100-01-02 10:00:00 (reference 3.3 to 5.1) is normal, not consistent with 'high'. |
| E1824650 | Monitor blood glucose and administer sliding-scale insulin as ordered. | Sliding-scale insulin orders are active. | presupposed by an action | The statement claims the patient is currently on a ventilator, but the most recent O2 Delivery Device records show nasal cannula at 04:00 and 05:54, and 'None (RA)' at 15:35, with no endotracheal tube or ventilator setting charted after the 18:00 endotracheal tube entry. |
| E1824650 | Assess readiness for ICU discharge given stable vitals, GCS 15, and room air. | Vitals are stable. | stated outright | 'vital signs normal' holds when any component is normal. heart rate: yes; systolic BP: yes; mean arterial pressure: yes; respiratory rate: no; SpO2: yes; temperature: yes. |
| E1824650 | Assess readiness for ICU discharge given stable vitals, GCS 15, and room air. | The patient is on room air. | stated outright | The records show the patient was on mechanical ventilation (R23) and later on oxygen therapy with ventilator weaning (R33, R34), with a PEEP setting of 0 cmH2O at 05:55 (R40). There is no record of the patient being on room air at the decision time. |
| E1829278 | Continue nicardipine infusion for blood pressure control, as it was running at 7.5 mg/hour at the decision point. | Nicardipine infusion is currently running. | presupposed by an action | The nicardipine infusion ended at 08:24 on 2100-01-02, before the decision time of 21:00, and there is no record of it running at the decision time. |
| E1829278 | Continue nicardipine infusion for blood pressure control, as it was running at 7.5 mg/hour at the decision point. | Nicardipine infusion was running at 7.5 mg/hour. | stated outright | The records show a Nicardipine infusion at 7.5 mg/hour from 03:00 to 08:24 on 2100-01-02, but no administration record within 24 hours before the decision time (2100-01-02 21:00) indicates it was running at the decision time. The infusion ended at 08:24, so the statement that the patient is currently receiving Nicardipine is not supported. |
| E1829278 | Monitor neurological status with Glasgow Coma Scale, which was 9 at 03:00 and improved from 11 earlier. | Glasgow Coma Scale improved from 11 earlier. | stated outright | The records show GCS total of 9 at 08:00 (R8), 11 at 15:27 (R33), and 9 at 03:00 (R43). The statement claims GCS was 9 at 03:00 and improved from 11 earlier, but the 11 occurred before the 9, so the GCS did not improve from 11 to 9; it decreased. |
| E1837964 | Continue BiPAP/CPAP with PEEP 5 cmH2O and FiO2 60% for respiratory support. | FiO2 is 60%. | stated outright | The records show the patient is on a BiPAP mask with FiO2 60%, but there is no record of PEEP 5 cmH2O or a specific CPAP setting. The statement about PEEP is not addressed by the available data. |
| E2309912 | Monitor blood pressure and heart rate closely given persistent hypertension and tachycardia, with PRN antihypertensives available. | Hypertension is persistent. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E2309912 | Monitor blood pressure and heart rate closely given persistent hypertension and tachycardia, with PRN antihypertensives available. | Tachycardia is persistent. | stated outright | Median heart rate over the 6 h before the decision: 83.5 bpm (12 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E2418055 | Continue mechanical ventilation with current settings (FiO2 40%, PEEP 5 cmH2O, set tidal volume 600 mL, set respiratory rate 10/min) and monitor oxygenation and ventilation. | PEEP is 5 cmH2O. | stated outright | The most recent PEEP set record (R44) shows 5 cmH2O, but the most recent set respiratory rate (R50) is 10 insp/min, not 12 as stated. |
| E2419768 | Continue supplemental oxygen therapy with titration to maintain oxygen saturation above 90%, given recurrent desaturations to 77-90% on 12-15 L/min. | Oxygen was given at 12-15 L/min. | stated outright | The statement says the patient is on 12-15 L/min oxygen, but the most recent record before the decision time (R50 at 16:42) shows 10 L/min, which is outside that range. |
| E2558122 | Assess and manage hypoxemia with escalating oxygen support, including consideration of noninvasive ventilation, given SpO2 90–92% on oxymask and prior BiPAP use. | Hypoxemia is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no. |
| E2609672 | Monitor blood glucose with finger-stick checks given recent hypoglycemia and glucose variability. | Recent hypoglycemia is present. | stated outright | 0 of 2 glucose values in the 24 h before the decision were low. |
| E2609672 | Monitor blood glucose with finger-stick checks given recent hypoglycemia and glucose variability. | Glucose variability is present. | stated outright | The most recent glucose value before the decision time is 119 mg/dL (R50), which is within the normal range and does not indicate hypoglycemia. Earlier values were low, but the present-tense statement about current hypoglycemia is contradicted by the latest measurement. |
| E2714303 | Continue levetiracetam and phenytoin anticonvulsant therapy for seizure management. | Levetiracetam is currently being given. | presupposed by an action | The records document levetiracetam as a treatment (R33), but there is no administration record showing it was given in the 24 hours before the decision time. Therefore, the statement that it is 'currently being given' is not supported. |
| E2714303 | Continue levetiracetam and phenytoin anticonvulsant therapy for seizure management. | Phenytoin is currently being given. | presupposed by an action | The records document phenytoin as a seizure therapy treatment, but there is no administration record showing it was given in the 24 hours before the decision time. A treatment documentation alone does not confirm current administration. |
| E2714303 | Assess and manage fever with temperature 101.7°F and tachycardia. | Temperature is 101.7°F. | stated outright | Median temperature over the 6 h before the decision: 99.15 F (2 readings), normal by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. |
| E2814579 | Monitor blood glucose and continue insulin infusion to maintain glycemic control. | Insulin infusion is currently being given. | presupposed by an action | The only insulin administration record is at 13:00 on 2100-01-02, which is more than 24 hours before the decision time of 2100-01-01 22:47. No insulin administration is recorded in the 24 hours before the decision time. |
| E2879373 | Monitor blood pressure closely due to wide pulse pressure and diastolic pressures as low as 30 mmHg. | Pulse pressure is wide. | stated outright | Median heart rate over the 6 h before the decision: 86 bpm (6 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E3035113 | Monitor blood glucose given recent hyperglycemia and hypoglycemia. | Recent hypoglycemia is present. | stated outright | 0 of 1 glucose values in the 24 h before the decision were low. |
| E3035113 | Assess and manage hypokalemia (potassium 3.4 mmol/L). | Hypokalemia is present. | stated outright | Latest potassium 3.4 mmol/L at 2100-01-02 09:39:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E3053511 | Continue monitoring respiratory status and oxygenation given persistent tachypnea and intermittent hypoxemia. | Intermittent hypoxemia is present. | stated outright | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E3053511 | Continue antibiotic therapy with vancomycin and piperacillin/tazobactam as documented, with monitoring of vancomycin trough. | Vancomycin is currently being given. | presupposed by an action | The records mention vancomycin as a documented treatment and a trough level, but there is no administration record of vancomycin in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E3053511 | Continue antibiotic therapy with vancomycin and piperacillin/tazobactam as documented, with monitoring of vancomycin trough. | Piperacillin/tazobactam is currently being given. | presupposed by an action | The records document piperacillin/tazobactam as a treatment, but there is no administration record showing it was given in the 24 hours before the decision time. The statement that it is 'currently being given' is therefore not supported. |
| E3067309 | Continue mechanical ventilation with current settings (FiO2 50%, PEEP 5 cmH2O, set tidal volume 450 mL, set respiratory rate 16/min) and monitor oxygenation and ventilation. | FiO2 is 50%. | stated outright | The most recent FiO2 measurement before the decision time is 50% (R46), not 60% as stated. The statement is therefore not supported by the records. |
| E3111371 | Monitor vital signs and CIWA/withdrawal scores closely given fluctuating hypertension, tachycardia, tachypnea, and sedation scores. | Hypertension is fluctuating. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E3111371 | Monitor vital signs and CIWA/withdrawal scores closely given fluctuating hypertension, tachycardia, tachypnea, and sedation scores. | Tachycardia is fluctuating. | stated outright | Median heart rate over the 6 h before the decision: 96 bpm (5 readings), normal by the rule 'tachycardia HR > 100; bradycardia HR < 60'. |
| E3111371 | Monitor vital signs and CIWA/withdrawal scores closely given fluctuating hypertension, tachycardia, tachypnea, and sedation scores. | Tachypnea is fluctuating. | stated outright | Median respiratory rate over the 6 h before the decision: 19 insp/min (5 readings), normal by the rule 'tachypnea RR > 20; bradypnea RR < 12'. |
| E3111371 | Monitor vital signs and CIWA/withdrawal scores closely given fluctuating hypertension, tachycardia, tachypnea, and sedation scores. | Sedation scores are fluctuating. | stated outright | The records show multiple diazepam administrations (intravenous and oral) running at the decision time, but the statement claims the patient is not receiving diazepam. These administration records directly contradict the statement. |
| E3124669 | Monitor serum potassium and replete as needed, given persistent hypokalemia (3.3 mmol/L at 20:00 on 2100-01-01). | Hypokalemia is present. | stated outright | Latest potassium 3.3 mmol/L at 2100-01-01 20:00:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E3130379 | Continue BiPAP support with current settings (FiO2 30%, PEEP 8 cmH2O) and monitor oxygenation and ventilation, given persistent hypercapnia (pCO2 61 mmHg) and borderline oxygen saturation. | FiO2 is 30%. | stated outright | The most recent O2 Delivery Device record (R52) shows a nasal cannula, not BiPAP, and no later BiPAP setting is charted. The statement claims current BiPAP support, which is contradicted by the latest device record. |
| E3130379 | Continue BiPAP support with current settings (FiO2 30%, PEEP 8 cmH2O) and monitor oxygenation and ventilation, given persistent hypercapnia (pCO2 61 mmHg) and borderline oxygen saturation. | PEEP is 8 cmH2O. | stated outright | The most recent record before the decision time shows the patient was switched to a nasal cannula at 13:00, which contradicts the statement that the patient is currently on BiPAP with PEEP 8 cmH2O. |
| E3130379 | Continue BiPAP support with current settings (FiO2 30%, PEEP 8 cmH2O) and monitor oxygenation and ventilation, given persistent hypercapnia (pCO2 61 mmHg) and borderline oxygen saturation. | Oxygen saturation is borderline. | stated outright | The statement claims the patient is on BiPAP with PEEP 8 and FiO2 30%, but the most recent device record (R50) shows a nasal cannula, not a ventilator, and no PEEP is charted. |
| E3130379 | Obtain repeat arterial blood gas to reassess hypercapnia and acid-base status. | Acid-base status is abnormal. | presupposed by an action | The most recent arterial blood gas shows a pH of 7.35, which is within the normal range (7.35-7.45), and the base excess is 8, indicating a mild metabolic alkalosis, not an abnormal acid-base status. The statement that the acid-base status is abnormal is not supported by these values. |
| E3148216 | Monitor oxygen saturation and respiratory status closely given declining SpO2 and increased oxygen requirement. | SpO2 is declining. | stated outright | 0 of 23 SpO2 values in the 24 h before the decision were low. |
| E3148216 | Monitor oxygen saturation and respiratory status closely given declining SpO2 and increased oxygen requirement. | Oxygen requirement is increased. | stated outright | The records show oxygen therapy at 2-4 L/min, which is less than 40% FiO2, but the statement claims oxygen therapy is at 40% or more. The documented oxygen flow rates do not support the stated FiO2 level. |
| E3148216 | Assess for possible infection or other cause of fever and respiratory changes. | Fever is present. | presupposed by an action | Median temperature over the 6 h before the decision: 99.9 F (1 readings), normal by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. |
| E3178242 | Assess and manage worsening hypoxemia and tachypnea on 2 L/min nasal cannula, with SpO2 93% and pO2 85 mmHg, considering escalation of respiratory support. | Hypoxemia is present. | presupposed by an action | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: no. |
| E3220742 | Continue levetiracetam for seizure prophylaxis/therapy as ordered. | Levetiracetam is currently being given. | presupposed by an action | The records show a levetiracetam administration that ended at 11:47 on 2100-01-01, and treatment documentation for levetiracetam, but no administration record within 24 hours before the decision time of 2100-01-02 02:33. Therefore, the statement that levetiracetam is currently being given is not supported. |
| E3220742 | Monitor blood pressure closely given intermittent hypotension and PRN antihypertensive orders. | PRN antihypertensive orders are active. | stated outright | The statement claims the patient is hypertensive, but the recorded diastolic blood pressures are mostly below 90 mmHg, with many values in the 50s-70s range, and the most recent value is 60 mmHg. Only a few early readings (e.g., R12-R15) are elevated, so the overall record does not support current hypertension. |
| E3223097 | Monitor serum potassium and treat hyperkalemia as indicated. | Hyperkalemia is present. | presupposed by an action | Latest potassium 4.2 mmol/L at 2100-01-02 08:10:00 (reference 3.3 to 5.1) is normal, not consistent with 'high'. |
| E3223097 | Monitor blood pressure and hemoglobin for ongoing bleeding and hemodynamic instability. | Ongoing bleeding is present. | stated outright | The records document an admission diagnosis of upper GI bleeding and treatments for bleeding (blood product administration), but they do not contain any direct evidence of ongoing bleeding at the decision time. The most recent relevant records show no active bleeding event. |
| E3233620 | Monitor vital signs and oxygen saturation closely given diminished breath sounds and borderline oxygenation. | Oxygenation is borderline. | stated outright | 'oxygenation abnormal' holds when any component is abnormal. SpO2: no. |
| E3237226 | Continue supplemental oxygen therapy via nasal cannula at 3 L/min to maintain oxygen saturation. | Supplemental oxygen therapy via nasal cannula is currently being given. | presupposed by an action | The most recent O2 Flow record before the decision time (2100-01-02) is R33 at 3 L/min, not the stated 2 L/min. The records address the oxygen flow rate but do not support the specific value claimed. |

## 5. Judge panel

287 items went to the judge panel. Agreement: {'1/1': 287} (split = no majority; the conservative label was used and the item needs human review).

## 6. Per-case score sheets

| Case | Facts | supported | not_supported | not_addressed | unverifiable | Treatment agreement | Vital recall | All recall |
|---|---|---|---|---|---|---|---|---|
| E153972 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E172015 | 9 | 88.9% | 11.1% | 0.0% | 0.0% | - | - | - |
| E184757 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 0.0% | - | - |
| E211144 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E284265 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E297175 | 5 | 60.0% | 20.0% | 20.0% | 0.0% | 33.3% | - | - |
| E322290 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E375854 | 8 | 62.5% | 37.5% | 0.0% | 0.0% | - | - | - |
| E383358 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E395323 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E405746 | 7 | 57.1% | 42.9% | 0.0% | 0.0% | - | - | - |
| E454584 | 9 | 66.7% | 33.3% | 0.0% | 0.0% | 33.3% | - | - |
| E467819 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E490454 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 100.0% | - | - |
| E521456 | 6 | 50.0% | 50.0% | 0.0% | 0.0% | 25.0% | - | - |
| E664474 | 7 | 42.9% | 57.1% | 0.0% | 0.0% | 0.0% | - | - |
| E733082 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E756295 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 33.3% | - | - |
| E758325 | 9 | 100.0% | 0.0% | 0.0% | 0.0% | 66.7% | - | - |
| E826669 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E850469 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E876429 | 8 | 62.5% | 37.5% | 0.0% | 0.0% | 0.0% | - | - |
| E899746 | 8 | 87.5% | 12.5% | 0.0% | 0.0% | - | - | - |
| E942382 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E962227 | 7 | 71.4% | 14.3% | 14.3% | 0.0% | 0.0% | - | - |
| E978037 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1056063 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | - | - | - |
| E1057910 | 9 | 33.3% | 44.4% | 22.2% | 0.0% | 0.0% | - | - |
| E1057967 | 7 | 85.7% | 0.0% | 14.3% | 0.0% | - | - | - |
| E1064283 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1065859 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1068212 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1071224 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071450 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1090039 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 100.0% | - | - |
| E1090889 | 8 | 87.5% | 12.5% | 0.0% | 0.0% | 100.0% | - | - |
| E1099398 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1117947 | 4 | 25.0% | 50.0% | 25.0% | 0.0% | 50.0% | - | - |
| E1121034 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 33.3% | - | - |
| E1171473 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1173453 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1177589 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1287791 | 6 | 16.7% | 83.3% | 0.0% | 0.0% | - | - | - |
| E1290248 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1449360 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | - | - | - |
| E1496959 | 7 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1497157 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1588473 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1592666 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1619343 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1636307 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1653043 | 8 | 62.5% | 25.0% | 12.5% | 0.0% | - | - | - |
| E1672915 | 6 | 83.3% | 16.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1674875 | 8 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1682105 | 4 | 50.0% | 25.0% | 25.0% | 0.0% | 0.0% | - | - |
| E1705630 | 7 | 71.4% | 28.6% | 0.0% | 0.0% | - | - | - |
| E1739131 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1781359 | 9 | 100.0% | 0.0% | 0.0% | 0.0% | 33.3% | - | - |
| E1790816 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823356 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823727 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1824650 | 9 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1829278 | 6 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1837964 | 11 | 90.9% | 9.1% | 0.0% | 0.0% | 10.0% | - | - |
| E1853162 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1856821 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2230341 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E2309912 | 4 | 25.0% | 50.0% | 25.0% | 0.0% | - | - | - |
| E2418055 | 8 | 87.5% | 12.5% | 0.0% | 0.0% | 50.0% | - | - |
| E2419768 | 6 | 66.7% | 16.7% | 16.7% | 0.0% | 0.0% | - | - |
| E2558122 | 7 | 85.7% | 14.3% | 0.0% | 0.0% | 0.0% | - | - |
| E2609672 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2714303 | 6 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2725629 | 4 | 75.0% | 0.0% | 25.0% | 0.0% | 0.0% | - | - |
| E2757707 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2814579 | 7 | 71.4% | 14.3% | 14.3% | 0.0% | 66.7% | - | - |
| E2860378 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E2879373 | 7 | 71.4% | 14.3% | 14.3% | 0.0% | 100.0% | - | - |
| E3001552 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3027283 | 5 | 80.0% | 0.0% | 20.0% | 0.0% | 100.0% | - | - |
| E3033795 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3035113 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3053511 | 6 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3067309 | 7 | 85.7% | 14.3% | 0.0% | 0.0% | 25.0% | - | - |
| E3110594 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E3111371 | 5 | 20.0% | 80.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3112232 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3115505 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3124669 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3130379 | 9 | 55.6% | 44.4% | 0.0% | 0.0% | 50.0% | - | - |
| E3148216 | 4 | 25.0% | 75.0% | 0.0% | 0.0% | - | - | - |
| E3150018 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E3152779 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E3170528 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3178242 | 6 | 66.7% | 16.7% | 16.7% | 0.0% | - | - | - |
| E3205786 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3220742 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3223097 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3233620 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3237226 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
