"""Integration tests for the HTTP API via FastAPI's TestClient."""

from __future__ import annotations


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_calculate_returns_breakdown(client):
    resp = client.post(
        "/api/calculate",
        json={
            "transport": {"car_km_per_week": 100, "car_fuel": "petrol"},
            "diet": "vegan",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["breakdown_kg"]) == {"transport", "home", "diet", "consumption"}
    assert body["total_annual_kg"] > 0
    assert "comparison" in body


def test_calculate_rejects_negative_values(client):
    resp = client.post("/api/calculate", json={"transport": {"car_km_per_week": -5}})
    assert resp.status_code == 422  # Pydantic validation rejects out-of-bounds input


def test_calculate_rejects_unknown_enum(client):
    resp = client.post("/api/calculate", json={"diet": "carnivore_supreme"})
    assert resp.status_code == 422


def test_insights_uses_rules_when_gemini_disabled(client):
    resp = client.post("/api/insights", json={"diet": "heavy_meat"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "rules"
    assert len(body["recommendations"]) >= 1


def test_entries_roundtrip(client):
    calc = client.post("/api/calculate", json={"diet": "vegan"}).json()
    device_id = "device-test-1234"
    create = client.post(
        "/api/entries",
        json={"device_id": device_id, "input": {"diet": "vegan"}, "result": calc},
    )
    assert create.status_code == 201

    listing = client.get(f"/api/entries/{device_id}")
    assert listing.status_code == 200
    entries = listing.json()
    assert len(entries) == 1
    assert entries[0]["device_id"] == device_id


def test_entries_rejects_bad_device_id(client):
    resp = client.get("/api/entries/short")  # fails min_length / pattern
    assert resp.status_code == 422


def test_unknown_api_route_returns_json_404(client):
    resp = client.get("/api/does-not-exist")
    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/json")


def test_security_headers_present(client):
    resp = client.get("/api/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in resp.headers
