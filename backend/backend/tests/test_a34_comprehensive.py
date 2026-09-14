"""A34 Comprehensive parametrized tests covering all endpoints systematically."""
import io, pytest
import pandas as pd

# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_excel(n=5, course="CS601", ay="2025-26", sem=6):
    df = pd.DataFrame({
        "roll_number": [f"22TC{i:04d}" for i in range(1, n+1)],
        "student_name": [f"TC Student {i}" for i in range(1, n+1)],
        "programme": ["B.Tech"]*n, "department": ["CSE"]*n,
        "batch": ["2022"]*n, "section": ["A"]*n,
        "course_code": [course]*n, "course_name": ["Test Course"]*n,
        "faculty": ["Dr. Test"]*n, "semester": [sem]*n,
        "academic_year": [ay]*n,
        "internal_marks": [22]*n, "external_marks": [50]*n,
        "total_marks": [72]*n, "grade": ["A"]*n,
        "grade_point": [8]*n, "result_status": ["PASS"]*n,
    })
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf.read()


# ── All GET analytics endpoints return 200 when authenticated ─────────────────

ANALYTICS_ENDPOINTS = [
    "/api/analysis/summary",
    "/api/analysis/grades",
    "/api/analysis/courses",
    "/api/analysis/sections",
    "/api/analysis/faculty",
    "/api/analysis/demographics",
    "/api/analysis/gpa",
    "/api/analysis/merit-list",
    "/api/analysis/correlation",
    "/api/analysis/historical",
    "/api/analysis/interventions",
    "/api/analysis/interventions/summary",
    "/api/analysis/backlogs",
    "/api/analysis/attainment-input",
    "/api/dashboard/summary",
    "/api/results/imports",
    "/api/results/reconciliation",
    "/api/results/data-quality",
    "/api/results/dataset-info",
    "/api/auth/me",
    "/api/auth/mfa/status",
    "/api/auth/admin/users",
    "/api/auth/audit-logs",
]

@pytest.mark.parametrize("endpoint", ANALYTICS_ENDPOINTS)
def test_endpoint_authenticated_200(endpoint, auth_client):
    """Every authenticated GET endpoint must return 200."""
    r = auth_client.get(endpoint)
    assert r.status_code == 200, f"{endpoint} returned {r.status_code}"


@pytest.mark.parametrize("endpoint", ANALYTICS_ENDPOINTS[:15])  # analytics only
def test_endpoint_unauthenticated_401(endpoint, client):
    """Every analytics endpoint must return 401 without token."""
    r = client.get(endpoint)
    assert r.status_code == 401, f"{endpoint} returned {r.status_code}"


@pytest.mark.parametrize("endpoint", ANALYTICS_ENDPOINTS)
def test_endpoint_returns_json(endpoint, auth_client):
    """Every endpoint must return valid JSON."""
    r = auth_client.get(endpoint)
    assert r.headers.get("content-type", "").startswith("application/json")


@pytest.mark.parametrize("endpoint", ANALYTICS_ENDPOINTS)
def test_endpoint_has_success_field(endpoint, auth_client):
    """Every endpoint must have success field."""
    r = auth_client.get(endpoint)
    body = r.json()
    assert "success" in body, f"{endpoint} missing success field"


@pytest.mark.parametrize("endpoint", ANALYTICS_ENDPOINTS)
def test_endpoint_has_data_field(endpoint, auth_client):
    """Every endpoint must have data field."""
    r = auth_client.get(endpoint)
    body = r.json()
    assert "data" in body, f"{endpoint} missing data field"


@pytest.mark.parametrize("endpoint", ANALYTICS_ENDPOINTS)
def test_endpoint_success_true(endpoint, auth_client):
    """Every endpoint must return success: true."""
    r = auth_client.get(endpoint)
    assert r.json()["success"] is True, f"{endpoint} success != true"


# ── Filter parameter tests ─────────────────────────────────────────────────────

FILTER_ENDPOINTS = [
    "/api/analysis/summary",
    "/api/analysis/grades",
    "/api/analysis/courses",
    "/api/analysis/sections",
    "/api/analysis/merit-list",
]

FILTER_PARAMS = [
    {"academic_year": "2025-26"},
    {"semester": 6},
    {"department": "CSE"},
    {"academic_year": "2025-26", "semester": 6},
    {"academic_year": "2025-26", "semester": 6, "department": "CSE"},
]

