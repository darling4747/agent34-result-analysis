"""General-purpose helper utilities."""
from __future__ import annotations
import math
import os
import re

COLUMN_ALIASES: dict[str, str] = {
    "roll_no": "roll_number",
    "rollno": "roll_number",
    "htno": "roll_number",
    "hall_ticket": "roll_number",
    "hall_ticket_no": "roll_number",
    "hallticketno": "roll_number",
    "reg_no": "roll_number",
    "regno": "roll_number",
    "registration_no": "roll_number",
    "student_id": "roll_number",
    "pin": "roll_number",
    "student_roll_number": "roll_number",
    "usn": "roll_number",
    "enrollment_no": "roll_number",
    "enrollment_number": "roll_number",
    "enrollment": "roll_number",
    "sno": "sl_no",
    "sl_no": "sl_no",

    "name": "student_name",
    "name_of_the_student": "student_name",
    "candidate_name": "student_name",
    "sname": "student_name",

    "sub_code": "course_code",
    "subject_code": "course_code",
    "subjectcode": "course_code",
    "subcode": "course_code",
    "course_id": "course_code",
    "paper_code": "course_code",
    "ccode": "course_code",
    "code": "course_code",

    "sub_name": "course_name",
    "subject_name": "course_name",
    "subjectname": "course_name",
    "subname": "course_name",
    "subject": "course_name",
    "paper_name": "course_name",
    "cname": "course_name",
    "title": "course_name",
    "course_title": "course_name",

    "internal": "internal_marks",
    "internals": "internal_marks",
    "mid_marks": "internal_marks",
    "mids": "internal_marks",
    "cia": "internal_marks",
    "im": "internal_marks",
    "int_marks": "internal_marks",
    "int": "internal_marks",

    "external": "external_marks",
    "externals": "external_marks",
    "end_sem_marks": "external_marks",
    "end_sem": "external_marks",
    "see": "external_marks",
    "em": "external_marks",
    "ext_marks": "external_marks",
    "ext": "external_marks",

    "total": "total_marks",
    "tot": "total_marks",
    "tot_marks": "total_marks",
    "marks_obtained": "total_marks",
    "grand_total": "total_marks",
    "final_marks": "total_marks",
    "marks": "total_marks",

    "grade_letter": "grade",
    "lg": "grade",
    "letter_grade": "grade",

    "grade_points": "grade_point",
    "gp": "grade_point",
    "point": "grade_point",
    "points": "grade_point",

    "result": "result_status",
    "status": "result_status",
    "pass_fail": "result_status",
    "pf": "result_status",
    "res": "result_status",

    "branch": "department",
    "dept": "department",
    "branch_name": "department",
    "program": "programme",
    "sec": "section",
    "teacher": "faculty",
    "faculty_name": "faculty",
    "instructor": "faculty",
}

def normalise_column_name(name: str) -> str:
    """Lowercase, strip, replace spaces/hyphens with underscore, map common aliases."""
    raw = str(name).strip().lower()
    cleaned = re.sub(r"[\s\-]+", "_", raw)
    cleaned = re.sub(r"[^\w]", "", cleaned)
    return COLUMN_ALIASES.get(cleaned, cleaned)


def safe_float(val, default=None) -> float | None:
    """Convert to float, return default on failure."""
    if val is None:
        return default
    try:
        result = float(val)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (ValueError, TypeError):
        return default


def safe_int(val, default=None) -> int | None:
    """Convert to int, return default on failure."""
    if val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def ensure_dirs(paths: list[str]) -> None:
    """Create directories if they do not exist."""
    for path in paths:
        os.makedirs(path, exist_ok=True)


def nan_safe_dict(d: dict) -> dict:
    """Recursively replace NaN/Inf/-Inf with None in a dict."""
    result = {}
    for key, value in d.items():
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                result[key] = None
            else:
                result[key] = value
        elif isinstance(value, dict):
            result[key] = nan_safe_dict(value)
        elif isinstance(value, list):
            result[key] = [nan_safe_dict(i) if isinstance(i, dict) else i for i in value]
        else:
            result[key] = value
    return result


def format_academic_period(semester: int, academic_year: str) -> str:
    """Return e.g. 'Semester 6 — 2025-26'"""
    return f"Semester {semester} \u2014 {academic_year}"


def nan_safe_list(lst: list) -> list:
    """Recursively clean a list of dicts for JSON safety."""
    cleaned = []
    for item in lst:
        if isinstance(item, dict):
            cleaned.append(nan_safe_dict(item))
        elif isinstance(item, float) and (math.isnan(item) or math.isinf(item)):
            cleaned.append(None)
        else:
            cleaned.append(item)
    return cleaned
