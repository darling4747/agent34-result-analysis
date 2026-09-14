"""Tests for institutional system configuration endpoints (/api/config)."""

import pytest


def test_get_config(auth_client):
    resp = auth_client.get("/api/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    
    # Verify expected config keys
    assert "assessment" in data
    assert data["assessment"]["internal_max"] == 30
    assert data["assessment"]["external_max"] == 70
    assert data["assessment"]["total_max"] == 100
    
    assert "intervention_weights" in data
    assert "ai_provider" in data
    assert "database" in data
    assert "integrations" in data


def test_update_config_weights(auth_client):
    new_weights = {
        "failure_weight": 0.50,
        "historical_weight": 0.20,
        "section_weight": 0.20,
        "correlation_weight": 0.10,
    }
    resp = auth_client.put("/api/config", json={"weights": new_weights})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["intervention_weights"]["failure_weight"] == 0.50

    # Reset back to default
    default_weights = {
        "failure_weight": 0.40,
        "historical_weight": 0.30,
        "section_weight": 0.20,
        "correlation_weight": 0.10,
    }
    auth_client.put("/api/config", json={"weights": default_weights})


def test_update_config_invalid_weights(auth_client):
    # Weights sum to 0.80 instead of 1.00
    invalid_weights = {
        "failure_weight": 0.50,
        "historical_weight": 0.10,
        "section_weight": 0.10,
        "correlation_weight": 0.10,
    }
    resp = auth_client.put("/api/config", json={"weights": invalid_weights})
    assert resp.status_code == 400
    body = resp.json()
    assert "must sum to 1.0" in body["detail"]
