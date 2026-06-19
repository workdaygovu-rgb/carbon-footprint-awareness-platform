"""Tests for environment-driven configuration."""

from __future__ import annotations

from app.config import Settings


def test_origins_list_parses_and_strips_whitespace():
    settings = Settings(allowed_origins=" http://a.example , http://b.example ,")
    assert settings.origins_list == ["http://a.example", "http://b.example"]


def test_origins_list_ignores_empty_segments():
    settings = Settings(allowed_origins=",,")
    assert settings.origins_list == []


def test_defaults_are_well_typed():
    settings = Settings()
    assert isinstance(settings.project_id, str) and settings.project_id
    assert isinstance(settings.region, str) and settings.region
    assert isinstance(settings.use_gemini, bool)
    assert isinstance(settings.use_firestore, bool)
    assert isinstance(settings.origins_list, list)
