# Evaluation of AI clinical suggestions against patient records

- Input: `eicu_triples_gpt-oss-120b.json`; 100 cases, 3.0 AI suggestions per case on average.
- Models: atomizer `deepseek-v4-pro:0813:cloud`; judge panel `deepseek-v4-pro:0813:cloud` (majority vote; reasoning mode: none); 156 new model calls, 24 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 19.0% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 262 |
| supported / not_supported / not_addressed / unverifiable | 153 / 83 / 26 / 0 |
| Fact accuracy = supported / (supported + not_supported) | 64.8% |
| Cases with at least one not_supported fact | 61 / 100 |
| Omitted findings: abnormalities the clinicians treated that no AI fact mentions | 0 / 0 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 73 | 76.4% | {'supported': 55, 'not_addressed': 1, 'not_supported': 17} |
| presupposed by an action | 170 | 59.1% | {'supported': 88, 'not_supported': 61, 'not_addressed': 21} |
| clinical judgment | 19 | 66.7% | {'supported': 10, 'not_supported': 5, 'not_addressed': 4} |
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
| E172015 | Continue PRN lorazepam dosing for alcohol withdrawal symptom control. | PRN lorazepam is currently being given. | presupposed by an action | The records show a lorazepam administration at 00:15 on 2099-12-31 and active PRN orders, but no administration of lorazepam within 24 hours before the decision time (2100-01-01). Therefore, the statement that PRN lorazepam is currently being given is not supported. |
| E284265 | Obtain a repeat 12-lead electrocardiogram to assess rhythm control and QT interval after ibutilide administration. | Ibutilide was administered. | presupposed by an action | The records document ibutilide as a treatment (R25, R38), but there is no medication administration record showing that ibutilide was actually given. Treatment documentation alone does not confirm administration. |
| E284265 | Continue intravenous diltiazem infusion at the current rate and monitor blood pressure and heart rate q1h. | Intravenous diltiazem infusion is currently being given. | presupposed by an action | The only administration record for diltiazem is an infusion that ran from 2100-01-01 21:00 to 2100-01-02 05:00, which ended more than 13 hours before the decision time of 2100-01-02 18:11. There is no record of a diltiazem infusion running at the decision time. |
| E297175 | Order a chest radiograph to evaluate for possible infiltrates or atelectasis given persistent respiratory symptoms. | Persistent respiratory symptoms are present. | stated outright | The statement claims persistent respiratory symptoms, but the recorded respiratory rates fluctuate between 15 and 26 breaths per minute and are within normal range at several points, including the most recent measurement of 23. The records do not document any persistent symptoms. |
| E322290 | Adjust warfarin dose based on the repeat INR result to achieve therapeutic range for pulmonary embolism. | Therapeutic INR range is needed for pulmonary embolism. | clinical judgment | The records show a pulmonary embolism diagnosis and enoxaparin administration, but no warfarin order or administration. The INR values are 1, which is not therapeutic, and there is no evidence of warfarin being used to achieve a therapeutic range. |
| E322290 | Continue low molecular weight heparin (enoxaparin) as a bridge until therapeutic INR is confirmed. | Low molecular weight heparin (enoxaparin) is currently being given. | presupposed by an action | The records document enoxaparin as a treatment (R18, R30), but there is no medication administration record showing it was given within 24 hours before the decision time. Therefore, the statement that it is 'currently being given' is not supported. |
| E375854 | Continue intravenous meropenem therapy for broad‑spectrum coverage of possible intra‑abdominal infection. | Intravenous meropenem therapy is currently being given. | presupposed by an action | The records document meropenem as a treatment (R32), but there is no medication order or administration record showing that intravenous meropenem was actively being given at the decision time. |
| E383358 | Check INR in 12 hours and adjust warfarin (coumadin) dosing to keep INR within therapeutic range (2.0‑3.0). | Warfarin (coumadin) is currently being given. | presupposed by an action | The records document 'anticoagulant administration / coumadin' as a treatment, but there is no medication administration record showing warfarin was given in the 24 hours before the decision time. The treatment documentation alone does not confirm current administration. |
| E454584 | Check bedside glucose hourly and adjust sliding‑scale insulin infusion to maintain glucose 80‑140 mg/dL. | Insulin infusion is currently being given. | presupposed by an action | The records show a subcutaneous insulin order (R13) and documented subcutaneous insulin administration (R21, R22), but no record of an insulin infusion being given. Therefore, the statement that an insulin infusion is currently being given is not supported. |
| E467819 | Continue intravenous nicardipine infusion with titration to maintain mean arterial pressure ≥65 mmHg. | Nicardipine infusion is currently being given. | presupposed by an action | The most recent nicardipine administration record (R50) ended at 00:00 on 2100-01-02, which is more than 24 hours before the decision time of 01:43 on 2100-01-02. There is no record of an active infusion at the decision time. |
| E521456 | Continue volume‑controlled mechanical ventilation with tidal volume 6‑8 mL/kg, FiO₂ 65‑70 % and PEEP 5‑7 cmH₂O. | Tidal volume is 6-8 mL/kg. | stated outright | The records show a tidal volume of 300 mL with a TV/kg IBW of 4.3871, which is below the stated 6-8 mL/kg range. The documented treatment note (R16) mentions a target of 6-10 ml/kg, but the actual recorded values do not support the statement. |
| E521456 | Monitor point‑of‑care glucose q4h and adjust insulin sliding‑scale as needed. | Insulin sliding-scale is currently being given. | presupposed by an action | The only record mentioning insulin sliding scale is a treatment documentation from 2100-01-01 20:30, which is over 22 hours before the decision time. There is no administration record of insulin sliding scale within the 24 hours before 2100-01-02 18:57, so the statement that it is currently being given is not supported. |
| E733082 | Obtain repeat blood cultures to assess ongoing bacteremia and guide antimicrobial therapy. | Bacteremia is present. | presupposed by an action | The records show an admission diagnosis of 'Sepsis, GI' but do not contain any blood culture results or a stated diagnosis of bacteremia. Sepsis does not directly confirm bacteremia. |
| E733082 | Administer a 500 mL crystalloid bolus to support borderline mean arterial pressure and improve tissue perfusion. | Mean arterial pressure is borderline. | stated outright | The most recent mean arterial pressure before the decision time is 82 mmHg (R50), which is within the normal range, not borderline low. Earlier values were also mostly normal, so the records do not support the claim of borderline MAP. |
| E758325 | Obtain a repeat complete blood count in 6 hours to reassess platelet trend. | Platelet trend is being reassessed. | presupposed by an action | The records show a platelet count of 130 K/MM3 on 2100-01-01 and 90 K/MM3 on 2100-01-02, indicating a decreasing trend, not a reassessment or stable trend. The statement 'Platelet trend is being reassessed' is not directly supported by these values. |
| E850469 | Obtain repeat blood cultures to assess ongoing bacteremia. | Bacteremia is present. | presupposed by an action | The records show an admission diagnosis of 'Sepsis, pulmonary' (R10), but there is no positive blood culture result or other direct evidence confirming bacteremia. The diagnosis of sepsis does not necessarily imply bacteremia. |
| E876429 | Begin gradual weaning of epinephrine and phenylephrine infusions as mean arterial pressure stabilizes above 65 mmHg with adequate cardiac output. | Phenylephrine infusion is currently being given. | presupposed by an action | The records show a phenylephrine infusion was administered from 01:00 to 13:00 on 2100-01-02, but the most recent record (R42) indicates it ended at 13:00. There is no administration record of phenylephrine within 24 hours before the decision time of 2100-01-02 19:53, so the statement that it is currently being given is not supported. |
| E876429 | Assess readiness for spontaneous breathing trial and consider extubation if mental status improves (GCS ≥ 13) and ventilatory parameters remain stable. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 8.4 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E942382 | Continue the IV diltiazem infusion to maintain rate control of atrial arrhythmia. | IV diltiazem infusion is currently being given. | presupposed by an action | The only diltiazem administration record is an infusion that started and ended at 17:04 on 2100-01-01, which is more than 24 hours before the decision time of 2100-01-02 15:23. There is no record of a diltiazem infusion running at the decision time. |
| E962227 | Continue daily hemodialysis and monitor serum electrolytes (potassium, bicarbonate) each shift. | The patient is currently on hemodialysis. | presupposed by an action | The records document a hemodialysis treatment at 22:06 on 2100-01-01, but there is no administration record or 'Running at decision time' entry for hemodialysis within the 24 hours before the decision time of 2100-01-01 21:10. The treatment documentation alone does not confirm the patient is currently on hemodialysis. |
| E1056063 | Maintain therapeutic enoxaparin dosing and schedule the next subcutaneous dose per protocol. | Enoxaparin is currently being given. | presupposed by an action | The only enoxaparin record is an administration at 14:00 on 2100-01-01, which is more than 24 hours before the decision time of 2100-01-02 10:15. There is no administration record within the 24 hours before the decision time, so the statement that enoxaparin is currently being given is not supported. |
| E1057910 | Continue norepinephrine infusion and titrate to maintain MAP ≥65 mmHg. | Norepinephrine infusion is currently being given. | presupposed by an action | The only norepinephrine administration record (R1) ended at 15:32 on 2100-01-01, which is more than 24 hours before the decision time of 2100-01-02 05:25. No administration or 'Running at decision time' record for norepinephrine is present within the 24 hours before the decision time. |
| E1064283 | Continue IV nicardipine infusion to maintain systolic blood pressure < 150 mmHg. | IV nicardipine infusion is currently being given. | presupposed by an action | The records mention nicardipine only as a treatment documented for hypertension (R33), but there is no medication order or administration record showing an IV nicardipine infusion was given or running at the decision time. |
| E1064283 | Monitor blood pressure and heart rate every hour while on antihypertensive therapy. | Antihypertensive therapy is currently being given. | presupposed by an action | The records show labetalol and lisinopril were given on 2099-12-31, and nicardipine is documented as a treatment, but there is no administration record of any antihypertensive in the 24 hours before the decision time (2100-01-02). |
| E1071450 | Continue milrinone infusion for inotropic support. | Milrinone infusion is currently being given. | presupposed by an action | The records mention milrinone only as a documented treatment for shock (R28), but there is no medication order or administration record showing that a milrinone infusion is currently being given. |
| E1071450 | Monitor capillary glucose q4h and adjust insulin aspart dosing per protocol. | Insulin aspart is currently being given. | presupposed by an action | The records show a corrective insulin aspart order that was running at decision time, but no administration record of insulin aspart being given in the 24 hours before the decision time. |
| E1099398 | Continue intravenous antihistamine infusion for ongoing anaphylaxis management. | Anaphylaxis is ongoing. | clinical judgment | The records show an admission diagnosis of anaphylaxis, but there are no current clinical findings (e.g., hypotension, respiratory distress, wheezing) or medication administration records indicating that anaphylaxis is ongoing at the decision time. |
| E1117947 | Order packed red blood cell transfusion to address hemoglobin ~8.5 g/dL with ongoing respiratory distress. | Respiratory distress is ongoing. | stated outright | The statement claims ongoing respiratory distress, but the most recent respiratory rates before the decision time (2100-01-02) are 31-37 insp/min, which are not markedly elevated. The highest recent value is 49 at 22:00 on 2100-01-01, but the latest values do not show persistent distress. |
| E1171473 | Continue mechanical ventilation with current settings and assess readiness for weaning in the next 4–6 hours. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('Tidal Volume (set): 500 mL') was 6.8 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1171473 | Obtain arterial blood gas to monitor pH, pCO₂, and pO₂ trends while on FiO₂ 35% and PEEP 5 cm H₂O. | FiO2 is 35%. | stated outright | The most recent FiO2 record before the decision time is 35% at 12:00 on 2100-01-02, which contradicts the statement's claim of 35% FiO2 being current at 21:00. The statement is not supported by the records. |
| E1173453 | Continue current broad‑spectrum antibiotic regimen and reassess culture results for potential de‑escalation. | Broad-spectrum antibiotics are currently being given. | presupposed by an action | The records document vancomycin as a treatment, but there is no administration record showing that broad-spectrum antibiotics are currently being given at the decision time. |
| E1177589 | Continue hourly point‑of‑care glucose monitoring to detect recurrent hypoglycemia. | Hourly point-of-care glucose monitoring is currently being performed. | presupposed by an action | The records show multiple point-of-care glucose measurements, but they are not hourly. The intervals between measurements are often 1-2 hours or more, so the statement that hourly monitoring is currently being performed is not supported. |
| E1287791 | Continue the mannitol continuous infusion to manage intracranial pressure. | Mannitol continuous infusion is currently being given. | presupposed by an action | The records document a treatment plan for 'mannitol / continuous infusion' (R18), but there is no administration record showing that mannitol is currently being given or was given in the 24 hours before the decision time. |
| E1287791 | Continue the mannitol continuous infusion to manage intracranial pressure. | Intracranial pressure is elevated. | presupposed by an action | The statement claims intracranial pressure is elevated, but the records contain only non-invasive blood pressure measurements and no intracranial pressure values. The highest systolic blood pressure (185 mmHg at R19) does not directly indicate elevated intracranial pressure. |
| E1449360 | Order a short‑acting antihypertensive (e.g., labetalol IV) to maintain systolic blood pressure <140 mmHg given persistent elevations. | Systolic blood pressure is persistently elevated. | stated outright | Median systolic BP over the 6 h before the decision: 134 mmHg (7 readings), normal by the rule 'hypotension SBP < 90; hypertension SBP > 140'. |
| E1588473 | Obtain a platelet transfusion given platelet count of 109 ×10³/µL and ongoing hypotension. | Hypotension is ongoing. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1619343 | Continue intravenous regular insulin infusion with hourly glucose checks to target glucose 140-180 mg/dL. | The patient is currently receiving intravenous regular insulin infusion. | presupposed by an action | The records document a treatment for 'glucose metabolism / insulin / continuous infusion' (R20), but there is no medication administration record showing an intravenous insulin infusion running at the decision time. The only running IV medications are normal saline, ondansetron, vancomycin, and metoclopramide. |
| E1653043 | Continue therapeutic anticoagulation with intravenous heparin and monitor PTT q6h. | The patient is currently receiving intravenous heparin. | presupposed by an action | The records document 'conventional heparin therapy / intravenous' at 07:45 on 2100-01-02, but there is no administration record of intravenous heparin within the 24 hours before the decision time (2100-01-02 21:00). The only running IV medication at decision time is sodium chloride 0.9%. |
| E1653043 | Order repeat lower extremity duplex ultrasound to assess for DVT progression. | DVT is present. | presupposed by an action | The records document that non-invasive testing for DVT was performed, but they do not state that DVT is present. The statement 'DVT is present' is a diagnosis not supported by the available records. |
| E1672915 | Start norepinephrine infusion to maintain MAP ≥65 mmHg given persistent tachycardia, hypertension, and signs of septic shock. | Septic shock is present. | clinical judgment | The records show an admission diagnosis of 'Sepsis, unknown' (R4), but there is no mention of septic shock or any recorded hypotension, organ dysfunction, or vasopressor requirement to support the diagnosis of septic shock. |
| E1674875 | Initiate norepinephrine infusion to support mean arterial pressure. | Mean arterial pressure is low. | presupposed by an action | Median mean arterial pressure over the 6 h before the decision: 65 mmHg (6 readings), normal by the rule 'hypotension MAP < 65'. |
| E1674875 | Continue low tidal volume ventilation strategy for ARDS. | The patient is currently on low tidal volume ventilation. | presupposed by an action | The records mention CPAP/PEEP therapy, but there is no record of low tidal volume ventilation or any ventilator setting. The statement about being on low tidal volume ventilation is therefore not supported by the available data. |
| E1682105 | Titrate intravenous labetalol or add a short‑acting vasodilator to maintain mean arterial pressure >65 mmHg given fluctuating hypotension and hypertension. | Hypotension is fluctuating. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1682105 | Titrate intravenous labetalol or add a short‑acting vasodilator to maintain mean arterial pressure >65 mmHg given fluctuating hypotension and hypertension. | Hypertension is fluctuating. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E1705630 | Continue intravenous potassium chloride infusion to correct persistent hypokalemia (K⁺ 3.2‑3.3 mmol/L). | Intravenous potassium chloride infusion is currently being given. | presupposed by an action | The records show potassium chloride was administered starting at 00:00 on 2100-01-02 and a running infusion at 01:15, but no administration is recorded in the 24 hours before the decision time of 2100-01-01 22:19. The most recent relevant record is an order for sodium chloride, not potassium chloride. |
| E1705630 | Continue intravenous potassium chloride infusion to correct persistent hypokalemia (K⁺ 3.2‑3.3 mmol/L). | Persistent hypokalemia is present. | stated outright | Latest potassium 3.9 mmol/L at 2100-01-02 17:35:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E1705630 | Monitor blood pressure closely and titrate IV labetalol infusion to maintain MAP < 100 mmHg given sustained systolic pressures 150‑170 mmHg. | IV labetalol infusion is currently being given. | presupposed by an action | The records show labetalol was given as one-time intravenous doses at 17:20 and 20:05, but there is no administration record of a continuous labetalol infusion running at the decision time. The active order (R27) is for PRN dosing, not a continuous infusion. |
| E1790816 | Continue intravenous heparin infusion per current dosing and monitor activated partial thromboplastin time (aPTT) q6h. | Intravenous heparin infusion is currently being given. | presupposed by an action | The records show a subcutaneous (SC) heparin order running at decision time, not an intravenous (IV) infusion. No IV heparin administration is documented. |
| E1823356 | Continue intravenous insulin infusion at the current rate and monitor bedside glucose every hour. | Intravenous insulin infusion is currently being given. | presupposed by an action | The records show an intravenous insulin infusion was administered from 01:00 to 20:13 (R5) and from 04:00 to 20:53 (R11), but both ended before the decision time of 21:00. No record shows an IV insulin infusion running at or after 21:00; the only insulin running at decision time is subcutaneous lispro (R47). |
| E1824650 | Continue ventilator weaning and transition to spontaneous breathing trials. | The patient is currently on mechanical ventilation. | presupposed by an action | The latest record before the decision (2100-01-02 15:35:00) reads 'O2 Delivery Device(s): None (charted: RA)'. |
| E1829278 | Continue nicardipine infusion with titration to maintain mean arterial pressure between 65-75 mmHg. | Nicardipine infusion is currently being given. | presupposed by an action | The records show a Nicardipine infusion that ran from 03:00 to 08:24 on 2100-01-02, but no administration record indicates it was running at the decision time of 21:00 on 2100-01-01. The infusion ended before the decision time, so the statement that it is currently being given is not supported. |
| E1837964 | Continue intravenous diuretic therapy and monitor daily weight and electrolytes. | Intravenous diuretic therapy is currently being given. | presupposed by an action | The records show a one-time IV furosemide dose at 14:15 on 2100-01-01 (R1) and a treatment documentation of 'intravenous diuretic' at 17:14 (R15), but no IV diuretic administration within 24 hours before the decision time. The most recent furosemide administrations are oral (R26, R45), so the statement that IV diuretic therapy is currently being given is not supported. |
| E1853162 | Continue scheduled nebulized ipratropium‑albuterol (3 mL q4h PRN) to maintain bronchodilation. | Scheduled nebulized ipratropium-albuterol is currently being given. | presupposed by an action | The records show a one-time nebulized ipratropium-albuterol dose at 09:30 and an active PRN order, but no administration of the scheduled nebulized ipratropium-albuterol within 24 hours before the decision time. |
| E1856821 | Start stress‑dose hydrocortisone 50 mg IV q6h for possible refractory septic shock. | Refractory septic shock is possible. | clinical judgment | The records show sepsis and shock requiring norepinephrine, but they do not document refractory septic shock. The blood pressure values and norepinephrine doses do not directly demonstrate refractory shock. |
| E2309912 | Monitor blood pressure and heart rate every 30 minutes and titrate antihypertensive infusion as needed. | Antihypertensive infusion is currently being given. | presupposed by an action | The statement claims the patient is currently receiving an antihypertensive infusion, but the records contain no administration record for any antihypertensive infusion. The most recent blood pressure at 20:00 is 177 mmHg, which does not support the claim of an active infusion. |
| E2558122 | Continue non‑invasive positive pressure ventilation (BiPAP) to support oxygenation. | The patient is currently on non-invasive positive pressure ventilation (BiPAP). | presupposed by an action | The records show the patient is on oxygen therapy via nasal cannula, not non-invasive positive pressure ventilation (BiPAP). No BiPAP or NIPPV device or setting is documented. |
| E2714303 | Continue maintenance anticonvulsant therapy with levetiracetam and phenytoin. | Levetiracetam is currently being given. | presupposed by an action | The records document levetiracetam as a treatment (R33), but there is no administration record showing it was given in the 24 hours before the decision time. Therefore, the statement that it is 'currently being given' is not supported. |
| E2714303 | Continue maintenance anticonvulsant therapy with levetiracetam and phenytoin. | Phenytoin is currently being given. | presupposed by an action | The records document phenytoin as a treatment for seizure therapy, but there is no administration record showing it was given in the 24 hours before the decision time. The statement that it is 'currently being given' is therefore not supported. |
| E2757707 | Continue pressure support ventilation with current settings and begin gradual weaning as tolerated. | The patient is currently on pressure support ventilation. | presupposed by an action | The only record mentioning pressure support is R18, which shows a Pressure Support setting of 10 at 02:25 on 2100-01-02. There is no record of pressure support ventilation at the decision time of 2100-01-02 23:07, and no later ventilator settings or device rows confirm ongoing pressure support ventilation. |
| E2814579 | Titrate norepinephrine infusion to maintain a mean arterial pressure ≥65 mmHg. | Norepinephrine infusion is currently being given. | presupposed by an action | The only norepinephrine record is an infusion at 13:00 on 2100-01-02, which is more than 24 hours before the decision time of 2100-01-01 22:47. No administration record exists within the 24 hours prior to the decision time, so the statement that it is currently being given is not supported. |
| E2879373 | Continue intravenous furosemide infusion to maintain diuresis and manage congestive heart failure. | Intravenous furosemide infusion is currently being given. | presupposed by an action | The records document IV furosemide as a treatment, but there is no administration record showing it was given within 24 hours before the decision time. A treatment documentation alone does not confirm current administration. |
| E3001552 | Transition from non‑invasive ventilation to high‑flow nasal cannula and monitor respiratory status. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records document non-invasive ventilation (R16, R17, R23, R32) and oxygen flow rates (R38, R45, R49), but there is no record of a transition to high-flow nasal cannula. The statement about transitioning to high-flow nasal cannula is not supported by the supplied records. |
| E3001552 | Continue current broad‑spectrum antibacterial therapy and reassess culture results in 48 hours. | Broad-spectrum antibacterial therapy is currently being given. | presupposed by an action | The records document 'antibacterials' as a treatment category but contain no medication administration record for any antibacterial drug. Therefore, the statement that broad-spectrum antibacterial therapy is currently being given is not supported by evidence of actual administration. |
| E3035113 | Order a portable chest X‑ray to evaluate for possible pneumonia or atelectasis in the setting of COPD exacerbation. | COPD exacerbation is present. | stated outright | The records show elevated pCO2 (54.6 mm Hg), bicarbonate (35.9 mm/l), and base excess (10 mm/l), which suggest chronic CO2 retention, but there is no documented diagnosis of COPD or an acute exacerbation. |
| E3053511 | Continue non‑invasive positive pressure ventilation (BiPAP) to support respiratory status. | The patient is currently on non-invasive positive pressure ventilation (BiPAP). | presupposed by an action | The records document oxygen therapy (< 40%), not non-invasive positive pressure ventilation (BiPAP). No record of BiPAP or any ventilator device is present. |
| E3067309 | Obtain arterial blood gas to reassess acid‑base status and oxygenation after recent FiO₂ increase. | FiO2 was recently increased. | stated outright | The records show FiO2 was 100% at 10:34, then decreased to 50% by 16:55 and 40% by 18:20, with a later increase to 60% at 23:38. The statement that FiO2 was recently increased is not supported because the most recent change before the decision time was a decrease from 100% to 40%, and the increase to 60% occurred after the decision time. |
| E3110594 | Gradually wean norepinephrine infusion while closely monitoring mean arterial pressure. | Norepinephrine infusion is currently being given. | presupposed by an action | The records show norepinephrine infusions that ended at 04:00 on 2100-01-01, with no administration or 'Running at decision time' record for norepinephrine in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E3112232 | Obtain a repeat basic metabolic panel to reassess sodium and other electrolytes given mild hyponatremia (Na 130 mmol/L) and recent fluctuations in blood pressure. | Blood pressure has fluctuated recently. | stated outright | The most recent blood pressure readings before the decision time (20:46) show a systolic of 94 mmHg and diastolic of 55 mmHg, which are low, but the statement claims the blood pressure is 'fluctuating' and 'rising'. The latest value at 21:00 (126/76) is not the highest recorded, and the overall trend shows a drop from earlier values, so the records do not support the claim of rising blood pressure. |
| E3124669 | Continue intravenous sodium bicarbonate infusion to enhance salicylate alkalinization. | Intravenous sodium bicarbonate infusion is currently being given. | presupposed by an action | The records document sodium bicarbonate as a treatment for salicylate toxicity, but there is no administration record showing an intravenous sodium bicarbonate infusion was given in the 24 hours before the decision time. |
| E3150018 | Continue scheduled antipsychotic (haloperidol) for agitation management. | Haloperidol is currently being given. | presupposed by an action | The records document haloperidol (haldol) as a treatment for agitation at 00:06 and 15:23, but there is no administration record (e.g., 'MAR Administered' or 'Given') showing it was actually given in the 24 hours before the decision time. |
| E3152779 | Obtain a bedside transthoracic echocardiogram to evaluate cardiac function given fluctuating cardiac index and low systemic vascular resistance. | Cardiac index is fluctuating. | stated outright | The records show heart rate values ranging from 58 to 107 bpm, with the latest value at 96 bpm. The statement 'fluctuating' is not supported because the most recent values are relatively stable around 80 bpm, and the highest value (107) is not the latest. |
| E3152779 | Obtain a bedside transthoracic echocardiogram to evaluate cardiac function given fluctuating cardiac index and low systemic vascular resistance. | Systemic vascular resistance is low. | stated outright | The statement claims the patient is currently receiving mechanical ventilation, but the records show only respiratory rate measurements and no ventilator settings, device orders, or administration records. The most recent respiratory rates are elevated but do not directly indicate mechanical ventilation. |
| E3170528 | Continue intermittent pneumatic compression for VTE prophylaxis. | Intermittent pneumatic compression is currently being given. | presupposed by an action | The records document 'compression boots' as a treatment for VTE prophylaxis, but there is no administration record showing intermittent pneumatic compression is currently being given at the decision time. |
| E3170528 | Monitor blood pressure closely and titrate nicardipine infusion to maintain mean arterial pressure between 80-100 mmHg. | Nicardipine infusion is currently being given. | presupposed by an action | The records mention nicardipine as a treatment documented for ICH/cerebral infarct, but there is no administration record of a nicardipine infusion in the 24 hours before the decision time or a 'Running at decision time' record for it. |
| E3178242 | Continue current mechanical ventilation settings and reassess readiness for spontaneous breathing trial in 12 hours. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 7.4 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E3205786 | Continue low‑dose intravenous fluid bolus of 0.9% sodium chloride to maintain euvolemia and support blood pressure. | Low-dose intravenous fluid bolus of 0.9% sodium chloride is currently being given. | presupposed by an action | The statement claims a low-dose 0.9% sodium chloride IV bolus is being given to maintain euvolemia and support blood pressure. The records show an order for a 0.9% sodium chloride IV bolus (R8) and a continuous 0.9% sodium chloride infusion running at decision time (R26), but no administration of a bolus; the only IV fluid administered at decision time is Lactated Ringers (R12). |
| E3205786 | Maintain current nasal cannula oxygen at 2 L/min and reassess SpO₂ in 2 hours; consider weaning to room air if SpO₂ remains ≥94% on 21% FiO₂. | The patient is currently on nasal cannula oxygen at 2 L/min. | presupposed by an action | The most recent O2 Flow record before the decision time is 2 L/min (R25), and a treatment documentation at 00:16 on 2100-01-02 confirms nasal cannula oxygen therapy (R27). However, the statement specifies 'currently on nasal cannula oxygen at 2 L/min' at 2100-01-01 22:25, but the flow rate of 2 L/min is recorded at 23:06, after the decision time, and the nasal cannula documentation is also after the decision time. The records do not show a nasal cannula at 2 L/min at the decision time. |
| E3220742 | Continue scheduled levetiracetam for seizure prophylaxis. | Levetiracetam is currently being given. | presupposed by an action | The records show a levetiracetam administration from 05:00 to 11:47 on 2100-01-01, but no administration within 24 hours before the decision time of 2100-01-01 02:33. Treatment documentation mentions levetiracetam, but this does not confirm it is currently being given. |
| E3223097 | Continue octreotide infusion at 50 mcg/hour for variceal bleeding control. | Variceal bleeding is present. | clinical judgment | The records document an upper GI bleed and octreotide administration for varices, but they do not explicitly state or directly show that the bleeding is variceal in origin. |
| E3223097 | Administer a bolus of isotonic crystalloid (e.g., 500 mL normal saline) to address persistent hypotension (SBP ≈ 85‑95 mmHg). | SBP is 85-95 mmHg. | stated outright | The records show multiple systolic blood pressure readings below 90 mmHg (e.g., 78, 83, 85, 88 mmHg) in the hours before the decision time, but the most recent reading at 21:05 is 104 mmHg. The statement's claim of persistent hypotension with SBP 85-95 mmHg is not supported by the latest value, which is above that range. |
| E3233620 | Obtain a chest radiograph to assess for postoperative pulmonary complications given diminished breath sounds and persistent cough. | Cough is persistent. | stated outright | The most recent cough assessments before the decision time show 'No cough' at 05:06 and 'Loose non-productive' at 08:40 and 13:21, which do not support the claim of a 'persistent' cough. Earlier records show a strong non-productive cough, but the latest records contradict the persistence. |
| E3233620 | Continue broad‑spectrum intravenous antibiotics and obtain repeat blood cultures to monitor for ongoing infection indicated by leukocytosis. | Broad-spectrum intravenous antibiotics are currently being given. | presupposed by an action | The records document antibiotics as a treatment category (e.g., 'therapeutic antibacterials') but contain no medication order or administration record for a specific intravenous antibiotic at or near the decision time. Therefore, the statement that broad-spectrum IV antibiotics are currently being given is not supported by the supplied records. |
| E3233620 | Maintain current analgesic regimen and reassess pain score in 1 hour; if pain remains ≥4, consider titrating morphine IV push per PRN order. | An analgesic regimen is currently being given. | presupposed by an action | The records show a one-time morphine administration at 07:18 and a PRN morphine order, but no analgesic administration in the 24 hours before the decision time. Therefore, the statement that an analgesic regimen is currently being given is not supported. |

