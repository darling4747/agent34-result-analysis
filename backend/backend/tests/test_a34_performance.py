"""A34 Performance Tests."""
import io, time, pandas as pd

def _make_excel(n):
    df = pd.DataFrame({
        "roll_number": [f"22CS{i:04d}" for i in range(1, n+1)],
        "student_name": [f"Student {i}" for i in range(1, n+1)],
        "programme": ["B.Tech"]*n, "department": ["CSE"]*n,
        "batch": ["2022"]*n, "section": ["A"]*n,
        "course_code": ["CS601"]*n, "course_name": ["Course"]*n,
        "faculty": ["Dr. X"]*n, "semester": [6]*n,
        "academic_year": ["2025-26"]*n,
        "internal_marks": [22]*n, "external_marks": [50]*n,
        "total_marks": [72]*n, "grade": ["A"]*n,
        "grade_point": [8]*n, "result_status": ["PASS"]*n,
    })
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf.read()

class TestResponseTime:
    def test_health_responds_fast(self, client):
        start = time.time()
        r = client.get("/health")
        elapsed = time.time() - start
        assert r.status_code == 200
        assert elapsed < 5.0, f"Health took {elapsed:.2f}s"

    def test_root_responds_fast(self, client):
        start = time.time()
        r = client.get("/")
        elapsed = time.time() - start
        assert r.status_code == 200
        assert elapsed < 5.0

    def test_login_responds_within_10s(self, client, db_session):
        from app.models import Role, User
        from app.security.password import hash_password
        from app.services.auth_service import AuthService
        from app.config import get_settings
        AuthService(db_session, get_settings()).seed_roles_and_permissions()
        role = db_session.query(Role).filter_by(name="HOD").first()
        u = User(email="perf_login@test.com", full_name="P", role_id=role.id,
                 is_active=True, password_hash=hash_password("PerfPass99!X"),
                 must_change_password=False)
        db_session.add(u); db_session.commit()
        start = time.time()
        r = client.post("/api/auth/login", json={"email": "perf_login@test.com", "password": "PerfPass99!X"})
        elapsed = time.time() - start
        assert r.status_code == 200
        assert elapsed < 10.0

    def test_dashboard_summary_responds_within_30s(self, auth_client):
        start = time.time()
        r = auth_client.get("/api/dashboard/summary")
        elapsed = time.time() - start
        assert r.status_code == 200
        assert elapsed < 30.0

    def test_analysis_summary_responds_within_30s(self, auth_client):
        start = time.time()
        r = auth_client.get("/api/analysis/summary")
        elapsed = time.time() - start
        assert r.status_code == 200
        assert elapsed < 30.0

    def test_grade_distribution_responds_within_30s(self, auth_client):
        start = time.time()
        r = auth_client.get("/api/analysis/grades")
        elapsed = time.time() - start
        assert r.status_code == 200
        assert elapsed < 30.0

    def test_intervention_responds_within_30s(self, auth_client):
        start = time.time()
        r = auth_client.get("/api/analysis/interventions")
        elapsed = time.time() - start
        assert r.status_code == 200
        assert elapsed < 30.0

class TestUploadPerformance:
    def test_small_dataset_upload_within_30s(self, auth_client):
        data = _make_excel(50)
        start = time.time()
        r = auth_client.post("/api/results/upload",
            files={"file": ("perf.xlsx", io.BytesIO(data),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        elapsed = time.time() - start
        assert r.status_code == 200
        assert elapsed < 30.0

class TestConcurrentRequests:
    def test_multiple_dashboard_requests(self, auth_client):
        """Dashboard should handle repeated requests without error."""
        for _ in range(3):
            r = auth_client.get("/api/dashboard/summary")
            assert r.status_code == 200

    def test_multiple_analysis_requests(self, auth_client):
        """Analytics endpoints should be stable under repeated calls."""
        endpoints = ["/api/analysis/summary", "/api/analysis/grades", "/api/analysis/courses"]
        for ep in endpoints:
            r = auth_client.get(ep)
            assert r.status_code == 200
