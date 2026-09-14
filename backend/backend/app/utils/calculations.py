"""Pure math helper functions — no DB, no pandas."""
from __future__ import annotations
import math
from .constants import CORRELATION_THRESHOLDS, MIN_SAMPLE_FOR_CORRELATION


def compute_pass_percentage(passed: int, eligible: int) -> float:
    """passed / eligible * 100.  Returns 0.0 if eligible == 0."""
    if eligible == 0:
        return 0.0
    return round((passed / eligible) * 100, 2)


def compute_weighted_gpa(grade_points: list[float], credits: list[float]) -> float:
    """SUM(gp * cr) / SUM(cr).  Falls back to simple mean if credits empty/zero."""
    if not grade_points:
        return 0.0
    if not credits or sum(credits) == 0:
        return round(sum(grade_points) / len(grade_points), 4)
    total_credit = sum(credits)
    weighted_sum = sum(gp * cr for gp, cr in zip(grade_points, credits))
    return round(weighted_sum / total_credit, 4)


def interpret_correlation(r: float, n: int, min_sample: int = MIN_SAMPLE_FOR_CORRELATION) -> str:
    """Return one of: STRONG_POSITIVE, MODERATE_POSITIVE, WEAK_POSITIVE,
    WEAK_NEGATIVE, MODERATE_NEGATIVE, STRONG_NEGATIVE, INSUFFICIENT_DATA."""
    if n < min_sample:
        return "INSUFFICIENT_DATA"
    if math.isnan(r):
        return "INSUFFICIENT_DATA"
    if r >= CORRELATION_THRESHOLDS["STRONG_POSITIVE"]:
        return "STRONG_POSITIVE"
    elif r >= CORRELATION_THRESHOLDS["MODERATE_POSITIVE"]:
        return "MODERATE_POSITIVE"
    elif r >= CORRELATION_THRESHOLDS["WEAK_POSITIVE"]:
        return "WEAK_POSITIVE"
    elif r <= CORRELATION_THRESHOLDS["STRONG_NEGATIVE"]:
        return "STRONG_NEGATIVE"
    elif r <= CORRELATION_THRESHOLDS["MODERATE_NEGATIVE"]:
        return "MODERATE_NEGATIVE"
    elif r <= CORRELATION_THRESHOLDS["WEAK_NEGATIVE"]:
        return "WEAK_NEGATIVE"
    else:
        return "WEAK_POSITIVE"


def compute_priority_score(
    failure_rate: float,
    historical_deviation: float | None,
    section_deviation: float | None,
    ie_anomaly_score: float | None,
    weights: dict[str, float],
) -> float:
    """Weighted composite score normalised 0–100."""
    # Normalise failure_rate from 0–100% range to 0–1
    failure_component = min(failure_rate / 100.0, 1.0)

    # Historical deviation: normalise — treat ±30 pp as full scale
    if historical_deviation is not None:
        hist_component = min(abs(historical_deviation) / 30.0, 1.0)
    else:
        hist_component = 0.0

    # Section deviation: normalise — treat ±20 pp as full scale
    if section_deviation is not None:
        section_component = min(abs(section_deviation) / 20.0, 1.0)
    else:
        section_component = 0.0

    # IE anomaly already 0–1
    ie_component = ie_anomaly_score if ie_anomaly_score is not None else 0.0

    w_fail = weights.get("failure", 0.40)
    w_hist = weights.get("historical", 0.30)
    w_sect = weights.get("section", 0.20)
    w_corr = weights.get("correlation", 0.10)

    score = (
        w_fail * failure_component
        + w_hist * hist_component
        + w_sect * section_component
        + w_corr * ie_component
    ) * 100

    return round(min(max(score, 0.0), 100.0), 2)


def grade_to_priority_level(score: float) -> str:
    """CRITICAL>=75, HIGH>=55, MEDIUM>=35, LOW otherwise."""
    if score >= 75:
        return "CRITICAL"
    elif score >= 55:
        return "HIGH"
    elif score >= 35:
        return "MEDIUM"
    else:
        return "LOW"


def safe_json_value(val) -> float | int | str | None:
    """Convert NaN/Inf to None for JSON safety."""
    if val is None:
        return None
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
    return val


def bucket_marks(marks_list: list[float], bucket_size: int = 10) -> list[dict]:
    """Return histogram buckets: [{range: '0-10', count: N}, ...]"""
    if not marks_list:
        return []
    max_val = 100
    buckets = []
    for start in range(0, max_val, bucket_size):
        end = start + bucket_size
        label = f"{start}-{end}"
        count = sum(1 for m in marks_list if start <= m < end)
        # include 100 in the last bucket
        if end == max_val:
            count = sum(1 for m in marks_list if start <= m <= end)
        buckets.append({"range": label, "count": count})
    return buckets
