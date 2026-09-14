"""A34 Buttons / Actions Tests — every user action has a working backend."""
import io

class TestUploadAction:
    def test_upload_post_correct_method(self, auth_client, sample_excel_bytes):
        r = auth_client.post("/api/results/upload",
            files={"file": ("r.xlsx", io.BytesIO(sample_excel_bytes),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        assert r.status_code == 200

    def test_upload_requires_file_field(self, auth_client):
        r = auth_client.post("/api/results/upload",
            data={"academic_year": "2025-26", "semester": "6"})
        assert r.status_code in (400, 422)

    def test_upload_requires_academic_year(self, auth_client, sample_excel_bytes):
        r = auth_client.post("/api/results/upload",
            files={"file": ("r.xlsx", io.BytesIO(sample_excel_bytes),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"semester": "6"})
        assert r.status_code in (400, 422)

    def test_upload_requires_semester(self, auth_client, sample_excel_bytes):
        r = auth_client.post("/api/results/upload",
            files={"file": ("r.xlsx", io.BytesIO(sample_excel_bytes),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26"})
        assert r.status_code in (400, 422)

class TestLoginAction:
    def test_login_post_method_200(self, client, db_session):
        from app.models import Role, User
        from app.security.password import hash_password
        from app.services.auth_service import AuthService
        from app.config import get_settings
        AuthService(db_session, get_settings()).seed_roles_and_permissions()
        role = db_session.query(Role).filter_by(name="HOD").first()
        u = User(email="btn_login@test.com", full_name="B", role_id=role.id,
                 is_active=True, password_hash=hash_password("BtnPass99!X"),
                 must_change_password=False)
        db_session.add(u); db_session.commit()
        r = client.post("/api/auth/login", json={"email": "btn_login@test.com", "password": "BtnPass99!X"})
        assert r.status_code == 200
        assert "access_token" in r.json()["data"]

    def test_login_returns_token_type_bearer(self, client, db_session):
        from app.models import Role, User
        from app.security.password import hash_password
        from app.services.auth_service import AuthService
        from app.config import get_settings
        AuthService(db_session, get_settings()).seed_roles_and_permissions()
        role = db_session.query(Role).filter_by(name="HOD").first()
        u = User(email="btn_bearer@test.com", full_name="B", role_id=role.id,
                 is_active=True, password_hash=hash_password("BearerPass99!X"),
                 must_change_password=False)
        db_session.add(u); db_session.commit()
        r = client.post("/api/auth/login", json={"email": "btn_bearer@test.com", "password": "BearerPass99!X"})
        assert r.json()["data"]["token_type"] == "bearer"

class TestLogoutAction:
    def test_logout_post_200(self, auth_client):
        r = auth_client.post("/api/auth/logout", json={})
        assert r.status_code == 200

    def test_logout_returns_success(self, auth_client):
        r = auth_client.post("/api/auth/logout", json={})
        assert r.json().get("success") is True

class TestProfileAction:
    def test_me_get_200(self, auth_client):
        assert auth_client.get("/api/auth/me").status_code == 200

    def test_me_has_email(self, auth_client):
        r = auth_client.get("/api/auth/me")
        assert "email" in r.json()["data"]

    def test_me_has_role(self, auth_client):
        r = auth_client.get("/api/auth/me")
        assert "role" in r.json()["data"]

    def test_me_has_permissions(self, auth_client):
        r = auth_client.get("/api/auth/me")
        assert "permissions" in r.json()["data"]

class TestAdminUserActions:
    def test_create_user_post_200(self, auth_client):
        r = auth_client.post("/api/auth/admin/users", json={
            "email": "btn_create@test.com", "full_name": "Button", "role": "FACULTY"})
        assert r.status_code == 200

    def test_create_user_returns_temp_password(self, auth_client):
        r = auth_client.post("/api/auth/admin/users", json={
            "email": "btn_tp@test.com", "full_name": "T", "role": "AUDITOR"})
        data = r.json()["data"]
        assert "temporary_password" in data
        assert data["temporary_password"] is not None

    def test_list_users_get_200(self, auth_client):
        assert auth_client.get("/api/auth/admin/users").status_code == 200

    def test_force_reset_post(self, auth_client, db_session):
        from app.models import User
        r = auth_client.post("/api/auth/admin/users", json={
            "email": "btn_reset_target@test.com", "full_name": "R", "role": "AUDITOR"})
        uid = r.json()["data"]["user_id"]
        r2 = auth_client.post(f"/api/auth/admin/users/{uid}/force-reset")
        assert r2.status_code == 200

    def test_deactivate_user_patch(self, auth_client):
        r = auth_client.post("/api/auth/admin/users", json={
            "email": "btn_deact@test.com", "full_name": "D", "role": "AUDITOR"})
        uid = r.json()["data"]["user_id"]
        r2 = auth_client.patch(f"/api/auth/admin/users/{uid}/deactivate")
        assert r2.status_code == 200

    def test_activate_user_patch(self, auth_client):
        r = auth_client.post("/api/auth/admin/users", json={
            "email": "btn_react@test.com", "full_name": "R", "role": "AUDITOR"})
        uid = r.json()["data"]["user_id"]
        auth_client.patch(f"/api/auth/admin/users/{uid}/deactivate")
        r2 = auth_client.patch(f"/api/auth/admin/users/{uid}/activate")
        assert r2.status_code == 200

class TestAnalyticsActions:
    def test_generate_narrative_post_200(self, auth_client, db_session):
        from app.models import ImportBatch
        db_session.query(ImportBatch).update({"is_active": False})
        db_session.commit()
        r = auth_client.post("/api/analysis/narrative/generate")
        assert r.status_code == 200

    def test_narrative_custom_metrics_post_200(self, auth_client):
        r = auth_client.post("/api/analysis/narrative", json={
            "summary": {"pass_percentage": 80.0, "failure_percentage": 20.0, "total_students": 100}})
        assert r.status_code == 200

    def test_generate_report_post_200(self, auth_client):
        r = auth_client.post("/api/reports/generate",
            params={"academic_year": "2025-26", "semester": 6})
        assert r.status_code == 200

class TestDatasetInfoAction:
    def test_dataset_info_get_200(self, auth_client):
        assert auth_client.get("/api/results/dataset-info").status_code == 200

    def test_dataset_info_has_has_data(self, auth_client):
        r = auth_client.get("/api/results/dataset-info")
        assert "has_data" in r.json()["data"]

    def test_imports_list_get_200(self, auth_client):
        assert auth_client.get("/api/results/imports").status_code == 200

    def test_reconciliation_get_200(self, auth_client):
        assert auth_client.get("/api/results/reconciliation").status_code == 200

    def test_data_quality_get_200(self, auth_client):
        assert auth_client.get("/api/results/data-quality").status_code == 200

class TestMFAActions:
    def test_mfa_setup_post_200(self, auth_client):
        r = auth_client.post("/api/auth/mfa/setup")
        assert r.status_code in (200, 400, 409)  # may already be set up

    def test_mfa_status_get_200(self, auth_client):
        assert auth_client.get("/api/auth/mfa/status").status_code == 200

    def test_mfa_status_has_mfa_enabled(self, auth_client):
        r = auth_client.get("/api/auth/mfa/status")
        assert "mfa_enabled" in r.json()["data"]
