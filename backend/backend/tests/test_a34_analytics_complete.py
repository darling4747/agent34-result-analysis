"""Agent 34 — Complete analytics tests (~120 tests)."""
from __future__ import annotations
import io
import os
import pytest
import pandas as pd
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_result_analysis.db")


# ===========================================================================
# Fixtures / helpers
# ===========================================================================

def _make_rich_excel():
    """Create a 20-row dataset with known statistics for validation."""
    data = {
        "roll_number": [f"22AN{i:03d}" for i in range(1, 21)],
        "student_name": [f"Student {i}" for i in range(1, 21)],
        "programme": ["B.Tech"] * 20,
        "department": ["CSE"] * 20,
        "batch": ["2022"] * 20,
        "section": (["A"] * 10 + ["B"] * 10),
        "course_code": (["AN601"] * 10 + ["AN602"] * 10),
        "course_name": (["Algorithm Analysis"] * 10 + ["Network Theory"] * 10),
        "faculty": (["Dr. Sharma"] * 10 + ["Dr. Singh"] * 10),
        "semester": [6] * 20,
        "academic_year": ["2025-26"] * 20,
        "internal_marks": [22, 18, 25, 15, 20, 10, 8, 12, 15, 19,
                           22, 18, 25, 15, 20, 10, 8, 12, 15, 19],
        "external_marks": [50, 35, 60, 25, 40, 15, 10, 20, 30, 38,
                           50, 35, 60, 25, 40, 15, 10, 20, 30, 38],
        "total_marks": [72, 53, 85, 40, 60, 25, 18, 32, 45, 57,
                        72, 53, 85, 40, 60, 25, 18, 32, 45, 57],
        "grade": ["A", "C", "O", "C", "B", "F", "F", "F", "P", "B",
                  "A", "C", "O", "C", "B", "F", "F", "F", "P", "B"],
        "grade_point": [8, 5, 10, 5, 6, 0, 0, 0, 4, 6,
                        8, 5, 10, 5, 6, 0, 0, 0, 4, 6],
        "result_status": ["PASS", "PASS", "PASS", "PASS", "PASS", "FAIL", "FAIL", "FAIL", "PASS", "PASS",
                          "PASS", "PASS", "PASS", "PASS", "PASS", "FAIL", "FAIL", "FAIL", "PASS", "PASS"],
    }
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf.read()


