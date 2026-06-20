"""Footprint calculation and insights endpoints."""

from fastapi import APIRouter, Body, Depends, Request

from app.carbon.calculator import calculate_footprint
from app.config import Settings, get_settings
from app.insights.gemini import generate_insights
from app.models import CarbonInput, FootprintResult, InsightsResponse
from app.rate_limit import limiter

router = APIRouter(prefix="/api", tags=["footprint"])


@router.post("/calculate", response_model=FootprintResult)
def calculate(payload: CarbonInput) -> FootprintResult:
    """Compute the annual carbon footprint breakdown for the supplied inputs."""
    return calculate_footprint(payload)


@router.post("/insights", response_model=InsightsResponse)
@limiter.limit("10/minute")
async def insights(
    request: Request,
    payload: CarbonInput = Body(...),
    settings: Settings = Depends(get_settings),
) -> InsightsResponse:
    """Return personalized reduction advice (Gemini, with rule-based fallback).

    Rate-limited to 10 requests/minute per IP to protect Vertex AI quota and
    billing. The ``request`` parameter is required by SlowAPI's key function.
    """
    result = calculate_footprint(payload)
    return await generate_insights(payload, result, settings)
