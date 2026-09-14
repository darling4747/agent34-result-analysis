"""Correlation analysis routes."""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...config import get_settings
from ...database import get_db
from ...security.auth import get_current_active_user, enforce_department_scope
from ...schemas import ApiResponse
from ...services.correlation import CorrelationService
from ...utils.helpers import nan_safe_list

router = APIRouter()


@router.get("/correlation")
def get_correlation(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    course_code: Optional[str] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Internal vs External marks Pearson correlation per course."""
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
    if course_code:
        filters["course_code"] = course_code

    svc = CorrelationService(db, settings)
    data = svc.get_correlation(filters)
    return ApiResponse(success=True, data=nan_safe_list(data))