"""Tests for ValidationEngine."""
import pandas as pd

from app.config import get_settings
from app.services.validation import ValidationEngine


def _engine():
    return ValidationEngine(get_settings())


def _base_df(**overrides):
    data = {
        "roll_number": ["22CS001"],
        "student_name": ["Alice"],
        "programme": ["B.Tech"],
        "department": ["CSE"],
        "batch": ["2022"],
        "section": ["A"],
        "course_code": ["CS601"],
        "course_name": ["Compiler Design"],
        "faculty": ["Dr. Kumar"],
        "semester": [6],
        "academic_year": ["2025-26"],
        "internal_marks": [22.0],
        "external_marks": [50.0],
        "total_marks": [72.0],
        "grade": ["A"],
        "grade_point": [8.0],
        "result_status": ["PASS"],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_required_columns_present():
    df = _base_df()
    result = _engine().validate_dataframe(df)
    assert result.is_valid
    assert len(result.errors) == 0


def test_missing_required_column():
    df = _base_df()
    df = df.drop(columns=["roll_number"])
    result = _engine().validate_dataframe(df)
    assert not result.is_valid
    codes = [e.error_code for e in result.errors]
    assert "MISSING_COLUMN" in codes


def test_invalid_marks_negative():
    df = _base_df(internal_marks=[-5.0])
    result = _engine().validate_dataframe(df)
    assert not result.is_valid
    codes = [e.error_code for e in result.errors]
    assert "MARKS_BELOW_MINIMUM" in codes


def test_marks_exceed_maximum():
    df = _base_df(internal_marks=[35.0])  # max is 30
    result = _engine().validate_dataframe(df)
    assert not result.is_valid
    codes = [e.error_code for e in result.errors]
    assert "MARKS_EXCEED_MAXIMUM" in codes


def test_total_mismatch():
    df = _base_df(internal_marks=[22.0], external_marks=[50.0], total_marks=[80.0])
    result = _engine().validate_dataframe(df)
    assert not result.is_valid
    codes = [e.error_code for e in result.errors]
    assert "TOTAL_MARKS_MISMATCH" in codes


def test_invalid_grade():
    df = _base_df(grade=["X"])
    result = _engine().validate_dataframe(df)
    assert not result.is_valid
    codes = [e.error_code for e in result.errors]
    assert "INVALID_GRADE" in codes


def test_invalid_result_status():
    df = _base_df(result_status=["MAYBE"])
    result = _engine().validate_dataframe(df)
    assert not result.is_valid
    codes = [e.error_code for e in result.errors]
    assert "INVALID_RESULT_STATUS" in codes


def test_duplicate_detection():
    """Two rows with the same roll_number + course_code trigger a WARNING."""
    df = _base_df()
    df = pd.concat([df, df], ignore_index=True)
    result = _engine().validate_dataframe(df)
    warn_codes = [w.error_code for w in result.warnings]
    assert "DUPLICATE_RECORD" in warn_codes
