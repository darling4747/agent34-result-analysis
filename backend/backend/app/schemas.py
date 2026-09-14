"""Pydantic v2 schemas for Agent 34 — Result Analysis Agent."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Generic wrappers
# ---------------------------------------------------------------------------

class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T
    meta: dict[str, Any] = {}


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool
    data: list[T]
    pagination: PaginationMeta


# ---------------------------------------------------------------------------
# Entity schemas
# ---------------------------------------------------------------------------

class StudentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    roll_number: str
    student_name: str
    programme: Optional[str] = None
    department: Optional[str] = None
    batch: Optional[str] = None
    section: Optional[str] = None
    gender: Optional[str] = None
    category: Optional[str] = None
    admission_category: Optional[str] = None
    entry_qualification: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CourseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_code: str
    course_name: str
    credits: Optional[float] = None
    department: Optional[str] = None
    programme: Optional[str] = None
    semester: Optional[int] = None
    course_type: Optional[str] = None


class FacultySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    faculty_name: str
    employee_id: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None


class ResultSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course_id: int
    faculty_id: Optional[int] = None
    import_batch_id: Optional[int] = None
    semester: int
    academic_year: str
    section: Optional[str] = None
    attempt_number: int = 1
    internal_marks: Optional[float] = None
    external_marks: Optional[float] = None
    total_marks: Optional[float] = None
    grade: Optional[str] = None
    grade_point: Optional[float] = None
    credits: Optional[float] = None
    result_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ImportBatchSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_path: Optional[str] = None
    academic_year: str
    semester: int
    department: Optional[str] = None
    status: str
    total_rows: int = 0
    valid_rows: int = 0
    rejected_rows: int = 0
    warning_rows: int = 0
    error_summary: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_active: bool = False
    student_count: int = 0
    result_count: int = 0
    course_count: int = 0
    analysis_status: str = "PENDING"
    uploaded_by_id: Optional[int] = None


class ValidationErrorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    import_batch_id: int
    row_number: Optional[int] = None
    column_name: Optional[str] = None
    error_code: str
    message: str
    raw_value: Optional[str] = None
    severity: str = "ERROR"
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Analytics response schemas
# ---------------------------------------------------------------------------

class SummaryResponse(BaseModel):
    total_students: int = 0
    total_results: int = 0
    pass_count: int = 0
    fail_count: int = 0
    absent_count: int = 0
    withheld_count: int = 0
    pass_percentage: float = 0.0
    failure_percentage: float = 0.0
    average_marks: Optional[float] = None
    median_marks: Optional[float] = None
    std_dev: Optional[float] = None
    min_marks: Optional[float] = None
    max_marks: Optional[float] = None
    average_gpa: Optional[float] = None
    previous_pass_percentage: Optional[float] = None


class GradeDistributionItem(BaseModel):
    grade: str
    count: int
    percentage: float
    cumulative_percentage: float
    grade_point: Optional[float] = None


class CourseMetrics(BaseModel):
    course_code: str
    course_name: str
    department: Optional[str] = None
    total_students: int = 0
    pass_count: int = 0
    fail_count: int = 0
    absent_count: int = 0
    pass_percentage: float = 0.0
    failure_percentage: float = 0.0
    average_marks: Optional[float] = None
    average_internal: Optional[float] = None
    average_external: Optional[float] = None
    average_gpa: Optional[float] = None
    grade_distribution: list[GradeDistributionItem] = []
    priority_score: Optional[float] = None
    priority_level: Optional[str] = None


class SectionMetrics(BaseModel):
    section: str
    student_count: int = 0
    pass_count: int = 0
    fail_count: int = 0
    absent_count: int = 0
    pass_rate: float = 0.0
    failure_rate: float = 0.0
    avg_marks: Optional[float] = None
    avg_gpa: Optional[float] = None
    top_score: Optional[float] = None
    lowest_score: Optional[float] = None
    section_deviation: Optional[float] = None


class FacultyMetrics(BaseModel):
    faculty_id: Optional[int] = None
    faculty_name: str
    department: Optional[str] = None
    courses_handled: int = 0
    total_students: int = 0
    avg_marks: Optional[float] = None
    pass_rate: Optional[float] = None
    historical_baseline: Optional[float] = None
    deviation: Optional[float] = None
    courses_requiring_review: list[str] = []
    context_note: str = ""


class MeritEntry(BaseModel):
    rank: int
    roll_number: str
    student_name: str
    programme: Optional[str] = None
    section: Optional[str] = None
    batch: Optional[str] = None
    sgpa: float
    cgpa: Optional[float] = None
    total_marks: Optional[float] = None
    status: str = "PASS"


class CorrelationResult(BaseModel):
    course_code: str
    course_name: str
    internal_average: Optional[float] = None
    external_average: Optional[float] = None
    pearson_correlation: Optional[float] = None
    sample_size: int = 0
    interpretation: str = ""
    flags: list[str] = []
    scatter_data: list[dict[str, Any]] = []


class CorrelationFlag(BaseModel):
    course_code: str
    flag: str
    message: str


class HistoricalComparison(BaseModel):
    course_code: str
    course_name: str
    current_pass_rate: Optional[float] = None
    previous_pass_rate: Optional[float] = None
    historical_average: Optional[float] = None
    deviation_from_average: Optional[float] = None
    percentage_change: Optional[float] = None
    trend: str = "UNKNOWN"
    data_points: list[dict[str, Any]] = []


class InterventionCourse(BaseModel):
    course_code: str
    course_name: str
    department: Optional[str] = None
    section: Optional[str] = None
    failure_rate: float = 0.0
    fail_count: int = 0
    total_students: int = 0
    priority_score: float = 0.0
    priority_level: str = "LOW"
    historical_deviation: Optional[float] = None
    section_deviation: Optional[float] = None
    ie_anomaly_score: Optional[float] = None
    weights_used: dict[str, float] = {}
    suggested_action: str = ""


class InterventionSummary(BaseModel):
    total_courses_flagged: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    total_students_at_risk: int = 0
    most_affected_department: Optional[str] = None
    weights_used: dict[str, float] = {}


class ReconciliationResult(BaseModel):
    total_expected: int = 0
    total_uploaded: int = 0
    matched: int = 0
    unmatched: int = 0
    discrepancies: list[dict[str, Any]] = []
    reconciliation_score: float = 0.0


class DataQualityReport(BaseModel):
    overall_score: float = 0.0
    total_records: int = 0
    complete_records: int = 0
    missing_fields_count: int = 0
    duplicate_records: int = 0
    out_of_range_values: int = 0
    grade_total_mismatches: int = 0
    issues: list[dict[str, Any]] = []


class DashboardSummary(BaseModel):
    summary: SummaryResponse
    grade_distribution: list[GradeDistributionItem] = []
    top_intervention_courses: list[InterventionCourse] = []
    section_overview: list[SectionMetrics] = []
    historical_trends: list[HistoricalComparison] = []
    correlation_highlights: list[CorrelationResult] = []


class BacklogEntry(BaseModel):
    roll_number: str
    student_name: str
    programme: Optional[str] = None
    section: Optional[str] = None
    batch: Optional[str] = None
    semester: int
    academic_year: str
    failed_courses: list[dict[str, Any]] = []
    backlog_count: int = 0
    attempt_number: int = 1


class AttainmentEntry(BaseModel):
    course_code: str
    course_name: str
    section: Optional[str] = None
    roll_number: str
    student_name: str
    internal_marks: Optional[float] = None
    external_marks: Optional[float] = None
    total_marks: Optional[float] = None
    grade: Optional[str] = None
    grade_point: Optional[float] = None
    semester: int
    academic_year: str
    credits: Optional[float] = None


class NarrativeResponse(BaseModel):
    summary: str = ""
    key_findings: list[str] = []
    recommendations: list[str] = []
    disclaimer: str = ""
    model_used: str = "deterministic"


class ReportJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    report_path: Optional[str] = None
    report_format: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[int] = None
    department: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None
