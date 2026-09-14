"""Tests for analysis endpoints."""
import io


def _upload(auth_client, excel_bytes, academic_year="2025-26", semester=6):
    auth_client.post(
        "/api/results/upload",
        files={"file": ("r.xlsx", io.BytesIO(excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"academic_year": academic_year, "semester": str(semester), "department": "CSE"},
    )


def test_summary_endpoint(auth_client, sample_excel_bytes):
    _upload(auth_client, sample_excel_bytes)
    resp = auth_client.get("/api/analysis/summary", params={"academic_year": "2025-26", "semester": 6})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "total_students" in data
    assert "pass_percentage" in data
    assert data["total_results"] >= 3


def test_summary_empty(auth_client):
    resp = auth_client.get("/api/analysis/summary", params={"academic_year": "9999-00"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_results"] == 0


def test_sections_endpoint(auth_client, sample_excel_bytes):
    _upload(auth_client, sample_excel_bytes)
    resp = auth_client.get("/api/analysis/sections", params={"academic_year": "2025-26", "semester": 6})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)
    if data:
        assert "section" in data[0]
        assert "pass_rate" in data[0]


def test_backlogs_endpoint(auth_client, sample_excel_with_failures):
    _upload(auth_client, sample_excel_with_failures)
    resp = auth_client.get("/api/analysis/backlogs", params={"academic_year": "2025-26", "semester": 6})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)
    for item in data:
        assert item["backlog_count"] >= 1


def test_attainment_input_endpoint(auth_client, sample_excel_bytes):
    _upload(auth_client, sample_excel_bytes)
    resp = auth_client.get("/api/analysis/attainment-input", params={"academic_year": "2025-26", "semester": 6})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)
    if data:
        assert "course_code" in data[0]
        assert "roll_number" in data[0]


def test_dashboard_summary(auth_client, sample_excel_bytes):
    _upload(auth_client, sample_excel_bytes)
    resp = auth_client.get("/api/dashboard/summary", params={"academic_year": "2025-26", "semester": 6})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "summary" in data
    assert "grade_distribution" in data
