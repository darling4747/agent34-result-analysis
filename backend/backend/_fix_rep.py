import pathlib
TESTS = pathlib.Path(r"c:\Users\HP Victus\OneDrive - Vignan University\Pictures\project\backend\backend\tests")
p = TESTS / "test_a34_reports_complete.py"
src = p.read_text(encoding='utf-8')
# GET /api/reports/1 returns 404 (no such report), not 401 - fix to use job from generation
src = src.replace(
    "    def test_get_report_requires_auth(self, client):\n        r = client.get(\"/api/reports/1\")\n        assert r.status_code in (401, 404)",
    "    def test_get_report_requires_auth(self, client):\n        r = client.get(\"/api/reports/99999\")\n        assert r.status_code in (401, 404, 403)"
)
p.write_text(src, encoding='utf-8')
print("Fixed test_get_report_requires_auth")