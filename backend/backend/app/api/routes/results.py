"""Results & Upload routes."""
from __future__ import annotations
import os
import shutil
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ...config import get_settings
from ...database import get_db
from ...security.permissions import P
from ...security.auth import get_current_active_user, enforce_department_scope, require_permission
from ...models import ImportBatch, Result, Student, ValidationError as ValidationErrorModel
from ...schemas import ApiResponse, ImportBatchSchema, PaginatedResponse, PaginationMeta, ReconciliationResult, DataQualityReport, ValidationErrorSchema
from ...services.ingestion import IngestionService
from ...utils.helpers import ensure_dirs

router = APIRouter()


@router.post("/upload", response_model=ApiResponse[ImportBatchSchema])
async def upload_results(
    file: UploadFile = File(...),
    academic_year: str = Form(...),
    semester: int = Form(...),
    department: str = Form(""),
    _user: object = Depends(require_permission(P.RESULT_UPLOAD)),
    db: Session = Depends(get_db),
):
    """Upload a result file (xlsx/xls/csv) for ingestion."""
    settings = get_settings()
    ensure_dirs([settings.UPLOAD_DIR])

    # Validate extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    # Sanitize filename to prevent path traversal
    safe_filename = os.path.basename(file.filename.replace('..', '').replace('/', '_').replace('\\', '_'))
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    ext = os.path.splitext(safe_filename)[1].lower()
    if ext not in (".xlsx", ".xls", ".csv"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Upload .xlsx, .xls, or .csv only.",
        )

    # Check file is not empty
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Save to disk
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp}_{safe_filename}"
    save_path = os.path.join(settings.UPLOAD_DIR, safe_name)
    with open(save_path, "wb") as f:
        f.write(content)

    # Ingest
    svc = IngestionService(db, settings)
    batch = svc.process_upload(
        file_path=save_path,
        filename=file.filename,
        academic_year=academic_year,
        semester=semester,
        department=department,
    )
    return ApiResponse(success=True, data=ImportBatchSchema.model_validate(batch))


@router.get("/imports", response_model=PaginatedResponse[ImportBatchSchema])
def list_imports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Paginated list of import batches."""
    query = db.query(ImportBatch)
    if status:
        query = query.filter(ImportBatch.status == status.upper())
    if academic_year:
        query = query.filter(ImportBatch.academic_year == academic_year)
    if semester is not None:
        query = query.filter(ImportBatch.semester == semester)

    total = query.count()
    batches = query.order_by(ImportBatch.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = max((total + page_size - 1) // page_size, 1)

    return PaginatedResponse(
        success=True,
        data=[ImportBatchSchema.model_validate(b) for b in batches],
        pagination=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
    )


@router.post("/imports/{batch_id}/activate", response_model=ApiResponse[ImportBatchSchema])
def activate_import_batch(
    batch_id: int,
    _user: object = Depends(require_permission(P.RESULT_UPLOAD)),
    db: Session = Depends(get_db),
):
    """Activate a specific ImportBatch as the single active dataset."""
    from ...services.dataset_service import DatasetService
    batch = db.get(ImportBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail=f"ImportBatch with ID {batch_id} not found.")
    if batch.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Cannot activate an incomplete or failed batch.")

    DatasetService(db).activate_batch(batch_id)
    db.refresh(batch)
    return ApiResponse(success=True, data=ImportBatchSchema.model_validate(batch))


@router.get("/reconciliation", response_model=ApiResponse[ReconciliationResult])
def get_reconciliation(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return reconciliation stats: total imported vs unique students/results."""
    query = (
        db.query(ImportBatch)
        .filter(ImportBatch.status == "COMPLETED")
    )
    if academic_year:
        query = query.filter(ImportBatch.academic_year == academic_year)
    if semester is not None:
        query = query.filter(ImportBatch.semester == semester)
    if department:
        query = query.filter(ImportBatch.department == department)

    batches = query.all()
    total_uploaded = sum(b.total_rows for b in batches)
    total_valid = sum(b.valid_rows for b in batches)
    total_rejected = sum(b.rejected_rows for b in batches)

    # Count actual results in DB
    result_query = db.query(Result)
    if academic_year:
        result_query = result_query.filter(Result.academic_year == academic_year)
    if semester is not None:
        result_query = result_query.filter(Result.semester == semester)
    actual_results = result_query.count()

    matched = min(total_valid, actual_results)
    unmatched = abs(total_valid - actual_results)
    score = round((matched / total_uploaded * 100) if total_uploaded > 0 else 0.0, 2)

    discrepancies = []
    if total_rejected > 0:
        discrepancies.append({
            "type": "REJECTED_ROWS",
            "count": total_rejected,
            "message": f"{total_rejected} rows were rejected during validation.",
        })
    if unmatched > 0:
        discrepancies.append({
            "type": "DB_MISMATCH",
            "count": unmatched,
            "message": f"Expected {total_valid} valid results but found {actual_results} in database.",
        })

    return ApiResponse(
        success=True,
        data=ReconciliationResult(
            total_expected=total_uploaded,
            total_uploaded=total_uploaded,
            matched=matched,
            unmatched=unmatched,
            discrepancies=discrepancies,
            reconciliation_score=score,
        ),
    )


@router.get("/data-quality", response_model=ApiResponse[DataQualityReport])
def get_data_quality(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return a data quality report for the specified period."""
    settings = get_settings()

    # Pull all validation errors for matching batches
    batch_query = db.query(ImportBatch)
    if academic_year:
        batch_query = batch_query.filter(ImportBatch.academic_year == academic_year)
    if semester is not None:
        batch_query = batch_query.filter(ImportBatch.semester == semester)
    if department:
        batch_query = batch_query.filter(ImportBatch.department == department)
    batches = batch_query.all()
    batch_ids = [b.id for b in batches]

    total_records = sum(b.total_rows for b in batches)
    valid_records = sum(b.valid_rows for b in batches)

    err_query = db.query(ValidationErrorModel)
    if batch_ids:
        err_query = err_query.filter(ValidationErrorModel.import_batch_id.in_(batch_ids))
    errors = err_query.all()

    missing_fields = sum(1 for e in errors if e.error_code == "MISSING_REQUIRED_FIELD")
    duplicates = sum(1 for e in errors if e.error_code == "DUPLICATE_RECORD")
    out_of_range = sum(1 for e in errors if e.error_code in ("MARKS_BELOW_MINIMUM", "MARKS_EXCEED_MAXIMUM"))
    mismatches = sum(1 for e in errors if e.error_code == "TOTAL_MARKS_MISMATCH")

    issues = [
        {"type": e.error_code, "count": 1, "severity": e.severity, "message": e.message[:200]}
        for e in errors[:50]
    ]

    overall_score = round((valid_records / total_records * 100) if total_records > 0 else 0.0, 2)

    return ApiResponse(
        success=True,
        data=DataQualityReport(
            overall_score=overall_score,
            total_records=total_records,
            complete_records=valid_records,
            missing_fields_count=missing_fields,
            duplicate_records=duplicates,
            out_of_range_values=out_of_range,
            grade_total_mismatches=mismatches,
            issues=issues,
        ),
    )

@router.get("/dataset-info")
def get_dataset_info(
    _user: object = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return current active dataset metadata — used by frontend status bar."""
    from ...services.dataset_service import DatasetService
    info = DatasetService(db).get_dataset_info()
    return {"success": True, "data": info}
