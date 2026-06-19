"""Emission factors for carbon footprint estimation.

All factors are expressed in **kilograms of CO2-equivalent (kg CO2e)** and are
documented with their source so the numbers are auditable rather than magic
constants. Figures are rounded, representative averages intended for awareness
and education — not regulatory accounting.

Primary sources:
  * UK DEFRA / DESNZ 2023 Greenhouse Gas Conversion Factors
    https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2023
  * US EPA — Greenhouse Gas Emissions from a Typical Passenger Vehicle
    https://www.epa.gov/greenvehicles
  * IPCC AR6 and Our World in Data — food & energy emissions
    https://ourworldindata.org/food-choice-vs-eating-local

The platform reports estimates in metric tonnes/kg CO2e per year unless noted.
"""

from __future__ import annotations

from enum import Enum

# ─────────────────────── Time conversions ───────────────────────────
# Used to normalise weekly/monthly inputs to annual figures.
WEEKS_PER_YEAR: int = 52
MONTHS_PER_YEAR: int = 12

# ──────────────────────────── Transport ─────────────────────────────
# Per-kilometre factors for personal travel.


class CarFuel(str, Enum):
    """Car drivetrain type, which determines the per-km emission factor."""

    PETROL = "petrol"
    DIESEL = "diesel"
    HYBRID = "hybrid"
    ELECTRIC = "electric"


# kg CO2e per km driven (single occupant). Source: DEFRA 2023 average car.
CAR_FACTORS_PER_KM: dict[CarFuel, float] = {
    CarFuel.PETROL: 0.170,
    CarFuel.DIESEL: 0.171,
    CarFuel.HYBRID: 0.120,
    CarFuel.ELECTRIC: 0.047,  # includes grid generation emissions
}

# kg CO2e per passenger-km. Source: DEFRA 2023 (bus/rail averages).
PUBLIC_TRANSIT_PER_KM: float = 0.060

# kg CO2e per passenger-km for flights (incl. radiative forcing uplift).
# Short-haul is more carbon-intensive per km than long-haul. Source: DEFRA 2023.
FLIGHT_SHORT_HAUL_PER_KM: float = 0.158
FLIGHT_LONG_HAUL_PER_KM: float = 0.150
# Representative one-way distances used to convert "number of flights" → km.
SHORT_HAUL_TRIP_KM: float = 1100.0
LONG_HAUL_TRIP_KM: float = 6500.0

# ──────────────────────────── Home energy ───────────────────────────
# kg CO2e per kWh of grid electricity (global-ish average; grids vary widely).
# Source: IEA / Our World in Data ~2022 world average.
ELECTRICITY_PER_KWH: float = 0.450
# kg CO2e per kWh of natural gas (heating). Source: DEFRA 2023.
NATURAL_GAS_PER_KWH: float = 0.183

# ──────────────────────────────── Diet ──────────────────────────────
# Annual kg CO2e attributable to diet type (food production footprint).
# Source: Scarborough et al. 2014 / Our World in Data dietary footprints.


class DietType(str, Enum):
    """Diet profile, mapped to an annual food-production footprint."""

    HEAVY_MEAT = "heavy_meat"
    MEDIUM_MEAT = "medium_meat"
    LOW_MEAT = "low_meat"
    PESCATARIAN = "pescatarian"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"


DIET_ANNUAL_KG: dict[DietType, float] = {
    DietType.HEAVY_MEAT: 3300.0,
    DietType.MEDIUM_MEAT: 2500.0,
    DietType.LOW_MEAT: 1900.0,
    DietType.PESCATARIAN: 1700.0,
    DietType.VEGETARIAN: 1500.0,
    DietType.VEGAN: 1050.0,
}

# ───────────────────────── Goods, services & waste ──────────────────
# kg CO2e per USD spent on general consumer goods (rough EEIO-style intensity).
# Source: derived from EXIOBASE / consumer-spend emission intensity studies.
GOODS_PER_USD_MONTHLY: float = 0.40
# kg CO2e per kg of landfilled waste (methane-weighted). Source: EPA WARM.
WASTE_PER_KG: float = 0.580

# ──────────────────────────── References ────────────────────────────
# Annual per-capita footprints for context/comparison (tonnes CO2e/yr → kg).
# Source: Our World in Data, 2022 per-capita consumption emissions.
GLOBAL_AVG_ANNUAL_KG: float = 4800.0
SUSTAINABLE_TARGET_ANNUAL_KG: float = 2000.0  # ~Paris-aligned 2030 per-capita
