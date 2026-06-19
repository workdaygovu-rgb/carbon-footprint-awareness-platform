"""Tests for prompt versioning and evaluation against representative profiles."""

from __future__ import annotations

import pytest
from app.carbon import factors
from app.carbon.calculator import calculate_footprint
from app.insights.gemini import _load_prompt_config
from app.insights.rules import generate_rule_based_insights
from app.models import CarbonInput, ConsumptionInput, HomeInput, TransportInput


@pytest.fixture(autouse=True)
def _clear_prompt_cache():
    _load_prompt_config.cache_clear()
    yield
    _load_prompt_config.cache_clear()


def test_v1_prompt_config_loads_and_has_required_fields():
    config = _load_prompt_config("v1")
    assert "system_instruction" in config
    assert "response_schema" in config
    assert "temperature" in config
    assert "max_output_tokens" in config
    assert isinstance(config["system_instruction"], str)
    assert len(config["system_instruction"]) > 20


def test_missing_prompt_version_returns_empty_dict_gracefully():
    config = _load_prompt_config("nonexistent_version_99")
    assert config == {}


def test_prompt_config_is_cached():
    first = _load_prompt_config("v1")
    second = _load_prompt_config("v1")
    assert first is second  # same object — cached


# ── Rule-engine evaluation against representative profiles ────────────
# Ensures the insight engine's recommendations target each user's largest
# emission sources, validating the logic the prompt is also expected to follow.


def test_profile_heavy_driver_gets_transport_first():
    """A user who drives 500 km/week in a petrol car: transport dominates."""
    data = CarbonInput(
        transport=TransportInput(car_km_per_week=500, car_fuel=factors.CarFuel.PETROL),
        diet=factors.DietType.VEGAN,
    )
    result = calculate_footprint(data)
    insights = generate_rule_based_insights(data, result)
    assert insights.recommendations[0].category == "transport"


def test_profile_heavy_consumer_gets_consumption_addressed():
    """A user with high goods spending and waste: consumption must appear."""
    data = CarbonInput(
        consumption=ConsumptionInput(goods_spend_usd_per_month=1500, waste_kg_per_week=30),
        diet=factors.DietType.VEGAN,
    )
    result = calculate_footprint(data)
    insights = generate_rule_based_insights(data, result)
    categories = [r.category for r in insights.recommendations]
    assert "consumption" in categories


def test_profile_energy_heavy_household_gets_home_addressed():
    """A user with high electricity and gas: home energy must appear early."""
    data = CarbonInput(
        home=HomeInput(electricity_kwh_per_month=900, natural_gas_kwh_per_month=600),
        diet=factors.DietType.VEGAN,
    )
    result = calculate_footprint(data)
    insights = generate_rule_based_insights(data, result)
    categories = [r.category for r in insights.recommendations]
    assert "home" in categories
