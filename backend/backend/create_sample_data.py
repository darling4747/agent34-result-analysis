"""
Script to create sample Excel result files for development and testing.
Run from the backend directory:
  ./venv/Scripts/python.exe create_sample_data.py
"""
from __future__ import annotations
import os
import random

import pandas as pd

random.seed(42)

COURSES = [
    {"course_code": "CS601", "course_name": "Compiler Design", "difficulty": "hard"},
    {"course_code": "CS602", "course_name": "Computer Networks", "difficulty": "medium"},
    {"course_code": "CS603", "course_name": "Machine Learning", "difficulty": "easy"},
    {"course_code": "CS606", "course_name": "Operating Systems", "difficulty": "critical"},
]

SECTIONS = ["A", "B", "C", "D"]
TOTAL_STUDENTS = 60

FACULTY_MAP = {
    "CS601": "Dr. R. Kumar",
    "CS602": "Dr. S. Patel",
    "CS603": "Dr. A. Rao",
    "CS606": "Dr. M. Sharma",
}

GRADE_MAP = {
    (90, 100): ("O", 10),
    (80, 89): ("A+", 9),
    (70, 79): ("A", 8),
    (60, 69): ("B+", 7),
    (50, 59): ("B", 6),
    (40, 49): ("C", 5),
    (35, 39): ("P", 4),
    (0, 34): ("F", 0),
}


def get_grade(total: float):
    for (lo, hi), (grade, gp) in GRADE_MAP.items():
        if lo <= total <= hi:
            return grade, gp
    return "F", 0


def make_marks(difficulty: str, absent: bool = False):
    if absent:
        return None, None, None
    if difficulty == "easy":
        internal = random.uniform(20, 30)
        external = random.uniform(42, 70)
    elif difficulty == "medium":
        internal = random.uniform(14, 28)
        external = random.uniform(30, 63)
    elif difficulty == "hard":
        internal = random.uniform(12, 26)
        external = random.uniform(20, 55)
    else:  # critical — high failure
        internal = random.uniform(8, 22)
        external = random.uniform(10, 45)
    internal = round(min(internal, 30), 1)
    external = round(min(external, 70), 1)
    total = round(internal + external, 1)
    return internal, external, total


def generate_students(n: int):
    students = []
    for i in range(1, n + 1):
        section = SECTIONS[(i - 1) % len(SECTIONS)]
        students.append({
            "roll_number": f"22CS{i:03d}",
            "student_name": f"Student {i:03d}",
            "programme": "B.Tech",
            "department": "CSE",
            "batch": "2022",
            "section": section,
        })
    return students


def build_rows(students, courses, academic_year, semester):
    rows = []
    for student in students:
        for course in courses:
            # ~5% chance of absence
            absent = random.random() < 0.05
            internal, external, total = make_marks(course["difficulty"], absent=absent)
            if absent:
                grade, gp = None, None
                status = "ABSENT"
            else:
                grade, gp = get_grade(total)
                status = "PASS" if grade != "F" else "FAIL"

            rows.append({
                "roll_number": student["roll_number"],
                "student_name": student["student_name"],
                "programme": student["programme"],
                "department": student["department"],
                "batch": student["batch"],
                "section": student["section"],
                "course_code": course["course_code"],
                "course_name": course["course_name"],
                "faculty": FACULTY_MAP[course["course_code"]],
                "semester": semester,
                "academic_year": academic_year,
                "internal_marks": internal,
                "external_marks": external,
                "total_marks": total,
                "grade": grade,
                "grade_point": gp,
                "result_status": status,
                "credits": 4,
                "attempt_number": 1,
            })
    return rows


def main():
    os.makedirs("sample_data", exist_ok=True)
    students = generate_students(TOTAL_STUDENTS)

    # Current results: 2025-26 Semester 6
    current_rows = build_rows(students, COURSES, "2025-26", 6)
    df_current = pd.DataFrame(current_rows)
    out_path = os.path.join("sample_data", "sample_results.xlsx")
    df_current.to_excel(out_path, index=False)
    print(f"Created {out_path} with {len(df_current)} rows")

    # Stats
    for cc in [c["course_code"] for c in COURSES]:
        subset = df_current[df_current["course_code"] == cc]
        eligible = subset[~subset["result_status"].isin(["ABSENT", "WITHHELD"])].shape[0]
        pass_c = (subset["result_status"] == "PASS").sum()
        fail_c = (subset["result_status"] == "FAIL").sum()
        print(f"  {cc}: {pass_c} pass / {fail_c} fail / eligible={eligible} => {100*pass_c/eligible:.1f}% pass")

    # Historical results: 2024-25 Semester 6 (slightly different marks)
    # Modify marks slightly for historical variation
    hist_rows = []
    for row in build_rows(students, COURSES, "2024-25", 6):
        row = dict(row)
        if row["result_status"] not in ("ABSENT",):
            # perturb marks by +/- 5
            delta = random.uniform(-5, 5)
            if row["internal_marks"] is not None:
                row["internal_marks"] = round(max(0, min(30, row["internal_marks"] + random.uniform(-3, 3))), 1)
                row["external_marks"] = round(max(0, min(70, row["external_marks"] + delta)), 1)
                row["total_marks"] = round(row["internal_marks"] + row["external_marks"], 1)
                row["grade"], row["grade_point"] = get_grade(row["total_marks"])
                row["result_status"] = "PASS" if row["grade"] != "F" else "FAIL"
        hist_rows.append(row)

    df_hist = pd.DataFrame(hist_rows)
    hist_path = os.path.join("sample_data", "sample_historical_results.xlsx")
    df_hist.to_excel(hist_path, index=False)
    print(f"Created {hist_path} with {len(df_hist)} rows")


if __name__ == "__main__":
    main()
