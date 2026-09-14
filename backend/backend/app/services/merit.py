"""Merit list service."""
from __future__ import annotations
import math

import pandas as pd
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Course, Result, Student
from ..utils.calculations import compute_weighted_gpa


class MeritService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def get_merit_list(self, filters: dict) -> list[dict]:
        """
        Rank students by GPA (weighted if credits exist).
        Scope: PROGRAMME | SECTION | COURSE
        Handle ties by secondary sort on total_marks, then roll_number.
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

        # Compute per-student aggregated GPA and total marks
        student_rows = []
        for (student_id, roll_number, student_name, programme, section, batch), grp in df.groupby(
            ["student_id", "roll_number", "student_name", "programme", "section", "batch"],
            dropna=False,
        ):
            gp_list = grp["grade_point"].dropna().tolist()
            cr_list = grp["credits"].dropna().tolist()
            if len(gp_list) == 0:
                continue
            sgpa = compute_weighted_gpa(gp_list, cr_list if len(cr_list) == len(gp_list) else [])
            total_marks = _safe(grp["total_marks"].sum())
            student_rows.append({
                "student_id": student_id,
                "roll_number": roll_number,
                "student_name": student_name,
                "programme": programme,
                "section": section,
                "batch": batch,
                "sgpa": sgpa,
                "total_marks": total_marks,
            })

        if not student_rows:
            return []

        # Sort: sgpa DESC, total_marks DESC, roll_number ASC
        student_rows.sort(
            key=lambda x: (-x["sgpa"], -(x["total_marks"] or 0), x["roll_number"] or "")
        )

        # Identify course toppers (highest mark per course)
        course_topper_rolls = set()
        for ccode, cgrp in df.groupby("course_code"):
            cgrp_valid = cgrp.dropna(subset=["total_marks"])
            if not cgrp_valid.empty:
                max_m = cgrp_valid["total_marks"].max()
                top_rolls = cgrp_valid[cgrp_valid["total_marks"] == max_m]["roll_number"].tolist()
                course_topper_rolls.update(top_rolls)

        # Track section ranks (top 3 per section)
        sec_ranks = {}
        for (sec,), sgrp in df.groupby(["section"]):
            s_rows = []
            for (student_id, roll_number, student_name, programme, section, batch), grp in sgrp.groupby(
                ["student_id", "roll_number", "student_name", "programme", "section", "batch"],
                dropna=False,
            ):
                gp_list = grp["grade_point"].dropna().tolist()
                cr_list = grp["credits"].dropna().tolist()
                if len(gp_list) == 0:
                    continue
                sgpa = compute_weighted_gpa(gp_list, cr_list if len(cr_list) == len(gp_list) else [])
                tot = _safe(grp["total_marks"].sum())
                s_rows.append((roll_number, sgpa, tot or 0))
            s_rows.sort(key=lambda x: (-x[1], -x[2]))
            top3 = [r[0] for r in s_rows[:3]]
            sec_ranks[sec] = set(top3)

        # Assign ranks with tie handling and determine scope
        result = []
        rank = 0
        prev_sgpa = None
        prev_total = None
        same_rank_count = 0
        for i, sr in enumerate(student_rows):
            if sr["sgpa"] != prev_sgpa or sr["total_marks"] != prev_total:
                rank = i + 1
                same_rank_count = 0
            same_rank_count += 1
            prev_sgpa = sr["sgpa"]
            prev_total = sr["total_marks"]

            status = _determine_status(sr["sgpa"])
            roll = sr["roll_number"]
            sec = sr["section"]

            # Determine primary scope
            if roll in course_topper_rolls:
                scope = "COURSE"
            elif sec in sec_ranks and roll in sec_ranks[sec]:
                scope = "SECTION"
            else:
                scope = "PROGRAMME"

            clean_name = str(sr["student_name"] or "").replace("\n", " ").strip()
            clean_name = " ".join(clean_name.split())

            result.append({
                "rank": rank,
                "roll_number": roll,
                "student_name": clean_name or f"Student {roll}",
                "programme": sr["programme"] or "B.Tech",
                "section": str(sec or "A"),
                "batch": sr["batch"] or "2023-27",
                "sgpa": round(sr["sgpa"], 4),
                "cgpa": None,
                "total_marks": sr["total_marks"],
                "status": status,
                "scope": scope,
            })

        return result

    # ------------------------------------------------------------------
    def _query_rows(self, filters: dict):
        query = (
            self.db.query(
                Result.student_id,
                Result.grade_point,
                Result.credits,
                Result.total_marks,
                Student.roll_number,
                Student.student_name,
                Student.programme,
                Student.section,
                Student.batch,
                Course.course_code,
            )
            .join(Student, Result.student_id == Student.id)
            .join(Course, Result.course_id == Course.id)
            .filter(Result.result_status.in_(["PASS", "FAIL"]))
        )
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
        if filters.get("section"):
            query = query.filter(Result.section == filters["section"])
        if filters.get("course_code"):
            query = query.filter(Course.course_code == filters["course_code"].upper())
        return query.all()

    def _to_df(self, rows) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows, columns=[
            "student_id", "grade_point", "credits", "total_marks",
            "roll_number", "student_name", "programme", "section", "batch", "course_code",
        ])
        df["grade_point"] = pd.to_numeric(df["grade_point"], errors="coerce")
        df["credits"] = pd.to_numeric(df["credits"], errors="coerce")
        df["total_marks"] = pd.to_numeric(df["total_marks"], errors="coerce")
        df["programme"] = df["programme"].fillna("")
        df["section"] = df["section"].fillna("")
        df["batch"] = df["batch"].fillna("")
        return df


def _safe(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else round(f, 4)
    except (TypeError, ValueError):
        return None


def _determine_status(sgpa: float) -> str:
    if sgpa >= 9.0:
        return "DISTINCTION"
    elif sgpa >= 7.5:
        return "FIRST_CLASS"
    elif sgpa >= 6.0:
        return "SECOND_CLASS"
    else:
        return "PASS"
