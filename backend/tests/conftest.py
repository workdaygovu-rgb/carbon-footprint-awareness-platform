"""Shared pytest fixtures.

Forces the offline-friendly configuration (no Gemini, in-memory store) so the
full API surface can be exercised without any GCP credentials.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("USE_GEMINI", "false")
    monkeypatch.setenv("USE_FIRESTORE", "false")

    # Settings, repository, and prompt config are cached singletons — clear
    # them so the env overrides above take effect for this test.
    from app import config, deps
    from app.insights import gemini

    config.get_settings.cache_clear()
    deps.get_repository.cache_clear()
    gemini._load_prompt_config.cache_clear()
    gemini._get_gemini_client.cache_clear()
    gemini._INSIGHTS_CACHE.clear()

    from app.main import create_app
    from fastapi.testclient import TestClient

    with TestClient(create_app()) as test_client:
        yield test_client

    config.get_settings.cache_clear()
    deps.get_repository.cache_clear()
    gemini._load_prompt_config.cache_clear()
    gemini._get_gemini_client.cache_clear()
    gemini._INSIGHTS_CACHE.clear()
