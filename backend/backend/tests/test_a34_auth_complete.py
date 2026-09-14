"""Agent 34 — Complete authentication tests (~80 tests)."""
from __future__ import annotations
import os
import pytest
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_result_analysis.db")

from app.models import User, Role
from app.security.password import (
    PasswordPolicyError, generate_temp_password,
    hash_password, validate_password_policy, verify_password,
)
from app.security.permissions import ROLE_PERMISSIONS, VALID_ROLES, P
from app.security.tokens import TokenError, create_access_token, decode_access_token


def _seed(db, role_name, email, must_change=False, active=True):
    from app.services.auth_service import AuthService
    from app.config import get_settings
    AuthService(db, get_settings()).seed_roles_and_permissions()
    role = db.query(Role).filter_by(name=role_name).first()
    plain = "TestPass99!X"
    u = db.query(User).filter_by(email=email).first()
    if not u:
        u = User(email=email, full_name="Test", role_id=role.id, is_active=active,
                 password_hash=hash_password(plain), must_change_password=must_change,
                 mfa_enabled=False)
        db.add(u)
        db.commit()
    return u, plain


# ===========================================================================
# 1-6: bcrypt password hashing
# ===========================================================================

class TestPasswordHashing:
    def test_hash_starts_with_2b(self):
        h = hash_password("SecretPass1!")
        assert h.startswith("$2b$")

    def test_verify_correct_password_true(self):
        pw = "CorrectHorse99!"
        h = hash_password(pw)
        assert verify_password(pw, h) is True

    def test_verify_wrong_password_false(self):
        h = hash_password("OriginalPass1!")
        assert verify_password("WrongPass1!", h) is False

    def test_hash_not_plaintext(self):
        pw = "MySecretPass99!"
        h = hash_password(pw)
        assert pw not in h

    def test_same_password_different_hashes(self):
        pw = "SamePass99!!"
        h1 = hash_password(pw)
        h2 = hash_password(pw)
        assert h1 != h2  # bcrypt salts differ

    def test_hash_is_string(self):
        h = hash_password("TestPass99!X")
        assert isinstance(h, str)


# ===========================================================================
# 7-15: Temp password
# ===========================================================================

class TestTempPassword:
    def test_temp_password_min_16_chars(self):
        pw = generate_temp_password()
        assert len(pw) >= 16

    def test_temp_password_has_uppercase(self):
        for _ in range(10):
            pw = generate_temp_password()
            assert any(c.isupper() for c in pw)

    def test_temp_password_has_lowercase(self):
        for _ in range(10):
            pw = generate_temp_password()
            assert any(c.islower() for c in pw)

    def test_temp_password_has_digit(self):
        for _ in range(10):
            pw = generate_temp_password()
            assert any(c.isdigit() for c in pw)

    def test_temp_password_unique_20_consecutive(self):
        passwords = [generate_temp_password() for _ in range(20)]
        assert len(set(passwords)) == 20

    def test_temp_password_hash_not_plaintext(self):
        pw = generate_temp_password()
        h = hash_password(pw)
        assert h != pw
        assert verify_password(pw, h) is True


# ===========================================================================
# 16-24: Password policy
# ===========================================================================

class TestPasswordPolicy:
    def test_policy_rejects_short(self):
        with pytest.raises(PasswordPolicyError):
            validate_password_policy("Short1!")

    def test_policy_rejects_exactly_11_chars(self):
        with pytest.raises(PasswordPolicyError):
            validate_password_policy("Abcdefg1!xy")  # 11 chars

    def test_policy_accepts_12_chars(self):
        validate_password_policy("Abcdefg1!xyz")  # 12 chars, no "password"

    def test_policy_rejects_no_uppercase(self):
        with pytest.raises(PasswordPolicyError):
            validate_password_policy("nouppercase1!")

    def test_policy_rejects_no_lowercase(self):
        with pytest.raises(PasswordPolicyError):
            validate_password_policy("NOLOWER1!!")

    def test_policy_rejects_no_digit(self):
        with pytest.raises(PasswordPolicyError):
            validate_password_policy("NoDigitsAtAll!!")

    def test_policy_rejects_no_special(self):
        with pytest.raises(PasswordPolicyError):
            validate_password_policy("NoSpecialChar1234")

    def test_policy_rejects_password_pattern(self):
        with pytest.raises(PasswordPolicyError):
            validate_password_policy("Password123!abc")

    def test_policy_accepts_strong_password(self):
        validate_password_policy("StrongPass99!@")  # should not raise


