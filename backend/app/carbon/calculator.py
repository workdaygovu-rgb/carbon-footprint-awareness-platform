"""The carbon footprint calculation engine.

Pure, deterministic, side-effect-free functions: the same input always yields the
same output, with no I/O. This makes the engine trivially unit-testable and lets
the API compute results without touching the database or any external service.

All quantities are normalised to **annual kg CO2e** before being summed.
"""

from __future__ import annotations

from app.carbon import factors
from app.models import (
    CarbonInput,
    CategoryKey,
    Comparison,
    ConsumptionInput,
    FootprintResult,
    HomeInput,
    TransportInput,
)

# Display rounding precision for totals and ratios.
_KG_TO_TONNES = 1000
_ROUND_TONNES = 3
_ROUND_RATIO = 3
_ROUND_KG = 2


def _transport_annual_kg(t: TransportInput) -> float:
    car = t.car_km_per_week * factors.WEEKS_PER_YEAR * factors.CAR_FACTORS_PER_KM[t.car_fuel]
    transit = t.public_transit_km_per_week * factors.WEEKS_PER_YEAR * factors.PUBLIC_TRANSIT_PER_KM
    flights = (
        t.short_haul_flights_per_year
        * factors.SHORT_HAUL_TRIP_KM
        * factors.FLIGHT_SHORT_HAUL_PER_KM
        + t.long_haul_flights_per_year * factors.LONG_HAUL_TRIP_KM * factors.FLIGHT_LONG_HAUL_PER_KM
    )
    return car + transit + flights


def _home_annual_kg(h: HomeInput) -> float:
    electricity = (
        h.electricity_kwh_per_month * factors.MONTHS_PER_YEAR * factors.ELECTRICITY_PER_KWH
    )
    gas = h.natural_gas_kwh_per_month * factors.MONTHS_PER_YEAR * factors.NATURAL_GAS_PER_KWH
    # Household energy is shared, so attribute a per-person share.
    return (electricity + gas) / h.household_size


def _consumption_annual_kg(c: ConsumptionInput) -> float:
    goods = c.goods_spend_usd_per_month * factors.MONTHS_PER_YEAR * factors.GOODS_PER_USD_MONTHLY
    waste = c.waste_kg_per_week * factors.WEEKS_PER_YEAR * factors.WASTE_PER_KG
    return goods + waste


def calculate_footprint(data: CarbonInput) -> FootprintResult:
    """Compute the annual carbon footprint breakdown for a set of inputs."""
    breakdown: dict[CategoryKey, float] = {
        "transport": round(_transport_annual_kg(data.transport), _ROUND_KG),
        "home": round(_home_annual_kg(data.home), _ROUND_KG),
        "diet": round(factors.DIET_ANNUAL_KG[data.diet], _ROUND_KG),
        "consumption": round(_consumption_annual_kg(data.consumption), _ROUND_KG),
    }
    total = round(sum(breakdown.values()), _ROUND_KG)

    comparison = Comparison(
        global_average_annual_kg=factors.GLOBAL_AVG_ANNUAL_KG,
        sustainable_target_annual_kg=factors.SUSTAINABLE_TARGET_ANNUAL_KG,
        ratio_to_global_average=round(total / factors.GLOBAL_AVG_ANNUAL_KG, _ROUND_RATIO),
        ratio_to_sustainable_target=round(total / factors.SUSTAINABLE_TARGET_ANNUAL_KG, _ROUND_RATIO),
    )

    return FootprintResult(
        breakdown_kg=breakdown,
        total_annual_kg=total,
        total_annual_tonnes=round(total / _KG_TO_TONNES, _ROUND_TONNES),
        comparison=comparison,
    )
