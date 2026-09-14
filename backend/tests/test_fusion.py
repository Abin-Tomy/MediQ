"""
Comprehensive Multimodal AI Fusion Test Suite.

Verifies:
1. All 15 non-empty modality combinations.
2. Strict model execution rules (models execute only when input is present).
3. Missing model weights / unavailable model behavior (zero fabricated predictions).
4. Validation rules: empty requests, whitespace-only, ambiguous image types, malformed base64.
5. Cross-modal agreement: confidence bonus, unified condition, explanation citations.
6. Cross-modal disagreement / multi-domain preservation: both findings preserved, conservative urgency.
7. T5 report safety: informational summary preserved without diagnostic fabrication.
8. Deterministic specialist mappings and conservative urgency levels.
"""

import base64
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app
from app.ai import model_manager
from app.ai.image_model import (
    BoundingBox,
    Detection,
    ImageInferenceResult,
    YOLOv8ImageModel,
)
from app.ai.report_model import ReportInferenceResult, T5ReportModel
from app.ai.symptom_model import (
    ConditionPrediction,
    DistilBERTSymptomModel,
    SymptomInferenceResult,
)
from app.models.analysis import FusionInput
from app.utils.auth_dependencies import get_current_user

# Sample 1x1 valid base64 PNG for image testing
DUMMY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


class BaseFusionTestCase(unittest.TestCase):
    """Base test case setting up TestClient with authenticated mock user."""

    @classmethod
    def setUpClass(cls):
        # Override authentication dependency for tests
        app.dependency_overrides[get_current_user] = lambda: {
            "uid": "test_patient_001",
            "role": "patient",
            "email": "test@mediq.app",
        }
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()


class TestFusionInputValidation(BaseFusionTestCase):
    """Tests input validation and error handling for /analyse/fuse."""

    def test_empty_request_rejected(self):
        """Completely empty request body must be rejected with 422."""
        response = self.client.post("/analyse/fuse", json={})
        self.assertEqual(response.status_code, 422)

    def test_whitespace_only_symptoms_rejected(self):
        """Whitespace-only symptoms without other modalities must be rejected with 422."""
        response = self.client.post("/analyse/fuse", json={"symptoms": "   \n\t  "})
        self.assertEqual(response.status_code, 422)

    def test_ambiguous_image_type_rejected(self):
        """Generic image without image_type must be rejected with 422."""
        response = self.client.post("/analyse/fuse", json={"image": DUMMY_PNG_B64})
        self.assertEqual(response.status_code, 422)
        errors = response.json().get("detail", [])
        self.assertTrue(any("Image type ambiguous" in str(e) for e in errors))

    def test_invalid_image_type_rejected(self):
        """Generic image with invalid image_type (not 'skin' or 'eye') must be rejected with 422."""
        response = self.client.post(
            "/analyse/fuse",
            json={"image": DUMMY_PNG_B64, "image_type": "cardiac"},
        )
        self.assertEqual(response.status_code, 422)

    def test_malformed_base64_skin_image_rejected(self):
        """Corrupted base64 for skin_image must return 400 Bad Request."""
        response = self.client.post(
            "/analyse/fuse",
            json={"skin_image": "not_valid_base64_!@#$%^&*()"},
        )
        # Note: If mock model is unavailable, it checks availability before decoding,
        # but with mock available model it must raise 400.
        with patch.object(model_manager.get_skin_model(), "is_available", return_value=True):
            resp = self.client.post(
                "/analyse/fuse",
                json={"skin_image": "not_valid_base64_!@#$%^&*()"},
            )
            self.assertEqual(resp.status_code, 400)
            self.assertIn("Malformed or invalid base64", resp.json()["detail"])

    def test_malformed_base64_eye_image_rejected(self):
        """Corrupted base64 for eye_image must return 400 Bad Request."""
        with patch.object(model_manager.get_eye_model(), "is_available", return_value=True):
            resp = self.client.post(
                "/analyse/fuse",
                json={"eye_image": "not_valid_base64_!@#$%^&*()"},
            )
            self.assertEqual(resp.status_code, 400)
            self.assertIn("Malformed or invalid base64", resp.json()["detail"])

    def test_unauthorized_role_rejected(self):
        """User with unauthorized role must receive 403 Forbidden."""
        app.dependency_overrides[get_current_user] = lambda: {
            "uid": "intruder",
            "role": "unauthorized_role",
        }
        try:
            resp = self.client.post(
                "/analyse/fuse",
                json={"symptoms": "Headache and fever"},
            )
            self.assertEqual(resp.status_code, 403)
        finally:
            app.dependency_overrides[get_current_user] = lambda: {
                "uid": "test_patient_001",
                "role": "patient",
            }


class TestFusionModelUnavailableRealEnvironment(BaseFusionTestCase):
    """
    Tests Fusion behavior in the real un-mocked environment where model weights
    have not been deployed yet. Strictly validates NO fabricated predictions.
    """

    def test_symptoms_unavailable_real_env(self):
        """Symptom input with unavailable model returns safe response with zero fabricated predictions."""
        resp = self.client.post("/analyse/fuse", json={"symptoms": "fever and rash"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["modalities_received"], ["symptoms"])
        self.assertEqual(data["modalities_run"], [])
        self.assertIn("symptoms", data["modalities_unavailable"])
        self.assertIsNone(data["fused_result"])
        self.assertEqual(data["all_fused_conditions"], [])
        self.assertEqual(data["urgency"], "routine")
        self.assertEqual(data["recommended_specialist"], "General Physician")
        self.assertIn("In accordance with clinical safety guidelines, no diagnostic predictions", data["explanation"])
        self.assertIn("MediQ provides informational decision support", data["disclaimer"])

    def test_all_four_modalities_unavailable_real_env(self):
        """All 4 modalities supplied with no weights returns safe unavailable response."""
        resp = self.client.post(
            "/analyse/fuse",
            json={
                "symptoms": "cough, high fever, chest tightness",
                "skin_image": DUMMY_PNG_B64,
                "eye_image": DUMMY_PNG_B64,
                "report_text": "CBC: WBC 14.5, Platelets 120k. LFT: ALT 45, AST 52.",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(set(data["modalities_received"]), {"symptoms", "skin", "eye", "report"})
        self.assertEqual(data["modalities_run"], [])
        self.assertEqual(set(data["modalities_unavailable"]), {"symptoms", "skin", "eye", "report"})
        self.assertIsNone(data["fused_result"])
        self.assertEqual(data["all_fused_conditions"], [])
        self.assertEqual(data["urgency_score"], 0.0)


class TestAll15ModalityCombinations(BaseFusionTestCase):
    """
    Tests ALL 15 non-empty modality combinations using controlled stubs solely
    within test boundaries, as specified in the requirements.
    """

    def _setup_stubs(self):
        # Symptom model stub
        mock_symptom_model = MagicMock(spec=DistilBERTSymptomModel)
        mock_symptom_model.is_available.return_value = True
        mock_symptom_model.infer.return_value = SymptomInferenceResult(
            model="distilbert_symptom",
            available=True,
            predictions=[
                ConditionPrediction(condition="Pneumonia", confidence=0.82),
                ConditionPrediction(condition="Bronchial Asthma", confidence=0.65),
            ],
            notes="DistilBERT stub inference.",
            model_version="distilbert-symptom-v1",
        )

        # Skin model stub
        mock_skin_model = MagicMock(spec=YOLOv8ImageModel)
        mock_skin_model.is_available.return_value = True
        mock_skin_model.infer.return_value = ImageInferenceResult(
            model="yolov8_skin",
            available=True,
            detections=[
                Detection(
                    condition="Melanoma",
                    confidence=0.88,
                    bounding_box=BoundingBox(x1=10.0, y1=15.0, x2=120.0, y2=130.0),
                )
            ],
            notes="YOLOv8 skin stub inference.",
        )

        # Eye model stub
        mock_eye_model = MagicMock(spec=YOLOv8ImageModel)
        mock_eye_model.is_available.return_value = True
        mock_eye_model.infer.return_value = ImageInferenceResult(
            model="yolov8_eye",
            available=True,
            detections=[
                Detection(
                    condition="Cataract",
                    confidence=0.79,
                    bounding_box=BoundingBox(x1=50.0, y1=50.0, x2=200.0, y2=200.0),
                )
            ],
            notes="YOLOv8 eye stub inference.",
        )

        # Report model stub
        mock_report_model = MagicMock(spec=T5ReportModel)
        mock_report_model.is_available.return_value = True
        mock_report_model.infer.return_value = ReportInferenceResult(
            model="t5_medical_report",
            available=True,
            summary="Chest X-ray shows bibasilar patchy consolidations consistent with lower respiratory tract process.",
            notes="T5 stub inference.",
        )

        return (
            patch.object(model_manager, "get_symptom_model", return_value=mock_symptom_model),
            patch.object(model_manager, "get_skin_model", return_value=mock_skin_model),
            patch.object(model_manager, "get_eye_model", return_value=mock_eye_model),
            patch.object(model_manager, "get_report_model", return_value=mock_report_model),
            mock_symptom_model,
            mock_skin_model,
            mock_eye_model,
            mock_report_model,
        )

    def test_comb_01_symptoms_only(self):
        """Combination 1: symptoms only."""
        p_sym, p_skin, p_eye, p_rep, m_sym, m_skin, m_eye, m_rep = self._setup_stubs()
        with p_sym, p_skin, p_eye, p_rep:
            resp = self.client.post("/analyse/fuse", json={"symptoms": "Severe cough and chills"})
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["modalities_received"], ["symptoms"])
            self.assertEqual(data["modalities_run"], ["symptoms"])
            self.assertEqual(data["fused_result"]["condition"], "Pneumonia")
            self.assertEqual(data["recommended_specialist"], "Pulmonologist / General Physician")
            m_sym.infer.assert_called_once()
            m_skin.infer.assert_not_called()
            m_eye.infer.assert_not_called()
            m_rep.infer.assert_not_called()

    def test_comb_02_skin_only(self):
        """Combination 2: skin only."""
        p_sym, p_skin, p_eye, p_rep, m_sym, m_skin, m_eye, m_rep = self._setup_stubs()
        with p_sym, p_skin, p_eye, p_rep:
            resp = self.client.post("/analyse/fuse", json={"skin_image": DUMMY_PNG_B64})
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["modalities_received"], ["skin"])
            self.assertEqual(data["modalities_run"], ["skin"])
            self.assertEqual(data["fused_result"]["condition"], "Melanoma")
            self.assertEqual(data["recommended_specialist"], "Dermatologist / Oncologist")
            self.assertEqual(data["urgency"], "high")
            m_skin.infer.assert_called_once()
            m_sym.infer.assert_not_called()
            m_eye.infer.assert_not_called()
            m_rep.infer.assert_not_called()

    def test_comb_03_eye_only(self):
        """Combination 3: eye only."""
        p_sym, p_skin, p_eye, p_rep, m_sym, m_skin, m_eye, m_rep = self._setup_stubs()
        with p_sym, p_skin, p_eye, p_rep:
            resp = self.client.post("/analyse/fuse", json={"eye_image": DUMMY_PNG_B64})
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["modalities_received"], ["eye"])
            self.assertEqual(data["modalities_run"], ["eye"])
            self.assertEqual(data["fused_result"]["condition"], "Cataract")
            self.assertEqual(data["recommended_specialist"], "Ophthalmologist")
            m_eye.infer.assert_called_once()
            m_sym.infer.assert_not_called()
            m_skin.infer.assert_not_called()
            m_rep.infer.assert_not_called()

    def test_comb_04_report_only(self):
        """Combination 4: report only (verifies T5 summary as informational, not diagnosis)."""
        p_sym, p_skin, p_eye, p_rep, m_sym, m_skin, m_eye, m_rep = self._setup_stubs()
        with p_sym, p_skin, p_eye, p_rep:
            resp = self.client.post(
                "/analyse/fuse",
                json={"report_text": "Pathology report: Biopsy shows normal dermal architecture."},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["modalities_received"], ["report"])
            self.assertEqual(data["modalities_run"], ["report"])
            self.assertEqual(data["fused_result"]["condition"], "Medical Report Summarized")
            self.assertIsNone(data["fused_result"]["confidence"])
            self.assertEqual(data["fused_result"]["finding_type"], "informational")
            self.assertIn("Abstractive text summarization", data["explanation"])
            m_rep.infer.assert_called_once()
            m_sym.infer.assert_not_called()
            m_skin.infer.assert_not_called()
            m_eye.infer.assert_not_called()

    def test_comb_05_symptoms_and_skin(self):
        """Combination 5: symptoms + skin."""
        p_sym, p_skin, p_eye, p_rep, m_sym, m_skin, m_eye, m_rep = self._setup_stubs()
        with p_sym, p_skin, p_eye, p_rep:
            resp = self.client.post(
                "/analyse/fuse",
                json={"symptoms": "Cough and fever", "skin_image": DUMMY_PNG_B64},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(set(data["modalities_received"]), {"symptoms", "skin"})
            self.assertEqual(set(data["modalities_run"]), {"symptoms", "skin"})
            m_sym.infer.assert_called_once()
            m_skin.infer.assert_called_once()
            m_eye.infer.assert_not_called()
            m_rep.infer.assert_not_called()

    def test_comb_06_symptoms_and_eye(self):
        """Combination 6: symptoms + eye."""
        p_sym, p_skin, p_eye, p_rep, m_sym, m_skin, m_eye, m_rep = self._setup_stubs()
        with p_sym, p_skin, p_eye, p_rep:
            resp = self.client.post(
                "/analyse/fuse",
                json={"symptoms": "Cough and fever", "eye_image": DUMMY_PNG_B64},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(set(data["modalities_received"]), {"symptoms", "eye"})
            self.assertEqual(set(data["modalities_run"]), {"symptoms", "eye"})
            m_sym.infer.assert_called_once()
            m_eye.infer.assert_called_once()
            m_skin.infer.assert_not_called()
            m_rep.infer.assert_not_called()

    def test_comb_07_symptoms_and_report(self):
        """Combination 7: symptoms + report."""
        p_sym, p_skin, p_eye, p_rep, m_sym, m_skin, m_eye, m_rep = self._setup_stubs()
        with p_sym, p_skin, p_eye, p_rep:
            resp = self.client.post(
                "/analyse/fuse",
                json={"symptoms": "Chest pain", "report_text": "X-ray shows consolidation."},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(set(data["modalities_received"]), {"symptoms", "report"})
            self.assertEqual(set(data["modalities_run"]), {"symptoms", "report"})
            m_sym.infer.assert_called_once()
            m_rep.infer.assert_called_once()
            m_skin.infer.assert_not_called()
            m_eye.infer.assert_not_called()

    def test_comb_08_skin_and_eye(self):
        """Combination 8: skin + eye."""
        p_sym, p_skin, p_eye, p_rep, m_sym, m_skin, m_eye, m_rep = self._setup_stubs()
        with p_sym, p_skin, p_eye, p_rep:
            resp = self.client.post(
                "/analyse/fuse",
                json={"skin_image": DUMMY_PNG_B64, "eye_image": DUMMY_PNG_B64},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(set(data["modalities_received"]), {"skin", "eye"})
            self.assertEqual(set(data["modalities_run"]), {"skin", "eye"})
            m_skin.infer.assert_called_once()
            m_eye.infer.assert_called_once()
            m_sym.infer.assert_not_called()
            m_rep.infer.assert_not_called()

    def test_comb_09_skin_and_report(self):
        """Combination 9: skin + report."""
        p_sym, p_skin, p_eye, p_rep, m_sym, m_skin, m_eye, m_rep = self._setup_stubs()
        with p_sym, p_skin, p_eye, p_rep:
            resp = self.client.post(
                "/analyse/fuse",
                json={"skin_image": DUMMY_PNG_B64, "report_text": "Dermatopathology report..."},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(set(data["modalities_received"]), {"skin", "report"})
            self.assertEqual(set(data["modalities_run"]), {"skin", "report"})
            m_skin.infer.assert_called_once()
            m_rep.infer.assert_called_once()
            m_sym.infer.assert_not_called()
            m_eye.infer.assert_not_called()

    def test_comb_10_eye_and_report(self):
        """Combination 10: eye + report."""
        p_sym, p_skin, p_eye, p_rep, m_sym, m_skin, m_eye, m_rep = self._setup_stubs()
        with p_sym, p_skin, p_eye, p_rep:
            resp = self.client.post(
                "/analyse/fuse",
                json={"eye_image": DUMMY_PNG_B64, "report_text": "Slit-lamp exam report..."},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(set(data["modalities_received"]), {"eye", "report"})
            self.assertEqual(set(data["modalities_run"]), {"eye", "report"})
            m_eye.infer.assert_called_once()
            m_rep.infer.assert_called_once()
            m_sym.infer.assert_not_called()
            m_skin.infer.assert_not_called()

    def test_comb_11_symptoms_skin_eye(self):
        """Combination 11: symptoms + skin + eye."""
        p_sym, p_skin, p_eye, p_rep, m_sym, m_skin, m_eye, m_rep = self._setup_stubs()
        with p_sym, p_skin, p_eye, p_rep:
            resp = self.client.post(
                "/analyse/fuse",
                json={
                    "symptoms": "Fever and generalized symptoms",
                    "skin_image": DUMMY_PNG_B64,
                    "eye_image": DUMMY_PNG_B64,
                },
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(set(data["modalities_received"]), {"symptoms", "skin", "eye"})
            self.assertEqual(set(data["modalities_run"]), {"symptoms", "skin", "eye"})
            m_sym.infer.assert_called_once()
            m_skin.infer.assert_called_once()
            m_eye.infer.assert_called_once()
            m_rep.infer.assert_not_called()

    def test_comb_12_symptoms_skin_report(self):
        """Combination 12: symptoms + skin + report."""
        p_sym, p_skin, p_eye, p_rep, m_sym, m_skin, m_eye, m_rep = self._setup_stubs()
        with p_sym, p_skin, p_eye, p_rep:
            resp = self.client.post(
                "/analyse/fuse",
                json={
                    "symptoms": "Skin itch and fever",
                    "skin_image": DUMMY_PNG_B64,
                    "report_text": "Biopsy report...",
                },
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(set(data["modalities_received"]), {"symptoms", "skin", "report"})
            self.assertEqual(set(data["modalities_run"]), {"symptoms", "skin", "report"})
            m_sym.infer.assert_called_once()
            m_skin.infer.assert_called_once()
            m_rep.infer.assert_called_once()
            m_eye.infer.assert_not_called()

    def test_comb_13_symptoms_eye_report(self):
        """Combination 13: symptoms + eye + report."""
        p_sym, p_skin, p_eye, p_rep, m_sym, m_skin, m_eye, m_rep = self._setup_stubs()
        with p_sym, p_skin, p_eye, p_rep:
            resp = self.client.post(
                "/analyse/fuse",
                json={
                    "symptoms": "Eye blurriness",
                    "eye_image": DUMMY_PNG_B64,
                    "report_text": "Tonometry report...",
                },
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(set(data["modalities_received"]), {"symptoms", "eye", "report"})
            self.assertEqual(set(data["modalities_run"]), {"symptoms", "eye", "report"})
            m_sym.infer.assert_called_once()
            m_eye.infer.assert_called_once()
            m_rep.infer.assert_called_once()
            m_skin.infer.assert_not_called()

    def test_comb_14_skin_eye_report(self):
        """Combination 14: skin + eye + report."""
        p_sym, p_skin, p_eye, p_rep, m_sym, m_skin, m_eye, m_rep = self._setup_stubs()
        with p_sym, p_skin, p_eye, p_rep:
            resp = self.client.post(
                "/analyse/fuse",
                json={
                    "skin_image": DUMMY_PNG_B64,
                    "eye_image": DUMMY_PNG_B64,
                    "report_text": "Clinical summary...",
                },
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(set(data["modalities_received"]), {"skin", "eye", "report"})
            self.assertEqual(set(data["modalities_run"]), {"skin", "eye", "report"})
            m_skin.infer.assert_called_once()
            m_eye.infer.assert_called_once()
            m_rep.infer.assert_called_once()
            m_sym.infer.assert_not_called()

    def test_comb_15_all_four_modalities(self):
        """Combination 15: symptoms + skin + eye + report."""
        p_sym, p_skin, p_eye, p_rep, m_sym, m_skin, m_eye, m_rep = self._setup_stubs()
        with p_sym, p_skin, p_eye, p_rep:
            resp = self.client.post(
                "/analyse/fuse",
                json={
                    "symptoms": "Fever, rash, ocular discharge",
                    "skin_image": DUMMY_PNG_B64,
                    "eye_image": DUMMY_PNG_B64,
                    "report_text": "Hospital admission clinical notes...",
                },
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(set(data["modalities_received"]), {"symptoms", "skin", "eye", "report"})
            self.assertEqual(set(data["modalities_run"]), {"symptoms", "skin", "eye", "report"})
            m_sym.infer.assert_called_once()
            m_skin.infer.assert_called_once()
            m_eye.infer.assert_called_once()
            m_rep.infer.assert_called_once()


class TestCrossModalAgreementAndDisagreement(BaseFusionTestCase):
    """Tests cross-modal condition matching, agreement bonus, and discrepancy handling."""

    def test_cross_modal_agreement_symptoms_and_skin(self):
        """When symptoms and skin model corroborate the same condition, agreement bonus is applied."""
        mock_sym = MagicMock(spec=DistilBERTSymptomModel)
        mock_sym.is_available.return_value = True
        mock_sym.infer.return_value = SymptomInferenceResult(
            model="distilbert_symptom",
            available=True,
            predictions=[ConditionPrediction(condition="Melanoma", confidence=0.75)],
            notes="Symptom inference",
        )

        mock_skin = MagicMock(spec=YOLOv8ImageModel)
        mock_skin.is_available.return_value = True
        mock_skin.infer.return_value = ImageInferenceResult(
            model="yolov8_skin",
            available=True,
            detections=[Detection(condition="mel", confidence=0.80)],
            notes="Skin inference",
        )

        with patch.object(model_manager, "get_symptom_model", return_value=mock_sym), \
             patch.object(model_manager, "get_skin_model", return_value=mock_skin):
            resp = self.client.post(
                "/analyse/fuse",
                json={"symptoms": "Dark growing skin lesion with irregular borders", "skin_image": DUMMY_PNG_B64},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            fused = data["fused_result"]
            self.assertEqual(fused["condition"], "Melanoma")
            # max(0.80, 0.75) + 0.15 * min(0.80, 0.75) = 0.80 + 0.1125 = 0.9125
            self.assertGreater(fused["confidence"], 0.80)
            self.assertEqual(set(fused["supporting_modalities"]), {"symptoms", "skin"})
            self.assertIn("Cross-modal agreement", fused["notes"])
            self.assertIn("Corroborating evidence across", data["explanation"])

    def test_cross_modal_agreement_symptoms_and_eye(self):
        """When symptoms and eye model corroborate conjunctivitis / injection, agreement is applied."""
        mock_sym = MagicMock(spec=DistilBERTSymptomModel)
        mock_sym.is_available.return_value = True
        mock_sym.infer.return_value = SymptomInferenceResult(
            model="distilbert_symptom",
            available=True,
            predictions=[ConditionPrediction(condition="Conjunctivitis", confidence=0.70)],
            notes="Symptom inference",
        )

        mock_eye = MagicMock(spec=YOLOv8ImageModel)
        mock_eye.is_available.return_value = True
        mock_eye.infer.return_value = ImageInferenceResult(
            model="yolov8_eye",
            available=True,
            detections=[Detection(condition="Conjunctival injection", confidence=0.85)],
            notes="Eye inference",
        )

        with patch.object(model_manager, "get_symptom_model", return_value=mock_sym), \
             patch.object(model_manager, "get_eye_model", return_value=mock_eye):
            resp = self.client.post(
                "/analyse/fuse",
                json={"symptoms": "Red itchy watery eyes", "eye_image": DUMMY_PNG_B64},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            fused = data["fused_result"]
            self.assertIn("Conjunctivitis", fused["condition"])
            self.assertGreater(fused["confidence"], 0.85)
            self.assertEqual(set(fused["supporting_modalities"]), {"symptoms", "eye"})

    def test_multi_domain_findings_preserved(self):
        """Multi-domain findings (e.g. Pneumonia + Nevus) are both preserved in all_fused_conditions."""
        mock_sym = MagicMock(spec=DistilBERTSymptomModel)
        mock_sym.is_available.return_value = True
        mock_sym.infer.return_value = SymptomInferenceResult(
            model="distilbert_symptom",
            available=True,
            predictions=[ConditionPrediction(condition="Pneumonia", confidence=0.85)],
            notes="Symptom inference",
        )

        mock_skin = MagicMock(spec=YOLOv8ImageModel)
        mock_skin.is_available.return_value = True
        mock_skin.infer.return_value = ImageInferenceResult(
            model="yolov8_skin",
            available=True,
            detections=[Detection(condition="nv", confidence=0.70)],  # Melanocytic nevus
            notes="Skin inference",
        )

        with patch.object(model_manager, "get_symptom_model", return_value=mock_sym), \
             patch.object(model_manager, "get_skin_model", return_value=mock_skin):
            resp = self.client.post(
                "/analyse/fuse",
                json={"symptoms": "Cough and high fever", "skin_image": DUMMY_PNG_B64},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            conditions = [c["condition"] for c in data["all_fused_conditions"]]
            self.assertIn("Pneumonia", conditions)
            self.assertIn("Melanocytic Nevus", conditions)
            self.assertIn("Distinct multi-domain findings", data["explanation"])

    def test_same_domain_conflict_elevates_urgency(self):
        """When conflicting indications occur within the same domain, urgency is elevated and confidence moderated."""
        mock_sym = MagicMock(spec=DistilBERTSymptomModel)
        mock_sym.is_available.return_value = True
        mock_sym.infer.return_value = SymptomInferenceResult(
            model="distilbert_symptom",
            available=True,
            predictions=[ConditionPrediction(condition="Acne", confidence=0.70)],
            notes="Symptom inference",
        )

        mock_skin = MagicMock(spec=YOLOv8ImageModel)
        mock_skin.is_available.return_value = True
        mock_skin.infer.return_value = ImageInferenceResult(
            model="yolov8_skin",
            available=True,
            detections=[Detection(condition="Melanoma", confidence=0.85)],
            notes="Skin inference",
        )

        with patch.object(model_manager, "get_symptom_model", return_value=mock_sym), \
             patch.object(model_manager, "get_skin_model", return_value=mock_skin):
            resp = self.client.post(
                "/analyse/fuse",
                json={"symptoms": "Mild acne lesions on face", "skin_image": DUMMY_PNG_B64},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["urgency"], "high")
            self.assertIn("discrepancy noted", data["explanation"].lower())
            for cond in data["all_fused_conditions"]:
                self.assertEqual(cond["finding_type"], "conflicting")

    def test_one_available_one_unavailable_modality(self):
        """When one requested model is available and another is unavailable, available output is used."""
        mock_sym = MagicMock(spec=DistilBERTSymptomModel)
        mock_sym.is_available.return_value = True
        mock_sym.infer.return_value = SymptomInferenceResult(
            model="distilbert_symptom",
            available=True,
            predictions=[ConditionPrediction(condition="Dengue", confidence=0.80)],
            notes="Symptom inference",
        )

        mock_skin = MagicMock(spec=YOLOv8ImageModel)
        mock_skin.is_available.return_value = False  # Unavailable!

        with patch.object(model_manager, "get_symptom_model", return_value=mock_sym), \
             patch.object(model_manager, "get_skin_model", return_value=mock_skin):
            resp = self.client.post(
                "/analyse/fuse",
                json={"symptoms": "High fever with joint pain", "skin_image": DUMMY_PNG_B64},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(set(data["modalities_received"]), {"symptoms", "skin"})
            self.assertEqual(data["modalities_run"], ["symptoms"])
            self.assertEqual(data["modalities_unavailable"], ["skin"])
            self.assertEqual(data["fused_result"]["condition"], "Dengue")
            self.assertIn("skin model(s) were unavailable", data["explanation"])


class TestSpecialistAndUrgencyTriage(BaseFusionTestCase):
    """Tests deterministic clinical specialist and urgency mapping."""

    def test_specialist_mapping_dermatology(self):
        """Dermatologic condition maps to Dermatologist."""
        mock_skin = MagicMock(spec=YOLOv8ImageModel)
        mock_skin.is_available.return_value = True
        mock_skin.infer.return_value = ImageInferenceResult(
            model="yolov8_skin",
            available=True,
            detections=[Detection(condition="nv", confidence=0.80)],
        )
        with patch.object(model_manager, "get_skin_model", return_value=mock_skin):
            resp = self.client.post("/analyse/fuse", json={"skin_image": DUMMY_PNG_B64})
            self.assertEqual(resp.json()["recommended_specialist"], "Dermatologist")
            self.assertEqual(resp.json()["urgency"], "low")

    def test_specialist_mapping_ophthalmology(self):
        """Ophthalmic condition maps to Ophthalmologist."""
        mock_eye = MagicMock(spec=YOLOv8ImageModel)
        mock_eye.is_available.return_value = True
        mock_eye.infer.return_value = ImageInferenceResult(
            model="yolov8_eye",
            available=True,
            detections=[Detection(condition="Keratitis", confidence=0.85)],
        )
        with patch.object(model_manager, "get_eye_model", return_value=mock_eye):
            resp = self.client.post("/analyse/fuse", json={"eye_image": DUMMY_PNG_B64})
            self.assertEqual(resp.json()["recommended_specialist"], "Ophthalmologist")
            self.assertEqual(resp.json()["urgency"], "high")

    def test_emergency_condition_urgency(self):
        """Nipah virus or cardiac condition maps to emergency urgency and 1.0 score."""
        mock_sym = MagicMock(spec=DistilBERTSymptomModel)
        mock_sym.is_available.return_value = True
        mock_sym.infer.return_value = SymptomInferenceResult(
            model="distilbert_symptom",
            available=True,
            predictions=[ConditionPrediction(condition="Nipah Virus Infection", confidence=0.90)],
        )
        with patch.object(model_manager, "get_symptom_model", return_value=mock_sym):
            resp = self.client.post("/analyse/fuse", json={"symptoms": "Severe fever and acute disorientation"})
            self.assertEqual(resp.json()["urgency"], "emergency")
            self.assertEqual(resp.json()["urgency_score"], 1.0)
            self.assertIn("Infectious Disease Specialist / Neurologist", resp.json()["recommended_specialist"])

    def test_unknown_condition_fallback(self):
        """Unmapped condition safely falls back to General Physician."""
        mock_sym = MagicMock(spec=DistilBERTSymptomModel)
        mock_sym.is_available.return_value = True
        mock_sym.infer.return_value = SymptomInferenceResult(
            model="distilbert_symptom",
            available=True,
            predictions=[ConditionPrediction(condition="Unusual Syndromic Manifestation XYZ", confidence=0.55)],
        )
        with patch.object(model_manager, "get_symptom_model", return_value=mock_sym):
            resp = self.client.post("/analyse/fuse", json={"symptoms": "Unusual non-specific symptoms"})
            self.assertEqual(resp.json()["recommended_specialist"], "General Physician")


class TestExistingSymptomEndpoint(BaseFusionTestCase):
    """Verifies that existing /analyse/symptoms endpoint remains 100% preserved and operational."""

    def test_existing_symptom_endpoint_preserved(self):
        """POST /analyse/symptoms works with rule-based fallback and produces valid clinical triage."""
        resp = self.client.post(
            "/analyse/symptoms",
            json={"symptoms": "fever and joint pain with rash"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["analysis_type"], "symptom_analysis")
        self.assertTrue(len(data["possible_conditions"]) > 0)
        self.assertEqual(data["urgency_hint"], "moderate")
        self.assertIn("General Physician", data["specialist_hint"])
        self.assertIn("This is not a medical diagnosis", data["disclaimer"])


if __name__ == "__main__":
    unittest.main()
