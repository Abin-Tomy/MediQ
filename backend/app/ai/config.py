"""
AI Model Configuration.

Centralises all AI-related configuration so that model paths and runtime
options are never scattered or hardcoded across the codebase.

Environment variables (all optional — safe defaults apply):

    MEDIQ_AI_MODELS_DIR        Base directory that holds all model sub-folders.
                               Default: ./models  (relative to backend root)

    MEDIQ_SYMPTOM_MODEL_PATH   Full path to the DistilBERT symptom model artefacts.
                               Default: <MEDIQ_AI_MODELS_DIR>/symptom

    MEDIQ_IMAGE_MODEL_PATH     Full path to the YOLOv8 .pt weights file or directory.
                               Default: <MEDIQ_AI_MODELS_DIR>/image

    MEDIQ_REPORT_MODEL_PATH    Full path to the T5-small report model artefacts.
                               Default: <MEDIQ_AI_MODELS_DIR>/report

    MEDIQ_AI_DEVICE            Inference device: 'cpu' or 'cuda'.
                               Default: cpu  (backend runs on Windows/CPU during development)

Configuration is loaded once at import time.  The module re-uses the same
.env loading mechanism already established in app/database.py — python-dotenv
is available in the venv so we delegate to it here for consistency.
"""

import os
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Ensure .env is loaded (python-dotenv is already a project dependency)
# ─────────────────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv as _load_dotenv

    _BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    _env_path = os.path.join(_BASE_DIR, ".env")
    _load_dotenv(_env_path, override=False)  # never overwrite already-set env vars
except ImportError:
    # python-dotenv unavailable — rely on env vars already in the environment
    _BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    logger.debug("python-dotenv not available; reading environment variables as-is.")


# ─────────────────────────────────────────────────────────────────────────────
# Base models directory
# ─────────────────────────────────────────────────────────────────────────────

# Resolve the backend root (one level above app/)
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

_DEFAULT_MODELS_DIR = os.path.join(_BACKEND_ROOT, "models")
AI_MODELS_DIR: str = os.getenv("MEDIQ_AI_MODELS_DIR", _DEFAULT_MODELS_DIR)

# ─────────────────────────────────────────────────────────────────────────────
# Per-model path resolution
# ─────────────────────────────────────────────────────────────────────────────

SYMPTOM_MODEL_PATH: str = os.getenv(
    "MEDIQ_SYMPTOM_MODEL_PATH",
    os.path.join(AI_MODELS_DIR, "symptom"),
)

IMAGE_MODEL_PATH: str = os.getenv(
    "MEDIQ_IMAGE_MODEL_PATH",
    os.path.join(AI_MODELS_DIR, "image"),
)

SKIN_MODEL_PATH: str = os.getenv(
    "MEDIQ_SKIN_MODEL_PATH",
    os.path.join(IMAGE_MODEL_PATH, "skin"),
)

EYE_MODEL_PATH: str = os.getenv(
    "MEDIQ_EYE_MODEL_PATH",
    os.path.join(IMAGE_MODEL_PATH, "eye"),
)

REPORT_MODEL_PATH: str = os.getenv(
    "MEDIQ_REPORT_MODEL_PATH",
    os.path.join(AI_MODELS_DIR, "report"),
)

# ─────────────────────────────────────────────────────────────────────────────
# Inference device
# ─────────────────────────────────────────────────────────────────────────────

AI_DEVICE: str = os.getenv("MEDIQ_AI_DEVICE", "cpu").lower()
if AI_DEVICE not in ("cpu", "cuda"):
    logger.warning(
        "MEDIQ_AI_DEVICE='%s' is not recognised; falling back to 'cpu'.", AI_DEVICE
    )
    AI_DEVICE = "cpu"
