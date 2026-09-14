"""Attainment input service — downstream-ready for Agent 8."""
from __future__ import annotations
import math

import pandas as pd
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Course, Result, Student


class AttainmentService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def get_attainment_input(self, filters: dict) -> list[dict]:
        """
        Per student per course:
        course_code, course_name, section, roll_number, student_name,
        internal_marks, external_marks, total_marks, grade, grade_point,
        semester, academic_year, credits
        """
        if "import_batch_id" not in filters:
            from .dataset_service import DatasetService
            batch_id = DatasetService(self.db).get_active_batch_id()
            if batch_id:
                filters = {**filters, "import_batch_id": batch_id}
        rows = self._query_rows(filters)
        df = self._to_df(rows)

        if df.empty:
            return []

        result = []
        for _, row in df.iterrows():
            result.append({
                "course_code": row["course_code"],
                "course_name": row["course_name"],
                "section": row["section"],
                "roll_number": row["roll_number"],
                "student_name": row["student_name"],
                "internal_marks": _safe(row["internal_marks"]),
                "external_marks": _safe(row["external_marks"]),
                "total_marks": _safe(row["total_marks"]),
                "grade": row["grade"],
                "grade_point": _safe(row["grade_point"]),
                "semester": int(row["semester"]) if row["semester"] is not None else None,
                "academic_year": row["academic_year"],
                "credits": _safe(row["credits"]),
                "result_status": row["result_status"],
            })

        return result

    # ------------------------------------------------------------------
    def _query_rows(self, filters: dict):
        query = (
            self.db.query(
                Course.course_code,
                Course.course_name,
                Result.section,
                Student.roll_number,
                Student.student_name,
                Result.internal_marks,
                Result.external_marks,
                Result.total_marks,
                Result.grade,
                Result.grade_point,
                Result.semester,
                Result.academic_year,
                Result.credits,
                Result.result_status,
            )
            .join(Student, Result.student_id == Student.id)
            .join(Course, Result.course_id == Course.id)
        )
        if filters.get("import_batch_id"):
            query = query.filter(Result.import_batch_id == filters["import_batch_id"])
        if filters.get("academic_year"):
            query = query.filter(Result.academic_year == filters["academic_year"])
        if filters.get("semester"):
            query = query.filter(Result.semester == int(filters["semester"]))
        if filters.get("department"):
            query = query.filter(Student.department == filters["department"])
        if filters.get("section"):
            query = query.filter(Result.section == filters["section"])
        if filters.get("course_code"):
            query = query.filter(Course.course_code == filters["course_code"].upper())
        if filters.get("roll_number"):
            query = query.filter(Student.roll_number == filters["roll_number"])
        return query.order_by(Course.course_code, Student.roll_number).all()

    def _to_df(self, rows) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows, columns=[
            "course_code", "course_name", "section", "roll_number", "student_name",
            "internal_marks", "external_marks", "total_marks", "grade", "grade_point",
            "semester", "academic_year", "credits", "result_status",
        ])
        for col in ["internal_marks", "external_marks", "total_marks", "grade_point", "credits"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df


def _safe(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else round(f, 4)
    except (TypeError, ValueError):
        return None
