import pathlib

BASE = pathlib.Path(r"c:\Users\HP Victus\OneDrive - Vignan University\Pictures\project\backend\backend")

# Fix results.py — remove .pdf from allowed extensions
p = BASE / "app" / "api" / "routes" / "results.py"
src = p.read_text(encoding='utf-8')
src = src.replace(
    'if ext not in (".xlsx", ".xls", ".csv", ".pdf"):',
    'if ext not in (".xlsx", ".xls", ".csv"):'
)
src = src.replace(
    "detail=f\"Unsupported file type '{ext}'. Upload .xlsx, .xls, .csv, or .pdf only.\"",
    "detail=f\"Unsupported file type '{ext}'. Upload .xlsx, .xls, or .csv only.\""
)
p.write_text(src, encoding='utf-8')
print("results.py: .pdf removed from allowed extensions")

# Verify
check = p.read_text(encoding='utf-8')
print("pdf in allowed list:", ".pdf" in check.split("if ext not in")[1].split(")")[0])