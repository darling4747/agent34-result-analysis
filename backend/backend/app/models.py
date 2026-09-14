"""SQLAlchemy ORM models for Agent 34 — Result Analysis Agent."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime, ForeignKey,
    UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    roll_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    student_name: Mapped[str] = mapped_column(String(200), nullable=False)
    programme: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    batch: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    section: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    admission_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entry_qualification: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    results: Mapped[List["Result"]] = relationship("Result", back_populates="student")
    historical_results: Mapped[List["HistoricalResult"]] = relationship("HistoricalResult", back_populates="student")

    __table_args__ = (
        Index("ix_students_department_batch", "department", "batch"),
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    course_name: Mapped[str] = mapped_column(String(300), nullable=False)
    credits: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    programme: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    course_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    results: Mapped[List["Result"]] = relationship("Result", back_populates="course")
    historical_results: Mapped[List["HistoricalResult"]] = relationship("HistoricalResult", back_populates="course")
    allocations: Mapped[List["CourseAllocation"]] = relationship("CourseAllocation", back_populates="course")


class Faculty(Base):
    __tablename__ = "faculty"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    faculty_name: Mapped[str] = mapped_column(String(200), nullable=False)
    employee_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True, index=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    results: Mapped[List["Result"]] = relationship("Result", back_populates="faculty")
    allocations: Mapped[List["CourseAllocation"]] = relationship("CourseAllocation", back_populates="faculty")


class CourseAllocation(Base):
    __tablename__ = "course_allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)
    faculty_id: Mapped[int] = mapped_column(Integer, ForeignKey("faculty.id"), nullable=False)
    section: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    academic_year: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    course: Mapped["Course"] = relationship("Course", back_populates="allocations")
    faculty: Mapped["Faculty"] = relationship("Faculty", back_populates="allocations")

    __table_args__ = (
        UniqueConstraint("course_id", "faculty_id", "section", "semester", "academic_year",
                         name="uq_course_allocation"),
    )


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    faculty_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("faculty.id"), nullable=True)
    import_batch_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("import_batches.id"), nullable=True)

    semester: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    section: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    internal_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    external_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    grade_point: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    credits: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    result_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="results")
    course: Mapped["Course"] = relationship("Course", back_populates="results")
    faculty: Mapped[Optional["Faculty"]] = relationship("Faculty", back_populates="results")
    import_batch: Mapped[Optional["ImportBatch"]] = relationship("ImportBatch", back_populates="results")

    __table_args__ = (
        UniqueConstraint(
            "student_id", "course_id", "semester", "academic_year", "attempt_number",
            name="uq_result"
        ),
        Index("ix_results_academic_year_semester", "academic_year", "semester"),
    )


class HistoricalResult(Base):
    __tablename__ = "historical_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("students.id"), nullable=True, index=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False, index=True)

    semester: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    section: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    internal_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    external_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    grade_point: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    result_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    pass_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fail_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pass_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    student: Mapped[Optional["Student"]] = relationship("Student", back_populates="historical_results")
    course: Mapped["Course"] = relationship("Course", back_populates="historical_results")

    __table_args__ = (
        Index("ix_hist_results_academic_year_semester", "academic_year", "semester"),
    )


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    semester: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    student_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    course_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    analysis_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    uploaded_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    results: Mapped[List["Result"]] = relationship("Result", back_populates="import_batch")
    validation_errors: Mapped[List["ValidationError"]] = relationship("ValidationError", back_populates="import_batch")


class ValidationError(Base):
    __tablename__ = "validation_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    import_batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("import_batches.id"), nullable=False, index=True)
    row_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    column_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_code: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="ERROR", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    import_batch: Mapped["ImportBatch"] = relationship("ImportBatch", back_populates="validation_errors")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_type: Mapped[str] = mapped_column(String(50), nullable=False)
    academic_year: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    report_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    report_format: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    metric_version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    filters_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_identifier: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_audit_logs_action_created", "action", "created_at"),
    )


# =============================================================================
# Authentication & RBAC Models
# =============================================================================

class Permission(Base):
    """Fine-grained permission definitions."""
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    role_permissions: Mapped[List["RolePermission"]] = relationship("RolePermission", back_populates="permission")


class Role(Base):
    """Application roles: PLATFORM_ADMIN, DEAN, HOD, FACULTY, IQAC, MANAGEMENT, AUDITOR."""
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    role_permissions: Mapped[List["RolePermission"]] = relationship("RolePermission", back_populates="role")
    users: Mapped[List["User"]] = relationship("User", back_populates="role")


class RolePermission(Base):
    """Maps roles to permissions."""
    __tablename__ = "role_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"), nullable=False, index=True)
    permission_id: Mapped[int] = mapped_column(Integer, ForeignKey("permissions.id"), nullable=False, index=True)

    role: Mapped["Role"] = relationship("Role", back_populates="role_permissions")
    permission: Mapped["Permission"] = relationship("Permission", back_populates="role_permissions")

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )


class User(Base):
    """Platform user account."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(300), nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"), nullable=False)

    # Scope bindings (nullable for roles with broad scope)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    faculty_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("faculty.id"), nullable=True)

    # Auth state
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    temp_password_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # MFA state
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret_encrypted: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    mfa_pending_secret_encrypted: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    mfa_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    mfa_enabled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    faculty_profile: Mapped[Optional["Faculty"]] = relationship("Faculty", foreign_keys=[faculty_id])
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="user")
    audit_logs: Mapped[List["UserAuditLog"]] = relationship("UserAuditLog", back_populates="user")
    mfa_recovery_codes: Mapped[List["MFARecoveryCode"]] = relationship("MFARecoveryCode", back_populates="user", cascade="all, delete-orphan")


class MFARecoveryCode(Base):
    """Hashed recovery codes for TOTP Multi-Factor Authentication."""
    __tablename__ = "mfa_recovery_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="mfa_recovery_codes")


class RefreshToken(Base):
    """Stored refresh token identifier for rotation / revocation."""
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")


class UserAuditLog(Base):
    """Security-relevant audit trail for user actions."""
    __tablename__ = "user_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_user_audit_action_created", "action", "created_at"),
    )
