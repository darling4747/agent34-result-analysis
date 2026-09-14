"""Tests for health and root endpoints."""


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == 34
    assert data["status"] == "running"


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "1.0.0"
    assert data["agent"] == 34


def test_health_db_connected(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["database"] == "connected"
    assert data["status"] == "healthy"
