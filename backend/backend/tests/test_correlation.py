"""Tests for CorrelationService."""
import io
import pytest

from app.utils.calculations import interpret_correlation, compute_pass_percentage


def _upload(auth_client, excel_bytes, academic_year="2025-26", semester=6):
    auth_client.post(
        "/api/results/upload",
        files={"file": ("r.xlsx", io.BytesIO(excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"academic_year": academic_year, "semester": str(semester), "department": "CSE"},
    )


def test_correlation_endpoint_returns_list(auth_client, sample_excel_bytes):
    _upload(auth_client, sample_excel_bytes)
    resp = auth_client.get("/api/analysis/correlation", params={"academic_year": "2025-26", "semester": 6})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)


def test_correlation_has_required_fields(auth_client, sample_excel_bytes):
    _upload(auth_client, sample_excel_bytes)
    resp = auth_client.get("/api/analysis/correlation", params={"academic_year": "2025-26", "semester": 6})
    data = resp.json()["data"]
    if data:
        item = data[0]
        assert "course_code" in item
        assert "sample_size" in item
        assert "interpretation" in item


def test_interpret_correlation_strong_positive():
    assert interpret_correlation(0.85, 10) == "STRONG_POSITIVE"


def test_interpret_correlation_insufficient_data():
    assert interpret_correlation(0.9, 3) == "INSUFFICIENT_DATA"


def test_interpret_correlation_negative():
    assert interpret_correlation(-0.75, 10) == "STRONG_NEGATIVE"


def test_correlation_empty_filters(auth_client):
    resp = auth_client.get("/api/analysis/correlation", params={"academic_year": "9999-00"})
    assert resp.status_code == 200
    assert resp.json()["data"] == []
