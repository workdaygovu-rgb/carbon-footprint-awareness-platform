"""Tests for the deterministic rule-based insights engine."""

from __future__ import annotations

from app.carbon import factors
from app.carbon.calculator import calculate_footprint
from app.insights.rules import generate_rule_based_insights
from app.models import CarbonInput, ConsumptionInput, HomeInput, TransportInput


def _insights_for(data: CarbonInput):
    return generate_rule_based_insights(data, calculate_footprint(data))


def test_source_is_rules_and_has_summary():
    data = CarbonInput()
    resp = _insights_for(data)
    assert resp.source == "rules"
    assert resp.summary
    assert len(resp.recommendations) >= 1


def test_recommendations_target_largest_category_first():
    # Heavy car use makes transport dominate; it should be addressed first.
    data = CarbonInput(
        transport=TransportInput(car_km_per_week=500, car_fuel=factors.CarFuel.PETROL),
        diet=factors.DietType.VEGAN,
    )
    resp = _insights_for(data)
    assert resp.recommendations[0].category == "transport"


def test_high_meat_diet_yields_diet_recommendation():
    data = CarbonInput(diet=factors.DietType.HEAVY_MEAT)
    resp = _insights_for(data)
    categories = {r.category for r in resp.recommendations}
    assert "diet" in categories


def test_savings_are_positive_and_finite():
    data = CarbonInput(
        transport=TransportInput(car_km_per_week=300, short_haul_flights_per_year=4),
        diet=factors.DietType.HEAVY_MEAT,
    )
    resp = _insights_for(data)
    for rec in resp.recommendations:
        assert rec.estimated_annual_savings_kg > 0
        assert rec.action


def test_already_green_user_still_gets_constructive_summary():
    data = CarbonInput(diet=factors.DietType.VEGAN)
    resp = _insights_for(data)
    # Even a low footprint should produce a non-empty, encouraging response.
    assert resp.summary
    assert isinstance(resp.recommendations, list)


def test_frequent_flyer_gets_flight_recommendation():
    # Flights dominate transport → the advice should target aviation, not the car.
    data = CarbonInput(
        transport=TransportInput(long_haul_flights_per_year=6, car_km_per_week=10),
        diet=factors.DietType.VEGAN,
    )
    resp = _insights_for(data)
    transport_recs = [r for r in resp.recommendations if r.category == "transport"]
    assert transport_recs and "flight" in transport_recs[0].action.lower()


def test_transit_only_traveller_gets_generic_transport_advice():
    # No car, no flights — but transit emissions still exist, so advice is offered.
    data = CarbonInput(
        transport=TransportInput(public_transit_km_per_week=200),
        diet=factors.DietType.VEGAN,
    )
    resp = _insights_for(data)
    categories = {r.category for r in resp.recommendations}
    assert "transport" in categories


def test_home_energy_user_gets_home_recommendation():
    data = CarbonInput(
        home=HomeInput(electricity_kwh_per_month=500, natural_gas_kwh_per_month=300),
        diet=factors.DietType.VEGAN,
    )
    resp = _insights_for(data)
    categories = {r.category for r in resp.recommendations}
    assert "home" in categories


def test_heavy_consumer_gets_consumption_recommendation():
    data = CarbonInput(
        consumption=ConsumptionInput(goods_spend_usd_per_month=800, waste_kg_per_week=20),
        diet=factors.DietType.VEGAN,
    )
    resp = _insights_for(data)
    categories = {r.category for r in resp.recommendations}
    assert "consumption" in categories


def test_diet_recommendation_skipped_when_no_saving(monkeypatch):
    # Defensive branch: if two adjacent diet rungs ever had equal footprints,
    # a zero-saving recommendation must be suppressed rather than shown.
    flat = dict.fromkeys(factors.DIET_ANNUAL_KG, 1500.0)
    monkeypatch.setattr(factors, "DIET_ANNUAL_KG", flat)
    data = CarbonInput(diet=factors.DietType.HEAVY_MEAT)
    resp = _insights_for(data)
    assert all(r.category != "diet" for r in resp.recommendations)
