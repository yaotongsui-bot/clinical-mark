# Evaluation of AI clinical suggestions against patient records

- Input: `eicu_triples_gpt-oss-120b.json`; 100 cases, 3.0 AI suggestions per case on average.
- Models: atomizer `deepseek-v4-pro:0813:cloud`; judge panel `deepseek-v4-pro:0813:cloud`, `minimax-m3.1-flash:cloud`, `glm-5.3:cloud` (majority vote; reasoning mode: none); 468 new model calls, 72 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 20.1% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 262 |
| supported / not_supported / not_addressed / unverifiable | 155 / 72 / 35 / 0 |
| Fact accuracy = supported / (supported + not_supported) | 68.3% |
| Cases with at least one not_supported fact | 56 / 100 |
| Omitted findings: abnormalities the clinicians treated that no AI fact mentions | 0 / 0 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 73 | 85.7% | {'supported': 60, 'not_supported': 10, 'not_addressed': 3} |
| presupposed by an action | 170 | 60.6% | {'supported': 86, 'not_supported': 56, 'not_addressed': 28} |
| clinical judgment | 19 | 60.0% | {'supported': 9, 'not_addressed': 4, 'not_supported': 6} |
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
| E172015 | Continue PRN lorazepam dosing for alcohol withdrawal symptom control. | PRN lorazepam is currently being given. | presupposed by an action | The records show PRN lorazepam orders (R4, R16, R17) and a single dose given on 2099-12-31 (R2), but no lorazepam administration in the 24 hours before the decision time of 2100-01-02 23:52. Therefore, the statement that PRN lorazepam is currently being given is not supported. |
| E184757 | Start intravenous labetalol infusion for persistent hypertension (SBP 148‑184 mmHg). | SBP is 148-184 mmHg. | stated outright | The records report MAP values, not systolic blood pressure (SBP), so they do not support an SBP range of 148–184 mmHg. |
| E284265 | Continue intravenous diltiazem infusion at the current rate and monitor blood pressure and heart rate q1h. | Intravenous diltiazem infusion is currently being given. | presupposed by an action | The only administration record for diltiazem (R14) shows an infusion that ended at 05:00 on 2100-01-02, which is more than 24 hours before the decision time of 18:11. No 'Running at decision time' record or recent administration within 24 hours supports the statement that it is currently being given. |
| E375854 | Continue intravenous meropenem therapy for broad‑spectrum coverage of possible intra‑abdominal infection. | Intravenous meropenem therapy is currently being given. | presupposed by an action | The records document meropenem as a treatment (R32), but there is no medication order or administration record showing that intravenous meropenem was actively being given at the decision time. |
| E375854 | Continue intravenous meropenem therapy for broad‑spectrum coverage of possible intra‑abdominal infection. | Possible intra-abdominal infection is present. | clinical judgment | The records show consultations for infectious disease, gastroenterology, and surgery, and a GI bleeding diagnosis, but they do not state an intra-abdominal infection. The temperature measurements are all normal, which does not support the presence of an infection. |
| E383358 | Check INR in 12 hours and adjust warfarin (coumadin) dosing to keep INR within therapeutic range (2.0‑3.0). | Warfarin (coumadin) is currently being given. | presupposed by an action | The records document coumadin (warfarin) as a treatment, but there is no medication order or administration record showing warfarin was given within 24 hours before the decision time. Treatment documentation alone does not confirm current administration. |
| E454584 | Check bedside glucose hourly and adjust sliding‑scale insulin infusion to maintain glucose 80‑140 mg/dL. | Insulin infusion is currently being given. | presupposed by an action | The records show subcutaneous insulin (NovoLOG Flexpen) and documented subcutaneous/sliding-scale insulin administration, but no record of an insulin infusion being given at or near the decision time. |
| E467819 | Continue intravenous nicardipine infusion with titration to maintain mean arterial pressure ≥65 mmHg. | Nicardipine infusion is currently being given. | presupposed by an action | The most recent nicardipine administration record (R50) ended at 00:00 on 2100-01-02, which is more than 1 hour and 43 minutes before the decision time of 01:43. There is no administration record within the 24 hours before the decision time showing the infusion was running at that moment. |
| E490454 | Continue non‑invasive ventilation with BiPAP and titrate FiO₂ to maintain SpO₂ ≥ 92 % while monitoring for respiratory fatigue. | The patient is currently on non-invasive ventilation with BiPAP. | presupposed by an action | The records document non-invasive ventilation via face mask, but do not mention BiPAP specifically. Therefore, the statement that the patient is on BiPAP is not supported by the available records. |
| E521456 | Continue volume‑controlled mechanical ventilation with tidal volume 6‑8 mL/kg, FiO₂ 65‑70 % and PEEP 5‑7 cmH₂O. | Tidal volume is 6-8 mL/kg. | stated outright | The records show a set tidal volume of 300 mL with a TV/kg IBW of 4.3871, which is below the stated 6-8 mL/kg range. The documented treatment note (R16) mentions a target of 6-10 ml/kg, but the actual recorded values do not support the specific 6-8 mL/kg claim. |
| E733082 | Administer a 500 mL crystalloid bolus to support borderline mean arterial pressure and improve tissue perfusion. | Mean arterial pressure is borderline. | stated outright | The most recent mean arterial pressures before the decision time are 75, 78, and 82 mmHg, which are within normal range, not borderline low. The statement that MAP is borderline is not supported by the latest recorded values. |
| E758325 | Obtain a repeat complete blood count in 6 hours to reassess platelet trend. | Platelet trend is being reassessed. | presupposed by an action | The records show a platelet count of 130 K/MM3 on 2100-01-01 and 90 K/MM3 on 2100-01-02, indicating a decreasing trend, not a reassessment or stable trend. The statement 'Platelet trend is being reassessed' is not directly supported by these values. |
| E876429 | Begin gradual weaning of epinephrine and phenylephrine infusions as mean arterial pressure stabilizes above 65 mmHg with adequate cardiac output. | Phenylephrine infusion is currently being given. | presupposed by an action | The records show phenylephrine infusions that ended at 13:00 on 2100-01-02, but no administration is documented in the 24 hours before the decision time of 2100-01-02 19:53. Therefore, the statement that phenylephrine is currently being given is not supported. |
| E876429 | Assess readiness for spontaneous breathing trial and consider extubation if mental status improves (GCS ≥ 13) and ventilatory parameters remain stable. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 8.4 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E942382 | Continue the IV diltiazem infusion to maintain rate control of atrial arrhythmia. | IV diltiazem infusion is currently being given. | presupposed by an action | The only diltiazem administration record is an infusion that started and ended at 17:04 on 2100-01-01, which is more than 24 hours before the decision time of 2100-01-02 15:23. There is no record of a diltiazem infusion running at the decision time. |
| E962227 | Continue daily hemodialysis and monitor serum electrolytes (potassium, bicarbonate) each shift. | The patient is currently on hemodialysis. | presupposed by an action | The records document hemodialysis as a treatment (R35), but there is no administration record showing the patient is currently receiving hemodialysis at the decision time. |
| E978037 | Obtain repeat hemoglobin and hematocrit in 2 hours to assess ongoing bleeding | Ongoing bleeding is present. | clinical judgment | The records document an admission diagnosis of lower GI bleeding, but they do not explicitly state that bleeding was ongoing at the decision time. |
| E1056063 | Maintain therapeutic enoxaparin dosing and schedule the next subcutaneous dose per protocol. | Enoxaparin is currently being given. | presupposed by an action | The only enoxaparin record is an administration at 14:00 on 2100-01-01, which is more than 24 hours before the decision time of 2100-01-02 10:15. There is no administration record in the 24 hours before the decision time, so the statement that enoxaparin is currently being given is not supported. |
| E1057910 | Continue norepinephrine infusion and titrate to maintain MAP ≥65 mmHg. | Norepinephrine infusion is currently being given. | presupposed by an action | The norepinephrine infusion documented in R1 ended at 15:32 on 2100-01-01, and R26 only documents treatment with norepinephrine at 07:10. There is no administration record of norepinephrine in the 24 hours before the decision time (2100-01-02 05:25), so the statement that it is currently being given is not supported. |
| E1064283 | Continue IV nicardipine infusion to maintain systolic blood pressure < 150 mmHg. | IV nicardipine infusion is currently being given. | presupposed by an action | The records mention nicardipine only as a treatment documented at 02:32 on 2100-01-02, but there is no administration record or 'Running at decision time' entry for an IV nicardipine infusion. Therefore, the statement that it is currently being given is not supported. |
| E1071450 | Continue milrinone infusion for inotropic support. | Milrinone infusion is currently being given. | presupposed by an action | The records mention milrinone only as a treatment documented for shock (R28), but there is no medication order or administration record showing that a milrinone infusion is currently being given. |
| E1071450 | Monitor capillary glucose q4h and adjust insulin aspart dosing per protocol. | Insulin aspart is currently being given. | presupposed by an action | The records show a 'Running at decision time' administration of insulin aspart corrective dosing (R28), but this is a scheduled order that started on 2099-12-31 21:30, not an administration within 24 hours of the decision time (2100-01-02 02:00). No administration of insulin aspart is recorded in the 24 hours before the decision time. |
| E1099398 | Continue intravenous antihistamine infusion for ongoing anaphylaxis management. | Anaphylaxis is ongoing. | clinical judgment | The records show an admission diagnosis of anaphylaxis, but there are no current signs, symptoms, or treatments indicating that anaphylaxis is ongoing at the decision time. The vital signs and laboratory values do not directly demonstrate an active anaphylactic reaction. |
| E1171473 | Continue mechanical ventilation with current settings and assess readiness for weaning in the next 4–6 hours. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('Tidal Volume (set): 500 mL') was 6.8 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1173453 | Continue current broad‑spectrum antibiotic regimen and reassess culture results for potential de‑escalation. | Broad-spectrum antibiotics are currently being given. | presupposed by an action | The records document vancomycin as a treatment, but there is no administration record showing that broad-spectrum antibiotics are currently being given at the decision time. |
| E1177589 | Continue hourly point‑of‑care glucose monitoring to detect recurrent hypoglycemia. | Hourly point-of-care glucose monitoring is currently being performed. | presupposed by an action | The records show glucose finger sticks at 20:59 and 01:21, but no glucose measurement at the decision time of 21:00 and no order or documentation of hourly point-of-care glucose monitoring. The available measurements do not demonstrate that hourly monitoring is currently being performed. |
| E1177589 | Maintain nasal cannula oxygen at 2 L/min and reassess FiO₂ and saturation q2h. | Nasal cannula oxygen is currently being given at 2 L/min. | presupposed by an action | The latest charted nasal-cannula delivery device was the prior day, while the most recent oxygen-related record shows only 21% O2 without specifying the device. No record confirms nasal-cannula oxygen at 2 L/min at the decision time. |
| E1287791 | Continue the mannitol continuous infusion to manage intracranial pressure. | Mannitol continuous infusion is currently being given. | presupposed by an action | The records mention mannitol as a continuous infusion in a treatment documentation note (R18), but there is no administration record showing that mannitol is currently being given at the decision time. |
| E1449360 | Order a short‑acting antihypertensive (e.g., labetalol IV) to maintain systolic blood pressure <140 mmHg given persistent elevations. | Systolic blood pressure is persistently elevated. | stated outright | Median systolic BP over the 6 h before the decision: 134 mmHg (7 readings), normal by the rule 'hypotension SBP < 90; hypertension SBP > 140'. |
| E1588473 | Obtain a platelet transfusion given platelet count of 109 ×10³/µL and ongoing hypotension. | Hypotension is ongoing. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1619343 | Continue intravenous regular insulin infusion with hourly glucose checks to target glucose 140-180 mg/dL. | The patient is currently receiving intravenous regular insulin infusion. | presupposed by an action | The records document a treatment of 'insulin / continuous infusion' at 06:48, but there is no medication administration record showing an intravenous insulin infusion running at the decision time or within the prior 24 hours. The only running IV medications are normal saline, ondansetron, vancomycin, and metoclopramide. |
| E1653043 | Continue therapeutic anticoagulation with intravenous heparin and monitor PTT q6h. | The patient is currently receiving intravenous heparin. | presupposed by an action | The records document 'conventional heparin therapy / intravenous' at 07:45 on 2100-01-02, but there is no administration record of intravenous heparin within 24 hours before the decision time (2100-01-02 21:00). The only running IV medication is sodium chloride. |
| E1653043 | Order repeat lower extremity duplex ultrasound to assess for DVT progression. | DVT is present. | presupposed by an action | The records document that non-invasive testing for DVT was performed, but they do not state that DVT is present. The statement 'DVT is present' is a diagnosis not supported by the available records. |
| E1653043 | Maintain current oxygen supplementation at 2 L/min via nasal cannula and reassess SpO₂ q4h. | The patient is currently receiving oxygen supplementation at 2 L/min via nasal cannula. | presupposed by an action | The most recent record shows oxygen at 2 L/min within 24 hours, but no supplied record identifies the delivery device as a nasal cannula. |
| E1672915 | Start norepinephrine infusion to maintain MAP ≥65 mmHg given persistent tachycardia, hypertension, and signs of septic shock. | Septic shock is present. | clinical judgment | The records show an admission diagnosis of 'Sepsis, unknown' but do not document septic shock. Septic shock requires evidence of hypotension or organ hypoperfusion, which is not present in the provided records. |
| E1674875 | Initiate norepinephrine infusion to support mean arterial pressure. | Mean arterial pressure is low. | presupposed by an action | Median mean arterial pressure over the 6 h before the decision: 65 mmHg (6 readings), normal by the rule 'hypotension MAP < 65'. |
| E1674875 | Continue low tidal volume ventilation strategy for ARDS. | The patient is currently on low tidal volume ventilation. | presupposed by an action | The records mention CPAP/PEEP therapy, but there is no record of low tidal volume ventilation or any ventilator setting indicating tidal volume. The statement about being on low tidal volume ventilation is therefore not supported. |
| E1682105 | Titrate intravenous labetalol or add a short‑acting vasodilator to maintain mean arterial pressure >65 mmHg given fluctuating hypotension and hypertension. | Hypotension is fluctuating. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1682105 | Titrate intravenous labetalol or add a short‑acting vasodilator to maintain mean arterial pressure >65 mmHg given fluctuating hypotension and hypertension. | Hypertension is fluctuating. | stated outright | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E1705630 | Continue intravenous potassium chloride infusion to correct persistent hypokalemia (K⁺ 3.2‑3.3 mmol/L). | Persistent hypokalemia is present. | stated outright | Latest potassium 3.9 mmol/L at 2100-01-02 17:35:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E1705630 | Monitor blood pressure closely and titrate IV labetalol infusion to maintain MAP < 100 mmHg given sustained systolic pressures 150‑170 mmHg. | IV labetalol infusion is currently being given. | presupposed by an action | The records show labetalol was given as one-time intravenous doses at 17:20 and 20:05, but there is no administration record of a continuous labetalol infusion running at the decision time. The active order is for PRN dosing, not a continuous infusion. |
| E1790816 | Continue intravenous heparin infusion per current dosing and monitor activated partial thromboplastin time (aPTT) q6h. | Intravenous heparin infusion is currently being given. | presupposed by an action | The records show a subcutaneous (SC) heparin order, not an intravenous (IV) infusion. No IV heparin administration is documented. |
| E1823356 | Continue intravenous insulin infusion at the current rate and monitor bedside glucose every hour. | Intravenous insulin infusion is currently being given. | presupposed by an action | The records show an intravenous insulin infusion (R5, R11) that ended at 20:53, before the decision time of 21:00. At the decision time, the only running insulin is a subcutaneous lispro order (R47), not an intravenous infusion. |
| E1824650 | Continue ventilator weaning and transition to spontaneous breathing trials. | The patient is currently on mechanical ventilation. | presupposed by an action | The latest record before the decision (2100-01-02 15:35:00) reads 'O2 Delivery Device(s): None (charted: RA)'. |
| E1829278 | Continue nicardipine infusion with titration to maintain mean arterial pressure between 65-75 mmHg. | Nicardipine infusion is currently being given. | presupposed by an action | The records show a Nicardipine infusion that ran from 03:00 to 08:24 on 2100-01-02, but there is no record of it running at the decision time of 2100-01-02 08:43. The infusion ended before the decision time, so the statement that it is currently being given is not supported. |
| E1837964 | Continue intravenous diuretic therapy and monitor daily weight and electrolytes. | Intravenous diuretic therapy is currently being given. | presupposed by an action | The records show a one-time IV furosemide dose at 14:15 on 2100-01-01 (R1) and a treatment documentation of 'intravenous diuretic' (R15), but no IV diuretic administration within 24 hours before the decision time. The most recent furosemide administrations are oral (R26, R45), so the statement that IV diuretic therapy is currently being given is not supported. |
| E1853162 | Continue scheduled nebulized ipratropium‑albuterol (3 mL q4h PRN) to maintain bronchodilation. | Scheduled nebulized ipratropium-albuterol is currently being given. | presupposed by an action | The records show a one-time administration of ipratropium-albuterol at 09:30 (R3) and an active PRN order (R23), but no administration of the nebulized medication within 24 hours before the decision time. Therefore, the statement that it is 'currently being given' is not supported. |
| E1856821 | Start stress‑dose hydrocortisone 50 mg IV q6h for possible refractory septic shock. | Refractory septic shock is possible. | clinical judgment | The records document septic shock requiring norepinephrine, but the most recent blood pressure (R49) is 120 mmHg while on norepinephrine, which does not indicate refractory shock. The statement of 'possible refractory septic shock' is not directly supported by the recorded values. |
| E2230341 | Continue eptifibatide infusion at the current rate and monitor for bleeding complications. | Eptifibatide infusion is currently being given. | presupposed by an action | Eptifibatide infusions are recorded only earlier on 2100-01-02, with the latest infusion ending at 09:05, and no record shows it running at the decision time of 14:38. |
| E2230341 | Monitor platelet count and hemoglobin every 6 hours while on the glycoprotein IIb/IIIa inhibitor. | The patient is currently on a glycoprotein IIb/IIIa inhibitor. | presupposed by an action | Eptifibatide, a glycoprotein IIb/IIIa inhibitor, was infused only until 09:05, and no record shows it was running or administered at the 14:38 decision time. |
| E2558122 | Continue non‑invasive positive pressure ventilation (BiPAP) to support oxygenation. | The patient is currently on non-invasive positive pressure ventilation (BiPAP). | presupposed by an action | The most recent respiratory support record (R33) documents oxygen therapy via nasal cannula, not non-invasive positive pressure ventilation (BiPAP). No BiPAP or NIPPV administration is recorded. |
| E2714303 | Continue maintenance anticonvulsant therapy with levetiracetam and phenytoin. | Levetiracetam is currently being given. | presupposed by an action | The records document levetiracetam as a treatment (R33), but there is no administration record showing it was given in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E2714303 | Continue maintenance anticonvulsant therapy with levetiracetam and phenytoin. | Phenytoin is currently being given. | presupposed by an action | The records document phenytoin as a treatment for seizure therapy, but there is no administration record showing it was given in the 24 hours before the decision time. A treatment documentation alone does not confirm current administration. |
| E2757707 | Continue pressure support ventilation with current settings and begin gradual weaning as tolerated. | The patient is currently on pressure support ventilation. | presupposed by an action | The only record mentioning pressure support is R18, which shows a Pressure Support setting of 10 at 02:25 on 2100-01-02. There is no record of pressure support ventilation at the decision time (2100-01-02 23:07), so the statement that the patient is currently on pressure support ventilation is not supported. |
| E2814579 | Titrate norepinephrine infusion to maintain a mean arterial pressure ≥65 mmHg. | Norepinephrine infusion is currently being given. | presupposed by an action | The only record of norepinephrine is an infusion at 13:00 on 2100-01-02, which is more than 24 hours before the decision time of 2100-01-01 21:00. There is no administration record within the 24 hours prior to the decision time. |
| E2860378 | Continue intravenous insulin infusion with titration to maintain glucose 140-180 mg/dL. | Intravenous insulin infusion is currently being given. | presupposed by an action | The last documented insulin infusion ran until 2100-01-02 02:30, and the subsequent infusion record has zero duration. No record shows an intravenous insulin infusion running at the 14:07 decision time. |
| E2879373 | Continue intravenous furosemide infusion to maintain diuresis and manage congestive heart failure. | Intravenous furosemide infusion is currently being given. | presupposed by an action | The records document IV furosemide as a treatment, but there is no administration record showing it was given in the 24 hours before the decision time. A treatment documentation alone does not confirm current administration. |
| E3001552 | Transition from non‑invasive ventilation to high‑flow nasal cannula and monitor respiratory status. | The patient is currently on non-invasive ventilation. | presupposed by an action | Non-invasive ventilation was documented as recently as 2100-01-01 at 14:02, but no administration or ongoing record confirms it was still being received at the decision time; the only running therapy is a saline infusion. |
| E3001552 | Continue current broad‑spectrum antibacterial therapy and reassess culture results in 48 hours. | Broad-spectrum antibacterial therapy is currently being given. | presupposed by an action | The records document antibacterial treatment (R26, R33, R40), but there is no medication administration record for any antibacterial agent in the 24 hours before the decision time. Therefore, the statement that broad-spectrum antibacterial therapy is currently being given is not supported. |
| E3067309 | Obtain arterial blood gas to reassess acid‑base status and oxygenation after recent FiO₂ increase. | FiO2 was recently increased. | stated outright | The records show FiO2 was 100% at 10:34, then decreased to 50% by 16:55 and 40% by 18:20. It was later increased to 60% at 23:38, but the most recent value before the decision time is 50% at 11:30, which is not an increase from the prior 60%. |
| E3110594 | Gradually wean norepinephrine infusion while closely monitoring mean arterial pressure. | Norepinephrine infusion is currently being given. | presupposed by an action | The records show norepinephrine infusions that ended at 04:00 on 2100-01-01, with no administration or 'Running at decision time' record for norepinephrine in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E3112232 | Continue scheduled thiamine supplementation (Thiamine HCl PO daily) to address potential deficiency in the setting of alcohol withdrawal. | Thiamine deficiency is potential in the setting of alcohol withdrawal. | clinical judgment | The records show an ethanol level and a drug withdrawal admission diagnosis, but do not establish alcohol withdrawal or thiamine deficiency. Thiamine is being administered, which does not itself support the stated rationale. |
| E3124669 | Continue intravenous sodium bicarbonate infusion to enhance salicylate alkalinization. | Intravenous sodium bicarbonate infusion is currently being given. | presupposed by an action | The records document sodium bicarbonate as a treatment for salicylate toxicity, but there is no administration record of an intravenous sodium bicarbonate infusion at or near the decision time. The treatment documentation alone does not confirm that the infusion is currently being given. |
| E3170528 | Continue intermittent pneumatic compression for VTE prophylaxis. | Intermittent pneumatic compression is currently being given. | presupposed by an action | The records document that compression boots were part of the VTE prophylaxis treatment plan, but there is no administration record showing that intermittent pneumatic compression is currently being given at the decision time. |
| E3170528 | Monitor blood pressure closely and titrate nicardipine infusion to maintain mean arterial pressure between 80-100 mmHg. | Nicardipine infusion is currently being given. | presupposed by an action | The records mention nicardipine only as a documented treatment for ICH/cerebral infarct, but there is no medication order or administration record showing a nicardipine infusion was actively running at the decision time. |
| E3178242 | Continue current mechanical ventilation settings and reassess readiness for spontaneous breathing trial in 12 hours. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 7.4 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E3205786 | Continue low‑dose intravenous fluid bolus of 0.9% sodium chloride to maintain euvolemia and support blood pressure. | Low-dose intravenous fluid bolus of 0.9% sodium chloride is currently being given. | presupposed by an action | The statement claims a low-dose 0.9% sodium chloride IV bolus is being given to maintain euvolemia and support blood pressure. The records show an order for a 0.9% sodium chloride IV bolus (R8) and a continuous infusion of lactated ringers (R12), but no administration of a 0.9% sodium chloride bolus; the only 0.9% sodium chloride administration is a continuous infusion (R26), not a bolus. |
| E3205786 | Maintain current nasal cannula oxygen at 2 L/min and reassess SpO₂ in 2 hours; consider weaning to room air if SpO₂ remains ≥94% on 21% FiO₂. | The patient is currently on nasal cannula oxygen at 2 L/min. | presupposed by an action | The records show an O2 flow of 4 L/min at 22:29 and 2 L/min at 23:06, but no record of 2 L/min at the decision time of 21:00. The nasal cannula is documented at 00:16, but the flow rate at the decision time is not specified as 2 L/min. |
| E3220742 | Continue scheduled levetiracetam for seizure prophylaxis. | Levetiracetam is currently being given. | presupposed by an action | The records show a levetiracetam administration from 05:00 to 11:47 on 2100-01-01, but no administration within 24 hours before the decision time of 2100-01-02 02:33. Treatment documentation mentions levetiracetam, but that does not confirm it is currently being given. |
| E3233620 | Obtain a chest radiograph to assess for postoperative pulmonary complications given diminished breath sounds and persistent cough. | Cough is persistent. | stated outright | The most recent cough assessments before the decision time show 'No cough' at 05:06 and 'Loose non-productive' at 08:40 and 13:21, which do not support the statement that the cough is 'persistent'. |
| E3233620 | Continue broad‑spectrum intravenous antibiotics and obtain repeat blood cultures to monitor for ongoing infection indicated by leukocytosis. | Broad-spectrum intravenous antibiotics are currently being given. | presupposed by an action | The records document antibiotics as a treatment category (e.g., 'therapeutic antibacterials') but contain no medication order or administration record for a specific intravenous antibiotic at or near the decision time. Therefore, the claim that broad-spectrum IV antibiotics are currently being given is not supported by administration data. |
| E3233620 | Maintain current analgesic regimen and reassess pain score in 1 hour; if pain remains ≥4, consider titrating morphine IV push per PRN order. | An analgesic regimen is currently being given. | presupposed by an action | The records show a one-time morphine administration at 07:18 and an active PRN morphine order, but no analgesic administration in the 24 hours before the decision time. Therefore, the statement that an analgesic regimen is currently being given is not supported. |

## 5. Judge panel

180 items went to the judge panel. Agreement: {'3/3': 123, '2/3': 56, 'split': 1} (split = no majority; the conservative label was used and the item needs human review).

## 6. Per-case score sheets

| Case | Facts | supported | not_supported | not_addressed | unverifiable | Treatment agreement | Vital recall | All recall |
|---|---|---|---|---|---|---|---|---|
| E153972 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E172015 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E184757 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E211144 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E284265 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E297175 | 3 | 33.3% | 0.0% | 66.7% | 0.0% | 50.0% | - | - |
| E322290 | 3 | 33.3% | 0.0% | 66.7% | 0.0% | 0.0% | - | - |
| E375854 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E383358 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 50.0% | - | - |
| E395323 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E405746 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E454584 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 33.3% | - | - |
| E467819 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E490454 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 50.0% | - | - |
| E521456 | 5 | 60.0% | 20.0% | 20.0% | 0.0% | 100.0% | - | - |
| E664474 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E733082 | 4 | 25.0% | 25.0% | 50.0% | 0.0% | 0.0% | - | - |
| E756295 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E758325 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 50.0% | - | - |
| E826669 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E850469 | 3 | 33.3% | 0.0% | 66.7% | 0.0% | 0.0% | - | - |
| E876429 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | - | - | - |
| E899746 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E942382 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E962227 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E978037 | 3 | 33.3% | 33.3% | 33.3% | 0.0% | 0.0% | - | - |
| E1056063 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1057910 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1057967 | 0 | - | - | - | - | 0.0% | - | - |
| E1064283 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1065859 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1068212 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071224 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1071450 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1090039 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1090889 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1099398 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | - | - |
| E1117947 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 50.0% | - | - |
| E1121034 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 33.3% | - | - |
| E1171473 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1173453 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1177589 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1287791 | 3 | 33.3% | 33.3% | 33.3% | 0.0% | 0.0% | - | - |
| E1290248 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1449360 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | - | - |
| E1496959 | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1497157 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 0.0% | - | - |
| E1588473 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1592666 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1619343 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1636307 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1653043 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1672915 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1674875 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1682105 | 6 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1705630 | 7 | 71.4% | 28.6% | 0.0% | 0.0% | 0.0% | - | - |
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
| E2230341 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E2309912 | 5 | 40.0% | 0.0% | 60.0% | 0.0% | - | - | - |
| E2418055 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E2419768 | 0 | - | - | - | - | - | - | - |
| E2558122 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E2609672 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2714303 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E2725629 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 0.0% | - | - |
| E2757707 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E2814579 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 33.3% | - | - |
| E2860378 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2879373 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E3001552 | 4 | 25.0% | 50.0% | 25.0% | 0.0% | 50.0% | - | - |
| E3027283 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E3033795 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3035113 | 4 | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | - | - |
| E3053511 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 0.0% | - | - |
| E3067309 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 100.0% | - | - |
| E3110594 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E3111371 | 2 | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | - | - |
| E3112232 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3115505 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3124669 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3130379 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E3148216 | 0 | - | - | - | - | 0.0% | - | - |
| E3150018 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 0.0% | - | - |
| E3152779 | 4 | 25.0% | 0.0% | 75.0% | 0.0% | 0.0% | - | - |
| E3170528 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E3178242 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3205786 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3220742 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3223097 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3233620 | 5 | 40.0% | 60.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3237226 | 2 | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | - | - |
