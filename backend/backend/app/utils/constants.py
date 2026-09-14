"""Constants used across Agent 34."""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Column name expectations for uploaded files
# ---------------------------------------------------------------------------
REQUIRED_COLUMNS: list[str] = [
    "roll_number",
    "student_name",
]

OPTIONAL_COLUMNS: list[str] = [
    "programme",
    "department",
    "batch",
    "section",
    "faculty",
    "credits",
    "gender",
    "category",
    "admission_category",
    "entry_qualification",
    "attempt_number",
]

# ---------------------------------------------------------------------------
# Status values
# ---------------------------------------------------------------------------
RESULT_STATUSES: set[str] = {"PASS", "FAIL", "ABSENT", "WITHHELD", "DEBARRED"}

PRIORITY_LEVELS: set[str] = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

# ---------------------------------------------------------------------------
# Pearson r thresholds for interpretation
# ---------------------------------------------------------------------------
CORRELATION_THRESHOLDS: dict[str, float] = {
    "STRONG_POSITIVE": 0.70,
    "MODERATE_POSITIVE": 0.40,
    "WEAK_POSITIVE": 0.10,
    "WEAK_NEGATIVE": -0.10,
    "MODERATE_NEGATIVE": -0.40,
    "STRONG_NEGATIVE": -0.70,
}

MIN_SAMPLE_FOR_CORRELATION: int = 5

# ---------------------------------------------------------------------------
# Grade point buckets for GPA distribution
# ---------------------------------------------------------------------------
GPA_BUCKETS: list[dict] = [
    {"range": "0.0–4.0", "min": 0.0, "max": 4.0},
    {"range": "4.0–5.0", "min": 4.0, "max": 5.0},
    {"range": "5.0–6.0", "min": 5.0, "max": 6.0},
    {"range": "6.0–7.0", "min": 6.0, "max": 7.0},
    {"range": "7.0–8.0", "min": 7.0, "max": 8.0},
    {"range": "8.0–9.0", "min": 8.0, "max": 9.0},
    {"range": "9.0–10.0", "min": 9.0, "max": 10.01},
]

# ---------------------------------------------------------------------------
# Marks buckets (0–100 in steps of 10)
# ---------------------------------------------------------------------------
MARK_BUCKETS: list[dict] = [
    {"range": f"{i}–{i+10}", "min": i, "max": i + 10}
    for i in range(0, 100, 10)
]

# ---------------------------------------------------------------------------
# Valid grade labels
# ---------------------------------------------------------------------------
VALID_GRADES: set[str] = {"O", "A+", "A", "B+", "B", "C", "P", "F", "W", "I"}

# ---------------------------------------------------------------------------
# Historical trend thresholds
# ---------------------------------------------------------------------------
TREND_STABLE_THRESHOLD: float = 2.0   # percentage points
TREND_NOTABLE_THRESHOLD: float = 5.0  # percentage points

# ---------------------------------------------------------------------------
# Intervention thresholds
# ---------------------------------------------------------------------------
INTERVENTION_FAILURE_THRESHOLD: float = 20.0   # %  — below this = watch
INTERVENTION_CRITICAL_THRESHOLD: float = 40.0  # %  — above this = critical

# Internal–external gap threshold
IE_GAP_THRESHOLD: float = 20.0

# Faculty deviation threshold (percentage points) that triggers review flag
FACULTY_DEVIATION_THRESHOLD: float = 10.0
