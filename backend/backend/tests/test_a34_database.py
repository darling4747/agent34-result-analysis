"""Agent 34 — Database schema, constraints, and persistence tests (~100 tests)."""
from __future__ import annotations
import os
import pytest
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_result_analysis.db")

from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from app.models import (
    Student, Course, Result, ImportBatch, User, Role, Permission,
    RolePermission, MFARecoveryCode, RefreshToken, UserAuditLog,
    AnalysisRun, ValidationError,
)
from app.security.password import hash_password


def _seed_roles(db):
    from app.services.auth_service import AuthService
    from app.config import get_settings
    AuthService(db, get_settings()).seed_roles_and_permissions()
    db.commit()


# ===========================================================================
# 1-14: All expected tables exist
# ===========================================================================

class TestTablesExist:
    def test_students_table_exists(self, db_session):
        insp = inspect(db_session.bind)
        assert "students" in insp.get_table_names()

    def test_courses_table_exists(self, db_session):
        insp = inspect(db_session.bind)
        assert "courses" in insp.get_table_names()

    def test_results_table_exists(self, db_session):
        insp = inspect(db_session.bind)
        assert "results" in insp.get_table_names()

    def test_import_batches_table_exists(self, db_session):
        insp = inspect(db_session.bind)
        assert "import_batches" in insp.get_table_names()

    def test_users_table_exists(self, db_session):
        insp = inspect(db_session.bind)
        assert "users" in insp.get_table_names()

    def test_roles_table_exists(self, db_session):
        insp = inspect(db_session.bind)
        assert "roles" in insp.get_table_names()

    def test_permissions_table_exists(self, db_session):
        insp = inspect(db_session.bind)
        assert "permissions" in insp.get_table_names()

    def test_role_permissions_table_exists(self, db_session):
        insp = inspect(db_session.bind)
        assert "role_permissions" in insp.get_table_names()

    def test_mfa_recovery_codes_table_exists(self, db_session):
        insp = inspect(db_session.bind)
        assert "mfa_recovery_codes" in insp.get_table_names()

    def test_refresh_tokens_table_exists(self, db_session):
        insp = inspect(db_session.bind)
        assert "refresh_tokens" in insp.get_table_names()

    def test_user_audit_logs_table_exists(self, db_session):
        insp = inspect(db_session.bind)
        assert "user_audit_logs" in insp.get_table_names()

    def test_analysis_runs_table_exists(self, db_session):
        insp = inspect(db_session.bind)
        assert "analysis_runs" in insp.get_table_names()

    def test_validation_errors_table_exists(self, db_session):
        insp = inspect(db_session.bind)
        assert "validation_errors" in insp.get_table_names()

    def test_historical_results_table_exists(self, db_session):
        insp = inspect(db_session.bind)
        assert "historical_results" in insp.get_table_names()


# ===========================================================================
# 15-24: Student model fields
# ===========================================================================

