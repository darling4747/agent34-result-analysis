"""Comprehensive authentication and RBAC tests for Agent 34."""
from __future__ import annotations
import os
import pytest

# Ensure test DB env var is set before any app imports
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_result_analysis.db")

from app.models import Role, User
from app.security.password import (
    PasswordPolicyError,
    generate_temp_password,
    hash_password,
    validate_password_policy,
    verify_password,
)
from app.security.permissions import ROLE_PERMISSIONS, VALID_ROLES, P
from app.security.tokens import TokenError, create_access_token, decode_access_token


# ---------------------------------------------------------------------------
# Helper: seed a user into the test DB
# ---------------------------------------------------------------------------

def _seed_user(db, role_name: str, email: str, must_change: bool = False) -> tuple:
    """Create a user with the given role and a known password. Returns (user, plain_password)."""
    from app.services.auth_service import AuthService
    from app.config import get_settings

    AuthService(db, get_settings()).seed_roles_and_permissions()
    role = db.query(Role).filter_by(name=role_name).first()
    plain = "TestPass99!X"
    user = User(
        email=email,
        full_name="Test User",
        role_id=role.id,
        is_active=True,
        password_hash=hash_password(plain),
        must_change_password=must_change,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, plain


def _login(client, email: str, password: str) -> dict:
    """Helper to log in and return the response JSON."""
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    return resp


def _auth_headers(client, email: str, password: str) -> dict:
    """Login and return authorization headers."""
    resp = _login(client, email, password)
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# 1-6: Password hashing
# ===========================================================================

def test_hash_not_plaintext():
    """Bcrypt hash must not store plaintext."""
    h = hash_password("SecretPass1!")
    assert h.startswith("$2b$"), "bcrypt hash should start with $2b$"


def test_verify_password_correct():
    """verify_password returns True for correct password."""
    plain = "CorrectHorse99!"
    h = hash_password(plain)
    assert verify_password(plain, h) is True


def test_verify_password_wrong():
    """verify_password returns False for wrong password."""
    h = hash_password("OriginalPass1!")
    assert verify_password("WrongPass1!", h) is False


def test_generate_temp_password_length():
    """Temp password must be at least 16 characters."""
    pw = generate_temp_password()
    assert len(pw) >= 16, f"Expected ≥16 chars, got {len(pw)}"


def test_generate_temp_password_unique():
    """20 consecutive temp passwords must all be unique (cryptographic uniqueness)."""
    passwords = [generate_temp_password() for _ in range(20)]
    assert len(set(passwords)) == 20, "Temp passwords should be unique"


def test_generate_temp_password_has_required_chars():
    """Temp password must have uppercase, lowercase, and digit."""
    for _ in range(10):
        pw = generate_temp_password()
        has_upper = any(c.isupper() for c in pw)
        has_lower = any(c.islower() for c in pw)
        has_digit = any(c.isdigit() for c in pw)
        assert has_upper, f"Missing uppercase in: {pw}"
        assert has_lower, f"Missing lowercase in: {pw}"
        assert has_digit, f"Missing digit in: {pw}"


# ===========================================================================
# 7-12: Password policy validation
# ===========================================================================

def test_policy_rejects_short():
    """Policy rejects passwords shorter than 12 characters."""
    with pytest.raises(PasswordPolicyError):
        validate_password_policy("Short1!")


def test_policy_rejects_no_uppercase():
    """Policy rejects password without uppercase letter."""
    with pytest.raises(PasswordPolicyError):
        validate_password_policy("nouppercase1!")


def test_policy_rejects_no_digit():
    """Policy rejects password without a digit."""
    with pytest.raises(PasswordPolicyError):
        validate_password_policy("NoDigitsAtAll!!")


def test_policy_rejects_no_special():
    """Policy rejects password without a special character."""
    with pytest.raises(PasswordPolicyError):
        validate_password_policy("NoSpecialChar1234")


def test_policy_rejects_password_pattern():
    """Policy rejects passwords containing 'password'."""
    with pytest.raises(PasswordPolicyError):
        validate_password_policy("Password123!abc")


def test_policy_accepts_valid():
    """Policy accepts a strong password."""
    # Should not raise
    validate_password_policy("StrongPass99!@")


# ===========================================================================
# 13-14: JWT tokens
# ===========================================================================

def test_jwt_roundtrip():
    """JWT encode/decode roundtrip preserves user_id, email, role, permissions."""
    token = create_access_token(
        user_id=42,
        email="user@test.com",
        role="HOD",
        permissions=["RESULT_READ", "ANALYSIS_READ"],
    )
    payload = decode_access_token(token)
    assert payload["user_id"] == 42
    assert payload["sub"] == "user@test.com"
    assert payload["role"] == "HOD"
    assert "RESULT_READ" in payload["permissions"]


def test_jwt_invalid_raises_token_error():
    """Decoding a garbage token raises TokenError."""
    with pytest.raises(TokenError):
        decode_access_token("not.a.valid.jwt.token")


# ===========================================================================
# 15-19: RBAC permissions
# ===========================================================================

def test_all_seven_roles_present():
    """All 7 required roles must be present in ROLE_PERMISSIONS."""
    required = {"PLATFORM_ADMIN", "DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"}
    assert required.issubset(set(VALID_ROLES))


def test_platform_admin_has_full_permissions():
    """PLATFORM_ADMIN must have USER_CREATE, RESULT_UPLOAD, AUDIT_READ, CONFIG_MANAGE."""
    perms = set(ROLE_PERMISSIONS["PLATFORM_ADMIN"])
    assert P.USER_CREATE in perms
    assert P.RESULT_UPLOAD in perms
    assert P.AUDIT_READ in perms
    assert P.CONFIG_MANAGE in perms


def test_auditor_has_no_write_permissions():
    """AUDITOR must NOT have write permissions (USER_CREATE, USER_DISABLE, RESULT_UPLOAD)."""
    perms = set(ROLE_PERMISSIONS["AUDITOR"])
    assert P.USER_CREATE not in perms
    assert P.USER_DISABLE not in perms
    assert P.RESULT_UPLOAD not in perms


def test_faculty_lacks_admin_permissions():
    """FACULTY must not have USER_CREATE or ROLE_ASSIGN."""
    perms = set(ROLE_PERMISSIONS["FACULTY"])
    assert P.USER_CREATE not in perms
    assert P.ROLE_ASSIGN not in perms


def test_management_lacks_user_management():
    """MANAGEMENT must not have USER_CREATE or USER_DISABLE."""
    perms = set(ROLE_PERMISSIONS["MANAGEMENT"])
    assert P.USER_CREATE not in perms
    assert P.USER_DISABLE not in perms


# ===========================================================================
# 20-24: Login endpoint
# ===========================================================================

def test_login_success(client, db_session):
    """Successful login returns access_token."""
    _seed_user(db_session, "HOD", "hod_login@test.com")
    resp = _login(client, "hod_login@test.com", "TestPass99!X")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, db_session):
    """Wrong password returns 401."""
    _seed_user(db_session, "FACULTY", "fac_wrong@test.com")
    resp = _login(client, "fac_wrong@test.com", "WrongPassword1!")
    assert resp.status_code == 401


