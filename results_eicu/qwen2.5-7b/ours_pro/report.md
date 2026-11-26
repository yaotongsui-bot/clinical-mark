# Evaluation of AI clinical suggestions against patient records

- Input: `eicu_triples_qwen2.5-7b.json`; 100 cases, 2.99 AI suggestions per case on average.
- Models: atomizer `deepseek-v4-pro:0813:cloud`; judge panel `deepseek-v4-pro:0813:cloud` (majority vote; reasoning mode: none); 131 new model calls, 0 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 27.2% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 173 |
| supported / not_supported / not_addressed / unverifiable | 96 / 69 / 8 / 0 |
| Fact accuracy = supported / (supported + not_supported) | 58.2% |
| Cases with at least one not_supported fact | 49 / 100 |
| Omitted findings: abnormalities the clinicians treated that no AI fact mentions | 0 / 0 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 51 | 82.4% | {'supported': 42, 'not_supported': 9} |
| presupposed by an action | 110 | 49.0% | {'supported': 50, 'not_supported': 52, 'not_addressed': 8} |
| clinical judgment | 12 | 33.3% | {'not_supported': 8, 'supported': 4} |
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
| E297175 | Monitor patient's respiratory status closely due to ongoing respiratory distress. | Respiratory distress is ongoing. | stated outright | The most recent respiratory rate before the decision time is 23 insp/min (R50), which is mildly elevated but not definitive evidence of ongoing respiratory distress. The records show treatments for respiratory issues (e.g., bronchodilators, non-invasive ventilation) but no documented diagnosis or clinical finding of 'respiratory distress' itself. |
| E395323 | Continue vancomycin and piperacillin/tazobactam for suspected sepsis. | Vancomycin is currently being given. | presupposed by an action | The records mention vancomycin only as a documented treatment (R13), but there is no medication administration record showing it was given in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E395323 | Continue vancomycin and piperacillin/tazobactam for suspected sepsis. | Piperacillin/tazobactam is currently being given. | presupposed by an action | The records only document piperacillin/tazobactam as a treatment (R13), but there is no medication administration record showing it was given within 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E395323 | Continue vancomycin and piperacillin/tazobactam for suspected sepsis. | Sepsis is suspected. | clinical judgment | The records show administration of antibiotics (piperacillin/tazobactam and vancomycin) and a transient temperature of 100.3 F, but no diagnosis of sepsis is documented. The vital signs do not meet criteria for sepsis (e.g., no sustained fever, hypotension, or elevated respiratory rate), so the suspicion is not directly supported by the records. |
| E405746 | Continue labetalol for hypertension management. | Labetalol is currently being given. | presupposed by an action | The records contain an active order for labetalol (R11) and a treatment documentation note (R34), but there is no administration record showing labetalol was given in the 24 hours before the decision time. Therefore, the statement that it is currently being given is not supported. |
| E405746 | Continue labetalol for hypertension management. | Hypertension is present. | clinical judgment | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E467819 | Continue monitoring blood pressure and adjust nicardipine infusion as needed. | Nicardipine infusion is currently being given. | presupposed by an action | The most recent nicardipine administration record (R50) shows an infusion that ended at 00:00 on 2100-01-02, which is more than 1 hour and 43 minutes before the decision time of 01:43. There is no record of an infusion running at the decision time or within the preceding 24 hours that is still active. |
| E467819 | Administer oral enalapril as ordered. | Oral enalapril is ordered. | presupposed by an action | The records document enalapril as a treatment for hypertension, but there is no medication order for oral enalapril. The statement that it is ordered is therefore not supported. |
| E521456 | Continue mechanical ventilation with tidal volume 300 mL and PEEP 5 cmH2O. | PEEP is 5 cmH2O. | stated outright | The most recent PEEP records before the decision time show a setting of 7 cmH2O, not 5 cmH2O. Earlier records show 5 cmH2O, but the latest values contradict the statement. |
| E521456 | Administer 10 mL of magnesium sulfate intravenously for potential delirium. | Delirium is potentially present. | clinical judgment | The records include CAM-ICU delirium assessments at 21:00, 22:00, and 12:00, all with a score of 'No', which directly contradicts the statement that delirium is potentially present. |
| E733082 | Monitor blood glucose levels closely due to recent high readings and risk of hypoglycemia. | There is a risk of hypoglycemia. | clinical judgment | The statement claims a risk of hypoglycemia, but all recorded glucose values are elevated (153-216 mg/dL), indicating hyperglycemia rather than hypoglycemia. The presence of PRN orders for glucose, glucagon, and dextrose (R42-R45) suggests a precautionary protocol, but the actual measurements do not support a current risk of low blood sugar. |
| E733082 | Administer IV fluids to maintain adequate hydration and blood pressure support. | Hydration is inadequate. | presupposed by an action | The records show multiple administrations of IV fluids (sodium chloride) including a running infusion at decision time, which indicates hydration was being actively managed, not inadequate. |
| E733082 | Administer IV fluids to maintain adequate hydration and blood pressure support. | Blood pressure support is needed. | presupposed by an action | The records show multiple systolic blood pressure readings below 90 mmHg (e.g., R9 at 87 mmHg) and several in the low 100s, but the most recent readings before the decision time (R48-R50) are 104, 121, and 120 mmHg, which do not indicate a current need for blood pressure support. |
| E850469 | Continue aggressive fluid resuscitation to maintain adequate perfusion. | Aggressive fluid resuscitation is currently being given. | presupposed by an action | The records show a single 1000 mL normal saline bolus given on 2100-01-01 at 12:27 and a treatment note for aggressive volume resuscitation at 14:20, but there is no administration record of ongoing aggressive fluid resuscitation within 24 hours before the decision time of 2100-01-02 13:47. |
| E942382 | Continue the administration of diltiazem to manage the patient's heart rate and rhythm. | Diltiazem is currently being given. | presupposed by an action | The records mention diltiazem as a documented treatment (R15) and show a brief infusion on 2100-01-01 at 17:04 (R20), but there is no administration record within 24 hours before the decision time (2100-01-02 15:23) or a 'Running at decision time' record for diltiazem. Therefore, the statement that it is currently being given is not supported. |
| E1056063 | Continue oxygen therapy with nasal cannula at 2 L/min to maintain adequate oxygen saturation. | Oxygen therapy with nasal cannula at 2 L/min is currently being given. | presupposed by an action | The records document nasal cannula oxygen therapy and O2 flow of 2 L/min on 2100-01-01, but the most recent administration record is from 17:00 on 2100-01-01, more than 24 hours before the decision time of 2100-01-02 10:15. No administration record within the 24 hours before the decision time supports that oxygen is currently being given. |
| E1057967 | Monitor blood glucose levels closely given the patient's fluctuating readings and risk of sepsis. | The patient is at risk of sepsis. | clinical judgment | The records mention therapeutic antibacterials (R11), which could relate to infection, but they do not state a sepsis diagnosis or provide values (e.g., SIRS criteria, lactate, WBC) that directly show sepsis risk. The statement is therefore not supported by the available data. |
| E1064283 | Administer potassium chloride PO to address low potassium levels. | Potassium is low. | stated outright | Latest potassium 4.1 mmol/L at 2100-01-02 10:38:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E1065859 | Monitor blood glucose levels closely due to persistent hyperglycemia. | Hyperglycemia is present. | stated outright | Latest glucose 96 mg/dL at 2100-01-02 19:40:00 (reference 70 to 100) is normal, not consistent with 'high'. |
| E1065859 | Continue intravenous fluid administration to maintain adequate blood pressure and volume status. | Intravenous fluids are currently being given. | presupposed by an action | The most recent IV fluid administration (R10) ended at 00:28 on 2100-01-02, which is more than 20 hours before the decision time of 20:54. There is no record of IV fluids being administered within the 24 hours prior to the decision time, so the statement that they are currently being given is not supported. |
| E1068212 | Continue pericardial drainage catheter monitoring. | Pericardial drainage catheter monitoring is currently being performed. | presupposed by an action | The records document placement of a pericardial drainage catheter (R16), but there is no record of ongoing monitoring of the catheter at or near the decision time. |
| E1071450 | Administer intravenous potassium chloride to correct hypokalemia. | Hypokalemia is present. | presupposed by an action | Latest potassium 4.1 mmol/L at 2100-01-01 13:50:00 (reference 3.3 to 5.1) is normal, not consistent with 'low'. |
| E1071450 | Continue inotropic support with milrinone. | Milrinone is currently being given. | presupposed by an action | The records document milrinone as a treatment for shock (R29), but there is no medication order or administration record showing that milrinone was actively being given at the decision time. The statement that it is 'currently being given' is therefore not supported by the available records. |
| E1071450 | Continue inotropic support with milrinone. | The patient is currently receiving milrinone. | presupposed by an action | The records document milrinone as a treatment for shock (R28), but there is no medication order or administration record showing that milrinone was actively being given at the decision time. |
| E1090889 | Assess for potential causes of hypotension. | Hypotension is present. | presupposed by an action | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1099398 | Patient's blood pressure is fluctuating, with systolic readings as high as 202 mmHg and diastolic as low as 60 mmHg. Consider adjusting antihypertensive therapy. | Diastolic blood pressure is as low as 60 mmHg. | stated outright | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: no. |
| E1117947 | Continue non-invasive ventilation to support respiratory function. | The patient is currently on non-invasive ventilation. | presupposed by an action | The only record mentioning non-invasive ventilation is a treatment documentation from 2100-01-01 07:31, which is over 23 hours before the decision time. There is no administration or ongoing ventilation record within the 24 hours before 2100-01-02 06:58 to support that the patient is currently on non-invasive ventilation. |
| E1171473 | Continue intravenous fluid administration with normal saline. | Intravenous fluid administration with normal saline is currently being given. | presupposed by an action | The records document normal saline administration at 00:50, 00:51, and 12:53, but none within the 24 hours before the decision time of 15:48 on 2100-01-02. The most recent documentation is over 2.5 hours prior, so it does not support that it is 'currently being given'. |
| E1171473 | Assess for signs of respiratory distress and adjust mechanical ventilation parameters as needed. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('Tidal Volume (set): 500 mL') was 6.8 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1173453 | Continue antibiotic therapy with vancomycin. | Vancomycin is currently being given. | presupposed by an action | The records document vancomycin as a treatment on 2100-01-01 at 13:12, but there is no administration record (e.g., MAR Administered, Given, Infusion) within 24 hours before the decision time to show it is currently being given. |
| E1177589 | Continue oxygen therapy with 2 L/min nasal cannula. | Oxygen therapy with 2 L/min nasal cannula is currently being given. | presupposed by an action | The most recent oxygen delivery record at 06:00 on 2100-01-02 shows an O2 L/% of 21, which corresponds to room air, not 2 L/min via nasal cannula. Earlier records show 2 L/min, but the latest record contradicts the statement. |
| E1287791 | Continue sedation at -1 RASS score. | The patient is currently receiving sedation. | presupposed by an action | The records show a PRN lorazepam order (R1) and RASS scores indicating sedation (e.g., -4 at R7, -1 at R19), but no administration of lorazepam or any sedative in the 24 hours before the decision time. Therefore, the statement that the patient is currently receiving sedation is not supported. |
| E1290248 | Continue intravenous fluid administration to maintain hydration. | Intravenous fluids are currently being administered. | presupposed by an action | The records show PRN orders for intravenous sodium chloride (R14, R15) and a treatment documentation note for intravenous fluid administration (R35), but no administration record within 24 hours before the decision time. Therefore, current administration is not confirmed. |
| E1592666 | Administer IV vancomycin for suspected infection. | Infection is suspected. | clinical judgment | The records show multiple normal temperature readings (97.2-97.9 F) and no elevated white blood cell count, positive cultures, or other documented signs of infection. The statement 'Infection is suspected' is not supported by the provided data. |
| E1636307 | Continue intravenous sedation and analgesia to maintain patient comfort. | Intravenous sedation is currently being given. | presupposed by an action | The only intravenous sedation administration record is propofol from 2100-01-01 02:15 to 17:08, which ended more than 7 hours before the decision time of 2100-01-02 00:42. No sedation administration is documented within the 24 hours before the decision time. |
| E1636307 | Continue intravenous sedation and analgesia to maintain patient comfort. | Intravenous analgesia is currently being given. | presupposed by an action | The records show orders for intravenous analgesics (HYDROmorphone, fentaNYL) and an administration of propofol that ended at 17:08 on 2100-01-01, but no intravenous analgesia administration is documented in the 24 hours before the decision time of 2100-01-02 00:42. |
| E1636307 | Assess patient for signs of respiratory distress and adjust mechanical ventilation settings if necessary. | The patient is currently on mechanical ventilation. | presupposed by an action | The last ventilator/intubation record ('PEEP set: 5 cmH2O') was 9.7 h before the decision, with none after it. Ventilator settings are charted every 1-4 h while ventilated, so by the rule (> 6 h without a record) the patient was not ventilated at T. |
| E1653043 | Continue anticoagulant therapy with warfarin. | Warfarin is currently being given. | presupposed by an action | The records show a warfarin administration on 2100-01-01 at 22:00 (R7) and a treatment documentation for coumadin on 2100-01-02 at 07:45 (R33), but no administration record within 24 hours before the decision time of 2100-01-02 21:32. Therefore, the statement that warfarin is currently being given is not supported. |
| E1672915 | Continue intravenous insulin to manage glucose levels. | Intravenous insulin is currently being given. | presupposed by an action | The records show insulin lispro being administered subcutaneously (R19, R36), but there is no record of intravenous insulin administration. The statement specifically claims intravenous insulin is being given, which is not supported by the available records. |
| E1674875 | Continue intravenous sodium chloride to maintain fluid balance. | Intravenous sodium chloride is currently being given. | presupposed by an action | The most recent sodium chloride administration (R49) ended at 19:01 on 2100-01-02, over an hour before the decision time of 20:48. The earlier continuous infusion (R5) also ended the previous day. No record shows sodium chloride running at the decision time. |
| E1705630 | Continue sedation at a reduced level. | Sedation is currently being given. | presupposed by an action | The records show an active PRN order for lorazepam (a sedative) and documentation of sedative agents, but no administration of any sedative in the 24 hours before the decision time. The most recent RASS scores are 0 and 1, indicating the patient is not currently sedated. |
| E1739131 | Continue pain management with hydromorphone as needed. | Hydromorphone is currently being given. | presupposed by an action | The records show hydromorphone administrations on 2100-01-01 at 06:59, 07:58, and 10:28, but none within 24 hours before the decision time of 2100-01-02 09:51. The active PRN order (R12, R13) does not indicate current administration. |
| E1790816 | Continue nitroglycerin infusion. | Nitroglycerin infusion is currently being given. | presupposed by an action | The nitroglycerin infusion record (R7) ended at 15:12 on 2100-01-02, over five hours before the decision time of 20:23, so it was not being given at the decision time. |
| E1823727 | Continue IV fluids and electrolyte management. | IV fluids are currently being given. | presupposed by an action | The most recent IV fluid administration was a one-time dose on 2100-01-01 at 14:05 (R29), which is over 24 hours before the decision time of 2100-01-02 14:58. While there is an active PRN order for IV fluids (R32) and a prior continuous infusion (R14), there is no record of IV fluids being administered within the 24 hours preceding the decision time. |
| E1823727 | Continue IV fluids and electrolyte management. | Electrolyte management is currently being given. | presupposed by an action | The records show administration of sodium chloride (an electrolyte) but the most recent administration was on 2100-01-01 at 14:05, which is more than 24 hours before the decision time of 2100-01-02 14:58. No electrolyte administration is documented within the 24 hours prior to the decision time. |
| E1823727 | Assess for signs of infection given leukocytosis. | Leukocytosis is present. | stated outright | Latest WBC 8.3 K/mm3 at 2100-01-02 10:00:00 (reference 4 to 11) is normal, not consistent with 'high'. |
| E1824650 | Wean off mechanical ventilation. | The patient is currently on mechanical ventilation. | presupposed by an action | The latest record before the decision (2100-01-02 15:35:00) reads 'O2 Delivery Device(s): None (charted: RA)'. |
| E1829278 | Administer intravenous Nicardipine to manage hypertension. | Hypertension is present. | presupposed by an action | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| E1853162 | Increase oxygen flow to 4 L/min due to elevated systolic blood pressure and respiratory rate. | Respiratory rate is elevated. | stated outright | Median respiratory rate over the 6 h before the decision: 20 insp/min (1 readings), normal by the rule 'tachypnea RR > 20; bradypnea RR < 12'. |
| E1856821 | Continue norepinephrine infusion to maintain hemodynamic stability. | Norepinephrine infusion is currently being given. | presupposed by an action | The most recent norepinephrine infusion record (R40) ended at 14:11 on 2100-01-02, which is more than 4 hours before the decision time of 18:36. No administration record shows the infusion running at the decision time. |
| E2230341 | Continue Eptifibatide infusion at 20.6 ml/hour. | Eptifibatide infusion is currently being given. | presupposed by an action | The most recent Eptifibatide administration record (R38) ended at 09:05 on 2100-01-02, and the 20.6 ml/hour infusion (R40) was a zero-duration entry at 05:00. There is no administration record showing Eptifibatide running at the decision time of 14:38. |
| E2419768 | Continue IV fluid administration to maintain hydration. | IV fluids are currently being administered. | presupposed by an action | The records show IV fluid administrations (sodium chloride 0.9% syringes) that were running at decision time on 2100-01-01, but the decision time is 2100-01-02 19:34. No IV fluid administration is documented within the 24 hours before the decision time; the most recent IV-related record is an antibiotic (Rocephin) at 19:00 on 2100-01-02. |
| E2860378 | Continue insulin infusion to manage hyperglycemia. | Insulin infusion is currently being given. | presupposed by an action | The most recent insulin administration record (R46) shows an infusion that ended at 02:30 on 2100-01-02, over 11 hours before the decision time of 14:07. There is no record of insulin being administered within the 24 hours prior to the decision time, so the statement that it is currently being given is not supported. |
| E2879373 | Continue IV furosemide for diuretic therapy. | IV furosemide is currently being given. | presupposed by an action | The records document IV furosemide as a treatment on 2100-01-01 at 10:19, but there is no administration record within 24 hours before the decision time to confirm it is currently being given. |
| E3001552 | Monitor heart rate and blood pressure closely due to fluctuations. | Heart rate and blood pressure have been fluctuating. | stated outright | The records contain only heart rate measurements and no blood pressure readings. While the heart rate values do fluctuate, the statement about blood pressure fluctuation cannot be assessed because blood pressure is not mentioned in any of the supplied records. |
| E3001552 | Administer IV furosemide to manage fluid overload and ventricular dysfunction. | Fluid overload is present. | clinical judgment | The records show ongoing administration of intravenous sodium chloride infusions (R43, R46, R48), which can contribute to fluid overload, but they do not contain any direct documentation, diagnosis, or clinical findings (such as edema, weight gain, or elevated BNP) that state or directly demonstrate fluid overload. |
| E3027283 | Monitor pain levels and adjust ondansetron as needed. | Ondansetron is currently being given. | presupposed by an action | The records contain an active PRN order for ondansetron (R5), but no administration record of ondansetron in the 24 hours before the decision time. An order alone does not show the drug is currently being given. |
| E3035113 | Continue vancomycin and zosyn IV as ordered for suspected infection. | Vancomycin is currently being given. | presupposed by an action | The records show a one-time vancomycin dose on 2100-01-01 at 10:15 (R7) and a scheduled vancomycin infusion that started on 2100-01-01 at 22:30 (R35, R36), but no administration record within 24 hours before the decision time of 2100-01-02 11:08. The most recent vancomycin administration is over 12 hours before the decision time, so the statement that it is 'currently being given' is not supported. |
| E3035113 | Continue vancomycin and zosyn IV as ordered for suspected infection. | Zosyn is currently being given. | presupposed by an action | The only Zosyn administration record is from 2100-01-01 10:16, which is more than 24 hours before the decision time of 2100-01-02 11:08. There is no record of Zosyn being given or running at the decision time. |
| E3035113 | Continue vancomycin and zosyn IV as ordered for suspected infection. | Infection is suspected. | clinical judgment | The records show vancomycin and Zosyn were administered, but they do not contain any diagnosis, note, or laboratory finding that states or directly indicates an infection is suspected. The administration of antibiotics alone does not confirm the suspicion of infection. |
| E3115505 | Continue administration of intravenous methylprednisolone. | Intravenous methylprednisolone is currently being given. | presupposed by an action | The records show an intravenous methylprednisolone order that ended at 17:10 on 2100-01-01 (R11) and a new Q24HR order started at 16:51 (R43), but no administration record within 24 hours before the decision time of 2100-01-02 03:00. Therefore, the statement that it is currently being given is not supported. |
| E3124669 | Continue pain management with oral medications as needed. | Pain management with oral medications is currently being given. | presupposed by an action | The records document pulmonary medications (antibacterials, bronchodilators, glucocorticoids) but contain no order or administration record for any oral pain medication. Pain levels are recorded, but they do not show that oral pain management is being given. |
| E3148216 | Monitor the patient's oxygen saturation closely, as it has fluctuated between 94% and 100%. | Oxygen saturation has fluctuated between 94% and 100%. | stated outright | The records show oxygen saturation values ranging from 91% to 100%, including values below 94% (e.g., 92% at R46, 91% at R47), so the statement that it fluctuated between 94% and 100% is not fully supported. |
| E3148216 | Continue sedation at the RASS score of 0 to maintain patient comfort. | Sedation is currently being given. | presupposed by an action | The records show a sedation scale score of 0 (RASS) at 01:58, but no medication administration record for any sedative is present. A sedation score alone does not prove that sedation is currently being given. |
| E3150018 | Continue sedative and anti-psychotic medications for pain and agitation. | Sedative medications are currently being given. | presupposed by an action | The records document treatment with the sedative lorazepam at 00:06 and 15:23 on 2100-01-02, but these are treatment documentation entries, not administration records. There is no MAR administration or 'Running at decision time' record for any sedative within 24 hours before the decision time, so current administration is not supported. |
| E3150018 | Continue sedative and anti-psychotic medications for pain and agitation. | Anti-psychotic medications are currently being given. | presupposed by an action | The records document treatment with the anti-psychotic agent haldol at 00:06 and 15:23, but these are treatment documentation entries, not administration records. There is no MAR administration or 'Given' record for an anti-psychotic within the 24 hours before the decision time, so the statement that it is 'currently being given' is not supported. |
| E3170528 | Continue intravenous fluids to maintain hydration. | Intravenous fluids are currently being given. | presupposed by an action | The only intravenous fluid administration record, R19, shows a continuous infusion that ended at 2100-01-02 01:40:00, which is before the decision time of 03:39:00. No other IV fluid administration is documented as running at the decision time. |
| E3178242 | Continue intravenous fluid administration to maintain adequate hydration. | Intravenous fluids are currently being administered. | presupposed by an action | The most recent IV fluid administration record (R46) shows Lactated Ringers running at 15:00 on 2100-01-01, which is over 16 hours before the decision time of 07:26 on 2100-01-02. No IV fluid administration is documented within the 24 hours preceding the decision time. |
| E3223097 | Continue pain management with IV morphine as needed. | IV morphine is currently being given. | presupposed by an action | The records contain an active PRN order for IV morphine (R13), but no administration record of morphine within the 24 hours before the decision time. Therefore, the statement that IV morphine is currently being given is not supported. |

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
| E395323 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
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
| E1057967 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1064283 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1065859 | 4 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1068212 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071224 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1071450 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1090039 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1090889 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1099398 | 7 | 85.7% | 14.3% | 0.0% | 0.0% | - | - | - |
| E1117947 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 100.0% | - | - |
| E1121034 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 50.0% | - | - |
| E1171473 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1173453 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1177589 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E1287791 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1290248 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1449360 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | - | - | - |
| E1496959 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1497157 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1588473 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1592666 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1619343 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
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
| E1823727 | 3 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1824650 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1829278 | 3 | 66.7% | 33.3% | 0.0% | 0.0% | 0.0% | - | - |
| E1837964 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E1853162 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | - | - | - |
| E1856821 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2230341 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E2309912 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2418055 | 3 | 66.7% | 0.0% | 33.3% | 0.0% | 50.0% | - | - |
| E2419768 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2558122 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2609672 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2714303 | 0 | - | - | - | - | - | - | - |
| E2725629 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2757707 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2814579 | 0 | - | - | - | - | 0.0% | - | - |
| E2860378 | 4 | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | - | - |
| E2879373 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3001552 | 4 | 25.0% | 50.0% | 25.0% | 0.0% | 50.0% | - | - |
| E3027283 | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 50.0% | - | - |
| E3033795 | 2 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3035113 | 5 | 40.0% | 60.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3053511 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
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
| E3220742 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| E3223097 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| E3233620 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | - |
| E3237226 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | - | - | - |
