"""Automated test suite verifying strict enterprise RBAC across all 7 roles."""
import pytest
from app.models import User, Role
from app.services.auth_service import AuthService

ROLES = ["PLATFORM_ADMIN", "DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"]


def _get_token_for_role(client, db_session, role_name: str) -> str:
    """Helper to seed and obtain a Bearer JWT for any given role."""
    email = f"test_{role_name.lower()}@university.edu"
    user = db_session.query(User).filter_by(email=email).first()
    if not user:
        role = db_session.query(Role).filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=f"{role_name} Role")
            db_session.add(role)
            db_session.flush()

        from app.security.password import hash_password
        user = User(
            email=email,
            full_name=f"Test {role_name}",
            password_hash=hash_password("TestPass123!"),
            role_id=role.id,
            department="Computer Science & Engineering",
            is_active=True,
            must_change_password=False,
            mfa_enabled=False,
        )
        db_session.add(user)
        db_session.commit()
    else:
        user.must_change_password = False
        user.mfa_enabled = False
        db_session.commit()

    resp = client.post("/api/auth/login", json={"email": email, "password": "TestPass123!"})
    assert resp.status_code == 200, f"Login failed for {role_name}: {resp.json()}"
    return resp.json()["data"]["access_token"]


def test_upload_results_restricted_to_platform_admin(client, db_session):
    """Verify ONLY PLATFORM_ADMIN can upload results. All other 6 roles receive 403."""
    admin_token = _get_token_for_role(client, db_session, "PLATFORM_ADMIN")
    
    # Non-admin roles must be rejected (403)
    for role_name in ["DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"]:
        token = _get_token_for_role(client, db_session, role_name)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            "/api/results/upload",
            data={"academic_year": "2025-26", "semester": 6, "department": "Computer Science & Engineering"},
            files={"file": ("test.csv", b"usn,name,course_code,internal_marks,external_marks\n1,Test,CS101,25,60", "text/csv")},
            headers=headers,
        )
        assert resp.status_code == 403, f"Role {role_name} should be forbidden from uploading results, but got {resp.status_code}"


def test_user_management_restricted_to_platform_admin(client, db_session):
    """Verify ONLY PLATFORM_ADMIN can list or create users."""
    admin_token = _get_token_for_role(client, db_session, "PLATFORM_ADMIN")
    resp_admin = client.get("/api/auth/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_admin.status_code == 200

    for role_name in ["DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"]:
        token = _get_token_for_role(client, db_session, role_name)
        resp = client.get("/api/auth/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403, f"Role {role_name} should be forbidden from user management"


def test_faculty_analysis_restricted_to_authorized_roles(client, db_session):
    """Verify FACULTY role is forbidden from /api/analysis/faculty."""
    faculty_token = _get_token_for_role(client, db_session, "FACULTY")
    resp = client.get("/api/analysis/faculty", headers={"Authorization": f"Bearer {faculty_token}"})
    assert resp.status_code == 403

    admin_token = _get_token_for_role(client, db_session, "PLATFORM_ADMIN")
    resp_admin = client.get("/api/analysis/faculty", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_admin.status_code == 200


def test_report_generation_mutation_restricted(client, db_session):
    """Verify report generation (mutation) requires REPORT_GENERATE permission."""
    auditor_token = _get_token_for_role(client, db_session, "AUDITOR")
    resp_auditor = client.post(
        "/api/reports/generate?academic_year=2025-26&semester=6",
        headers={"Authorization": f"Bearer {auditor_token}"},
    )
    assert resp_auditor.status_code == 403, "AUDITOR must not be allowed to generate reports"
