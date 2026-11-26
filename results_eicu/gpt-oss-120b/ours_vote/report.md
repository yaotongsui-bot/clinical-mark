# Evaluation of AI clinical suggestions against patient records

- Input: `eicu_triples_gpt-oss-120b.json`; 100 cases, 3.0 AI suggestions per case on average.
- Models: atomizer `deepseek-v4-pro:0813:cloud`; judge panel `deepseek-v4-pro:0813:cloud`, `minimax-m3.1-flash:cloud`, `glm-5.3:cloud` (majority vote; reasoning mode: none); 648 new model calls, 0 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 21.4% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 262 |
| supported / not_supported / not_addressed / unverifiable | 142 / 75 / 45 / 0 |
| Fact accuracy = supported / (supported + not_supported) | 65.4% |
| Cases with at least one not_supported fact | 54 / 100 |
| Omitted findings: abnormalities the clinicians treated that no AI fact mentions | 0 / 0 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 73 | 85.5% | {'supported': 59, 'not_supported': 10, 'not_addressed': 4} |
| presupposed by an action | 170 | 57.2% | {'supported': 79, 'not_supported': 59, 'not_addressed': 32} |
| clinical judgment | 19 | 40.0% | {'not_supported': 6, 'not_addressed': 9, 'supported': 4} |
| vague | 0 | - | {} |

## 2. How close is the AI to what clinicians did?

Target (same class, or the drug the AI named) and direction (continue / stop / adjust) are decided by code; suggestions the rule file cannot classify go to the judge panel.

| Metric | Value |
|---|---|
| Treatment action atoms | 261 |
| Labels | {'not_done': 162, 'vague_target': 45, 'condition_not_met': 28, 'match': 16, 'unobservable': 10} |
| Agreement (strict) = match / (match + partial_match + not_done) | 9.0% |
| Agreement (lenient) = (match + partial_match) / same | 9.0% |

