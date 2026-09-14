"""Correlation analysis between internal and external marks."""
from __future__ import annotations
import math
from typing import Any

import pandas as pd
from scipy import stats
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Course, Result, Student
from ..utils.calculations import interpret_correlation
from ..utils.constants import IE_GAP_THRESHOLD, MIN_SAMPLE_FOR_CORRELATION
from ..utils.helpers import safe_float


class CorrelationService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def get_correlation(self, filters: dict) -> list[dict]:
        """
        For each course:
        - internal_average, external_average
        - pearson_correlation (scipy.stats.pearsonr)
        - sample_size
        - interpretation
        - flags: HIGH_INTERNAL_LOW_EXTERNAL, LARGE_IE_GAP, WEAK_CORRELATION, NEGATIVE_CORRELATION
        - scatter_data: list of {roll_number, internal_marks, external_marks}
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
        for course_code, group in df.groupby("course_code"):
            valid = group.dropna(subset=["internal_marks", "external_marks"])
            n = len(valid)
            internal_avg = _safe(valid["internal_marks"].mean())
            external_avg = _safe(valid["external_marks"].mean())

            pearson_r = None
            p_value = None
            if n >= MIN_SAMPLE_FOR_CORRELATION:
                try:
                    r, p = stats.pearsonr(
                        valid["internal_marks"].tolist(),
                        valid["external_marks"].tolist(),
                    )
                    pearson_r = None if math.isnan(r) else round(float(r), 4)
                    p_value = None if math.isnan(p) else round(float(p), 4)
                except Exception:
                    pearson_r = None

            interpretation = interpret_correlation(pearson_r if pearson_r is not None else float("nan"), n)

            flags: list[str] = []
            if (
                internal_avg is not None
                and external_avg is not None
                and internal_avg > (self.settings.INTERNAL_MAX * 0.7)
                and external_avg < (self.settings.EXTERNAL_MAX * 0.4)
            ):
                flags.append("HIGH_INTERNAL_LOW_EXTERNAL")

            if internal_avg is not None and external_avg is not None:
                # normalise both to 100-point scale for comparison
                norm_internal = (internal_avg / self.settings.INTERNAL_MAX) * 100
                norm_external = (external_avg / self.settings.EXTERNAL_MAX) * 100
                if abs(norm_internal - norm_external) > IE_GAP_THRESHOLD:
                    flags.append("LARGE_IE_GAP")

            if interpretation in ("WEAK_POSITIVE", "WEAK_NEGATIVE", "INSUFFICIENT_DATA"):
                if n >= MIN_SAMPLE_FOR_CORRELATION:
                    flags.append("WEAK_CORRELATION")

            if pearson_r is not None and pearson_r < 0:
                flags.append("NEGATIVE_CORRELATION")

            scatter_data = [
                {
                    "roll_number": row_r,
                    "internal_marks": _safe(row_i),
                    "external_marks": _safe(row_e),
                }
                for row_r, row_i, row_e in zip(
                    valid["roll_number"].tolist(),
                    valid["internal_marks"].tolist(),
                    valid["external_marks"].tolist(),
                )
            ]

            course_name = group["course_name"].iloc[0] if not group.empty else course_code

            results.append({
                "course_code": course_code,
                "course_name": course_name,
                "internal_average": internal_avg,
                "external_average": external_avg,
                "pearson_correlation": pearson_r,
                "p_value": p_value,
                "sample_size": n,
                "interpretation": interpretation,
                "flags": flags,
                "scatter_data": scatter_data,
            })

        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _query_rows(self, filters: dict):
        query = (
            self.db.query(
                Result.internal_marks,
                Result.external_marks,
                Result.total_marks,
                Student.roll_number,
                Course.course_code,
                Course.course_name,
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
        return query.all()

    def _to_df(self, rows) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows, columns=[
            "internal_marks", "external_marks", "total_marks",
            "roll_number", "course_code", "course_name",
        ])
        df["internal_marks"] = pd.to_numeric(df["internal_marks"], errors="coerce")
        df["external_marks"] = pd.to_numeric(df["external_marks"], errors="coerce")
        return df


def _safe(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else round(f, 4)
    except (TypeError, ValueError):
        return None
