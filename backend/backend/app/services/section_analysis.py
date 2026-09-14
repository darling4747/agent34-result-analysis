"""Section-level analysis service."""
from __future__ import annotations
import math

import pandas as pd
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Course, Result, Student
from ..utils.calculations import compute_pass_percentage


class SectionAnalysisService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def get_sections(self, filters: dict) -> list[dict]:
        """
        Per section: student_count, pass_count, fail_count, pass_rate,
        failure_rate, avg_marks, avg_gpa, top_score, lowest_score
        + section_deviation from section mean.
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

        section_results = []
        for section, grp in df.groupby("section"):
            excluded = grp["result_status"].isin(["ABSENT", "WITHHELD", "DEBARRED"])
            eligible_grp = grp[~excluded]
            eligible_count = len(eligible_grp)
            pass_count = int((grp["result_status"] == "PASS").sum())
            fail_count = int((grp["result_status"] == "FAIL").sum())
            absent_count = int((grp["result_status"] == "ABSENT").sum())
            pass_rate = compute_pass_percentage(pass_count, eligible_count)
            failure_rate = compute_pass_percentage(fail_count, eligible_count)
            marks = grp["total_marks"].dropna()
            avg_marks = _safe(marks.mean())
            top_score = _safe(marks.max())
            lowest_score = _safe(marks.min())
            gp_series = grp["grade_point"].dropna()
            avg_gpa = _safe(gp_series.mean())

            section_results.append({
                "section": str(section),
                "student_count": len(grp["student_id"].unique()),
                "pass_count": pass_count,
                "fail_count": fail_count,
                "absent_count": absent_count,
                "pass_rate": pass_rate,
                "failure_rate": failure_rate,
                "avg_marks": avg_marks,
                "avg_gpa": avg_gpa,
                "top_score": top_score,
                "lowest_score": lowest_score,
                "section_deviation": None,  # computed below
            })

        if not section_results:
            return []

        # Compute section deviation from the mean of section pass rates
        pass_rates = [s["pass_rate"] for s in section_results if s["pass_rate"] is not None]
        if pass_rates:
            mean_pass_rate = sum(pass_rates) / len(pass_rates)
            for s in section_results:
                if s["pass_rate"] is not None:
                    s["section_deviation"] = round(s["pass_rate"] - mean_pass_rate, 2)

        return section_results

    # ------------------------------------------------------------------
    def _query_rows(self, filters: dict):
        query = (
            self.db.query(
                Result.student_id,
                Result.result_status,
                Result.total_marks,
                Result.grade_point,
                Result.section,
                Course.course_code,
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
        if filters.get("course_code"):
            query = query.filter(Course.course_code == filters["course_code"].upper())
        if filters.get("section"):
            query = query.filter(Result.section == filters["section"])
        return query.filter(Result.section.isnot(None)).all()

    def _to_df(self, rows) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows, columns=["student_id", "result_status", "total_marks", "grade_point", "section", "course_code"])
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
