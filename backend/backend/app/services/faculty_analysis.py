"""Faculty contextual analysis service."""
from __future__ import annotations
import math

import pandas as pd
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Course, Faculty, HistoricalResult, Result, Student
from ..utils.calculations import compute_pass_percentage
from ..utils.constants import FACULTY_DEVIATION_THRESHOLD


class FacultyAnalysisService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def get_faculty(self, filters: dict) -> list[dict]:
        """
        Per faculty: courses_handled, total_students, avg_marks, pass_rate,
        historical_baseline, deviation, courses_requiring_review, context_note.
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
        # If no faculty_id data exists, group by course_code as a fallback
        has_any_faculty_id = df['faculty_id'].notna().any()
        if not has_any_faculty_id:
            # Fill faculty_name with course_code when no faculty data
            df['faculty_id'] = df['course_code']
            df['faculty_name'] = df['course_code'].apply(lambda x: f'Course: {x}')
        for faculty_id_val, grp in df.groupby("faculty_id"):
            faculty_name = grp["faculty_name"].iloc[0]
            department = grp["department"].iloc[0] if "department" in grp.columns else None
            courses = list(grp["course_code"].unique())
            total_students = int(grp["student_id"].nunique())
            excluded = grp["result_status"].isin(["ABSENT", "WITHHELD", "DEBARRED"])
            eligible = int((~excluded).sum())
            pass_count = int((grp["result_status"] == "PASS").sum())
            fail_count = int((grp["result_status"] == "FAIL").sum())
            pass_rate = compute_pass_percentage(pass_count, eligible)
            marks = grp["total_marks"].dropna()
            avg_marks = _safe(marks.mean())

            # Historical baseline from HistoricalResult
            hist_pass_rates: list[float] = []
            for cc in courses:
                hist_rows = (
                    self.db.query(HistoricalResult.pass_rate)
                    .join(Course, HistoricalResult.course_id == Course.id)
                    .filter(Course.course_code == cc)
                    .filter(HistoricalResult.pass_rate.isnot(None))
                    .all()
                )
                hist_pass_rates.extend([float(h[0]) for h in hist_rows])

            historical_baseline = round(sum(hist_pass_rates) / len(hist_pass_rates), 2) if hist_pass_rates else None
            deviation = round(pass_rate - historical_baseline, 2) if historical_baseline is not None else None

            # Courses requiring review
            review_courses: list[str] = []
            if deviation is not None and abs(deviation) > FACULTY_DEVIATION_THRESHOLD:
                review_courses = courses  # all courses this faculty handles need review

            context_note = _build_context_note(faculty_name, courses, pass_rate, deviation)

            results.append({
                "faculty_id": (int(faculty_id_val) if str(faculty_id_val).isdigit() else str(faculty_id_val)) if faculty_id_val is not None else None,
                "faculty_name": str(faculty_name),
                "department": str(department) if department else None,
                "courses_handled": len(courses),
                "total_students": total_students,
                "avg_marks": avg_marks,
                "pass_rate": pass_rate,
                "historical_baseline": historical_baseline,
                "deviation": deviation,
                "courses_requiring_review": review_courses,
                "context_note": context_note,
            })

        return results

    # ------------------------------------------------------------------
    def _query_rows(self, filters: dict):
        # Check if any results have faculty_id set
        has_faculty = self.db.query(Result).filter(Result.faculty_id.isnot(None)).limit(1).first() is not None

        query = (
            self.db.query(
                Result.student_id,
                Result.result_status,
                Result.total_marks,
                Result.faculty_id,
                Faculty.faculty_name,
                Student.department,
                Course.course_code,
            )
            .join(Student, Result.student_id == Student.id)
            .join(Course, Result.course_id == Course.id)
            .outerjoin(Faculty, Result.faculty_id == Faculty.id)
        )
        # Only filter by faculty_id when faculty data actually exists
        if has_faculty:
            query = query.filter(Result.faculty_id.isnot(None))
        if filters.get("import_batch_id"):
            query = query.filter(Result.import_batch_id == filters["import_batch_id"])
        if filters.get("academic_year"):
            query = query.filter(Result.academic_year == filters["academic_year"])
        if filters.get("semester"):
            query = query.filter(Result.semester == int(filters["semester"]))
        if filters.get("department"):
            query = query.filter(Student.department == filters["department"])
        return query.all()

    def _to_df(self, rows) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows, columns=[
            "student_id", "result_status", "total_marks", "faculty_id",
            "faculty_name", "department", "course_code",
        ])
        df["total_marks"] = pd.to_numeric(df["total_marks"], errors="coerce")
        return df


def _safe(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else round(f, 4)
    except (TypeError, ValueError):
        return None


def _build_context_note(name: str, courses: list[str], pass_rate: float, deviation: float | None) -> str:
    courses_str = ", ".join(courses[:3]) + ("…" if len(courses) > 3 else "")
    note = (
        f"{name} handled {len(courses)} course(s) ({courses_str}) "
        f"with an overall pass rate of {pass_rate:.1f}%."
    )
    if deviation is not None:
        direction = "above" if deviation > 0 else "below"
        note += f" This is {abs(deviation):.1f} percentage points {direction} the historical baseline."
    note += " Data is provided for contextual review; individual performance should be evaluated holistically."
    return note