# Evaluation of AI clinical suggestions against patient records

- Input: `eicu_triples_gpt-oss-120b.json`; 100 cases, 3.0 AI suggestions per case on average.
- Models: atomizer `deepseek-v4-pro:0813:cloud`; judge panel `deepseek-v4-pro:0813:cloud` (majority vote; reasoning mode: none); 180 new model calls, 0 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 18.7% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 262 |
| supported / not_supported / not_addressed / unverifiable | 152 / 86 / 24 / 0 |
| Fact accuracy = supported / (supported + not_supported) | 63.9% |
| Cases with at least one not_supported fact | 63 / 100 |
| Omitted findings: abnormalities the clinicians treated that no AI fact mentions | 0 / 0 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 73 | 85.5% | {'supported': 59, 'not_addressed': 4, 'not_supported': 10} |
| presupposed by an action | 170 | 53.6% | {'supported': 82, 'not_supported': 71, 'not_addressed': 17} |
| clinical judgment | 19 | 68.8% | {'supported': 11, 'not_supported': 5, 'not_addressed': 3} |
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
| E172015 | Continue PRN lorazepam dosing for alcohol withdrawal symptom control. | PRN lorazepam is currently being given. | presupposed by an action | The records show active PRN orders for lorazepam (R4, R16, R17) and a single administration on 2099-12-31 at 00:15 (R2), but no administration of lorazepam within 24 hours before the decision time of 2100-01-02 23:52. Therefore, the statement that PRN lorazepam is currently being given is not supported. |
| E284265 | Obtain a repeat 12-lead electrocardiogram to assess rhythm control and QT interval after ibutilide administration. | Ibutilide was administered. | presupposed by an action | The records document ibutilide as a treatment (R25, R38), but there is no medication administration record showing it was actually given. The documentation occurs after the decision time and does not confirm administration. |
| E284265 | Continue intravenous diltiazem infusion at the current rate and monitor blood pressure and heart rate q1h. | Intravenous diltiazem infusion is currently being given. | presupposed by an action | The records show a diltiazem infusion starting at 21:00 on 2100-01-01, which is after the decision time of 18:11 on 2100-01-01. There is no administration record of diltiazem in the 24 hours before the decision time, so the statement that it is currently being given is not supported. |
| E322290 | Continue low molecular weight heparin (enoxaparin) as a bridge until therapeutic INR is confirmed. | Low molecular weight heparin (enoxaparin) is currently being given. | presupposed by an action | The records document enoxaparin as a treatment (R18, R30), but there is no medication administration record showing it was given within 24 hours before the decision time. The statement that it is 'currently being given' is therefore not supported. |
| E375854 | Continue intravenous meropenem therapy for broad‑spectrum coverage of possible intra‑abdominal infection. | Intravenous meropenem therapy is currently being given. | presupposed by an action | The records document meropenem as a treatment (R32), but there is no medication order or administration record showing intravenous meropenem was being given at the decision time. The only IV administrations are magnesium sulfate and sodium chloride. |
| E375854 | Continue intravenous meropenem therapy for broad‑spectrum coverage of possible intra‑abdominal infection. | Possible intra-abdominal infection is present. | clinical judgment | The records show consultations for infectious disease, gastroenterology, and surgery, and a GI bleeding diagnosis, but they do not state an intra-abdominal infection. The temperature measurements are normal, which does not directly support the presence of an infection. |
| E383358 | Check INR in 12 hours and adjust warfarin (coumadin) dosing to keep INR within therapeutic range (2.0‑3.0). | Warfarin (coumadin) is currently being given. | presupposed by an action | The records document 'anticoagulant administration / coumadin' as a treatment, but there is no medication administration record showing warfarin was actually given in the 24 hours before the decision time. The treatment documentation alone does not confirm current administration. |
| E454584 | Check bedside glucose hourly and adjust sliding‑scale insulin infusion to maintain glucose 80‑140 mg/dL. | Insulin infusion is currently being given. | presupposed by an action | The records mention insulin administration via subcutaneous route (NovoLOG Flexpen SUBQ Q4H) and documented subcutaneous insulin doses, but there is no record of an insulin infusion being administered at or near the decision time. |
| E467819 | Continue intravenous nicardipine infusion with titration to maintain mean arterial pressure ≥65 mmHg. | Nicardipine infusion is currently being given. | presupposed by an action | The most recent nicardipine administration record (R50) ended at 00:00 on 2100-01-02, which is more than 24 hours before the decision time of 01:43 on 2100-01-02. There is no record of an active infusion at the decision time. |
| E490454 | Continue non‑invasive ventilation with BiPAP and titrate FiO₂ to maintain SpO₂ ≥ 92 % while monitoring for respiratory fatigue. | The patient is currently on non-invasive ventilation with BiPAP. | presupposed by an action | The records document non-invasive ventilation via face mask, but do not mention BiPAP. Therefore, the specific mode of non-invasive ventilation (BiPAP) is not supported. |
| E521456 | Continue volume‑controlled mechanical ventilation with tidal volume 6‑8 mL/kg, FiO₂ 65‑70 % and PEEP 5‑7 cmH₂O. | Tidal volume is 6-8 mL/kg. | stated outright | The records show a tidal volume of 300 mL with a TV/kg IBW of 4.3871, which is below the stated 6-8 mL/kg range. The treatment documentation mentions a target of 6-10 ml/kg, but the actual measured values do not support the statement. |
| E521456 | Monitor point‑of‑care glucose q4h and adjust insulin sliding‑scale as needed. | Insulin sliding-scale is currently being given. | presupposed by an action | The records contain a treatment documentation for 'insulin / sliding scale administration' (R12), but this is not an administration record showing the insulin was actually given within 24 hours before the decision time. No MAR Administered, Given, or Running at decision time record for insulin is present. |
| E664474 | Continue non‑invasive ventilation with current settings and monitor respiratory parameters closely. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records contain a treatment documentation note for non-invasive ventilation (R30), but no administration record or current ventilator setting is charted within 24 hours before the decision time. Therefore, the statement that the patient is currently on non-invasive ventilation is not supported. |
| E733082 | Obtain repeat blood cultures to assess ongoing bacteremia and guide antimicrobial therapy. | Bacteremia is present. | presupposed by an action | The records mention sepsis as an admission diagnosis, but do not contain any blood culture results or other direct evidence confirming bacteremia. Sepsis can occur without bacteremia, so the diagnosis of sepsis alone does not support the statement that bacteremia is present. |
| E733082 | Administer a 500 mL crystalloid bolus to support borderline mean arterial pressure and improve tissue perfusion. | Mean arterial pressure is borderline. | stated outright | The most recent mean arterial pressure before the decision time is 82 mmHg (R50), which is within the normal range, not borderline low. Earlier values were also generally above 70 mmHg, so the records do not support the statement that the mean arterial pressure is borderline. |
| E826669 | Gradually wean norepinephrine infusion as blood pressure stabilizes, targeting MAP ≥65 mmHg. | Norepinephrine infusion is currently being given. | presupposed by an action | The records show a norepinephrine infusion order started at 2100-01-01 17:48, which is after the decision time of 2100-01-01 00:46. There is no administration record of norepinephrine in the 24 hours before the decision time. |
| E850469 | Obtain repeat blood cultures to assess ongoing bacteremia. | Bacteremia is present. | presupposed by an action | The records mention sepsis (R10), but there is no positive blood culture or other direct evidence of bacteremia. The diagnosis of sepsis alone does not confirm bacteremia. |
| E850469 | Continue current broad‑spectrum antibiotics (piperacillin‑tazobactam and vancomycin) pending culture results. | Vancomycin is currently being given. | presupposed by an action | The records show vancomycin was administered on 2100-01-01 from 14:33 to 15:18 and again starting at 15:30, but there is no administration record within 24 hours before the decision time of 2100-01-02 13:47. The most recent vancomycin administration ended over 22 hours prior, so the statement that it is 'currently being given' is not supported. |
| E876429 | Begin gradual weaning of epinephrine and phenylephrine infusions as mean arterial pressure stabilizes above 65 mmHg with adequate cardiac output. | Phenylephrine infusion is currently being given. | presupposed by an action | The records show phenylephrine infusions that ended at 13:00 on 2100-01-02, but no administration record within 24 hours before the decision time of 19:53 on 2100-01-01. The most recent relevant record (R42) indicates the infusion stopped, so the statement that it is currently being given is not supported. |
| E876429 | Assess readiness for spontaneous breathing trial and consider extubation if mental status improves (GCS ≥ 13) and ventilatory parameters remain stable. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 8.4 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E942382 | Continue the IV diltiazem infusion to maintain rate control of atrial arrhythmia. | IV diltiazem infusion is currently being given. | presupposed by an action | The records mention diltiazem as a documented treatment (R17) and show an infusion input at 17:04 on 2100-01-01 (R21), but there is no administration record within 24 hours before the decision time (2100-01-01 15:23) or a 'Running at decision time' record for diltiazem. The infusion record is after the decision time, so it does not support the statement that it is currently being given. |
| E962227 | Continue daily hemodialysis and monitor serum electrolytes (potassium, bicarbonate) each shift. | The patient is currently on hemodialysis. | presupposed by an action | The only record mentioning hemodialysis is R35, which documents it as a treatment at 22:06 on 2100-01-01, after the decision time of 21:10. There is no administration record of hemodialysis in the 24 hours before the decision time, so the statement that the patient is currently on hemodialysis is not supported. |
| E978037 | Increase norepinephrine infusion to maintain MAP ≥65 mmHg | Norepinephrine infusion is currently being given. | presupposed by an action | The records show norepinephrine was administered earlier (R30, R32, R37, R39), but the most recent infusion ended at 17:15 on 2100-01-01, over 11 hours before the decision time of 04:37 on 2100-01-02. There is no administration record within 24 hours of the decision time, so the statement that it is currently being given is not supported. |
| E978037 | Obtain repeat hemoglobin and hematocrit in 2 hours to assess ongoing bleeding | Ongoing bleeding is present. | clinical judgment | The records show an admission diagnosis of lower GI bleeding and documentation of blood product administration, but there is no direct evidence of ongoing bleeding at the decision time. The statement of ongoing bleeding is not directly supported by the available records. |
| E1056063 | Maintain therapeutic enoxaparin dosing and schedule the next subcutaneous dose per protocol. | Enoxaparin is currently being given. | presupposed by an action | The only enoxaparin record is an administration from 2100-01-01 14:00, which is more than 24 hours before the decision time of 2100-01-02 10:15. There is no record of enoxaparin being given within the 24 hours prior to the decision time. |
| E1057910 | Continue norepinephrine infusion and titrate to maintain MAP ≥65 mmHg. | Norepinephrine infusion is currently being given. | presupposed by an action | The records show a norepinephrine infusion that ended on 2100-01-01 at 15:32 (R1) and a treatment note from 07:10 (R26), but no administration of norepinephrine within 24 hours before the decision time of 2100-01-02 05:25. Therefore, the statement that it is currently being given is not supported. |
| E1064283 | Continue IV nicardipine infusion to maintain systolic blood pressure < 150 mmHg. | IV nicardipine infusion is currently being given. | presupposed by an action | The records mention nicardipine only as a treatment documented for hypertension (R33), but there is no administration record or 'Running at decision time' entry for IV nicardipine. Therefore, the statement that it is currently being given is not supported. |
| E1071450 | Continue milrinone infusion for inotropic support. | Milrinone infusion is currently being given. | presupposed by an action | The records mention milrinone only as a treatment documented for shock/inotropic agent (R28), but there is no medication order or administration record showing that a milrinone infusion is currently being given at the decision time. |
| E1099398 | Continue intravenous antihistamine infusion for ongoing anaphylaxis management. | Anaphylaxis is ongoing. | clinical judgment | The records only show an admission diagnosis of anaphylaxis from the previous day, with no recent signs, symptoms, or treatment records indicating that anaphylaxis is ongoing at the decision time. |
| E1117947 | Continue non‑invasive ventilation with close monitoring of respiratory rate and oxygen saturation. | The patient is currently on non-invasive ventilation. | presupposed by an action | The only record mentioning non-invasive ventilation is R31, which documents it as a treatment at 07:31, after the decision time of 06:58. There is no record of non-invasive ventilation being administered or active at the decision time. |
| E1171473 | Continue mechanical ventilation with current settings and assess readiness for weaning in the next 4–6 hours. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('Tidal Volume (set): 500 mL') was 6.8 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1173453 | Continue current broad‑spectrum antibiotic regimen and reassess culture results for potential de‑escalation. | Broad-spectrum antibiotics are currently being given. | presupposed by an action | The records document vancomycin as a treatment, but there is no administration record showing that broad-spectrum antibiotics are currently being given at the decision time. |
| E1177589 | Continue hourly point‑of‑care glucose monitoring to detect recurrent hypoglycemia. | Hourly point-of-care glucose monitoring is currently being performed. | presupposed by an action | The records show multiple glucose finger stick measurements, but they are not hourly. The intervals between measurements are often 1-2 hours or longer, and there is no record of an order or protocol for hourly monitoring. |
| E1287791 | Continue the mannitol continuous infusion to manage intracranial pressure. | Mannitol continuous infusion is currently being given. | presupposed by an action | The records mention mannitol as a continuous infusion in a treatment documentation note (R18), but there is no administration record showing that mannitol was actually being given at or within 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E1449360 | Continue the magnesium sulfate infusion at the current rate with close monitoring of blood pressure, reflexes, and urine output. | Magnesium sulfate infusion is currently being given. | presupposed by an action | The records show magnesium infusions, but the most recent administration before the decision time (06:16) ended at 05:45 on 2100-01-02, and the next infusion started at 13:00 on 2100-01-01. There is no 'Running at decision time' record for magnesium at 06:16, so the statement that it is currently being given is not supported. |
| E1449360 | Order a short‑acting antihypertensive (e.g., labetalol IV) to maintain systolic blood pressure <140 mmHg given persistent elevations. | Systolic blood pressure is persistently elevated. | stated outright | Median systolic BP over the 6 h before the decision: 134 mmHg (7 readings), normal by the rule 'hypotension SBP < 90; hypertension SBP > 140'. |
| E1588473 | Obtain a platelet transfusion given platelet count of 109 ×10³/µL and ongoing hypotension. | Hypotension is ongoing. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1619343 | Continue intravenous regular insulin infusion with hourly glucose checks to target glucose 140-180 mg/dL. | The patient is currently receiving intravenous regular insulin infusion. | presupposed by an action | The records mention insulin as a continuous infusion in a treatment documentation note (R20), but there is no medication administration record showing an intravenous regular insulin infusion running at the decision time or within the prior 24 hours. The only running IV medications documented are normal saline, ondansetron, vancomycin, and metoclopramide. |
| E1653043 | Continue therapeutic anticoagulation with intravenous heparin and monitor PTT q6h. | The patient is currently receiving intravenous heparin. | presupposed by an action | The records document 'conventional heparin therapy / intravenous' at 07:45 on 2100-01-02, but there is no administration record of intravenous heparin within 24 hours before the decision time (21:32 on 2100-01-02). The only running IV medication is sodium chloride 0.9% (R46), so the statement that the patient is currently receiving IV heparin is not supported. |
| E1653043 | Maintain current oxygen supplementation at 2 L/min via nasal cannula and reassess SpO₂ q4h. | The patient is currently receiving oxygen supplementation at 2 L/min via nasal cannula. | presupposed by an action | The records show oxygen flow rate of 2 L/min (e.g., R48 at 20:00), but there is no documentation of the delivery device being a nasal cannula. The statement about the specific device is therefore not fully supported. |
| E1672915 | Start norepinephrine infusion to maintain MAP ≥65 mmHg given persistent tachycardia, hypertension, and signs of septic shock. | Septic shock is present. | clinical judgment | The records show an admission diagnosis of 'Sepsis, unknown' (R4) and fluctuating fevers, but they do not document septic shock. Septic shock requires evidence of hypotension or hypoperfusion, which is absent from the provided records. |
| E1674875 | Initiate norepinephrine infusion to support mean arterial pressure. | Mean arterial pressure is low. | presupposed by an action | Median mean arterial pressure over the 6 h before the decision: 65 mmHg (6 readings), normal by the rule 'hypotension MAP < 65'. |
| E1674875 | Continue low tidal volume ventilation strategy for ARDS. | The patient is currently on low tidal volume ventilation. | presupposed by an action | The records mention CPAP/PEEP therapy (R8), but there is no record of low tidal volume ventilation or any tidal volume setting. The statement about current low tidal volume ventilation is therefore not supported. |
| E1682105 | Titrate intravenous labetalol or add a short‑acting vasodilator to maintain mean arterial pressure >65 mmHg given fluctuating hypotension and hypertension. | Hypotension is fluctuating. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1682105 | Titrate intravenous labetalol or add a short‑acting vasodilator to maintain mean arterial pressure >65 mmHg given fluctuating hypotension and hypertension. | Hypertension is fluctuating. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E1705630 | Continue intravenous potassium chloride infusion to correct persistent hypokalemia (K⁺ 3.2‑3.3 mmol/L). | Intravenous potassium chloride infusion is currently being given. | presupposed by an action | The records show potassium chloride was administered starting at 00:00 on 2100-01-02, which is after the decision time of 22:19 on 2100-01-01. There is no administration record of potassium chloride in the 24 hours before the decision time, so the statement that it is currently being given is not supported. |
| E1705630 | Continue intravenous potassium chloride infusion to correct persistent hypokalemia (K⁺ 3.2‑3.3 mmol/L). | Persistent hypokalemia is present. | stated outright | Latest potassium 3.9 mmol/L at 2100-01-02 17:35:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E1705630 | Monitor blood pressure closely and titrate IV labetalol infusion to maintain MAP < 100 mmHg given sustained systolic pressures 150‑170 mmHg. | IV labetalol infusion is currently being given. | presupposed by an action | The records show labetalol was given as one-time intravenous doses at 17:20 and 20:05 on 2100-01-01, and there is an active PRN order for labetalol every 6 hours, but no continuous infusion or administration within 24 hours of the decision time (2100-01-02 22:19) is documented. Therefore, the statement that an IV labetalol infusion is currently being given is not supported. |
| E1790816 | Continue intravenous heparin infusion per current dosing and monitor activated partial thromboplastin time (aPTT) q6h. | Intravenous heparin infusion is currently being given. | presupposed by an action | The records show a subcutaneous (SC) heparin order running at decision time, not an intravenous (IV) infusion. No IV heparin administration or infusion record is present. |
| E1823356 | Continue intravenous insulin infusion at the current rate and monitor bedside glucose every hour. | Intravenous insulin infusion is currently being given. | presupposed by an action | The records show an intravenous insulin infusion was started at 01:00 and ran until 20:13, but there is no administration record of it within the 24 hours before the decision time of 03:18. The most recent insulin administration is a subcutaneous lispro order, not an intravenous infusion. |
| E1823727 | Continue intermittent hemodialysis as scheduled to manage uremia and fluid balance. | The patient is currently receiving intermittent hemodialysis. | presupposed by an action | The records document hemodialysis as a treatment at 15:00 on 2100-01-01, but this is after the decision time of 14:58 and there is no administration or running record of hemodialysis at or before the decision time. The statement that the patient is currently receiving intermittent hemodialysis is therefore not supported. |
| E1824650 | Continue ventilator weaning and transition to spontaneous breathing trials. | The patient is currently on mechanical ventilation. | presupposed by an action | The latest record before the decision (2100-01-02 15:35:00) reads 'O2 Delivery Device(s): None (charted: RA)'. |
| E1824650 | Monitor capillary glucose every 4 hours and adjust insulin dosing as needed. | Insulin is currently being given. | presupposed by an action | The records show an insulin infusion that ended at 14:30 on 2100-01-02 (R21) and a subcutaneous insulin order that started at 16:00 on 2100-01-02 (R49), but no administration of insulin within the 24 hours before the decision time of 17:48 on 2100-01-02. Therefore, the statement that insulin is currently being given is not supported. |
| E1829278 | Continue nicardipine infusion with titration to maintain mean arterial pressure between 65-75 mmHg. | Nicardipine infusion is currently being given. | presupposed by an action | The records show a Nicardipine infusion that ran from 03:00 to 08:24 on 2100-01-02, but it ended 19 minutes before the decision time of 08:43. There is no record of a Nicardipine infusion running at the decision time. |
| E1837964 | Continue intravenous diuretic therapy and monitor daily weight and electrolytes. | Intravenous diuretic therapy is currently being given. | presupposed by an action | The records show an IV furosemide administration on 2100-01-01 at 14:15 (R1) and a treatment documentation for intravenous diuretic (R15), but the most recent diuretic administrations at decision time are oral furosemide (R26, R45). No IV diuretic administration is recorded within 24 hours before the decision time. |
| E1853162 | Continue scheduled nebulized ipratropium‑albuterol (3 mL q4h PRN) to maintain bronchodilation. | Scheduled nebulized ipratropium-albuterol is currently being given. | presupposed by an action | The records show a one-time administration of ipratropium-albuterol on 2100-01-01 at 09:30 (R3) and an active PRN order (R23), but no administration of the nebulized medication within 24 hours before the decision time of 2100-01-02 13:51. Therefore, the statement that it is 'currently being given' is not supported. |
| E1856821 | Add vasopressin infusion to the current norepinephrine regimen to achieve target MAP ≥65 mmHg. | Norepinephrine is currently being given. | presupposed by an action | The most recent norepinephrine infusion record (R43) ended at 14:11 on 2100-01-02, which is more than 24 hours before the decision time of 18:36 on 2100-01-01. There is no administration record showing norepinephrine was running at the decision time. |
| E2230341 | Continue eptifibatide infusion at the current rate and monitor for bleeding complications. | Eptifibatide infusion is currently being given. | presupposed by an action | The records show an Eptifibatide infusion that started on 2100-01-01 at 17:58 and ended on 2100-01-02 at 00:24, which is before the decision time of 2100-01-02 14:38. A subsequent infusion started at 04:24 and ended at 09:05, also before the decision time. There is no record of an Eptifibatide infusion running at the decision time. |
| E2309912 | Continue PRN lorazepam for agitation and tremor as needed. | Lorazepam is currently being given. | presupposed by an action | The records show an active PRN order for lorazepam (Ativan) and a treatment documentation mentioning lorazepam, but no administration record within 24 hours before the decision time. The only Ativan administration record (R33) is dated after the decision time, so it does not support that lorazepam is currently being given. |
| E2558122 | Continue non‑invasive positive pressure ventilation (BiPAP) to support oxygenation. | The patient is currently on non-invasive positive pressure ventilation (BiPAP). | presupposed by an action | The records do not mention BiPAP or non-invasive positive pressure ventilation. The only ventilation-related record, R33, documents oxygen therapy via nasal cannula, which contradicts the statement that the patient is on BiPAP. |
| E2714303 | Continue maintenance anticonvulsant therapy with levetiracetam and phenytoin. | Levetiracetam is currently being given. | presupposed by an action | The records document levetiracetam as a treatment for seizure therapy, but there is no administration record showing it was given within 24 hours before the decision time. A treatment documentation alone does not confirm current administration. |
| E2714303 | Continue maintenance anticonvulsant therapy with levetiracetam and phenytoin. | Phenytoin is currently being given. | presupposed by an action | The records mention phenytoin via a lab value and treatment documentation, but there is no administration record (e.g., MAR Administered, Given, or Infusion) for phenytoin within 24 hours of the decision time. Therefore, the statement that it is currently being given is not supported. |
| E2757707 | Continue pressure support ventilation with current settings and begin gradual weaning as tolerated. | The patient is currently on pressure support ventilation. | presupposed by an action | The only record mentioning pressure support is R18, which shows a Pressure Support value of 10 at 02:25 on 2100-01-02. This is a single measurement from over 20 hours before the decision time and does not establish that the patient is currently on pressure support ventilation at 23:07. |
| E2814579 | Titrate norepinephrine infusion to maintain a mean arterial pressure ≥65 mmHg. | Norepinephrine infusion is currently being given. | presupposed by an action | The only record of norepinephrine is an infusion documented at 13:00 on 2100-01-02, which is over 33 hours before the decision time of 22:47 on 2100-01-01. There is no administration record within the 24 hours prior to the decision time to support the statement that it is currently being given. |
| E2814579 | Continue pressure‑support ventilation and begin a spontaneous breathing trial to assess readiness for weaning. | The patient is currently on pressure-support ventilation. | presupposed by an action | The records show a Pressure Support measurement of 10 at 14:53 on 2100-01-02, but this is after the decision time of 22:47 on 2100-01-01. There is no record of pressure-support ventilation at or before the decision time. |
| E2879373 | Continue intravenous furosemide infusion to maintain diuresis and manage congestive heart failure. | Intravenous furosemide infusion is currently being given. | presupposed by an action | The records mention IV furosemide only as a treatment documented at 10:19 on 2100-01-01, which is after the decision time of 09:35. There is no administration record of furosemide in the 24 hours before the decision time, so the statement that it is currently being given is not supported. |
| E3001552 | Transition from non‑invasive ventilation to high‑flow nasal cannula and monitor respiratory status. | The patient is currently on non-invasive ventilation. | presupposed by an action | The records document non-invasive ventilation as a treatment, but the most recent relevant rows (R38, R45, R49) show oxygen flow rates without any ventilator settings or device confirmation at the decision time. The statement that the patient is currently on non-invasive ventilation is therefore not supported by the latest records. |
| E3001552 | Continue current broad‑spectrum antibacterial therapy and reassess culture results in 48 hours. | Broad-spectrum antibacterial therapy is currently being given. | presupposed by an action | The records document 'antibacterials' as a treatment category, but there is no medication administration record for any specific antibacterial drug in the 24 hours before the decision time. Therefore, the statement that broad-spectrum antibacterial therapy is currently being given is not supported by evidence of actual administration. |
| E3053511 | Continue non‑invasive positive pressure ventilation (BiPAP) to support respiratory status. | The patient is currently on non-invasive positive pressure ventilation (BiPAP). | presupposed by an action | The records document oxygen therapy (<40%) but do not mention BiPAP or non-invasive positive pressure ventilation. Oxygen therapy alone does not establish that the patient is on BiPAP. |
| E3067309 | Obtain arterial blood gas to reassess acid‑base status and oxygenation after recent FiO₂ increase. | FiO2 was recently increased. | stated outright | The most recent FiO2 values before the decision time show a decrease from 60% at 10:44 to 50% at 11:30, not an increase. Earlier values were higher, but the latest trend contradicts the statement. |
| E3110594 | Gradually wean norepinephrine infusion while closely monitoring mean arterial pressure. | Norepinephrine infusion is currently being given. | presupposed by an action | The records show norepinephrine infusions that ended at 04:00 on 2100-01-01, but no administration or 'Running at decision time' record within 24 hours before the decision time of 2100-01-02 01:02:00. Therefore, the statement that it is currently being given is not supported. |
| E3115505 | Continue scheduled inhaled albuterol therapy via nebulizer as ordered. | Scheduled inhaled albuterol therapy via nebulizer is currently being given. | presupposed by an action | The records show albuterol orders and administrations, but none specify delivery via nebulizer. The available albuterol records include concentrated solution and inhalation forms, but the route of administration is not documented as nebulizer. |
| E3124669 | Continue intravenous sodium bicarbonate infusion to enhance salicylate alkalinization. | Intravenous sodium bicarbonate infusion is currently being given. | presupposed by an action | The records document sodium bicarbonate as a treatment for salicylate toxicity, but there is no medication order or administration record showing an intravenous sodium bicarbonate infusion was being given at the decision time. The treatment documentation alone does not confirm active administration. |
| E3150018 | Continue scheduled antipsychotic (haloperidol) for agitation management. | Haloperidol is currently being given. | presupposed by an action | The records document haloperidol (haldol) as a treatment for agitation, but they do not show an administration record within 24 hours before the decision time. Documentation of a treatment does not confirm it is currently being given. |
| E3170528 | Continue intermittent pneumatic compression for VTE prophylaxis. | Intermittent pneumatic compression is currently being given. | presupposed by an action | The records document 'compression boots' as a treatment for VTE prophylaxis (R19), but there is no administration record or 'Running at decision time' entry showing intermittent pneumatic compression is currently being given at the decision time. |
| E3170528 | Monitor blood pressure closely and titrate nicardipine infusion to maintain mean arterial pressure between 80-100 mmHg. | Nicardipine infusion is currently being given. | presupposed by an action | The records mention nicardipine only as a treatment documented for ICH/cerebral infarct (R14), but there is no medication order or administration record showing a nicardipine infusion was being given at the decision time. |
| E3178242 | Increase norepinephrine infusion rate to target a mean arterial pressure ≥65 mmHg. | Norepinephrine is currently being given. | presupposed by an action | The only norepinephrine record is R14, which shows the infusion started at 08:00 on 2100-01-01, after the decision time of 07:26. There is no administration record of norepinephrine in the 24 hours before the decision time, so the statement that it is currently being given is not supported. |
| E3178242 | Continue current mechanical ventilation settings and reassess readiness for spontaneous breathing trial in 12 hours. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 7.4 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E3205786 | Continue low‑dose intravenous fluid bolus of 0.9% sodium chloride to maintain euvolemia and support blood pressure. | Low-dose intravenous fluid bolus of 0.9% sodium chloride is currently being given. | presupposed by an action | The statement claims a low-dose intravenous fluid bolus of 0.9% sodium chloride is currently being given. The only 0.9% sodium chloride IV bolus order (R8) was stopped at 22:11, before the decision time of 22:25. The continuous 0.9% sodium chloride infusion (R26) started at 23:00, after the decision time, and is not a bolus. |
| E3205786 | Maintain current nasal cannula oxygen at 2 L/min and reassess SpO₂ in 2 hours; consider weaning to room air if SpO₂ remains ≥94% on 21% FiO₂. | The patient is currently on nasal cannula oxygen at 2 L/min. | presupposed by an action | The records do not show nasal cannula oxygen at 2 L/min at the decision time. The most recent flow measurement before the decision time is 4 L/min (R22), and the nasal cannula documentation (R27) occurs after the decision time. The 2 L/min flow (R25) is also recorded after the decision time. |
| E3220742 | Continue scheduled levetiracetam for seizure prophylaxis. | Levetiracetam is currently being given. | presupposed by an action | The records show a levetiracetam administration that ended at 11:47 on 2100-01-01, which is over 14 hours before the decision time of 02:33 on 2100-01-02. There is no administration record for levetiracetam within the 24 hours prior to the decision time, so the statement that it is 'currently being given' is not supported. |
| E3223097 | Continue octreotide infusion at 50 mcg/hour for variceal bleeding control. | Variceal bleeding is present. | clinical judgment | The records show an admission diagnosis of 'Bleeding, upper GI' and treatment with octreotide 'for varices', but they do not explicitly state or directly confirm that the bleeding is variceal in origin. The diagnosis of variceal bleeding is not documented. |
| E3223097 | Administer a bolus of isotonic crystalloid (e.g., 500 mL normal saline) to address persistent hypotension (SBP ≈ 85‑95 mmHg). | SBP is 85-95 mmHg. | stated outright | The most recent systolic blood pressure readings before the decision time are 94 mmHg (R49), 104 mmHg (R47), and 88 mmHg (R45). The statement claims SBP is 85-95 mmHg, but the latest value of 104 mmHg is outside this range, so the records do not fully support the claim. |
| E3233620 | Obtain a chest radiograph to assess for postoperative pulmonary complications given diminished breath sounds and persistent cough. | Cough is persistent. | stated outright | The most recent cough assessment before the decision time (R49, 13:21) describes the cough as 'Loose non-productive', which does not support the statement that the cough is 'persistent'. Earlier records show intermittent coughs and periods of no cough. |
| E3233620 | Continue broad‑spectrum intravenous antibiotics and obtain repeat blood cultures to monitor for ongoing infection indicated by leukocytosis. | Broad-spectrum intravenous antibiotics are currently being given. | presupposed by an action | The records document antibiotic treatment (e.g., 'Treatment documented: gastrointestinal / medications / antibiotics' and 'therapeutic antibacterials'), but there is no medication order or administration record for a specific intravenous antibiotic. The only IV administration records are for Lactated Ringer's, esomeprazole, and morphine, none of which are antibiotics. |
| E3233620 | Maintain current analgesic regimen and reassess pain score in 1 hour; if pain remains ≥4, consider titrating morphine IV push per PRN order. | An analgesic regimen is currently being given. | presupposed by an action | The records show a morphine order (R2) and a single administration over 24 hours before the decision time (R1), but no analgesic administration in the 24 hours immediately preceding the decision time. Treatment documentation mentions analgesics (R12, R29, R43), but this does not confirm current administration. |

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
| E297175 | 3 | 33.3% | 0.0% | 66.7% | 0.0% | 50.0% | - | - |
| E322290 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E375854 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E383358 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 50.0% | - | - |
| E395323 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E405746 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E454584 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 33.3% | - | - |
| E467819 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E490454 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 50.0% | - | - |
| E521456 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 100.0% | - | - |
| E664474 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E733082 | 4 | 25.0% | 50.0% | 25.0% | 0.0% | 0.0% | - | - |
| E756295 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E758325 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E826669 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E850469 | 3 | 0.0% | 66.7% | 33.3% | 0.0% | 0.0% | - | - |
| E876429 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | - | - | - |
| E899746 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E942382 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E962227 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E978037 | 3 | 0.0% | 66.7% | 33.3% | 0.0% | 0.0% | - | - |
| E1056063 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1057910 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1057967 | 0 | - | - | - | - | 0.0% | - | - |
| E1064283 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1065859 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1068212 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071224 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1071450 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1090039 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1090889 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1099398 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | - | - |
| E1117947 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 50.0% | - | - |
| E1121034 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 33.3% | - | - |
| E1171473 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1173453 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1177589 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1287791 | 3 | 33.3% | 33.3% | 33.3% | 0.0% | 0.0% | - | - |
| E1290248 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1449360 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
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
| E1823727 | 4 | 50.0% | 25.0% | 25.0% | 0.0% | 0.0% | - | - |
| E1824650 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 33.3% | - | - |
| E1829278 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1837964 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1853162 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1856821 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E2230341 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | - | - | - |
| E2309912 | 5 | 40.0% | 20.0% | 40.0% | 0.0% | - | - | - |
| E2418055 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E2419768 | 0 | - | - | - | - | - | - | - |
| E2558122 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E2609672 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2714303 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E2725629 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 0.0% | - | - |
| E2757707 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E2814579 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 33.3% | - | - |
| E2860378 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2879373 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E3001552 | 4 | 25.0% | 50.0% | 25.0% | 0.0% | 50.0% | - | - |
| E3027283 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E3033795 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3035113 | 4 | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | - | - |
| E3053511 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E3067309 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 100.0% | - | - |
| E3110594 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E3111371 | 2 | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | - | - |
| E3112232 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3115505 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3124669 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3130379 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E3148216 | 0 | - | - | - | - | 0.0% | - | - |
| E3150018 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E3152779 | 4 | 25.0% | 0.0% | 75.0% | 0.0% | 0.0% | - | - |
| E3170528 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E3178242 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3205786 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3220742 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3223097 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E3233620 | 5 | 40.0% | 60.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3237226 | 2 | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | - | - |
