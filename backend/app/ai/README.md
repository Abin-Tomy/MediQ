# MediQ Multimodal AI Diagnostic Fusion Layer

> **Clinical Decision Support Disclaimer**  
> MediQ provides informational clinical decision support and does not replace a qualified healthcare professional or provide definitive medical diagnosis. Consult a qualified medical practitioner for clinical diagnosis and treatment.

---

## Architecture Overview

The MediQ Multimodal AI Fusion Layer provides centralized, explainable evidence synthesis across four specialized AI models:

| Modality | Model Architecture | Training Domain / Dataset | Primary Clinical Task |
| :--- | :--- | :--- | :--- |
| **1. Symptoms** | Fine-tuned DistilBERT | DDXPlus (49 pathologies) | Symptom narrative classification & condition probability ranking |
| **2. Skin Image** | YOLOv8 Nano | HAM10000 (7 diagnostic classes) | Dermoscopy skin lesion detection & bounding-box localization |
| **3. Eye Image** | YOLOv8 Nano | SLID anterior-eye (14 verified classes) | Slit-lamp anterior-eye pathology detection & localization |
| **4. Medical Report** | Fine-tuned T5-small | PubMed Scientific Papers | Clinical lab/pathology report text summarization |

---

## 15 Modality Combinations

The Fusion engine dynamically inspects incoming payloads and supports every valid non-empty subset of the four modalities ($2^4 - 1 = 15$ combinations):

| # | Active Modalities | Description |
| :---: | :--- | :--- |
| **1** | `symptoms` | Single-modality symptom narrative triage |
| **2** | `skin` | Single-modality skin lesion detection |
| **3** | `eye` | Single-modality anterior-eye slit-lamp detection |
| **4** | `report` | Informational clinical report summarization |
| **5** | `symptoms + skin` | Corroborates dermatological symptoms with dermoscopy imaging |
| **6** | `symptoms + eye` | Corroborates ophthalmic complaints with slit-lamp photograph |
| **7** | `symptoms + report` | Synthesizes patient complaints with laboratory/pathology findings |
| **8** | `skin + eye` | Multi-domain dual-photograph evaluation |
| **9** | `skin + report` | Evaluates skin lesion alongside biopsy/histology report text |
| **10** | `eye + report` | Evaluates ocular photo alongside tonometry/slit-lamp report text |
| **11** | `symptoms + skin + eye` | Tri-modal clinical synthesis across narrative and dual-organ images |
| **12** | `symptoms + skin + report` | Comprehensive dermatological triage with lab context |
| **13** | `symptoms + eye + report` | Comprehensive ophthalmic triage with diagnostic report |
| **14** | `skin + eye + report` | Dual-organ visual inspection contextualized by medical report |
| **15** | `symptoms + skin + eye + report` | Complete quadri-modal clinical evidence synthesis |

---

## Core Operational Principles

### 1. Model Execution Rule
- An AI model **MUST run only when its corresponding input exists**.
  - No symptoms $\to$ DistilBERT does not run.
  - No skin image $\to$ Skin YOLOv8 does not run.
  - No eye image $\to$ Eye YOLOv8 does not run.
  - No report text $\to$ T5 does not run.
- Missing inputs are **never replaced** with synthetic text, dummy predictions, or random scores.

### 2. Model Availability & Safe Fallback
- Models check their weights before execution. When weights have not yet been deployed:
  - The modality is explicitly marked `available: false, ran: false`.
  - Predictions are **never fabricated** or populated with fake placeholders.
  - If other requested modalities have loaded models, fusion proceeds with the available inputs.
  - If all requested models are unavailable, a safe status (`fused_result: null`, `urgency: "routine"`, `urgency_score: 0.0`) is returned with a transparent explanation.

### 3. Report Summarization Safety Limitation
- T5 is an **abstractive text summarization model**, NOT a diagnostic classifier.
- Report summaries provide clinical context and are stored under `individual_results["report"]["summary"]`.
- Report summaries are **never converted into an artificial diagnosis**.
- When `report` is the sole modality, the result is classified as `finding_type: "informational"`.

### 4. Cross-Modal Agreement vs. Discrepancy
- **Cross-Modal Corroboration**: When independent modalities identify the same or closely-related pathology (e.g. skin itching/melanoma symptoms + dermoscopy melanoma detection), the finding is corroborated:
  $$\text{Confidence}_{\text{fused}} = \min\left(0.95, \max(c_1, c_2) + 0.15 \cdot \min(c_1, c_2)\right)$$
- **Multi-Domain Distinct Findings**: When independent modalities detect different organs (e.g. respiratory pneumonia symptoms + incidental benign melanocytic nevus), both findings are preserved in `all_fused_conditions`. Artificial consensus is never manufactured.
- **Same-Domain Discrepancies**: When modalities present conflicting indicators within the same domain, confidence is moderated and triage urgency is elevated conservatively to protect patient safety.

---

## Deterministic Triage & Specialist Mapping

### Urgency Levels & Scores
| Urgency Level | Score | Representative Triggers |
| :--- | :---: | :--- |
| **`emergency`** | `1.0` | Acute cardiopulmonary distress, heart attack, stroke, Nipah virus infection |
| **`high`** | `0.75` | Melanoma, Basal Cell Carcinoma, Keratitis, Pneumonia, Tuberculosis, Leptospirosis |
| **`moderate`** | `0.50` | Arboviral fevers (Dengue, Chikungunya), Cataract, Conjunctivitis, Conflicting findings |
| **`low`** | `0.25` | Common cold, Acne, Benign Nevus, Pterygium, Pure report summarization |

