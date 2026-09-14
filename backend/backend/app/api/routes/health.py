"""Health check routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...database import get_db

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    """Deep health check: verifies DB connectivity."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "version": "1.0.0",
        "agent": 34,
    }
