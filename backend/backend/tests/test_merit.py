"""Tests for MeritService."""
import io
import pytest


def _upload(auth_client, excel_bytes, academic_year="2025-26", semester=6):
    auth_client.post(
        "/api/results/upload",
        files={"file": ("r.xlsx", io.BytesIO(excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"academic_year": academic_year, "semester": str(semester), "department": "CSE"},
    )


def test_merit_list_returns_ranked(auth_client, sample_excel_bytes):
    _upload(auth_client, sample_excel_bytes)
    resp = auth_client.get("/api/analysis/merit-list", params={"academic_year": "2025-26", "semester": 6})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)
    if len(data) > 0:
        assert "rank" in data[0]
        assert "sgpa" in data[0]
        assert data[0]["rank"] == 1


def test_merit_list_rank_order(auth_client, sample_excel_bytes):
    _upload(auth_client, sample_excel_bytes)
    resp = auth_client.get("/api/analysis/merit-list", params={"academic_year": "2025-26", "semester": 6})
    data = resp.json()["data"]
    # Ranks should be non-decreasing
    ranks = [d["rank"] for d in data]
    assert ranks == sorted(ranks)


def test_merit_list_status_labels(auth_client, sample_excel_bytes):
    _upload(auth_client, sample_excel_bytes)
    resp = auth_client.get("/api/analysis/merit-list", params={"academic_year": "2025-26", "semester": 6})
    data = resp.json()["data"]
    valid_statuses = {"DISTINCTION", "FIRST_CLASS", "SECOND_CLASS", "PASS"}
    for item in data:
        assert item["status"] in valid_statuses


def test_merit_list_empty_filters(auth_client):
    resp = auth_client.get("/api/analysis/merit-list", params={"academic_year": "9999-00"})
    assert resp.status_code == 200
    assert resp.json()["data"] == []
