"""Report generation routes."""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ...config import get_settings
from ...database import get_db
from ...security.permissions import P
from ...security.auth import get_current_active_user, enforce_department_scope, require_permission
from ...models import AnalysisRun
from ...schemas import ApiResponse, ReportJobResponse
from ...services.attainment import AttainmentService
from ...services.backlog import BacklogService
from ...services.correlation import CorrelationService
from ...services.faculty_analysis import FacultyAnalysisService
from ...services.historical import HistoricalService
from ...services.intervention import InterventionService
from ...services.merit import MeritService
from ...services.metrics import MetricsService
from ...services.narrative import NarrativeService
from ...services.report_generator import ReportGenerator
from ...services.section_analysis import SectionAnalysisService
from ...utils.helpers import nan_safe_dict, nan_safe_list

router = APIRouter()


@router.post("/generate", response_model=ApiResponse[ReportJobResponse])
def generate_report(
    academic_year: str = Query(...),
    semester: int = Query(...),
    department: str = Query("All Departments"),
    report_type: str = Query("FULL"),
    format: str = Query("PDF"),
    _user: object = Depends(require_permission(P.REPORT_GENERATE)),
    db: Session = Depends(get_db),
):
    """Generate a comprehensive PDF report."""
    settings = get_settings()
    filters: dict = {"academic_year": academic_year, "semester": semester}
    if department and department != "All Departments":
        filters["department"] = department

    # Create the run record
    run = AnalysisRun(
        run_type=report_type,
        academic_year=academic_year,
        semester=semester,
        department=department if department != "All Departments" else None,
        status="RUNNING",
        report_format=format,
        filters_used=json.dumps(filters),
    )
    db.add(run)
    db.flush()

    try:
        metrics = _build_full_metrics(db, settings, filters, academic_year, semester, department)

        generator = ReportGenerator(settings)
        filepath = generator.generate(
            metrics=metrics,
            run_id=run.id,
            academic_year=academic_year,
            semester=semester,
            department=department,
        )

        run.status = "COMPLETED"
        run.report_path = filepath
        run.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as exc:
        run.status = "FAILED"
        run.error_message = str(exc)[:500]
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    return ApiResponse(
        success=True,
        data=ReportJobResponse(
            id=run.id,
            status=run.status,
            report_path=run.report_path,
            report_format=run.report_format,
            academic_year=run.academic_year,
            semester=run.semester,
            department=run.department,
            created_at=run.created_at,
            completed_at=run.completed_at,
            download_url=f"/api/reports/{run.id}/download",
        ),
    )


@router.get("/{report_id}", response_model=ApiResponse[ReportJobResponse])
def get_report_status(report_id: int, db: Session = Depends(get_db)):
    """Get the status of a report generation job."""
    run = db.query(AnalysisRun).filter(AnalysisRun.id == report_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found.")
    return ApiResponse(
        success=True,
        data=ReportJobResponse(
            id=run.id,
            status=run.status,
            report_path=run.report_path,
            report_format=run.report_format,
            academic_year=run.academic_year,
            semester=run.semester,
            department=run.department,
            created_at=run.created_at,
            completed_at=run.completed_at,
            download_url=f"/api/reports/{run.id}/download" if run.status == "COMPLETED" else None,
        ),
    )


@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    """Download the generated PDF report."""
    run = db.query(AnalysisRun).filter(AnalysisRun.id == report_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found.")
    if run.status != "COMPLETED":
        raise HTTPException(status_code=400, detail=f"Report {report_id} is not ready (status: {run.status}).")
    if not run.report_path or not os.path.isfile(run.report_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk.")
    return FileResponse(
        path=run.report_path,
        media_type="application/pdf",
        filename=os.path.basename(run.report_path),
    )


def _build_full_metrics(db, settings, filters, academic_year, semester, department):
    """Assemble metrics from all services into one dict for report generation."""
    metrics_svc = MetricsService(db, settings)
    section_svc = SectionAnalysisService(db, settings)
    faculty_svc = FacultyAnalysisService(db, settings)
    merit_svc = MeritService(db, settings)
    corr_svc = CorrelationService(db, settings)
    hist_svc = HistoricalService(db, settings)
    intv_svc = InterventionService(db, settings)
    narrative_svc = NarrativeService(settings)

    summary = nan_safe_dict(metrics_svc.get_summary(filters))
    grade_dist = nan_safe_list(metrics_svc.get_grade_distribution(filters))
    sections = nan_safe_list(section_svc.get_sections(filters))
    faculty = nan_safe_list(faculty_svc.get_faculty(filters))
    merit = nan_safe_list(merit_svc.get_merit_list(filters))
    correlation = nan_safe_list(corr_svc.get_correlation(filters))
    historical = nan_safe_list(hist_svc.get_historical(filters))
    interventions = nan_safe_list(intv_svc.get_interventions(filters))

    metrics = {
        "summary": summary,
        "grade_distribution": grade_dist,
        "sections": sections,
        "faculty": faculty,
        "merit": merit,
        "correlation": correlation,
        "historical": historical,
        "interventions": interventions,
        "reconciliation": {"total_expected": summary.get("total_results", 0),
                           "total_uploaded": summary.get("total_results", 0),
                           "matched": summary.get("total_results", 0),
                           "unmatched": 0,
                           "reconciliation_score": 100.0},
        "data_quality": {"overall_score": 100.0, "total_records": summary.get("total_results", 0),
                         "complete_records": summary.get("total_results", 0)},
        "period": f"Semester {semester} {academic_year}",
        "courses": [],
    }

    narrative = narrative_svc.generate(metrics)
    metrics["narrative"] = narrative
    return metrics