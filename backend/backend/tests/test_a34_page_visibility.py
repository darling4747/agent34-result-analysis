"""Agent 34 — Page visibility / API restriction tests per role (~70 tests)."""
from __future__ import annotations
import os
import pytest
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_result_analysis.db")

from app.models import User, Role
from app.security.password import hash_password


def _get_token(client, db_session, role_name: str) -> str:
    from app.services.auth_service import AuthService
    from app.config import get_settings
    AuthService(db_session, get_settings()).seed_roles_and_permissions()
    email = f"pv_{role_name.lower()}@test.com"
    role = db_session.query(Role).filter_by(name=role_name).first()
    u = db_session.query(User).filter_by(email=email).first()
    if not u:
        u = User(email=email, full_name=f"{role_name}", role_id=role.id,
                 password_hash=hash_password("TestPass99!X"), is_active=True,
                 must_change_password=False, mfa_enabled=False,
                 department="Computer Science & Engineering")
        db_session.add(u)
        db_session.commit()
    else:
        u.must_change_password = False
        u.mfa_enabled = False
        db_session.commit()
    resp = client.post("/api/auth/login", json={"email": email, "password": "TestPass99!X"})
    return resp.json()["data"]["access_token"]


def _h(token): return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# 1-7: Upload restricted to PLATFORM_ADMIN only
# ===========================================================================

class TestUploadPageVisibility:
    def test_dean_cannot_upload(self, client, db_session):
        token = _get_token(client, db_session, "DEAN")
        resp = client.post("/api/results/upload",
                           data={"academic_year": "2025-26", "semester": "6"},
                           files={"file": ("t.xlsx", b"data", "application/vnd.ms-excel")},
                           headers=_h(token))
        assert resp.status_code == 403

    def test_hod_cannot_upload(self, client, db_session):
        token = _get_token(client, db_session, "HOD")
        resp = client.post("/api/results/upload",
                           data={"academic_year": "2025-26", "semester": "6"},
                           files={"file": ("t.xlsx", b"data", "application/vnd.ms-excel")},
                           headers=_h(token))
        assert resp.status_code == 403

    def test_faculty_cannot_upload(self, client, db_session):
        token = _get_token(client, db_session, "FACULTY")
        resp = client.post("/api/results/upload",
                           data={"academic_year": "2025-26", "semester": "6"},
                           files={"file": ("t.xlsx", b"data", "application/vnd.ms-excel")},
                           headers=_h(token))
        assert resp.status_code == 403

    def test_iqac_cannot_upload(self, client, db_session):
        token = _get_token(client, db_session, "IQAC")
        resp = client.post("/api/results/upload",
                           data={"academic_year": "2025-26", "semester": "6"},
                           files={"file": ("t.xlsx", b"data", "application/vnd.ms-excel")},
                           headers=_h(token))
        assert resp.status_code == 403

    def test_management_cannot_upload(self, client, db_session):
        token = _get_token(client, db_session, "MANAGEMENT")
        resp = client.post("/api/results/upload",
                           data={"academic_year": "2025-26", "semester": "6"},
                           files={"file": ("t.xlsx", b"data", "application/vnd.ms-excel")},
                           headers=_h(token))
        assert resp.status_code == 403

    def test_auditor_cannot_upload(self, client, db_session):
        token = _get_token(client, db_session, "AUDITOR")
        resp = client.post("/api/results/upload",
                           data={"academic_year": "2025-26", "semester": "6"},
                           files={"file": ("t.xlsx", b"data", "application/vnd.ms-excel")},
                           headers=_h(token))
        assert resp.status_code == 403


# ===========================================================================
# 8-14: User management restricted to PLATFORM_ADMIN
# ===========================================================================

class TestUserManagementVisibility:
    @pytest.mark.parametrize("role", ["DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"])
    def test_non_admin_cannot_get_users(self, client, db_session, role):
        token = _get_token(client, db_session, role)
        resp = client.get("/api/auth/admin/users", headers=_h(token))
        assert resp.status_code == 403

    @pytest.mark.parametrize("role", ["DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"])
    def test_non_admin_cannot_create_user(self, client, db_session, role):
        token = _get_token(client, db_session, role)
        resp = client.post("/api/auth/admin/users",
                           json={"email": f"new_{role}@t.com", "full_name": "Test", "role": "FACULTY"},
                           headers=_h(token))
        assert resp.status_code == 403


# ===========================================================================
# 22-28: Faculty analysis — only authorized roles
# ===========================================================================