def test_login_unknown_email(client, db_session):
    """Unknown email returns 401."""
    resp = _login(client, "nobody@nowhere.com", "AnyPassword1!")
    assert resp.status_code == 401


def test_login_must_change_password_flag(client, db_session):
    """Login with must_change_password=True returns that flag as true."""
    _seed_user(db_session, "FACULTY", "fac_mustchange@test.com", must_change=True)
    resp = _login(client, "fac_mustchange@test.com", "TestPass99!X")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["must_change_password"] is True


# ===========================================================================
# 25-27: No public registration endpoints
# ===========================================================================

def test_no_public_register_endpoint(client):
    """/register must not exist (404)."""
    resp = client.post("/register", json={})
    assert resp.status_code == 404


def test_no_public_signup_endpoint(client):
    """/signup must not exist (404)."""
    resp = client.post("/signup", json={})
    assert resp.status_code == 404


def test_no_api_register_endpoint(client):
    """/api/register must not exist (404)."""
    resp = client.post("/api/register", json={})
    assert resp.status_code == 404


# ===========================================================================
# 28-30: Unauthenticated access is blocked (401)
# ===========================================================================

def test_unauthenticated_analysis_summary(client):
    """Unauthenticated access to /api/analysis/summary returns 401."""
    resp = client.get("/api/analysis/summary")
    assert resp.status_code == 401


def test_unauthenticated_dashboard_summary(client):
    """Unauthenticated access to /api/dashboard/summary returns 401."""
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 401


def test_unauthenticated_upload(client):
    """Unauthenticated POST to /api/results/upload returns 401."""
    resp = client.post("/api/results/upload", files={"file": ("test.xlsx", b"data")})
    assert resp.status_code == 401


# ===========================================================================
# 31-33: Role-based access control via API
# ===========================================================================

