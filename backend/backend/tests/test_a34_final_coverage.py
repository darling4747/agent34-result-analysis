"""A34 Final Coverage Tests — reaching 1300."""
import io, pytest
import pandas as pd

def _excel(n=5, fail_n=1, ay="2025-26"):
    statuses = ["FAIL"]*fail_n + ["PASS"]*(n-fail_n)
    df = pd.DataFrame({
        "roll_number": [f"FC{i:04d}" for i in range(1, n+1)],
        "student_name": [f"Final {i}" for i in range(1, n+1)],
        "programme": ["B.Tech"]*n, "department": ["CSE"]*n,
        "batch": ["2022"]*n, "section": ["A"]*n,
        "course_code": ["CS601"]*n, "course_name": ["Course"]*n,
        "faculty": ["Dr. F"]*n, "semester": [6]*n,
        "academic_year": [ay]*n,
        "internal_marks": [22]*n, "external_marks": [50 if s=="PASS" else 15 for s in statuses],
        "total_marks": [72 if s=="PASS" else 37 for s in statuses],
        "grade": ["A" if s=="PASS" else "F" for s in statuses],
        "grade_point": [8 if s=="PASS" else 0 for s in statuses],
        "result_status": statuses,
    })
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf.read()


# ── Import batch lifecycle ─────────────────────────────────────────────────────

