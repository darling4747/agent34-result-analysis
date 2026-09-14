"""Unit tests for TOTP Multi-Factor Authentication (MFA)."""
import pytest
import pyotp
from app.security.mfa import decrypt_mfa_secret


def test_mfa_setup_flow(auth_client):
    """Test generating TOTP setup secret, QR code, and recovery codes."""
    resp = auth_client.post("/api/auth/mfa/setup")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "secret" in data
    assert "provisioning_uri" in data
    assert data["qr_code_data_uri"].startswith("data:image/png;base64,")
    assert len(data["recovery_codes"]) == 8


def test_mfa_verify_setup_and_login_challenge(auth_client, client, db_session):
    """Test activating MFA and logging in with TOTP verification."""
    # 1. Initiate setup
    setup_resp = auth_client.post("/api/auth/mfa/setup")
    setup_data = setup_resp.json()["data"]
    secret = setup_data["secret"]
    recovery_codes = setup_data["recovery_codes"]

    # Generate valid 6-digit TOTP code
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()

    # 2. Verify setup
    verify_resp = auth_client.post(
        "/api/auth/mfa/verify-setup",
        json={"totp_code": valid_code, "recovery_codes": recovery_codes},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["data"]["mfa_enabled"] is True

    # 3. Check MFA status
    status_resp = auth_client.get("/api/auth/mfa/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["data"]["mfa_enabled"] is True

    # 4. Attempt login with password -> expect mfa_required=True
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "fixture_admin@test.com", "password": "FixturePass99!X"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()["data"]
    assert login_data["mfa_required"] is True
    mfa_token = login_data["mfa_token"]

    # 5. Complete MFA login with TOTP code
    code_now = totp.now()
    mfa_verify_resp = client.post(
        "/api/auth/mfa/verify",
        json={"mfa_token": mfa_token, "totp_code": code_now},
    )
    assert mfa_verify_resp.status_code == 200
    final_data = mfa_verify_resp.json()["data"]
    assert "access_token" in final_data
    assert final_data["user"]["mfa_enabled"] is True


def test_mfa_login_with_recovery_code(auth_client, client):
    """Test logging in using a single-use recovery code."""
    # Setup MFA
    setup_data = auth_client.post("/api/auth/mfa/setup").json()["data"]
    secret = setup_data["secret"]
    recovery_codes = setup_data["recovery_codes"]
    totp_code = pyotp.TOTP(secret).now()

    auth_client.post(
        "/api/auth/mfa/verify-setup",
        json={"totp_code": totp_code, "recovery_codes": recovery_codes},
    )

    # Login to get MFA token
    login_data = client.post(
        "/api/auth/login",
        json={"email": "fixture_admin@test.com", "password": "FixturePass99!X"},
    ).json()["data"]
    mfa_token = login_data["mfa_token"]

    # Use first recovery code
    used_rec_code = recovery_codes[0]
    rec_resp = client.post(
        "/api/auth/mfa/verify",
        json={"mfa_token": mfa_token, "recovery_code": used_rec_code},
    )
    assert rec_resp.status_code == 200
    assert "access_token" in rec_resp.json()["data"]

    # Re-using the same recovery code must fail
    login_data2 = client.post(
        "/api/auth/login",
        json={"email": "fixture_admin@test.com", "password": "FixturePass99!X"},
    ).json()["data"]
    mfa_token2 = login_data2["mfa_token"]

    fail_resp = client.post(
        "/api/auth/mfa/verify",
        json={"mfa_token": mfa_token2, "recovery_code": used_rec_code},
    )
    assert fail_resp.status_code == 401


def test_admin_mfa_reset(auth_client, client):
    """Test admin resetting MFA for a user who lost their device."""
    # Setup MFA
    setup_data = auth_client.post("/api/auth/mfa/setup").json()["data"]
    totp_code = pyotp.TOTP(setup_data["secret"]).now()
    auth_client.post(
        "/api/auth/mfa/verify-setup",
        json={"totp_code": totp_code, "recovery_codes": setup_data["recovery_codes"]},
    )

    # Get admin user ID
    me_resp = auth_client.get("/api/auth/me")
    user_id = me_resp.json()["data"]["id"]

    # Reset MFA as admin
    reset_resp = auth_client.post(f"/api/auth/admin/users/{user_id}/mfa/reset")
    assert reset_resp.status_code == 200

    # Status should now be mfa_enabled=False
    status_resp = auth_client.get("/api/auth/mfa/status")
    assert status_resp.json()["data"]["mfa_enabled"] is False
