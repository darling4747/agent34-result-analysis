"""Active dataset resolution service - single source of truth for current data."""
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from ..models import ImportBatch


class DatasetService:
    def __init__(self, db: Session):
        self.db = db

    def get_active_batch(self) -> Optional[ImportBatch]:
        """Return the single active ImportBatch, or None if no data has been uploaded."""
        return (
            self.db.query(ImportBatch)
            .filter(ImportBatch.is_active == True, ImportBatch.status == 'COMPLETED')
            .order_by(ImportBatch.created_at.desc())
            .first()
        )

    def get_active_batch_id(self) -> Optional[int]:
        batch = self.get_active_batch()
        return batch.id if batch else None

    def activate_batch(self, batch_id: int) -> None:
        """Deactivate all batches, then activate the given one."""
        self.db.query(ImportBatch).update({'is_active': False})
        batch = self.db.get(ImportBatch, batch_id)
        if batch:
            batch.is_active = True
        self.db.commit()

    def get_dataset_info(self) -> dict:
        """Return current dataset metadata for frontend display."""
        batch = self.get_active_batch()
        if not batch:
            return {
                'has_data': False,
                'message': 'No result dataset has been uploaded yet.',
                'batch_id': None,
                'filename': None,
                'academic_year': None,
                'semester': None,
                'department': None,
                'uploaded_at': None,
                'student_count': 0,
                'result_count': 0,
                'course_count': 0,
                'status': 'no_data',
                'analysis_status': 'no_data',
            }
        return {
            'has_data': True,
            'batch_id': batch.id,
            'filename': batch.filename,
            'academic_year': batch.academic_year,
            'semester': batch.semester,
            'department': batch.department,
            'uploaded_at': batch.created_at.isoformat() if batch.created_at else None,
            'student_count': getattr(batch, 'student_count', 0) or 0,
            'result_count': getattr(batch, 'result_count', 0) or 0,
            'course_count': getattr(batch, 'course_count', 0) or 0,
            'status': batch.status,
            'analysis_status': getattr(batch, 'analysis_status', 'COMPLETED') or 'COMPLETED',
        }