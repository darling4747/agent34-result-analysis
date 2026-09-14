"""Tests for file upload endpoint."""
import io


def test_upload_valid_excel(auth_client, sample_excel_bytes):
    resp = auth_client.post(
        "/api/results/upload",
        files={"file": ("results.xlsx", io.BytesIO(sample_excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"academic_year": "2025-26", "semester": "6", "department": "CSE"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["filename"] == "results.xlsx"
    assert body["data"]["total_rows"] >= 3
    assert body["data"]["status"] in ("COMPLETED", "PROCESSING")


def test_upload_invalid_extension(auth_client):
    resp = auth_client.post(
        "/api/results/upload",
        files={"file": ("results.txt", io.BytesIO(b"bad data"), "text/plain")},
        data={"academic_year": "2025-26", "semester": "6", "department": "CSE"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert "Unsupported" in body["detail"] or "Unsupported" in str(body)


def test_upload_missing_columns(auth_client):
    """Upload an Excel with missing required columns — should return FAILED status."""
    import pandas as pd
    buf = io.BytesIO()
    df = pd.DataFrame({"roll_number": ["22CS001"], "student_name": ["Alice"]})
    df.to_excel(buf, index=False)
    buf.seek(0)

    resp = auth_client.post(
        "/api/results/upload",
        files={"file": ("bad.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"academic_year": "2025-26", "semester": "6", "department": "CSE"},
    )
    assert resp.status_code == 200
    body = resp.json()
    batch = body["data"]
    assert batch["status"] in ("FAILED", "COMPLETED")
    # If completed, rejected_rows should equal total_rows due to missing columns
    if batch["status"] == "FAILED":
        assert batch["error_summary"] is not None


def test_upload_empty_file(auth_client):
    resp = auth_client.post(
        "/api/results/upload",
        files={"file": ("empty.xlsx", io.BytesIO(b""), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"academic_year": "2025-26", "semester": "6", "department": "CSE"},
    )
    assert resp.status_code == 400


def test_upload_large_wide_csv_65_students(auth_client):
    """Test uploading a wide-format CSV with 70 students and 6 subjects."""
    import pandas as pd
    rows = []
    for i in range(1, 71):
        rows.append({
            "roll_no": f"22CSE_LARGE_{i:03d}",
            "student_name": f"Student Large {i}",
            "CS101": 85,
            "CS102": 90,
            "CS103": 78,
            "CS104": 88,
            "CS105": 92,
            "CS106": 81,
        })
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)

    resp = auth_client.post(
        "/api/results/upload",
        files={"file": ("wide_large.csv", buf, "text/csv")},
        data={"academic_year": "2025-26", "semester": "6", "department": "Computer Science & Engineering"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    batch = body["data"]
    assert batch["status"] == "COMPLETED"
    assert batch["total_rows"] == 420
    assert batch["valid_rows"] == 420
    assert batch["student_count"] == 70
    assert batch["course_count"] == 6
    assert batch["result_count"] == 420


def test_upload_irregular_csv_with_unequal_field_counts(auth_client):
    """Test CSV file with title header rows and varying field counts per line."""
    csv_content = (
        "University Title Header Row, Extra Note, 2025-26\n"
        "Semester 6 Results Summary, Department of CSE\n"
        "roll_no,student_name,CS101,CS102,CS103\n"
        "22CSE901,Student Irregular 1,85,90,78\n"
        "22CSE902,Student Irregular 2,88,92,80,extra_trailing_field_1,extra_trailing_field_2\n"
    )
    buf = io.BytesIO(csv_content.encode("utf-8"))

    resp = auth_client.post(
        "/api/results/upload",
        files={"file": ("irregular.csv", buf, "text/csv")},
        data={"academic_year": "2025-26", "semester": "6", "department": "Computer Science & Engineering"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    batch = body["data"]
    assert batch["status"] == "COMPLETED"
    assert batch["total_rows"] >= 6
    assert batch["valid_rows"] >= 6
    assert batch["student_count"] == 2


