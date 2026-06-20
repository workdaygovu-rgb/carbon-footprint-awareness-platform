"""Footprint calculation and insights endpoints."""

from fastapi import APIRouter, Depends, Request, Body
from fastapi.responses import JSONResponse

from app.carbon.calculator import calculate_footprint
from app.config import Settings, get_settings
from app.insights.gemini import generate_insights
from app.rate_limit import limiter
from app.models import CarbonInput, FootprintResult, InsightsResponse

router = APIRouter(prefix="/api", tags=["footprint"])


@router.post("/calculate", response_model=FootprintResult)
def calculate(payload: CarbonInput) -> FootprintResult:
    """Compute the annual carbon footprint breakdown for the supplied inputs.

    The carbon engine is pure and deterministic — identical inputs always
    produce identical outputs, with no side effects or external calls.
    Input validation is handled by Pydantic before this function runs.
    """
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

    The insights engine degrades gracefully: if Gemini is unreachable or
    returns invalid output, the deterministic rule-based fallback guarantees
    the user always receives actionable, quantified advice.
    """
    try:
        result = calculate_footprint(payload)
        return await generate_insights(payload, result, settings)
    except ValueError as exc:
        return JSONResponse(
            {"detail": f"Invalid input: {exc}"}, status_code=400
        )
    except Exception as exc:
        return JSONResponse(
            {"detail": "Insight generation temporarily unavailable. Please try again."},
            status_code=503,
        )
