"""
MediQ - AI Healthcare Assistant Backend Application.

Entry point that configures the FastAPI application, CORS middleware,
and mounts all feature routers.

Stage 3 additions
-----------------
* FastAPI lifespan context manager initialises the AI ModelManager once at
  startup so model weights are loaded a single time, never per-request.
* GET /ai/status route mounted at prefix /ai.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.analysis import router as analysis_router
from app.routes.doctor import router as doctor_router
from app.routes.appointment import router as appointment_router
from app.routes.medication import router as medication_router
from app.routes.record import router as record_router
from app.routes.ai_status import router as ai_status_router

from app.ai import model_manager


# ─────────────────────────────────────────────────────────────────────────────
# Application Lifespan
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Startup: initialises the AI ModelManager (attempts to load model weights).
             If no weights exist the server still starts successfully.
    Shutdown: reserved for future cleanup (e.g. releasing GPU memory).
    """
    # Startup — safe even if no model artefacts are present
    model_manager.initialize()
    yield
    # Shutdown — nothing to clean up in Step 1


# Initialize FastAPI application with API metadata
app = FastAPI(
    title="MediQ - AI Healthcare Assistant",
    description="Backend API for AI-powered healthcare assistant with role-based access control",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS) for Flutter/web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount feature routers
app.include_router(auth_router, prefix="/auth")
app.include_router(admin_router, prefix="/admin")
app.include_router(analysis_router, prefix="/analyse")
app.include_router(doctor_router, prefix="/doctors")
app.include_router(appointment_router, prefix="/appointments")
app.include_router(medication_router, prefix="/medications")
app.include_router(record_router, prefix="/records")
app.include_router(ai_status_router, prefix="/ai")


# ─────────────────────────────────────────────────────────────────────────────
# Health & Status Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get(
    "/",
    tags=["Health"],
    status_code=status.HTTP_200_OK,
    summary="Root service info",
)
def read_root() -> dict[str, str]:
    """Root status endpoint returning service description and operational state."""
    return {
        "message": "MediQ AI Healthcare Assistant Backend Running",
        "version": "1.0.0",
        "status": "healthy",
    }


@app.get(
    "/health",
    tags=["Health"],
    status_code=status.HTTP_200_OK,
    summary="Health check probe",
)
def health_check() -> dict[str, str]:
    """Lightweight health check endpoint for monitoring probes and load balancers."""
    return {"status": "ok"}