def test_platform_admin_can_create_user(client, db_session):
    """PLATFORM_ADMIN can POST /api/auth/admin/users and get temporary_password."""
    _seed_user(db_session, "PLATFORM_ADMIN", "admin_create@test.com")
    headers = _auth_headers(client, "admin_create@test.com", "TestPass99!X")
    resp = client.post(
        "/api/auth/admin/users",
        json={
            "email": "newuser_by_admin@test.com",
            "full_name": "New User",
            "role": "FACULTY",
            "department": "CSE",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "temporary_password" in data
    assert data["temporary_password"] is not None


def test_hod_cannot_create_user(client, db_session):
    """HOD cannot POST /api/auth/admin/users — returns 403."""
    _seed_user(db_session, "HOD", "hod_nonadmin@test.com")
    headers = _auth_headers(client, "hod_nonadmin@test.com", "TestPass99!X")
    resp = client.post(
        "/api/auth/admin/users",
        json={
            "email": "shouldfail@test.com",
            "full_name": "Should Fail",
            "role": "FACULTY",
        },
        headers=headers,
    )
    assert resp.status_code == 403


def test_auditor_cannot_upload_results(client, db_session):
    """AUDITOR cannot upload results — returns 403 or 422."""
    _seed_user(db_session, "AUDITOR", "auditor_upload@test.com")
    headers = _auth_headers(client, "auditor_upload@test.com", "TestPass99!X")
    resp = client.post(
        "/api/results/upload",
        files={"file": ("test.xlsx", b"fake excel data", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"academic_year": "2025-26", "semester": "6"},
        headers=headers,
    )
    assert resp.status_code in (403, 422)


# ===========================================================================
# 34: must_change_password blocks access (403)
# ===========================================================================

def test_must_change_password_blocks_dashboard(client, db_session):
    """User with must_change_password=True cannot access /api/dashboard/summary."""
    _seed_user(db_session, "FACULTY", "fac_blocked@test.com", must_change=True)
    headers = _auth_headers(client, "fac_blocked@test.com", "TestPass99!X")
    resp = client.get("/api/dashboard/summary", headers=headers)
    assert resp.status_code == 403
    assert "PASSWORD_CHANGE_REQUIRED" in resp.json().get("detail", "")


# ===========================================================================
# 35: Full force-password-reset flow
# ===========================================================================

def test_force_password_reset_flow(client, db_session):
    """
    Full flow:
    1. Admin creates user → user has must_change_password=True
    2. Old token cannot access dashboard (403)
    3. User calls /change-initial-password with temp pw
    4. New token works for protected endpoints
    """
    # Step 1: Seed an admin and create a target user
    admin, admin_pw = _seed_user(db_session, "PLATFORM_ADMIN", "admin_flow@test.com")
    admin_headers = _auth_headers(client, "admin_flow@test.com", admin_pw)

    create_resp = client.post(
        "/api/auth/admin/users",
        json={
            "email": "flowuser@test.com",
            "full_name": "Flow User",
            "role": "FACULTY",
            "department": "CSE",
        },
        headers=admin_headers,
    )
    assert create_resp.status_code == 200
    temp_pw = create_resp.json()["data"]["temporary_password"]

    # Step 2: New user logs in — must_change_password is True
    login_resp = _login(client, "flowuser@test.com", temp_pw)
    assert login_resp.status_code == 200
    assert login_resp.json()["data"]["must_change_password"] is True
    old_token = login_resp.json()["data"]["access_token"]
    old_headers = {"Authorization": f"Bearer {old_token}"}

    # Dashboard access blocked
    block_resp = client.get("/api/dashboard/summary", headers=old_headers)
    assert block_resp.status_code == 403

    # Step 3: Change initial password
    new_pw = "NewSecurePass99!@"
    change_resp = client.post(
        "/api/auth/change-initial-password",
        json={
            "current_password": temp_pw,
            "new_password": new_pw,
            "confirm_password": new_pw,
        },
        headers=old_headers,
    )
    assert change_resp.status_code == 200, f"Change failed: {change_resp.json()}"
    new_token = change_resp.json()["data"]["access_token"]
    assert new_token is not None

    # Step 4: New token allows access
    new_headers = {"Authorization": f"Bearer {new_token}"}
    # /api/auth/me should be accessible
    me_resp = client.get("/api/auth/me", headers=new_headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["email"] == "flowuser@test.com"


# ===========================================================================
# 36: User list never contains password fields
# ===========================================================================

def test_user_list_no_passwords(client, db_session):
    """GET /api/auth/admin/users must never contain password_hash or temporary_password."""
    _seed_user(db_session, "PLATFORM_ADMIN", "admin_list@test.com")
    headers = _auth_headers(client, "admin_list@test.com", "TestPass99!X")
    resp = client.get("/api/auth/admin/users", headers=headers)
    assert resp.status_code == 200
    users = resp.json()["data"]
    assert isinstance(users, list)
    for u in users:
        assert "password_hash" not in u, "password_hash must never be returned"
        assert "temporary_password" not in u, "temporary_password must never be returned"
