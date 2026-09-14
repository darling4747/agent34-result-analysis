"""Intervention prioritization service."""
from __future__ import annotations
import math

import pandas as pd
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Course, Result, Student
from ..utils.calculations import (
    compute_pass_percentage,
    compute_priority_score,
    grade_to_priority_level,
)
from ..utils.constants import IE_GAP_THRESHOLD, MIN_SAMPLE_FOR_CORRELATION
from .correlation import CorrelationService
from .historical import HistoricalService
from .section_analysis import SectionAnalysisService


class InterventionService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def get_interventions(self, filters: dict) -> list[dict]:
        """
        For each course: compute composite priority score using configured weights.
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

        weights = self._weights()
        corr_service = CorrelationService(self.db, self.settings)
        hist_service = HistoricalService(self.db, self.settings)

        corr_data = {c["course_code"]: c for c in corr_service.get_correlation(filters)}
        hist_data = {c["course_code"]: c for c in hist_service.get_historical(filters)}

        results = []
        for course_code, grp in df.groupby("course_code"):
            course_name = grp["course_name"].iloc[0]
            department = grp["department"].iloc[0] if "department" in grp.columns else None
            section = None

            total = len(grp)
            excluded = grp["result_status"].isin(["ABSENT", "WITHHELD", "DEBARRED"])
            eligible = int((~excluded).sum())
            pass_count = int((grp["result_status"] == "PASS").sum())
            fail_count = int((grp["result_status"] == "FAIL").sum())
            failure_rate = compute_pass_percentage(fail_count, eligible)

            # Historical deviation
            hist_item = hist_data.get(course_code)
            historical_deviation = hist_item.get("deviation_from_average") if hist_item else None

            # IE anomaly score
            ie_anomaly_score = self._compute_ie_anomaly_score(course_code, corr_data)

            # Section deviation — use worst section deviation for this course
            section_deviation = self._compute_section_deviation_score(course_code, filters)

            priority_score = compute_priority_score(
                failure_rate=failure_rate,
                historical_deviation=historical_deviation,
                section_deviation=section_deviation,
                ie_anomaly_score=ie_anomaly_score,
                weights=weights,
            )
            priority_level = grade_to_priority_level(priority_score)

            suggested_action = _suggest_action(priority_level, failure_rate, course_code)

            results.append({
                "course_code": course_code,
                "course_name": course_name,
                "department": str(department) if department else None,
                "section": section,
                "failure_rate": failure_rate,
                "fail_count": fail_count,
                "total_students": total,
                "priority_score": priority_score,
                "priority_level": priority_level,
                "historical_deviation": historical_deviation,
                "section_deviation": section_deviation,
                "ie_anomaly_score": ie_anomaly_score,
                "weights_used": weights,
                "suggested_action": suggested_action,
            })

        # Sort by priority score descending
        results.sort(key=lambda x: -x["priority_score"])
        return results

    def get_summary(self, filters: dict) -> dict:
        items = self.get_interventions(filters)
        total = len(items)
        critical = sum(1 for i in items if i["priority_level"] == "CRITICAL")
        high = sum(1 for i in items if i["priority_level"] == "HIGH")
        medium = sum(1 for i in items if i["priority_level"] == "MEDIUM")
        low = sum(1 for i in items if i["priority_level"] == "LOW")
        students_at_risk = sum(i["fail_count"] for i in items if i["priority_level"] in ("CRITICAL", "HIGH"))

        dept_counts: dict[str, int] = {}
        for i in items:
            if i.get("department"):
                dept_counts[i["department"]] = dept_counts.get(i["department"], 0) + i["fail_count"]
        most_affected = max(dept_counts, key=dept_counts.get) if dept_counts else None

        return {
            "total_courses_flagged": total,
            "critical_count": critical,
            "high_count": high,
            "medium_count": medium,
            "low_count": low,
            "total_students_at_risk": students_at_risk,
            "most_affected_department": most_affected,
            "weights_used": self._weights(),
        }

    # ------------------------------------------------------------------
    def _compute_ie_anomaly_score(self, course_code: str, corr_data: dict) -> float:
        """0-1 score from correlation weakness and IE gap."""
        corr_item = corr_data.get(course_code)
        if not corr_item:
            return 0.0
        score = 0.0
        interp = corr_item.get("interpretation", "")
        if interp in ("STRONG_NEGATIVE", "MODERATE_NEGATIVE"):
            score += 0.5
        elif interp in ("WEAK_NEGATIVE", "WEAK_POSITIVE", "INSUFFICIENT_DATA"):
            score += 0.25
        if "LARGE_IE_GAP" in corr_item.get("flags", []):
            score += 0.3
        if "HIGH_INTERNAL_LOW_EXTERNAL" in corr_item.get("flags", []):
            score += 0.2
        return min(score, 1.0)

    def _compute_section_deviation_score(self, course_code: str, filters: dict) -> float | None:
        """Return absolute max section deviation for this course, or None."""
        svc = SectionAnalysisService(self.db, self.settings)
        course_filters = dict(filters)
        course_filters["course_code"] = course_code
        sections = svc.get_sections(course_filters)
        if not sections:
            return None
        deviations = [abs(s["section_deviation"]) for s in sections if s.get("section_deviation") is not None]
        return max(deviations) if deviations else None

    def _compute_historical_deviation_score(self, course_code: str, filters: dict) -> float | None:
        hist_svc = HistoricalService(self.db, self.settings)
        course_filters = dict(filters)
        course_filters["course_code"] = course_code
        items = hist_svc.get_historical(course_filters)
        if not items:
            return None
        return items[0].get("deviation_from_average")

    def _weights(self) -> dict:
        return {
            "failure": self.settings.INTERVENTION_FAILURE_WEIGHT,
            "historical": self.settings.INTERVENTION_HISTORICAL_WEIGHT,
            "section": self.settings.INTERVENTION_SECTION_WEIGHT,
            "correlation": self.settings.INTERVENTION_CORRELATION_WEIGHT,
        }

    def _query_rows(self, filters: dict):
        query = (
            self.db.query(
                Result.result_status,
                Course.course_code,
                Course.course_name,
                Student.department,
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
        return query.all()

    def _to_df(self, rows) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows, columns=["result_status", "course_code", "course_name", "department"])


def _suggest_action(priority_level: str, failure_rate: float, course_code: str) -> str:
    if priority_level == "CRITICAL":
        return (
            f"Immediate academic intervention required for {course_code}. "
            f"Consider remedial classes, revised teaching strategies, and student counselling. "
            f"Failure rate: {failure_rate:.1f}%."
        )
    elif priority_level == "HIGH":
        return (
            f"Scheduled review recommended for {course_code}. "
            f"Identify and support at-risk students. Failure rate: {failure_rate:.1f}%."
        )
    elif priority_level == "MEDIUM":
        return (
            f"Monitor {course_code} in the next assessment cycle. "
            f"Provide supplementary learning materials. Failure rate: {failure_rate:.1f}%."
        )
    else:
        return f"No immediate action required for {course_code}. Continue regular monitoring."
