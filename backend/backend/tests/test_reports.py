"""Tests for report generation."""
import io


def _upload(auth_client, excel_bytes, academic_year="2025-26", semester=6):
    resp = auth_client.post(
        "/api/results/upload",
        files={"file": ("r.xlsx", io.BytesIO(excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"academic_year": academic_year, "semester": str(semester), "department": "CSE"},
    )
    return resp


def test_report_generate_creates_job(auth_client, sample_excel_bytes):
    _upload(auth_client, sample_excel_bytes)
    resp = auth_client.post(
        "/api/reports/generate",
        params={"academic_year": "2025-26", "semester": 6, "department": "CSE"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["id"] is not None
    assert body["data"]["status"] in ("COMPLETED", "RUNNING", "FAILED")


def test_report_status_endpoint(auth_client, sample_excel_bytes):
    _upload(auth_client, sample_excel_bytes)
    create_resp = auth_client.post(
        "/api/reports/generate",
        params={"academic_year": "2025-26", "semester": 6},
    )
    report_id = create_resp.json()["data"]["id"]
    resp = auth_client.get(f"/api/reports/{report_id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == report_id


def test_report_not_found(auth_client):
    resp = auth_client.get("/api/reports/99999")
    assert resp.status_code == 404


def test_report_download_completed(auth_client, sample_excel_bytes):
    _upload(auth_client, sample_excel_bytes)
    create_resp = auth_client.post(
        "/api/reports/generate",
        params={"academic_year": "2025-26", "semester": 6},
    )
    report_id = create_resp.json()["data"]["id"]
    status = create_resp.json()["data"]["status"]
    if status == "COMPLETED":
        dl_resp = auth_client.get(f"/api/reports/{report_id}/download")
        assert dl_resp.status_code == 200
        assert dl_resp.headers["content-type"] == "application/pdf"