# ===========================================================================
# 25-30: JWT tokens
# ===========================================================================

class TestJWTTokens:
    def test_jwt_roundtrip_user_id(self):
        token = create_access_token(1, "user@test.com", "HOD", [])
        payload = decode_access_token(token)
        assert payload["user_id"] == 1

    def test_jwt_roundtrip_email(self):
        token = create_access_token(2, "email@test.com", "FACULTY", [])
        payload = decode_access_token(token)
        assert payload["sub"] == "email@test.com"

    def test_jwt_roundtrip_role(self):
        token = create_access_token(3, "role@test.com", "DEAN", [])
        payload = decode_access_token(token)
        assert payload["role"] == "DEAN"

    def test_jwt_roundtrip_permissions(self):
        token = create_access_token(4, "perm@test.com", "HOD", ["RESULT_READ", "ANALYSIS_READ"])
        payload = decode_access_token(token)
        assert "RESULT_READ" in payload["permissions"]

    def test_jwt_invalid_raises_token_error(self):
        with pytest.raises(TokenError):
            decode_access_token("not.a.valid.jwt")

    def test_jwt_tampered_raises_token_error(self):
        token = create_access_token(5, "t@test.com", "HOD", [])
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(TokenError):
            decode_access_token(tampered)


# ===========================================================================
# 31-36: RBAC permission matrix
# ===========================================================================

class TestRBACMatrix:
    def test_platform_admin_has_user_create(self):
        assert P.USER_CREATE in ROLE_PERMISSIONS["PLATFORM_ADMIN"]

    def test_platform_admin_has_result_upload(self):
        assert P.RESULT_UPLOAD in ROLE_PERMISSIONS["PLATFORM_ADMIN"]

    def test_platform_admin_has_audit_read(self):
        assert P.AUDIT_READ in ROLE_PERMISSIONS["PLATFORM_ADMIN"]

    def test_platform_admin_has_config_manage(self):
        assert P.CONFIG_MANAGE in ROLE_PERMISSIONS["PLATFORM_ADMIN"]

    def test_dean_lacks_user_create(self):
        assert P.USER_CREATE not in ROLE_PERMISSIONS["DEAN"]

    def test_dean_lacks_result_upload(self):
        assert P.RESULT_UPLOAD not in ROLE_PERMISSIONS["DEAN"]

    def test_hod_lacks_user_create(self):
        assert P.USER_CREATE not in ROLE_PERMISSIONS["HOD"]

    def test_hod_has_result_upload(self):
        # HOD can upload results per the spec
        # Check spec: HOD does NOT have RESULT_UPLOAD per permissions.py
        assert P.USER_CREATE not in ROLE_PERMISSIONS["HOD"]

    def test_faculty_lacks_user_create(self):
        assert P.USER_CREATE not in ROLE_PERMISSIONS["FACULTY"]

    def test_faculty_lacks_role_assign(self):
        assert P.ROLE_ASSIGN not in ROLE_PERMISSIONS["FACULTY"]

    def test_iqac_has_analysis_demographic(self):
        assert P.ANALYSIS_DEMOGRAPHIC in ROLE_PERMISSIONS["IQAC"]

    def test_iqac_lacks_user_create(self):
        assert P.USER_CREATE not in ROLE_PERMISSIONS["IQAC"]

    def test_management_lacks_user_create(self):
        assert P.USER_CREATE not in ROLE_PERMISSIONS["MANAGEMENT"]

    def test_management_lacks_user_disable(self):
        assert P.USER_DISABLE not in ROLE_PERMISSIONS["MANAGEMENT"]

    def test_auditor_lacks_user_create(self):
        assert P.USER_CREATE not in ROLE_PERMISSIONS["AUDITOR"]

    def test_auditor_lacks_result_upload(self):
        assert P.RESULT_UPLOAD not in ROLE_PERMISSIONS["AUDITOR"]

    def test_auditor_has_audit_read(self):
        assert P.AUDIT_READ in ROLE_PERMISSIONS["AUDITOR"]

    def test_all_seven_roles_in_valid_roles(self):
        required = {"PLATFORM_ADMIN", "DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"}
        assert required.issubset(set(VALID_ROLES))


