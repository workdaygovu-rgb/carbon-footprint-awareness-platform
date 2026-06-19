"""Tests for the dependency-injection wiring (repository selection)."""

from __future__ import annotations

import pytest
from app import config, deps
from app.repository.firestore_repo import FirestoreEntryRepository
from app.repository.memory_repo import InMemoryEntryRepository


@pytest.fixture(autouse=True)
def _fresh_caches():
    """Settings and repository are cached singletons; isolate each test."""
    config.get_settings.cache_clear()
    deps.get_repository.cache_clear()
    yield
    config.get_settings.cache_clear()
    deps.get_repository.cache_clear()


def test_in_memory_repository_selected_when_firestore_disabled(monkeypatch):
    monkeypatch.setenv("USE_FIRESTORE", "false")
    repo = deps.get_repository()
    assert isinstance(repo, InMemoryEntryRepository)


def test_repository_is_cached_singleton(monkeypatch):
    monkeypatch.setenv("USE_FIRESTORE", "false")
    assert deps.get_repository() is deps.get_repository()


def test_firestore_repository_selected_when_enabled(monkeypatch):
    class _FakeClient:
        def __init__(self, project=None):
            self.project = project

    monkeypatch.setenv("USE_FIRESTORE", "true")
    monkeypatch.setattr("google.cloud.firestore.Client", _FakeClient)
    repo = deps.get_repository()
    assert isinstance(repo, FirestoreEntryRepository)
