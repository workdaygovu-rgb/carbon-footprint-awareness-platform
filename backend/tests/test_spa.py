"""Tests for production SPA static serving and client-side-routing fallback."""

from __future__ import annotations

import pytest


@pytest.fixture
def spa_client(tmp_path, monkeypatch):
    """A client whose app serves a built SPA from a temporary static dir."""
    static = tmp_path / "static"
    (static / "assets").mkdir(parents=True)
    (static / "index.html").write_text("<!doctype html><h1>SPA index</h1>", encoding="utf-8")
    (static / "assets" / "app.js").write_text("console.log('app')", encoding="utf-8")
    (static / "robots.txt").write_text("User-agent: *", encoding="utf-8")

    monkeypatch.setenv("USE_GEMINI", "false")
    monkeypatch.setenv("USE_FIRESTORE", "false")

    from app import config, deps, main

    config.get_settings.cache_clear()
    deps.get_repository.cache_clear()
    monkeypatch.setattr(main, "_STATIC_DIR", static)

    from fastapi.testclient import TestClient

    with TestClient(main.create_app()) as client:
        yield client

    config.get_settings.cache_clear()
    deps.get_repository.cache_clear()


def test_root_serves_spa_index(spa_client):
    resp = spa_client.get("/")
    assert resp.status_code == 200
    assert "SPA index" in resp.text


def test_unknown_client_route_falls_back_to_index(spa_client):
    resp = spa_client.get("/history/some/client/route")
    assert resp.status_code == 200
    assert "SPA index" in resp.text


def test_real_static_file_is_served_directly(spa_client):
    resp = spa_client.get("/robots.txt")
    assert resp.status_code == 200
    assert resp.text.startswith("User-agent")


def test_unknown_api_route_stays_json_404(spa_client):
    resp = spa_client.get("/api/definitely-not-a-route")
    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/json")
    assert resp.json() == {"detail": "Not Found"}


def test_api_still_works_with_spa_mounted(spa_client):
    resp = spa_client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
