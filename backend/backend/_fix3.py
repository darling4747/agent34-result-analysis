import pathlib

p = pathlib.Path(r"c:\Users\HP Victus\OneDrive - Vignan University\Pictures\project\backend\backend\app\services\faculty_analysis.py")
lines = p.read_text(encoding='utf-8').splitlines()
for i, l in enumerate(lines[74:84], 75):
    print(i, repr(l))