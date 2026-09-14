import pathlib

TESTS = pathlib.Path(r"c:\Users\HP Victus\OneDrive - Vignan University\Pictures\project\backend\backend\tests")
p = TESTS / "test_a34_analytics_complete.py"
src = p.read_text(encoding='utf-8')

# Remove the class scope from the fixture - change @pytest.fixture(scope="class") to @pytest.fixture
src = src.replace(
    '@pytest.fixture(scope="class")',
    '@pytest.fixture'
)
p.write_text(src, encoding='utf-8')
print("Scope mismatch fixed in test_a34_analytics_complete.py")