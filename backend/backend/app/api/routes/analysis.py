"""Analysis endpoints."""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...config import get_settings
from ...database import get_db
from ...security.permissions import P
from ...security.auth import get_current_active_user, enforce_department_scope, require_permission
from ...schemas import ApiResponse
from ...services.attainment import AttainmentService
from ...services.backlog import BacklogService
from ...services.demographic_analysis import DemographicService
from ...services.faculty_analysis import FacultyAnalysisService
from ...services.merit import MeritService
from ...services.metrics import MetricsService
from ...services.narrative import NarrativeService
from ...services.section_analysis import SectionAnalysisService
from ...services.intervention import InterventionService
from ...models import Course, Result, Student
from ...utils.helpers import nan_safe_dict, nan_safe_list
from ...utils.calculations import compute_pass_percentage

router = APIRouter()


def _build_filters(
    academic_year: Optional[str] = None,
    semester: Optional[int] = None,
    department: Optional[str] = None,
    programme: Optional[str] = None,
    batch: Optional[str] = None,
    section: Optional[str] = None,
    course_code: Optional[str] = None,
    user: Optional[object] = None,
) -> dict:
    if user is not None:
        department = enforce_department_scope(user, department)
    f = {}
    if academic_year:
        f["academic_year"] = academic_year
    if semester is not None:
        f["semester"] = semester
    if department:
        f["department"] = department
    if programme:
        f["programme"] = programme
    if batch:
        f["batch"] = batch
    if section:
        f["section"] = section
    if course_code:
        f["course_code"] = course_code
    return f