*Conservative rule: Overall urgency escalates to $\max(\text{urgency levels})$.*

### Specialist Recommendation
- **Dermatology**: `Dermatologist` (or `Dermatologist / Oncologist` for suspected melanoma/carcinoma)
- **Ophthalmology**: `Ophthalmologist`
- **Pulmonology**: `Pulmonologist / General Physician`
- **Cardiology / Emergency**: `Cardiologist / Emergency Medicine`
- **Infectious Disease**: `General Physician / Infectious Disease Specialist`
- **Gastroenterology**: `Gastroenterologist`
- **Neurology**: `Neurologist`
- **Default / Unmapped**: `General Physician`

---

## Canonical API Endpoint

### `POST /analyse/fuse`
Requires JWT Bearer authentication (`patient`, `doctor`, or `admin` role).

#### Headers
```http
POST /analyse/fuse HTTP/1.1
Host: localhost:8000
Authorization: Bearer <JWT_ACCESS_TOKEN>
Content-Type: application/json
```

---

## Postman Testing Guide & Example Payloads

### 1. Symptoms Only
```json
{
  "symptoms": "Patient has had a persistent dry cough, high fever of 102F, and progressive shortness of breath for 4 days.",
  "language": "en"
}
```

### 2. Skin Image Only
```json
{
  "skin_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
}
```
*Note: Generic `image` with `image_type: "skin"` is also supported.*

### 3. Eye Image Only
```json
{
  "eye_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
}
```
*Note: Generic `image` with `image_type: "eye"` is also supported.*

### 4. Medical Report Only
```json
{
  "report_text": "CLINICAL PATHOLOGY REPORT\nSpecimen: Full thickness punch biopsy left forearm.\nMicroscopic Description: Section reveals atypical melanocytic proliferation extending along dermal-epidermal junction.\nDiagnosis: Features suspicious for malignant melanoma in situ."
}
```

### 5. Symptoms + Skin Image
```json
{
  "symptoms": "Patient reports an asymmetrical, dark mole on the upper back that has changed color and developed irregular borders.",
  "skin_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
}
```

### 6. Symptoms + Medical Report
```json
{
  "symptoms": "Fever, productive cough with rust-colored sputum, and right-sided pleuritic chest pain.",
  "report_text": "CHEST RADIOGRAPH REPORT\nFindings: Prominent airspace opacification identified in the right lower lobe with silhouette sign along the right hemidiaphragm. No pneumothorax. Heart size normal.\nImpression: Right lower lobe consolidation consistent with acute bacterial pneumonia."
}
```

### 7. All Four Modalities (Comprehensive Quadri-modal)
```json
{
  "symptoms": "Patient reports fever, erythematous petechial rash over upper chest, and bilateral conjunctival redness.",
  "skin_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "eye_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "report_text": "COMPLETE BLOOD COUNT & METABOLIC PANEL\nPlatelets: 95,000 /uL (Low)\nWBC: 3.2 x10^3/uL (Leukopenia)\nHematocrit: 48% (Elevated hemoconcentration)\nAST: 88 U/L, ALT: 72 U/L\nClinical impression: Acute febrile illness with thrombocytopenia."
}
```

---

## Response Structure Example

```json
{
  "modalities_received": ["symptoms", "skin"],
  "modalities_run": ["symptoms", "skin"],
  "modalities_unavailable": [],
  "individual_results": {
    "symptoms": {
      "modality": "symptoms",
      "available": true,
      "ran": true,
      "predictions": [
        { "condition": "Melanoma", "confidence": 0.75 }
      ],
      "detections": [],
      "summary": null,
      "notes": "DistilBERT inference completed."
    },
    "skin": {
      "modality": "skin",
      "available": true,
      "ran": true,
      "predictions": [],
      "detections": [
        {
          "condition": "mel",
          "confidence": 0.80,
          "bounding_box": { "x1": 15.0, "y1": 20.0, "x2": 150.0, "y2": 160.0 }
        }
      ],
      "summary": null,
      "notes": "YOLOv8 skin inference completed."
    }
  },
  "fused_result": {
    "condition": "Melanoma",
    "confidence": 0.9125,
    "supporting_modalities": ["symptoms", "skin"],
    "finding_type": "primary",
    "notes": "Cross-modal agreement: Corroborated independently by symptoms, skin. Agreement bonus applied."
  },
  "all_fused_conditions": [
    {
      "condition": "Melanoma",
      "confidence": 0.9125,
      "supporting_modalities": ["symptoms", "skin"],
      "finding_type": "primary",
      "notes": "Cross-modal agreement: Corroborated independently by symptoms, skin. Agreement bonus applied."
    }
  ],
  "urgency": "high",
  "urgency_score": 0.75,
  "recommended_specialist": "Dermatologist / Oncologist",
  "explanation": "Corroborating evidence across symptoms, skin independently identifies 'Melanoma' (cross-modal confidence: 0.91).",
  "disclaimer": "MediQ provides informational decision support and does not replace a qualified healthcare professional or provide definitive diagnosis. Consult a qualified medical practitioner for formal diagnosis and treatment.",
  "notes": "Multimodal AI Fusion evaluation completed successfully."
}
```
