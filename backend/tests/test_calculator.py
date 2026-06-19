"""Unit tests for the pure carbon calculation engine."""

from __future__ import annotations

import math

import pytest
from app.carbon import factors
from app.carbon.calculator import calculate_footprint
from app.models import (
    CarbonInput,
    ConsumptionInput,
    HomeInput,
    TransportInput,
)


def test_empty_input_produces_diet_only_footprint():
    # With no transport/home/consumption, the footprint is just the diet baseline.
    result = calculate_footprint(CarbonInput(diet=factors.DietType.VEGAN))

    assert result.breakdown_kg["transport"] == 0.0
    assert result.breakdown_kg["home"] == 0.0
    assert result.breakdown_kg["consumption"] == 0.0
    assert result.breakdown_kg["diet"] == pytest.approx(
        factors.DIET_ANNUAL_KG[factors.DietType.VEGAN]
    )
    assert result.total_annual_kg == pytest.approx(factors.DIET_ANNUAL_KG[factors.DietType.VEGAN])


def test_car_emissions_annualized_by_fuel():
    result = calculate_footprint(
        CarbonInput(
            transport=TransportInput(car_km_per_week=100, car_fuel=factors.CarFuel.PETROL),
            diet=factors.DietType.VEGAN,
        )
    )
    expected_car = 100 * 52 * factors.CAR_FACTORS_PER_KM[factors.CarFuel.PETROL]
    assert result.breakdown_kg["transport"] == pytest.approx(expected_car)


def test_electric_car_lower_than_petrol():
    petrol = calculate_footprint(
        CarbonInput(transport=TransportInput(car_km_per_week=100, car_fuel=factors.CarFuel.PETROL))
    )
    electric = calculate_footprint(
        CarbonInput(
            transport=TransportInput(car_km_per_week=100, car_fuel=factors.CarFuel.ELECTRIC)
        )
    )
    assert electric.breakdown_kg["transport"] < petrol.breakdown_kg["transport"]


def test_flights_use_representative_distances():
    result = calculate_footprint(
        CarbonInput(
            transport=TransportInput(short_haul_flights_per_year=2, long_haul_flights_per_year=1),
            diet=factors.DietType.VEGAN,
        )
    )
    expected = (
        2 * factors.SHORT_HAUL_TRIP_KM * factors.FLIGHT_SHORT_HAUL_PER_KM
        + 1 * factors.LONG_HAUL_TRIP_KM * factors.FLIGHT_LONG_HAUL_PER_KM
    )
    assert result.breakdown_kg["transport"] == pytest.approx(expected)


def test_home_energy_split_by_household_size():
    solo = calculate_footprint(
        CarbonInput(home=HomeInput(electricity_kwh_per_month=300, household_size=1))
    )
    shared = calculate_footprint(
        CarbonInput(home=HomeInput(electricity_kwh_per_month=300, household_size=3))
    )
    # Shared household splits the same energy three ways → one-third per person.
    assert shared.breakdown_kg["home"] == pytest.approx(solo.breakdown_kg["home"] / 3)


def test_consumption_combines_goods_and_waste():
    result = calculate_footprint(
        CarbonInput(
            consumption=ConsumptionInput(goods_spend_usd_per_month=200, waste_kg_per_week=5),
            diet=factors.DietType.VEGAN,
        )
    )
    expected = 200 * 12 * factors.GOODS_PER_USD_MONTHLY + 5 * 52 * factors.WASTE_PER_KG
    assert result.breakdown_kg["consumption"] == pytest.approx(expected)


def test_total_is_sum_of_breakdown_and_tonnes_consistent():
    result = calculate_footprint(
        CarbonInput(
            transport=TransportInput(car_km_per_week=100),
            home=HomeInput(electricity_kwh_per_month=300),
            consumption=ConsumptionInput(goods_spend_usd_per_month=100),
        )
    )
    assert result.total_annual_kg == pytest.approx(sum(result.breakdown_kg.values()))
    assert result.total_annual_tonnes == pytest.approx(result.total_annual_kg / 1000)


def test_comparison_ratios():
    result = calculate_footprint(CarbonInput(diet=factors.DietType.VEGAN))
    c = result.comparison
    assert c.ratio_to_global_average == pytest.approx(
        round(result.total_annual_kg / factors.GLOBAL_AVG_ANNUAL_KG, 3)
    )
    assert c.ratio_to_sustainable_target == pytest.approx(
        round(result.total_annual_kg / factors.SUSTAINABLE_TARGET_ANNUAL_KG, 3)
    )


def test_values_are_rounded_and_finite():
    result = calculate_footprint(CarbonInput(transport=TransportInput(car_km_per_week=123.456)))
    for v in result.breakdown_kg.values():
        assert math.isfinite(v)
        assert round(v, 2) == v
