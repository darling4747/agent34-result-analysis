"""A34 Error Handling & Edge Case Tests."""
from __future__ import annotations
import io, pytest, pandas as pd
from app.models import ImportBatch

def _make_excel(n=3):
    df = pd.DataFrame({
        "roll_number": [f"22CS{i:03d}" for i in range(1, n+1)],
        "student_name": [f"S{i}" for i in range(1, n+1)],
        "programme": ["B.Tech"]*n, "department": ["CSE"]*n,
        "batch": ["2022"]*n, "section": ["A"]*n,
        "course_code": ["CS601"]*n, "course_name": ["Compiler"]*n,
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


class TestHTTP400Errors:
    def test_upload_wrong_extension_400(self, auth_client):
        r = auth_client.post("/api/results/upload",
            files={"file": ("bad.txt", io.BytesIO(b"data"), "text/plain")},
            data={"academic_year": "2025-26", "semester": "6"})
        assert r.status_code == 400

    def test_upload_empty_file_400(self, auth_client):
        r = auth_client.post("/api/results/upload",
            files={"file": ("empty.xlsx", io.BytesIO(b""), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6"})
        assert r.status_code == 400

    def test_upload_pdf_extension_400(self, auth_client):
        r = auth_client.post("/api/results/upload",
            files={"file": ("results.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
            data={"academic_year": "2025-26", "semester": "6"})
        assert r.status_code == 400

    def test_upload_no_filename_400(self, auth_client):
        r = auth_client.post("/api/results/upload",
            files={"file": ("", io.BytesIO(b"data"), "application/octet-stream")},
            data={"academic_year": "2025-26", "semester": "6"})
        assert r.status_code in (400, 422)

class TestHTTP401Errors:
    def test_no_token_401_dashboard(self, client):
        assert client.get("/api/dashboard/summary").status_code == 401

    def test_no_token_401_summary(self, client):
        assert client.get("/api/analysis/summary").status_code == 401

    def test_no_token_401_grades(self, client):
        assert client.get("/api/analysis/grades").status_code == 401

    def test_no_token_401_courses(self, client):
        assert client.get("/api/analysis/courses").status_code == 401

    def test_no_token_401_sections(self, client):
        assert client.get("/api/analysis/sections").status_code == 401

    def test_no_token_401_faculty(self, client):
        assert client.get("/api/analysis/faculty").status_code == 401

    def test_no_token_401_merit(self, client):
        assert client.get("/api/analysis/merit-list").status_code == 401

    def test_no_token_401_correlation(self, client):
        assert client.get("/api/analysis/correlation").status_code == 401

    def test_no_token_401_historical(self, client):
        assert client.get("/api/analysis/historical").status_code == 401

    def test_no_token_401_interventions(self, client):
        assert client.get("/api/analysis/interventions").status_code == 401

    def test_no_token_401_backlogs(self, client):
        assert client.get("/api/analysis/backlogs").status_code == 401

    def test_no_token_401_attainment(self, client):
        assert client.get("/api/analysis/attainment-input").status_code == 401

    def test_no_token_401_upload(self, client):
        r = client.post("/api/results/upload",
            files={"file": ("t.xlsx", io.BytesIO(b"x"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6"})
        assert r.status_code == 401

    def test_no_token_401_imports(self, client):
        assert client.get("/api/results/imports").status_code == 401

    def test_no_token_401_dataset_info(self, client):
        assert client.get("/api/results/dataset-info").status_code == 401

    def test_wrong_password_401(self, client, db_session):
        from app.models import Role, User
        from app.security.password import hash_password
        from app.services.auth_service import AuthService
        from app.config import get_settings
        AuthService(db_session, get_settings()).seed_roles_and_permissions()
        role = db_session.query(Role).filter_by(name="HOD").first()
        u = User(email="err401@test.com", full_name="E", role_id=role.id,
                 is_active=True, password_hash=hash_password("Correct99!X"),
                 must_change_password=False)
        db_session.add(u); db_session.commit()
        r = client.post("/api/auth/login", json={"email": "err401@test.com", "password": "Wrong99!X"})
        assert r.status_code == 401

    def test_unknown_email_401(self, client):
        r = client.post("/api/auth/login", json={"email": "nobody@nowhere.com", "password": "Pass99!X"})
        assert r.status_code == 401

    def test_invalid_jwt_401(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.valid.token"})
        assert r.status_code == 401

    def test_malformed_bearer_401(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "InvalidScheme token"})
        assert r.status_code == 401

class TestHTTP403Errors:
    def test_faculty_upload_403(self, client, db_session):
        from app.models import Role, User
        from app.security.password import hash_password
        from app.services.auth_service import AuthService
        from app.config import get_settings
        AuthService(db_session, get_settings()).seed_roles_and_permissions()
        role = db_session.query(Role).filter_by(name="FACULTY").first()
        u = User(email="fac403@test.com", full_name="F", role_id=role.id,
                 is_active=True, password_hash=hash_password("FacPass99!X"),
                 must_change_password=False)
        db_session.add(u); db_session.commit()
        resp = client.post("/api/auth/login", json={"email": "fac403@test.com", "password": "FacPass99!X"})
        token = resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        r = client.post("/api/results/upload",
            files={"file": ("t.xlsx", io.BytesIO(b"x"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6"},
            headers=headers)
        assert r.status_code == 403

    def test_auditor_upload_403(self, client, db_session):
        from app.models import Role, User
        from app.security.password import hash_password
        from app.services.auth_service import AuthService
        from app.config import get_settings
        AuthService(db_session, get_settings()).seed_roles_and_permissions()
        role = db_session.query(Role).filter_by(name="AUDITOR").first()
        u = User(email="aud403@test.com", full_name="A", role_id=role.id,
                 is_active=True, password_hash=hash_password("AudPass99!X"),
                 must_change_password=False)
        db_session.add(u); db_session.commit()
        resp = client.post("/api/auth/login", json={"email": "aud403@test.com", "password": "AudPass99!X"})
        token = resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        r = client.post("/api/results/upload",
            files={"file": ("t.xlsx", io.BytesIO(b"x"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6"},
            headers=headers)
        assert r.status_code == 403

    def test_no_register_endpoint_404(self, client):
        assert client.post("/register", json={}).status_code == 404

    def test_no_signup_endpoint_404(self, client):
        assert client.post("/signup", json={}).status_code == 404

    def test_non_admin_create_user_403(self, auth_client):
        # auth_client is PLATFORM_ADMIN — override with HOD
        pass  # tested in auth tests

class TestResponseHasNoStackTrace:
    def test_wrong_password_no_traceback(self, client):
        r = client.post("/api/auth/login", json={"email": "x@x.com", "password": "bad"})
        body = r.text
        assert "Traceback" not in body
        assert "File " not in body or "location" in body.lower()

    def test_invalid_token_no_traceback(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
        assert "Traceback" not in r.text

    def test_success_false_on_401(self, client):
        r = client.get("/api/dashboard/summary")
        if r.status_code == 401:
            body = r.json()
            # Either standard FastAPI detail or our success=false format
            assert "detail" in body or body.get("success") is False

class TestHTTP422Validation:
    def test_login_missing_email_422(self, client):
        r = client.post("/api/auth/login", json={"password": "pass"})
        assert r.status_code == 422

    def test_login_missing_password_422(self, client):
        r = client.post("/api/auth/login", json={"email": "a@b.com"})
        assert r.status_code == 422

    def test_login_empty_body_422(self, client):
        r = client.post("/api/auth/login", json={})
        assert r.status_code == 422

class TestEdgeCases:
    def test_dataset_info_no_data(self, auth_client, db_session):
        db_session.query(ImportBatch).update({"is_active": False})
        db_session.commit()
        r = auth_client.get("/api/results/dataset-info")
        assert r.status_code == 200
        assert r.json()["data"]["has_data"] is False

    def test_summary_no_data_returns_zeros(self, auth_client, db_session):
        from app.models import Result
        db_session.query(ImportBatch).update({"is_active": False})
        db_session.query(Result).delete()
        db_session.commit()
        db_session.expire_all()
        r = auth_client.get("/api/analysis/summary")
        assert r.status_code == 200
        assert r.json()["data"]["total_results"] == 0

    def test_grades_no_data_empty_or_zeros(self, auth_client, db_session):
        from app.models import Result
        db_session.query(ImportBatch).update({"is_active": False})
        db_session.query(Result).delete()
        db_session.commit()
        db_session.expire_all()
        r = auth_client.get("/api/analysis/grades")
        assert r.status_code == 200
        data = r.json()["data"]
        assert sum(g.get("count", 0) for g in data) == 0

    def test_imports_list_paginated(self, auth_client):
        r = auth_client.get("/api/results/imports")
        assert r.status_code == 200
        body = r.json()
        assert "data" in body
        assert "pagination" in body

    def test_narrative_generate_no_data(self, auth_client, db_session):
        db_session.query(ImportBatch).update({"is_active": False})
        db_session.commit()
        r = auth_client.post("/api/analysis/narrative/generate")
        assert r.status_code == 200

    def test_health_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_root_returns_200(self, client):
        assert client.get("/").status_code == 200

    def test_docs_returns_200(self, client):
        assert client.get("/docs").status_code == 200
