"""A34 Security Tests."""
import io

class TestNoSensitiveDataLeakage:
    def test_no_password_hash_in_user_list(self, auth_client):
        r = auth_client.get("/api/auth/admin/users")
        assert r.status_code == 200
        for u in r.json()["data"]:
            assert "password_hash" not in u

    def test_no_temp_password_in_user_list(self, auth_client):
        r = auth_client.get("/api/auth/admin/users")
        for u in r.json()["data"]:
            assert "temporary_password" not in u or u.get("temporary_password") is None

    def test_no_password_in_me_response(self, auth_client):
        r = auth_client.get("/api/auth/me")
        body = str(r.json())
        assert "password_hash" not in body

    def test_no_jwt_secret_in_health(self, client):
        r = client.get("/health")
        body = r.text
        assert "JWT_SECRET" not in body
        assert "Ewx6vZ" not in body  # partial of the actual secret

    def test_no_database_url_in_health(self, client):
        r = client.get("/health")
        assert "postgresql" not in r.text.lower() or "database_url" not in r.text.lower()

    def test_no_gemini_key_in_narrative(self, auth_client, db_session):
        from app.models import ImportBatch
        db_session.query(ImportBatch).update({"is_active": False})
        db_session.commit()
        r = auth_client.post("/api/analysis/narrative/generate")
        assert "AQ.Ab8RN6K" not in r.text

class TestAuthenticationSecurity:
    def test_bcrypt_hash_not_plaintext(self):
        from app.security.password import hash_password
        h = hash_password("TestPass99!X")
        assert not h.startswith("TestPass")
        assert "$" in h

    def test_bcrypt_verify_correct(self):
        from app.security.password import hash_password, verify_password
        pw = "SecurePass99!X"
        assert verify_password(pw, hash_password(pw)) is True

    def test_bcrypt_verify_wrong(self):
        from app.security.password import hash_password, verify_password
        assert verify_password("Wrong99!X", hash_password("Right99!X")) is False

    def test_jwt_structure(self):
        from app.security.tokens import create_access_token, decode_access_token
        tok = create_access_token(99, "t@t.com", "HOD", ["RESULT_READ"])
        payload = decode_access_token(tok)
        assert payload["user_id"] == 99
        assert payload["role"] == "HOD"
        assert "exp" in payload
        assert "jti" in payload

    def test_tampered_jwt_rejected(self):
        from app.security.tokens import create_access_token, TokenError
        tok = create_access_token(1, "t@t.com", "HOD", [])
        tampered = tok[:-5] + "XXXXX"
        with pytest.raises(TokenError):
            from app.security.tokens import decode_access_token
            decode_access_token(tampered)

    def test_garbage_jwt_rejected(self):
        from app.security.tokens import decode_access_token, TokenError
        with pytest.raises(TokenError):
            decode_access_token("not.a.jwt.token")

    def test_temp_password_unique_per_generation(self):
        from app.security.password import generate_temp_password
        passwords = {generate_temp_password() for _ in range(20)}
        assert len(passwords) == 20

    def test_temp_password_length(self):
        from app.security.password import generate_temp_password
        for _ in range(10):
            assert len(generate_temp_password()) >= 16

    def test_temp_password_complexity(self):
        from app.security.password import generate_temp_password
        import re
        for _ in range(10):
            pw = generate_temp_password()
            assert re.search(r"[A-Z]", pw), f"No uppercase: {pw}"
            assert re.search(r"[a-z]", pw), f"No lowercase: {pw}"
            assert re.search(r"\d", pw), f"No digit: {pw}"

class TestRBACEnforcement:
    def test_no_register_404(self, client):
        assert client.post("/register", json={}).status_code == 404

    def test_no_signup_404(self, client):
        assert client.post("/signup", json={}).status_code == 404

    def test_unauthenticated_all_analytics_401(self, client):
        endpoints = [
            "/api/analysis/summary", "/api/analysis/grades",
            "/api/analysis/courses", "/api/analysis/sections",
            "/api/analysis/faculty", "/api/analysis/merit-list",
            "/api/analysis/correlation", "/api/analysis/historical",
            "/api/analysis/interventions", "/api/analysis/backlogs",
            "/api/dashboard/summary",
        ]
        for ep in endpoints:
            r = client.get(ep)
            assert r.status_code == 401, f"{ep} returned {r.status_code}"

class TestFileUploadSecurity:
    def test_txt_file_rejected(self, auth_client):
        r = auth_client.post("/api/results/upload",
            files={"file": ("bad.txt", io.BytesIO(b"text"), "text/plain")},
            data={"academic_year": "2025-26", "semester": "6"})
        assert r.status_code == 400

    def test_exe_file_rejected(self, auth_client):
        r = auth_client.post("/api/results/upload",
            files={"file": ("bad.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
            data={"academic_year": "2025-26", "semester": "6"})
        assert r.status_code == 400

import pytest
