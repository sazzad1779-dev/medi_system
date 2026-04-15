"""
API Routes for Health Checks.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import httpx

from app.dependencies import get_db
from app.config import settings
from app.models.schemas import HealthCheckResponse

router = APIRouter(prefix="/health", tags=["health"])

@router.get("", response_model=HealthCheckResponse)
async def health_check():
    """
    Basic liveness probe.
    """
    return HealthCheckResponse(
        status="ok",
        timestamp=datetime.now()
    )

@router.get("/ready", response_model=HealthCheckResponse)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe checking DB and VLM service.
    """
    details = {}
    
    # Check DB
    try:
        await db.execute(text("SELECT 1"))
        details["database"] = "reachable"
    except Exception:
        details["database"] = "unreachable"

    # Check VLM Service
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.VLLM_BASE_URL.replace('/v1', '/health')}", timeout=2.0)
            details["vlm_service"] = "ok" if resp.status_code == 200 else "unhealthy"
    except Exception:
        details["vlm_service"] = "unreachable"

    all_ok = all(v in ["reachable", "ok"] for v in details.values())
    
    return HealthCheckResponse(
        status="ok" if all_ok else "degraded",
        timestamp=datetime.now(),
        details=details
    )
