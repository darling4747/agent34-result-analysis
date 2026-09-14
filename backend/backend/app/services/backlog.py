"""Backlog tracking service — downstream-ready for Agent 35."""
from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Course, Result, Student


class BacklogService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def get_backlogs(self, filters: dict) -> list[dict]:
        """
        For each student with FAIL results:
        roll_number, student_name, failed_courses (list), backlog_count,
        semester_of_failure, attempt_number
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

        fail_df = df[df["result_status"] == "FAIL"]
        if fail_df.empty:
            return []

        result = []
        for (student_id, roll_number, student_name, programme, section, batch), grp in fail_df.groupby(
            ["student_id", "roll_number", "student_name", "programme", "section", "batch"],
            dropna=False,
        ):
            failed_courses = []
            for _, row in grp.iterrows():
                failed_courses.append({
                    "course_code": row["course_code"],
                    "course_name": row["course_name"],
                    "semester": int(row["semester"]) if row["semester"] is not None else None,
                    "academic_year": row["academic_year"],
                    "grade": row["grade"],
                    "total_marks": row["total_marks"],
                    "attempt_number": int(row["attempt_number"]) if row["attempt_number"] is not None else 1,
                })

            result.append({
                "roll_number": roll_number,
                "student_name": student_name,
                "programme": programme,
                "section": section,
                "batch": batch,
                "semester": int(grp["semester"].iloc[0]) if not grp.empty else None,
                "academic_year": grp["academic_year"].iloc[0] if not grp.empty else None,
                "failed_courses": failed_courses,
                "backlog_count": len(failed_courses),
                "attempt_number": int(grp["attempt_number"].max()) if not grp.empty else 1,
            })

        result.sort(key=lambda x: -x["backlog_count"])
        return result

    # ------------------------------------------------------------------
    def _query_rows(self, filters: dict):
        query = (
            self.db.query(
                Result.student_id,
                Result.result_status,
                Result.semester,
                Result.academic_year,
                Result.grade,
                Result.total_marks,
                Result.attempt_number,
                Student.roll_number,
                Student.student_name,
                Student.programme,
                Student.section,
                Student.batch,
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
        return pd.DataFrame(rows, columns=[
            "student_id", "result_status", "semester", "academic_year",
            "grade", "total_marks", "attempt_number",
            "roll_number", "student_name", "programme", "section", "batch",
            "course_code", "course_name",
        ])