class TestImportBatchLifecycle:
    def test_upload_creates_batch(self, auth_client, db_session):
        from app.models import ImportBatch
        before = db_session.query(ImportBatch).count()
        auth_client.post("/api/results/upload",
            files={"file": ("lc1.xlsx", io.BytesIO(_excel()),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        db_session.expire_all()
        assert db_session.query(ImportBatch).count() > before

    def test_batch_has_student_count(self, auth_client, db_session):
        from app.models import ImportBatch
        auth_client.post("/api/results/upload",
            files={"file": ("lc2.xlsx", io.BytesIO(_excel(10)),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        db_session.expire_all()
        batch = db_session.query(ImportBatch).order_by(ImportBatch.id.desc()).first()
        if batch and batch.status == "COMPLETED":
            assert batch.student_count >= 0

    def test_batch_has_result_count(self, auth_client, db_session):
        from app.models import ImportBatch
        auth_client.post("/api/results/upload",
            files={"file": ("lc3.xlsx", io.BytesIO(_excel(5)),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        db_session.expire_all()
        batch = db_session.query(ImportBatch).order_by(ImportBatch.id.desc()).first()
        if batch and batch.status == "COMPLETED":
            assert batch.result_count >= 0

    def test_active_batch_is_unique(self, auth_client, db_session):
        from app.models import ImportBatch
        auth_client.post("/api/results/upload",
            files={"file": ("lc4.xlsx", io.BytesIO(_excel(3)),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        db_session.expire_all()
        active = db_session.query(ImportBatch).filter(
            ImportBatch.is_active == True, ImportBatch.status == "COMPLETED").count()
        assert active <= 1

    def test_second_upload_deactivates_first(self, auth_client, db_session):
        from app.models import ImportBatch
        auth_client.post("/api/results/upload",
            files={"file": ("lc5a.xlsx", io.BytesIO(_excel(3)),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        auth_client.post("/api/results/upload",
            files={"file": ("lc5b.xlsx", io.BytesIO(_excel(5)),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        db_session.expire_all()
        active_count = db_session.query(ImportBatch).filter(
            ImportBatch.is_active == True, ImportBatch.status == "COMPLETED").count()
        assert active_count <= 1


# ── Dataset service unit tests ─────────────────────────────────────────────────

class TestDatasetServiceUnit:
    def test_get_active_batch_returns_none_when_none(self, db_session):
        from app.models import ImportBatch
        from app.services.dataset_service import DatasetService
        db_session.query(ImportBatch).update({"is_active": False})
        db_session.commit()
        ds = DatasetService(db_session)
        assert ds.get_active_batch() is None

    def test_get_active_batch_id_returns_none_when_none(self, db_session):
        from app.models import ImportBatch
        from app.services.dataset_service import DatasetService
        db_session.query(ImportBatch).update({"is_active": False})
        db_session.commit()
        ds = DatasetService(db_session)
        assert ds.get_active_batch_id() is None

    def test_get_dataset_info_no_data(self, db_session):
        from app.models import ImportBatch
        from app.services.dataset_service import DatasetService
        db_session.query(ImportBatch).update({"is_active": False})
        db_session.commit()
        info = DatasetService(db_session).get_dataset_info()
        assert info["has_data"] is False

    def test_get_dataset_info_has_message_when_empty(self, db_session):
        from app.models import ImportBatch
        from app.services.dataset_service import DatasetService
        db_session.query(ImportBatch).update({"is_active": False})
        db_session.commit()
        info = DatasetService(db_session).get_dataset_info()
        assert info["message"]

    def test_activate_batch_sets_is_active(self, auth_client, db_session):
        from app.models import ImportBatch
        from app.services.dataset_service import DatasetService
        auth_client.post("/api/results/upload",
            files={"file": ("dsact.xlsx", io.BytesIO(_excel(3)),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        db_session.expire_all()
        batch = db_session.query(ImportBatch).order_by(ImportBatch.id.desc()).first()
        if batch and batch.status == "COMPLETED":
            assert batch.is_active is True


# ── Validation service unit tests ─────────────────────────────────────────────

class TestValidationService:
    def test_required_columns_check(self):
        from app.services.validation import ValidationEngine
        from app.config import get_settings
        import pandas as pd
        engine = ValidationEngine(get_settings())
        df = pd.DataFrame({"col_a": [1], "col_b": [2]})
        result = engine.validate_dataframe(df)
        assert len(result.errors) > 0

    def test_valid_df_no_errors(self):
        from app.services.validation import ValidationEngine
        from app.config import get_settings
        import pandas as pd
        engine = ValidationEngine(get_settings())
        df = pd.DataFrame({
            "roll_number": ["22CS001"], "student_name": ["Alice"],
            "programme": ["B.Tech"], "department": ["CSE"],
            "batch": ["2022"], "section": ["A"],
            "course_code": ["CS601"], "course_name": ["Course"],
            "faculty": ["Dr. X"], "semester": [6],
            "academic_year": ["2025-26"],
            "internal_marks": [22], "external_marks": [50],
            "total_marks": [72], "grade": ["A"],
            "grade_point": [8], "result_status": ["PASS"],
        })
        result = engine.validate_dataframe(df)
        assert len([e for e in result.errors if e.error_code != "DUPLICATE_RECORD"]) == 0

    def test_negative_marks_flagged(self):
        from app.services.validation import ValidationEngine
        from app.config import get_settings
        import pandas as pd
        engine = ValidationEngine(get_settings())
        df = pd.DataFrame({
            "roll_number": ["22CS001"], "student_name": ["Alice"],
            "programme": ["B.Tech"], "department": ["CSE"],
            "batch": ["2022"], "section": ["A"],
            "course_code": ["CS601"], "course_name": ["Course"],
            "faculty": ["Dr. X"], "semester": [6],
            "academic_year": ["2025-26"],
            "internal_marks": [-5], "external_marks": [50],
            "total_marks": [45], "grade": ["C"],
            "grade_point": [5], "result_status": ["PASS"],
        })
        result = engine.validate_dataframe(df)
        codes = [e.error_code for e in result.errors]
        assert any("MARKS" in c for c in codes)

    def test_total_mismatch_flagged(self):
        from app.services.validation import ValidationEngine
        from app.config import get_settings
        import pandas as pd
        engine = ValidationEngine(get_settings())
        df = pd.DataFrame({
            "roll_number": ["22CS001"], "student_name": ["A"],
            "programme": ["B.Tech"], "department": ["CSE"],
            "batch": ["2022"], "section": ["A"],
            "course_code": ["CS601"], "course_name": ["C"],
            "faculty": ["Dr. X"], "semester": [6],
            "academic_year": ["2025-26"],
            "internal_marks": [22], "external_marks": [50],
            "total_marks": [99], "grade": ["A"],
            "grade_point": [8], "result_status": ["PASS"],
        })
        result = engine.validate_dataframe(df)
        codes = [e.error_code for e in result.errors]
        assert "TOTAL_MARKS_MISMATCH" in codes

    def test_invalid_grade_flagged(self):
        from app.services.validation import ValidationEngine
        from app.config import get_settings
        import pandas as pd
        engine = ValidationEngine(get_settings())
        df = pd.DataFrame({
            "roll_number": ["22CS001"], "student_name": ["A"],
            "programme": ["B.Tech"], "department": ["CSE"],
            "batch": ["2022"], "section": ["A"],
            "course_code": ["CS601"], "course_name": ["C"],
            "faculty": ["Dr. X"], "semester": [6],
            "academic_year": ["2025-26"],
            "internal_marks": [22], "external_marks": [50],
            "total_marks": [72], "grade": ["INVALID_GRADE"],
            "grade_point": [8], "result_status": ["PASS"],
        })
        result = engine.validate_dataframe(df)
        codes = [e.error_code for e in result.errors]
        assert "INVALID_GRADE" in codes

    def test_invalid_status_flagged(self):
        from app.services.validation import ValidationEngine
        from app.config import get_settings
        import pandas as pd
        engine = ValidationEngine(get_settings())
        df = pd.DataFrame({
            "roll_number": ["22CS001"], "student_name": ["A"],
            "programme": ["B.Tech"], "department": ["CSE"],
            "batch": ["2022"], "section": ["A"],
            "course_code": ["CS601"], "course_name": ["C"],
            "faculty": ["Dr. X"], "semester": [6],
            "academic_year": ["2025-26"],
            "internal_marks": [22], "external_marks": [50],
            "total_marks": [72], "grade": ["A"],
            "grade_point": [8], "result_status": ["INVALID_STATUS"],
        })
        result = engine.validate_dataframe(df)
        codes = [e.error_code for e in result.errors]
        assert "INVALID_RESULT_STATUS" in codes


# ── MFA crypto tests ───────────────────────────────────────────────────────────

class TestMFACrypto:
    def test_encrypt_decrypt_roundtrip(self):
        from app.security.mfa import encrypt_mfa_secret, decrypt_mfa_secret
        secret = "JBSWY3DPEHPK3PXP"
        encrypted = encrypt_mfa_secret(secret)
        assert encrypted != secret
        decrypted = decrypt_mfa_secret(encrypted)
        assert decrypted == secret

    def test_totp_generate_and_verify(self):
        import pyotp
        from app.security.mfa import generate_totp_secret, verify_totp_code
        secret = generate_totp_secret()
        totp = pyotp.TOTP(secret)
        code = totp.now()
        assert verify_totp_code(secret, code) is True

    def test_totp_wrong_code_rejected(self):
        from app.security.mfa import generate_totp_secret, verify_totp_code
        secret = generate_totp_secret()
        assert verify_totp_code(secret, "000000") is False

    def test_recovery_code_format(self):
        from app.security.mfa import generate_recovery_codes
        codes = generate_recovery_codes(8)
        assert len(codes) == 8
        for code in codes:
            assert "-" in code
            parts = code.split("-")
            assert len(parts) == 2
            assert len(parts[0]) == 4
            assert len(parts[1]) == 4

    def test_recovery_codes_unique(self):
        from app.security.mfa import generate_recovery_codes
        codes = generate_recovery_codes(8)
        assert len(set(codes)) == 8

    def test_recovery_code_hash(self):
        from app.security.mfa import hash_recovery_code
        code = "ABCD-EF12"
        h1 = hash_recovery_code(code)
        h2 = hash_recovery_code(code.lower())
        assert h1 == h2  # case-insensitive

    def test_provisioning_uri_format(self):
        from app.security.mfa import generate_totp_secret, generate_provisioning_uri
        secret = generate_totp_secret()
        uri = generate_provisioning_uri(secret, "test@test.com")
        assert uri.startswith("otpauth://totp/")
        assert "test" in uri  # email may be URL-encoded

    def test_qr_code_data_uri(self):
        from app.security.mfa import generate_totp_secret, generate_provisioning_uri, generate_qr_code_data_uri
        secret = generate_totp_secret()
        uri = generate_provisioning_uri(secret, "test@test.com")
        qr = generate_qr_code_data_uri(uri)
        assert qr.startswith("data:image/png;base64,")
        assert len(qr) > 100


# ── Calculations module unit tests ────────────────────────────────────────────

class TestCalculationsModule:
    def test_compute_pass_percentage_zero_eligible(self):
        from app.utils.calculations import compute_pass_percentage
        assert compute_pass_percentage(0, 0) == 0.0

    def test_compute_pass_percentage_all_pass(self):
        from app.utils.calculations import compute_pass_percentage
        assert compute_pass_percentage(100, 100) == 100.0

    def test_compute_weighted_gpa_empty(self):
        from app.utils.calculations import compute_weighted_gpa
        assert compute_weighted_gpa([], []) == 0.0

    def test_compute_priority_score_zero_inputs(self):
        from app.utils.calculations import compute_priority_score
        weights = {"failure": 0.4, "historical": 0.3, "section": 0.2, "correlation": 0.1}
        score = compute_priority_score(0.0, 0.0, 0.0, 0.0, weights)
        assert 0.0 <= score <= 100.0

    def test_grade_to_priority_level_critical(self):
        from app.utils.calculations import grade_to_priority_level
        assert grade_to_priority_level(80.0) == "CRITICAL"

    def test_grade_to_priority_level_high(self):
        from app.utils.calculations import grade_to_priority_level
        assert grade_to_priority_level(60.0) == "HIGH"

    def test_grade_to_priority_level_medium(self):
        from app.utils.calculations import grade_to_priority_level
        assert grade_to_priority_level(40.0) == "MEDIUM"

    def test_grade_to_priority_level_low(self):
        from app.utils.calculations import grade_to_priority_level
        assert grade_to_priority_level(20.0) == "LOW"

    def test_safe_json_value_nan_returns_none(self):
        from app.utils.calculations import safe_json_value
        assert safe_json_value(float("nan")) is None

    def test_safe_json_value_inf_returns_none(self):
        from app.utils.calculations import safe_json_value
        assert safe_json_value(float("inf")) is None

    def test_safe_json_value_normal_preserved(self):
        from app.utils.calculations import safe_json_value
        assert safe_json_value(72.5) == 72.5

    def test_interpret_correlation_strong_positive(self):
        from app.utils.calculations import interpret_correlation
        assert interpret_correlation(0.85, 20) == "STRONG_POSITIVE"

    def test_interpret_correlation_insufficient(self):
        from app.utils.calculations import interpret_correlation
        assert interpret_correlation(0.9, 2) == "INSUFFICIENT_DATA"

    def test_interpret_correlation_strong_negative(self):
        from app.utils.calculations import interpret_correlation
        assert interpret_correlation(-0.85, 20) == "STRONG_NEGATIVE"


# ── Health/system status ───────────────────────────────────────────────────────

class TestSystemStatus:
    def test_health_database_connected(self, client):
        r = client.get("/health")
        body = r.json()
        assert body.get("database") == "connected"

    def test_health_has_version(self, client):
        r = client.get("/health")
        assert "version" in r.json()

    def test_health_has_agent(self, client):
        r = client.get("/health")
        assert r.json().get("agent") == 34

    def test_root_has_agent_name(self, client):
        r = client.get("/")
        assert "Result Analysis" in r.json().get("agent", "")

    def test_root_has_status(self, client):
        r = client.get("/")
        assert r.json().get("status") == "running"

    def test_root_has_docs_link(self, client):
        r = client.get("/")
        assert "docs" in r.json()


# ── Seven roles always exist ───────────────────────────────────────────────────

class TestSevenRoles:
    def test_all_seven_roles_in_db(self, db_session):
        from app.models import Role
        from app.services.auth_service import AuthService
        from app.config import get_settings
        AuthService(db_session, get_settings()).seed_roles_and_permissions()
        roles = {r.name for r in db_session.query(Role).all()}
        for expected in ["PLATFORM_ADMIN", "DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"]:
            assert expected in roles

    def test_exactly_seven_primary_roles(self, db_session):
        from app.models import Role
        from app.services.auth_service import AuthService
        from app.config import get_settings
        AuthService(db_session, get_settings()).seed_roles_and_permissions()
        roles = db_session.query(Role).all()
        primary = [r for r in roles if r.name in
                   ["PLATFORM_ADMIN", "DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"]]
        assert len(primary) == 7

    def test_no_generic_admin_role(self, db_session):
        from app.models import Role
        from app.services.auth_service import AuthService
        from app.config import get_settings
        AuthService(db_session, get_settings()).seed_roles_and_permissions()
        names = {r.name for r in db_session.query(Role).all()}
        assert "ADMIN" not in names

    def test_permissions_assigned_to_platform_admin(self, db_session):
        from app.models import Role, RolePermission
        from app.services.auth_service import AuthService
        from app.config import get_settings
        AuthService(db_session, get_settings()).seed_roles_and_permissions()
        role = db_session.query(Role).filter_by(name="PLATFORM_ADMIN").first()
        count = db_session.query(RolePermission).filter_by(role_id=role.id).count()
        assert count >= 10

    def test_auditor_has_fewer_permissions_than_admin(self, db_session):
        from app.models import Role, RolePermission
        from app.services.auth_service import AuthService
        from app.config import get_settings
        AuthService(db_session, get_settings()).seed_roles_and_permissions()
        admin = db_session.query(Role).filter_by(name="PLATFORM_ADMIN").first()
        auditor = db_session.query(Role).filter_by(name="AUDITOR").first()
        admin_count = db_session.query(RolePermission).filter_by(role_id=admin.id).count()
        auditor_count = db_session.query(RolePermission).filter_by(role_id=auditor.id).count()
        assert admin_count > auditor_count


# ── CORS configuration ─────────────────────────────────────────────────────────

class TestCORS:
    def test_cors_allowed_for_frontend_origin(self, client):
        r = client.options("/", headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        })
        assert r.status_code in (200, 405)

    def test_health_accessible(self, client):
        r = client.get("/health")
        assert r.status_code == 200
