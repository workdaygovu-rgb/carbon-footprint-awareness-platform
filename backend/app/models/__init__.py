"""Pydantic schemas — the validated contract for the API.

Re-exports all models from schemas.py so existing ``from app.models import ...``
imports continue to work without changes. The schemas module is kept in its own
file for organisation; this package __init__ provides a flat public API.
"""

from app.models.schemas import (
    CarbonInput,
    CategoryKey,
    Comparison,
    ConsumptionInput,
    Entry,
    EntryCreate,
    FootprintResult,
    HomeInput,
    InsightsResponse,
    Recommendation,
    TransportInput,
)

__all__ = [
    "CarbonInput",
    "CategoryKey",
    "Comparison",
    "ConsumptionInput",
    "Entry",
    "EntryCreate",
    "FootprintResult",
    "HomeInput",
    "InsightsResponse",
    "Recommendation",
    "TransportInput",
]
