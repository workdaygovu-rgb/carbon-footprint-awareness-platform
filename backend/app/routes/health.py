"""Health and readiness endpoint (used by Cloud Run and uptime checks)."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__

router = APIRouter(tags=["system"])


@router.get("/api/health")
def health() -> dict[str, str]:
    """Report service liveness and the running application version."""
    return {"status": "ok", "version": __version__}