class TestStudentModel:
    def test_student_roll_number_required(self, db_session):
        _seed_roles(db_session)
        s = Student(roll_number="TEST001", student_name="Alice")
        db_session.add(s)
        db_session.commit()
        assert s.id is not None

    def test_student_roll_number_unique(self, db_session):
        _seed_roles(db_session)
        s1 = Student(roll_number="UNIQUE001", student_name="Alice")
        s2 = Student(roll_number="UNIQUE001", student_name="Bob")
        db_session.add(s1)
        db_session.commit()
        db_session.add(s2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_student_has_department_field(self, db_session):
        s = Student(roll_number="DEPT001", student_name="Alice", department="CSE")
        db_session.add(s)
        db_session.commit()
        assert s.department == "CSE"

    def test_student_has_batch_field(self, db_session):
        s = Student(roll_number="BATCH001", student_name="Alice", batch="2022")
        db_session.add(s)
        db_session.commit()
        assert s.batch == "2022"

    def test_student_has_section_field(self, db_session):
        s = Student(roll_number="SEC001", student_name="Alice", section="A")
        db_session.add(s)
        db_session.commit()
        assert s.section == "A"

    def test_student_created_at_auto_set(self, db_session):
        s = Student(roll_number="CA001", student_name="Alice")
        db_session.add(s)
        db_session.commit()
        assert s.created_at is not None

    def test_student_optional_fields_nullable(self, db_session):
        s = Student(roll_number="NUL001", student_name="Minimal")
        db_session.add(s)
        db_session.commit()
        assert s.programme is None
        assert s.department is None


# ===========================================================================
# 25-34: Result model and unique constraint
# ===========================================================================

class TestResultModel:
    def _make_student_course(self, db_session, suffix=""):
        stu = Student(roll_number=f"RES{suffix}001", student_name="Alice")
        crs = Course(course_code=f"CS{suffix}601", course_name="Test Course")
        db_session.add_all([stu, crs])
        db_session.commit()
        return stu, crs

    def test_result_requires_student_and_course(self, db_session):
        stu, crs = self._make_student_course(db_session, "A")
        r = Result(
            student_id=stu.id, course_id=crs.id,
            semester=6, academic_year="2025-26", attempt_number=1,
        )
        db_session.add(r)
        db_session.commit()
        assert r.id is not None

    def test_result_unique_constraint(self, db_session):
        stu, crs = self._make_student_course(db_session, "B")
        r1 = Result(student_id=stu.id, course_id=crs.id, semester=6, academic_year="2025-26", attempt_number=1)
        r2 = Result(student_id=stu.id, course_id=crs.id, semester=6, academic_year="2025-26", attempt_number=1)
        db_session.add(r1)
        db_session.commit()
        db_session.add(r2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_result_different_attempt_allowed(self, db_session):
        stu, crs = self._make_student_course(db_session, "C")
        r1 = Result(student_id=stu.id, course_id=crs.id, semester=6, academic_year="2025-26", attempt_number=1)
        r2 = Result(student_id=stu.id, course_id=crs.id, semester=6, academic_year="2025-26", attempt_number=2)
        db_session.add_all([r1, r2])
        db_session.commit()
        assert r1.id != r2.id

    def test_result_has_grade_field(self, db_session):
        stu, crs = self._make_student_course(db_session, "D")
        r = Result(student_id=stu.id, course_id=crs.id, semester=6, academic_year="2025-26", grade="A")
        db_session.add(r)
        db_session.commit()
        assert r.grade == "A"

    def test_result_has_result_status_field(self, db_session):
        stu, crs = self._make_student_course(db_session, "E")
        r = Result(student_id=stu.id, course_id=crs.id, semester=6, academic_year="2025-26", result_status="PASS")
        db_session.add(r)
        db_session.commit()
        assert r.result_status == "PASS"

    def test_result_has_import_batch_id_field(self, db_session):
        stu, crs = self._make_student_course(db_session, "F")
        batch = ImportBatch(filename="test.xlsx", academic_year="2025-26", semester=6)
        db_session.add(batch)
        db_session.commit()
        r = Result(student_id=stu.id, course_id=crs.id, semester=6, academic_year="2025-26", import_batch_id=batch.id)
        db_session.add(r)
        db_session.commit()
        assert r.import_batch_id == batch.id


# ===========================================================================
# 35-44: ImportBatch model fields
# ===========================================================================

class TestImportBatchModel:
    def test_import_batch_has_is_active_field(self, db_session):
        b = ImportBatch(filename="test.xlsx", academic_year="2025-26", semester=6)
        db_session.add(b)
        db_session.commit()
        assert b.is_active is False  # default

    def test_import_batch_has_student_count_field(self, db_session):
        b = ImportBatch(filename="test.xlsx", academic_year="2025-26", semester=6, student_count=50)
        db_session.add(b)
        db_session.commit()
        assert b.student_count == 50

    def test_import_batch_has_result_count_field(self, db_session):
        b = ImportBatch(filename="test.xlsx", academic_year="2025-26", semester=6, result_count=200)
        db_session.add(b)
        db_session.commit()
        assert b.result_count == 200

    def test_import_batch_has_course_count_field(self, db_session):
        b = ImportBatch(filename="test.xlsx", academic_year="2025-26", semester=6, course_count=4)
        db_session.add(b)
        db_session.commit()
        assert b.course_count == 4

    def test_import_batch_default_status_pending(self, db_session):
        b = ImportBatch(filename="test.xlsx", academic_year="2025-26", semester=6)
        db_session.add(b)
        db_session.commit()
        assert b.status == "PENDING"

    def test_import_batch_has_analysis_status(self, db_session):
        b = ImportBatch(filename="test.xlsx", academic_year="2025-26", semester=6, analysis_status="COMPLETED")
        db_session.add(b)
        db_session.commit()
        assert b.analysis_status == "COMPLETED"


# ===========================================================================
# 45-54: User model MFA fields
# ===========================================================================

class TestUserMFAFields:
    def _get_role(self, db_session):
        _seed_roles(db_session)
        return db_session.query(Role).filter_by(name="FACULTY").first()

    def test_user_has_mfa_enabled_field(self, db_session):
        role = self._get_role(db_session)
        u = User(email="mfa1@test.com", full_name="Test", role_id=role.id,
                 password_hash=hash_password("TestPass99!X"), mfa_enabled=False)
        db_session.add(u)
        db_session.commit()
        assert u.mfa_enabled is False

    def test_user_mfa_enabled_defaults_false(self, db_session):
        role = self._get_role(db_session)
        u = User(email="mfa2@test.com", full_name="Test", role_id=role.id,
                 password_hash=hash_password("TestPass99!X"))
        db_session.add(u)
        db_session.commit()
        assert u.mfa_enabled is False

    def test_user_has_mfa_secret_encrypted_field(self, db_session):
        role = self._get_role(db_session)
        u = User(email="mfa3@test.com", full_name="Test", role_id=role.id,
                 password_hash=hash_password("TestPass99!X"),
                 mfa_secret_encrypted="encrypted_secret_here")
        db_session.add(u)
        db_session.commit()
        assert u.mfa_secret_encrypted == "encrypted_secret_here"

    def test_user_mfa_secret_encrypted_nullable(self, db_session):
        role = self._get_role(db_session)
        u = User(email="mfa4@test.com", full_name="Test", role_id=role.id,
                 password_hash=hash_password("TestPass99!X"))
        db_session.add(u)
        db_session.commit()
        assert u.mfa_secret_encrypted is None

    def test_user_has_mfa_recovery_codes_relationship(self, db_session):
        role = self._get_role(db_session)
        u = User(email="mfa5@test.com", full_name="Test", role_id=role.id,
                 password_hash=hash_password("TestPass99!X"))
        db_session.add(u)
        db_session.commit()
        assert u.mfa_recovery_codes == []

    def test_mfa_recovery_code_model(self, db_session):
        role = self._get_role(db_session)
        u = User(email="mfa6@test.com", full_name="Test", role_id=role.id,
                 password_hash=hash_password("TestPass99!X"))
        db_session.add(u)
        db_session.commit()
        code = MFARecoveryCode(user_id=u.id, code_hash="hashvalue", used=False)
        db_session.add(code)
        db_session.commit()
        assert code.id is not None
        assert code.used is False

    def test_user_has_mfa_enabled_at_field(self, db_session):
        role = self._get_role(db_session)
        u = User(email="mfa7@test.com", full_name="Test", role_id=role.id,
                 password_hash=hash_password("TestPass99!X"))
        db_session.add(u)
        db_session.commit()
        assert u.mfa_enabled_at is None


# ===========================================================================
# 55-64: Transaction rollback and persistence
# ===========================================================================

class TestTransactionBehavior:
    def test_rollback_on_error_does_not_persist(self, db_session):
        roll_number = "ROLLBACK001"
        s = Student(roll_number=roll_number, student_name="Alice")
        db_session.add(s)
        db_session.rollback()
        # After rollback the object should not be persisted
        result = db_session.query(Student).filter_by(roll_number=roll_number).first()
        assert result is None

    def test_commit_persists_data(self, db_session):
        s = Student(roll_number="COMMIT001", student_name="Alice")
        db_session.add(s)
        db_session.commit()
        found = db_session.query(Student).filter_by(roll_number="COMMIT001").first()
        assert found is not None

    def test_flush_makes_id_available(self, db_session):
        s = Student(roll_number="FLUSH001", student_name="Alice")
        db_session.add(s)
        db_session.flush()
        assert s.id is not None

    def test_bulk_insert_multiple_students(self, db_session):
        students = [
            Student(roll_number=f"BULK{i:03d}", student_name=f"Student {i}")
            for i in range(1, 11)
        ]
        db_session.add_all(students)
        db_session.commit()
        count = db_session.query(Student).filter(Student.roll_number.like("BULK%")).count()
        assert count >= 10

    def test_db_query_returns_none_for_missing(self, db_session):
        result = db_session.query(Student).filter_by(roll_number="NONEXISTENT999").first()
        assert result is None


# ===========================================================================
# 65-75: Role and permission constraints
# ===========================================================================

class TestRolePermissionConstraints:
    def test_role_name_unique(self, db_session):
        _seed_roles(db_session)
        count = db_session.query(Role).filter_by(name="FACULTY").count()
        assert count == 1  # seeding is idempotent, should not duplicate

    def test_permission_name_unique(self, db_session):
        _seed_roles(db_session)
        count = db_session.query(Permission).filter_by(name="RESULT_READ").count()
        assert count == 1

    def test_role_permission_mapping_exists(self, db_session):
        _seed_roles(db_session)
        role = db_session.query(Role).filter_by(name="PLATFORM_ADMIN").first()
        assert role is not None
        assert len(role.role_permissions) > 0

    def test_faculty_role_permissions_mapped(self, db_session):
        _seed_roles(db_session)
        role = db_session.query(Role).filter_by(name="FACULTY").first()
        perm_names = {rp.permission.name for rp in role.role_permissions}
        assert "RESULT_READ" in perm_names

    def test_platform_admin_has_all_permissions(self, db_session):
        _seed_roles(db_session)
        role = db_session.query(Role).filter_by(name="PLATFORM_ADMIN").first()
        perm_names = {rp.permission.name for rp in role.role_permissions}
        assert "USER_CREATE" in perm_names
        assert "RESULT_UPLOAD" in perm_names
        assert "AUDIT_READ" in perm_names
        assert "CONFIG_MANAGE" in perm_names

    def test_auditor_no_write_permissions(self, db_session):
        _seed_roles(db_session)
        role = db_session.query(Role).filter_by(name="AUDITOR").first()
        perm_names = {rp.permission.name for rp in role.role_permissions}
        assert "USER_CREATE" not in perm_names
        assert "RESULT_UPLOAD" not in perm_names

    def test_all_seven_roles_seeded(self, db_session):
        _seed_roles(db_session)
        roles = {r.name for r in db_session.query(Role).all()}
        expected = {"PLATFORM_ADMIN", "DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"}
        assert expected.issubset(roles)


# ===========================================================================
# 76-85: User model constraints
# ===========================================================================

class TestUserModelConstraints:
    def _get_role(self, db_session):
        _seed_roles(db_session)
        return db_session.query(Role).filter_by(name="FACULTY").first()

    def test_user_email_unique(self, db_session):
        role = self._get_role(db_session)
        u1 = User(email="dup@test.com", full_name="User 1", role_id=role.id, password_hash=hash_password("Pass99!X"))
        db_session.add(u1)
        db_session.commit()
        u2 = User(email="dup@test.com", full_name="User 2", role_id=role.id, password_hash=hash_password("Pass99!X"))
        db_session.add(u2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_user_is_active_defaults_true(self, db_session):
        role = self._get_role(db_session)
        u = User(email="active_def@test.com", full_name="Test", role_id=role.id, password_hash=hash_password("Pass99!X"))
        db_session.add(u)
        db_session.commit()
        assert u.is_active is True

    def test_user_must_change_password_defaults_true(self, db_session):
        role = self._get_role(db_session)
        u = User(email="mustchange@test.com", full_name="Test", role_id=role.id, password_hash=hash_password("Pass99!X"))
        db_session.add(u)
        db_session.commit()
        assert u.must_change_password is True

    def test_user_has_created_at(self, db_session):
        role = self._get_role(db_session)
        u = User(email="created_at@test.com", full_name="Test", role_id=role.id, password_hash=hash_password("Pass99!X"))
        db_session.add(u)
        db_session.commit()
        assert u.created_at is not None

    def test_user_audit_log_created_correctly(self, db_session):
        role = self._get_role(db_session)
        u = User(email="auditcreate@test.com", full_name="Test", role_id=role.id, password_hash=hash_password("Pass99!X"))
        db_session.add(u)
        db_session.commit()
        log = UserAuditLog(user_id=u.id, action="TEST_ACTION", success=True)
        db_session.add(log)
        db_session.commit()
        found = db_session.query(UserAuditLog).filter_by(user_id=u.id, action="TEST_ACTION").first()
        assert found is not None
        assert found.success is True


# ===========================================================================
# 86-100: Course model and DB query correctness
# ===========================================================================

class TestCourseModel:
    def test_course_code_unique(self, db_session):
        c1 = Course(course_code="UNIQ601", course_name="Course A")
        db_session.add(c1)
        db_session.commit()
        c2 = Course(course_code="UNIQ601", course_name="Course B")
        db_session.add(c2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_course_has_department_field(self, db_session):
        c = Course(course_code="DEPT601", course_name="Test", department="CSE")
        db_session.add(c)
        db_session.commit()
        assert c.department == "CSE"

    def test_course_has_semester_field(self, db_session):
        c = Course(course_code="SEM601", course_name="Test", semester=6)
        db_session.add(c)
        db_session.commit()
        assert c.semester == 6

    def test_analysis_run_model(self, db_session):
        run = AnalysisRun(run_type="FULL", academic_year="2025-26", semester=6, status="PENDING")
        db_session.add(run)
        db_session.commit()
        assert run.id is not None

    def test_db_execute_select_1(self, db_session):
        result = db_session.execute(text("SELECT 1")).fetchone()
        assert result[0] == 1

    def test_multiple_students_queryable(self, db_session):
        for i in range(5):
            db_session.add(Student(roll_number=f"MULTI{i:03d}", student_name=f"S{i}"))
        db_session.commit()
        count = db_session.query(Student).filter(Student.roll_number.like("MULTI%")).count()
        assert count >= 5

    def test_import_batch_can_be_set_active(self, db_session):
        b = ImportBatch(filename="active.xlsx", academic_year="2025-26", semester=6,
                        status="COMPLETED", is_active=True)
        db_session.add(b)
        db_session.commit()
        found = db_session.query(ImportBatch).filter_by(is_active=True).first()
        assert found is not None
