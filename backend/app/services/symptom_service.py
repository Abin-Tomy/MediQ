"""
Symptom Analysis Service.

Provides clinical symptom evaluation and preliminary decision support.
Wires the fine-tuned DistilBERT symptom classifier from app.ai.model_manager,
with safety-oriented emergency screening and safe fallback to deterministic rules
when trained model weights are not deployed.
"""

import re
from typing import Optional, Tuple

from app.ai import model_manager
from app.models.analysis import (
    ConditionPrediction,
    SymptomAnalysisResponse,
    SymptomInput,
)

# Malayalam Unicode block regex range: U+0D00 to U+0D7F
_MALAYALAM_CHAR_PATTERN = re.compile(r"[\u0d00-\u0d7f]")


def _contains_malayalam(text: str) -> bool:
    """Detect whether input text contains Malayalam characters."""
    return bool(_MALAYALAM_CHAR_PATTERN.search(text))


def _has_all_keywords(text: str, *keywords: str) -> bool:
    """Check if all keywords/phrases are present in the text."""
    return all(kw in text for kw in keywords)


def _has_any_keyword(text: str, *keywords: str) -> bool:
    """Check if at least one of the keywords/phrases is present in the text."""
    return any(kw in text for kw in keywords)


# Clinical triage mapping for predicted conditions (urgency_hint, specialist_hint)
_CONDITION_TRIAGE_MAP = {
    "nipah": ("emergency", "Infectious Disease Specialist / Neurologist"),
    "heart attack": ("emergency", "Cardiologist / Emergency Medicine"),
    "paralysis (brain hemorrhage)": ("emergency", "Neurologist / Emergency Medicine"),
    "pneumonia": ("high", "Pulmonologist / General Physician"),
    "leptospirosis": ("high", "Infectious Disease Specialist / Nephrologist"),
    "tuberculosis": ("high", "Pulmonologist / Infectious Disease"),
    "hepatitis": ("moderate", "Gastroenterologist / Hepatologist"),
    "jaundice": ("moderate", "Gastroenterologist"),
    "chikungunya": ("moderate", "General Physician / Rheumatologist"),
    "dengue": ("moderate", "General Physician / Infectious Disease Specialist"),
    "malaria": ("moderate", "General Physician / Infectious Disease"),
    "typhoid": ("moderate", "General Physician"),
    "bronchial asthma": ("moderate", "Pulmonologist / Allergist"),
    "diabetes": ("moderate", "Endocrinologist"),
    "hypoglycemia": ("high", "Endocrinologist / Emergency Medicine"),
    "hypertension": ("moderate", "Cardiologist / General Physician"),
    "migraine": ("moderate", "Neurologist"),
    "cervical spondylosis": ("low", "Orthopedist / Physiotherapist"),
    "arthritis": ("moderate", "Rheumatologist / Orthopedist"),
    "osteoarthristis": ("moderate", "Orthopedist / Rheumatologist"),
    "common cold": ("low", "General Physician / ENT Specialist"),
    "allergy": ("low", "Allergist / General Physician"),
    "gerd": ("low", "Gastroenterologist"),
    "gastroenteritis": ("moderate", "Gastroenterologist / General Physician"),
    "peptic ulcer diseae": ("moderate", "Gastroenterologist"),
    "urinary tract infection": ("moderate", "Urologist / General Physician"),
    "psoriasis": ("low", "Dermatologist"),
    "impetigo": ("low", "Dermatologist"),
    "acne": ("low", "Dermatologist"),
    "fungal infection": ("low", "Dermatologist"),
    "drug reaction": ("moderate", "Allergist / Dermatologist"),
    "varicose veins": ("low", "Vascular Surgeon / General Physician"),
}


def _get_triage_hints(condition_name: str) -> Tuple[str, str]:
    """Derive recommended clinical specialty and triage urgency from predicted condition."""
    cond_lower = condition_name.lower()
    for key, (urgency, specialist) in _CONDITION_TRIAGE_MAP.items():
        if key in cond_lower:
            return urgency, specialist
    return "moderate", "General Physician"


