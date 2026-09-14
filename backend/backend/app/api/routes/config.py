"""System configuration management routes."""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...config import get_settings
from ...database import get_db
from ...security.auth import get_current_active_user, require_permission
from ...schemas import ApiResponse

router = APIRouter()


class WeightConfig(BaseModel):
    failure_weight: float = 0.40
    historical_weight: float = 0.30
    section_weight: float = 0.20
    correlation_weight: float = 0.10


class AssessmentConfig(BaseModel):
    internal_max: float = 30.0
    external_max: float = 70.0
    total_max: float = 100.0


@router.get("/config")
def get_system_config(
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return system & assessment configuration settings."""
    settings = get_settings()
    has_key = bool(settings.LLM_API_KEY)
    
    return ApiResponse(success=True, data={
        "assessment": {
            "internal_max": settings.INTERNAL_MAX,
            "external_max": settings.EXTERNAL_MAX,
            "total_max": settings.TOTAL_MAX,
            "grade_map": settings.grade_map,
        },
        "intervention_weights": {
            "failure_weight": settings.INTERVENTION_FAILURE_WEIGHT,
            "historical_weight": settings.INTERVENTION_HISTORICAL_WEIGHT,
            "section_weight": settings.INTERVENTION_SECTION_WEIGHT,
            "correlation_weight": settings.INTERVENTION_CORRELATION_WEIGHT,
        },
        "ai_provider": {
            "provider": settings.LLM_PROVIDER or "gemini",
            "model": settings.LLM_MODEL or "gemini-3.6-flash",
            "has_api_key": has_key,
            "status": "Connected (Gemini 3.6 Flash)" if has_key else "Deterministic Engine Fallback",
        },
        "database": {
            "type": "PostgreSQL",
            "name": "result_analysis",
            "host": "localhost",
            "port": 5432,
            "status": "healthy",
        },
        "integrations": {
            "agent_35": "Active — Backlog Data Export Contract Enabled",
            "agent_8": "Active — Attainment & SGPA Contract Enabled",
        }
    })


@router.put("/config")
def update_system_config(
    weights: Optional[WeightConfig] = None,
    assessment: Optional[AssessmentConfig] = None,
    _user: object = Depends(require_permission("CONFIG_MANAGE")),
    db: Session = Depends(get_db),
):
    """Update system settings (Admin only)."""
    settings = get_settings()
    if weights:
        total = round(weights.failure_weight + weights.historical_weight + weights.section_weight + weights.correlation_weight, 2)
        if total != 1.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Intervention weights must sum to 1.0 (currently sums to {total}).",
            )
        settings.INTERVENTION_FAILURE_WEIGHT = weights.failure_weight
        settings.INTERVENTION_HISTORICAL_WEIGHT = weights.historical_weight
        settings.INTERVENTION_SECTION_WEIGHT = weights.section_weight
        settings.INTERVENTION_CORRELATION_WEIGHT = weights.correlation_weight

    if assessment:
        settings.INTERNAL_MAX = assessment.internal_max
        settings.EXTERNAL_MAX = assessment.external_max
        settings.TOTAL_MAX = assessment.total_max

    return ApiResponse(success=True, data={
        "message": "System configuration updated successfully.",
        "intervention_weights": {
            "failure_weight": settings.INTERVENTION_FAILURE_WEIGHT,
            "historical_weight": settings.INTERVENTION_HISTORICAL_WEIGHT,
            "section_weight": settings.INTERVENTION_SECTION_WEIGHT,
            "correlation_weight": settings.INTERVENTION_CORRELATION_WEIGHT,
        }
    })