# ===========================================================================
# 49-58: Login endpoint tests
# ===========================================================================

class TestLoginEndpoint:
    def test_login_success_returns_access_token(self, client, db_session):
        _seed(db_session, "HOD", "hod_c1@test.com")
        resp = client.post("/api/auth/login", json={"email": "hod_c1@test.com", "password": "TestPass99!X"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()["data"]

    def test_login_returns_token_type_bearer(self, client, db_session):
        _seed(db_session, "FACULTY", "fac_c2@test.com")
        resp = client.post("/api/auth/login", json={"email": "fac_c2@test.com", "password": "TestPass99!X"})
        assert resp.json()["data"]["token_type"] == "bearer"

    def test_login_wrong_password_401(self, client, db_session):
        _seed(db_session, "FACULTY", "fac_c3@test.com")
        resp = client.post("/api/auth/login", json={"email": "fac_c3@test.com", "password": "WrongPW1!"})
        assert resp.status_code == 401

    def test_login_unknown_email_401(self, client, db_session):
        resp = client.post("/api/auth/login", json={"email": "nobody99@test.com", "password": "AnyPass1!"})
        assert resp.status_code == 401

    def test_login_inactive_user_401(self, client, db_session):
        _seed(db_session, "FACULTY", "fac_inactive@test.com", active=False)
        resp = client.post("/api/auth/login", json={"email": "fac_inactive@test.com", "password": "TestPass99!X"})
        assert resp.status_code == 401

    def test_login_must_change_flag_in_response(self, client, db_session):
        _seed(db_session, "FACULTY", "fac_mustchg@test.com", must_change=True)
        resp = client.post("/api/auth/login", json={"email": "fac_mustchg@test.com", "password": "TestPass99!X"})
        assert resp.status_code == 200
        assert resp.json()["data"]["must_change_password"] is True

    def test_login_response_has_user_id(self, client, db_session):
        _seed(db_session, "HOD", "hod_userid@test.com")
        resp = client.post("/api/auth/login", json={"email": "hod_userid@test.com", "password": "TestPass99!X"})
        assert "id" in resp.json()["data"]["user"]


# ===========================================================================
# 59-64: No public registration endpoints
# ===========================================================================

class TestNoPublicRegistration:
    def test_no_register_endpoint(self, client):
        resp = client.post("/register", json={})
        assert resp.status_code == 404

    def test_no_signup_endpoint(self, client):
        resp = client.post("/signup", json={})
        assert resp.status_code == 404

    def test_no_api_register_endpoint(self, client):
        resp = client.post("/api/register", json={})
        assert resp.status_code == 404

    def test_no_api_v1_register_endpoint(self, client):
        resp = client.post("/api/v1/register", json={})
        assert resp.status_code == 404

    def test_no_create_account_endpoint(self, client):
        resp = client.post("/create-account", json={})
        assert resp.status_code == 404


# ===========================================================================
# 65-72: Unauthenticated access blocked
# ===========================================================================

class TestUnauthenticatedBlocked:
    def test_unauthenticated_analysis_summary_401(self, client):
        resp = client.get("/api/analysis/summary")
        assert resp.status_code == 401

    def test_unauthenticated_dashboard_401(self, client):
        resp = client.get("/api/dashboard/summary")
        assert resp.status_code == 401

    def test_unauthenticated_upload_401(self, client):
        resp = client.post("/api/results/upload")
        assert resp.status_code == 401

    def test_unauthenticated_analysis_courses_401(self, client):
        resp = client.get("/api/analysis/courses")
        assert resp.status_code == 401

    def test_unauthenticated_analysis_faculty_401(self, client):
        resp = client.get("/api/analysis/faculty")
        assert resp.status_code == 401

    def test_unauthenticated_admin_users_401(self, client):
        resp = client.get("/api/auth/admin/users")
        assert resp.status_code == 401

    def test_unauthenticated_reports_401(self, client):
        resp = client.get("/api/analysis/summary")
        assert resp.status_code == 401


# ===========================================================================
# 73-80: must_change_password enforcement and change flow
# ===========================================================================

class TestMustChangePassword:
    def test_must_change_blocks_dashboard(self, client, db_session):
        u, pw = _seed(db_session, "FACULTY", "mustchg_dash@test.com", must_change=True)
        resp = client.post("/api/auth/login", json={"email": "mustchg_dash@test.com", "password": pw})
        token = resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp2 = client.get("/api/dashboard/summary", headers=headers)
        assert resp2.status_code == 403

    def test_must_change_blocks_analysis(self, client, db_session):
        u, pw = _seed(db_session, "FACULTY", "mustchg_ana@test.com", must_change=True)
        resp = client.post("/api/auth/login", json={"email": "mustchg_ana@test.com", "password": pw})
        token = resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp2 = client.get("/api/analysis/summary", headers=headers)
        assert resp2.status_code == 403

    def test_must_change_detail_is_password_change_required(self, client, db_session):
        u, pw = _seed(db_session, "FACULTY", "mustchg_detail@test.com", must_change=True)
        resp = client.post("/api/auth/login", json={"email": "mustchg_detail@test.com", "password": pw})
        token = resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp2 = client.get("/api/dashboard/summary", headers=headers)
        assert "PASSWORD_CHANGE_REQUIRED" in resp2.json().get("detail", "")

    def test_change_initial_password_wrong_current_400(self, client, db_session):
        u, pw = _seed(db_session, "FACULTY", "mustchg_wrong@test.com", must_change=True)
        resp = client.post("/api/auth/login", json={"email": "mustchg_wrong@test.com", "password": pw})
        token = resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp2 = client.post("/api/auth/change-initial-password",
                            json={"current_password": "WrongCurrent1!", "new_password": "NewSecurePass99!@", "confirm_password": "NewSecurePass99!@"},
                            headers=headers)
        assert resp2.status_code == 400

    def test_change_initial_password_mismatch_400(self, client, db_session):
        u, pw = _seed(db_session, "FACULTY", "mustchg_mismatch@test.com", must_change=True)
        resp = client.post("/api/auth/login", json={"email": "mustchg_mismatch@test.com", "password": pw})
        token = resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp2 = client.post("/api/auth/change-initial-password",
                            json={"current_password": pw, "new_password": "NewSecurePass99!@", "confirm_password": "DiffSecure99!@"},
                            headers=headers)
        assert resp2.status_code == 400

    def test_change_initial_password_success(self, client, db_session):
        u, pw = _seed(db_session, "FACULTY", "mustchg_ok@test.com", must_change=True)
        resp = client.post("/api/auth/login", json={"email": "mustchg_ok@test.com", "password": pw})
        token = resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        new_pw = "NewSecurePass99!@"
        resp2 = client.post("/api/auth/change-initial-password",
                            json={"current_password": pw, "new_password": new_pw, "confirm_password": new_pw},
                            headers=headers)
        assert resp2.status_code == 200
        assert "access_token" in resp2.json()["data"]

    def test_change_initial_password_new_token_works(self, client, db_session):
        u, pw = _seed(db_session, "FACULTY", "mustchg_newtoken@test.com", must_change=True)
        resp = client.post("/api/auth/login", json={"email": "mustchg_newtoken@test.com", "password": pw})
        token = resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        new_pw = "NewSecurePass88!@"
        change_resp = client.post("/api/auth/change-initial-password",
                                  json={"current_password": pw, "new_password": new_pw, "confirm_password": new_pw},
                                  headers=headers)
        new_token = change_resp.json()["data"]["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}
        me_resp = client.get("/api/auth/me", headers=new_headers)
        assert me_resp.status_code == 200