async def analyze_symptoms(symptom_input: SymptomInput) -> SymptomAnalysisResponse:
    """
    Evaluate symptoms and return ranked potential conditions with confidence scores.

    Workflow:
    1. Language check: detect Malayalam and return clear unsupported notice.
    2. Emergency condition screening: life-safety triage layer (chest pain, respiratory distress).
    3. DistilBERT inference: if trained model is available, use real model predictions.
    4. Deterministic rule-based placeholder: fallback if model weights are not deployed.
    """
    raw_text = symptom_input.symptoms.strip()
    norm_text = raw_text.lower()
    lang = symptom_input.language or "en"

    # ─────────────────────────────────────────────────────────────────────────
    # Step 1: Language Architecture Check (Malayalam Support Preparation)
    # ─────────────────────────────────────────────────────────────────────────
    if lang == "ml" or _contains_malayalam(raw_text):
        return SymptomAnalysisResponse(
            input=symptom_input,
            analysis_type="symptom_analysis",
            possible_conditions=[],
            urgency_hint="moderate",
            specialist_hint="General Physician",
            disclaimer="This is not a medical diagnosis. Consult a qualified medical professional.",
            notes=(
                "Malayalam language input detected. Automated translation and bilingual "
                "inference are scheduled for integration in a future batch. The English DistilBERT "
                "model currently accepts English symptoms."
            ),
            model_version=None,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Step 2: Emergency & High-Risk Symptom Screening (Life-Safety Layer)
    # ─────────────────────────────────────────────────────────────────────────
    has_chest_pain = _has_any_keyword(
        norm_text, "chest pain", "chest pressure", "chest tightness", "pain in chest"
    )
    has_breathing_difficulty = _has_any_keyword(
        norm_text,
        "difficulty breathing",
        "shortness of breath",
        "breathless",
        "trouble breathing",
        "hard to breathe",
    )

    if has_chest_pain or has_breathing_difficulty:
        return SymptomAnalysisResponse(
            input=symptom_input,
            analysis_type="symptom_analysis",
            possible_conditions=[
                ConditionPrediction(
                    condition="Possible Acute Cardiopulmonary Condition",
                    confidence=0.85,
                ),
                ConditionPrediction(
                    condition="Acute Respiratory Distress",
                    confidence=0.75,
                ),
            ],
            urgency_hint="emergency",
            specialist_hint="Emergency Medicine / Cardiologist",
            disclaimer="This is not a medical diagnosis. Consult a qualified medical professional.",
            notes=(
                "EMERGENCY CLINICAL SAFETY ALERT: Severe chest discomfort or difficulty breathing "
                "was flagged by safety screening. This is a life-safety triage rule, not an AI model "
                "diagnosis. Seek immediate emergency medical care or contact emergency services."
            ),
            model_version=None,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Step 3: Real DistilBERT Symptom Model Inference
    # ─────────────────────────────────────────────────────────────────────────
    symptom_model = model_manager.get_symptom_model()
    if symptom_model.is_available():
        result = symptom_model.infer(symptoms=raw_text, language=lang, top_k=5)
        if result.available and result.predictions:
            predictions = [
                ConditionPrediction(
                    condition=p.condition,
                    confidence=p.confidence,
                )
                for p in result.predictions
            ]
            top_cond = predictions[0].condition if predictions else ""
            urgency, specialist = _get_triage_hints(top_cond)

            return SymptomAnalysisResponse(
                input=symptom_input,
                analysis_type="symptom_analysis",
                possible_conditions=predictions,
                urgency_hint=urgency,
                specialist_hint=specialist,
                disclaimer="This is not a medical diagnosis. Consult a qualified medical professional.",
                notes=result.notes or "DistilBERT symptom inference completed.",
                model_version=result.model_version,
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Step 4: Deterministic Rule-Based Fallback (When Model Weights Missing)
    # ─────────────────────────────────────────────────────────────────────────
    has_fever = _has_any_keyword(norm_text, "fever", "high temperature", "febrile", "pyrexia")
    has_rash = _has_any_keyword(norm_text, "rash", "skin eruption", "petechiae", "red spots")
    has_joint_pain = _has_any_keyword(
        norm_text, "joint pain", "joint ache", "arthralgia", "pain in joints", "stiff joints"
    )
    has_flood_water = _has_any_keyword(
        norm_text,
        "flood",
        "floodwater",
        "flood water",
        "stagnant water",
        "contaminated water",
        "drainage water",
        "sewage",
    )
    has_headache = _has_any_keyword(norm_text, "headache", "head ache", "head pain")
    has_body_pain = _has_any_keyword(
        norm_text, "body pain", "body ache", "muscle pain", "myalgia", "generalized pain"
    )
    has_cough = _has_any_keyword(norm_text, "cough", "coughing")
    has_sore_throat = _has_any_keyword(norm_text, "sore throat", "throat pain", "scratchy throat")
    has_runny_nose = _has_any_keyword(
        norm_text, "runny nose", "running nose", "rhinorrhea", "nasal discharge", "sneezing", "cold"
    )
    has_eye_redness = _has_any_keyword(
        norm_text, "eye redness", "red eye", "red eyes", "pink eye", "bloodshot"
    )
    has_eye_pain = _has_any_keyword(
        norm_text, "eye pain", "pain in eye", "pain in eyes", "burning eyes", "eye irritation"
    )
    has_itching = _has_any_keyword(norm_text, "itching", "itchy", "pruritus", "hives", "welts")

    fallback_note = (
        "Note: DistilBERT symptom model is currently unavailable (weights pending Colab training). "
        "Evaluated via clinical rule-based triage placeholder."
    )

    # Rule 3: Fever + floodwater/water exposure (Leptospirosis)
    if has_fever and has_flood_water:
        return SymptomAnalysisResponse(
            input=symptom_input,
            analysis_type="symptom_analysis",
            possible_conditions=[
                ConditionPrediction(condition="Leptospirosis", confidence=0.80),
                ConditionPrediction(condition="Water-borne Bacterial Infection", confidence=0.65),
            ],
            urgency_hint="high",
            specialist_hint="General Physician / Infectious Disease Specialist",
            disclaimer="This is not a medical diagnosis. Consult a qualified medical professional.",
            notes=f"{fallback_note} Exposure to floodwater combined with fever raises suspicion for leptospirosis.",
            model_version=None,
        )

    # Combined check: Fever + joint pain + rash (Classic Arboviral cluster)
    if has_fever and has_joint_pain and has_rash:
        return SymptomAnalysisResponse(
            input=symptom_input,
            analysis_type="symptom_analysis",
            possible_conditions=[
                ConditionPrediction(condition="Dengue", confidence=0.72),
                ConditionPrediction(condition="Chikungunya", confidence=0.70),
            ],
            urgency_hint="moderate",
            specialist_hint="General Physician",
            disclaimer="This is not a medical diagnosis. Consult a qualified medical professional.",
            notes=f"{fallback_note} Symptoms align with mosquito-borne arboviral illnesses.",
            model_version=None,
        )

    # Rule 1: Fever + rash (without joint pain explicit)
    if has_fever and has_rash:
        return SymptomAnalysisResponse(
            input=symptom_input,
            analysis_type="symptom_analysis",
            possible_conditions=[
                ConditionPrediction(condition="Dengue", confidence=0.70),
                ConditionPrediction(condition="Chikungunya", confidence=0.65),
            ],
            urgency_hint="moderate",
            specialist_hint="General Physician",
            disclaimer="This is not a medical diagnosis. Consult a qualified medical professional.",
            notes=f"{fallback_note} Fever accompanied by rash warrants monitoring of vitals.",
            model_version=None,
        )

    # Rule 2: Fever + joint pain (without rash explicit)
    if has_fever and has_joint_pain:
        return SymptomAnalysisResponse(
            input=symptom_input,
            analysis_type="symptom_analysis",
            possible_conditions=[
                ConditionPrediction(condition="Chikungunya", confidence=0.72),
                ConditionPrediction(condition="Dengue", confidence=0.68),
            ],
            urgency_hint="moderate",
            specialist_hint="General Physician / Rheumatologist",
            disclaimer="This is not a medical diagnosis. Consult a qualified medical professional.",
            notes=f"{fallback_note} Joint pain with fever is characteristic of viral arthralgia.",
            model_version=None,
        )

    # Rule 4: Fever + headache + body pain
    if has_fever and (has_headache or has_body_pain):
        return SymptomAnalysisResponse(
            input=symptom_input,
            analysis_type="symptom_analysis",
            possible_conditions=[
                ConditionPrediction(condition="Dengue", confidence=0.65),
                ConditionPrediction(condition="Viral Fever", confidence=0.60),
            ],
            urgency_hint="moderate",
            specialist_hint="General Physician",
            disclaimer="This is not a medical diagnosis. Consult a qualified medical professional.",
            notes=f"{fallback_note} Common acute febrile presentation. Monitor temperature.",
            model_version=None,
        )

    # Rule 5: Cough + sore throat + runny nose
    if (has_cough and has_sore_throat) or (has_cough and has_runny_nose) or (has_sore_throat and has_runny_nose):
        return SymptomAnalysisResponse(
            input=symptom_input,
            analysis_type="symptom_analysis",
            possible_conditions=[
                ConditionPrediction(condition="Common Cold", confidence=0.75),
                ConditionPrediction(condition="Upper Respiratory Tract Infection", confidence=0.65),
            ],
            urgency_hint="low",
            specialist_hint="General Physician / ENT Specialist",
            disclaimer="This is not a medical diagnosis. Consult a qualified medical professional.",
            notes=f"{fallback_note} Symptoms suggest typical upper respiratory viral infection.",
            model_version=None,
        )

    # Rule 6: Eye redness + eye pain / irritation
    if has_eye_redness or (has_eye_pain and _has_any_keyword(norm_text, "eye", "eyes")):
        return SymptomAnalysisResponse(
            input=symptom_input,
            analysis_type="symptom_analysis",
            possible_conditions=[
                ConditionPrediction(condition="Conjunctivitis", confidence=0.75),
                ConditionPrediction(condition="Ophthalmic Irritation", confidence=0.60),
            ],
            urgency_hint="moderate",
            specialist_hint="Ophthalmologist",
            disclaimer="This is not a medical diagnosis. Consult a qualified medical professional.",
            notes=f"{fallback_note} Ophthalmic irritation. Seek eye evaluation if pain persists.",
            model_version=None,
        )

    # Rule 7: Skin rash/itching without systemic symptoms
    if (has_rash or has_itching) and not has_fever:
        return SymptomAnalysisResponse(
            input=symptom_input,
            analysis_type="symptom_analysis",
            possible_conditions=[
                ConditionPrediction(condition="Allergic Dermatitis", confidence=0.70),
                ConditionPrediction(condition="Contact Dermatitis", confidence=0.65),
            ],
            urgency_hint="low",
            specialist_hint="Dermatologist",
            disclaimer="This is not a medical diagnosis. Consult a qualified medical professional.",
            notes=f"{fallback_note} Localized cutaneous reaction without systemic fever signs.",
            model_version=None,
        )

    # Step 5: Safe Fallback (No known pattern matches)
    return SymptomAnalysisResponse(
        input=symptom_input,
        analysis_type="symptom_analysis",
        possible_conditions=[
            ConditionPrediction(
                condition="Insufficient information to determine potential conditions",
                confidence=0.0,
            )
        ],
        urgency_hint="low",
        specialist_hint="General Physician",
        disclaimer="This is not a medical diagnosis. Consult a qualified medical professional.",
        notes=(
            f"{fallback_note} The symptoms provided do not match recognized common symptom clusters. "
            "Please provide a more detailed description or consult a healthcare professional."
        ),
        model_version=None,
    )
