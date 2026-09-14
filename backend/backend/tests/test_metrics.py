"""Tests for pure calculation functions and MetricsService."""
import io

import pytest

from app.utils.calculations import (
    compute_pass_percentage,
    compute_weighted_gpa,
    bucket_marks,
)


# ---- Pure calculation tests ----

def test_pass_percentage_calculation():
    result = compute_pass_percentage(45, 60)
    assert result == pytest.approx(75.0, rel=1e-3)


def test_pass_percentage_with_absent():
    # 40 pass out of 50 eligible (10 absent, not in eligible)
    result = compute_pass_percentage(40, 50)
    assert result == pytest.approx(80.0, rel=1e-3)


def test_pass_percentage_zero_eligible():
    result = compute_pass_percentage(0, 0)
    assert result == 0.0


def test_failure_rate():
    pct = compute_pass_percentage(15, 50)
    assert pct == pytest.approx(30.0, rel=1e-3)


def test_grade_distribution(auth_client, sample_excel_bytes):
    """Upload data then check grade distribution endpoint."""
    import io
    auth_client.post(
        "/api/results/upload",
        files={"file": ("r.xlsx", io.BytesIO(sample_excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"academic_year": "2025-26", "semester": "6", "department": "CSE"},
    )
    resp = auth_client.get("/api/analysis/grades", params={"academic_year": "2025-26", "semester": 6})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)


def test_gpa_calculation():
    gpa = compute_weighted_gpa([8.0, 9.0, 10.0], [4.0, 4.0, 4.0])
    assert gpa == pytest.approx(9.0, rel=1e-3)


def test_weighted_gpa():
    gpa = compute_weighted_gpa([10.0, 4.0], [3.0, 1.0])
    # (10*3 + 4*1) / 4 = 34/4 = 8.5
    assert gpa == pytest.approx(8.5, rel=1e-3)


def test_bucket_marks_basic():
    marks = [5, 15, 25, 35, 45, 55, 65, 75, 85, 95]
    buckets = bucket_marks(marks)
    totals = sum(b["count"] for b in buckets)
    assert totals == len(marks)


def test_bucket_marks_empty():
    assert bucket_marks([]) == []
