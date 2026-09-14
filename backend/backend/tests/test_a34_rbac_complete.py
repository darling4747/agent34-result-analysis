"""Agent 34 — Complete RBAC tests for all 7 roles (~100 tests)."""
from __future__ import annotations
import os
import pytest
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_result_analysis.db")

from app.models import User, Role
from app.security.password import hash_password
from app.security.permissions import ROLE_PERMISSIONS, P


ROLES = ["PLATFORM_ADMIN", "DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"]


def _get_token(client, db_session, role_name: str) -> str:
    from app.services.auth_service import AuthService
    from app.config import get_settings
    AuthService(db_session, get_settings()).seed_roles_and_permissions()
    email = f"rbac_{role_name.lower()}@test.com"
    role = db_session.query(Role).filter_by(name=role_name).first()
    u = db_session.query(User).filter_by(email=email).first()
    if not u:
        u = User(email=email, full_name=f"{role_name} User", role_id=role.id,
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
    assert resp.status_code == 200, f"Login failed for {role_name}: {resp.json()}"
    return resp.json()["data"]["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# 1-7: All 7 roles can login
# ===========================================================================

class TestAllRolesCanLogin:
    def test_platform_admin_login(self, client, db_session):
        token = _get_token(client, db_session, "PLATFORM_ADMIN")
        assert token

    def test_dean_login(self, client, db_session):
        token = _get_token(client, db_session, "DEAN")
        assert token

    def test_hod_login(self, client, db_session):
        token = _get_token(client, db_session, "HOD")
        assert token

    def test_faculty_login(self, client, db_session):
        token = _get_token(client, db_session, "FACULTY")
        assert token

    def test_iqac_login(self, client, db_session):
        token = _get_token(client, db_session, "IQAC")
        assert token

    def test_management_login(self, client, db_session):
        token = _get_token(client, db_session, "MANAGEMENT")
        assert token

    def test_auditor_login(self, client, db_session):
        token = _get_token(client, db_session, "AUDITOR")
        assert token


# ===========================================================================
# 8-14: All 7 roles can access /api/auth/me
# ===========================================================================

class TestAllRolesCanAccessProfile:
    @pytest.mark.parametrize("role", ROLES)
    def test_role_can_access_me(self, client, db_session, role):
        token = _get_token(client, db_session, role)
        resp = client.get("/api/auth/me", headers=_headers(token))
        assert resp.status_code == 200
        assert resp.json()["data"]["role"] == role


# ===========================================================================
# 15-21: All 7 roles can access dashboard
# ===========================================================================

class TestAllRolesCanAccessDashboard:
    @pytest.mark.parametrize("role", ROLES)
    def test_role_can_access_dashboard(self, client, db_session, role):
        token = _get_token(client, db_session, role)
        resp = client.get("/api/dashboard/summary", headers=_headers(token))
        assert resp.status_code == 200


# ===========================================================================
# 22-28: All 7 roles can access analysis summary
# ===========================================================================

class TestAllRolesCanAccessAnalysis:
    @pytest.mark.parametrize("role", ROLES)
    def test_role_can_access_analysis_summary(self, client, db_session, role):
        token = _get_token(client, db_session, role)
        resp = client.get("/api/analysis/summary", headers=_headers(token))
        assert resp.status_code == 200


# ===========================================================================
# 29-35: Upload — only PLATFORM_ADMIN can upload
# ===========================================================================

class TestUploadRestrictions:
    def test_platform_admin_upload_not_403(self, client, db_session, sample_excel_bytes):
        token = _get_token(client, db_session, "PLATFORM_ADMIN")
        resp = client.post("/api/results/upload",
                           data={"academic_year": "2025-26", "semester": "6"},
                           files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                           headers=_headers(token))
        assert resp.status_code != 403

    @pytest.mark.parametrize("role", ["DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"])
    def test_non_admin_upload_403(self, client, db_session, role):
        token = _get_token(client, db_session, role)
        resp = client.post("/api/results/upload",
                           data={"academic_year": "2025-26", "semester": "6"},
                           files={"file": ("test.xlsx", b"fake", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                           headers=_headers(token))
        assert resp.status_code == 403


# ===========================================================================
# 36-42: Admin user management — only PLATFORM_ADMIN
# ===========================================================================

class TestUserManagementRestrictions:
    def test_platform_admin_can_list_users(self, client, db_session):
        token = _get_token(client, db_session, "PLATFORM_ADMIN")
        resp = client.get("/api/auth/admin/users", headers=_headers(token))
        assert resp.status_code == 200

    @pytest.mark.parametrize("role", ["DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"])
    def test_non_admin_cannot_list_users(self, client, db_session, role):
        token = _get_token(client, db_session, role)
        resp = client.get("/api/auth/admin/users", headers=_headers(token))
        assert resp.status_code == 403

    @pytest.mark.parametrize("role", ["DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"])
    def test_non_admin_cannot_create_user(self, client, db_session, role):
        token = _get_token(client, db_session, role)
        resp = client.post("/api/auth/admin/users",
                           json={"email": f"newusr_{role}@t.com", "full_name": "Test", "role": "FACULTY"},
                           headers=_headers(token))
        assert resp.status_code == 403


# ===========================================================================
# 43-49: Faculty analysis — FACULTY cannot access
# ===========================================================================

class TestFacultyAnalysisRestrictions:
    def test_faculty_cannot_access_faculty_analysis(self, client, db_session):
        token = _get_token(client, db_session, "FACULTY")
        resp = client.get("/api/analysis/faculty", headers=_headers(token))
        assert resp.status_code == 403

    def test_platform_admin_can_access_faculty_analysis(self, client, db_session):
        token = _get_token(client, db_session, "PLATFORM_ADMIN")
        resp = client.get("/api/analysis/faculty", headers=_headers(token))
        assert resp.status_code == 200

    def test_dean_can_access_faculty_analysis(self, client, db_session):
        token = _get_token(client, db_session, "DEAN")
        resp = client.get("/api/analysis/faculty", headers=_headers(token))
        assert resp.status_code == 200

    def test_hod_can_access_faculty_analysis(self, client, db_session):
        token = _get_token(client, db_session, "HOD")
        resp = client.get("/api/analysis/faculty", headers=_headers(token))
        assert resp.status_code == 200

    def test_management_cannot_access_faculty_analysis(self, client, db_session):
        token = _get_token(client, db_session, "MANAGEMENT")
        resp = client.get("/api/analysis/faculty", headers=_headers(token))
        assert resp.status_code == 403


# ===========================================================================
# 50-56: Report generation permissions
# ===========================================================================

class TestReportGeneration:
    def test_auditor_cannot_generate_report(self, client, db_session):
        token = _get_token(client, db_session, "AUDITOR")
        resp = client.post("/api/reports/generate?academic_year=2025-26&semester=6",
                           headers=_headers(token))
        assert resp.status_code == 403

    def test_faculty_can_read_reports(self, client, db_session):
        token = _get_token(client, db_session, "FACULTY")
        resp = client.get("/api/reports/999999", headers=_headers(token))
        # 404 is acceptable (report not found) — just not 401/403
        assert resp.status_code in (200, 404)

    def test_platform_admin_can_generate_report(self, client, db_session):
        token = _get_token(client, db_session, "PLATFORM_ADMIN")
        resp = client.post("/api/reports/generate?academic_year=2025-26&semester=6",
                           headers=_headers(token))
        # May be 200 (no data) or 500 (no data to generate from) — not 403
        assert resp.status_code != 403


# ===========================================================================
# 57-63: Audit log access
# ===========================================================================

class TestAuditLogAccess:
    def test_platform_admin_can_access_audit_logs(self, client, db_session):
        token = _get_token(client, db_session, "PLATFORM_ADMIN")
        resp = client.get("/api/auth/audit-logs", headers=_headers(token))
        assert resp.status_code == 200

    def test_auditor_can_access_audit_logs(self, client, db_session):
        token = _get_token(client, db_session, "AUDITOR")
        resp = client.get("/api/auth/audit-logs", headers=_headers(token))
        assert resp.status_code == 200

    @pytest.mark.parametrize("role", ["DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT"])
    def test_non_auditor_cannot_access_audit_logs(self, client, db_session, role):
        token = _get_token(client, db_session, role)
        resp = client.get("/api/auth/audit-logs", headers=_headers(token))
        assert resp.status_code == 403


# ===========================================================================
# 64-70: Admin diagnostics
# ===========================================================================

class TestAdminDiagnostics:
    def test_admin_diagnostics_requires_auth(self, client):
        resp = client.get("/api/admin/diagnostics")
        assert resp.status_code == 401

    def test_admin_diagnostics_platform_admin_200(self, client, db_session):
        token = _get_token(client, db_session, "PLATFORM_ADMIN")
        resp = client.get("/api/admin/diagnostics", headers=_headers(token))
        assert resp.status_code == 200

    def test_admin_diagnostics_has_database_field(self, client, db_session):
        token = _get_token(client, db_session, "PLATFORM_ADMIN")
        resp = client.get("/api/admin/diagnostics", headers=_headers(token))
        assert "database" in resp.json()["data"]

    def test_admin_diagnostics_has_students_count(self, client, db_session):
        token = _get_token(client, db_session, "PLATFORM_ADMIN")
        resp = client.get("/api/admin/diagnostics", headers=_headers(token))
        assert "students" in resp.json()["data"]

    def test_admin_diagnostics_non_admin_403(self, client, db_session):
        token = _get_token(client, db_session, "FACULTY")
        resp = client.get("/api/admin/diagnostics", headers=_headers(token))
        assert resp.status_code == 403

    def test_admin_diagnostics_no_credentials_in_response(self, client, db_session):
        token = _get_token(client, db_session, "PLATFORM_ADMIN")
        resp = client.get("/api/admin/diagnostics", headers=_headers(token))
        text = str(resp.json())
        assert "password" not in text.lower()
        assert "secret" not in text.lower()


# ===========================================================================
# 71-78: Permission matrix (unit tests)
# ===========================================================================

class TestPermissionMatrix:
    def test_platform_admin_permissions_count(self):
        assert len(ROLE_PERMISSIONS["PLATFORM_ADMIN"]) > 10

    def test_faculty_has_result_read(self):
        assert P.RESULT_READ in ROLE_PERMISSIONS["FACULTY"]

    def test_faculty_has_merit_read(self):
        assert P.MERIT_READ in ROLE_PERMISSIONS["FACULTY"]

    def test_iqac_has_analysis_institution(self):
        assert P.ANALYSIS_INSTITUTION in ROLE_PERMISSIONS["IQAC"]

    def test_management_lacks_result_upload(self):
        assert P.RESULT_UPLOAD not in ROLE_PERMISSIONS["MANAGEMENT"]

    def test_hod_has_analysis_department(self):
        assert P.ANALYSIS_DEPARTMENT in ROLE_PERMISSIONS["HOD"]

    def test_dean_has_result_export(self):
        assert P.RESULT_EXPORT in ROLE_PERMISSIONS["DEAN"]

    def test_auditor_lacks_config_manage(self):
        assert P.CONFIG_MANAGE not in ROLE_PERMISSIONS["AUDITOR"]


# ===========================================================================
# 79-85: Role response in /me endpoint
# ===========================================================================

class TestMeEndpointRoles:
    @pytest.mark.parametrize("role", ROLES)
    def test_me_returns_correct_role(self, client, db_session, role):
        token = _get_token(client, db_session, role)
        resp = client.get("/api/auth/me", headers=_headers(token))
        assert resp.json()["data"]["role"] == role


# ===========================================================================
# 86-92: Invalid token returns 401
# ===========================================================================

class TestInvalidTokens:
    def test_garbage_token_401(self, client):
        resp = client.get("/api/dashboard/summary", headers={"Authorization": "Bearer garbage.token.here"})
        assert resp.status_code == 401

    def test_missing_bearer_prefix_401(self, client):
        from app.security.tokens import create_access_token
        token = create_access_token(1, "test@t.com", "FACULTY", [])
        resp = client.get("/api/dashboard/summary", headers={"Authorization": token})
        assert resp.status_code == 401

    def test_no_auth_header_401(self, client):
        resp = client.get("/api/dashboard/summary")
        assert resp.status_code == 401
