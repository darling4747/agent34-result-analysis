"""A34 Additional parametrized tests to reach 1300."""
import pytest

# ── All analytics GET endpoints respond correctly ─────────────────────────────

ALL_GET_ENDPOINTS = [
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

@pytest.mark.parametrize("ep", ALL_GET_ENDPOINTS)
def test_ep_content_type_json(ep, auth_client):
    r = auth_client.get(ep)
    ct = r.headers.get("content-type", "")
    assert "application/json" in ct, f"{ep}: {ct}"

@pytest.mark.parametrize("ep", ALL_GET_ENDPOINTS)
def test_ep_no_traceback_in_body(ep, auth_client):
    r = auth_client.get(ep)
    body = r.text
    assert "Traceback (most recent call last)" not in body, f"{ep} leaks traceback"

@pytest.mark.parametrize("ep", ALL_GET_ENDPOINTS)
def test_ep_not_500(ep, auth_client):
    r = auth_client.get(ep)
    assert r.status_code != 500, f"{ep} returned 500: {r.text[:200]}"

@pytest.mark.parametrize("ep", ALL_GET_ENDPOINTS)
def test_ep_body_parseable(ep, auth_client):
    r = auth_client.get(ep)
    body = r.json()  # must not raise
    assert body is not None


# ── Query param combinations ───────────────────────────────────────────────────

ANALYTICS_SUBSET = [
    "/api/analysis/summary",
    "/api/analysis/grades",
    "/api/analysis/courses",
]

SINGLE_PARAMS = [
    ("academic_year", "2025-26"),
    ("academic_year", "2024-25"),
    ("semester", "6"),
    ("semester", "5"),
    ("semester", "1"),
    ("department", "CSE"),
    ("department", "ECE"),
    ("programme", "B.Tech"),
]

@pytest.mark.parametrize("ep,param_key,param_val", [
    (ep, k, v) for ep in ANALYTICS_SUBSET for k, v in SINGLE_PARAMS
])
def test_single_filter_param(ep, param_key, param_val, auth_client):
    r = auth_client.get(ep, params={param_key: param_val})
    assert r.status_code == 200, f"{ep}?{param_key}={param_val} -> {r.status_code}"


# ── Role permissions detailed ─────────────────────────────────────────────────

from app.security.permissions import ROLE_PERMISSIONS, P, VALID_ROLES

ROLE_HAS_PERMISSION = [
    ("PLATFORM_ADMIN", P.USER_CREATE),
    ("PLATFORM_ADMIN", P.USER_READ),
    ("PLATFORM_ADMIN", P.USER_UPDATE),
    ("PLATFORM_ADMIN", P.USER_DISABLE),
    ("PLATFORM_ADMIN", P.ROLE_ASSIGN),
    ("PLATFORM_ADMIN", P.PASSWORD_RESET),
    ("PLATFORM_ADMIN", P.RESULT_UPLOAD),
    ("PLATFORM_ADMIN", P.RESULT_READ),
    ("PLATFORM_ADMIN", P.RESULT_EXPORT),
    ("PLATFORM_ADMIN", P.ANALYSIS_READ),
    ("PLATFORM_ADMIN", P.ANALYSIS_INSTITUTION),
    ("PLATFORM_ADMIN", P.ANALYSIS_DEPARTMENT),
    ("PLATFORM_ADMIN", P.ANALYSIS_COURSE),
    ("PLATFORM_ADMIN", P.ANALYSIS_SECTION),
    ("PLATFORM_ADMIN", P.ANALYSIS_FACULTY),
    ("PLATFORM_ADMIN", P.MERIT_READ),
    ("PLATFORM_ADMIN", P.CORRELATION_READ),
    ("PLATFORM_ADMIN", P.HISTORICAL_READ),
    ("PLATFORM_ADMIN", P.INTERVENTION_READ),
    ("PLATFORM_ADMIN", P.REPORT_GENERATE),
    ("PLATFORM_ADMIN", P.REPORT_READ),
    ("PLATFORM_ADMIN", P.AUDIT_READ),
    ("PLATFORM_ADMIN", P.CONFIG_MANAGE),
    ("HOD", P.RESULT_READ),
    ("HOD", P.ANALYSIS_READ),
    ("HOD", P.ANALYSIS_DEPARTMENT),
    ("HOD", P.ANALYSIS_COURSE),
    ("HOD", P.ANALYSIS_SECTION),
    ("HOD", P.MERIT_READ),
    ("HOD", P.CORRELATION_READ),
    ("HOD", P.HISTORICAL_READ),
    ("HOD", P.INTERVENTION_READ),
    ("HOD", P.REPORT_GENERATE),
    ("IQAC", P.ANALYSIS_DEMOGRAPHIC),
    ("IQAC", P.ANALYSIS_INSTITUTION),
    ("IQAC", P.MERIT_READ),
    ("IQAC", P.RESULT_READ),
    ("AUDITOR", P.AUDIT_READ),
    ("AUDITOR", P.RESULT_READ),
    ("AUDITOR", P.REPORT_READ),
]

@pytest.mark.parametrize("role,perm", ROLE_HAS_PERMISSION)
def test_role_has_perm(role, perm):
    perms = set(ROLE_PERMISSIONS.get(role, []))
    assert perm in perms, f"{role} should have {perm}"


ROLE_LACKS_PERMISSION = [
    ("DEAN", P.USER_CREATE),
    ("DEAN", P.USER_DISABLE),
    ("DEAN", P.RESULT_UPLOAD),
    ("DEAN", P.CONFIG_MANAGE),
    ("HOD", P.USER_CREATE),
    ("HOD", P.ROLE_ASSIGN),
    ("HOD", P.CONFIG_MANAGE),
    ("HOD", P.ANALYSIS_INSTITUTION),
    ("FACULTY", P.USER_CREATE),
    ("FACULTY", P.ROLE_ASSIGN),
    ("FACULTY", P.RESULT_UPLOAD),
    ("FACULTY", P.ANALYSIS_INSTITUTION),
    ("FACULTY", P.AUDIT_READ),
    ("FACULTY", P.CONFIG_MANAGE),
    ("IQAC", P.USER_CREATE),
    ("IQAC", P.RESULT_UPLOAD),
    ("IQAC", P.CONFIG_MANAGE),
    ("MANAGEMENT", P.USER_CREATE),
    ("MANAGEMENT", P.USER_DISABLE),
    ("MANAGEMENT", P.RESULT_UPLOAD),
    ("MANAGEMENT", P.CONFIG_MANAGE),
    ("MANAGEMENT", P.AUDIT_READ),
    ("AUDITOR", P.USER_CREATE),
    ("AUDITOR", P.USER_DISABLE),
    ("AUDITOR", P.RESULT_UPLOAD),
    ("AUDITOR", P.REPORT_GENERATE),
    ("AUDITOR", P.CONFIG_MANAGE),
]

@pytest.mark.parametrize("role,perm", ROLE_LACKS_PERMISSION)
def test_role_lacks_perm(role, perm):
    perms = set(ROLE_PERMISSIONS.get(role, []))
    assert perm not in perms, f"{role} should NOT have {perm}"


# ── Seven valid roles defined ─────────────────────────────────────────────────

EXPECTED_ROLES = ["PLATFORM_ADMIN", "DEAN", "HOD", "FACULTY", "IQAC", "MANAGEMENT", "AUDITOR"]

@pytest.mark.parametrize("role", EXPECTED_ROLES)
def test_role_exists_in_valid_roles(role):
    assert role in VALID_ROLES


@pytest.mark.parametrize("role", EXPECTED_ROLES)
def test_role_has_permissions_defined(role):
    perms = ROLE_PERMISSIONS.get(role, [])
    assert len(perms) > 0, f"Role {role} has no permissions defined"


# ── Helpers module ─────────────────────────────────────────────────────────────

class TestHelpersModule:
    def test_normalise_column_name_strips(self):
        from app.utils.helpers import normalise_column_name
        assert normalise_column_name("  Roll Number  ") == "roll_number"

    def test_normalise_column_name_lowercases(self):
        from app.utils.helpers import normalise_column_name
        assert normalise_column_name("ROLL_NUMBER") == "roll_number"

    def test_normalise_column_name_replaces_spaces(self):
        from app.utils.helpers import normalise_column_name
        assert normalise_column_name("Roll Number") == "roll_number"

    def test_safe_float_valid(self):
        from app.utils.helpers import safe_float
        assert safe_float("72.5") == 72.5

    def test_safe_float_invalid_returns_default(self):
        from app.utils.helpers import safe_float
        assert safe_float("abc") is None

    def test_safe_float_none_returns_default(self):
        from app.utils.helpers import safe_float
        assert safe_float(None) is None

    def test_safe_int_valid(self):
        from app.utils.helpers import safe_int
        assert safe_int("6") == 6

    def test_safe_int_invalid_returns_default(self):
        from app.utils.helpers import safe_int
        assert safe_int("xyz") is None

    def test_format_academic_period(self):
        from app.utils.helpers import format_academic_period
        result = format_academic_period(6, "2025-26")
        assert "6" in result or "Semester" in result

    def test_nan_safe_dict_removes_nan(self):
        from app.utils.helpers import nan_safe_dict
        import math
        d = {"value": float("nan"), "normal": 42.0}
        result = nan_safe_dict(d)
        assert result["value"] is None
        assert result["normal"] == 42.0

    def test_nan_safe_dict_removes_inf(self):
        from app.utils.helpers import nan_safe_dict
        d = {"value": float("inf")}
        result = nan_safe_dict(d)
        assert result["value"] is None
