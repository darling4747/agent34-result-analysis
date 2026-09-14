"""Tests for InterventionService."""
import io

from app.utils.calculations import compute_priority_score, grade_to_priority_level


def _upload(auth_client, excel_bytes, academic_year="2025-26", semester=6):
    auth_client.post(
        "/api/results/upload",
        files={"file": ("r.xlsx", io.BytesIO(excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"academic_year": academic_year, "semester": str(semester), "department": "CSE"},
    )


def test_interventions_endpoint(auth_client, sample_excel_with_failures):
    _upload(auth_client, sample_excel_with_failures)
    resp = auth_client.get("/api/analysis/interventions", params={"academic_year": "2025-26", "semester": 6})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)


def test_interventions_priority_levels(auth_client, sample_excel_with_failures):
    _upload(auth_client, sample_excel_with_failures)
    resp = auth_client.get("/api/analysis/interventions", params={"academic_year": "2025-26", "semester": 6})
    data = resp.json()["data"]
    valid_levels = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
    for item in data:
        assert item["priority_level"] in valid_levels


def test_interventions_sorted_by_score(auth_client, sample_excel_with_failures):
    _upload(auth_client, sample_excel_with_failures)
    resp = auth_client.get("/api/analysis/interventions", params={"academic_year": "2025-26", "semester": 6})
    data = resp.json()["data"]
    if len(data) > 1:
        scores = [d["priority_score"] for d in data]
        assert scores == sorted(scores, reverse=True)


def test_intervention_summary(auth_client, sample_excel_with_failures):
    _upload(auth_client, sample_excel_with_failures)
    resp = auth_client.get("/api/analysis/interventions/summary", params={"academic_year": "2025-26", "semester": 6})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "total_courses_flagged" in data
    assert "weights_used" in data


def test_priority_score_formula():
    score = compute_priority_score(
        failure_rate=50.0,
        historical_deviation=-15.0,
        section_deviation=10.0,
        ie_anomaly_score=0.5,
        weights={"failure": 0.4, "historical": 0.3, "section": 0.2, "correlation": 0.1},
    )
    assert 0 <= score <= 100


def test_grade_to_priority_level():
    assert grade_to_priority_level(80) == "CRITICAL"
    assert grade_to_priority_level(60) == "HIGH"
    assert grade_to_priority_level(40) == "MEDIUM"
    assert grade_to_priority_level(20) == "LOW"
