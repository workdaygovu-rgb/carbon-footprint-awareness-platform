"""Tests for the Gemini insights service, validation, caching, and fallback.

v1.3: Migrated from asyncio.get_event_loop().run_until_complete() to
pytest-asyncio @pytest.mark.asyncio to eliminate DeprecationWarning on
Python 3.12+ and future-proof the test suite.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from app.carbon.calculator import calculate_footprint
from app.config import Settings
from app.insights import gemini
from app.models import CarbonInput, InsightsResponse, Recommendation


def _ctx():
    data = CarbonInput()
    return data, calculate_footprint(data)


def _fake_genai_client(response_text: str):
    """A stand-in for ``genai.Client`` returning a canned model response."""

    class _FakeClient:
        def __init__(self, **_kwargs):
            self.models = SimpleNamespace(
                generate_content=lambda **_kw: SimpleNamespace(text=response_text)
            )

    return _FakeClient


@pytest.mark.asyncio
async def test_disabled_gemini_uses_rules():
    data, result = _ctx()
    resp = await gemini.generate_insights(data, result, Settings(use_gemini=False))
    assert resp.source == "rules"


@pytest.mark.asyncio
async def test_gemini_failure_falls_back_to_rules(monkeypatch):
    def boom(*_args, **_kwargs):
        raise RuntimeError("vertex unavailable")

    monkeypatch.setattr(gemini, "_call_gemini", boom)
    data, result = _ctx()
    resp = await gemini.generate_insights(data, result, Settings(use_gemini=True))
    assert resp.source == "rules"
    assert resp.recommendations  # fallback still produces advice


def test_build_prompt_mentions_totals_and_context():
    data, result = _ctx()
    prompt = gemini._build_prompt(data, result)
    assert str(result.total_annual_kg) in prompt
    assert data.diet.value in prompt
    assert "advice" in prompt


def test_call_gemini_parses_structured_response(monkeypatch):
    payload = {
        "summary": "You are close to the sustainable target.",
        "recommendations": [
            {"category": "diet", "action": "More plants", "estimated_annual_savings_kg": 400.123},
            {"category": "home", "action": "LED bulbs", "estimated_annual_savings_kg": 120.0},
        ],
    }
    monkeypatch.setattr("google.genai.Client", _fake_genai_client(json.dumps(payload)))
    data, result = _ctx()
    resp = gemini._call_gemini(data, result, Settings())
    assert resp.source == "gemini"
    assert resp.summary == payload["summary"]
    assert len(resp.recommendations) == 2
    # Savings are rounded to 2 decimal places for display.
    assert resp.recommendations[0].estimated_annual_savings_kg == 400.12


@pytest.mark.asyncio
async def test_empty_gemini_recommendations_fall_back_to_rules(monkeypatch):
    payload = {"summary": "ok", "recommendations": []}
    monkeypatch.setattr("google.genai.Client", _fake_genai_client(json.dumps(payload)))
    data, result = _ctx()
    resp = await gemini.generate_insights(data, result, Settings(use_gemini=True))
    assert resp.source == "rules"


@pytest.mark.asyncio
async def test_malformed_gemini_json_falls_back_to_rules(monkeypatch):
    monkeypatch.setattr("google.genai.Client", _fake_genai_client("not valid json {"))
    data, result = _ctx()
    resp = await gemini.generate_insights(data, result, Settings(use_gemini=True))
    assert resp.source == "rules"
    assert resp.recommendations


@pytest.mark.asyncio
async def test_gemini_success_path(monkeypatch):
    canned = InsightsResponse(
        summary="Great progress!",
        recommendations=[
            Recommendation(
                category="diet", action="Eat more plants", estimated_annual_savings_kg=200.0
            )
        ],
        source="gemini",
    )
    monkeypatch.setattr(gemini, "_call_gemini", lambda *_a, **_k: canned)
    data, result = _ctx()
    resp = await gemini.generate_insights(data, result, Settings(use_gemini=True))
    assert resp.source in ("gemini", "cache")
    assert resp.summary == "Great progress!"


# ── Validation tests (Improvement 4) ──────────────────────────────────


def test_validate_rejects_savings_exceeding_total():
    payload = {
        "summary": "Fine.",
        "recommendations": [
            {"category": "transport", "action": "Walk", "estimated_annual_savings_kg": 99999},
        ],
    }
    with pytest.raises(ValueError, match="exceed total"):
        gemini._validate_gemini_response(payload, total_annual_kg=2500.0)


def test_validate_rejects_negative_savings():
    payload = {
        "summary": "Fine.",
        "recommendations": [
            {"category": "diet", "action": "Less meat", "estimated_annual_savings_kg": -100},
        ],
    }
    with pytest.raises(ValueError, match="Non-positive"):
        gemini._validate_gemini_response(payload, total_annual_kg=5000.0)


def test_validate_rejects_unknown_category():
    payload = {
        "summary": "Fine.",
        "recommendations": [
            {
                "category": "crypto_mining",
                "action": "Stop mining",
                "estimated_annual_savings_kg": 100,
            },
        ],
    }
    with pytest.raises(ValueError, match="Unknown category"):
        gemini._validate_gemini_response(payload, total_annual_kg=5000.0)


def test_validate_rejects_oversized_summary():
    payload = {
        "summary": "x" * 1500,
        "recommendations": [
            {"category": "diet", "action": "Veg", "estimated_annual_savings_kg": 100},
        ],
    }
    with pytest.raises(ValueError, match="too long"):
        gemini._validate_gemini_response(payload, total_annual_kg=5000.0)


def test_validate_accepts_valid_response():
    payload = {
        "summary": "Good work!",
        "recommendations": [
            {"category": "transport", "action": "Cycle more", "estimated_annual_savings_kg": 200},
            {"category": "diet", "action": "Less meat", "estimated_annual_savings_kg": 300},
        ],
    }
    # Should not raise.
    gemini._validate_gemini_response(payload, total_annual_kg=5000.0)


@pytest.mark.asyncio
async def test_validation_failure_triggers_rules_fallback(monkeypatch):
    """If Gemini returns out-of-bounds savings, the fallback engine is used."""
    bad_payload = {
        "summary": "ok",
        "recommendations": [
            {"category": "transport", "action": "Fly less", "estimated_annual_savings_kg": 999999},
        ],
    }
    monkeypatch.setattr("google.genai.Client", _fake_genai_client(json.dumps(bad_payload)))
    data, result = _ctx()
    resp = await gemini.generate_insights(data, result, Settings(use_gemini=True))
    assert resp.source == "rules"  # fell back because validation failed


# ── Client caching test (Improvement 3) ───────────────────────────────


def test_gemini_client_is_cached(monkeypatch):
    """The Gemini client should be created once and reused."""
    call_count = 0

    class _CountingClient:
        def __init__(self, **_kwargs):
            nonlocal call_count
            call_count += 1

    monkeypatch.setattr("google.genai.Client", _CountingClient)
    gemini._get_gemini_client("project-a", "us-central1")
    gemini._get_gemini_client("project-a", "us-central1")

    assert call_count == 1  # only one instantiation despite two calls


# ── Response cache tests (Improvement 2, v1.3) ────────────────────────


@pytest.mark.asyncio
async def test_insights_cache_returns_cached_result():
    """Second call with identical input should return source='cache'."""
    data, result = _ctx()
    settings = Settings(use_gemini=False)

    resp1 = await gemini.generate_insights(data, result, settings)
    assert resp1.source == "rules"

    resp2 = await gemini.generate_insights(data, result, settings)
    assert resp2.source == "cache"
    assert resp2.summary == resp1.summary
    assert resp2.recommendations == resp1.recommendations


@pytest.mark.asyncio
async def test_insights_cache_miss_on_different_input():
    """Different input data should not hit the cache."""
    data1 = CarbonInput()
    result1 = calculate_footprint(data1)
    settings = Settings(use_gemini=False)

    await gemini.generate_insights(data1, result1, settings)

    # Different input (heavy meat diet).
    from app.carbon.factors import DietType

    data2 = CarbonInput(diet=DietType.HEAVY_MEAT)
    result2 = calculate_footprint(data2)

    resp2 = await gemini.generate_insights(data2, result2, settings)
    assert resp2.source == "rules"  # cache miss -> fresh rules call