class TestFacultyAnalysisVisibility:
    def test_faculty_cannot_access_faculty_analysis(self, client, db_session):
        token = _get_token(client, db_session, "FACULTY")
        resp = client.get("/api/analysis/faculty", headers=_h(token))
        assert resp.status_code == 403

    def test_management_cannot_access_faculty_analysis(self, client, db_session):
        token = _get_token(client, db_session, "MANAGEMENT")
        resp = client.get("/api/analysis/faculty", headers=_h(token))
        assert resp.status_code == 403

    def test_dean_can_access_faculty_analysis(self, client, db_session):
        token = _get_token(client, db_session, "DEAN")
        resp = client.get("/api/analysis/faculty", headers=_h(token))
        assert resp.status_code == 200

    def test_iqac_can_access_faculty_analysis(self, client, db_session):
        token = _get_token(client, db_session, "IQAC")
        resp = client.get("/api/analysis/faculty", headers=_h(token))
        assert resp.status_code == 200


# ===========================================================================
# 29-35: Dataset info accessible to all authenticated
# ===========================================================================

class TestDatasetInfoVisibility:
    @pytest.mark.parametrize("role", ["PLATFORM_ADMIN", "DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"])
    def test_all_roles_can_access_dataset_info(self, client, db_session, role):
        token = _get_token(client, db_session, role)
        resp = client.get("/api/results/dataset-info", headers=_h(token))
        assert resp.status_code == 200


# ===========================================================================
# 36-42: Analysis pages accessible to all roles
# ===========================================================================

class TestAnalysisVisibility:
    @pytest.mark.parametrize("role", ["PLATFORM_ADMIN", "DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"])
    def test_all_roles_can_access_course_analysis(self, client, db_session, role):
        token = _get_token(client, db_session, role)
        resp = client.get("/api/analysis/courses", headers=_h(token))
        assert resp.status_code == 200

    @pytest.mark.parametrize("role", ["PLATFORM_ADMIN", "DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"])
    def test_all_roles_can_access_merit_list(self, client, db_session, role):
        token = _get_token(client, db_session, role)
        resp = client.get("/api/analysis/merit-list", headers=_h(token))
        assert resp.status_code == 200


# ===========================================================================
# 43-49: Audit logs — admin and auditor only
# ===========================================================================

class TestAuditLogVisibility:
    def test_admin_can_see_audit_logs(self, client, db_session):
        token = _get_token(client, db_session, "PLATFORM_ADMIN")
        resp = client.get("/api/auth/audit-logs", headers=_h(token))
        assert resp.status_code == 200

    def test_auditor_can_see_audit_logs(self, client, db_session):
        token = _get_token(client, db_session, "AUDITOR")
        resp = client.get("/api/auth/audit-logs", headers=_h(token))
        assert resp.status_code == 200

    @pytest.mark.parametrize("role", ["DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT"])
    def test_other_roles_cannot_see_audit_logs(self, client, db_session, role):
        token = _get_token(client, db_session, role)
        resp = client.get("/api/auth/audit-logs", headers=_h(token))
        assert resp.status_code == 403


# ===========================================================================
# 50-56: No credentials exposed in any response
# ===========================================================================

class TestNoCredentialsExposed:
    def test_user_list_no_password_hash(self, client, db_session):
        token = _get_token(client, db_session, "PLATFORM_ADMIN")
        resp = client.get("/api/auth/admin/users", headers=_h(token))
        for user in resp.json()["data"]:
            assert "password_hash" not in user

    def test_me_no_password_hash(self, client, db_session):
        token = _get_token(client, db_session, "FACULTY")
        resp = client.get("/api/auth/me", headers=_h(token))
        data = resp.json()["data"]
        assert "password_hash" not in data

    def test_diagnostics_no_password(self, client, db_session):
        token = _get_token(client, db_session, "PLATFORM_ADMIN")
        resp = client.get("/api/admin/diagnostics", headers=_h(token))
        assert "password" not in str(resp.json()).lower()


# ===========================================================================
# 57-63: Department scope enforcement
# ===========================================================================

class TestDepartmentScope:
    def test_hod_dashboard_accessible(self, client, db_session):
        token = _get_token(client, db_session, "HOD")
        resp = client.get("/api/dashboard/summary?department=Computer+Science+%26+Engineering", headers=_h(token))
        assert resp.status_code == 200

    def test_hod_cross_department_blocked(self, client, db_session):
        token = _get_token(client, db_session, "HOD")
        resp = client.get("/api/analysis/summary?department=Mechanical+Engineering", headers=_h(token))
        assert resp.status_code == 403

    def test_faculty_cross_department_blocked(self, client, db_session):
        token = _get_token(client, db_session, "FACULTY")
        resp = client.get("/api/analysis/summary?department=Mechanical+Engineering", headers=_h(token))
        assert resp.status_code == 403

    def test_dean_can_access_any_department(self, client, db_session):
        token = _get_token(client, db_session, "DEAN")
        resp = client.get("/api/analysis/summary?department=Mechanical+Engineering", headers=_h(token))
        assert resp.status_code == 200
