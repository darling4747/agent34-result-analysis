"""Dashboard summary endpoint."""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...config import get_settings
from ...database import get_db
from ...security.auth import get_current_active_user, enforce_department_scope
from ...schemas import ApiResponse
from ...services.correlation import CorrelationService
from ...services.historical import HistoricalService
from ...services.intervention import InterventionService
from ...services.metrics import MetricsService
from ...services.dataset_service import DatasetService
from ...services.section_analysis import SectionAnalysisService
from ...utils.helpers import nan_safe_dict, nan_safe_list

router = APIRouter()


@router.get("/summary")
def dashboard_summary(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Single combined payload for dashboard:
    summary KPIs, grade_distribution, top_courses, section_overview,
    top_5_interventions, historical_trends, correlation_highlights.
    All in one DB session.
    """
    settings = get_settings()
    filters: dict = {}
    if academic_year:
        filters["academic_year"] = academic_year
    if semester is not None:
        filters["semester"] = semester
    if department:
        filters["department"] = department

    metrics_svc = MetricsService(db, settings)
    section_svc = SectionAnalysisService(db, settings)
    corr_svc = CorrelationService(db, settings)
    hist_svc = HistoricalService(db, settings)
    intv_svc = InterventionService(db, settings)

    summary = nan_safe_dict(metrics_svc.get_summary(filters))
    grade_dist = nan_safe_list(metrics_svc.get_grade_distribution(filters))
    sections = nan_safe_list(section_svc.get_sections(filters))
    interventions = nan_safe_list(intv_svc.get_interventions(filters))
    historical = nan_safe_list(hist_svc.get_historical(filters))
    correlation = nan_safe_list(corr_svc.get_correlation(filters))

    # Top 5 interventions
    top_interventions = interventions[:5]

    # Correlation highlights — courses with flags
    corr_highlights = [c for c in correlation if c.get("flags")][:5]

    dataset_info = DatasetService(db).get_dataset_info()
    if not dataset_info["has_data"]:
        return ApiResponse(
            success=True,
            data={"no_data": True, "message": "No result dataset uploaded yet.", "dataset_info": dataset_info}
        )

    return ApiResponse(
        success=True,
        data={
            "dataset_info": dataset_info,
            "summary": summary,
            "grade_distribution": grade_dist,
            "section_overview": sections,
            "top_intervention_courses": top_interventions,
            "historical_trends": historical,
            "correlation_highlights": corr_highlights,
        },
    )