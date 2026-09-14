import pathlib

BASE = pathlib.Path(r"c:\Users\HP Victus\OneDrive - Vignan University\Pictures\project\backend\backend")

p = BASE / "app" / "services" / "faculty_analysis.py"
src = p.read_text(encoding='utf-8')

# Replace the _query_rows method to include results WITHOUT faculty_id
# (fall back to course-level grouping when no faculty data exists)
old = (
    "        query = (\n"
    "            self.db.query(\n"
    "                Result.student_id,\n"
    "                Result.result_status,\n"
    "                Result.total_marks,\n"
    "                Result.faculty_id,\n"
    "                Faculty.faculty_name,\n"
    "                Student.department,\n"
    "                Course.course_code,\n"
    "            )\n"
    "            .join(Student, Result.student_id == Student.id)\n"
    "            .join(Course, Result.course_id == Course.id)\n"
    "            .outerjoin(Faculty, Result.faculty_id == Faculty.id)\n"
    "            .filter(Result.faculty_id.isnot(None))\n"
    "        )"
)
new = (
    "        # Check if any results have faculty_id set\n"
    "        has_faculty = self.db.query(Result).filter(Result.faculty_id.isnot(None)).limit(1).first() is not None\n"
    "\n"
    "        query = (\n"
    "            self.db.query(\n"
    "                Result.student_id,\n"
    "                Result.result_status,\n"
    "                Result.total_marks,\n"
    "                Result.faculty_id,\n"
    "                Faculty.faculty_name,\n"
    "                Student.department,\n"
    "                Course.course_code,\n"
    "            )\n"
    "            .join(Student, Result.student_id == Student.id)\n"
    "            .join(Course, Result.course_id == Course.id)\n"
    "            .outerjoin(Faculty, Result.faculty_id == Faculty.id)\n"
    "        )\n"
    "        # Only filter by faculty_id when faculty data actually exists\n"
    "        if has_faculty:\n"
    "            query = query.filter(Result.faculty_id.isnot(None))"
)

if old in src:
    src = src.replace(old, new)
    p.write_text(src, encoding='utf-8')
    print("faculty_analysis.py: faculty_id filter made conditional")
else:
    print("Pattern not found — checking lines...")
    idx = src.find(".filter(Result.faculty_id.isnot(None))")
    print(src[max(0,idx-100):idx+60])