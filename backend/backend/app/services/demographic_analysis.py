"""Demographic analysis — slice by gender/category/etc."""
from __future__ import annotations
import math

import pandas as pd
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Course, Result, Student
from ..utils.calculations import compute_pass_percentage


DEMOGRAPHIC_SLICES = [
    "gender",
    "category",
    "admission_category",
    "entry_qualification",
]


class DemographicService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def get_demographics(self, filters: dict) -> list[dict]:
        """
        Slice by gender/category/admission_category/entry_qualification.
        Only return slices with data.
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

        results = []
        for slice_col in DEMOGRAPHIC_SLICES:
            if slice_col not in df.columns:
                continue
            if df[slice_col].dropna().empty:
                continue

            slice_data = []
            for val, grp in df.groupby(slice_col, dropna=True):
                if not val or str(val).strip() in ("", "nan", "None"):
                    continue
                total = len(grp)
                excluded = grp["result_status"].isin(["ABSENT", "WITHHELD", "DEBARRED"])
                eligible = int((~excluded).sum())
                pass_count = int((grp["result_status"] == "PASS").sum())
                fail_count = int((grp["result_status"] == "FAIL").sum())
                absent_count = int((grp["result_status"] == "ABSENT").sum())
                pass_rate = compute_pass_percentage(pass_count, eligible)
                avg_marks = _safe(grp["total_marks"].dropna().mean())
                avg_gpa = _safe(grp["grade_point"].dropna().mean())
                slice_data.append({
                    "value": str(val),
                    "total_students": int(grp["student_id"].nunique()),
                    "total_results": total,
                    "pass_count": pass_count,
                    "fail_count": fail_count,
                    "absent_count": absent_count,
                    "pass_rate": pass_rate,
                    "avg_marks": avg_marks,
                    "avg_gpa": avg_gpa,
                })

            if slice_data:
                results.append({
                    "dimension": slice_col,
                    "slices": slice_data,
                })

        return results

    # ------------------------------------------------------------------
    def _query_rows(self, filters: dict):
        query = (
            self.db.query(
                Result.student_id,
                Result.result_status,
                Result.total_marks,
                Result.grade_point,
                Student.gender,
                Student.category,
                Student.admission_category,
                Student.entry_qualification,
            )
            .join(Student, Result.student_id == Student.id)
            .join(Course, Result.course_id == Course.id)
        )
        if filters.get("academic_year"):
            query = query.filter(Result.academic_year == filters["academic_year"])
        if filters.get("semester"):
            query = query.filter(Result.semester == int(filters["semester"]))
        if filters.get("department"):
            query = query.filter(Student.department == filters["department"])
        if filters.get("section"):
            query = query.filter(Result.section == filters["section"])
        return query.all()

    def _to_df(self, rows) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows, columns=[
            "student_id", "result_status", "total_marks", "grade_point",
            "gender", "category", "admission_category", "entry_qualification",
        ])
        df["total_marks"] = pd.to_numeric(df["total_marks"], errors="coerce")
        df["grade_point"] = pd.to_numeric(df["grade_point"], errors="coerce")
        return df


def _safe(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else round(f, 4)
    except (TypeError, ValueError):
        return None