## 5. Judge panel

180 items went to the judge panel. Agreement: {'1/1': 180} (split = no majority; the conservative label was used and the item needs human review).

## 6. Per-case score sheets

| Case | Facts | supported | not_supported | not_addressed | unverifiable | Treatment agreement | Vital recall | All recall |
|---|---|---|---|---|---|---|---|---|
| E153972 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E172015 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E184757 | 5 | 80.0% | 0.0% | 20.0% | 0.0% | 0.0% | - | - |
| E211144 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E284265 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E297175 | 3 | 0.0% | 33.3% | 66.7% | 0.0% | 50.0% | - | - |
| E322290 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E375854 | 4 | 50.0% | 25.0% | 25.0% | 0.0% | 0.0% | - | - |
| E383358 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 50.0% | - | - |
| E395323 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E405746 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E454584 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 33.3% | - | - |
| E467819 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E490454 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E521456 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 100.0% | - | - |
| E664474 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E733082 | 4 | 25.0% | 50.0% | 25.0% | 0.0% | 0.0% | - | - |
| E756295 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E758325 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 50.0% | - | - |
| E826669 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E850469 | 3 | 33.3% | 33.3% | 33.3% | 0.0% | 0.0% | - | - |
| E876429 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | - | - | - |
| E899746 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E942382 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E962227 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E978037 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 0.0% | - | - |
| E1056063 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1057910 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1057967 | 0 | - | - | - | - | 0.0% | - | - |
| E1064283 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1065859 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1068212 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071224 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1071450 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1090039 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1090889 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1099398 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | - | - |
| E1117947 | 3 | 33.3% | 33.3% | 33.3% | 0.0% | 50.0% | - | - |
| E1121034 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 33.3% | - | - |
| E1171473 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1173453 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1177589 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1287791 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1290248 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1449360 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | - | - |
| E1496959 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1497157 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 0.0% | - | - |
| E1588473 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1592666 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1619343 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1636307 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1653043 | 3 | 0.0% | 66.7% | 33.3% | 0.0% | 0.0% | - | - |
| E1672915 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1674875 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1682105 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1705630 | 7 | 57.1% | 42.9% | 0.0% | 0.0% | 0.0% | - | - |
| E1739131 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1781359 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1790816 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823356 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823727 | 4 | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | - | - |
| E1824650 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 33.3% | - | - |
| E1829278 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1837964 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1853162 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1856821 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E2230341 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E2309912 | 5 | 40.0% | 20.0% | 40.0% | 0.0% | - | - | - |
| E2418055 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E2419768 | 0 | - | - | - | - | - | - | - |
| E2558122 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E2609672 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2714303 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E2725629 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 0.0% | - | - |
| E2757707 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E2814579 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 33.3% | - | - |
| E2860378 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2879373 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E3001552 | 4 | 25.0% | 50.0% | 25.0% | 0.0% | 50.0% | - | - |
| E3027283 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E3033795 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3035113 | 4 | 50.0% | 25.0% | 25.0% | 0.0% | 0.0% | - | - |
| E3053511 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E3067309 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 100.0% | - | - |
| E3110594 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E3111371 | 2 | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | - | - |
| E3112232 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3115505 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3124669 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3130379 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E3148216 | 0 | - | - | - | - | 0.0% | - | - |
| E3150018 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E3152779 | 4 | 25.0% | 50.0% | 25.0% | 0.0% | 0.0% | - | - |
| E3170528 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E3178242 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3205786 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3220742 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3223097 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E3233620 | 5 | 40.0% | 60.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3237226 | 2 | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | - | - |
