"""Tests for results/imports endpoints."""
import io


def test_list_imports_empty(auth_client):
    resp = auth_client.get("/api/results/imports")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "data" in body
    assert "pagination" in body


def test_list_imports_after_upload(auth_client, sample_excel_bytes):
    auth_client.post(
        "/api/results/upload",
        files={"file": ("r.xlsx", io.BytesIO(sample_excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"academic_year": "2025-26", "semester": "6", "department": "CSE"},
    )
    resp = auth_client.get("/api/results/imports")
    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] >= 1


def test_reconciliation_endpoint(auth_client, sample_excel_bytes):
    auth_client.post(
        "/api/results/upload",
        files={"file": ("r.xlsx", io.BytesIO(sample_excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"academic_year": "2025-26", "semester": "6", "department": "CSE"},
    )
    resp = auth_client.get("/api/results/reconciliation", params={"academic_year": "2025-26", "semester": 6})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "reconciliation_score" in data


def test_data_quality_endpoint(auth_client, sample_excel_bytes):
    auth_client.post(
        "/api/results/upload",
        files={"file": ("r.xlsx", io.BytesIO(sample_excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"academic_year": "2025-26", "semester": "6", "department": "CSE"},
    )
    resp = auth_client.get("/api/results/data-quality", params={"academic_year": "2025-26", "semester": 6})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "overall_score" in data
    assert "total_records" in data