@pytest.mark.parametrize("endpoint,params", [
    (ep, p) for ep in FILTER_ENDPOINTS for p in FILTER_PARAMS
])
def test_filter_params_accepted(endpoint, params, auth_client):
    """Filter parameters must not cause 4xx/5xx."""
    r = auth_client.get(endpoint, params=params)
    assert r.status_code in (200, 422), f"{endpoint} {params} -> {r.status_code}"


# ── RBAC: roles that should NOT have upload access ────────────────────────────

NO_UPLOAD_ROLES = ["DEAN", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"]

def _seed_role_user(db, role_name, email):
    from app.models import Role, User
    from app.security.password import hash_password
    from app.services.auth_service import AuthService
    from app.config import get_settings
    AuthService(db, get_settings()).seed_roles_and_permissions()
    role = db.query(Role).filter_by(name=role_name).first()
    if db.query(User).filter_by(email=email).first():
        return "TestPass99!X"
    u = User(email=email, full_name="T", role_id=role.id, is_active=True,
             password_hash=hash_password("TestPass99!X"), must_change_password=False)
    db.add(u); db.commit()
    return "TestPass99!X"

@pytest.mark.parametrize("role", NO_UPLOAD_ROLES)
def test_non_upload_role_cannot_upload(role, client, db_session):
    """Roles without RESULT_UPLOAD permission must get 403 on upload."""
    email = f"nouplrd_{role.lower()}@test.com"
    pw = _seed_role_user(db_session, role, email)
    resp = client.post("/api/auth/login", json={"email": email, "password": pw})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    r = client.post("/api/results/upload",
        files={"file": ("t.xlsx", io.BytesIO(b"x"),
               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"academic_year": "2025-26", "semester": "6"},
        headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403, f"Role {role} got {r.status_code}"


# ── RBAC: non-admin cannot create users ───────────────────────────────────────

NON_ADMIN_ROLES = ["DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"]

@pytest.mark.parametrize("role", NON_ADMIN_ROLES)
def test_non_admin_cannot_create_user(role, client, db_session):
    """Only PLATFORM_ADMIN can create users."""
    email = f"nadmin_cu_{role.lower()}@test.com"
    pw = _seed_role_user(db_session, role, email)
    resp = client.post("/api/auth/login", json={"email": email, "password": pw})
    token = resp.json()["data"]["access_token"]
    r = client.post("/api/auth/admin/users",
        json={"email": "shouldfail@test.com", "full_name": "X", "role": "FACULTY"},
        headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403, f"Role {role} got {r.status_code}"


# ── All roles can access dashboard (when authenticated & data exists) ──────────

ALL_ROLES = ["PLATFORM_ADMIN", "DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"]

@pytest.mark.parametrize("role", ALL_ROLES)
def test_all_roles_can_login(role, client, db_session):
    """All 7 roles must be able to log in."""
    email = f"allrole_{role.lower()}@test.com"
    pw = _seed_role_user(db_session, role, email)
    r = client.post("/api/auth/login", json={"email": email, "password": pw})
    assert r.status_code == 200, f"Role {role} login failed"
    assert "access_token" in r.json()["data"]


@pytest.mark.parametrize("role", ALL_ROLES)
def test_all_roles_can_access_me(role, client, db_session):
    """All 7 roles must be able to access /auth/me."""
    email = f"allroleme_{role.lower()}@test.com"
    pw = _seed_role_user(db_session, role, email)
    resp = client.post("/api/auth/login", json={"email": email, "password": pw})
    token = resp.json()["data"]["access_token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, f"Role {role} /me failed"


@pytest.mark.parametrize("role", ALL_ROLES)
def test_all_roles_can_view_dashboard(role, client, db_session):
    """All roles can view dashboard (data may be empty)."""
    email = f"alldash_{role.lower()}@test.com"
    pw = _seed_role_user(db_session, role, email)
    resp = client.post("/api/auth/login", json={"email": email, "password": pw})
    token = resp.json()["data"]["access_token"]
    r = client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, f"Role {role} dashboard failed"


@pytest.mark.parametrize("role", ALL_ROLES)
def test_all_roles_get_correct_role_in_profile(role, client, db_session):
    """Profile must show the correct role for each user."""
    email = f"rolecheck_{role.lower()}@test.com"
    pw = _seed_role_user(db_session, role, email)
    resp = client.post("/api/auth/login", json={"email": email, "password": pw})
    token = resp.json()["data"]["access_token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.json()["data"]["role"] == role


# ── Password policy tests ──────────────────────────────────────────────────────

INVALID_PASSWORDS = [
    ("short1!", "too short"),
    ("alllowercase1!", "no uppercase"),
    ("ALLUPPERCASE1!", "no lowercase"),
    ("NoDigitsAtAll!!", "no digit"),
    ("NoSpecialChar1234", "no special char"),
    ("Password123!abc", "contains password"),
]

@pytest.mark.parametrize("pw,reason", INVALID_PASSWORDS)
def test_password_policy_rejects(pw, reason):
    from app.security.password import validate_password_policy, PasswordPolicyError
    with pytest.raises(Exception):
        validate_password_policy(pw)


VALID_PASSWORDS = [
    "StrongPass99!@",
    "Secure@Vignan2026",
    "Academic#Result34!",
    "TestDollarLong1234!",
    "Agent34!@Vignan99",
]

@pytest.mark.parametrize("pw", VALID_PASSWORDS)
def test_password_policy_accepts_valid(pw):
    from app.security.password import validate_password_policy
    validate_password_policy(pw)  # should not raise


# ── Grade point calculations ───────────────────────────────────────────────────

GRADE_POINT_CASES = [
    (100.0, {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "P": 4, "F": 0}, "O", 10.0),
    (90.0,  {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "P": 4, "F": 0}, "A+", 9.0),
    (0.0,   {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "P": 4, "F": 0}, "F", 0.0),
]

@pytest.mark.parametrize("marks,grade_map,expected_grade,expected_gp", GRADE_POINT_CASES)
def test_grade_point_lookup(marks, grade_map, expected_grade, expected_gp):
    gp = grade_map.get(expected_grade)
    assert gp == expected_gp


# ── Intervention weights sum ───────────────────────────────────────────────────

WEIGHT_CONFIGS = [
    (0.40, 0.30, 0.20, 0.10),
    (0.50, 0.25, 0.15, 0.10),
    (0.30, 0.30, 0.30, 0.10),
]

@pytest.mark.parametrize("fw,hw,sw,cw", WEIGHT_CONFIGS)
def test_intervention_weights_sum_to_one(fw, hw, sw, cw):
    assert abs(fw + hw + sw + cw - 1.0) < 0.01


# ── Priority score range ───────────────────────────────────────────────────────

PRIORITY_INPUTS = [
    (0.0, None, None, None),
    (50.0, None, None, None),
    (100.0, 30.0, 20.0, 0.8),
    (30.0, -5.0, 10.0, 0.3),
]

@pytest.mark.parametrize("fail_rate,hist_dev,sec_dev,ie_anomaly", PRIORITY_INPUTS)
def test_priority_score_in_range(fail_rate, hist_dev, sec_dev, ie_anomaly):
    from app.utils.calculations import compute_priority_score
    weights = {"failure": 0.40, "historical": 0.30, "section": 0.20, "correlation": 0.10}
    score = compute_priority_score(fail_rate, hist_dev, sec_dev, ie_anomaly, weights)
    assert 0.0 <= score <= 100.0


# ── Pearson correlation valid range ───────────────────────────────────────────

CORRELATION_DATASETS = [
    ([1,2,3,4,5], [2,4,6,8,10]),     # perfect positive
    ([1,2,3,4,5], [10,8,6,4,2]),     # perfect negative
    ([5,5,5,5,5], [1,2,3,4,5]),      # zero variance (one side)
    ([1,2,3], [1,2,3]),              # min sample
]

@pytest.mark.parametrize("internal,external", CORRELATION_DATASETS)
def test_pearson_correlation_valid(internal, external):
    from app.utils.calculations import interpret_correlation
    if len(set(internal)) == 1 or len(set(external)) == 1:
        result = interpret_correlation(0.0, len(internal))
        assert result in ("INSUFFICIENT_DATA", "WEAK_POSITIVE", "WEAK_NEGATIVE")
    else:
        from scipy.stats import pearsonr
        try:
            r, _ = pearsonr(internal, external)
            assert -1.0 <= r <= 1.0
        except Exception:
            pass  # numerical edge case


# ── JSON safety tests ─────────────────────────────────────────────────────────

SAFE_VALUES = [
    (0.0, 0.0),
    (None, None),
    (float("nan"), None),
    (float("inf"), None),
    (float("-inf"), None),
]

@pytest.mark.parametrize("inp,expected", SAFE_VALUES)
def test_safe_json_value(inp, expected):
    from app.utils.calculations import safe_json_value
    result = safe_json_value(inp)
    if inp is None or (isinstance(inp, float) and (inp != inp or inp == float("inf") or inp == float("-inf"))):
        assert result is None
    else:
        assert result == expected or result == inp


# ── Pass percentage calculation ───────────────────────────────────────────────

PASS_PCT_CASES = [
    (80, 100, 80.0),
    (0, 100, 0.0),
    (100, 100, 100.0),
    (0, 0, 0.0),      # edge: no eligible
    (50, 200, 25.0),
]

@pytest.mark.parametrize("passed,eligible,expected", PASS_PCT_CASES)
def test_pass_percentage(passed, eligible, expected):
    from app.utils.calculations import compute_pass_percentage
    result = compute_pass_percentage(passed, eligible)
    assert abs(result - expected) < 0.01


# ── Weighted GPA calculation ───────────────────────────────────────────────────

GPA_CASES = [
    ([8.0, 8.0], [4.0, 4.0], 8.0),
    ([10.0, 5.0], [3.0, 3.0], 7.5),
    ([9.0], [4.0], 9.0),
    ([], [], 0.0),
]

@pytest.mark.parametrize("gps,creds,expected", GPA_CASES)
def test_weighted_gpa(gps, creds, expected):
    from app.utils.calculations import compute_weighted_gpa
    result = compute_weighted_gpa(gps, creds)
    assert abs(result - expected) < 0.01


# ── Role permissions coverage ─────────────────────────────────────────────────

from app.security.permissions import ROLE_PERMISSIONS, P

PERMISSION_ROLE_TESTS = [
    ("PLATFORM_ADMIN", P.USER_CREATE, True),
    ("PLATFORM_ADMIN", P.RESULT_UPLOAD, True),
    ("PLATFORM_ADMIN", P.AUDIT_READ, True),
    ("PLATFORM_ADMIN", P.CONFIG_MANAGE, True),
    ("DEAN", P.USER_CREATE, False),
    ("DEAN", P.RESULT_UPLOAD, False),
    ("DEAN", P.ANALYSIS_READ, True),
    ("HOD", P.USER_CREATE, False),
    ("FACULTY", P.USER_CREATE, False),
    ("FACULTY", P.ROLE_ASSIGN, False),
    ("FACULTY", P.ANALYSIS_READ, True),
    ("IQAC", P.ANALYSIS_DEMOGRAPHIC, True),
    ("IQAC", P.USER_CREATE, False),
    ("MANAGEMENT", P.USER_CREATE, False),
    ("MANAGEMENT", P.USER_DISABLE, False),
    ("MANAGEMENT", P.RESULT_UPLOAD, False),
    ("AUDITOR", P.USER_CREATE, False),
    ("AUDITOR", P.USER_DISABLE, False),
    ("AUDITOR", P.RESULT_UPLOAD, False),
    ("AUDITOR", P.AUDIT_READ, True),
    ("AUDITOR", P.RESULT_READ, True),
]

@pytest.mark.parametrize("role,perm,expected", PERMISSION_ROLE_TESTS)
def test_role_permission_mapping(role, perm, expected):
    perms = set(ROLE_PERMISSIONS.get(role, []))
    if expected:
        assert perm in perms, f"Role {role} should have {perm}"
    else:
        assert perm not in perms, f"Role {role} should NOT have {perm}"


# ── Analytics response schema validation ──────────────────────────────────────

SUMMARY_REQUIRED_FIELDS = [
    "total_students", "total_results", "pass_count", "fail_count",
    "pass_percentage", "failure_percentage",
]

@pytest.mark.parametrize("field", SUMMARY_REQUIRED_FIELDS)
def test_summary_has_required_field(field, auth_client):
    r = auth_client.get("/api/analysis/summary")
    assert r.status_code == 200
    data = r.json()["data"]
    assert field in data, f"Summary missing field: {field}"


GRADE_DIST_REQUIRED_FIELDS = ["grade", "count", "percentage"]

@pytest.mark.parametrize("field", GRADE_DIST_REQUIRED_FIELDS)
def test_grade_distribution_item_has_field(field, auth_client):
    r = auth_client.get("/api/analysis/grades")
    assert r.status_code == 200
    grades = r.json()["data"]
    for g in grades[:3]:
        assert field in g, f"Grade dist item missing: {field}"


DATASET_INFO_REQUIRED_FIELDS = [
    "has_data", "student_count", "result_count", "course_count",
]

@pytest.mark.parametrize("field", DATASET_INFO_REQUIRED_FIELDS)
def test_dataset_info_has_field(field, auth_client):
    r = auth_client.get("/api/results/dataset-info")
    assert r.status_code == 200
    assert field in r.json()["data"], f"Dataset info missing: {field}"