Monitoring/assessment atoms: 273 (reported separately, not part of agreement): {'not_performed': 80, 'performed': 151, 'unobservable': 42}; performed rate among observable items 65.4%. 49 'goal' atoms with no concrete action are not scored.

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
| E172015 | Continue PRN lorazepam dosing for alcohol withdrawal symptom control. | PRN lorazepam is currently being given. | presupposed by an action | The records show active PRN lorazepam orders (R4, R16, R17) and one administration on 2099-12-31 (R2), but no lorazepam administration in the 24 hours before the decision time. Therefore, the statement that PRN lorazepam is currently being given is not supported. |
| E172015 | Continue PRN lorazepam dosing for alcohol withdrawal symptom control. | Alcohol withdrawal is present. | clinical judgment | The records show a high ethanol level (R1) but no diagnosis of alcohol withdrawal. Repeated assessments explicitly state 'Symptoms of Delirium Present: No' (e.g., R5, R47), which contradicts the presence of alcohol withdrawal. |
| E184757 | Start intravenous labetalol infusion for persistent hypertension (SBP 148‑184 mmHg). | SBP is 148-184 mmHg. | stated outright | The records report MAP values, not systolic blood pressure (SBP), so they do not support an SBP range of 148–184 mmHg. |
| E284265 | Continue intravenous diltiazem infusion at the current rate and monitor blood pressure and heart rate q1h. | Intravenous diltiazem infusion is currently being given. | presupposed by an action | The only administration record for diltiazem is an infusion that ran from 2100-01-01 21:00 to 2100-01-02 05:00, which ended over 13 hours before the decision time of 18:11. No record shows a diltiazem infusion running at or near the decision time. |
| E284265 | Order a transthoracic echocardiogram to evaluate cardiac function and rule out structural contributors to supraventricular tachyarrhythmia. | Supraventricular tachyarrhythmia is present. | presupposed by an action | The records document treatments for 'arrhythmias' and antiarrhythmic medications, but they do not contain a diagnosis of 'supraventricular tachyarrhythmia' or an ECG/rhythm strip showing this specific rhythm. Elevated heart rates (112-127 bpm) are present, but these alone do not confirm the specific diagnosis. |
| E375854 | Continue intravenous meropenem therapy for broad‑spectrum coverage of possible intra‑abdominal infection. | Intravenous meropenem therapy is currently being given. | presupposed by an action | The records document meropenem as a treatment (R32), but there is no administration record of intravenous meropenem in the 24 hours before the decision time. The statement that it is 'currently being given' is therefore not supported. |
| E375854 | Continue intravenous meropenem therapy for broad‑spectrum coverage of possible intra‑abdominal infection. | Possible intra-abdominal infection is present. | clinical judgment | The records show consultations with infectious disease, gastroenterology, and surgery, as well as a bleeding scan, but they do not contain a diagnosis of intra-abdominal infection. The consultations suggest investigation but do not directly state or confirm the presence of an infection. |
| E375854 | Obtain an emergent upper endoscopy to locate and control the source of gastrointestinal bleeding. | Gastrointestinal bleeding is present. | presupposed by an action | The records show a bleeding scan was ordered and stress ulcer prophylaxis with IV pantoprazole was documented, which suggests concern for bleeding, but no record explicitly states gastrointestinal bleeding is present or provides direct evidence of active bleeding. |
| E383358 | Check INR in 12 hours and adjust warfarin (coumadin) dosing to keep INR within therapeutic range (2.0‑3.0). | Warfarin (coumadin) is currently being given. | presupposed by an action | The records document coumadin as a treatment (R6, R33), but there is no medication administration record showing warfarin was given within 24 hours before the decision time, so the statement that it is currently being given is not supported. |
| E395323 | Transfuse packed red blood cells to address hemoglobin of 8 g/dL in the setting of sepsis. | Sepsis is present. | clinical judgment | The records show antibiotic administration (piperacillin/tazobactam, vancomycin) and a fever of 100.3 F, which are suggestive but do not explicitly state a sepsis diagnosis. The statement 'Sepsis is present' is a diagnosis not directly documented in the provided records. |
| E454584 | Check bedside glucose hourly and adjust sliding‑scale insulin infusion to maintain glucose 80‑140 mg/dL. | Insulin infusion is currently being given. | presupposed by an action | The records mention insulin administration via subcutaneous injection (R13, R20, R21), but there is no record of an insulin infusion being administered or running at the decision time. The statement about a current insulin infusion is therefore not supported. |
| E467819 | Continue intravenous nicardipine infusion with titration to maintain mean arterial pressure ≥65 mmHg. | Nicardipine infusion is currently being given. | presupposed by an action | The most recent nicardipine administration record (R50) ended at 00:00 on 2100-01-02, which is more than 1 hour and 43 minutes before the decision time of 01:43. There is no administration record within the 24 hours before the decision time showing the infusion was running at that moment. |
| E490454 | Continue non‑invasive ventilation with BiPAP and titrate FiO₂ to maintain SpO₂ ≥ 92 % while monitoring for respiratory fatigue. | The patient is currently on non-invasive ventilation with BiPAP. | presupposed by an action | The records document non-invasive ventilation via face mask, but do not mention BiPAP. Therefore, the specific claim of BiPAP is not supported. |
| E521456 | Continue volume‑controlled mechanical ventilation with tidal volume 6‑8 mL/kg, FiO₂ 65‑70 % and PEEP 5‑7 cmH₂O. | Tidal volume is 6-8 mL/kg. | stated outright | The records show a set tidal volume of 300 mL with a TV/kg IBW of 4.3871, which is below the stated 6-8 mL/kg range. The documented treatment note (R16) mentions a target of 6-10 ml/kg, but the actual recorded values do not support the specific 6-8 mL/kg claim. |
| E733082 | Administer a 500 mL crystalloid bolus to support borderline mean arterial pressure and improve tissue perfusion. | Mean arterial pressure is borderline. | stated outright | The most recent mean arterial pressures before the decision time are 75, 78, and 82 mmHg, which are within normal range, not borderline low. The statement that MAP is borderline is not supported by the latest recorded values. |
| E876429 | Begin gradual weaning of epinephrine and phenylephrine infusions as mean arterial pressure stabilizes above 65 mmHg with adequate cardiac output. | Phenylephrine infusion is currently being given. | presupposed by an action | The records show phenylephrine infusions that ended at 13:00 on 2100-01-02, but no administration record within 24 hours before the decision time of 19:53. Therefore, the statement that it is currently being given is not supported. |
| E876429 | Assess readiness for spontaneous breathing trial and consider extubation if mental status improves (GCS ≥ 13) and ventilatory parameters remain stable. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 8.4 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E942382 | Continue the IV diltiazem infusion to maintain rate control of atrial arrhythmia. | IV diltiazem infusion is currently being given. | presupposed by an action | The records mention diltiazem as a documented treatment (R17) and show a brief infusion at 17:04 on 2100-01-01 (R21), but there is no administration record within 24 hours before the decision time on 2100-01-02 15:23 to support that it is currently being given. |
| E942382 | Continue the IV diltiazem infusion to maintain rate control of atrial arrhythmia. | Atrial arrhythmia is present. | presupposed by an action | The records document diltiazem as a class IV antiarrhythmic treatment, but they do not explicitly identify or otherwise establish an atrial arrhythmia; heart-rate measurements alone cannot determine the rhythm. |
| E1057910 | Continue norepinephrine infusion and titrate to maintain MAP ≥65 mmHg. | Norepinephrine infusion is currently being given. | presupposed by an action | The norepinephrine infusion record (R1) ended at 15:32 on 2100-01-01, which is more than 24 hours before the decision time of 2100-01-02 03:51. No administration of norepinephrine is recorded within the 24 hours before the decision time. |
| E1064283 | Continue IV nicardipine infusion to maintain systolic blood pressure < 150 mmHg. | IV nicardipine infusion is currently being given. | presupposed by an action | The records mention nicardipine only as a treatment documented for hypertension (R33), but there is no administration record of nicardipine in the 24 hours before the decision time. Therefore, the statement that the patient is currently receiving a nicardipine infusion is not supported. |
| E1071450 | Continue milrinone infusion for inotropic support. | Milrinone infusion is currently being given. | presupposed by an action | The records document milrinone as a treatment for shock (R28), but there is no administration record of milrinone in the 24 hours before the decision time, so the statement that the patient is currently receiving it is not supported. |
| E1171473 | Continue mechanical ventilation with current settings and assess readiness for weaning in the next 4–6 hours. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('Tidal Volume (set): 500 mL') was 6.8 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1173453 | Continue current broad‑spectrum antibiotic regimen and reassess culture results for potential de‑escalation. | Broad-spectrum antibiotics are currently being given. | presupposed by an action | The records show a treatment documentation for vancomycin at 13:12 on 2100-01-01, but no administration record (e.g., MAR Administered) within 24 hours before the decision time of 2100-01-02 21:00. Therefore, the statement that broad-spectrum antibiotics are currently being given is not supported. |
| E1177589 | Continue hourly point‑of‑care glucose monitoring to detect recurrent hypoglycemia. | Hourly point-of-care glucose monitoring is currently being performed. | presupposed by an action | The records show multiple glucose measurements, but none are documented as hourly. The intervals between measurements vary widely (e.g., 19 minutes, 34 minutes, 1 hour 7 minutes, 2 hours 38 minutes), so the claim of hourly monitoring is not supported. |
| E1177589 | Maintain nasal cannula oxygen at 2 L/min and reassess FiO₂ and saturation q2h. | Nasal cannula oxygen is currently being given at 2 L/min. | presupposed by an action | The records show nasal cannula oxygen at 2 L/min was charted from 09:00 to 15:00, but the most recent oxygen-related record at 06:00 on 2100-01-02 shows O2 L/% of 21 (room air) with no nasal cannula device or flow rate, indicating the patient is no longer on 2 L/min nasal cannula at the decision time. |
| E1287791 | Continue the mannitol continuous infusion to manage intracranial pressure. | Mannitol continuous infusion is currently being given. | presupposed by an action | The records document a treatment plan for 'mannitol / continuous infusion' (R17), but there is no administration record showing mannitol was actually given or running at the decision time. An order or treatment documentation alone does not confirm administration. |
| E1449360 | Order a short‑acting antihypertensive (e.g., labetalol IV) to maintain systolic blood pressure <140 mmHg given persistent elevations. | Systolic blood pressure is persistently elevated. | stated outright | Median systolic BP over the 6 h before the decision: 134 mmHg (7 readings), normal by the rule 'hypotension SBP < 90; hypertension SBP > 140'. |
| E1588473 | Obtain a platelet transfusion given platelet count of 109 ×10³/µL and ongoing hypotension. | Hypotension is ongoing. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1619343 | Continue intravenous regular insulin infusion with hourly glucose checks to target glucose 140-180 mg/dL. | The patient is currently receiving intravenous regular insulin infusion. | presupposed by an action | The records document a continuous insulin infusion (R18), but there is no administration record of insulin in the 24 hours before the decision time. The glucose values are falling, but lab values alone do not prove insulin was given. |
| E1653043 | Continue therapeutic anticoagulation with intravenous heparin and monitor PTT q6h. | The patient is currently receiving intravenous heparin. | presupposed by an action | The records document 'anticoagulant administration / conventional heparin therapy / intravenous' at 07:45, but there is no administration record of intravenous heparin within 24 hours before the decision time. The statement that the patient is currently receiving IV heparin is therefore not supported. |
| E1653043 | Order repeat lower extremity duplex ultrasound to assess for DVT progression. | DVT is present. | presupposed by an action | The records document that non-invasive testing for DVT and a spiral CT were ordered, but there is no record of a lower extremity duplex ultrasound being performed or its results. The statement claims a specific test was done, which is not supported by the available documentation. |
| E1653043 | Maintain current oxygen supplementation at 2 L/min via nasal cannula and reassess SpO₂ q4h. | The patient is currently receiving oxygen supplementation at 2 L/min via nasal cannula. | presupposed by an action | The records show a recent O2 flow setting of 2 L/min, but do not document nasal cannula use or oxygen administration at the decision time. Therefore, they do not fully support that the patient is currently receiving oxygen via nasal cannula. |
| E1672915 | Start norepinephrine infusion to maintain MAP ≥65 mmHg given persistent tachycardia, hypertension, and signs of septic shock. | Septic shock is present. | clinical judgment | The records show multiple temperature readings above 100.4°F (e.g., R1 102.9°F, R2 104.2°F, R17 102°F, R34 102.6°F), but the most recent reading at 19:17 (R48) is 99.5°F, which is below the fever threshold. Therefore, the statement that the patient is currently febrile is not supported by the latest data. |
| E1674875 | Initiate norepinephrine infusion to support mean arterial pressure. | Mean arterial pressure is low. | presupposed by an action | Median mean arterial pressure over the 6 h before the decision: 65 mmHg (6 readings), normal by the rule 'hypotension MAP < 65'. |
| E1674875 | Continue low tidal volume ventilation strategy for ARDS. | The patient is currently on low tidal volume ventilation. | presupposed by an action | The records document CPAP/PEEP therapy (R8), but no ventilator settings or administration records show low tidal volume ventilation. The statement about low tidal volume ventilation is not supported by the available data. |
| E1682105 | Titrate intravenous labetalol or add a short‑acting vasodilator to maintain mean arterial pressure >65 mmHg given fluctuating hypotension and hypertension. | Hypotension is fluctuating. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1682105 | Titrate intravenous labetalol or add a short‑acting vasodilator to maintain mean arterial pressure >65 mmHg given fluctuating hypotension and hypertension. | Hypertension is fluctuating. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E1705630 | Continue intravenous potassium chloride infusion to correct persistent hypokalemia (K⁺ 3.2‑3.3 mmol/L). | Persistent hypokalemia is present. | stated outright | Latest potassium 3.9 mmol/L at 2100-01-02 17:35:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E1705630 | Monitor blood pressure closely and titrate IV labetalol infusion to maintain MAP < 100 mmHg given sustained systolic pressures 150‑170 mmHg. | IV labetalol infusion is currently being given. | presupposed by an action | The records show labetalol was given as one-time intravenous doses at 17:20 and 20:05, but there is no administration record of a continuous labetalol infusion running at the decision time. The active order is for PRN dosing, not a continuous infusion. |
| E1790816 | Continue intravenous heparin infusion per current dosing and monitor activated partial thromboplastin time (aPTT) q6h. | Intravenous heparin infusion is currently being given. | presupposed by an action | The records show a nitroglycerin infusion was started at 20:53 on 2100-01-01 and ran until 15:12 on 2100-01-02, but the decision time is 21:00 on 2100-01-02, after the infusion ended. No administration of nitroglycerin is documented in the 24 hours before the decision time. |
| E1823356 | Continue intravenous insulin infusion at the current rate and monitor bedside glucose every hour. | Intravenous insulin infusion is currently being given. | presupposed by an action | The records show an insulin infusion that ended at 20:53 (R9) and a scheduled subcutaneous insulin lispro order running at decision time (R47), but no intravenous insulin administration in the 24 hours before the decision time. Therefore, the statement that the patient is currently receiving an intravenous insulin infusion is not supported. |
| E1824650 | Continue ventilator weaning and transition to spontaneous breathing trials. | The patient is currently on mechanical ventilation. | presupposed by an action | The latest record before the decision (2100-01-02 15:35:00) reads 'O2 Delivery Device(s): None (charted: RA)'. |
| E1829278 | Obtain a repeat serum lactate level to assess ongoing sepsis severity. | Sepsis is present. | presupposed by an action | The most recent glucose finger stick before the decision time is 352 mg/dL (R36), which is not borderline but markedly elevated, so the statement 'borderline' is not supported. |
| E1829278 | Continue nicardipine infusion with titration to maintain mean arterial pressure between 65-75 mmHg. | Nicardipine infusion is currently being given. | presupposed by an action | The records show a Nicardipine infusion that ended at 08:24 on 2100-01-02, but no administration of Nicardipine is documented within the 24 hours before the decision time of 2100-01-02 21:00. Therefore, the statement that the patient is currently receiving Nicardipine is not supported. |
| E1837964 | Continue intravenous diuretic therapy and monitor daily weight and electrolytes. | Intravenous diuretic therapy is currently being given. | presupposed by an action | The only IV furosemide administration was on 2100-01-01 at 14:15, more than 24 hours before the decision time. At the decision time, the recorded ongoing diuretic therapy is oral furosemide, not intravenous. |
| E1853162 | Continue scheduled nebulized ipratropium‑albuterol (3 mL q4h PRN) to maintain bronchodilation. | Scheduled nebulized ipratropium-albuterol is currently being given. | presupposed by an action | The records show a one-time nebulized ipratropium-albuterol dose at 09:30 and an active PRN order, but no administration of a scheduled nebulized ipratropium-albuterol within 24 hours before the decision time. |
| E1856821 | Add vasopressin infusion to the current norepinephrine regimen to achieve target MAP ≥65 mmHg. | Norepinephrine is currently being given. | presupposed by an action | The records show norepinephrine infusion ending at 14:11, with no subsequent administration or running record showing it is currently being given at the 18:36 decision time. |
| E1856821 | Obtain repeat blood cultures and a serum lactate level to assess ongoing sepsis and guide antimicrobial therapy. | Sepsis is ongoing. | clinical judgment | The records show norepinephrine infusions at 21.01 mcg/min and 16 mcg/min, but no administration record within 24 hours before the decision time (2100-01-02) indicates the patient is currently receiving it. The most recent infusion ended at 13:16, over 7 hours prior. |
| E2230341 | Continue eptifibatide infusion at the current rate and monitor for bleeding complications. | Eptifibatide infusion is currently being given. | presupposed by an action | The most recent eptifibatide infusion was documented from 04:24 to 09:05 on 2100-01-02 and ended before the decision time of 14:38. No record shows an eptifibatide infusion running at the decision time. |
| E2230341 | Monitor platelet count and hemoglobin every 6 hours while on the glycoprotein IIb/IIIa inhibitor. | The patient is currently on a glycoprotein IIb/IIIa inhibitor. | presupposed by an action | Eptifibatide infusions were administered earlier, but the latest infusion ended at 09:05 on 2100-01-02, before the decision time at 14:38. Thus, the patient was not currently receiving the glycoprotein IIb/IIIa inhibitor. |
| E2309912 | Continue PRN lorazepam for agitation and tremor as needed. | Agitation is present. | presupposed by an action | The records show an active PRN order for Ativan (R21), a running administration of Ativan IV (R37), and a treatment note for lorazepam (R40), but no administration record within the 24 hours before the decision time (2100-01-02) confirms the patient is currently receiving it. |
| E2558122 | Continue non‑invasive positive pressure ventilation (BiPAP) to support oxygenation. | The patient is currently on non-invasive positive pressure ventilation (BiPAP). | presupposed by an action | The most recent relevant record, R33, documents oxygen therapy via nasal cannula, which is a non-ventilator device. This contradicts the statement that the patient is currently on non-invasive positive pressure ventilation (BiPAP). |
| E2714303 | Continue maintenance anticonvulsant therapy with levetiracetam and phenytoin. | Levetiracetam is currently being given. | presupposed by an action | The records document levetiracetam and phenytoin as seizure therapy treatments, but there is no administration record showing these medications were given in the 24 hours before the decision time. |
| E2714303 | Continue maintenance anticonvulsant therapy with levetiracetam and phenytoin. | Phenytoin is currently being given. | presupposed by an action | The records show phenytoin levels of 22.7 and 20.5 ug/mL, which are within the therapeutic range, but there is no administration record of phenytoin being given in the 24 hours before the decision time. The treatment documentation only lists phenytoin as a documented therapy, not as an administered dose. |
| E2757707 | Continue pressure support ventilation with current settings and begin gradual weaning as tolerated. | The patient is currently on pressure support ventilation. | presupposed by an action | The records show a Pressure Support setting of 10 at 02:25, but no administration or current ventilator setting is documented near the decision time to confirm the patient is currently on pressure support ventilation. |
| E2860378 | Continue intravenous insulin infusion with titration to maintain glucose 140-180 mg/dL. | Intravenous insulin infusion is currently being given. | presupposed by an action | The statement claims the patient is currently receiving an intravenous insulin infusion, but the most recent insulin administration record (R21) shows an infusion that ended at 02:30 on 2100-01-02, before the decision time of 21:00 on 2100-01-01. No 'Running at decision time' record exists. |
| E2879373 | Continue intravenous furosemide infusion to maintain diuresis and manage congestive heart failure. | Intravenous furosemide infusion is currently being given. | presupposed by an action | The records document IV furosemide as a treatment at 10:19 on 2100-01-01, but there is no administration record (e.g., MAR Administered or Running at decision time) within 24 hours before the decision time of 2100-01-02 09:00 to confirm it is currently being given. |
| E3001552 | Transition from non‑invasive ventilation to high‑flow nasal cannula and monitor respiratory status. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records show non-invasive ventilation was documented and PEEP was set, but the most recent oxygen flow records (R38, R45, R49) indicate high-flow oxygen therapy without a matching PEEP setting or ventilator device after 10:41, suggesting the patient was transitioned off non-invasive ventilation by the decision time. |
| E3001552 | Continue current broad‑spectrum antibacterial therapy and reassess culture results in 48 hours. | Broad-spectrum antibacterial therapy is currently being given. | presupposed by an action | The records document antibacterial treatment (R26, R33, R40) but do not specify the antibacterial agent or show an administration record of a specific antibacterial within 24 hours before the decision time. The statement about 'broad-spectrum antibacterial therapy' is therefore not fully supported. |
| E3053511 | Continue non‑invasive positive pressure ventilation (BiPAP) to support respiratory status. | The patient is currently on non-invasive positive pressure ventilation (BiPAP). | presupposed by an action | The records document oxygen therapy (< 40%) at 22:52 and 14:46, but there is no record of BiPAP or non-invasive positive pressure ventilation being administered. The statement about continuing BiPAP is therefore not supported by the available records. |
| E3067309 | Obtain arterial blood gas to reassess acid‑base status and oxygenation after recent FiO₂ increase. | FiO2 was recently increased. | stated outright | The records show FiO2 was 100% at 10:34, then decreased to 50% by 16:55 and 40% by 18:20. It was later increased to 60% at 23:38, but the most recent value before the decision time is 50% at 11:30, which is not an increase from the prior 60%. |
| E3110594 | Gradually wean norepinephrine infusion while closely monitoring mean arterial pressure. | Norepinephrine infusion is currently being given. | presupposed by an action | The records show norepinephrine infusions ending at 04:00 on 2100-01-01, with no administration in the 24 hours before the decision time of 2100-01-02 00:00. Therefore, the statement that the patient is currently receiving norepinephrine is not supported. |
| E3112232 | Continue scheduled thiamine supplementation (Thiamine HCl PO daily) to address potential deficiency in the setting of alcohol withdrawal. | Thiamine deficiency is potential in the setting of alcohol withdrawal. | clinical judgment | The records show ethanol 99 mg/dL, an active lorazepam order, and running thiamine supplementation, but they do not document alcohol withdrawal or thiamine deficiency. These findings do not fully establish the claimed setting. |
| E3124669 | Continue intravenous sodium bicarbonate infusion to enhance salicylate alkalinization. | Intravenous sodium bicarbonate infusion is currently being given. | presupposed by an action | The records document sodium bicarbonate as a treatment for salicylate toxicity, but there is no administration record of an intravenous sodium bicarbonate infusion in the 24 hours before the decision time. |
| E3152779 | Continue invasive arterial blood pressure monitoring and record mean arterial pressure every hour to guide vasopressor titration. | Invasive arterial blood pressure monitoring is currently being performed. | presupposed by an action | The statement claims the patient is currently receiving invasive arterial blood pressure monitoring, but the records show only intermittent arterial blood pressure measurements, with the most recent at 16:00, not continuous monitoring at the decision time of 21:00. No 'Running at decision time' or continuous monitoring record is present. |
| E3170528 | Continue intermittent pneumatic compression for VTE prophylaxis. | Intermittent pneumatic compression is currently being given. | presupposed by an action | The records document an order for VTE prophylaxis with compression boots (R17), but there is no administration or ongoing treatment record showing the boots were actually applied or are currently in use at the decision time. |
| E3170528 | Monitor blood pressure closely and titrate nicardipine infusion to maintain mean arterial pressure between 80-100 mmHg. | Nicardipine infusion is currently being given. | presupposed by an action | The records mention nicardipine only as a documented treatment for ICH/cerebral infarct (R13), but there is no medication order or administration record showing that a nicardipine infusion was actually ordered or given at or before the decision time. |
| E3178242 | Continue current mechanical ventilation settings and reassess readiness for spontaneous breathing trial in 12 hours. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 7.4 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E3205786 | Continue low‑dose intravenous fluid bolus of 0.9% sodium chloride to maintain euvolemia and support blood pressure. | Low-dose intravenous fluid bolus of 0.9% sodium chloride is currently being given. | presupposed by an action | The statement claims a low-dose 0.9% sodium chloride IV bolus is being given to maintain euvolemia and support blood pressure. The records show an order for a 0.9% sodium chloride IV bolus (R8) and a continuous infusion of lactated ringers (R12), but no administration of a 0.9% sodium chloride bolus; the only 0.9% sodium chloride administration is a continuous infusion (R26), not a bolus. |
| E3205786 | Maintain current nasal cannula oxygen at 2 L/min and reassess SpO₂ in 2 hours; consider weaning to room air if SpO₂ remains ≥94% on 21% FiO₂. | The patient is currently on nasal cannula oxygen at 2 L/min. | presupposed by an action | The statement says the patient is on nasal cannula at 2 L/min, but the most recent oxygen flow record before the decision time is 4 L/min (R21), and the treatment documentation (R26) only confirms nasal cannula without specifying the flow rate. |
| E3233620 | Obtain a chest radiograph to assess for postoperative pulmonary complications given diminished breath sounds and persistent cough. | Cough is persistent. | stated outright | The records show cough descriptions of 'No cough' at 05:06 and 'Loose non-productive' at 08:40 and 13:21, which do not support the statement of a 'persistent cough'. |
| E3233620 | Continue broad‑spectrum intravenous antibiotics and obtain repeat blood cultures to monitor for ongoing infection indicated by leukocytosis. | Broad-spectrum intravenous antibiotics are currently being given. | presupposed by an action | The records document antibiotic treatment (R7, R27, R29, R40, R42) but contain no administration record of an antibiotic within 24 hours before the decision time. The statement that the patient is 'currently receiving' antibiotics is therefore not supported by the available administration data. |
| E3233620 | Maintain current analgesic regimen and reassess pain score in 1 hour; if pain remains ≥4, consider titrating morphine IV push per PRN order. | An analgesic regimen is currently being given. | presupposed by an action | The statement claims the patient is currently receiving an analgesic regimen, but the only morphine administration (R1) was at 07:18, over 13 hours before the decision time. Although a PRN morphine order exists (R2), pain assessments at 21:00 (R25) and 23:00 (R26) show no administration of morphine in the 24 hours prior to the decision time. |
| E3237226 | Continue non‑invasive ventilation with current settings and reassess need for escalation. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records document non-invasive ventilation as a treatment on 2100-01-01, but the most recent relevant record (R50) is a transthoracic echocardiography and there is no administration or setting record for non-invasive ventilation at the decision time of 2100-01-02 21:00. The statement that the patient is currently receiving non-invasive ventilation is therefore not supported by the latest records. |

