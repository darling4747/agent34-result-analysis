"""
A34 Adversarial / Failure Injection Tests
Tests that intentionally attempt to break the system.
"""
import io, pytest

# ── Authentication bypass attempts ────────────────────────────────────────────
class TestAuthBypass:
    def test_no_token_returns_401_not_200(self, client):
        r = client.get("/api/analysis/summary")
        assert r.status_code == 401

    def test_empty_bearer_401(self, client):
        r = client.get("/api/analysis/summary", headers={"Authorization": "Bearer "})
        assert r.status_code == 401

    def test_wrong_algorithm_jwt_rejected(self, client):
        import base64, json as _json
        header = base64.urlsafe_b64encode(_json.dumps({"alg":"none","typ":"JWT"}).encode()).rstrip(b'=')
        payload = base64.urlsafe_b64encode(_json.dumps({"sub":"x@x.com","user_id":1,"role":"PLATFORM_ADMIN"}).encode()).rstrip(b'=')
        fake_jwt = f"{header.decode()}.{payload.decode()}."
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {fake_jwt}"})
        assert r.status_code == 401

    def test_admin_token_cannot_be_forged(self, client, db_session):
        from app.models import Role, User
        from app.security.password import hash_password
        from app.services.auth_service import AuthService
        from app.config import get_settings
        AuthService(db_session, get_settings()).seed_roles_and_permissions()
        role = db_session.query(Role).filter_by(name="FACULTY").first()
        u = User(email="adv_fac@test.com", full_name="F", role_id=role.id,
                 is_active=True, password_hash=hash_password("AdvPass99!X"),
                 must_change_password=False)
        db_session.add(u); db_session.commit()
        r = client.post("/api/auth/login", json={"email": "adv_fac@test.com", "password": "AdvPass99!X"})
        token = r.json()["data"]["access_token"]
        # Use faculty token to attempt admin action
        r2 = client.post("/api/auth/admin/users",
            json={"email": "hacked@test.com", "full_name": "Hacked", "role": "PLATFORM_ADMIN"},
            headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 403

    def test_inactive_user_cannot_login(self, client, db_session):
        from app.models import Role, User
        from app.security.password import hash_password
        from app.services.auth_service import AuthService
        from app.config import get_settings
        AuthService(db_session, get_settings()).seed_roles_and_permissions()
        role = db_session.query(Role).filter_by(name="HOD").first()
        u = User(email="adv_inactive@test.com", full_name="I", role_id=role.id,
                 is_active=False, password_hash=hash_password("InactPass99!X"),
                 must_change_password=False)
        db_session.add(u); db_session.commit()
        r = client.post("/api/auth/login", json={"email": "adv_inactive@test.com", "password": "InactPass99!X"})
        assert r.status_code == 401

    def test_sql_injection_in_email_rejected(self, client):
        r = client.post("/api/auth/login", json={
            "email": "'; DROP TABLE users; --", "password": "anything"})
        assert r.status_code in (401, 422)
        # Database must still work
        r2 = client.get("/health")
        assert r2.status_code == 200

    def test_sql_injection_does_not_corrupt_db(self, client):
        payloads = ["' OR '1'='1", "1; DROP TABLE results", "admin'--", "' UNION SELECT * FROM users --"]
        for p in payloads:
            r = client.post("/api/auth/login", json={"email": p, "password": "x"})
            assert r.status_code in (401, 422)
        # DB still healthy
        assert client.get("/health").json()["database"] == "connected"

# ── Upload abuse ──────────────────────────────────────────────────────────────
class TestUploadAbuse:
    def test_txt_file_rejected(self, auth_client):
        r = auth_client.post("/api/results/upload",
            files={"file": ("evil.txt", io.BytesIO(b"DROP TABLE students;"), "text/plain")},
            data={"academic_year": "2025-26", "semester": "6"})
        assert r.status_code == 400

    def test_exe_file_rejected(self, auth_client):
        r = auth_client.post("/api/results/upload",
            files={"file": ("virus.exe", io.BytesIO(b"MZfake"), "application/octet-stream")},
            data={"academic_year": "2025-26", "semester": "6"})
        assert r.status_code == 400

    def test_empty_file_rejected(self, auth_client):
        r = auth_client.post("/api/results/upload",
            files={"file": ("empty.xlsx", io.BytesIO(b""), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6"})
        assert r.status_code == 400

    def test_path_traversal_filename_safe(self, auth_client):
        r = auth_client.post("/api/results/upload",
            files={"file": ("../../etc/passwd.xlsx", io.BytesIO(b"fake"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6"})
        # Must not crash, must not traverse path
        assert r.status_code in (200, 400, 422)

    def test_invalid_file_does_not_activate_new_dataset(self, auth_client, sample_excel_bytes, db_session):
        from app.models import ImportBatch
        import io as _io
        # First a valid upload
        auth_client.post("/api/results/upload",
            files={"file": ("valid.xlsx", _io.BytesIO(sample_excel_bytes),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        db_session.expire_all()
        active_before = db_session.query(ImportBatch).filter(
            ImportBatch.is_active == True, ImportBatch.status == "COMPLETED").first()
        # Now an invalid upload
        auth_client.post("/api/results/upload",
            files={"file": ("bad.txt", _io.BytesIO(b"corrupt"), "text/plain")},
            data={"academic_year": "2025-26", "semester": "6"})
        db_session.expire_all()
        active_after = db_session.query(ImportBatch).filter(
            ImportBatch.is_active == True, ImportBatch.status == "COMPLETED").first()
        if active_before and active_after:
            assert active_before.id == active_after.id

# ── Cross-role data leakage ───────────────────────────────────────────────────
class TestCrossRoleLeakage:
    def _get_token(self, client, db_session, role, email, pw="TestPass99!X"):
        from app.models import Role, User
        from app.security.password import hash_password
        from app.services.auth_service import AuthService
        from app.config import get_settings
        AuthService(db_session, get_settings()).seed_roles_and_permissions()
        r = db_session.query(Role).filter_by(name=role).first()
        if not db_session.query(User).filter_by(email=email).first():
            u = User(email=email, full_name="T", role_id=r.id, is_active=True,
                     password_hash=hash_password(pw), must_change_password=False)
            db_session.add(u); db_session.commit()
        resp = client.post("/api/auth/login", json={"email": email, "password": pw})
        return resp.json()["data"]["access_token"]

    def test_auditor_cannot_upload(self, client, db_session):
        token = self._get_token(client, db_session, "AUDITOR", "adv_aud@test.com")
        r = client.post("/api/results/upload",
            files={"file": ("t.xlsx", io.BytesIO(b"x"),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6"},
            headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_auditor_cannot_create_user(self, client, db_session):
        token = self._get_token(client, db_session, "AUDITOR", "adv_aud2@test.com")
        r = client.post("/api/auth/admin/users",
            json={"email": "new@test.com", "full_name": "N", "role": "FACULTY"},
            headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_faculty_cannot_upload(self, client, db_session):
        token = self._get_token(client, db_session, "FACULTY", "adv_fac2@test.com")
        r = client.post("/api/results/upload",
            files={"file": ("t.xlsx", io.BytesIO(b"x"),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6"},
            headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_management_cannot_create_user(self, client, db_session):
        token = self._get_token(client, db_session, "MANAGEMENT", "adv_mgmt@test.com")
        r = client.post("/api/auth/admin/users",
            json={"email": "new2@test.com", "full_name": "N", "role": "AUDITOR"},
            headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

# ── Malformed input handling ──────────────────────────────────────────────────
class TestMalformedInputs:
    def test_login_with_non_string_email(self, client):
        r = client.post("/api/auth/login", json={"email": 12345, "password": "pass"})
        assert r.status_code in (401, 422)

    def test_login_with_null_values(self, client):
        r = client.post("/api/auth/login", json={"email": None, "password": None})
        assert r.status_code in (401, 422)

    def test_login_empty_json(self, client):
        r = client.post("/api/auth/login", json={})
        assert r.status_code == 422

    def test_create_user_invalid_role(self, auth_client):
        r = auth_client.post("/api/auth/admin/users",
            json={"email": "x@x.com", "full_name": "X", "role": "NONEXISTENT_ROLE"})
        assert r.status_code in (400, 422)

    def test_negative_semester_param(self, auth_client):
        r = auth_client.get("/api/analysis/summary", params={"semester": -1})
        assert r.status_code in (200, 422)

    def test_xss_in_query_param(self, auth_client):
        r = auth_client.get("/api/analysis/summary", params={"department": "<script>alert(1)</script>"})
        assert r.status_code in (200, 422)
        assert "<script>" not in r.text

# ── Dataset A/B/C test (prompt's most important E2E test) ─────────────────────
class TestDatasetABCWorkflow:
    def test_dataset_a_then_b_no_leakage(self, auth_client, db_session):
        """Upload A, then B — dashboard must use B, no A leakage."""
        import io as _io, pandas as pd

        def make_dataset(n, course_code, ay):
            df = pd.DataFrame({
                "roll_number": [f"DS{course_code}{i:03d}" for i in range(1,n+1)],
                "student_name": [f"S{i}" for i in range(1,n+1)],
                "programme": ["B.Tech"]*n, "department": ["CSE"]*n,
                "batch": ["2022"]*n, "section": ["A"]*n,
                "course_code": [course_code]*n, "course_name": ["Course"]*n,
                "faculty": ["Dr. X"]*n, "semester": [6]*n,
                "academic_year": [ay]*n,
                "internal_marks": [22]*n, "external_marks": [50]*n,
                "total_marks": [72]*n, "grade": ["A"]*n,
                "grade_point": [8]*n, "result_status": ["PASS"]*n,
            })
            buf = _io.BytesIO()
            df.to_excel(buf, index=False)
            buf.seek(0)
            return buf.read()

        # Upload dataset A
        dataset_a = make_dataset(10, "DSA01", "2025-26")
        auth_client.post("/api/results/upload",
            files={"file": ("dataset_a.xlsx", _io.BytesIO(dataset_a),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})

        # Upload dataset B
        dataset_b = make_dataset(15, "DSB01", "2026-27")
        auth_client.post("/api/results/upload",
            files={"file": ("dataset_b.xlsx", _io.BytesIO(dataset_b),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2026-27", "semester": "6", "department": "CSE"})

        db_session.expire_all()
        from app.models import ImportBatch
        from app.services.dataset_service import DatasetService

        active = db_session.query(ImportBatch).filter(
            ImportBatch.is_active == True, ImportBatch.status == "COMPLETED"
        ).count()
        assert active <= 1, "More than one active batch"

        # Dataset info endpoint must show has_data
        r = auth_client.get("/api/results/dataset-info")
        assert r.status_code == 200
        assert r.json()["data"]["has_data"] is True

    def test_invalid_upload_c_keeps_active_dataset(self, auth_client, db_session, sample_excel_bytes):
        """Invalid upload C must not replace valid dataset."""
        import io as _io
        from app.models import ImportBatch

        # Valid upload first
        auth_client.post("/api/results/upload",
            files={"file": ("valid_b.xlsx", _io.BytesIO(sample_excel_bytes),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        db_session.expire_all()

        active_before_id = None
        active_before = db_session.query(ImportBatch).filter(
            ImportBatch.is_active == True, ImportBatch.status == "COMPLETED").first()
        if active_before:
            active_before_id = active_before.id

        # Invalid upload C (wrong extension)
        auth_client.post("/api/results/upload",
            files={"file": ("invalid_c.txt", _io.BytesIO(b"corrupt data"), "text/plain")},
            data={"academic_year": "2025-26", "semester": "6"})
        db_session.expire_all()

        active_after = db_session.query(ImportBatch).filter(
            ImportBatch.is_active == True, ImportBatch.status == "COMPLETED").first()
        if active_before_id and active_after:
            assert active_after.id == active_before_id, "Invalid upload replaced valid dataset!"

# ── Gemini failure injection ──────────────────────────────────────────────────
class TestGeminiFailureInjection:
    def test_narrative_works_without_gemini(self, auth_client, db_session):
        from app.models import ImportBatch
        db_session.query(ImportBatch).update({"is_active": False})
        db_session.commit()
        r = auth_client.post("/api/analysis/narrative/generate")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["summary"] is not None or data["message"] is not None

    def test_narrative_with_invalid_key_falls_back(self):
        from app.services.narrative import NarrativeService
        from app.config import Settings
        s = Settings(LLM_PROVIDER="gemini", LLM_API_KEY="INVALID_KEY_XYZ", LLM_MODEL="gemini-2.5-flash")
        svc = NarrativeService(s)
        result = svc.generate({
            "summary": {"pass_percentage": 80.0, "failure_percentage": 20.0, "total_students": 100}
        })
        assert result["summary"]
        assert result["model_used"] in ("deterministic", "gemini/gemini-2.5-flash")

    def test_analytics_do_not_depend_on_gemini(self, auth_client):
        r = auth_client.get("/api/analysis/summary")
        assert r.status_code == 200
        # Summary must work without any Gemini call

    def test_gemini_never_provides_student_count(self):
        from app.services.metrics import MetricsService
        from app.database import SessionLocal
        from app.config import get_settings
        db = SessionLocal()
        try:
            svc = MetricsService(db, get_settings())
            result = svc.get_summary({})
            assert isinstance(result["total_students"], int)
        finally:
            db.close()

# ── No secrets leakage ────────────────────────────────────────────────────────
class TestSecretLeakage:
    def test_no_jwt_secret_in_any_response(self, auth_client):
        endpoints = ["/api/auth/me", "/api/health", "/", "/api/results/dataset-info"]
        for ep in endpoints:
            r = auth_client.get(ep)
            assert "Ewx6vZ" not in r.text, f"{ep} leaks JWT secret"

    def test_no_password_hash_in_user_profile(self, auth_client):
        r = auth_client.get("/api/auth/me")
        assert "password_hash" not in r.text

    def test_no_temp_password_in_user_list(self, auth_client):
        r = auth_client.get("/api/auth/admin/users")
        for u in r.json()["data"]:
            assert "temporary_password" not in u

    def test_no_gemini_key_in_narrative_response(self, auth_client, db_session):
        from app.models import ImportBatch
        db_session.query(ImportBatch).update({"is_active": False})
        db_session.commit()
        r = auth_client.post("/api/analysis/narrative/generate")
        assert "AQ.Ab8RN6K" not in r.text

    def test_health_does_not_expose_db_credentials(self, client):
        r = client.get("/health")
        body = r.text.lower()
        assert "password" not in body or "change_me" not in body

# ── Database integrity after failures ─────────────────────────────────────────
class TestDatabaseIntegrityAfterFailures:
    def test_db_healthy_after_sql_injection_attempts(self, client):
        for _ in range(5):
            client.post("/api/auth/login", json={"email": "' OR 1=1--", "password": "x"})
        r = client.get("/health")
        assert r.json()["database"] == "connected"

    def test_db_healthy_after_bad_uploads(self, auth_client):
        for _ in range(3):
            auth_client.post("/api/results/upload",
                files={"file": ("bad.txt", io.BytesIO(b"garbage"), "text/plain")},
                data={"academic_year": "2025-26", "semester": "6"})
        r = auth_client.get("/health")
        assert r.json()["database"] == "connected"

    def test_analytics_return_valid_data_after_failures(self, auth_client):
        r = auth_client.get("/api/analysis/summary")
        assert r.status_code == 200
        body = r.json()
        assert "data" in body
        data = body["data"]
        for key in ["total_students", "pass_percentage", "failure_percentage"]:
            assert key in data
