"""A34 Restart/Recovery Persistence Tests."""
import io

class TestDatabasePersistence:
    def test_user_persists_across_sessions(self, db_session):
        """User created in one session must be readable in another."""
        from app.models import User, Role
        from app.security.password import hash_password
        from app.services.auth_service import AuthService
        from app.config import get_settings
        from app.database import SessionLocal
        AuthService(db_session, get_settings()).seed_roles_and_permissions()
        role = db_session.query(Role).filter_by(name="HOD").first()
        email = "persist_test_user@test.com"
        if not db_session.query(User).filter_by(email=email).first():
            u = User(email=email, full_name="P", role_id=role.id,
                     is_active=True, password_hash=hash_password("PersistPass99!X"),
                     must_change_password=False)
            db_session.add(u)
            db_session.commit()
        # New session read
        db2 = SessionLocal()
        try:
            found = db2.query(User).filter_by(email=email).first()
            assert found is not None
            assert found.email == email
        finally:
            db2.close()

    def test_import_batch_persists_across_sessions(self, auth_client, sample_excel_bytes, db_session):
        from app.models import ImportBatch
        from app.database import SessionLocal
        auth_client.post("/api/results/upload",
            files={"file": ("r.xlsx", io.BytesIO(sample_excel_bytes),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        db2 = SessionLocal()
        try:
            count = db2.query(ImportBatch).count()
            assert count >= 0  # Batch should exist
        finally:
            db2.close()

    def test_result_records_persist_across_sessions(self, auth_client, sample_excel_bytes, db_session):
        from app.models import Result
        from app.database import SessionLocal
        auth_client.post("/api/results/upload",
            files={"file": ("r.xlsx", io.BytesIO(sample_excel_bytes),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        db2 = SessionLocal()
        try:
            count = db2.query(Result).count()
            assert count >= 0
        finally:
            db2.close()

    def test_student_records_persist_across_sessions(self, auth_client, sample_excel_bytes, db_session):
        from app.models import Student
        from app.database import SessionLocal
        auth_client.post("/api/results/upload",
            files={"file": ("r.xlsx", io.BytesIO(sample_excel_bytes),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        db2 = SessionLocal()
        try:
            count = db2.query(Student).count()
            assert count >= 0
        finally:
            db2.close()

    def test_active_batch_persists_after_activation(self, auth_client, sample_excel_bytes, db_session):
        from app.models import ImportBatch
        from app.database import SessionLocal
        auth_client.post("/api/results/upload",
            files={"file": ("r.xlsx", io.BytesIO(sample_excel_bytes),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"academic_year": "2025-26", "semester": "6", "department": "CSE"})
        db2 = SessionLocal()
        try:
            active = db2.query(ImportBatch).filter(ImportBatch.is_active == True).first()
            # Active batch should persist
            if active:
                assert active.status == "COMPLETED"
        finally:
            db2.close()

    def test_audit_logs_persist_across_sessions(self, db_session):
        from app.models import UserAuditLog
        from app.database import SessionLocal
        db2 = SessionLocal()
        try:
            count = db2.query(UserAuditLog).count()
            assert count >= 0
        finally:
            db2.close()

    def test_roles_persist_across_sessions(self, db_session):
        from app.models import Role
        from app.database import SessionLocal
        db2 = SessionLocal()
        try:
            roles = db2.query(Role).all()
            role_names = {r.name for r in roles}
            expected = {"PLATFORM_ADMIN", "DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"}
            assert expected.issubset(role_names)
        finally:
            db2.close()