## 5. Judge panel

180 items went to the judge panel. Agreement: {'3/3': 93, '2/3': 85, 'split': 2} (split = no majority; the conservative label was used and the item needs human review).

## 6. Per-case score sheets

| Case | Facts | supported | not_supported | not_addressed | unverifiable | Treatment agreement | Vital recall | All recall |
|---|---|---|---|---|---|---|---|---|
| E153972 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E172015 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E184757 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E211144 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E284265 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E297175 | 3 | 33.3% | 0.0% | 66.7% | 0.0% | 50.0% | - | - |
| E322290 | 3 | 33.3% | 0.0% | 66.7% | 0.0% | 0.0% | - | - |
| E375854 | 4 | 25.0% | 75.0% | 0.0% | 0.0% | 0.0% | - | - |
| E383358 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 50.0% | - | - |
| E395323 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E405746 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E454584 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 33.3% | - | - |
| E467819 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E490454 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 50.0% | - | - |
| E521456 | 5 | 60.0% | 20.0% | 20.0% | 0.0% | 100.0% | - | - |
| E664474 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E733082 | 4 | 25.0% | 25.0% | 50.0% | 0.0% | 0.0% | - | - |
| E756295 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E758325 | 2 | 50.0% | 0.0% | 50.0% | 0.0% | 50.0% | - | - |
| E826669 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E850469 | 3 | 33.3% | 0.0% | 66.7% | 0.0% | 0.0% | - | - |
| E876429 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | - | - | - |
| E899746 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E942382 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E962227 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E978037 | 3 | 33.3% | 0.0% | 66.7% | 0.0% | 0.0% | - | - |
| E1056063 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1057910 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1057967 | 0 | - | - | - | - | 0.0% | - | - |
| E1064283 | 3 | 33.3% | 33.3% | 33.3% | 0.0% | 0.0% | - | - |
| E1065859 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1068212 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071224 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1071450 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1090039 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1090889 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1099398 | 2 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E1117947 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 50.0% | - | - |
| E1121034 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 33.3% | - | - |
| E1171473 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1173453 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1177589 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1287791 | 3 | 33.3% | 33.3% | 33.3% | 0.0% | 0.0% | - | - |
| E1290248 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1449360 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | - | - |
| E1496959 | 4 | 75.0% | 0.0% | 25.0% | 0.0% | 0.0% | - | - |
| E1497157 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 0.0% | - | - |
| E1588473 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1592666 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1619343 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1636307 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1653043 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1672915 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1674875 | 3 | 0.0% | 66.7% | 33.3% | 0.0% | 0.0% | - | - |
| E1682105 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1705630 | 7 | 71.4% | 28.6% | 0.0% | 0.0% | 0.0% | - | - |
| E1739131 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1781359 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1790816 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823356 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823727 | 4 | 25.0% | 0.0% | 75.0% | 0.0% | 0.0% | - | - |
| E1824650 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 33.3% | - | - |
| E1829278 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1837964 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1853162 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1856821 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E2230341 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E2309912 | 5 | 20.0% | 20.0% | 60.0% | 0.0% | - | - | - |
| E2418055 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E2419768 | 0 | - | - | - | - | - | - | - |
| E2558122 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E2609672 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2714303 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E2725629 | 3 | 33.3% | 0.0% | 66.7% | 0.0% | 0.0% | - | - |
| E2757707 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E2814579 | 2 | 50.0% | 0.0% | 50.0% | 0.0% | 33.3% | - | - |
| E2860378 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2879373 | 3 | 33.3% | 33.3% | 33.3% | 0.0% | 0.0% | - | - |
| E3001552 | 4 | 0.0% | 50.0% | 50.0% | 0.0% | 50.0% | - | - |
| E3027283 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E3033795 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3035113 | 4 | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | - | - |
| E3053511 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E3067309 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 100.0% | - | - |
| E3110594 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E3111371 | 2 | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | - | - |
| E3112232 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3115505 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3124669 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3130379 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E3148216 | 0 | - | - | - | - | 0.0% | - | - |
| E3150018 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 0.0% | - | - |
| E3152779 | 4 | 0.0% | 25.0% | 75.0% | 0.0% | 0.0% | - | - |
| E3170528 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E3178242 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3205786 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3220742 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3223097 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3233620 | 5 | 40.0% | 60.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3237226 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | - | - |
