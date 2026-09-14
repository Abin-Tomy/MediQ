"""
MediQ FastAPI Application Forwarder.

Provides compatibility for invocations targeting `app.main:app`
by re-exporting the central FastAPI application from `main.py`.
"""

from main import app

__all__ = ["app"]
