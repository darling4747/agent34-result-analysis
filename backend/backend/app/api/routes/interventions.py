"""Intervention prioritization routes."""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...config import get_settings
from ...database import get_db
from ...security.auth import get_current_active_user, enforce_department_scope
from ...schemas import ApiResponse
from ...services.intervention import InterventionService
from ...utils.helpers import nan_safe_list, nan_safe_dict

router = APIRouter()


@router.get("/interventions")
def get_interventions(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Prioritised list of courses needing academic intervention."""
    settings = get_settings()
    filters: dict = {}
    if academic_year:
        filters["academic_year"] = academic_year
    if semester is not None:
        filters["semester"] = semester
    if department:
        filters["department"] = department
    if section:
        filters["section"] = section

    svc = InterventionService(db, settings)
    data = svc.get_interventions(filters)
    return ApiResponse(success=True, data=nan_safe_list(data))


@router.get("/interventions/summary")
def get_intervention_summary(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Aggregated intervention summary (counts by priority)."""
    settings = get_settings()
    filters: dict = {}
    if academic_year:
        filters["academic_year"] = academic_year
    if semester is not None:
        filters["semester"] = semester
    if department:
        filters["department"] = department
    if section:
        filters["section"] = section

    svc = InterventionService(db, settings)
    data = svc.get_summary(filters)
    return ApiResponse(success=True, data=nan_safe_dict(data))