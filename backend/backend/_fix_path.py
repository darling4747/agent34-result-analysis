import pathlib, re

BASE = pathlib.Path(r"c:\Users\HP Victus\OneDrive - Vignan University\Pictures\project\backend\backend")
p = BASE / "app" / "api" / "routes" / "results.py"
src = p.read_text(encoding='utf-8')

# Add filename sanitization after the extension check
old = (
    "    # Validate extension\n"
    "    if not file.filename:\n"
    "        raise HTTPException(status_code=400, detail=\"No filename provided.\")\n"
    "    ext = os.path.splitext(file.filename)[1].lower()"
)
new = (
    "    # Validate extension\n"
    "    if not file.filename:\n"
    "        raise HTTPException(status_code=400, detail=\"No filename provided.\")\n"
    "    # Sanitize filename to prevent path traversal\n"
    "    safe_filename = os.path.basename(file.filename.replace('..', '').replace('/', '_').replace('\\\\', '_'))\n"
    "    if not safe_filename:\n"
    "        raise HTTPException(status_code=400, detail=\"Invalid filename.\")\n"
    "    ext = os.path.splitext(safe_filename)[1].lower()"
)
if old in src:
    src = src.replace(old, new)
    # Also update the save_path to use safe_filename
    src = src.replace(
        "    safe_name = f\"{timestamp}_{file.filename}\"",
        "    safe_name = f\"{timestamp}_{safe_filename}\""
    )
    p.write_text(src, encoding='utf-8')
    print("Path traversal protection added to results.py")
else:
    print("Pattern not found — checking...")
    idx = src.find("if not file.filename:")
    print(src[idx:idx+200])