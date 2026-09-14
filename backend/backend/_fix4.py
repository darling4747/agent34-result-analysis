import pathlib

p = pathlib.Path(r"c:\Users\HP Victus\OneDrive - Vignan University\Pictures\project\backend\backend\app\services\faculty_analysis.py")
lines = p.read_text(encoding='utf-8').splitlines()
LF = chr(10)

new_lines = []
for line in lines:
    if '"faculty_id": int(faculty_id_val) if faculty_id_val is not None else None,' in line:
        # Make it safe: try int, fall back to string
        new_lines.append(line.replace(
            '"faculty_id": int(faculty_id_val) if faculty_id_val is not None else None,',
            '"faculty_id": (int(faculty_id_val) if str(faculty_id_val).isdigit() else str(faculty_id_val)) if faculty_id_val is not None else None,'
        ))
    else:
        new_lines.append(line)

p.write_text(LF.join(new_lines), encoding='utf-8')
print("faculty_id cast fixed")