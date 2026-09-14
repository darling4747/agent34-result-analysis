"""MetricsService — Pandas-based analytics on Result data."""
from __future__ import annotations
import math
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Course, Faculty, Result, Student
from ..utils.calculations import compute_pass_percentage, compute_weighted_gpa
from ..utils.constants import GPA_BUCKETS, MARK_BUCKETS
from ..utils.helpers import safe_float


class MetricsService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    def get_summary(self, filters: dict) -> dict:
        if "import_batch_id" not in filters:
            from .dataset_service import DatasetService
            batch_id = DatasetService(self.db).get_active_batch_id()
            if batch_id:
                filters = {**filters, "import_batch_id": batch_id}
        query = self._base_query()
        query = self._apply_filters(query, filters)
        rows = query.all()
        df = self._results_to_df(rows)

        if df.empty:
            return self._empty_summary()

        total = len(df)
        absent = int((df["result_status"] == "ABSENT").sum())
        withheld = int((df["result_status"] == "WITHHELD").sum())
        debarred = int((df["result_status"] == "DEBARRED").sum())
        excluded = absent + withheld + debarred
        eligible = total - excluded
        pass_count = int((df["result_status"] == "PASS").sum())
        fail_count = int((df["result_status"] == "FAIL").sum())

        marks_series = df["total_marks"].dropna()
        avg_marks = float(marks_series.mean()) if not marks_series.empty else None
        median_marks = float(marks_series.median()) if not marks_series.empty else None
        std_dev = float(marks_series.std()) if not marks_series.empty else None
        min_marks = float(marks_series.min()) if not marks_series.empty else None
        max_marks = float(marks_series.max()) if not marks_series.empty else None

        gp_series = df["grade_point"].dropna()
        credits_series = df["credits"].dropna()
        if not gp_series.empty and not credits_series.empty and len(gp_series) == len(credits_series):
            avg_gpa = compute_weighted_gpa(gp_series.tolist(), credits_series.tolist())
        elif not gp_series.empty:
            avg_gpa = float(gp_series.mean())
        else:
            avg_gpa = None

        pass_pct = compute_pass_percentage(pass_count, eligible)
        fail_pct = compute_pass_percentage(fail_count, eligible)

        return {
            "total_students": int(df["student_id"].nunique()),
            "total_results": total,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "absent_count": absent,
            "withheld_count": withheld,
            "pass_percentage": pass_pct,
            "failure_percentage": fail_pct,
            "average_marks": _safe(avg_marks),
            "median_marks": _safe(median_marks),
            "std_dev": _safe(std_dev),
            "min_marks": _safe(min_marks),
            "max_marks": _safe(max_marks),
            "average_gpa": _safe(avg_gpa),
            "previous_pass_percentage": None,  # populated by caller via historical service
        }

    # ------------------------------------------------------------------
    # Grade distribution
    # ------------------------------------------------------------------
    def get_grade_distribution(self, filters: dict) -> list[dict]:
        if "import_batch_id" not in filters:
            from .dataset_service import DatasetService
            batch_id = DatasetService(self.db).get_active_batch_id()
            if batch_id:
                filters = {**filters, "import_batch_id": batch_id}
        query = self._base_query()
        query = self._apply_filters(query, filters)
        rows = query.all()
        df = self._results_to_df(rows)

        if df.empty:
            return []

        grade_order = ["O", "A+", "A", "B+", "B", "C", "P", "F", "W", "I"]
        grade_map = self.settings.grade_map
        total = len(df)
        counts = df["grade"].value_counts().to_dict()

        # Build ordered list
        result = []
        cumulative = 0
        for g in grade_order:
            count = counts.get(g, 0)
            pct = round(count / total * 100, 2) if total > 0 else 0.0
            cumulative += pct
            result.append({
                "grade": g,
                "count": count,
                "percentage": pct,
                "cumulative_percentage": round(cumulative, 2),
                "grade_point": grade_map.get(g),
            })

        # Any grades not in order list
        for g, count in counts.items():
            if g not in grade_order:
                pct = round(count / total * 100, 2)
                cumulative += pct
                result.append({
                    "grade": g,
                    "count": count,
                    "percentage": pct,
                    "cumulative_percentage": round(cumulative, 2),
                    "grade_point": grade_map.get(g),
                })
        return result

    # ------------------------------------------------------------------
    # Mark distribution
    # ------------------------------------------------------------------
    def get_mark_distribution(self, filters: dict) -> list[dict]:
        if "import_batch_id" not in filters:
            from .dataset_service import DatasetService
            batch_id = DatasetService(self.db).get_active_batch_id()
            if batch_id:
                filters = {**filters, "import_batch_id": batch_id}
        query = self._base_query()
        query = self._apply_filters(query, filters)
        rows = query.all()
        df = self._results_to_df(rows)

        if df.empty:
            return []

        marks = df["total_marks"].dropna().tolist()
        total = len(marks)
        buckets = []
        for b in MARK_BUCKETS:
            lo, hi = b["min"], b["max"]
            if b == MARK_BUCKETS[-1]:
                count = sum(1 for m in marks if lo <= m <= hi)
            else:
                count = sum(1 for m in marks if lo <= m < hi)
            buckets.append({
                "range": b["range"],
                "count": count,
                "percentage": round(count / total * 100, 2) if total > 0 else 0.0,
            })
        return buckets

    # ------------------------------------------------------------------
    # GPA distribution
    # ------------------------------------------------------------------
    def get_gpa_distribution(self, filters: dict) -> list[dict]:
        if "import_batch_id" not in filters:
            from .dataset_service import DatasetService
            batch_id = DatasetService(self.db).get_active_batch_id()
            if batch_id:
                filters = {**filters, "import_batch_id": batch_id}
        query = self._base_query()
        query = self._apply_filters(query, filters)
        rows = query.all()
        df = self._results_to_df(rows)

        if df.empty:
            return []

        gp_list = df["grade_point"].dropna().tolist()
        total = len(gp_list)
        result = []
        for b in GPA_BUCKETS:
            lo, hi = b["min"], b["max"]
            count = sum(1 for gp in gp_list if lo <= gp < hi)
            result.append({
                "range": b["range"],
                "count": count,
                "percentage": round(count / total * 100, 2) if total > 0 else 0.0,
            })
        return result

    # ------------------------------------------------------------------
    # Filter helper
    # ------------------------------------------------------------------
    def _apply_filters(self, query, filters: dict):
        if filters.get("import_batch_id"):
            query = query.filter(Result.import_batch_id == filters["import_batch_id"])
        if filters.get("academic_year"):
            query = query.filter(Result.academic_year == filters["academic_year"])
        if filters.get("semester"):
            query = query.filter(Result.semester == int(filters["semester"]))
        if filters.get("department"):
            query = query.filter(Student.department == filters["department"])
        if filters.get("programme"):
            query = query.filter(Student.programme == filters["programme"])
        if filters.get("batch"):
            query = query.filter(Student.batch == filters["batch"])
        if filters.get("section"):
            query = query.filter(Result.section == filters["section"])
        if filters.get("course_code"):
            query = query.filter(Course.course_code == filters["course_code"].upper())
        return query

    def _base_query(self):
        return (
            self.db.query(
                Result.id,
                Result.student_id,
                Result.course_id,
                Result.semester,
                Result.academic_year,
                Result.section,
                Result.internal_marks,
                Result.external_marks,
                Result.total_marks,
                Result.grade,
                Result.grade_point,
                Result.credits,
                Result.result_status,
                Student.roll_number,
                Student.student_name,
                Student.department,
                Student.programme,
                Student.batch,
                Course.course_code,
                Course.course_name,
            )
            .join(Student, Result.student_id == Student.id)
            .join(Course, Result.course_id == Course.id)
        )

    def _results_to_df(self, rows) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame()
        cols = [
            "id", "student_id", "course_id", "semester", "academic_year",
            "section", "internal_marks", "external_marks", "total_marks",
            "grade", "grade_point", "credits", "result_status",
            "roll_number", "student_name", "department", "programme", "batch",
            "course_code", "course_name",
        ]
        return pd.DataFrame(rows, columns=cols)

    def _empty_summary(self) -> dict:
        return {
            "total_students": 0,
            "total_results": 0,
            "pass_count": 0,
            "fail_count": 0,
            "absent_count": 0,
            "withheld_count": 0,
            "pass_percentage": 0.0,
            "failure_percentage": 0.0,
            "average_marks": None,
            "median_marks": None,
            "std_dev": None,
            "min_marks": None,
            "max_marks": None,
            "average_gpa": None,
            "previous_pass_percentage": None,
        }


def _safe(val) -> float | None:
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return round(float(val), 4)
