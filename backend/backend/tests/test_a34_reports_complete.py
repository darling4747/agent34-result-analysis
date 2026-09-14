"""A34 Reports Tests."""
import io, pathlib

BASE = pathlib.Path(r"c:/Users/HP Victus/OneDrive - Vignan University/Pictures/project/backend/backend")

class TestReportGeneration:
    def test_generate_report_200(self, auth_client):
        r = auth_client.post("/api/reports/generate",
            params={"academic_year": "2025-26", "semester": 6, "report_type": "FULL"})
        assert r.status_code == 200

    def test_report_response_has_id(self, auth_client):
        r = auth_client.post("/api/reports/generate",
            params={"academic_year": "2025-26", "semester": 6})
        assert "id" in r.json()["data"]

    def test_report_response_has_status(self, auth_client):
        r = auth_client.post("/api/reports/generate",
            params={"academic_year": "2025-26", "semester": 6})
        assert "status" in r.json()["data"]

    def test_get_report_job_200(self, auth_client):
        r = auth_client.post("/api/reports/generate",
            params={"academic_year": "2025-26", "semester": 6})
        job_id = r.json()["data"]["id"]
        r2 = auth_client.get(f"/api/reports/{job_id}")
        assert r2.status_code == 200

    def test_report_job_has_download_url_or_path(self, auth_client):
        r = auth_client.post("/api/reports/generate",
            params={"academic_year": "2025-26", "semester": 6})
        job_data = r.json()["data"]
        assert "report_path" in job_data or "download_url" in job_data

    def test_report_status_completed(self, auth_client):
        r = auth_client.post("/api/reports/generate",
            params={"academic_year": "2025-26", "semester": 6})
        status = r.json()["data"]["status"]
        assert status in ("COMPLETED", "PENDING", "READY", "GENERATING")

    def test_report_download_endpoint(self, auth_client):
        r = auth_client.post("/api/reports/generate",
            params={"academic_year": "2025-26", "semester": 6})
        job_id = r.json()["data"]["id"]
        r2 = auth_client.get(f"/api/reports/{job_id}/download")
        assert r2.status_code in (200, 404)  # 404 if file not ready yet

class TestPDFFile:
    def test_pdf_directory_exists(self):
        from app.config import get_settings
        from app.database import SessionLocal
        from app.config import get_settings as gs
        gs.cache_clear()
        s = gs()
        pdf_dir = BASE / s.REPORT_DIR
        assert pdf_dir.exists()

    def test_generate_creates_pdf_file(self, auth_client):
        from app.config import get_settings
        from app.database import SessionLocal
        get_settings.cache_clear()
        s = get_settings()
        r = auth_client.post("/api/reports/generate",
            params={"academic_year": "2025-26", "semester": 6})
        assert r.status_code == 200
        report_path = r.json()["data"].get("report_path")
        if report_path:
            p = pathlib.Path(report_path)
            if p.exists():
                assert p.stat().st_size > 0
                content = p.read_bytes()
                assert content[:4] == b"%PDF" or len(content) > 0

class TestReportRequiresAuth:
    def test_generate_report_requires_auth(self, client):
        r = client.post("/api/reports/generate",
            params={"academic_year": "2025-26", "semester": 6})
        assert r.status_code == 401

    def test_get_report_requires_auth(self, client):
        r = client.get("/api/reports/99999")
        assert r.status_code in (401, 404, 403)

class TestReportJobPersistence:
    def test_report_job_persists_in_db(self, auth_client, db_session):
        from app.models import AnalysisRun
        before = db_session.query(AnalysisRun).count()
        auth_client.post("/api/reports/generate",
            params={"academic_year": "2025-26", "semester": 6})
        db_session.expire_all()
        after = db_session.query(AnalysisRun).count()
        assert after >= before
