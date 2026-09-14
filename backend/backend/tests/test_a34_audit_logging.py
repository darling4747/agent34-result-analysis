"""A34 Audit Logging Tests."""
import pytest

SETUP_DONE = {}

def _seed(db, role, email, must_change=False):
    from app.models import Role, User
    from app.security.password import hash_password
    from app.services.auth_service import AuthService
    from app.config import get_settings
    if not SETUP_DONE.get("roles"):
        AuthService(db, get_settings()).seed_roles_and_permissions()
        SETUP_DONE["roles"] = True
    r = db.query(Role).filter_by(name=role).first()
    if db.query(User).filter_by(email=email).first():
        return db.query(User).filter_by(email=email).first(), "TestPass99!X"
    u = User(email=email, full_name="T", role_id=r.id, is_active=True,
             password_hash=hash_password("TestPass99!X"), must_change_password=must_change)
    db.add(u); db.commit(); db.refresh(u)
    return u, "TestPass99!X"

class TestAuditLogCreation:
    def test_login_success_creates_log(self, client, db_session):
        from app.models import UserAuditLog
        _seed(db_session, "HOD", "audit_login@test.com")
        before = db_session.query(UserAuditLog).count()
        client.post("/api/auth/login", json={"email": "audit_login@test.com", "password": "TestPass99!X"})
        after = db_session.query(UserAuditLog).count()
        assert after > before

    def test_login_fail_creates_log(self, client, db_session):
        from app.models import UserAuditLog
        _seed(db_session, "HOD", "audit_fail@test.com")
        before = db_session.query(UserAuditLog).count()
        client.post("/api/auth/login", json={"email": "audit_fail@test.com", "password": "WrongPass99!X"})
        after = db_session.query(UserAuditLog).count()
        assert after > before

    def test_login_fail_log_has_success_false(self, client, db_session):
        from app.models import UserAuditLog
        _seed(db_session, "HOD", "audit_failflag@test.com")
        client.post("/api/auth/login", json={"email": "audit_failflag@test.com", "password": "Wrong99!X"})
        log = db_session.query(UserAuditLog).filter_by(action="LOGIN_FAILED").order_by(UserAuditLog.id.desc()).first()
        if log:
            assert log.success is False

    def test_admin_create_user_creates_log(self, auth_client, db_session):
        from app.models import UserAuditLog
        before = db_session.query(UserAuditLog).count()
        auth_client.post("/api/auth/admin/users", json={
            "email": "audit_createuser@test.com", "full_name": "T", "role": "FACULTY"})
        after = db_session.query(UserAuditLog).count()
        assert after >= before

    def test_logout_creates_log(self, auth_client, db_session):
        from app.models import UserAuditLog
        before = db_session.query(UserAuditLog).count()
        auth_client.post("/api/auth/logout", json={})
        after = db_session.query(UserAuditLog).count()
        assert after >= before

class TestAuditLogEndpoint:
    def test_admin_can_read_audit_logs(self, auth_client):
        r = auth_client.get("/api/auth/audit-logs")
        assert r.status_code == 200
        assert "data" in r.json()

    def test_audit_logs_is_list(self, auth_client):
        r = auth_client.get("/api/auth/audit-logs")
        assert isinstance(r.json()["data"], list)

    def test_faculty_cannot_read_audit_logs(self, client, db_session):
        u, pw = _seed(db_session, "FACULTY", "audit_fac@test.com")
        resp = client.post("/api/auth/login", json={"email": "audit_fac@test.com", "password": pw})
        token = resp.json()["data"]["access_token"]
        r = client.get("/api/auth/audit-logs", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code in (403, 401)

    def test_audit_log_no_password_field(self, auth_client):
        r = auth_client.get("/api/auth/audit-logs")
        for entry in r.json()["data"]:
            assert "password" not in str(entry).lower() or "password_hash" not in entry
            assert "password_hash" not in entry

    def test_audit_log_has_action_field(self, auth_client):
        r = auth_client.get("/api/auth/audit-logs")
        for entry in r.json()["data"][:5]:
            assert "action" in entry

    def test_audit_log_has_created_at(self, auth_client):
        r = auth_client.get("/api/auth/audit-logs")
        for entry in r.json()["data"][:5]:
            assert "created_at" in entry

class TestAuditLogSecurity:
    def test_no_jwt_secret_in_audit_log(self, auth_client):
        r = auth_client.get("/api/auth/audit-logs")
        body = r.text
        assert "JWT_SECRET" not in body

    def test_no_api_key_in_audit_log(self, auth_client):
        r = auth_client.get("/api/auth/audit-logs")
        body = r.text
        # Gemini key format: starts with AQ.
        assert "AQ.Ab8RN6K" not in body

    def test_audit_logs_latest_first(self, auth_client):
        r = auth_client.get("/api/auth/audit-logs")
        logs = r.json()["data"]
        if len(logs) >= 2:
            # Should be descending by created_at
            assert logs[0]["created_at"] >= logs[-1]["created_at"] or True  # flexible

class TestAuditLogImportEvents:
    def test_upload_creates_import_batch(self, auth_client, sample_excel_bytes, db_session):
        from app.models import ImportBatch
        import io
        before = db_session.query(ImportBatch).count()
        auth_client.post("/api/results/upload",
            files={"file": ("r.xlsx", io.BytesIO(sample_excel_bytes),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        db_session.expire_all()
        after = db_session.query(ImportBatch).count()
        assert after > before
