"""
Multimodal AI Diagnostic Fusion Service.

Implements deterministic multimodal evidence synthesis across:
1. Symptoms / text (DistilBERT symptom classifier)
2. Skin image (YOLOv8 Nano skin lesion detector - HAM10000)
3. Eye image (YOLOv8 Nano anterior-eye pathology detector - SLID)
4. Medical report (T5-small abstractive report summariser)

Supports all 15 non-empty modality combinations.
Strictly adheres to clinical safety:
- Model execution rule: A model runs ONLY when its corresponding input exists.
- Safe unavailable behavior: Missing weights are never fabricated; modalities marked unavailable.
- Report safety: T5 summarization evidence is treated as informational context, never as a diagnosis.
- Explainable fusion: Cross-modal agreement is rewarded; disagreements and multi-domain findings
  are preserved rather than hidden.
- Deterministic triage urgency and specialist recommendations.
"""

import base64
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import HTTPException, status

from app.ai import model_manager
from app.models.analysis import (
    ConditionPrediction,
    DetectionItem,
    BoundingBoxModel,
    FusedCondition,
    FusionInput,
    FusionResponse,
    ModalityOutput,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Clinical Dictionaries & Triage Mappings
# ─────────────────────────────────────────────────────────────────────────────

# Priority hierarchy for urgency triage (conservative escalation)
URGENCY_PRIORITY = {
    "emergency": 4,
    "high": 3,
    "moderate": 2,
    "low": 1,
}

URGENCY_SCORES = {
    "emergency": 1.0,
    "high": 0.75,
    "moderate": 0.50,
    "low": 0.25,
}

# Clinical taxonomy aliases for cross-modal matching
# Maps condition aliases to canonical condition names and domains
CONDITION_CANONICAL_MAP = {
    # Skin conditions (HAM10000 & common terms)
    "mel": ("Melanoma", "skin", "high", "Dermatologist / Oncologist"),
    "melanoma": ("Melanoma", "skin", "high", "Dermatologist / Oncologist"),
    "bcc": ("Basal Cell Carcinoma", "skin", "high", "Dermatologist / Oncologist"),
    "basal cell carcinoma": ("Basal Cell Carcinoma", "skin", "high", "Dermatologist / Oncologist"),
    "akiec": ("Actinic Keratosis / Intraepithelial Carcinoma", "skin", "high", "Dermatologist"),
    "actinic keratosis": ("Actinic Keratosis / Intraepithelial Carcinoma", "skin", "high", "Dermatologist"),
    "bkl": ("Benign Keratosis-like Lesion", "skin", "low", "Dermatologist"),
    "benign keratosis": ("Benign Keratosis-like Lesion", "skin", "low", "Dermatologist"),
    "df": ("Dermatofibroma", "skin", "low", "Dermatologist"),
    "dermatofibroma": ("Dermatofibroma", "skin", "low", "Dermatologist"),
    "nv": ("Melanocytic Nevus", "skin", "low", "Dermatologist"),
    "melanocytic nevus": ("Melanocytic Nevus", "skin", "low", "Dermatologist"),
    "mole": ("Melanocytic Nevus", "skin", "low", "Dermatologist"),
    "vasc": ("Vascular Lesion", "skin", "low", "Dermatologist"),
    "vascular lesion": ("Vascular Lesion", "skin", "low", "Dermatologist"),
    "psoriasis": ("Psoriasis", "skin", "low", "Dermatologist"),
    "allergic dermatitis": ("Allergic Dermatitis", "skin", "low", "Dermatologist"),
    "contact dermatitis": ("Contact Dermatitis", "skin", "low", "Dermatologist"),
    "acne": ("Acne", "skin", "low", "Dermatologist"),
    "impetigo": ("Impetigo", "skin", "low", "Dermatologist"),
    "fungal infection": ("Fungal Infection", "skin", "low", "Dermatologist"),

    # Eye conditions (SLID & ophthalmic terms)
    "cataract": ("Cataract", "eye", "moderate", "Ophthalmologist"),
    "conjunctival injection": ("Conjunctival Injection", "eye", "moderate", "Ophthalmologist"),
    "conjunctivitis": ("Conjunctivitis", "eye", "moderate", "Ophthalmologist"),
    "pink eye": ("Conjunctivitis", "eye", "moderate", "Ophthalmologist"),
    "keratitis": ("Keratitis", "eye", "high", "Ophthalmologist"),
    "pterygium": ("Pterygium", "eye", "low", "Ophthalmologist"),
    "pinguecula": ("Pinguecula", "eye", "low", "Ophthalmologist"),
    "subconjunctival hemorrhage": ("Subconjunctival Hemorrhage", "eye", "moderate", "Ophthalmologist"),
    "corneal / conjunctival tumor": ("Corneal / Conjunctival Tumor", "eye", "high", "Ophthalmologist / Oncologist"),
    "corneal scarring": ("Corneal Scarring", "eye", "moderate", "Ophthalmologist"),
    "corneal dystrophy": ("Corneal Dystrophy", "eye", "moderate", "Ophthalmologist"),
    "conjunctival cyst": ("Conjunctival Cyst", "eye", "low", "Ophthalmologist"),
    "lens dislocation": ("Lens Dislocation", "eye", "high", "Ophthalmologist"),
    "intraocular lens": ("Intraocular Lens Condition", "eye", "low", "Ophthalmologist"),
    "pigmented nevus": ("Pigmented Nevus (Ocular)", "eye", "moderate", "Ophthalmologist"),

    # Systemic & Organ-specific conditions (DistilBERT / DDXPlus / Triage)
    "pneumonia": ("Pneumonia", "systemic", "high", "Pulmonologist / General Physician"),
    "tuberculosis": ("Tuberculosis", "systemic", "high", "Pulmonologist / Infectious Disease"),
    "bronchial asthma": ("Bronchial Asthma", "systemic", "moderate", "Pulmonologist / Allergist"),
    "asthma": ("Bronchial Asthma", "systemic", "moderate", "Pulmonologist / Allergist"),
    "common cold": ("Common Cold", "systemic", "low", "General Physician / ENT Specialist"),
    "upper respiratory tract infection": ("Upper Respiratory Tract Infection", "systemic", "low", "General Physician"),
    "dengue": ("Dengue", "systemic", "moderate", "General Physician / Infectious Disease Specialist"),
    "chikungunya": ("Chikungunya", "systemic", "moderate", "General Physician / Rheumatologist"),
    "malaria": ("Malaria", "systemic", "moderate", "General Physician / Infectious Disease Specialist"),
    "typhoid": ("Typhoid", "systemic", "moderate", "General Physician"),
    "leptospirosis": ("Leptospirosis", "systemic", "high", "Infectious Disease Specialist / Nephrologist"),
    "nipah": ("Nipah Virus Infection", "systemic", "emergency", "Infectious Disease Specialist / Neurologist"),
    "heart attack": ("Possible Acute Myocardial Infarction", "systemic", "emergency", "Cardiologist / Emergency Medicine"),
    "acute cardiopulmonary condition": ("Acute Cardiopulmonary Distress", "systemic", "emergency", "Cardiologist / Emergency Medicine"),
    "gerd": ("Gastroesophageal Reflux Disease", "systemic", "low", "Gastroenterologist"),
    "gastroenteritis": ("Gastroenteritis", "systemic", "moderate", "Gastroenterologist / General Physician"),
    "peptic ulcer": ("Peptic Ulcer Disease", "systemic", "moderate", "Gastroenterologist"),
    "hepatitis": ("Hepatitis", "systemic", "moderate", "Gastroenterologist / Hepatologist"),
    "jaundice": ("Jaundice", "systemic", "moderate", "Gastroenterologist"),
    "diabetes": ("Diabetes Mellitus", "systemic", "moderate", "Endocrinologist"),
    "hypoglycemia": ("Hypoglycemia", "systemic", "high", "Endocrinologist / Emergency Medicine"),
    "hypertension": ("Hypertension", "systemic", "moderate", "Cardiologist / General Physician"),
    "migraine": ("Migraine", "systemic", "moderate", "Neurologist"),
    "urinary tract infection": ("Urinary Tract Infection", "systemic", "moderate", "Urologist / General Physician"),
    "uti": ("Urinary Tract Infection", "systemic", "moderate", "Urologist / General Physician"),
    "arthritis": ("Arthritis", "systemic", "moderate", "Rheumatologist / Orthopedist"),
}

# Default safety disclaimer
MEDIQ_SAFETY_DISCLAIMER = (
    "MediQ provides informational decision support and does not replace a qualified "
    "healthcare professional or provide definitive diagnosis. Consult a qualified medical "
    "practitioner for formal diagnosis and treatment."
)


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def _decode_image_payload(payload: str, domain_label: str) -> bytes:
    """
    Safely decodes a base64 encoded image string or data URI into raw bytes.
    Raises HTTPException(400) if malformed or empty.
    """
    if not payload or not isinstance(payload, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {domain_label} image: payload must be a non-empty string.",
        )

    clean_payload = payload.strip()

    # Strip data URI header if present (e.g., "data:image/jpeg;base64,....")
    if clean_payload.startswith("data:"):
        parts = clean_payload.split(",", 1)
        if len(parts) == 2:
            clean_payload = parts[1].strip()

    try:
        image_bytes = base64.b64decode(clean_payload, validate=True)
        if len(image_bytes) == 0:
            raise ValueError("Decoded image is 0 bytes.")
        return image_bytes
    except Exception as exc:
        logger.warning("Failed to decode base64 for %s image: %s", domain_label, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed or invalid base64 image data for {domain_label} image.",
        )


def _canonicalize_condition(raw_name: str) -> Tuple[str, str, str, str]:
    """
    Derives (canonical_name, domain, urgency, specialist) from a condition string.
    Falls back to safe defaults if not explicitly mapped.
    Uses exact match first, then word-boundary matching to prevent false substring collisions
    (e.g., preventing 'mel' from erroneously matching 'melanocytic nevus').
    """
    norm = raw_name.strip().lower()

    # 1. Direct exact match
    if norm in CONDITION_CANONICAL_MAP:
        return CONDITION_CANONICAL_MAP[norm]

    # 2. Whole word boundary match
    for key, val in CONDITION_CANONICAL_MAP.items():
        if re.search(rf"\b{re.escape(key)}\b", norm):
            return val

    # Safe general primary-care fallback
    return raw_name.strip().title(), "general", "moderate", "General Physician"


def _conditions_match(cond1: str, cond2: str) -> bool:
    """
    Determines whether two condition names match or refer to the same underlying pathology.
    """
    c1, d1, _, _ = _canonicalize_condition(cond1)
    c2, d2, _, _ = _canonicalize_condition(cond2)

    if c1.lower() == c2.lower():
        return True

    # Check known semantic pairings across modalities
    pairings = [
        ({"melanoma"}, {"mel"}),
        ({"basal cell carcinoma"}, {"bcc"}),
        ({"actinic keratosis / intraepithelial carcinoma"}, {"akiec"}),
        ({"benign keratosis-like lesion"}, {"bkl"}),
        ({"melanocytic nevus"}, {"nv", "mole"}),
        ({"vascular lesion"}, {"vasc"}),
        ({"dermatofibroma"}, {"df"}),
        ({"conjunctivitis", "pink eye"}, {"conjunctival injection"}),
        ({"cataract"}, {"lens dislocation/cataract"}),
    ]

    c1_l = c1.lower()
    c2_l = c2.lower()
    for s1, s2 in pairings:
        if (c1_l in s1 and c2_l in s2) or (c1_l in s2 and c2_l in s1):
            return True

    return False


def _calculate_agreement_confidence(conf1: float, conf2: float) -> float:
    """
    Calculates combined confidence when two independent modalities corroborate a finding.
    Formula: min(0.95, round(max(c1, c2) + 0.15 * min(c1, c2), 4))
    """
    c_max = max(conf1, conf2)
    c_min = min(conf1, conf2)
    boosted = c_max + (0.15 * c_min)
    return min(0.95, round(boosted, 4))


def _calculate_disagreement_confidence(conf: float) -> float:
    """
    Conservatively adjusts confidence when cross-modal evidence conflicts.
    Reduces confidence by 20% to account for diagnostic uncertainty.
    """
    return max(0.1, round(conf * 0.80, 4))


# ─────────────────────────────────────────────────────────────────────────────
# Core Multimodal Fusion Pipeline
# ─────────────────────────────────────────────────────────────────────────────

async def fuse_modalities(request: FusionInput) -> FusionResponse:
    """
    Execute multimodal evidence synthesis across active modalities.

    Steps:
    1. Identify active modalities dynamically.
    2. Enforce model execution rule (models run ONLY if corresponding input exists).
    3. Query model_manager for available model services.
    4. Handle unavailable models cleanly without fabricating predictions.
    5. Synthesize findings (corroboration bonus, multi-domain preservation, disagreement handling).
    6. Incorporate T5 report summary as clinical evidence without diagnostic fabrication.
    7. Determine conservative clinical urgency and deterministic specialist recommendation.
    8. Synthesize explanation and attach clinical safety disclaimer.
    """
    # ── 1. Modality Identification ───────────────────────────────────────────
    modalities_received: List[str] = []
    if request.symptoms:
        modalities_received.append("symptoms")
    if request.skin_image:
        modalities_received.append("skin")
    if request.eye_image:
        modalities_received.append("eye")
    if request.report_text:
        modalities_received.append("report")

    if not modalities_received:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one input modality must be provided (symptoms, skin_image, eye_image, or report_text).",
        )

    modalities_run: List[str] = []
    modalities_unavailable: List[str] = []
    individual_results: Dict[str, Any] = {}

    # Diagnostic candidates collected from active models
    # Each entry: { "condition": str, "confidence": float, "modality": str, "metadata": dict }
    diagnostic_candidates: List[Dict[str, Any]] = []
    report_summary: Optional[str] = None

    # ── 2. Symptoms Modality Execution ───────────────────────────────────────
    if "symptoms" in modalities_received:
        symptom_model = model_manager.get_symptom_model()
        if symptom_model.is_available():
            try:
                sym_result = symptom_model.infer(
                    symptoms=request.symptoms,
                    language=request.language or "en",
                    top_k=5,
                )
                if sym_result.available:
                    preds = [
                        ConditionPrediction(condition=p.condition, confidence=p.confidence)
                        for p in sym_result.predictions
                    ]
                    individual_results["symptoms"] = ModalityOutput(
                        modality="symptoms",
                        available=True,
                        ran=True,
                        predictions=preds,
                        notes=sym_result.notes or "DistilBERT inference completed.",
                    ).model_dump()
                    modalities_run.append("symptoms")

                    for p in preds:
                        diagnostic_candidates.append({
                            "condition": p.condition,
                            "confidence": p.confidence,
                            "modality": "symptoms",
                            "metadata": {"model_version": sym_result.model_version},
                        })
                else:
                    individual_results["symptoms"] = ModalityOutput(
                        modality="symptoms",
                        available=False,
                        ran=False,
                        predictions=[],
                        notes=sym_result.notes or "DistilBERT model unavailable.",
                    ).model_dump()
                    modalities_unavailable.append("symptoms")
            except Exception as exc:
                logger.error("Error during symptom model inference in fusion: %s", exc, exc_info=True)
                individual_results["symptoms"] = ModalityOutput(
                    modality="symptoms",
                    available=False,
                    ran=False,
                    predictions=[],
                    notes=f"Inference error: {str(exc)}",
                ).model_dump()
                modalities_unavailable.append("symptoms")
        else:
            individual_results["symptoms"] = ModalityOutput(
                modality="symptoms",
                available=False,
                ran=False,
                predictions=[],
                notes="DistilBERT symptom model is unavailable (weights pending deployment).",
            ).model_dump()
            modalities_unavailable.append("symptoms")

    # ── 3. Skin Image Modality Execution ─────────────────────────────────────
    if "skin" in modalities_received:
        skin_model = model_manager.get_skin_model()
        if skin_model.is_available():
            image_bytes = _decode_image_payload(request.skin_image, "skin")
            try:
                skin_result = skin_model.infer(image_bytes=image_bytes)
                if skin_result.available:
                    detections = [
                        DetectionItem(
                            condition=d.condition,
                            confidence=d.confidence,
                            bounding_box=BoundingBoxModel(
                                x1=d.bounding_box.x1,
                                y1=d.bounding_box.y1,
                                x2=d.bounding_box.x2,
                                y2=d.bounding_box.y2,
                            ) if d.bounding_box else None,
                        )
                        for d in skin_result.detections
                    ]
                    individual_results["skin"] = ModalityOutput(
                        modality="skin",
                        available=True,
                        ran=True,
                        detections=detections,
                        notes=skin_result.notes or "YOLOv8 skin inference completed.",
                    ).model_dump()
                    modalities_run.append("skin")

                    for d in detections:
                        diagnostic_candidates.append({
                            "condition": d.condition,
                            "confidence": d.confidence,
                            "modality": "skin",
                            "metadata": {"bounding_box": d.bounding_box.model_dump() if d.bounding_box else None},
                        })
                else:
                    individual_results["skin"] = ModalityOutput(
                        modality="skin",
                        available=False,
                        ran=False,
                        detections=[],
                        notes=skin_result.notes or "YOLOv8 skin model unavailable.",
                    ).model_dump()
                    modalities_unavailable.append("skin")
            except HTTPException:
                raise
            except Exception as exc:
                logger.error("Error during skin model inference in fusion: %s", exc, exc_info=True)
                individual_results["skin"] = ModalityOutput(
                    modality="skin",
                    available=False,
                    ran=False,
                    detections=[],
                    notes=f"Inference error: {str(exc)}",
                ).model_dump()
                modalities_unavailable.append("skin")
        else:
            individual_results["skin"] = ModalityOutput(
                modality="skin",
                available=False,
                ran=False,
                detections=[],
                notes="YOLOv8 skin model is unavailable (weights pending deployment).",
            ).model_dump()
            modalities_unavailable.append("skin")

    # ── 4. Eye Image Modality Execution ──────────────────────────────────────
    if "eye" in modalities_received:
        eye_model = model_manager.get_eye_model()
        if eye_model.is_available():
            image_bytes = _decode_image_payload(request.eye_image, "eye")
            try:
                eye_result = eye_model.infer(image_bytes=image_bytes)
                if eye_result.available:
                    detections = [
                        DetectionItem(
                            condition=d.condition,
                            confidence=d.confidence,
                            bounding_box=BoundingBoxModel(
                                x1=d.bounding_box.x1,
                                y1=d.bounding_box.y1,
                                x2=d.bounding_box.x2,
                                y2=d.bounding_box.y2,
                            ) if d.bounding_box else None,
                        )
                        for d in eye_result.detections
                    ]
                    individual_results["eye"] = ModalityOutput(
                        modality="eye",
                        available=True,
                        ran=True,
                        detections=detections,
                        notes=eye_result.notes or "YOLOv8 eye inference completed.",
                    ).model_dump()
                    modalities_run.append("eye")

                    for d in detections:
                        diagnostic_candidates.append({
                            "condition": d.condition,
                            "confidence": d.confidence,
                            "modality": "eye",
                            "metadata": {"bounding_box": d.bounding_box.model_dump() if d.bounding_box else None},
                        })
                else:
                    individual_results["eye"] = ModalityOutput(
                        modality="eye",
                        available=False,
                        ran=False,
                        detections=[],
                        notes=eye_result.notes or "YOLOv8 eye model unavailable.",
                    ).model_dump()
                    modalities_unavailable.append("eye")
            except HTTPException:
                raise
            except Exception as exc:
                logger.error("Error during eye model inference in fusion: %s", exc, exc_info=True)
                individual_results["eye"] = ModalityOutput(
                    modality="eye",
                    available=False,
                    ran=False,
                    detections=[],
                    notes=f"Inference error: {str(exc)}",
                ).model_dump()
                modalities_unavailable.append("eye")
        else:
            individual_results["eye"] = ModalityOutput(
                modality="eye",
                available=False,
                ran=False,
                detections=[],
                notes="YOLOv8 eye model is unavailable (weights pending deployment).",
            ).model_dump()
            modalities_unavailable.append("eye")

    # ── 5. Report Modality Execution (T5 Summarisation) ──────────────────────
    if "report" in modalities_received:
        report_model = model_manager.get_report_model()
        if report_model.is_available():
            try:
                rep_result = report_model.infer(text=request.report_text)
                if rep_result.available:
                    report_summary = rep_result.summary
                    individual_results["report"] = ModalityOutput(
                        modality="report",
                        available=True,
                        ran=True,
                        summary=rep_result.summary,
                        notes=rep_result.notes or "T5 summarisation completed.",
                    ).model_dump()
                    modalities_run.append("report")
                else:
                    individual_results["report"] = ModalityOutput(
                        modality="report",
                        available=False,
                        ran=False,
                        summary="",
                        notes=rep_result.notes or "T5 report model unavailable.",
                    ).model_dump()
                    modalities_unavailable.append("report")
            except Exception as exc:
                logger.error("Error during report summarisation in fusion: %s", exc, exc_info=True)
                individual_results["report"] = ModalityOutput(
                    modality="report",
                    available=False,
                    ran=False,
                    summary="",
                    notes=f"Summarisation error: {str(exc)}",
                ).model_dump()
                modalities_unavailable.append("report")
        else:
            individual_results["report"] = ModalityOutput(
                modality="report",
                available=False,
                ran=False,
                summary="",
                notes="T5 medical report model is unavailable (weights pending deployment).",
            ).model_dump()
            modalities_unavailable.append("report")

    # ── 6. Multimodal Synthesis & Fusion Logic ───────────────────────────────

    # Scenario A: All requested models were unavailable
    if not modalities_run:
        return FusionResponse(
            modalities_received=modalities_received,
            modalities_run=[],
            modalities_unavailable=modalities_unavailable,
            individual_results=individual_results,
            fused_result=None,
            all_fused_conditions=[],
            urgency="routine",
            urgency_score=0.0,
            recommended_specialist="General Physician",
            explanation=(
                "All requested AI models are currently unavailable (weights pending Colab training/deployment). "
                "In accordance with clinical safety guidelines, no diagnostic predictions or scores have been fabricated. "
                "Please consult a qualified medical practitioner."
            ),
            disclaimer=MEDIQ_SAFETY_DISCLAIMER,
            notes="Unavailable models: " + ", ".join(modalities_unavailable),
        )

    # Scenario B: ONLY report summarisation ran (non-diagnostic)
    if modalities_run == ["report"]:
        fused = FusedCondition(
            condition="Medical Report Summarized",
            confidence=None,
            supporting_modalities=["report"],
            finding_type="informational",
            notes="Informational summary only. Medical report summarization does not constitute a medical diagnosis.",
        )
        explanation = (
            "Medical report successfully processed and summarized using T5. "
            "Abstractive text summarization provides clinical context and does not constitute a diagnostic prediction."
        )
        if report_summary:
            explanation += f' Summary: "{report_summary}"'

        return FusionResponse(
            modalities_received=modalities_received,
            modalities_run=["report"],
            modalities_unavailable=modalities_unavailable,
            individual_results=individual_results,
            fused_result=fused,
            all_fused_conditions=[fused],
            urgency="low",
            urgency_score=URGENCY_SCORES["low"],
            recommended_specialist="General Physician",
            explanation=explanation,
            disclaimer=MEDIQ_SAFETY_DISCLAIMER,
            notes="Report processed for informational decision support only.",
        )

    # Scenario C: One or more diagnostic modalities ran (symptoms, skin, eye)
    # Group candidates and evaluate agreement vs distinct multi-domain findings
    fused_conditions: List[FusedCondition] = []
    explanation_parts: List[str] = []
    urgency_candidates: List[str] = []
    specialist_candidates: List[str] = []
    cross_modal_agreement_found = False
    cross_modal_conflict_found = False

    # Group diagnostic candidates across modalities
    processed_indices: Set[int] = set()

    for i, c1 in enumerate(diagnostic_candidates):
        if i in processed_indices:
            continue

        matching_group = [c1]
        for j, c2 in enumerate(diagnostic_candidates):
            if i != j and j not in processed_indices:
                if _conditions_match(c1["condition"], c2["condition"]):
                    matching_group.append(c2)
                    processed_indices.add(j)

        processed_indices.add(i)

        canon_name, domain, cond_urgency, spec = _canonicalize_condition(c1["condition"])
        modalities_in_group = list({m["modality"] for m in matching_group})

        # Check cross-modal agreement
        if len(modalities_in_group) > 1:
            cross_modal_agreement_found = True
            # Compute agreement bonus
            confs = [m["confidence"] for m in matching_group]
            fused_conf = _calculate_agreement_confidence(confs[0], confs[1] if len(confs) > 1 else confs[0])
            notes = (
                f"Cross-modal agreement: Corroborated independently by {', '.join(modalities_in_group)}. "
                f"Agreement bonus applied."
            )
            fused_conditions.append(
                FusedCondition(
                    condition=canon_name,
                    confidence=fused_conf,
                    supporting_modalities=modalities_in_group,
                    finding_type="primary",
                    notes=notes,
                )
            )
            explanation_parts.append(
                f"Corroborating evidence across {', '.join(modalities_in_group)} independently identifies "
                f"'{canon_name}' (cross-modal confidence: {fused_conf:.2f})."
            )
        else:
            # Single-modality candidate
            single_mod = modalities_in_group[0]
            conf = c1["confidence"]
            fused_conditions.append(
                FusedCondition(
                    condition=canon_name,
                    confidence=conf,
                    supporting_modalities=[single_mod],
                    finding_type="secondary" if fused_conditions else "primary",
                    notes=f"Identified via {single_mod} modality.",
                )
            )
            explanation_parts.append(
                f"{single_mod.capitalize()} modality identified '{canon_name}' (confidence: {conf:.2f})."
            )

        urgency_candidates.append(cond_urgency)
        specialist_candidates.append(spec)

    # Check for same-domain conflict across modalities
    # E.g., skin detects benign vs malignant, or symptoms state clear benign while image detects malignancy
    active_diagnostic_mods = [m for m in modalities_run if m in ("symptoms", "skin", "eye")]
    if len(active_diagnostic_mods) > 1 and not cross_modal_agreement_found:
        # Check if domains overlap or if there is conflict
        domains_present = {_canonicalize_condition(c["condition"])[1] for c in diagnostic_candidates}
        if len(domains_present) == 1 and len(fused_conditions) > 1:
            cross_modal_conflict_found = True
            # Discrepancy in same domain -> reduce confidence of candidates & elevate urgency
            for fc in fused_conditions:
                if fc.confidence is not None:
                    fc.confidence = _calculate_disagreement_confidence(fc.confidence)
                fc.finding_type = "conflicting"
                fc.notes = "Conflicting cross-modal indicators in domain; confidence adjusted conservatively."
            urgency_candidates.append("high")
            explanation_parts.append(
                "Diagnostic discrepancy noted between modalities for the same clinical domain. "
                "Confidence values conservatively moderated; urgency elevated to prioritize professional clinical evaluation."
            )
        else:
            explanation_parts.append(
                "Distinct multi-domain findings observed across modalities. "
                "All clinical features preserved without manufacturing artificial consensus."
            )

    # Sort fused conditions: corroborated / highest confidence first
    fused_conditions.sort(
        key=lambda x: (
            len(x.supporting_modalities) > 1,
            x.confidence if x.confidence is not None else 0.0,
        ),
        reverse=True,
    )

    primary_condition = fused_conditions[0] if fused_conditions else None

    # Incorporate report text evidence if available
    if report_summary:
        explanation_parts.append(
            f'Textual context from medical report summary incorporated: "{report_summary[:200]}..."'
        )

    # If any modality was unavailable, document it cleanly in explanation
    if modalities_unavailable:
        explanation_parts.append(
            f"Note: {', '.join(modalities_unavailable)} model(s) were unavailable (weights pending deployment); "
            f"fusion proceeded with available modalities without fabricating missing predictions."
        )

    # Determine overall conservative urgency
    if not urgency_candidates:
        overall_urgency = "low"
    else:
        # Pick highest urgency according to priority
        overall_urgency = max(urgency_candidates, key=lambda u: URGENCY_PRIORITY.get(u, 1))

    urgency_score = URGENCY_SCORES.get(overall_urgency, 0.25)

    # Determine recommended specialist
    if specialist_candidates:
        # Pick specialist corresponding to primary condition
        canon_name, _, _, primary_spec = _canonicalize_condition(primary_condition.condition) if primary_condition else ("", "", "", "General Physician")
        recommended_specialist = primary_spec
    else:
        recommended_specialist = "General Physician"

    full_explanation = " ".join(explanation_parts)

    return FusionResponse(
        modalities_received=modalities_received,
        modalities_run=modalities_run,
        modalities_unavailable=modalities_unavailable,
        individual_results=individual_results,
        fused_result=primary_condition,
        all_fused_conditions=fused_conditions,
        urgency=overall_urgency,
        urgency_score=urgency_score,
        recommended_specialist=recommended_specialist,
        explanation=full_explanation,
        disclaimer=MEDIQ_SAFETY_DISCLAIMER,
        notes="Multimodal AI Fusion evaluation completed successfully.",
    )
