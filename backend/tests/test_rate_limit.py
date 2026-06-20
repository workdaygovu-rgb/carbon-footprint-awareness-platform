"""Tests for rate limiting and request body size guards."""

from __future__ import annotations

from app.rate_limit import limiter


def test_insights_rate_limit_returns_429_after_burst(client):
    """The /api/insights endpoint is capped at 10 requests/minute per IP."""
    limiter.reset()
    payload = {"diet": "vegan"}
    for i in range(10):
        resp = client.post("/api/insights", json=payload)
        assert resp.status_code == 200, f"Request {i + 1} should succeed"

    resp = client.post("/api/insights", json=payload)
    assert resp.status_code == 429
    assert "rate limit" in resp.json()["detail"].lower()


def test_oversized_body_returns_413(client):
    """POST requests larger than 64 KB are rejected before JSON parsing."""
    # Build a payload that exceeds 64 KB via a long string value.
    huge = {"diet": "vegan", "extra": "x" * 70_000}
    resp = client.post(
        "/api/calculate",
        json=huge,
        headers={"content-length": str(len(str(huge)))},
    )
    # The body-size middleware checks Content-Length; if the header is present
    # and exceeds the limit, the request is rejected with 413.
    assert resp.status_code == 413
    assert "too large" in resp.json()["detail"].lower()


def test_calculate_not_rate_limited(client):
    """The /api/calculate endpoint has no rate limit — it's pure computation."""
    payload = {"diet": "vegan"}
    for _ in range(15):
        resp = client.post("/api/calculate", json=payload)
        assert resp.status_code == 200
