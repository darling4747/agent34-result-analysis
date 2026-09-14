import pathlib

TESTS = pathlib.Path(r"c:\Users\HP Victus\OneDrive - Vignan University\Pictures\project\backend\backend\tests")
p = TESTS / "test_a34_comprehensive.py"
src = p.read_text(encoding='utf-8')
# Remove the bad TestDollar! password (too short) - replace with valid one
src = src.replace('"TestDollar!",', '"TestDollarLong1234!",')
p.write_text(src, encoding='utf-8')
print("Fixed TestDollar!")