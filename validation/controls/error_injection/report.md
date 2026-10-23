# Evaluation of AI clinical suggestions against patient records

- Input: `control_error_injection.json`; 202 cases, 1.0 AI suggestions per case on average.
- Models: atomizer `qwen2.5:14b`; judge panel `gemma4:12b`, `llama3.1:8b-instruct-q4_K_M`, `qwen2.5:14b` (majority vote; reasoning mode: gemma4:12b); 0 new model calls, 292 cache hits.
- Fact evidence: the whole admission before the decision time (VeriFact's reference EHR); retrieval hybrid, top 50 records per statement.
- Gold standard: pre-decision records for facts; clinician actions recorded after the decision (24 h or until ICU discharge) for actions.
- A missing record does not prove something did not happen. Thresholds, treatment classes and importance tiers come from the editable files in `rules/`.
- Items that cannot be scored (not_addressed, unverifiable, unobservable, vague_target, condition_not_met): 13.7% of all judged items.

## 1. Does the AI state false facts?

| Metric | Value |
|---|---|
| Fact atoms | 56 |
| supported / not_supported / not_addressed / unverifiable | 4 / 25 / 26 / 1 |
| Fact accuracy = supported / (supported + not_supported) | 13.8% |
| Cases with at least one not_supported fact | 22 / 202 |

| Fact kind | n | Accuracy | Labels |
|---|---|---|---|
| stated outright | 14 | 0.0% | {'not_supported': 13, 'unverifiable': 1} |
| presupposed by an action | 42 | 25.0% | {'not_supported': 12, 'supported': 4, 'not_addressed': 26} |
| clinical judgment | 0 | - | {} |
| vague | 0 | - | {} |

## 2. How close is the AI to what clinicians did?

Target (same class, or the drug the AI named) and direction (continue / stop / adjust) are decided by code; suggestions the rule file cannot classify go to the judge panel.

| Metric | Value |
|---|---|
| Treatment action atoms | 193 |
| Labels | {'match': 7, 'vague_target': 3, 'not_done': 120, 'partial_match': 63} |
| Agreement (strict) = match / (match + partial_match + not_done) | 3.7% |
| Agreement (lenient) = (match + partial_match) / same | 36.8% |

Monitoring/assessment atoms: 28 (reported separately, not part of agreement): {'unobservable': 8, 'performed': 20}; performed rate among observable items 100.0%. 9 'goal' atoms with no concrete action are not scored.

## 3. What did the AI miss?

Vital = a class the rule file marks vital, or one whose indication was present at the decision time (for example low potassium followed by potassium chloride). Other non-routine classes are okay.

| Recall | All suggestions (micro / per-case) | First 3 suggestions only (micro / per-case) |
|---|---|---|
| vital (5/596) | 0.8% / 0.9% | 0.8% / 0.9% |
| okay (2/1036) | 0.2% / 0.2% | 0.2% / 0.2% |
| all (7/1632) | 0.4% / 0.6% | 0.4% / 0.6% |

392 clinician actions answered an abnormality present at the decision time; the AI missed 387 of them. Most often missed vital classes: antimicrobials (124), IV fluids (86), invasive mechanical ventilation (74), vasopressors (68), calcium replacement (50), insulin (31), red cell transfusion (27), rate / rhythm control (21), phosphate replacement (18), platelet / plasma transfusion (15)

### Problem-linked omissions

| Case | Clinicians gave | Indication at the decision time | AI suggestions |
|---|---|---|---|
| M34107647-R03 | antimicrobials (Ciprofloxacin, Ciprofloxacin HCl) | Latest WBC 116.1 K/uL at 2153-03-28 03:16:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Monitor blood glucose levels closely given the low glucose readings. |
| M34107647-R03 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 3.7 mmol/L at 2153-03-28 20:00:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Monitor blood glucose levels closely given the low glucose readings. |
| M34578020-R05 | antimicrobials (CefePIME, Cefepime) | Latest WBC 13.1 K/uL at 2187-02-11 20:00:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Assess and manage the patient's nutritional status given the elevated albumin and hemoglobin levels. |
| M34578020-R05 | calcium replacement (Calcium Gluconate) | Latest calcium 1.09 mmol/L at 2187-02-11 06:41:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Assess and manage the patient's nutritional status given the elevated albumin and hemoglobin levels. |
| M35026312-R06 | insulin (Insulin - Regular, Insulin Human Regular) | Latest glucose 383 mg/dL (treatment threshold > 180). | Monitor blood glucose levels closely due to hypoglycemia. |
| M35026312-R06 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.3 mmol/L at 2150-03-12 14:40:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Monitor blood glucose levels closely due to hypoglycemia. |
| M36107367-R07 | antimicrobials (Ciprofloxacin IV, MetroNIDAZOLE) | Latest WBC 10.4 K/uL at 2148-01-25 02:25:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Monitor blood glucose levels closely due to low glucose levels. |
| M36107367-R07 | invasive mechanical ventilation (Invasive Ventilation) | Latest PaCO2 59 mm Hg at 2148-01-24 05:30:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Monitor blood glucose levels closely due to low glucose levels. |
| M37049133-R09 | phosphate replacement (Neutra-Phos) | Latest phosphate 2.6 mg/dL at 2196-04-15 03:36:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Assess for signs of infection given elevated white blood cell count. |
| M31959184-R12 | insulin (Insulin - Regular) | Latest glucose 226 mg/dL (treatment threshold > 180). | Evaluate the patient for potential respiratory issues given the low lactate dehydrogenase and respiratory alarms. |
| M31959184-R12 | IV fluids (LR) | Latest lactate 2.3 mmol/L at 2110-11-30 16:43:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Evaluate the patient for potential respiratory issues given the low lactate dehydrogenase and respiratory alarms. |
| M32128372-R13 | albumin / colloid (Albumin 5%, Albumin 5% (25g / 500mL)) | Latest albumin 2.9 g/dL at 2137-02-26 13:03:00 (reference 3.5 to 5.2) is low, consistent with 'low'. | Administer IV calcium to manage hypercalcemia. |
| M32128372-R13 | IV fluids (Dextrose 5%, LR) | Latest lactate 5.9 mmol/L at 2137-02-26 22:38:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer IV calcium to manage hypercalcemia. |
| M32128372-R13 | rate / rhythm control (Amiodarone, Amiodarone 600/500) | Median heart rate over the 6 h before the decision: 127.5 bpm (6 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Administer IV calcium to manage hypercalcemia. |
| M32128372-R13 | platelet / plasma transfusion (Fresh Frozen Plasma, Platelets) | Latest INR 2  (treatment threshold > 1.5). | Administer IV calcium to manage hypercalcemia. |
| M32128372-R13 | vitamin K (Phytonadione) | Latest INR 2  (treatment threshold > 1.5). | Administer IV calcium to manage hypercalcemia. |
| M35128235-R14 | calcium replacement (Calcium Gluconate) | Latest calcium 0.8 mmol/L at 2129-04-06 23:32:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Evaluate the patient's renal function, given the elevated creatinine levels. |
| M35128235-R14 | phosphate replacement (K Phos, Potassium Phosphate) | Latest phosphate 1.3 mg/dL at 2129-04-06 17:15:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Evaluate the patient's renal function, given the elevated creatinine levels. |
| M37293400-R15 | IV fluids (0.9% Sodium Chloride, Dextrose 5%) | Latest lactate 2.5 mmol/L at 2133-12-19 16:32:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Monitor blood glucose levels given hypoglycemia. |
| M37293400-R15 | vitamin K (Phytonadione, Vitamin K (Phytonadione)) | Latest INR 4.1  (treatment threshold > 1.5). | Monitor blood glucose levels given hypoglycemia. |
| M38430513-R16 | antimicrobials (Meropenem) | Latest WBC 11.1 K/uL at 2115-10-10 09:05:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Administer intravenous fluids to correct hypertension. |
| M38430513-R16 | insulin (Insulin - Glargine) | Latest glucose 231 mg/dL (treatment threshold > 180). | Administer intravenous fluids to correct hypertension. |
| M38430513-R16 | vasopressors (Norepinephrine) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. | Administer intravenous fluids to correct hypertension. |
| M38430513-R16 | vitamin K (Phytonadione) | Latest INR 4.1  (treatment threshold > 1.5). | Administer intravenous fluids to correct hypertension. |
| M38540883-R17 | rate / rhythm control (Metoprolol Tartrate) | Median heart rate over the 6 h before the decision: 109 bpm (5 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Evaluate and manage renal function, considering the low creatinine levels. |
| M38540883-R17 | vitamin K (Vitamin K (Phytonadione)) | Latest INR 2  (treatment threshold > 1.5). | Evaluate and manage renal function, considering the low creatinine levels. |
| M39061571-R18 | antimicrobials (CefePIME, Cefepime) | Latest WBC 15.5 K/uL at 2185-01-18 18:15:00 (reference 4.0 to 11.0) is high, consistent with 'high'. Median temperature over the 6 h before the decision: 102.55 F (4 readings), high by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. | Administer intravenous calcium to address hypercalcemia. |
| M39061571-R18 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 5.8 mmol/L at 2185-01-18 18:24:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer intravenous calcium to address hypercalcemia. |
| M39061571-R18 | rate / rhythm control (Amiodarone, Amiodarone 600/500) | Median heart rate over the 6 h before the decision: 120 bpm (7 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Administer intravenous calcium to address hypercalcemia. |
| M39061571-R18 | invasive mechanical ventilation (Invasive Ventilation) | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: yes. Latest PaCO2 54 mm Hg at 2185-01-18 18:24:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Administer intravenous calcium to address hypercalcemia. |
| M36107367-R19 | antimicrobials (Ciprofloxacin IV, MetroNIDAZOLE) | Latest WBC 10.4 K/uL at 2148-01-25 02:25:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Assess for signs of infection given the low white blood cell count. |
| M36107367-R19 | invasive mechanical ventilation (Invasive Ventilation) | Latest PaCO2 59 mm Hg at 2148-01-24 05:30:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Assess for signs of infection given the low white blood cell count. |
| M31959184-R20 | insulin (Insulin - Regular) | Latest glucose 226 mg/dL (treatment threshold > 180). | Monitor blood glucose levels given the low glucose reading. |
| M31959184-R20 | IV fluids (LR) | Latest lactate 2.3 mmol/L at 2110-11-30 16:43:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Monitor blood glucose levels given the low glucose reading. |
| M31959184-R21 | insulin (Insulin - Regular) | Latest glucose 226 mg/dL (treatment threshold > 180). | Monitor for signs of hypovolemia given the elevated hematocrit and hemoglobin levels. |
| M31959184-R21 | IV fluids (LR) | Latest lactate 2.3 mmol/L at 2110-11-30 16:43:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Monitor for signs of hypovolemia given the elevated hematocrit and hemoglobin levels. |
| M37049133-R22 | phosphate replacement (Neutra-Phos) | Latest phosphate 2.6 mg/dL at 2196-04-15 03:36:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Assess for signs of infection given elevated white blood cell count. |
| M30057454-D01 | antimicrobials (Cefazolin) | Latest WBC 17.8 K/uL at 2171-11-15 02:53:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Administer amiodarone to maintain hydration and manage blood pressure. |
| M30057454-D01 | calcium replacement (Calcium Gluconate) | Latest calcium 0.83 mmol/L at 2171-11-15 09:01:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Administer amiodarone to maintain hydration and manage blood pressure. |
| M30057454-D01 | IV fluids (Dextrose 5%, NaCl 0.9%) | 'blood pressure low' holds when any component is low. systolic BP: yes; mean arterial pressure: yes. | Administer amiodarone to maintain hydration and manage blood pressure. |
| M30057454-D01 | potassium replacement (KCL (Bolus), Potassium Chloride) | Latest potassium 2.3 mEq/L at 2171-11-15 09:01:00 (reference 3.3 to 5.1) is low, consistent with 'low'. | Administer amiodarone to maintain hydration and manage blood pressure. |
| M30057454-D01 | vasopressors (DOBUTamine, DOPamine) | 'blood pressure low' holds when any component is low. systolic BP: yes; mean arterial pressure: yes. | Administer amiodarone to maintain hydration and manage blood pressure. |
| M30665396-D04 | IV fluids (Dextrose 5%) | Latest lactate 2.4 mmol/L at 2167-05-06 05:23:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer levetiracetam to maintain adequate hydration. |
| M30757476-D05 | hypoglycemia treatment (Dextrose 50%) | Latest glucose 34 mg/dL at 2131-02-28 04:16:00 (reference 70.0 to 100.0) is low, consistent with 'low'. | Administer levetiracetam to maintain adequate hydration. |
| M30757476-D05 | phosphate replacement (Na Phos) | Latest phosphate 1.2 mg/dL at 2131-02-28 04:16:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Administer levetiracetam to maintain adequate hydration. |
| M30757476-D05 | invasive mechanical ventilation (Invasive Ventilation) | Latest PaCO2 47 mm Hg at 2131-02-28 12:17:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Administer levetiracetam to maintain adequate hydration. |
| M31269608-D06 | calcium replacement (Calcium Gluconate) | Latest calcium 7.8 mg/dL at 2154-04-25 03:59:00 (reference 8.4 to 10.3) is low, consistent with 'low'. | Administer norepinephrine to maintain hydration. |
| M31269608-D06 | potassium replacement (Potassium Chloride, Potassium Chloride Replacement (Critical Care and Oncology)) | Latest potassium 3 mEq/L at 2154-04-25 03:59:00 (reference 3.3 to 5.1) is low, consistent with 'low'. | Administer norepinephrine to maintain hydration. |
| M31338022-D07 | antihypertensives (Lisinopril) | 'blood pressure high' holds when any component is high. systolic BP: yes; mean arterial pressure: no. | Administer dexamethasone to maintain hydration. |
| M31494479-D08 | IV fluids (Dextrose 5%) | Latest lactate 3.1 mmol/L at 2141-12-17 13:32:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer dexamethasone to maintain adequate hydration. |
| M31959184-D09 | insulin (Insulin - Regular) | Latest glucose 226 mg/dL (treatment threshold > 180). | Administer norepinephrine to maintain hydration. |
| M31959184-D09 | IV fluids (LR) | Latest lactate 2.3 mmol/L at 2110-11-30 16:43:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer norepinephrine to maintain hydration. |
| M32119961-D10 | antimicrobials (Vancomycin) | Latest WBC 13 K/uL at 2155-12-03 05:41:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Continue furosemide to manage coagulation status. |
| M32119961-D10 | IV fluids (Dextrose 5%, NaCl 0.9%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. | Continue furosemide to manage coagulation status. |
| M32119961-D10 | vasopressors (Norepinephrine) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. | Continue furosemide to manage coagulation status. |
| M32128372-D11 | albumin / colloid (Albumin 5%, Albumin 5% (25g / 500mL)) | Latest albumin 2.9 g/dL at 2137-02-26 13:03:00 (reference 3.5 to 5.2) is low, consistent with 'low'. | Administer furosemide to maintain adequate hydration. |
| M32128372-D11 | calcium replacement (Calcium Gluconate) | Latest calcium 1.07 mmol/L at 2137-02-26 22:38:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Administer furosemide to maintain adequate hydration. |
| M32128372-D11 | IV fluids (Dextrose 5%, LR) | Latest lactate 5.9 mmol/L at 2137-02-26 22:38:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer furosemide to maintain adequate hydration. |
| M32128372-D11 | rate / rhythm control (Amiodarone, Amiodarone 600/500) | Median heart rate over the 6 h before the decision: 127.5 bpm (6 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Administer furosemide to maintain adequate hydration. |
| M32128372-D11 | platelet / plasma transfusion (Fresh Frozen Plasma, Platelets) | Latest INR 2  (treatment threshold > 1.5). | Administer furosemide to maintain adequate hydration. |
| M32128372-D11 | vitamin K (Phytonadione) | Latest INR 2  (treatment threshold > 1.5). | Administer furosemide to maintain adequate hydration. |
| M32155744-D12 | antimicrobials (Cefazolin, Vancomycin) | Latest WBC 11.3 K/uL at 2111-01-18 00:21:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Continue heparin. |
| M32155744-D12 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.8 mmol/L at 2111-01-17 20:13:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Continue heparin. |
| M32283063-D13 | antimicrobials (Cefazolin) | Latest WBC 16.7 K/uL at 2118-11-17 02:23:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Administer levetiracetam to maintain adequate hydration. |
| M32283063-D13 | IV fluids (Dextrose 5%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 2.1 mmol/L at 2118-11-16 21:15:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer levetiracetam to maintain adequate hydration. |
| M32359580-D14 | antimicrobials (CefePIME, Cefepime) | Latest WBC 11.2 K/uL at 2146-06-23 09:20:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Administer levetiracetam to maintain adequate hydration. |
| M32359580-D14 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 9 mmol/L at 2146-06-23 09:22:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer levetiracetam to maintain adequate hydration. |
| M32359580-D14 | platelet / plasma transfusion (Cryoprecipitate, Fresh Frozen Plasma) | Latest INR 2.7  (treatment threshold > 1.5). | Administer levetiracetam to maintain adequate hydration. |
| M32359580-D14 | red cell transfusion (Packed Red Blood Cells) | Latest hemoglobin 6.3 g/dL (treatment threshold < 7). | Administer levetiracetam to maintain adequate hydration. |
| M32391858-D15 | antimicrobials (CefazoLIN) | Latest WBC 14.8 K/uL at 2201-10-31 02:06:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Continue sodium bicarbonate with current settings. |
| M32391858-D15 | calcium replacement (Calcium Gluconate) | Latest calcium 1.11 mmol/L at 2201-10-31 05:36:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Continue sodium bicarbonate with current settings. |
| M32587226-D17 | IV fluids (Dextrose 5%, LR) | Latest lactate 2.2 mmol/L at 2125-09-25 12:12:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer calcium gluconate to maintain fluid balance. |
| M32604416-D18 | antimicrobials (Ciprofloxacin, Vancomycin) | Latest WBC 14.9 K/uL at 2132-12-16 02:14:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Administer dexamethasone to maintain adequate hydration. |
| M32604416-D18 | calcium replacement (Calcium Gluconate) | Latest calcium 1.11 mmol/L at 2132-12-16 02:26:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Administer dexamethasone to maintain adequate hydration. |
| M32604416-D18 | IV fluids (Dextrose 5%, NaCl 0.9%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 2.3 mmol/L at 2132-12-15 12:57:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer dexamethasone to maintain adequate hydration. |
| M33558396-D21 | antimicrobials (Cefazolin) | Latest WBC 20.7 K/uL at 2125-02-28 02:46:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Administer furosemide to maintain adequate blood pressure. |
| M33558396-D21 | IV fluids (Dextrose 5%, NaCl 0.9%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 2.4 mmol/L at 2125-02-27 23:54:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer furosemide to maintain adequate blood pressure. |
| M33846653-D22 | insulin (Insulin, Insulin - Glargine) | Latest glucose 234 mg/dL (treatment threshold > 180). | Administer amiodarone to maintain hydration. |
| M33987268-D23 | antimicrobials (Azithromycin, CeftriaXONE) | Latest WBC 27.9 K/uL at 2156-04-13 01:41:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Administer propofol to maintain electrolyte balance. |
| M33987268-D23 | IV fluids (Dextrose 5%, LR) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 2.4 mmol/L at 2156-04-13 14:02:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer propofol to maintain electrolyte balance. |
| M34100191-D24 | antimicrobials (CefePIME, Cefepime) | Latest WBC 21.6 K/uL at 2196-02-25 14:54:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Continue heparin. |
| M34100191-D24 | sodium bicarbonate (Sodium Bicarbonate, Sodium Bicarbonate 8.4%) | Latest pH 7.24 units at 2196-02-25 15:10:00 (reference 7.35 to 7.45) is low, consistent with 'low'. Latest bicarbonate 14 mEq/L at 2196-02-25 14:54:00 (reference 22.0 to 32.0) is low, consistent with 'low'. | Continue heparin. |
| M34100191-D24 | calcium replacement (Calcium Gluconate) | Latest calcium 7.6 mg/dL at 2196-02-25 14:54:00 (reference 8.4 to 10.3) is low, consistent with 'low'. | Continue heparin. |
| M34100191-D24 | cultures (Blood Cultured, Sputum Culture) | Latest WBC 21.6 K/uL at 2196-02-25 14:54:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Continue heparin. |
| M34100191-D24 | insulin (Insulin, Insulin - Regular) | Latest glucose 195 mg/dL (treatment threshold > 180). | Continue heparin. |
| M34100191-D24 | IV fluids (Dextrose 5%, LR) | Latest lactate 4.8 mmol/L at 2196-02-25 15:10:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Continue heparin. |
| M34100191-D24 | potassium replacement (KCL (Bolus), Potassium Chloride) | Latest potassium 3 mEq/L at 2196-02-25 14:54:00 (reference 3.3 to 5.1) is low, consistent with 'low'. | Continue heparin. |
| M34100191-D24 | rate / rhythm control (Amiodarone, Amiodarone 600/500) | Median heart rate over the 6 h before the decision: 109 bpm (5 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Continue heparin. |
| M34100191-D24 | platelet / plasma transfusion (Platelets) | Latest platelets 29 K/uL (treatment threshold < 50). | Continue heparin. |
| M34107647-D25 | antimicrobials (Ciprofloxacin, Ciprofloxacin HCl) | Latest WBC 116.1 K/uL at 2153-03-28 03:16:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Administer levetiracetam to maintain adequate hydration. |
| M34107647-D25 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 3.7 mmol/L at 2153-03-28 20:00:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer levetiracetam to maintain adequate hydration. |
| M34170353-D26 | albumin / colloid (Albumin 5%, Albumin 5% (12.5g / 250mL)) | Latest albumin 2.7 g/dL at 2149-10-03 02:35:00 (reference 3.5 to 5.2) is low, consistent with 'low'. | Continue sodium bicarbonate. |
| M34170353-D26 | calcium replacement (Calcium Gluconate, Calcium Gluconate sliding scale (Critical Care-Ionized calcium)) | Latest calcium 1.09 mmol/L at 2149-10-03 11:26:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Continue sodium bicarbonate. |
| M34170353-D26 | phosphate replacement (K Phos, Potassium Phosphate) | Latest phosphate 1.7 mg/dL at 2149-10-03 11:20:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Continue sodium bicarbonate. |
| M34499716-D27 | insulin (Insulin - Glargine, Insulin - Regular) | Latest glucose 359 mg/dL (treatment threshold > 180). | Continue packed red blood cells with close monitoring of respiratory parameters. |
| M34499716-D27 | invasive mechanical ventilation (Invasive Ventilation) | Latest PaCO2 47 mm Hg at 2142-07-31 18:20:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Continue packed red blood cells with close monitoring of respiratory parameters. |
| M34531557-D28 | antimicrobials (CefTRIAXone, Ceftriaxone) | Latest WBC 16 K/uL at 2117-03-15 01:45:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Continue dexamethasone to maintain hydration. |
| M34531557-D28 | calcium replacement (Calcium Gluconate, Calcium Gluconate sliding scale (Critical Care-Ionized calcium)) | Latest calcium 7.9 mg/dL at 2117-03-15 01:45:00 (reference 8.4 to 10.3) is low, consistent with 'low'. | Continue dexamethasone to maintain hydration. |
| M34578020-D29 | antimicrobials (CefePIME, Cefepime) | Latest WBC 13.1 K/uL at 2187-02-11 20:00:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Continue dexamethasone with close monitoring of respiratory parameters. |
| M34578020-D29 | calcium replacement (Calcium Gluconate) | Latest calcium 1.09 mmol/L at 2187-02-11 06:41:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Continue dexamethasone with close monitoring of respiratory parameters. |
| M35009126-D30 | antimicrobials (CefTAZidime, CefTRIAXone) | Latest WBC 16 K/uL at 2186-11-13 14:29:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Continue furosemide with current settings, ensuring adequate oxygenation and ventilation. |
| M35009126-D30 | cultures (Blood Cultured, Sputum Culture) | Latest WBC 16 K/uL at 2186-11-13 14:29:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Continue furosemide with current settings, ensuring adequate oxygenation and ventilation. |
| M35026312-D31 | insulin (Insulin - Regular, Insulin Human Regular) | Latest glucose 383 mg/dL (treatment threshold > 180). | Administer furosemide to maintain hydration. |
| M35026312-D31 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.3 mmol/L at 2150-03-12 14:40:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer furosemide to maintain hydration. |
| M35128235-D32 | calcium replacement (Calcium Gluconate) | Latest calcium 0.8 mmol/L at 2129-04-06 23:32:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Continue furosemide. |
| M35128235-D32 | phosphate replacement (K Phos, Potassium Phosphate) | Latest phosphate 1.3 mg/dL at 2129-04-06 17:15:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Continue furosemide. |
| M35258379-D33 | calcium replacement (Calcium Gluconate) | Latest calcium 1.11 mmol/L at 2153-09-20 03:22:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Administer levetiracetam to maintain adequate hydration. |
| M35436337-D34 | antimicrobials (Metronidazole, Piperacillin-Tazobactam) | Latest WBC 11.8 K/uL at 2185-06-17 01:07:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Continue amiodarone. |
| M35436337-D34 | calcium replacement (Calcium Gluconate) | Latest calcium 7.8 mg/dL at 2185-06-17 01:07:00 (reference 8.4 to 10.3) is low, consistent with 'low'. | Continue amiodarone. |
| M35514836-D35 | rate / rhythm control (Metoprolol, Metoprolol Tartrate) | Median heart rate over the 6 h before the decision: 102.5 bpm (4 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Continue levetiracetam. |
| M36059427-D37 | calcium replacement (Calcium Gluconate, Calcium Gluconate sliding scale (Critical Care-Ionized calcium)) | Latest calcium 1.03 mmol/L at 2123-02-20 23:15:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Continue dexamethasone with current settings. |
| M36059427-D37 | cultures (Blood Cultured, Sputum Culture) | Latest WBC 16.1 K/uL at 2123-02-20 18:35:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Continue dexamethasone with current settings. |
| M36059427-D37 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.1 mmol/L at 2123-02-20 23:15:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Continue dexamethasone with current settings. |
| M36091287-D38 | antimicrobials (Ampicillin-Sulbactam, Ampicillin/Sulbactam (Unasyn)) | Latest WBC 15.1 K/uL at 2119-10-27 02:32:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Administer dexamethasone to maintain fluid balance. |
| M36091287-D38 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.6 mmol/L at 2119-10-26 07:22:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer dexamethasone to maintain fluid balance. |
| M36107367-D39 | antimicrobials (Ciprofloxacin IV, MetroNIDAZOLE) | Latest WBC 10.4 K/uL at 2148-01-25 02:25:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Administer levetiracetam to maintain fluid balance. |
| M36107367-D39 | invasive mechanical ventilation (Invasive Ventilation) | Latest PaCO2 59 mm Hg at 2148-01-24 05:30:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Administer levetiracetam to maintain fluid balance. |
| M36558922-D42 | antimicrobials (CefazoLIN, Cefazolin) | Latest WBC 12.9 K/uL at 2161-11-20 02:28:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Administer levetiracetam to maintain adequate hydration. |
| M36753294-D43 | antimicrobials (MetRONIDAZOLE (FLagyl), Metronidazole) | Latest WBC 28.5 K/uL at 2141-05-23 14:53:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Administer levetiracetam to manage fluid imbalance and maintain blood pressure. |
| M36753294-D43 | calcium replacement (Calcium Gluconate) | Latest calcium 7.9 mg/dL at 2141-05-23 10:52:00 (reference 8.4 to 10.3) is low, consistent with 'low'. | Administer levetiracetam to manage fluid imbalance and maintain blood pressure. |
| M36753294-D43 | insulin (Insulin - Humalog) | Latest glucose 275 mg/dL (treatment threshold > 180). | Administer levetiracetam to manage fluid imbalance and maintain blood pressure. |
| M36753294-D43 | IV fluids (Dextrose 5%, NaCl 0.9%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 3.5 mmol/L at 2141-05-23 15:21:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer levetiracetam to manage fluid imbalance and maintain blood pressure. |
| M36753294-D43 | vasopressors (Phenylephrine) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. | Administer levetiracetam to manage fluid imbalance and maintain blood pressure. |
| M37267577-D44 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.1 mmol/L at 2137-06-13 14:13:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Continue sodium bicarbonate to maintain hydration. |
| M37267577-D44 | rate / rhythm control (Digoxin, Digoxin (Lanoxin)) | Median heart rate over the 6 h before the decision: 113 bpm (5 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Continue sodium bicarbonate to maintain hydration. |
| M37293400-D45 | IV fluids (0.9% Sodium Chloride, Dextrose 5%) | Latest lactate 2.5 mmol/L at 2133-12-19 16:32:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer dexamethasone to maintain serum potassium levels. |
| M37293400-D45 | vitamin K (Phytonadione, Vitamin K (Phytonadione)) | Latest INR 4.1  (treatment threshold > 1.5). | Administer dexamethasone to maintain serum potassium levels. |
| M38197705-D46 | albumin / colloid (Albumin 5%, Albumin 5% (12.5g / 250mL)) | Latest albumin 3.4 g/dL at 2116-12-03 12:13:00 (reference 3.5 to 5.2) is low, consistent with 'low'. | Continue packed red blood cells with close monitoring of respiratory parameters. |
| M38197705-D46 | calcium replacement (Calcium Gluconate) | Latest calcium 1.01 mmol/L at 2116-12-04 00:25:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Continue packed red blood cells with close monitoring of respiratory parameters. |
| M38197705-D46 | IV fluids (Dextrose 5%, LR) | Latest lactate 3.1 mmol/L at 2116-12-04 00:25:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Continue packed red blood cells with close monitoring of respiratory parameters. |
| M38430513-D47 | antimicrobials (Meropenem) | Latest WBC 11.1 K/uL at 2115-10-10 09:05:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Continue amiodarone with close monitoring of respiratory parameters. |
| M38430513-D47 | insulin (Insulin - Glargine) | Latest glucose 231 mg/dL (treatment threshold > 180). | Continue amiodarone with close monitoring of respiratory parameters. |
| M38430513-D47 | IV fluids (NaCl 0.9%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 6.3 mmol/L at 2115-10-10 03:36:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Continue amiodarone with close monitoring of respiratory parameters. |
| M38430513-D47 | vasopressors (Norepinephrine) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. | Continue amiodarone with close monitoring of respiratory parameters. |
| M38430513-D47 | vitamin K (Phytonadione) | Latest INR 4.1  (treatment threshold > 1.5). | Continue amiodarone with close monitoring of respiratory parameters. |
| M38540883-D48 | rate / rhythm control (Metoprolol Tartrate) | Median heart rate over the 6 h before the decision: 109 bpm (5 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Administer furosemide as ordered to maintain hydration. |
| M38540883-D48 | vitamin K (Vitamin K (Phytonadione)) | Latest INR 2  (treatment threshold > 1.5). | Administer furosemide as ordered to maintain hydration. |
| M39061571-D49 | antimicrobials (CefePIME, Cefepime) | Latest WBC 15.5 K/uL at 2185-01-18 18:15:00 (reference 4.0 to 11.0) is high, consistent with 'high'. Median temperature over the 6 h before the decision: 102.55 F (4 readings), high by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. | Administer heparin to maintain hydration. |
| M39061571-D49 | calcium replacement (Calcium Gluconate) | Latest calcium 1.03 mmol/L at 2185-01-18 18:24:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Administer heparin to maintain hydration. |
| M39061571-D49 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 5.8 mmol/L at 2185-01-18 18:24:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Administer heparin to maintain hydration. |
| M39061571-D49 | rate / rhythm control (Amiodarone, Amiodarone 600/500) | Median heart rate over the 6 h before the decision: 120 bpm (7 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Administer heparin to maintain hydration. |
| M39061571-D49 | invasive mechanical ventilation (Invasive Ventilation) | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: yes. Latest PaCO2 54 mm Hg at 2185-01-18 18:24:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Administer heparin to maintain hydration. |
| M39142259-D50 | phosphate replacement (K Phos, Neutra-Phos) | Latest phosphate 1.7 mg/dL at 2115-12-29 12:29:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Administer levetiracetam to maintain hydration and electrolyte balance. |
| M39268883-D51 | IV fluids (Dextrose 5%) | Latest lactate 2.7 mmol/L at 2180-02-21 10:15:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Continue sodium bicarbonate to manage blood glucose levels. |
| M39635619-D52 | antimicrobials (Piperacillin-Tazobactam, Piperacillin/Tazobactam (Zosyn)) | Median temperature over the 6 h before the decision: 100.5 °F (2 readings), high by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. | Continue dexamethasone with current settings. |
| M39711498-D53 | antimicrobials (CefePIME, Cefepime) | Latest WBC 11.5 K/uL at 2131-05-23 18:29:00 (reference 4.0 to 10.0) is high, consistent with 'high'. Median temperature over the 6 h before the decision: 101.1 °F (2 readings), high by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. | Continue packed red blood cells with close monitoring of respiratory parameters. |
| M39711498-D53 | invasive mechanical ventilation (Invasive Ventilation) | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: yes. | Continue packed red blood cells with close monitoring of respiratory parameters. |
| M39880770-D54 | cultures (Urine Culture) | Latest WBC 11.7 K/uL at 2147-12-31 02:38:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Continue norepinephrine with current settings. |
| M39880770-D54 | IV fluids (LR, Lactated Ringers) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. | Continue norepinephrine with current settings. |
| M30101877-D55 | insulin (Insulin - Humalog) | Latest glucose 216 mg/dL (treatment threshold > 180). | Administer vancomycin to manage hyperglycemia. |
| M30849778-D56 | antimicrobials (Azithromycin, Piperacillin/Tazobactam (Zosyn)) | Latest WBC 20.6 K/uL at 2153-02-13 02:21:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Continue levetiracetam to maintain hydration. |
| M30849778-D56 | IV fluids (0.9% Sodium Chloride, Dextrose 5%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 2.8 mmol/L at 2153-02-13 16:33:00 (reference 0.5 to 2.0) is high, consistent with 'high'. Latest sodium 154 mEq/L at 2153-02-13 22:19:00 (reference 133.0 to 145.0) is high, consistent with 'high'. | Continue levetiracetam to maintain hydration. |
| M30849778-D56 | phosphate replacement (K Phos, Potassium Phosphate) | Latest phosphate 1.2 mg/dL at 2153-02-13 22:19:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Continue levetiracetam to maintain hydration. |
| M30932571-D58 | antimicrobials (Acyclovir, Bactrim (SMX/TMP)) | Latest WBC 16.6 K/uL at 2116-02-29 12:58:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Continue sodium bicarbonate to maintain fluid balance. |
| M30932571-D58 | insulin (Insulin) | Latest glucose 251 mg/dL (treatment threshold > 180). | Continue sodium bicarbonate to maintain fluid balance. |
| M30932571-D58 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.8 mmol/L at 2116-02-29 13:25:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Continue sodium bicarbonate to maintain fluid balance. |
| M30932571-D58 | invasive mechanical ventilation (Invasive Ventilation) | Latest PaCO2 50 mm Hg at 2116-02-29 16:42:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Continue sodium bicarbonate to maintain fluid balance. |
| M32166508-D60 | calcium replacement (Calcium Gluconate) | Latest calcium 1.1 mmol/L at 2148-09-11 02:36:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Continue heparin. |
| M32166508-D60 | IV fluids (NaCl 0.9%) | Latest lactate 2.5 mmol/L at 2148-09-10 18:29:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Continue heparin. |
| M32166508-D60 | rate / rhythm control (Metoprolol, Metoprolol Tartrate) | Median heart rate over the 6 h before the decision: 122.5 bpm (8 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Continue heparin. |
| M32119961-S01 | antimicrobials (Vancomycin) | Latest WBC 13 K/uL at 2155-12-03 05:41:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue heparin therapy to manage coagulation status. |
| M32119961-S01 | IV fluids (Dextrose 5%, NaCl 0.9%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. | Discontinue heparin therapy to manage coagulation status. |
| M32119961-S01 | vasopressors (Norepinephrine) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. | Discontinue heparin therapy to manage coagulation status. |
| M32128372-S02 | albumin / colloid (Albumin 5%, Albumin 5% (25g / 500mL)) | Latest albumin 2.9 g/dL at 2137-02-26 13:03:00 (reference 3.5 to 5.2) is low, consistent with 'low'. | Discontinue mechanical ventilation with current settings. |
| M32128372-S02 | calcium replacement (Calcium Gluconate) | Latest calcium 1.07 mmol/L at 2137-02-26 22:38:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Discontinue mechanical ventilation with current settings. |
| M32128372-S02 | IV fluids (Dextrose 5%, LR) | Latest lactate 5.9 mmol/L at 2137-02-26 22:38:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue mechanical ventilation with current settings. |
| M32128372-S02 | rate / rhythm control (Amiodarone, Amiodarone 600/500) | Median heart rate over the 6 h before the decision: 127.5 bpm (6 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Discontinue mechanical ventilation with current settings. |
| M32128372-S02 | platelet / plasma transfusion (Fresh Frozen Plasma, Platelets) | Latest INR 2  (treatment threshold > 1.5). | Discontinue mechanical ventilation with current settings. |
| M32128372-S02 | vitamin K (Phytonadione) | Latest INR 2  (treatment threshold > 1.5). | Discontinue mechanical ventilation with current settings. |
| M32155744-S03 | antimicrobials (Cefazolin, Vancomycin) | Latest WBC 11.3 K/uL at 2111-01-18 00:21:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Discontinue intravenous fluid and electrolyte management. |
| M32155744-S03 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.8 mmol/L at 2111-01-17 20:13:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue intravenous fluid and electrolyte management. |
| M32391858-S04 | antimicrobials (CefazoLIN) | Latest WBC 14.8 K/uL at 2201-10-31 02:06:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Discontinue mechanical ventilation with current settings. |
| M32391858-S04 | calcium replacement (Calcium Gluconate) | Latest calcium 1.11 mmol/L at 2201-10-31 05:36:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Discontinue mechanical ventilation with current settings. |
| M33846653-S06 | insulin (Insulin, Insulin - Glargine) | Latest glucose 234 mg/dL (treatment threshold > 180). | Discontinue insulin therapy to manage hyperglycemia. |
| M34100191-S07 | antimicrobials (CefePIME, Cefepime) | Latest WBC 21.6 K/uL at 2196-02-25 14:54:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Discontinue intravenous fluid support. |
| M34100191-S07 | sodium bicarbonate (Sodium Bicarbonate, Sodium Bicarbonate 8.4%) | Latest pH 7.24 units at 2196-02-25 15:10:00 (reference 7.35 to 7.45) is low, consistent with 'low'. Latest bicarbonate 14 mEq/L at 2196-02-25 14:54:00 (reference 22.0 to 32.0) is low, consistent with 'low'. | Discontinue intravenous fluid support. |
| M34100191-S07 | calcium replacement (Calcium Gluconate) | Latest calcium 7.6 mg/dL at 2196-02-25 14:54:00 (reference 8.4 to 10.3) is low, consistent with 'low'. | Discontinue intravenous fluid support. |
| M34100191-S07 | cultures (Blood Cultured, Sputum Culture) | Latest WBC 21.6 K/uL at 2196-02-25 14:54:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Discontinue intravenous fluid support. |
| M34100191-S07 | insulin (Insulin, Insulin - Regular) | Latest glucose 195 mg/dL (treatment threshold > 180). | Discontinue intravenous fluid support. |
| M34100191-S07 | IV fluids (Dextrose 5%, LR) | Latest lactate 4.8 mmol/L at 2196-02-25 15:10:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue intravenous fluid support. |
| M34100191-S07 | potassium replacement (KCL (Bolus), Potassium Chloride) | Latest potassium 3 mEq/L at 2196-02-25 14:54:00 (reference 3.3 to 5.1) is low, consistent with 'low'. | Discontinue intravenous fluid support. |
| M34100191-S07 | rate / rhythm control (Amiodarone, Amiodarone 600/500) | Median heart rate over the 6 h before the decision: 109 bpm (5 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Discontinue intravenous fluid support. |
| M34100191-S07 | platelet / plasma transfusion (Platelets) | Latest platelets 29 K/uL (treatment threshold < 50). | Discontinue intravenous fluid support. |
| M34170353-S08 | albumin / colloid (Albumin 5%, Albumin 5% (12.5g / 250mL)) | Latest albumin 2.7 g/dL at 2149-10-03 02:35:00 (reference 3.5 to 5.2) is low, consistent with 'low'. | Discontinue intravenous calcium supplementation. |
| M34170353-S08 | calcium replacement (Calcium Gluconate, Calcium Gluconate sliding scale (Critical Care-Ionized calcium)) | Latest calcium 1.09 mmol/L at 2149-10-03 11:26:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Discontinue intravenous calcium supplementation. |
| M34170353-S08 | phosphate replacement (K Phos, Potassium Phosphate) | Latest phosphate 1.7 mg/dL at 2149-10-03 11:20:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Discontinue intravenous calcium supplementation. |
| M34499716-S09 | insulin (Insulin - Glargine, Insulin - Regular) | Latest glucose 359 mg/dL (treatment threshold > 180). | Discontinue mechanical ventilation with close monitoring of respiratory parameters. |
| M34499716-S09 | invasive mechanical ventilation (Invasive Ventilation) | Latest PaCO2 47 mm Hg at 2142-07-31 18:20:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Discontinue mechanical ventilation with close monitoring of respiratory parameters. |
| M34531557-S10 | antimicrobials (CefTRIAXone, Ceftriaxone) | Latest WBC 16 K/uL at 2117-03-15 01:45:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue intravenous fluid administration to maintain hydration. |
| M34531557-S10 | calcium replacement (Calcium Gluconate, Calcium Gluconate sliding scale (Critical Care-Ionized calcium)) | Latest calcium 7.9 mg/dL at 2117-03-15 01:45:00 (reference 8.4 to 10.3) is low, consistent with 'low'. | Discontinue intravenous fluid administration to maintain hydration. |
| M34578020-S11 | antimicrobials (CefePIME, Cefepime) | Latest WBC 13.1 K/uL at 2187-02-11 20:00:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue mechanical ventilation with close monitoring of respiratory parameters. |
| M34578020-S11 | calcium replacement (Calcium Gluconate) | Latest calcium 1.09 mmol/L at 2187-02-11 06:41:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Discontinue mechanical ventilation with close monitoring of respiratory parameters. |
| M35009126-S12 | antimicrobials (CefTAZidime, CefTRIAXone) | Latest WBC 16 K/uL at 2186-11-13 14:29:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue mechanical ventilation with current settings, ensuring adequate oxygenation and ventilation. |
| M35009126-S12 | cultures (Blood Cultured, Sputum Culture) | Latest WBC 16 K/uL at 2186-11-13 14:29:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue mechanical ventilation with current settings, ensuring adequate oxygenation and ventilation. |
| M35026312-S13 | insulin (Insulin - Regular, Insulin Human Regular) | Latest glucose 383 mg/dL (treatment threshold > 180). | Discontinue mechanical ventilation with current settings. |
| M35026312-S13 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.3 mmol/L at 2150-03-12 14:40:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue mechanical ventilation with current settings. |
| M35128235-S14 | calcium replacement (Calcium Gluconate) | Latest calcium 0.8 mmol/L at 2129-04-06 23:32:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Discontinue intravenous fluid and electrolyte management. |
| M35128235-S14 | phosphate replacement (K Phos, Potassium Phosphate) | Latest phosphate 1.3 mg/dL at 2129-04-06 17:15:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Discontinue intravenous fluid and electrolyte management. |
| M35436337-S15 | antimicrobials (Metronidazole, Piperacillin-Tazobactam) | Latest WBC 11.8 K/uL at 2185-06-17 01:07:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Discontinue intravenous fluid administration. |
| M35436337-S15 | calcium replacement (Calcium Gluconate) | Latest calcium 7.8 mg/dL at 2185-06-17 01:07:00 (reference 8.4 to 10.3) is low, consistent with 'low'. | Discontinue intravenous fluid administration. |
| M35514836-S16 | rate / rhythm control (Metoprolol, Metoprolol Tartrate) | Median heart rate over the 6 h before the decision: 102.5 bpm (4 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Discontinue intravenous fluid and electrolyte management. |
| M36059427-S17 | calcium replacement (Calcium Gluconate, Calcium Gluconate sliding scale (Critical Care-Ionized calcium)) | Latest calcium 1.03 mmol/L at 2123-02-20 23:15:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Discontinue mechanical ventilation with current settings. |
| M36059427-S17 | cultures (Blood Cultured, Sputum Culture) | Latest WBC 16.1 K/uL at 2123-02-20 18:35:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue mechanical ventilation with current settings. |
| M36059427-S17 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.1 mmol/L at 2123-02-20 23:15:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue mechanical ventilation with current settings. |
| M37267577-S19 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.1 mmol/L at 2137-06-13 14:13:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue IV fluid administration to maintain hydration. |
| M37267577-S19 | rate / rhythm control (Digoxin, Digoxin (Lanoxin)) | Median heart rate over the 6 h before the decision: 113 bpm (5 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Discontinue IV fluid administration to maintain hydration. |
| M37293400-S20 | IV fluids (0.9% Sodium Chloride, Dextrose 5%) | Latest lactate 2.5 mmol/L at 2133-12-19 16:32:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue neuromuscular blockade as per PAR-Activity. |
| M37293400-S20 | vitamin K (Phytonadione, Vitamin K (Phytonadione)) | Latest INR 4.1  (treatment threshold > 1.5). | Discontinue neuromuscular blockade as per PAR-Activity. |
| M38197705-S21 | albumin / colloid (Albumin 5%, Albumin 5% (12.5g / 250mL)) | Latest albumin 3.4 g/dL at 2116-12-03 12:13:00 (reference 3.5 to 5.2) is low, consistent with 'low'. | Discontinue mechanical ventilation with close monitoring of respiratory parameters. |
| M38197705-S21 | calcium replacement (Calcium Gluconate) | Latest calcium 1.01 mmol/L at 2116-12-04 00:25:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Discontinue mechanical ventilation with close monitoring of respiratory parameters. |
| M38197705-S21 | IV fluids (Dextrose 5%, LR) | Latest lactate 3.1 mmol/L at 2116-12-04 00:25:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue mechanical ventilation with close monitoring of respiratory parameters. |
| M38430513-S22 | antimicrobials (Meropenem) | Latest WBC 11.1 K/uL at 2115-10-10 09:05:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue mechanical ventilation with close monitoring of respiratory parameters. |
| M38430513-S22 | insulin (Insulin - Glargine) | Latest glucose 231 mg/dL (treatment threshold > 180). | Discontinue mechanical ventilation with close monitoring of respiratory parameters. |
| M38430513-S22 | IV fluids (NaCl 0.9%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 6.3 mmol/L at 2115-10-10 03:36:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue mechanical ventilation with close monitoring of respiratory parameters. |
| M38430513-S22 | vasopressors (Norepinephrine) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. | Discontinue mechanical ventilation with close monitoring of respiratory parameters. |
| M38430513-S22 | vitamin K (Phytonadione) | Latest INR 4.1  (treatment threshold > 1.5). | Discontinue mechanical ventilation with close monitoring of respiratory parameters. |
| M39142259-S23 | phosphate replacement (K Phos, Neutra-Phos) | Latest phosphate 1.7 mg/dL at 2115-12-29 12:29:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Discontinue anticoagulation therapy with Heparin Sodium. |
| M39268883-S24 | IV fluids (Dextrose 5%) | Latest lactate 2.7 mmol/L at 2180-02-21 10:15:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue insulin therapy to manage blood glucose levels. |
| M39635619-S25 | antimicrobials (Piperacillin-Tazobactam, Piperacillin/Tazobactam (Zosyn)) | Median temperature over the 6 h before the decision: 100.5 °F (2 readings), high by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. | Discontinue mechanical ventilation with current settings. |
| M39711498-S26 | antimicrobials (CefePIME, Cefepime) | Latest WBC 11.5 K/uL at 2131-05-23 18:29:00 (reference 4.0 to 10.0) is high, consistent with 'high'. Median temperature over the 6 h before the decision: 101.1 °F (2 readings), high by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. | Discontinue mechanical ventilation with close monitoring of respiratory parameters. |
| M39711498-S26 | invasive mechanical ventilation (Invasive Ventilation) | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: yes. | Discontinue mechanical ventilation with close monitoring of respiratory parameters. |
| M39880770-S27 | cultures (Urine Culture) | Latest WBC 11.7 K/uL at 2147-12-31 02:38:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue mechanical ventilation with current settings. |
| M39880770-S27 | IV fluids (LR, Lactated Ringers) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. | Discontinue mechanical ventilation with current settings. |
| M30665396-S29 | IV fluids (Dextrose 5%) | Latest lactate 2.4 mmol/L at 2167-05-06 05:23:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue aggressive fluid resuscitation with intravenous fluids. |
| M30757476-S30 | hypoglycemia treatment (Dextrose 50%) | Latest glucose 34 mg/dL at 2131-02-28 04:16:00 (reference 70.0 to 100.0) is low, consistent with 'low'. | Discontinue mechanical ventilation settings to maintain adequate oxygenation and ventilation. |
| M30757476-S30 | phosphate replacement (Na Phos) | Latest phosphate 1.2 mg/dL at 2131-02-28 04:16:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Discontinue mechanical ventilation settings to maintain adequate oxygenation and ventilation. |
| M30757476-S30 | invasive mechanical ventilation (Invasive Ventilation) | Latest PaCO2 47 mm Hg at 2131-02-28 12:17:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Discontinue mechanical ventilation settings to maintain adequate oxygenation and ventilation. |
| M30849778-S31 | antimicrobials (Azithromycin, Piperacillin/Tazobactam (Zosyn)) | Latest WBC 20.6 K/uL at 2153-02-13 02:21:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Discontinue intravenous fluid management to maintain hydration. |
| M30849778-S31 | IV fluids (0.9% Sodium Chloride, Dextrose 5%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 2.8 mmol/L at 2153-02-13 16:33:00 (reference 0.5 to 2.0) is high, consistent with 'high'. Latest sodium 154 mEq/L at 2153-02-13 22:19:00 (reference 133.0 to 145.0) is high, consistent with 'high'. | Discontinue intravenous fluid management to maintain hydration. |
| M30849778-S31 | phosphate replacement (K Phos, Potassium Phosphate) | Latest phosphate 1.2 mg/dL at 2153-02-13 22:19:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Discontinue intravenous fluid management to maintain hydration. |
| M30932571-S33 | antimicrobials (Acyclovir, Bactrim (SMX/TMP)) | Latest WBC 16.6 K/uL at 2116-02-29 12:58:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue intravenous fluids to maintain fluid balance. |
| M30932571-S33 | insulin (Insulin) | Latest glucose 251 mg/dL (treatment threshold > 180). | Discontinue intravenous fluids to maintain fluid balance. |
| M30932571-S33 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.8 mmol/L at 2116-02-29 13:25:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue intravenous fluids to maintain fluid balance. |
| M30932571-S33 | invasive mechanical ventilation (Invasive Ventilation) | Latest PaCO2 50 mm Hg at 2116-02-29 16:42:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Discontinue intravenous fluids to maintain fluid balance. |
| M31269608-S35 | calcium replacement (Calcium Gluconate) | Latest calcium 7.8 mg/dL at 2154-04-25 03:59:00 (reference 8.4 to 10.3) is low, consistent with 'low'. | Discontinue dexamethasone administration. |
| M31269608-S35 | potassium replacement (Potassium Chloride, Potassium Chloride Replacement (Critical Care and Oncology)) | Latest potassium 3 mEq/L at 2154-04-25 03:59:00 (reference 3.3 to 5.1) is low, consistent with 'low'. | Discontinue dexamethasone administration. |
| M31338022-S36 | antihypertensives (Lisinopril) | 'blood pressure high' holds when any component is high. systolic BP: yes; mean arterial pressure: no. | Discontinue IV fluids as ordered. |
| M32166508-S37 | calcium replacement (Calcium Gluconate) | Latest calcium 1.1 mmol/L at 2148-09-11 02:36:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Discontinue intravenous fluid support. |
| M32166508-S37 | IV fluids (NaCl 0.9%) | Latest lactate 2.5 mmol/L at 2148-09-10 18:29:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue intravenous fluid support. |
| M32166508-S37 | rate / rhythm control (Metoprolol, Metoprolol Tartrate) | Median heart rate over the 6 h before the decision: 122.5 bpm (8 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Discontinue intravenous fluid support. |
| M32359580-S38 | antimicrobials (CefePIME, Cefepime) | Latest WBC 11.2 K/uL at 2146-06-23 09:20:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue vasopressor support due to low blood pressure. |
| M32359580-S38 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 9 mmol/L at 2146-06-23 09:22:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue vasopressor support due to low blood pressure. |
| M32359580-S38 | platelet / plasma transfusion (Cryoprecipitate, Fresh Frozen Plasma) | Latest INR 2.7  (treatment threshold > 1.5). | Discontinue vasopressor support due to low blood pressure. |
| M32359580-S38 | red cell transfusion (Packed Red Blood Cells) | Latest hemoglobin 6.3 g/dL (treatment threshold < 7). | Discontinue vasopressor support due to low blood pressure. |
| M32587226-S39 | IV fluids (Dextrose 5%, LR) | Latest lactate 2.2 mmol/L at 2125-09-25 12:12:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue administration of analgesics and sedatives as per current regimen. |
| M33281088-S41 | antimicrobials (CefePIME, Cefepime) | Latest WBC 13.2 K/uL at 2140-01-24 11:52:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue the current antibiotic therapy with MetRONIDAZOLE if there are signs of infection. |
| M33281088-S41 | sodium bicarbonate (Sodium Bicarbonate 8.4%) | Latest bicarbonate 9 mEq/L at 2140-01-24 11:56:00 (reference 22.0 to 32.0) is low, consistent with 'low'. | Discontinue the current antibiotic therapy with MetRONIDAZOLE if there are signs of infection. |
| M33281088-S41 | calcium replacement (Calcium Gluconate, Calcium Gluconate sliding scale (Critical Care-Ionized calcium)) | Latest calcium 1.1 mmol/L at 2140-01-24 12:15:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Discontinue the current antibiotic therapy with MetRONIDAZOLE if there are signs of infection. |
| M33281088-S41 | insulin (Insulin, Insulin - Humalog) | Latest glucose 311 mg/dL (treatment threshold > 180). | Discontinue the current antibiotic therapy with MetRONIDAZOLE if there are signs of infection. |
| M33281088-S41 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 7.2 mmol/L at 2140-01-24 17:30:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue the current antibiotic therapy with MetRONIDAZOLE if there are signs of infection. |
| M33281088-S41 | potassium replacement (Potassium Chloride, Potassium Chloride Replacement (Critical Care and Oncology)) | Latest potassium 3 mEq/L at 2140-01-24 11:56:00 (reference 3.3 to 5.1) is low, consistent with 'low'. | Discontinue the current antibiotic therapy with MetRONIDAZOLE if there are signs of infection. |
| M33558396-S43 | antimicrobials (Cefazolin) | Latest WBC 20.7 K/uL at 2125-02-28 02:46:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Discontinue intravenous fluids and electrolyte monitoring. |
| M33558396-S43 | IV fluids (Dextrose 5%, NaCl 0.9%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 2.4 mmol/L at 2125-02-27 23:54:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue intravenous fluids and electrolyte monitoring. |
| M33683112-S44 | antimicrobials (Azithromycin, CefePIME) | Latest WBC 21.3 K/uL at 2189-06-10 04:02:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue bisacodyl for bowel management. |
| M33987268-S45 | antimicrobials (Azithromycin, CeftriaXONE) | Latest WBC 27.9 K/uL at 2156-04-13 01:41:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Discontinue pain management. |
| M33987268-S45 | IV fluids (Dextrose 5%, LR) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 2.4 mmol/L at 2156-04-13 14:02:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue pain management. |
| M34629895-S46 | antimicrobials (CefazoLIN, Cefazolin) | Latest WBC 13.8 K/uL at 2130-10-28 04:01:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Discontinue pain management. |
| M36107367-S48 | antimicrobials (Ciprofloxacin IV, MetroNIDAZOLE) | Latest WBC 10.4 K/uL at 2148-01-25 02:25:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue IV fluids to maintain adequate hydration. |
| M36107367-S48 | invasive mechanical ventilation (Invasive Ventilation) | Latest PaCO2 59 mm Hg at 2148-01-24 05:30:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Discontinue IV fluids to maintain adequate hydration. |
| M37049133-S49 | phosphate replacement (Neutra-Phos) | Latest phosphate 2.6 mg/dL at 2196-04-15 03:36:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Discontinue intravenous fluids to maintain hydration and electrolyte balance. |
| M37057036-S50 | antimicrobials (Piperacillin/Tazobactam (Zosyn), Vancomycin) | Latest WBC 10.2 K/uL at 2178-07-04 09:34:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue insulin management to maintain normoglycemia. |
| M37057036-S50 | invasive mechanical ventilation (Invasive Ventilation) | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: yes. Latest PaCO2 47 mm Hg at 2178-07-04 01:03:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Discontinue insulin management to maintain normoglycemia. |
| M37127068-S51 | antimicrobials (CeFAZolin, Cefazolin) | Latest WBC 15.8 K/uL at 2187-07-30 02:04:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue appropriate antibiotic coverage. |
| M39061571-S55 | antimicrobials (CefePIME, Cefepime) | Latest WBC 15.5 K/uL at 2185-01-18 18:15:00 (reference 4.0 to 11.0) is high, consistent with 'high'. Median temperature over the 6 h before the decision: 102.55 F (4 readings), high by the rule 'fever > 38.0 C (100.4 F); hypothermia < 36.0 C (96.8 F); Celsius rows are converted to F'. | Discontinue mechanical ventilation with close monitoring of ventilator settings. |
| M39061571-S55 | calcium replacement (Calcium Gluconate) | Latest calcium 1.03 mmol/L at 2185-01-18 18:24:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Discontinue mechanical ventilation with close monitoring of ventilator settings. |
| M39061571-S55 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 5.8 mmol/L at 2185-01-18 18:24:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue mechanical ventilation with close monitoring of ventilator settings. |
| M39061571-S55 | rate / rhythm control (Amiodarone, Amiodarone 600/500) | Median heart rate over the 6 h before the decision: 120 bpm (7 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Discontinue mechanical ventilation with close monitoring of ventilator settings. |
| M39061571-S55 | invasive mechanical ventilation (Invasive Ventilation) | 'oxygenation low' holds when any component is low. SpO2: no; PaO2: yes. Latest PaCO2 54 mm Hg at 2185-01-18 18:24:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Discontinue mechanical ventilation with close monitoring of ventilator settings. |
| M39084876-S56 | antimicrobials (Cefazolin) | Latest WBC 10.6 K/uL at 2120-05-14 03:00:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue pain management with oral acetaminophen. |
| M39084876-S56 | IV fluids (Dextrose 5%) | Latest lactate 2.2 mmol/L at 2120-05-13 19:45:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue pain management with oral acetaminophen. |
| M30932571-S58 | antimicrobials (Acyclovir, Bactrim (SMX/TMP)) | Latest WBC 16.6 K/uL at 2116-02-29 12:58:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Discontinue mechanical ventilation support. |
| M30932571-S58 | insulin (Insulin) | Latest glucose 251 mg/dL (treatment threshold > 180). | Discontinue mechanical ventilation support. |
| M30932571-S58 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.8 mmol/L at 2116-02-29 13:25:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue mechanical ventilation support. |
| M30932571-S58 | invasive mechanical ventilation (Invasive Ventilation) | Latest PaCO2 50 mm Hg at 2116-02-29 16:42:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Discontinue mechanical ventilation support. |
| M32128372-S59 | albumin / colloid (Albumin 5%, Albumin 5% (25g / 500mL)) | Latest albumin 2.9 g/dL at 2137-02-26 13:03:00 (reference 3.5 to 5.2) is low, consistent with 'low'. | Discontinue mechanical ventilation support. |
| M32128372-S59 | calcium replacement (Calcium Gluconate) | Latest calcium 1.07 mmol/L at 2137-02-26 22:38:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Discontinue mechanical ventilation support. |
| M32128372-S59 | IV fluids (Dextrose 5%, LR) | Latest lactate 5.9 mmol/L at 2137-02-26 22:38:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue mechanical ventilation support. |
| M32128372-S59 | rate / rhythm control (Amiodarone, Amiodarone 600/500) | Median heart rate over the 6 h before the decision: 127.5 bpm (6 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Discontinue mechanical ventilation support. |
| M32128372-S59 | platelet / plasma transfusion (Fresh Frozen Plasma, Platelets) | Latest INR 2  (treatment threshold > 1.5). | Discontinue mechanical ventilation support. |
| M32128372-S59 | vitamin K (Phytonadione) | Latest INR 2  (treatment threshold > 1.5). | Discontinue mechanical ventilation support. |
| M32155744-S60 | antimicrobials (Cefazolin, Vancomycin) | Latest WBC 11.3 K/uL at 2111-01-18 00:21:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Discontinue IV inotrope support with phenylephrine to maintain adequate blood pressure. |
| M32155744-S60 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.8 mmol/L at 2111-01-17 20:13:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Discontinue IV inotrope support with phenylephrine to maintain adequate blood pressure. |
| M30057454-A01 | antimicrobials (Cefazolin) | Latest WBC 17.8 K/uL at 2171-11-15 02:53:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Start amiodarone. |
| M30057454-A01 | calcium replacement (Calcium Gluconate) | Latest calcium 0.83 mmol/L at 2171-11-15 09:01:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Start amiodarone. |
| M30057454-A01 | IV fluids (Dextrose 5%, NaCl 0.9%) | 'blood pressure low' holds when any component is low. systolic BP: yes; mean arterial pressure: yes. | Start amiodarone. |
| M30057454-A01 | potassium replacement (KCL (Bolus), Potassium Chloride) | Latest potassium 2.3 mEq/L at 2171-11-15 09:01:00 (reference 3.3 to 5.1) is low, consistent with 'low'. | Start amiodarone. |
| M30057454-A01 | vasopressors (DOBUTamine, DOPamine) | 'blood pressure low' holds when any component is low. systolic BP: yes; mean arterial pressure: yes. | Start amiodarone. |
| M30101877-A02 | insulin (Insulin - Humalog) | Latest glucose 216 mg/dL (treatment threshold > 180). | Start vancomycin. |
| M30665396-A05 | IV fluids (Dextrose 5%) | Latest lactate 2.4 mmol/L at 2167-05-06 05:23:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start levetiracetam. |
| M30757476-A06 | hypoglycemia treatment (Dextrose 50%) | Latest glucose 34 mg/dL at 2131-02-28 04:16:00 (reference 70.0 to 100.0) is low, consistent with 'low'. | Start levetiracetam. |
| M30757476-A06 | phosphate replacement (Na Phos) | Latest phosphate 1.2 mg/dL at 2131-02-28 04:16:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Start levetiracetam. |
| M30757476-A06 | invasive mechanical ventilation (Invasive Ventilation) | Latest PaCO2 47 mm Hg at 2131-02-28 12:17:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Start levetiracetam. |
| M30849778-A07 | antimicrobials (Azithromycin, Piperacillin/Tazobactam (Zosyn)) | Latest WBC 20.6 K/uL at 2153-02-13 02:21:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Start levetiracetam. |
| M30849778-A07 | IV fluids (0.9% Sodium Chloride, Dextrose 5%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 2.8 mmol/L at 2153-02-13 16:33:00 (reference 0.5 to 2.0) is high, consistent with 'high'. Latest sodium 154 mEq/L at 2153-02-13 22:19:00 (reference 133.0 to 145.0) is high, consistent with 'high'. | Start levetiracetam. |
| M30849778-A07 | phosphate replacement (K Phos, Potassium Phosphate) | Latest phosphate 1.2 mg/dL at 2153-02-13 22:19:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Start levetiracetam. |
| M30932571-A09 | antimicrobials (Acyclovir, Bactrim (SMX/TMP)) | Latest WBC 16.6 K/uL at 2116-02-29 12:58:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Start sodium bicarbonate. |
| M30932571-A09 | insulin (Insulin) | Latest glucose 251 mg/dL (treatment threshold > 180). | Start sodium bicarbonate. |
| M30932571-A09 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.8 mmol/L at 2116-02-29 13:25:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start sodium bicarbonate. |
| M30932571-A09 | invasive mechanical ventilation (Invasive Ventilation) | Latest PaCO2 50 mm Hg at 2116-02-29 16:42:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Start sodium bicarbonate. |
| M31269608-A11 | calcium replacement (Calcium Gluconate) | Latest calcium 7.8 mg/dL at 2154-04-25 03:59:00 (reference 8.4 to 10.3) is low, consistent with 'low'. | Start norepinephrine. |
| M31269608-A11 | potassium replacement (Potassium Chloride, Potassium Chloride Replacement (Critical Care and Oncology)) | Latest potassium 3 mEq/L at 2154-04-25 03:59:00 (reference 3.3 to 5.1) is low, consistent with 'low'. | Start norepinephrine. |
| M31338022-A12 | antihypertensives (Lisinopril) | 'blood pressure high' holds when any component is high. systolic BP: yes; mean arterial pressure: no. | Start dexamethasone. |
| M31494479-A13 | IV fluids (Dextrose 5%) | Latest lactate 3.1 mmol/L at 2141-12-17 13:32:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start dexamethasone. |
| M31959184-A15 | insulin (Insulin - Regular) | Latest glucose 226 mg/dL (treatment threshold > 180). | Start norepinephrine. |
| M31959184-A15 | IV fluids (LR) | Latest lactate 2.3 mmol/L at 2110-11-30 16:43:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start norepinephrine. |
| M32119961-A16 | antimicrobials (Vancomycin) | Latest WBC 13 K/uL at 2155-12-03 05:41:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Start furosemide. |
| M32119961-A16 | IV fluids (Dextrose 5%, NaCl 0.9%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. | Start furosemide. |
| M32119961-A16 | vasopressors (Norepinephrine) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. | Start furosemide. |
| M32128372-A17 | albumin / colloid (Albumin 5%, Albumin 5% (25g / 500mL)) | Latest albumin 2.9 g/dL at 2137-02-26 13:03:00 (reference 3.5 to 5.2) is low, consistent with 'low'. | Start furosemide. |
| M32128372-A17 | calcium replacement (Calcium Gluconate) | Latest calcium 1.07 mmol/L at 2137-02-26 22:38:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Start furosemide. |
| M32128372-A17 | IV fluids (Dextrose 5%, LR) | Latest lactate 5.9 mmol/L at 2137-02-26 22:38:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start furosemide. |
| M32128372-A17 | rate / rhythm control (Amiodarone, Amiodarone 600/500) | Median heart rate over the 6 h before the decision: 127.5 bpm (6 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Start furosemide. |
| M32128372-A17 | platelet / plasma transfusion (Fresh Frozen Plasma, Platelets) | Latest INR 2  (treatment threshold > 1.5). | Start furosemide. |
| M32128372-A17 | vitamin K (Phytonadione) | Latest INR 2  (treatment threshold > 1.5). | Start furosemide. |
| M32155744-A18 | antimicrobials (Cefazolin, Vancomycin) | Latest WBC 11.3 K/uL at 2111-01-18 00:21:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Start heparin. |
| M32155744-A18 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.8 mmol/L at 2111-01-17 20:13:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start heparin. |
| M32166508-A19 | calcium replacement (Calcium Gluconate) | Latest calcium 1.1 mmol/L at 2148-09-11 02:36:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Start heparin. |
| M32166508-A19 | IV fluids (NaCl 0.9%) | Latest lactate 2.5 mmol/L at 2148-09-10 18:29:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start heparin. |
| M32166508-A19 | rate / rhythm control (Metoprolol, Metoprolol Tartrate) | Median heart rate over the 6 h before the decision: 122.5 bpm (8 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Start heparin. |
| M32283063-A20 | antimicrobials (Cefazolin) | Latest WBC 16.7 K/uL at 2118-11-17 02:23:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Start levetiracetam. |
| M32283063-A20 | IV fluids (Dextrose 5%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 2.1 mmol/L at 2118-11-16 21:15:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start levetiracetam. |
| M32359580-A21 | antimicrobials (CefePIME, Cefepime) | Latest WBC 11.2 K/uL at 2146-06-23 09:20:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Start levetiracetam. |
| M32359580-A21 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 9 mmol/L at 2146-06-23 09:22:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start levetiracetam. |
| M32359580-A21 | platelet / plasma transfusion (Cryoprecipitate, Fresh Frozen Plasma) | Latest INR 2.7  (treatment threshold > 1.5). | Start levetiracetam. |
| M32359580-A21 | red cell transfusion (Packed Red Blood Cells) | Latest hemoglobin 6.3 g/dL (treatment threshold < 7). | Start levetiracetam. |
| M32391858-A23 | antimicrobials (CefazoLIN) | Latest WBC 14.8 K/uL at 2201-10-31 02:06:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Start sodium bicarbonate. |
| M32391858-A23 | calcium replacement (Calcium Gluconate) | Latest calcium 1.11 mmol/L at 2201-10-31 05:36:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Start sodium bicarbonate. |
| M32587226-A25 | IV fluids (Dextrose 5%, LR) | Latest lactate 2.2 mmol/L at 2125-09-25 12:12:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start calcium gluconate. |
| M32604416-A26 | antimicrobials (Ciprofloxacin, Vancomycin) | Latest WBC 14.9 K/uL at 2132-12-16 02:14:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Start dexamethasone. |
| M32604416-A26 | calcium replacement (Calcium Gluconate) | Latest calcium 1.11 mmol/L at 2132-12-16 02:26:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Start dexamethasone. |
| M32604416-A26 | IV fluids (Dextrose 5%, NaCl 0.9%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 2.3 mmol/L at 2132-12-15 12:57:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start dexamethasone. |
| M33281088-A28 | antimicrobials (CefePIME, Cefepime) | Latest WBC 13.2 K/uL at 2140-01-24 11:52:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Start packed red blood cells. |
| M33281088-A28 | sodium bicarbonate (Sodium Bicarbonate 8.4%) | Latest bicarbonate 9 mEq/L at 2140-01-24 11:56:00 (reference 22.0 to 32.0) is low, consistent with 'low'. | Start packed red blood cells. |
| M33281088-A28 | calcium replacement (Calcium Gluconate, Calcium Gluconate sliding scale (Critical Care-Ionized calcium)) | Latest calcium 1.1 mmol/L at 2140-01-24 12:15:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Start packed red blood cells. |
| M33281088-A28 | insulin (Insulin, Insulin - Humalog) | Latest glucose 311 mg/dL (treatment threshold > 180). | Start packed red blood cells. |
| M33281088-A28 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 7.2 mmol/L at 2140-01-24 17:30:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start packed red blood cells. |
| M33281088-A28 | potassium replacement (Potassium Chloride, Potassium Chloride Replacement (Critical Care and Oncology)) | Latest potassium 3 mEq/L at 2140-01-24 11:56:00 (reference 3.3 to 5.1) is low, consistent with 'low'. | Start packed red blood cells. |
| M33558396-A31 | antimicrobials (Cefazolin) | Latest WBC 20.7 K/uL at 2125-02-28 02:46:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Start furosemide. |
| M33558396-A31 | IV fluids (Dextrose 5%, NaCl 0.9%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 2.4 mmol/L at 2125-02-27 23:54:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start furosemide. |
| M33683112-A32 | antimicrobials (Azithromycin, CefePIME) | Latest WBC 21.3 K/uL at 2189-06-10 04:02:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Start insulin. |
| M33846653-A33 | insulin (Insulin, Insulin - Glargine) | Latest glucose 234 mg/dL (treatment threshold > 180). | Start amiodarone. |
| M33987268-A34 | antimicrobials (Azithromycin, CeftriaXONE) | Latest WBC 27.9 K/uL at 2156-04-13 01:41:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Start propofol. |
| M33987268-A34 | IV fluids (Dextrose 5%, LR) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 2.4 mmol/L at 2156-04-13 14:02:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start propofol. |
| M34100191-A35 | antimicrobials (CefePIME, Cefepime) | Latest WBC 21.6 K/uL at 2196-02-25 14:54:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Start heparin. |
| M34100191-A35 | sodium bicarbonate (Sodium Bicarbonate, Sodium Bicarbonate 8.4%) | Latest pH 7.24 units at 2196-02-25 15:10:00 (reference 7.35 to 7.45) is low, consistent with 'low'. Latest bicarbonate 14 mEq/L at 2196-02-25 14:54:00 (reference 22.0 to 32.0) is low, consistent with 'low'. | Start heparin. |
| M34100191-A35 | calcium replacement (Calcium Gluconate) | Latest calcium 7.6 mg/dL at 2196-02-25 14:54:00 (reference 8.4 to 10.3) is low, consistent with 'low'. | Start heparin. |
| M34100191-A35 | cultures (Blood Cultured, Sputum Culture) | Latest WBC 21.6 K/uL at 2196-02-25 14:54:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Start heparin. |
| M34100191-A35 | insulin (Insulin, Insulin - Regular) | Latest glucose 195 mg/dL (treatment threshold > 180). | Start heparin. |
| M34100191-A35 | IV fluids (Dextrose 5%, LR) | Latest lactate 4.8 mmol/L at 2196-02-25 15:10:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start heparin. |
| M34100191-A35 | potassium replacement (KCL (Bolus), Potassium Chloride) | Latest potassium 3 mEq/L at 2196-02-25 14:54:00 (reference 3.3 to 5.1) is low, consistent with 'low'. | Start heparin. |
| M34100191-A35 | rate / rhythm control (Amiodarone, Amiodarone 600/500) | Median heart rate over the 6 h before the decision: 109 bpm (5 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Start heparin. |
| M34100191-A35 | platelet / plasma transfusion (Platelets) | Latest platelets 29 K/uL (treatment threshold < 50). | Start heparin. |
| M34107647-A36 | antimicrobials (Ciprofloxacin, Ciprofloxacin HCl) | Latest WBC 116.1 K/uL at 2153-03-28 03:16:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Start levetiracetam. |
| M34107647-A36 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 3.7 mmol/L at 2153-03-28 20:00:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start levetiracetam. |
| M34170353-A37 | albumin / colloid (Albumin 5%, Albumin 5% (12.5g / 250mL)) | Latest albumin 2.7 g/dL at 2149-10-03 02:35:00 (reference 3.5 to 5.2) is low, consistent with 'low'. | Start sodium bicarbonate. |
| M34170353-A37 | calcium replacement (Calcium Gluconate, Calcium Gluconate sliding scale (Critical Care-Ionized calcium)) | Latest calcium 1.09 mmol/L at 2149-10-03 11:26:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Start sodium bicarbonate. |
| M34170353-A37 | phosphate replacement (K Phos, Potassium Phosphate) | Latest phosphate 1.7 mg/dL at 2149-10-03 11:20:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Start sodium bicarbonate. |
| M34499716-A39 | insulin (Insulin - Glargine, Insulin - Regular) | Latest glucose 359 mg/dL (treatment threshold > 180). | Start packed red blood cells. |
| M34499716-A39 | invasive mechanical ventilation (Invasive Ventilation) | Latest PaCO2 47 mm Hg at 2142-07-31 18:20:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Start packed red blood cells. |
| M34531557-A40 | antimicrobials (CefTRIAXone, Ceftriaxone) | Latest WBC 16 K/uL at 2117-03-15 01:45:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Start dexamethasone. |
| M34531557-A40 | calcium replacement (Calcium Gluconate, Calcium Gluconate sliding scale (Critical Care-Ionized calcium)) | Latest calcium 7.9 mg/dL at 2117-03-15 01:45:00 (reference 8.4 to 10.3) is low, consistent with 'low'. | Start dexamethasone. |
| M34578020-A41 | antimicrobials (CefePIME, Cefepime) | Latest WBC 13.1 K/uL at 2187-02-11 20:00:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Start dexamethasone. |
| M34578020-A41 | calcium replacement (Calcium Gluconate) | Latest calcium 1.09 mmol/L at 2187-02-11 06:41:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Start dexamethasone. |
| M34629895-A42 | antimicrobials (CefazoLIN, Cefazolin) | Latest WBC 13.8 K/uL at 2130-10-28 04:01:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Start heparin. |
| M35009126-A43 | antimicrobials (CefTAZidime, CefTRIAXone) | Latest WBC 16 K/uL at 2186-11-13 14:29:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Start furosemide. |
| M35009126-A43 | cultures (Blood Cultured, Sputum Culture) | Latest WBC 16 K/uL at 2186-11-13 14:29:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Start furosemide. |
| M35026312-A44 | insulin (Insulin - Regular, Insulin Human Regular) | Latest glucose 383 mg/dL (treatment threshold > 180). | Start furosemide. |
| M35026312-A44 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.3 mmol/L at 2150-03-12 14:40:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start furosemide. |
| M35128235-A45 | calcium replacement (Calcium Gluconate) | Latest calcium 0.8 mmol/L at 2129-04-06 23:32:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Start furosemide. |
| M35128235-A45 | phosphate replacement (K Phos, Potassium Phosphate) | Latest phosphate 1.3 mg/dL at 2129-04-06 17:15:00 (reference 2.7 to 4.5) is low, consistent with 'low'. | Start furosemide. |
| M35258379-A46 | calcium replacement (Calcium Gluconate) | Latest calcium 1.11 mmol/L at 2153-09-20 03:22:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Start levetiracetam. |
| M35436337-A47 | antimicrobials (Metronidazole, Piperacillin-Tazobactam) | Latest WBC 11.8 K/uL at 2185-06-17 01:07:00 (reference 4.0 to 11.0) is high, consistent with 'high'. | Start amiodarone. |
| M35436337-A47 | calcium replacement (Calcium Gluconate) | Latest calcium 7.8 mg/dL at 2185-06-17 01:07:00 (reference 8.4 to 10.3) is low, consistent with 'low'. | Start amiodarone. |
| M35514836-A49 | rate / rhythm control (Metoprolol, Metoprolol Tartrate) | Median heart rate over the 6 h before the decision: 102.5 bpm (4 readings), high by the rule 'tachycardia HR > 100; bradycardia HR < 60'. | Start levetiracetam. |
| M36059427-A53 | calcium replacement (Calcium Gluconate, Calcium Gluconate sliding scale (Critical Care-Ionized calcium)) | Latest calcium 1.03 mmol/L at 2123-02-20 23:15:00 (reference 1.12 to 1.32) is low, consistent with 'low'. | Start dexamethasone. |
| M36059427-A53 | cultures (Blood Cultured, Sputum Culture) | Latest WBC 16.1 K/uL at 2123-02-20 18:35:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Start dexamethasone. |
| M36059427-A53 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.1 mmol/L at 2123-02-20 23:15:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start dexamethasone. |
| M36091287-A54 | antimicrobials (Ampicillin-Sulbactam, Ampicillin/Sulbactam (Unasyn)) | Latest WBC 15.1 K/uL at 2119-10-27 02:32:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Start dexamethasone. |
| M36091287-A54 | IV fluids (Dextrose 5%, NaCl 0.9%) | Latest lactate 2.6 mmol/L at 2119-10-26 07:22:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start dexamethasone. |
| M36107367-A55 | antimicrobials (Ciprofloxacin IV, MetroNIDAZOLE) | Latest WBC 10.4 K/uL at 2148-01-25 02:25:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Start levetiracetam. |
| M36107367-A55 | invasive mechanical ventilation (Invasive Ventilation) | Latest PaCO2 59 mm Hg at 2148-01-24 05:30:00 (reference 35.0 to 45.0) is high, consistent with 'high'. | Start levetiracetam. |
| M36558922-A58 | antimicrobials (CefazoLIN, Cefazolin) | Latest WBC 12.9 K/uL at 2161-11-20 02:28:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Start levetiracetam. |
| M36753294-A59 | antimicrobials (MetRONIDAZOLE (FLagyl), Metronidazole) | Latest WBC 28.5 K/uL at 2141-05-23 14:53:00 (reference 4.0 to 10.0) is high, consistent with 'high'. | Start levetiracetam. |
| M36753294-A59 | calcium replacement (Calcium Gluconate) | Latest calcium 7.9 mg/dL at 2141-05-23 10:52:00 (reference 8.4 to 10.3) is low, consistent with 'low'. | Start levetiracetam. |
| M36753294-A59 | insulin (Insulin - Humalog) | Latest glucose 275 mg/dL (treatment threshold > 180). | Start levetiracetam. |
| M36753294-A59 | IV fluids (Dextrose 5%, NaCl 0.9%) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. Latest lactate 3.5 mmol/L at 2141-05-23 15:21:00 (reference 0.5 to 2.0) is high, consistent with 'high'. | Start levetiracetam. |
| M36753294-A59 | vasopressors (Phenylephrine) | 'blood pressure low' holds when any component is low. systolic BP: no; mean arterial pressure: yes. | Start levetiracetam. |

## 4. not_supported facts

| Case | AI sentence | Atomic fact | Kind | Evidence |
|---|---|---|---|---|
| M33348260-R01 | Assess for signs of infection given the low white blood cell count. | The white blood cell count is low. | stated outright | Latest WBC 14.2 K/uL at 2145-09-29 02:39:00 (reference 4.0 to 10.0) is high, not consistent with 'low'. |
| M33846653-R02 | Continue insulin therapy to manage hypoglycemia. | Hypoglycemia is present. | presupposed by an action | Latest glucose 234 mg/dL at 2137-06-20 12:53:00 (reference 70.0 to 100.0) is high, not consistent with 'low'. |
| M34107647-R03 | Monitor blood glucose levels closely given the low glucose readings. | Low glucose readings are present. | stated outright | Latest glucose 258 mg/dL at 2153-03-28 03:16:00 (reference 70.0 to 100.0) is high, not consistent with 'low'. |
| M34324099-R04 | Assess for potential causes of elevated hemoglobin and hematocrit levels. | Elevated hemoglobin levels are present. | presupposed by an action | Latest hemoglobin 10.2 g/dL at 2182-01-08 14:49:00 (reference 14.0 to 18.0) is low, not consistent with 'high'. |
| M34324099-R04 | Assess for potential causes of elevated hemoglobin and hematocrit levels. | Elevated hematocrit levels are present. | presupposed by an action | Latest hematocrit 28.5 % at 2182-01-08 14:49:00 (reference 40.0 to 52.0) is low, not consistent with 'high'. |
| M34578020-R05 | Assess and manage the patient's nutritional status given the elevated albumin and hemoglobin levels. | Albumin levels are elevated. | stated outright | Latest albumin 2.9 g/dL at 2187-02-11 03:55:00 (reference 3.5 to 5.2) is low, not consistent with 'high'. |
| M34578020-R05 | Assess and manage the patient's nutritional status given the elevated albumin and hemoglobin levels. | Hemoglobin levels are elevated. | stated outright | Latest hemoglobin 8 g/dL at 2187-02-11 20:00:00 (reference 13.7 to 17.5) is low, not consistent with 'high'. |
| M35026312-R06 | Monitor blood glucose levels closely due to hypoglycemia. | Hypoglycemia is present. | presupposed by an action | Latest glucose 383 mg/dL at 2150-03-12 03:03:00 (reference 70.0 to 100.0) is high, not consistent with 'low'. |
| M36107367-R07 | Monitor blood glucose levels closely due to low glucose levels. | Low glucose levels are present. | stated outright | Latest glucose 177 mg/dL at 2148-01-25 02:25:00 (reference 70.0 to 100.0) is high, not consistent with 'low'. |
| M37049133-R09 | Assess for signs of infection given elevated white blood cell count. | White blood cell count is elevated. | stated outright | Latest WBC 2.4 K/uL at 2196-04-15 03:36:00 (reference 4.0 to 11.0) is low, not consistent with 'high'. |
| M39492446-R10 | Monitor blood glucose levels closely due to hypoglycemia. | Hypoglycemia is present. | presupposed by an action | Latest glucose 208 mg/dL at 2181-10-13 12:00:00 (reference 70.0 to 100.0) is high, not consistent with 'low'. |
| M30101877-R11 | Administer insulin to manage hypoglycemia. | Hypoglycemia is present. | presupposed by an action | Latest glucose 216 mg/dL at 2143-03-23 02:19:00 (reference 70.0 to 100.0) is high, not consistent with 'low'. |
| M31959184-R12 | Evaluate the patient for potential respiratory issues given the low lactate dehydrogenase and respiratory alarms. | Lactate dehydrogenase is low. | stated outright | Latest lactate 2.3 mmol/L at 2110-11-30 16:43:00 (reference 0.5 to 2.0) is high, not consistent with 'low'. |
| M32128372-R13 | Administer IV calcium to manage hypercalcemia. | Hypercalcemia is present. | presupposed by an action | Latest calcium 1.07 mmol/L at 2137-02-26 22:38:00 (reference 1.12 to 1.32) is low, not consistent with 'high'. |
| M35128235-R14 | Evaluate the patient's renal function, given the elevated creatinine levels. | The patient has elevated creatinine levels. | stated outright | Latest creatinine 0.3 mg/dL at 2129-04-06 17:15:00 (reference 0.4 to 1.1) is low, not consistent with 'high'. |
| M37293400-R15 | Monitor blood glucose levels given hypoglycemia. | Hypoglycemia is present. | stated outright | Latest glucose 106 mg/dL at 2133-12-19 09:46:00 (reference 70.0 to 100.0) is high, not consistent with 'low'. |
| M38430513-R16 | Administer intravenous fluids to correct hypertension. | Hypertension is present. | presupposed by an action | 'blood pressure high' holds when any component is high. systolic BP: no; mean arterial pressure: no. |
| M38540883-R17 | Evaluate and manage renal function, considering the low creatinine levels. | Creatinine levels are low. | presupposed by an action | Latest creatinine 2 mg/dL at 2135-01-22 14:46:00 (reference 0.4 to 1.1) is high, not consistent with 'low'. |
| M39061571-R18 | Administer intravenous calcium to address hypercalcemia. | Hypercalcemia is present. | presupposed by an action | Latest calcium 1.03 mmol/L at 2185-01-18 18:24:00 (reference 1.12 to 1.32) is low, not consistent with 'high'. |
| M36107367-R19 | Assess for signs of infection given the low white blood cell count. | The white blood cell count is low. | presupposed by an action | Latest WBC 10.4 K/uL at 2148-01-25 02:25:00 (reference 4.0 to 10.0) is high, not consistent with 'low'. |
| M31959184-R20 | Monitor blood glucose levels given the low glucose reading. | The patient has a low glucose reading. | stated outright | Latest glucose 226 mg/dL at 2110-11-30 23:49:00 (reference 70.0 to 100.0) is high, not consistent with 'low'. |
| M31959184-R21 | Monitor for signs of hypovolemia given the elevated hematocrit and hemoglobin levels. | Hematocrit levels are elevated. | stated outright | Latest hematocrit 29.5 % at 2110-11-30 23:49:00 (reference 36.0 to 48.0) is low, not consistent with 'high'. |
| M31959184-R21 | Monitor for signs of hypovolemia given the elevated hematocrit and hemoglobin levels. | Hemoglobin levels are elevated. | stated outright | Latest hemoglobin 10.4 g/dL at 2110-11-30 23:49:00 (reference 12.0 to 16.0) is low, not consistent with 'high'. |
| M37049133-R22 | Assess for signs of infection given elevated white blood cell count. | White blood cell count is elevated. | stated outright | Latest WBC 2.4 K/uL at 2196-04-15 03:36:00 (reference 4.0 to 11.0) is low, not consistent with 'high'. |
| M32155744-D12 | Continue heparin. | The patient is currently receiving heparin. | presupposed by an action | The heparin order was explicitly marked as stopped on 2111-01-16, which is before the decision time. |

## 5. Judge panel

29 items went to the judge panel. Agreement: {'3/3': 7, '2/3': 22} (split = no majority; the conservative label was used and the item needs human review).

## 6. Per-case score sheets

| Case | Facts | supported | not_supported | not_addressed | unverifiable | Treatment agreement | Vital recall | All recall |
|---|---|---|---|---|---|---|---|---|
| M33348260-R01 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | 0.0% |
| M33846653-R02 | 2 | 50.0% | 50.0% | 0.0% | 0.0% | 100.0% | 50.0% | 16.7% |
| M34107647-R03 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | 0.0% | 0.0% |
| M34324099-R04 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | - |
| M34578020-R05 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | - | 0.0% | 0.0% |
| M35026312-R06 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | 0.0% | 0.0% |
| M36107367-R07 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | 0.0% | 0.0% |
| M36893762-R08 | 0 | - | - | - | - | - | - | - |
| M37049133-R09 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | 0.0% | 0.0% |
| M39492446-R10 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | - | 0.0% |
| M30101877-R11 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 100.0% | 50.0% | 33.3% |
| M31959184-R12 | 2 | 0.0% | 50.0% | 0.0% | 50.0% | - | 0.0% | 0.0% |
| M32128372-R13 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 100.0% | 12.5% | 8.3% |
| M35128235-R14 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | 0.0% | 0.0% |
| M37293400-R15 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | 0.0% | 0.0% |
| M38430513-R16 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 100.0% | 14.3% | 12.5% |
| M38540883-R17 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | 0.0% | 0.0% |
| M39061571-R18 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 100.0% | 16.7% | 11.1% |
| M36107367-R19 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | 0.0% | 0.0% |
| M31959184-R20 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | 0.0% | 0.0% |
| M31959184-R21 | 2 | 0.0% | 100.0% | 0.0% | 0.0% | - | 0.0% | 0.0% |
| M37049133-R22 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | - | 0.0% | 0.0% |
| M30057454-D01 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M30458995-D02 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M30585761-D03 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M30665396-D04 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M30757476-D05 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M31269608-D06 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M31338022-D07 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M31494479-D08 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M31959184-D09 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32119961-D10 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M32128372-D11 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32155744-D12 | 1 | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M32283063-D13 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32359580-D14 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32391858-D15 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M32506122-D16 | 2 | 50.0% | 0.0% | 50.0% | 0.0% | 50.0% | - | 25.0% |
| M32587226-D17 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32604416-D18 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33177122-D19 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33383124-D20 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33558396-D21 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33846653-D22 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33987268-D23 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M34100191-D24 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M34107647-D25 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M34170353-D26 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M34499716-D27 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M34531557-D28 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M34578020-D29 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M35009126-D30 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M35026312-D31 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M35128235-D32 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M35258379-D33 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M35436337-D34 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M35514836-D35 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M35636875-D36 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M36059427-D37 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M36091287-D38 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M36107367-D39 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M36427705-D40 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M36496303-D41 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | 0.0% |
| M36558922-D42 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M36753294-D43 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M37267577-D44 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M37293400-D45 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M38197705-D46 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M38430513-D47 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M38540883-D48 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M39061571-D49 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M39142259-D50 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M39268883-D51 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M39635619-D52 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M39711498-D53 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M39880770-D54 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M30101877-D55 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M30849778-D56 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M30913302-D57 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 50.0% | - | 14.3% |
| M30932571-D58 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M31205490-D59 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | - | 0.0% |
| M32166508-D60 | 1 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M32119961-S01 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32128372-S02 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32155744-S03 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32391858-S04 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32506122-S05 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M33846653-S06 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| M34100191-S07 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M34170353-S08 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M34499716-S09 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M34531557-S10 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M34578020-S11 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M35009126-S12 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M35026312-S13 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M35128235-S14 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M35436337-S15 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M35514836-S16 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M36059427-S17 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M36496303-S18 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M37267577-S19 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M37293400-S20 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M38197705-S21 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M38430513-S22 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M39142259-S23 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M39268883-S24 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M39635619-S25 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M39711498-S26 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M39880770-S27 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M30458995-S28 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M30665396-S29 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M30757476-S30 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M30849778-S31 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M30913302-S32 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M30932571-S33 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M31205490-S34 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M31269608-S35 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M31338022-S36 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32166508-S37 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32359580-S38 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32587226-S39 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33177122-S40 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33281088-S41 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33383124-S42 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33558396-S43 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33683112-S44 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33987268-S45 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M34629895-S46 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M35636875-S47 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M36107367-S48 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M37049133-S49 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M37057036-S50 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M37127068-S51 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M37507305-S52 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M37509585-S53 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M38907302-S54 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M39061571-S55 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M39084876-S56 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M30913302-S57 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M30932571-S58 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32128372-S59 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32155744-S60 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M30057454-A01 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M30101877-A02 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M30458995-A03 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M30585761-A04 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M30665396-A05 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M30757476-A06 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M30849778-A07 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M30913302-A08 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M30932571-A09 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M31205490-A10 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M31269608-A11 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M31338022-A12 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M31494479-A13 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M31921355-A14 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M31959184-A15 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32119961-A16 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32128372-A17 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32155744-A18 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32166508-A19 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32283063-A20 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32359580-A21 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32374504-A22 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M32391858-A23 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32506122-A24 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M32587226-A25 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M32604416-A26 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33177122-A27 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33281088-A28 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33348260-A29 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M33383124-A30 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33558396-A31 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33683112-A32 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33846653-A33 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M33987268-A34 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M34100191-A35 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M34107647-A36 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M34170353-A37 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M34324099-A38 | 0 | - | - | - | - | 0.0% | - | - |
| M34499716-A39 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M34531557-A40 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M34578020-A41 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M34629895-A42 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M35009126-A43 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M35026312-A44 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M35128235-A45 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M35258379-A46 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M35436337-A47 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M35446858-A48 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M35514836-A49 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M35544374-A50 | 0 | - | - | - | - | 0.0% | - | - |
| M35636875-A51 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M35679826-A52 | 0 | - | - | - | - | 0.0% | - | - |
| M36059427-A53 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M36091287-A54 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M36107367-A55 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M36427705-A56 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M36496303-A57 | 0 | - | - | - | - | 0.0% | - | 0.0% |
| M36558922-A58 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M36753294-A59 | 0 | - | - | - | - | 0.0% | 0.0% | 0.0% |
| M36893762-A60 | 0 | - | - | - | - | 0.0% | - | - |
