# Evaluation of AI clinical suggestions against patient records

- Input: `eicu_triples_qwen2.5-7b.json`; 100 cases, 2.99 AI suggestions per case on average.
- Models: atomizer `deepseek-v4-pro:0813:cloud`; judge panel `deepseek-v4-pro:0813:cloud` (majority vote; reasoning mode: none); 131 new model calls, 0 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 27.5% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 173 |
| supported / not_supported / not_addressed / unverifiable | 94 / 69 / 10 / 0 |
| Fact accuracy = supported / (supported + not_supported) | 57.7% |
| Cases with at least one not_supported fact | 52 / 100 |
| Omitted findings: abnormalities the clinicians treated that no AI fact mentions | 0 / 0 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 51 | 78.4% | {'supported': 40, 'not_supported': 11} |
| presupposed by an action | 110 | 47.5% | {'supported': 48, 'not_supported': 53, 'not_addressed': 9} |
| clinical judgment | 12 | 54.5% | {'supported': 6, 'not_supported': 5, 'not_addressed': 1} |
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
| E297175 | Monitor patient's respiratory status closely due to ongoing respiratory distress. | Respiratory distress is ongoing. | stated outright | The most recent respiratory rate before the decision time is 23 insp/min (R50), which is mildly elevated but not documented as respiratory distress. The records show treatments for pulmonary issues (e.g., bronchodilators, non-invasive ventilation) but no explicit diagnosis or ongoing distress is recorded. |
| E395323 | Continue vancomycin and piperacillin/tazobactam for suspected sepsis. | Vancomycin is currently being given. | presupposed by an action | The records document vancomycin as a treatment (R14), but there is no medication administration record showing vancomycin was given in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E395323 | Continue vancomycin and piperacillin/tazobactam for suspected sepsis. | Piperacillin/tazobactam is currently being given. | presupposed by an action | The records document piperacillin/tazobactam as a treatment (R13), but there is no medication administration record showing it was given in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E405746 | Continue labetalol for hypertension management. | Labetalol is currently being given. | presupposed by an action | The records show an active PRN order for labetalol (R10) and a treatment documentation entry (R34), but no administration record of labetalol being given in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E405746 | Continue labetalol for hypertension management. | Hypertension is present. | clinical judgment | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E467819 | Continue monitoring blood pressure and adjust nicardipine infusion as needed. | Nicardipine infusion is currently being given. | presupposed by an action | The most recent nicardipine administration record (R50) ended at 00:00 on 2100-01-02, more than 24 hours before the decision time of 01:43 on 2100-01-02. No administration record exists within the 24 hours prior to the decision time, so the statement that it is currently being given is not supported. |
| E467819 | Administer oral enalapril as ordered. | Oral enalapril is ordered. | presupposed by an action | The records document enalapril as a treatment for hypertension, but there is no medication order for oral enalapril. The statement that it is 'ordered' is therefore not supported. |
| E521456 | Continue mechanical ventilation with tidal volume 300 mL and PEEP 5 cmH2O. | PEEP is 5 cmH2O. | stated outright | The most recent PEEP records before the decision time show a setting of 7 cmH2O, not 5 cmH2O. Earlier records show 5 cmH2O, but the latest values contradict the statement. |
| E521456 | Administer 10 mL of magnesium sulfate intravenously for potential delirium. | Delirium is potentially present. | clinical judgment | The CAM-ICU delirium assessments at 21:00, 22:00, and 12:00 all record a Delirium Score of 'No', which directly contradicts the statement that delirium is potentially present. |
| E733082 | Monitor blood glucose levels closely due to recent high readings and risk of hypoglycemia. | There is a risk of hypoglycemia. | clinical judgment | The records show multiple glucose measurements, all of which are elevated (153-216 mg/dL), not low. There is no evidence of hypoglycemia or a risk of it; the data actually indicates hyperglycemia. |
| E733082 | Administer IV fluids to maintain adequate hydration and blood pressure support. | Hydration is inadequate. | presupposed by an action | The records show multiple IV fluid administrations (sodium chloride 0.9%) including one running at the decision time, indicating active hydration. Therefore, the statement that hydration is inadequate is not supported by the supplied records. |
| E733082 | Administer IV fluids to maintain adequate hydration and blood pressure support. | Blood pressure support is needed. | presupposed by an action | The records contain numerous blood pressure measurements, but none indicate hypotension requiring support. The systolic pressures range from 87 to 147 mmHg, with most values above 100 mmHg, and the most recent readings (R48-R50) are 104, 121, and 120 mmHg. Therefore, the statement that blood pressure support is needed is not supported by the recorded values. |
| E850469 | Continue aggressive fluid resuscitation to maintain adequate perfusion. | Aggressive fluid resuscitation is currently being given. | presupposed by an action | The records show a single 1000 mL normal saline bolus administered on 2100-01-01 at 12:27 and a treatment note for 'aggressive volume resuscitation (>250 mls/hr)' at 14:20, but no fluid administration is documented in the 24 hours before the decision time of 2100-01-02 13:47. Therefore, the statement that aggressive fluid resuscitation is currently being given is not supported. |
| E942382 | Continue the administration of diltiazem to manage the patient's heart rate and rhythm. | Diltiazem is currently being given. | presupposed by an action | The records mention diltiazem as a documented treatment (R16) and show a brief infusion at 17:04 on 2100-01-01 (R20), but there is no administration record within 24 hours before the decision time of 2100-01-02 15:23:00. Therefore, the statement that diltiazem is currently being given is not supported. |
| E1056063 | Continue oxygen therapy with nasal cannula at 2 L/min to maintain adequate oxygen saturation. | Oxygen therapy with nasal cannula at 2 L/min is currently being given. | presupposed by an action | The records document oxygen therapy via nasal cannula (R6) and an O2 flow of 2 L/min (R12), but the most recent flow measurement is from 2100-01-01 17:00, over 17 hours before the decision time. There is no administration or flow record within 24 hours of the decision time to confirm it is currently being given. |
| E1057967 | Monitor blood glucose levels closely given the patient's fluctuating readings and risk of sepsis. | Blood glucose readings are fluctuating. | stated outright | The blood glucose readings are relatively stable, ranging from 105 to 149 mg/dL, with no significant fluctuations. The values do not show a pattern of marked variability, so the statement that readings are fluctuating is not supported. |
| E1057967 | Continue pain management with PRN orders for Dilaudid IV, oxyCODONE PO, and Tylenol PO as needed. | Pain management is currently being given. | presupposed by an action | The records show PRN orders for Dilaudid, oxyCODONE, and Tylenol, and administrations of Dilaudid and acetaminophen earlier on 2100-01-02. However, there is no administration of any pain medication within the 24 hours before the decision time (2100-01-01 21:51), so the statement that pain management is 'currently being given' is not supported. |
| E1064283 | Administer potassium chloride PO to address low potassium levels. | Potassium is low. | stated outright | Latest potassium 4.1 mmol/L at 2100-01-02 10:38:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E1065859 | Monitor blood glucose levels closely due to persistent hyperglycemia. | Hyperglycemia is present. | stated outright | Latest glucose 96 mg/dL at 2100-01-02 19:40:00 (reference 70 to 100) is normal, not consistent with 'high'. |
| E1065859 | Assess for signs of hypovolemia or sepsis given the patient's hypotension and altered mental status. | Altered mental status is present. | stated outright | The only record addressing mental status is R17, which shows 'Best Verbal Response: Confused' at 01:00 on 2100-01-02. This is over 19 hours before the decision time and does not establish that altered mental status is present at 20:54. |
| E1068212 | Continue pericardial drainage catheter monitoring. | Pericardial drainage catheter monitoring is currently being performed. | presupposed by an action | The records document placement of a pericardial drainage catheter (R16), but there is no record of ongoing monitoring of the catheter at the decision time. The statement that monitoring is currently being performed is therefore not supported. |
| E1071224 | Continue the administration of heparin at 1300 units/hour to prevent thrombus formation. | Heparin is currently being given at 1300 units/hour. | presupposed by an action | The records show a heparin infusion at 1000 units/hour from 2099-12-30 to 2100-01-01 23:00, then at 22 units/hour until 2100-01-02 12:00. The 1300 units/hour infusion (R50) starts after the decision time of 2100-01-01 16:46, so it does not support the statement that heparin is currently being given at that rate. |
| E1071450 | Administer intravenous potassium chloride to correct hypokalemia. | Hypokalemia is present. | presupposed by an action | Latest potassium 4.1 mmol/L at 2100-01-01 13:50:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E1071450 | Continue inotropic support with milrinone. | Milrinone is currently being given. | presupposed by an action | The records mention milrinone only as a treatment documented for shock/inotropic agent (R29), but there is no medication order or administration record showing milrinone was given in the 24 hours before the decision time. |
| E1071450 | Continue inotropic support with milrinone. | The patient is currently receiving milrinone. | presupposed by an action | The records mention milrinone only as a treatment documented at 03:34 on 2100-01-01, which is after the decision time of 02:03. There is no administration record of milrinone in the 24 hours before the decision time, so the statement that the patient is currently receiving it is not supported. |
| E1090889 | Assess for potential causes of hypotension. | Hypotension is present. | presupposed by an action | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1099398 | Patient's blood pressure is fluctuating, with systolic readings as high as 202 mmHg and diastolic as low as 60 mmHg. Consider adjusting antihypertensive therapy. | Diastolic blood pressure is as low as 60 mmHg. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1117947 | Continue non-invasive ventilation to support respiratory function. | The patient is currently on non-invasive ventilation. | presupposed by an action | The only record mentioning non-invasive ventilation is R31, which documents it as a treatment at 07:31, after the decision time of 06:58. There is no record of the patient receiving non-invasive ventilation at or before the decision time. |
| E1171473 | Continue intravenous fluid administration with normal saline. | Intravenous fluid administration with normal saline is currently being given. | presupposed by an action | The most recent record of normal saline administration is from 12:53 on 2100-01-02, which is more than 24 hours before the decision time of 15:48 on 2100-01-02. There is no administration record within the 24 hours prior to the decision time, so the statement that it is currently being given is not supported. |
| E1171473 | Assess for signs of respiratory distress and adjust mechanical ventilation parameters as needed. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('Tidal Volume (set): 500 mL') was 6.8 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1173453 | Continue antibiotic therapy with vancomycin. | Vancomycin is currently being given. | presupposed by an action | The records document vancomycin as a treatment (R15), but there is no administration record (e.g., 'MAR Administered' or 'Given') within the 24 hours before the decision time to confirm it is currently being given. |
| E1287791 | Continue sedation at -1 RASS score. | The patient is currently receiving sedation. | presupposed by an action | The records show a PRN order for lorazepam (a sedative) and a RASS score of -4 at 19:10, but no administration of any sedative is documented in the 24 hours before the decision time. The statement that the patient is currently receiving sedation is therefore not supported by the records. |
| E1290248 | Continue intravenous fluid administration to maintain hydration. | Intravenous fluids are currently being administered. | presupposed by an action | The records mention this treatment but show no administration in the 24 h before the decision. (Panel verdict: supported.) |
| E1496959 | Continue anticonvulsant therapy for seizure prevention. | Anticonvulsant therapy is currently being given. | presupposed by an action | The records document 'anticonvulsant' as a treatment category, but there is no medication order or administration record for a specific anticonvulsant drug. Therefore, the statement that anticonvulsant therapy is currently being given is not supported by the available records. |
| E1592666 | Administer IV vancomycin for suspected infection. | Infection is suspected. | clinical judgment | The records show no clinical signs of infection. All recorded temperatures are normal (97.2-97.9 F), and there are no elevated white blood cell counts, cultures, or other indicators of infection. The administration of contrast media (Iopamidol) is not evidence of infection. |
| E1619343 | Administer intravenous vancomycin for suspected infection. | Infection is suspected. | presupposed by an action | The records show a urine WBC of 14/HPF (R16) and vancomycin administration (R36), but no documented diagnosis or clinical note stating infection is suspected. The elevated urine WBC alone does not directly confirm a suspicion of infection. |
| E1636307 | Continue intravenous sedation and analgesia to maintain patient comfort. | Intravenous sedation is currently being given. | presupposed by an action | The only intravenous sedation administration record is propofol from 2100-01-01 02:15 to 17:08, which ended more than 7 hours before the decision time of 2100-01-02 00:42. No sedation is documented as running at the decision time. |
| E1636307 | Continue intravenous sedation and analgesia to maintain patient comfort. | Intravenous analgesia is currently being given. | presupposed by an action | The records show orders for intravenous analgesics (HYDROmorphone, fentaNYL) and a documented narcotic analgesic treatment, but no administration of an intravenous analgesic within 24 hours before the decision time. The only intravenous analgesic administration, propofol, is a sedative, not an analgesic. |
| E1636307 | Assess patient for signs of respiratory distress and adjust mechanical ventilation settings if necessary. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 9.7 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1653043 | Continue anticoagulant therapy with warfarin. | Warfarin is currently being given. | presupposed by an action | The only warfarin administration record (R8) is dated 2100-01-01 at 22:00, which is more than 24 hours before the decision time of 2100-01-02 21:32. There is no administration record within the 24 hours prior to the decision time, so the statement that warfarin is currently being given is not supported. |
| E1672915 | Continue intravenous insulin to manage glucose levels. | Intravenous insulin is currently being given. | presupposed by an action | The records show insulin lispro being administered subcutaneously (R20, R36), but there is no record of intravenous insulin administration. The statement specifically claims intravenous insulin is being given, which is not supported by the available records. |
| E1674875 | Continue intravenous sodium chloride to maintain fluid balance. | Intravenous sodium chloride is currently being given. | presupposed by an action | The most recent sodium chloride administration record (R49) ended at 19:01 on 2100-01-02, over an hour before the decision time of 20:48, so it does not show the infusion was currently being given. |
| E1705630 | Continue sedation at a reduced level. | Sedation is currently being given. | presupposed by an action | The records mention sedative agents (lorazepam orders, diazepam and haloperidol treatment documentation), but there is no administration record of any sedative in the 24 hours before the decision time. The lorazepam orders are PRN and were stopped or are active without documented administration, so the statement that sedation is currently being given is not supported. |
| E1739131 | Continue pain management with hydromorphone as needed. | Hydromorphone is currently being given. | presupposed by an action | The records show hydromorphone was administered at 06:59, 07:58, and 10:28 on 2100-01-01, but the decision time is 2100-01-02 09:51. There is no administration record within 24 hours before the decision time, so the statement that it is currently being given is not supported. |
| E1790816 | Continue nitroglycerin infusion. | Nitroglycerin infusion is currently being given. | presupposed by an action | The nitroglycerin infusion record (R10) shows it ran from 2100-01-01 20:53 to 2100-01-02 15:12, which ended before the decision time of 2100-01-02 20:23. There is no administration record within 24 hours before the decision time showing it is currently running. |
| E1823727 | Continue IV fluids and electrolyte management. | Electrolyte management is currently being given. | presupposed by an action | The records show administration of IV fluids (sodium chloride) and medications like insulin and dextrose, but there is no administration record of a specific electrolyte replacement (e.g., potassium, magnesium, calcium) in the 24 hours before the decision time. The statement that 'electrolyte management is currently being given' is therefore not supported by the records. |
| E1823727 | Assess for signs of infection given leukocytosis. | Leukocytosis is present. | stated outright | Latest WBC 8.3 K/mm3 at 2100-01-02 10:00:00 (reference 4 to 11) is normal, not consistent with 'high'. |
| E1824650 | Wean off mechanical ventilation. | The patient is currently on mechanical ventilation. | presupposed by an action | The latest record before the decision (2100-01-02 15:35:00) reads 'O2 Delivery Device(s): None (charted: RA)'. |
| E1829278 | Administer intravenous Nicardipine to manage hypertension. | Hypertension is present. | presupposed by an action | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E1853162 | Increase oxygen flow to 4 L/min due to elevated systolic blood pressure and respiratory rate. | Respiratory rate is elevated. | stated outright | Median respiratory rate over the 6 h before the decision: 20 insp/min (1 readings), normal by the rule 'tachypnea RR > 20; bradypnea RR < 12'. |
| E2230341 | Continue Eptifibatide infusion at 20.6 ml/hour. | Eptifibatide infusion is currently being given. | presupposed by an action | The records show Eptifibatide infusions that ended before the decision time (R26 ended 2100-01-02 00:24, R41 ended 2100-01-02 09:05) and a zero-duration entry at 05:00 (R43). There is no administration record of Eptifibatide running at the decision time of 2100-01-02 14:38. |
| E2309912 | Continue intravenous potassium chloride to maintain electrolyte balance. | Intravenous potassium chloride is currently being given. | presupposed by an action | The records show a potassium chloride IV administration that started at 12:30 on 2100-01-01, which is after the decision time of 11:55. There is no administration record of potassium chloride in the 24 hours before the decision time. |
| E2860378 | Continue insulin infusion to manage hyperglycemia. | Insulin infusion is currently being given. | presupposed by an action | The most recent insulin administration record (R46) shows an infusion that ended at 02:30 on 2100-01-02, over 11 hours before the decision time of 14:07. There is no record of insulin being administered within the 24 hours prior to the decision time, so the statement that it is currently being given is not supported. |
| E2879373 | Continue IV furosemide for diuretic therapy. | IV furosemide is currently being given. | presupposed by an action | The records mention IV furosemide only as a documented treatment at 10:19 on 2100-01-01, which is after the decision time of 09:35. There is no administration record of IV furosemide in the 24 hours before the decision time, so the statement that it is currently being given is not supported. |
| E3001552 | Monitor heart rate and blood pressure closely due to fluctuations. | Heart rate and blood pressure have been fluctuating. | stated outright | The records contain only heart rate measurements and no blood pressure readings. While the heart rate values do fluctuate over time, the statement about blood pressure cannot be assessed because blood pressure is not mentioned in any of the supplied records. |
| E3027283 | Monitor pain levels and adjust ondansetron as needed. | Ondansetron is currently being given. | presupposed by an action | The records contain an active PRN order for ondansetron (R7), but there is no administration record showing it was given in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E3035113 | Continue vancomycin and zosyn IV as ordered for suspected infection. | Zosyn is currently being given. | presupposed by an action | The records show Zosyn was given once on 2100-01-01 at 10:16, which is more than 24 hours before the decision time of 2100-01-02 11:08. There is no administration record of Zosyn within the 24 hours prior to the decision time, so the statement that it is currently being given is not supported. |
| E3035113 | Continue vancomycin and zosyn IV as ordered for suspected infection. | Infection is suspected. | clinical judgment | The records show administration of vancomycin and Zosyn, but the admission diagnosis is emphysema/bronchitis, not an infection. There is no documented diagnosis or direct evidence of infection to support the statement that infection is suspected. |
| E3053511 | Continue midazolam for sedation. | Midazolam is currently being given. | presupposed by an action | The records show midazolam was given at 16:00 and 17:22-17:25 on 2100-01-02, but there is no administration record within 24 hours before the decision time of 20:31 on 2100-01-02, nor any 'Running at decision time' record. Therefore, the statement that midazolam is currently being given is not supported. |
| E3115505 | Continue administration of intravenous methylprednisolone. | Intravenous methylprednisolone is currently being given. | presupposed by an action | The records show a methylprednisolone administration that ended at 17:10 on 2100-01-01 (R12) and a scheduled order for it (R43), but no administration record within 24 hours before the decision time of 2100-01-02 03:00. Therefore, the statement that it is currently being given is not supported. |
| E3124669 | Continue pain management with oral medications as needed. | Pain management with oral medications is currently being given. | presupposed by an action | The records document pulmonary medications (antibacterials, bronchodilators, glucocorticoids) but no oral pain medications are ordered or administered. Pain levels are recorded, but no analgesic administration is documented. |
| E3148216 | Monitor the patient's oxygen saturation closely, as it has fluctuated between 94% and 100%. | Oxygen saturation has fluctuated between 94% and 100%. | stated outright | The statement claims oxygen saturation fluctuated between 94% and 100%, but the records show values outside this range, including 92% (R46) and 91% (R47) before the decision time. Therefore, the stated range is not fully supported. |
| E3148216 | Continue sedation at the RASS score of 0 to maintain patient comfort. | Sedation is currently being given. | presupposed by an action | The records mention sedation only as a RASS score of 0, which indicates the patient is alert and calm, not that a sedative medication is currently being administered. There is no order or administration record for any sedative drug. |
| E3150018 | Continue sedative and anti-psychotic medications for pain and agitation. | Sedative medications are currently being given. | presupposed by an action | The records document treatment with the sedative lorazepam at 00:06 and 15:23 on 2100-01-02, but there is no administration record (e.g., 'MAR Administered' or 'Given') within 24 hours before the decision time of 23:33 to confirm it is currently being given. |
| E3150018 | Continue sedative and anti-psychotic medications for pain and agitation. | Anti-psychotic medications are currently being given. | presupposed by an action | The records document treatment with the anti-psychotic agent haldol, but these are treatment documentation entries, not administration records. There is no MAR Administered or similar record showing the drug was actually given within 24 hours of the decision time. |
| E3170528 | Continue intravenous fluids to maintain hydration. | Intravenous fluids are currently being given. | presupposed by an action | The only intravenous fluid administration record, R22, shows a continuous infusion of potassium chloride in sodium chloride that ended at 01:40 on 2100-01-02, which is over two hours before the decision time of 03:39. No other IV fluid administration is documented in the 24 hours prior to the decision time. |
| E3178242 | Continue intravenous fluid administration to maintain adequate hydration. | Intravenous fluids are currently being administered. | presupposed by an action | The most recent IV fluid administration record (R1) ended at 07:23, before the decision time of 07:26. No other IV fluid administration is documented as running at the decision time, so the statement that IV fluids are currently being administered is not supported. |
| E3220742 | Continue intravenous sodium chloride for fluid management. | Intravenous sodium chloride is currently being given. | presupposed by an action | The records show sodium chloride was administered as boluses on 2099-12-31 (R2, R8) and as a continuous infusion starting 2100-01-01 03:00 (R33), but the most recent administration record (R44) indicates a continuous infusion that started at 16:00 on 2100-01-01, which is after the decision time of 02:33. There is no administration record showing sodium chloride was being given at the decision time. |
| E3223097 | Continue pain management with IV morphine as needed. | IV morphine is currently being given. | presupposed by an action | The records contain an active order for IV morphine (R15), but there is no administration record showing morphine was given in the 24 hours before the decision time. Therefore, the statement that IV morphine is currently being given is not supported. |

## 5. Judge panel

131 items went to the judge panel. Agreement: {'1/1': 131} (split = no majority; the conservative label was used and the item needs human review).

## 6. Per-case score sheets

| Case | Facts | supported | not_supported | not_addressed | unverifiable | Treatment agreement | Vital recall | All recall |
|---|---|---|---|---|---|---|---|---|
| E153972 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E172015 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E184757 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E211144 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E284265 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E297175 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E322290 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E375854 | 0 | - | - | - | - | 0.0% | - | - |
| E383358 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E395323 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E405746 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E454584 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E467819 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E490454 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E521456 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 50.0% | - | - |
| E664474 | 2 | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | - | - |
| E733082 | 4 | 25.0% | 75.0% | 0.0% | 0.0% | 0.0% | - | - |
| E756295 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E758325 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E826669 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E850469 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E876429 | 0 | - | - | - | - | 0.0% | - | - |
| E899746 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E942382 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E962227 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E978037 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1056063 | 5 | 80.0% | 20.0% | 0.0% | 0.0% | - | - | - |
| E1057910 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E1057967 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1064283 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1065859 | 4 | 25.0% | 50.0% | 25.0% | 0.0% | 0.0% | - | - |
| E1068212 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071224 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071450 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1090039 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1090889 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1099398 | 7 | 85.7% | 14.3% | 0.0% | 0.0% | - | - | - |
| E1117947 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1121034 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1171473 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1173453 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1177589 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1287791 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1290248 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1449360 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1496959 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1497157 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1588473 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1592666 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1619343 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1636307 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1653043 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1672915 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1674875 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1682105 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1705630 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1739131 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E1781359 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1790816 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823356 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1823727 | 3 | 33.3% | 66.7% | 0.0% | 0.0% | 0.0% | - | - |
| E1824650 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1829278 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1837964 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1853162 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | - | - | - |
| E1856821 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2230341 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E2309912 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2418055 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 50.0% | - | - |
| E2419768 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2558122 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2609672 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2714303 | 0 | - | - | - | - | - | - | - |
| E2725629 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2757707 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2814579 | 0 | - | - | - | - | 0.0% | - | - |
| E2860378 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2879373 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3001552 | 4 | 25.0% | 25.0% | 50.0% | 0.0% | 50.0% | - | - |
| E3027283 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 50.0% | - | - |
| E3033795 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3035113 | 5 | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3053511 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3067309 | 0 | - | - | - | - | 0.0% | - | - |
| E3110594 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3111371 | 0 | - | - | - | - | - | - | - |
| E3112232 | 0 | - | - | - | - | - | - | - |
| E3115505 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3124669 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3130379 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | - | - |
| E3148216 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3150018 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3152779 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E3170528 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3178242 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3205786 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3220742 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3223097 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E3233620 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E3237226 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | - | - | - |
