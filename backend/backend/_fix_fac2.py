import pathlib

BASE = pathlib.Path(r"c:\Users\HP Victus\OneDrive - Vignan University\Pictures\project\backend\backend")
p = BASE / "app" / "services" / "faculty_analysis.py"
src = p.read_text(encoding='utf-8')

# Fix get_faculty to handle NULL faculty_id by grouping on course_code when no faculty data
old_group = (
    "        results = []\n"
    "        for faculty_id_val, grp in df.groupby(\"faculty_id\"):"
)
new_group = (
    "        results = []\n"
    "        # If no faculty_id data exists, group by course_code as a fallback\n"
    "        has_any_faculty_id = df['faculty_id'].notna().any()\n"
    "        if not has_any_faculty_id:\n"
    "            # Fill faculty_name with course_code when no faculty data\n"
    "            df['faculty_id'] = df['course_code']\n"
    "            df['faculty_name'] = df['course_code'].apply(lambda x: f'Course: {x}')\n"
    "        for faculty_id_val, grp in df.groupby(\"faculty_id\"):"
)

if old_group in src:
    src = src.replace(old_group, new_group)
    p.write_text(src, encoding='utf-8')
    print("get_faculty: course-code fallback grouping added")
else:
    print("pattern not found")