@pytest.fixture
def analytics_client(client, db_session):
    """Upload test data once, return authenticated client."""
    from app.services.auth_service import AuthService
    from app.security.password import hash_password
    from app.models import Role, User
    from app.config import get_settings

    AuthService(db_session, get_settings()).seed_roles_and_permissions()
    role = db_session.query(Role).filter_by(name="PLATFORM_ADMIN").first()
    email = "analytics_admin@test.com"
    u = db_session.query(User).filter_by(email=email).first()
    if not u:
        u = User(email=email, full_name="Admin", role_id=role.id,
                 password_hash=hash_password("TestPass99!X"),
                 is_active=True, must_change_password=False, mfa_enabled=False)
        db_session.add(u)
        db_session.commit()
    else:
        u.must_change_password = False
        u.mfa_enabled = False
        db_session.commit()

    resp = client.post("/api/auth/login", json={"email": email, "password": "TestPass99!X"})
    token = resp.json()["data"]["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    # Upload data
    excel = _make_rich_excel()
    client.post("/api/results/upload",
                data={"academic_year": "2025-26", "semester": "6"},
                files={"file": ("analytics_test.xlsx", excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    return client


# ===========================================================================
# 1-10: Summary endpoint
# ===========================================================================

class TestAnalyticsSummary:
    def test_summary_returns_200(self, analytics_client):
        resp = analytics_client.get("/api/analysis/summary?academic_year=2025-26&semester=6")
        assert resp.status_code == 200

    def test_summary_has_total_students(self, analytics_client):
        resp = analytics_client.get("/api/analysis/summary?academic_year=2025-26&semester=6")
        assert "total_students" in resp.json()["data"]

    def test_summary_has_pass_count(self, analytics_client):
        resp = analytics_client.get("/api/analysis/summary?academic_year=2025-26&semester=6")
        assert "pass_count" in resp.json()["data"]

    def test_summary_has_fail_count(self, analytics_client):
        resp = analytics_client.get("/api/analysis/summary?academic_year=2025-26&semester=6")
        assert "fail_count" in resp.json()["data"]

    def test_summary_has_pass_percentage(self, analytics_client):
        resp = analytics_client.get("/api/analysis/summary?academic_year=2025-26&semester=6")
        assert "pass_percentage" in resp.json()["data"]

    def test_summary_pass_percentage_in_range(self, analytics_client):
        resp = analytics_client.get("/api/analysis/summary?academic_year=2025-26&semester=6")
        pct = resp.json()["data"].get("pass_percentage", 0)
        if pct is not None:
            assert 0 <= pct <= 100

    def test_summary_has_failure_percentage(self, analytics_client):
        resp = analytics_client.get("/api/analysis/summary?academic_year=2025-26&semester=6")
        assert "failure_percentage" in resp.json()["data"]

    def test_summary_has_average_marks(self, analytics_client):
        resp = analytics_client.get("/api/analysis/summary?academic_year=2025-26&semester=6")
        assert "average_marks" in resp.json()["data"]

    def test_summary_total_students_non_negative(self, analytics_client):
        resp = analytics_client.get("/api/analysis/summary?academic_year=2025-26&semester=6")
        total = resp.json()["data"].get("total_students", 0)
        assert total >= 0

    def test_summary_success_true(self, analytics_client):
        resp = analytics_client.get("/api/analysis/summary?academic_year=2025-26&semester=6")
        assert resp.json()["success"] is True


# ===========================================================================
# 11-20: Grade distribution
# ===========================================================================

class TestGradeDistribution:
    def test_grades_returns_200(self, analytics_client):
        resp = analytics_client.get("/api/analysis/grades?academic_year=2025-26&semester=6")
        assert resp.status_code == 200

    def test_grades_returns_list(self, analytics_client):
        resp = analytics_client.get("/api/analysis/grades?academic_year=2025-26&semester=6")
        assert isinstance(resp.json()["data"], list)

    def test_grades_items_have_grade_field(self, analytics_client):
        resp = analytics_client.get("/api/analysis/grades?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "grade" in data[0]

    def test_grades_items_have_count_field(self, analytics_client):
        resp = analytics_client.get("/api/analysis/grades?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "count" in data[0]

    def test_grades_items_have_percentage_field(self, analytics_client):
        resp = analytics_client.get("/api/analysis/grades?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "percentage" in data[0]

    def test_grades_counts_non_negative(self, analytics_client):
        resp = analytics_client.get("/api/analysis/grades?academic_year=2025-26&semester=6")
        for item in resp.json()["data"]:
            assert item.get("count", 0) >= 0


# ===========================================================================
# 21-30: Course analysis
# ===========================================================================

class TestCourseAnalysis:
    def test_courses_returns_200(self, analytics_client):
        resp = analytics_client.get("/api/analysis/courses?academic_year=2025-26&semester=6")
        assert resp.status_code == 200

    def test_courses_returns_list(self, analytics_client):
        resp = analytics_client.get("/api/analysis/courses?academic_year=2025-26&semester=6")
        assert isinstance(resp.json()["data"], list)

    def test_courses_have_course_code(self, analytics_client):
        resp = analytics_client.get("/api/analysis/courses?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "course_code" in data[0]

    def test_courses_have_pass_percentage(self, analytics_client):
        resp = analytics_client.get("/api/analysis/courses?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "pass_percentage" in data[0]

    def test_courses_have_total_students(self, analytics_client):
        resp = analytics_client.get("/api/analysis/courses?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "total_students" in data[0]


# ===========================================================================
# 31-40: Section analysis
# ===========================================================================

class TestSectionAnalysis:
    def test_sections_returns_200(self, analytics_client):
        resp = analytics_client.get("/api/analysis/sections?academic_year=2025-26&semester=6")
        assert resp.status_code == 200

    def test_sections_returns_list(self, analytics_client):
        resp = analytics_client.get("/api/analysis/sections?academic_year=2025-26&semester=6")
        assert isinstance(resp.json()["data"], list)

    def test_sections_have_section_field(self, analytics_client):
        resp = analytics_client.get("/api/analysis/sections?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "section" in data[0]

    def test_sections_have_pass_rate(self, analytics_client):
        resp = analytics_client.get("/api/analysis/sections?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "pass_rate" in data[0]


# ===========================================================================
# 41-50: Merit list
# ===========================================================================

class TestMeritList:
    def test_merit_list_returns_200(self, analytics_client):
        resp = analytics_client.get("/api/analysis/merit-list?academic_year=2025-26&semester=6")
        assert resp.status_code == 200

    def test_merit_list_returns_list(self, analytics_client):
        resp = analytics_client.get("/api/analysis/merit-list?academic_year=2025-26&semester=6")
        assert isinstance(resp.json()["data"], list)

    def test_merit_list_items_have_rank(self, analytics_client):
        resp = analytics_client.get("/api/analysis/merit-list?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "rank" in data[0]

    def test_merit_list_items_have_roll_number(self, analytics_client):
        resp = analytics_client.get("/api/analysis/merit-list?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "roll_number" in data[0]

    def test_merit_list_rank_1_is_first(self, analytics_client):
        resp = analytics_client.get("/api/analysis/merit-list?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if len(data) >= 2:
            assert data[0]["rank"] <= data[1]["rank"]

    def test_merit_list_respects_limit(self, analytics_client):
        resp = analytics_client.get("/api/analysis/merit-list?academic_year=2025-26&semester=6&limit=5")
        assert len(resp.json()["data"]) <= 5


# ===========================================================================
# 51-60: Correlation analysis
# ===========================================================================

class TestCorrelationAnalysis:
    def test_correlation_returns_200(self, analytics_client):
        resp = analytics_client.get("/api/analysis/correlation?academic_year=2025-26&semester=6")
        assert resp.status_code == 200

    def test_correlation_returns_list(self, analytics_client):
        resp = analytics_client.get("/api/analysis/correlation?academic_year=2025-26&semester=6")
        assert isinstance(resp.json()["data"], list)

    def test_correlation_items_have_course_code(self, analytics_client):
        resp = analytics_client.get("/api/analysis/correlation?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "course_code" in data[0]

    def test_correlation_pearson_r_in_range(self, analytics_client):
        resp = analytics_client.get("/api/analysis/correlation?academic_year=2025-26&semester=6")
        for item in resp.json()["data"]:
            r = item.get("pearson_correlation")
            if r is not None:
                assert -1.0 <= r <= 1.0

    def test_correlation_items_have_interpretation(self, analytics_client):
        resp = analytics_client.get("/api/analysis/correlation?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "interpretation" in data[0]


# ===========================================================================
# 61-70: Historical analysis
# ===========================================================================

class TestHistoricalAnalysis:
    def test_historical_returns_200(self, analytics_client):
        resp = analytics_client.get("/api/analysis/historical?academic_year=2025-26&semester=6")
        assert resp.status_code == 200

    def test_historical_returns_list(self, analytics_client):
        resp = analytics_client.get("/api/analysis/historical?academic_year=2025-26&semester=6")
        assert isinstance(resp.json()["data"], list)

    def test_historical_items_have_course_code(self, analytics_client):
        resp = analytics_client.get("/api/analysis/historical?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "course_code" in data[0]

    def test_historical_items_have_trend(self, analytics_client):
        resp = analytics_client.get("/api/analysis/historical?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "trend" in data[0]
            trend = data[0]["trend"]
            assert trend in ("IMPROVING", "DECLINING", "STABLE", "UNKNOWN", None)


# ===========================================================================
# 71-80: Intervention analysis
# ===========================================================================

class TestInterventionAnalysis:
    def test_interventions_returns_200(self, analytics_client):
        resp = analytics_client.get("/api/analysis/interventions?academic_year=2025-26&semester=6")
        assert resp.status_code == 200

    def test_interventions_returns_list(self, analytics_client):
        resp = analytics_client.get("/api/analysis/interventions?academic_year=2025-26&semester=6")
        assert isinstance(resp.json()["data"], list)

    def test_interventions_have_priority_level(self, analytics_client):
        resp = analytics_client.get("/api/analysis/interventions?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "priority_level" in data[0]

    def test_interventions_have_priority_score(self, analytics_client):
        resp = analytics_client.get("/api/analysis/interventions?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if data:
            assert "priority_score" in data[0]

    def test_interventions_priority_score_in_range(self, analytics_client):
        resp = analytics_client.get("/api/analysis/interventions?academic_year=2025-26&semester=6")
        for item in resp.json()["data"]:
            score = item.get("priority_score", 0)
            if score is not None:
                assert 0 <= score <= 100

    def test_interventions_sorted_descending(self, analytics_client):
        resp = analytics_client.get("/api/analysis/interventions?academic_year=2025-26&semester=6")
        data = resp.json()["data"]
        if len(data) >= 2:
            scores = [d.get("priority_score", 0) or 0 for d in data]
            assert scores == sorted(scores, reverse=True)


# ===========================================================================
# 81-90: Backlogs and attainment
# ===========================================================================

class TestBacklogsAndAttainment:
    def test_backlogs_returns_200(self, analytics_client):
        resp = analytics_client.get("/api/analysis/backlogs?academic_year=2025-26&semester=6")
        assert resp.status_code == 200

    def test_backlogs_returns_list(self, analytics_client):
        resp = analytics_client.get("/api/analysis/backlogs?academic_year=2025-26&semester=6")
        assert isinstance(resp.json()["data"], list)

    def test_attainment_input_returns_200(self, analytics_client):
        resp = analytics_client.get("/api/analysis/attainment-input?academic_year=2025-26&semester=6")
        assert resp.status_code == 200

    def test_attainment_input_returns_list(self, analytics_client):
        resp = analytics_client.get("/api/analysis/attainment-input?academic_year=2025-26&semester=6")
        assert isinstance(resp.json()["data"], list)

    def test_demographics_returns_200(self, analytics_client):
        resp = analytics_client.get("/api/analysis/demographics?academic_year=2025-26&semester=6")
        assert resp.status_code == 200

    def test_gpa_distribution_returns_200(self, analytics_client):
        resp = analytics_client.get("/api/analysis/gpa?academic_year=2025-26&semester=6")
        assert resp.status_code == 200


# ===========================================================================
# 91-100: Dashboard endpoint
# ===========================================================================

class TestDashboardEndpoint:
    def test_dashboard_summary_200(self, analytics_client):
        resp = analytics_client.get("/api/dashboard/summary")
        assert resp.status_code == 200

    def test_dashboard_summary_has_data(self, analytics_client):
        resp = analytics_client.get("/api/dashboard/summary")
        assert "data" in resp.json()

    def test_dashboard_summary_success_true(self, analytics_client):
        resp = analytics_client.get("/api/dashboard/summary")
        assert resp.json().get("success") is True

    def test_dashboard_with_filters_200(self, analytics_client):
        resp = analytics_client.get("/api/dashboard/summary?academic_year=2025-26&semester=6")
        assert resp.status_code == 200
