"""Tests for HistoricalService."""
import io
import pytest


def _upload(auth_client, excel_bytes, academic_year, semester=6):
    auth_client.post(
        "/api/results/upload",
        files={"file": ("r.xlsx", io.BytesIO(excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"academic_year": academic_year, "semester": str(semester), "department": "CSE"},
    )


def test_historical_endpoint_returns_list(auth_client, sample_excel_bytes):
    _upload(auth_client, sample_excel_bytes, "2025-26")
    resp = auth_client.get("/api/analysis/historical", params={"academic_year": "2025-26", "semester": 6})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)


def test_historical_has_required_fields(auth_client, sample_excel_bytes):
    _upload(auth_client, sample_excel_bytes, "2025-26")
    resp = auth_client.get("/api/analysis/historical", params={"academic_year": "2025-26", "semester": 6})
    data = resp.json()["data"]
    if data:
        item = data[0]
        assert "course_code" in item
        assert "current_pass_rate" in item
        assert "trend" in item


def test_historical_trend_values(auth_client, sample_excel_bytes):
    _upload(auth_client, sample_excel_bytes, "2025-26")
    resp = auth_client.get("/api/analysis/historical", params={"academic_year": "2025-26", "semester": 6})
    data = resp.json()["data"]
    valid_trends = {"IMPROVING", "DECLINING", "STABLE", "UNKNOWN"}
    for item in data:
        assert item["trend"] in valid_trends


def test_historical_empty_filters(auth_client):
    resp = auth_client.get("/api/analysis/historical", params={"academic_year": "9999-00"})
    assert resp.status_code == 200
    assert resp.json()["data"] == []
