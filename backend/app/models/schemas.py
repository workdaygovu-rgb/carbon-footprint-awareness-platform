"""Pydantic schemas — the validated contract for the API.

These models double as input validation (rejecting nonsensical values before any
computation) and as the OpenAPI documentation surface. Keeping every field
bounded is a deliberate security measure: clients cannot submit unbounded or
negative quantities.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.carbon.factors import CarFuel, DietType

# Valid emission-category keys used across the API and rule engine.
CategoryKey = Literal["transport", "home", "diet", "consumption"]

# Generous-but-finite upper bounds keep inputs sane without rejecting real users.
_MAX_KM_WEEK = 20_000.0
_MAX_KWH_MONTH = 100_000.0
_MAX_FLIGHTS = 200
_MAX_USD_MONTH = 1_000_000.0
_MAX_WASTE_WEEK = 1_000.0


class TransportInput(BaseModel):
    """Weekly travel habits plus yearly flight counts."""

    car_km_per_week: float = Field(
        0, ge=0, le=_MAX_KM_WEEK, description="Car kilometres driven per week."
    )
    car_fuel: CarFuel = Field(
        default=CarFuel.PETROL, description="Car drivetrain used for emission-factor lookup."
    )
    public_transit_km_per_week: float = Field(
        0, ge=0, le=_MAX_KM_WEEK, description="Public-transit kilometres travelled per week."
    )
    short_haul_flights_per_year: int = Field(
        0, ge=0, le=_MAX_FLIGHTS, description="Short-haul (≈1,100 km) one-way flights per year."
    )
    long_haul_flights_per_year: int = Field(
        0, ge=0, le=_MAX_FLIGHTS, description="Long-haul (≈6,500 km) one-way flights per year."
    )


class HomeInput(BaseModel):
    """Monthly household energy use, shared across the household size."""

    electricity_kwh_per_month: float = Field(
        0, ge=0, le=_MAX_KWH_MONTH, description="Monthly household electricity consumption in kWh."
    )
    natural_gas_kwh_per_month: float = Field(
        0, ge=0, le=_MAX_KWH_MONTH, description="Monthly household natural-gas consumption in kWh."
    )
    household_size: int = Field(
        1, ge=1, le=50, description="Number of people sharing the home energy footprint."
    )


class ConsumptionInput(BaseModel):
    """Consumer goods spending and landfill waste."""

    goods_spend_usd_per_month: float = Field(
        0, ge=0, le=_MAX_USD_MONTH, description="Monthly spending on goods in US dollars."
    )
    waste_kg_per_week: float = Field(
        0, ge=0, le=_MAX_WASTE_WEEK, description="Landfill waste disposed of per week in kilograms."
    )


class CarbonInput(BaseModel):
    """Full set of lifestyle inputs for a footprint estimate."""

    transport: TransportInput = Field(
        default_factory=TransportInput, description="Weekly transport habits and yearly flights."
    )
    home: HomeInput = Field(
        default_factory=HomeInput, description="Monthly home energy use and household size."
    )
    diet: DietType = Field(
        default=DietType.MEDIUM_MEAT, description="Diet profile for the food-emission estimate."
    )
    consumption: ConsumptionInput = Field(
        default_factory=ConsumptionInput,
        description="Monthly goods spending and weekly landfill waste.",
    )


class Comparison(BaseModel):
    """The user's total in context: global average and sustainable target."""

    global_average_annual_kg: float = Field(
        ..., description="Global per-capita annual footprint benchmark in kg CO2e."
    )
    sustainable_target_annual_kg: float = Field(
        ..., description="Paris-aligned sustainable annual target in kg CO2e."
    )
    ratio_to_global_average: float = Field(
        ..., description="User total divided by the global average."
    )
    ratio_to_sustainable_target: float = Field(
        ..., description="User total divided by the sustainable target."
    )


class FootprintResult(BaseModel):
    """Per-category annual breakdown (kg CO2e) plus totals and context."""

    breakdown_kg: dict[CategoryKey, float] = Field(
        ..., description="Annual emissions per known category in kg CO2e."
    )
    total_annual_kg: float = Field(..., description="Total annual footprint in kg CO2e.")
    total_annual_tonnes: float = Field(..., description="Total annual footprint in metric tonnes.")
    comparison: Comparison = Field(..., description="Benchmark context for the result.")


# ── Insights ──────────────────────────────────────────────────────────
class Recommendation(BaseModel):
    """One concrete reduction action with a quantified annual saving."""

    category: CategoryKey = Field(..., description="Emission category this recommendation targets.")
    action: str = Field(..., description="Concrete, user-facing reduction action.")
    estimated_annual_savings_kg: float = Field(
        ..., ge=0, description="Estimated annual saving in kg CO2e if the action is taken."
    )


class InsightsResponse(BaseModel):
    """Personalized advice: a summary plus ranked recommendations."""

    summary: str = Field(..., description="Short, encouraging summary of the footprint.")
    recommendations: list[Recommendation] = Field(
        ..., description="Ranked reduction actions with quantified savings."
    )
    source: Literal["gemini", "rules", "cache"] = Field(
        ..., description="Which engine produced this response."
    )


# ── Entries (tracking history) ────────────────────────────────────────
class EntryCreate(BaseModel):
    """Request payload to save a footprint snapshot for an anonymous device."""

    device_id: str = Field(
        ...,
        min_length=8,
        max_length=128,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Anonymous device identifier stored in localStorage.",
    )
    input: CarbonInput = Field(..., description="Inputs used to generate the footprint.")
    result: FootprintResult = Field(..., description="Calculated footprint result to store.")


class Entry(EntryCreate):
    """A stored footprint snapshot, as returned by the API."""

    id: str = Field(..., description="Unique entry identifier (UUID4, hex encoded).")
    created_at: str = Field(..., description="Entry creation timestamp in ISO-8601 UTC.")