@router.get("/summary")
def get_summary(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    programme: Optional[str] = Query(None),
    batch: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    course_code: Optional[str] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    filters = _build_filters(academic_year, semester, department, programme, batch, section, course_code, user=_user)
    svc = MetricsService(db, settings)
    data = svc.get_summary(filters)
    return ApiResponse(success=True, data=nan_safe_dict(data))


@router.get("/grades")
def get_grade_distribution(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    programme: Optional[str] = Query(None),
    batch: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    course_code: Optional[str] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    filters = _build_filters(academic_year, semester, department, programme, batch, section, course_code, user=_user)
    svc = MetricsService(db, settings)
    data = svc.get_grade_distribution(filters)
    return ApiResponse(success=True, data=nan_safe_list(data))


@router.get("/courses")
def get_course_metrics(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    programme: Optional[str] = Query(None),
    batch: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    filters = _build_filters(academic_year, semester, department, programme, batch, section, user=_user)
    metrics_svc = MetricsService(db, settings)
    int_svc = InterventionService(db, settings)

    # Get unique courses
    query = (
        db.query(Course.course_code, Course.course_name, Course.id)
        .join(Result, Result.course_id == Course.id)
        .join(Student, Result.student_id == Student.id)
    )
    if filters.get("academic_year"):
        query = query.filter(Result.academic_year == filters["academic_year"])
    if filters.get("semester"):
        query = query.filter(Result.semester == int(filters["semester"]))
    if filters.get("department"):
        query = query.filter(Student.department == filters["department"])
    courses = query.distinct().all()

    intervention_items = {
        i["course_code"]: i
        for i in int_svc.get_interventions(filters)
    }

    result = []
    for course_code, course_name, _ in courses:
        course_filters = dict(filters)
        course_filters["course_code"] = course_code
        summary = metrics_svc.get_summary(course_filters)
        grade_dist = metrics_svc.get_grade_distribution(course_filters)
        intv = intervention_items.get(course_code, {})
        result.append(nan_safe_dict({
            "course_code": course_code,
            "course_name": course_name,
            "total_students": summary.get("total_students", 0),
            "pass_count": summary.get("pass_count", 0),
            "fail_count": summary.get("fail_count", 0),
            "absent_count": summary.get("absent_count", 0),
            "pass_percentage": summary.get("pass_percentage", 0),
            "failure_percentage": summary.get("failure_percentage", 0),
            "average_marks": summary.get("average_marks"),
            "average_internal": None,  # can be computed per-course from marks svc
            "average_external": None,
            "average_gpa": summary.get("average_gpa"),
            "grade_distribution": grade_dist,
            "priority_score": intv.get("priority_score"),
            "priority_level": intv.get("priority_level"),
        }))

    result.sort(key=lambda x: -(x.get("priority_score") or 0))
    return ApiResponse(success=True, data=result)


@router.get("/sections")
def get_sections(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    programme: Optional[str] = Query(None),
    batch: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    course_code: Optional[str] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    filters = _build_filters(academic_year, semester, department, programme, batch, section, course_code)
    svc = SectionAnalysisService(db, settings)
    data = svc.get_sections(filters)
    return ApiResponse(success=True, data=nan_safe_list(data))


@router.get("/faculty")
def get_faculty(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    _user: object = Depends(require_permission(P.ANALYSIS_FACULTY)),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    filters = _build_filters(academic_year, semester, department)
    svc = FacultyAnalysisService(db, settings)
    data = svc.get_faculty(filters)
    return ApiResponse(success=True, data=nan_safe_list(data))


@router.get("/demographics")
def get_demographics(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    filters = _build_filters(academic_year, semester, department, section=section)
    svc = DemographicService(db, settings)
    data = svc.get_demographics(filters)
    return ApiResponse(success=True, data=nan_safe_list(data))


@router.get("/gpa")
def get_gpa_distribution(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    course_code: Optional[str] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    filters = _build_filters(academic_year, semester, department, section=section, course_code=course_code)
    svc = MetricsService(db, settings)
    data = svc.get_gpa_distribution(filters)
    return ApiResponse(success=True, data=nan_safe_list(data))


@router.get("/merit-list")
def get_merit_list(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    programme: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    course_code: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    filters = _build_filters(academic_year, semester, department, programme, section=section, course_code=course_code)
    svc = MeritService(db, settings)
    data = svc.get_merit_list(filters)
    return ApiResponse(success=True, data=nan_safe_list(data[:limit]))


@router.get("/backlogs")
def get_backlogs(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    course_code: Optional[str] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    filters = _build_filters(academic_year, semester, department, section=section, course_code=course_code)
    svc = BacklogService(db, settings)
    data = svc.get_backlogs(filters)
    return ApiResponse(success=True, data=nan_safe_list(data))


@router.get("/attainment-input")
def get_attainment_input(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    course_code: Optional[str] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    filters = _build_filters(academic_year, semester, department, section=section, course_code=course_code)
    svc = AttainmentService(db, settings)
    data = svc.get_attainment_input(filters)
    return ApiResponse(success=True, data=nan_safe_list(data))


@router.get("/narrative")
@router.post("/narrative/generate")
def auto_generate_narrative(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Auto-collect metrics from the active dataset and generate narrative.
    Metrics are computed deterministically. Gemini only generates narrative text.
    """
    from ...services.correlation import CorrelationService
    from ...services.dataset_service import DatasetService
    settings = get_settings()

    dataset_info = DatasetService(db).get_dataset_info()
    if not dataset_info["has_data"]:
        return ApiResponse(success=True, data={
            "summary": "No result dataset has been uploaded yet.",
            "key_findings": [],
            "recommendations": ["Upload a result dataset to generate analysis."],
            "disclaimer": "",
            "model_used": "none",
        })

    filters = _build_filters(academic_year, semester, department)
    metrics_svc = MetricsService(db, settings)
    intv_svc = InterventionService(db, settings)
    corr_svc = CorrelationService(db, settings)

    period = f"{dataset_info.get('academic_year', '')} Semester {dataset_info.get('semester', '')}"
    metrics = {
        "period": period,
        "dataset": dataset_info,
        "summary": nan_safe_dict(metrics_svc.get_summary(filters)),
        "interventions": nan_safe_list(intv_svc.get_interventions(filters))[:10],
        "correlation": nan_safe_list(corr_svc.get_correlation(filters))[:10],
    }

    svc = NarrativeService(settings)
    result = svc.generate(metrics)
    return ApiResponse(success=True, data=result)


@router.post("/narrative")
def generate_narrative(
    metrics: dict,
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate narrative from provided metrics dict."""
    settings = get_settings()
    svc = NarrativeService(settings)
    result = svc.generate(metrics)
    return ApiResponse(success=True, data=result)
