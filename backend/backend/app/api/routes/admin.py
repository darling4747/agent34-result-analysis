"""Admin diagnostics routes — PLATFORM_ADMIN only."""
from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import APIRouter, Depends

from ...database import get_db
from ...models import ImportBatch, Student, Result, Course, User
from ...security.auth import require_role

router = APIRouter()


@router.get("/diagnostics", tags=["Administration"])
def admin_diagnostics(
    _admin: User = Depends(require_role("PLATFORM_ADMIN")),
    db: Session = Depends(get_db),
):
    """PLATFORM_ADMIN only: system diagnostics. No credentials exposed."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"

    # Determine DB name safely (without credentials)
    from ...config import get_settings
    settings = get_settings()
    db_url = settings.DATABASE_URL or ""
    # Extract only the DB name segment, not the full URL
    try:
        db_name = db_url.rstrip("/").split("/")[-1].split("?")[0]
    except Exception:
        db_name = "unknown"

    # Active import batch
    active_batch = (
        db.query(ImportBatch)
        .filter(ImportBatch.is_active == True, ImportBatch.status == "COMPLETED")
        .order_by(ImportBatch.created_at.desc())
        .first()
    )

    return {
        "success": True,
        "data": {
            "database": db_status,
            "db_name": db_name,
            "active_import_batch_id": active_batch.id if active_batch else None,
            "students": db.query(Student).count(),
            "results": db.query(Result).count(),
            "courses": db.query(Course).count(),
            "users": db.query(User).count(),
        },
    }
