"""Validation engine for uploaded result files."""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List

import pandas as pd

from ..config import Settings
from ..utils.constants import (
    REQUIRED_COLUMNS,
    RESULT_STATUSES,
    VALID_GRADES,
)


@dataclass
class ValidationError:
    row_number: int
    column_name: str
    error_code: str
    message: str
    raw_value: str
    severity: str = "ERROR"  # ERROR | WARNING


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    valid_rows: int = 0
    rejected_rows: int = 0
    total_rows: int = 0


class ValidationEngine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._tolerance = 0.5  # marks tolerance for total check

    def validate_dataframe(self, df: pd.DataFrame) -> ValidationResult:
        """Run all validations.  Never raises — returns structured errors."""
        all_errors: List[ValidationError] = []
        all_warnings: List[ValidationError] = []

        # 1. Column checks first — if columns missing, some row checks cannot run
        col_errors = self._check_required_columns(df)
        all_errors.extend(col_errors)

        if col_errors:
            # Return early — row-level checks need the columns to be present
            return ValidationResult(
                is_valid=False,
                errors=all_errors,
                warnings=all_warnings,
                valid_rows=0,
                rejected_rows=len(df),
                total_rows=len(df),
            )

        # 2. Row-level checks
        all_errors.extend(self._validate_required_fields(df))
        all_errors.extend(self._validate_numeric_marks(df))
        all_errors.extend(self._validate_totals(df))
        all_errors.extend(self._validate_grades(df))
        all_errors.extend(self._validate_result_status(df))
        all_warnings.extend(self._validate_duplicates(df))

        # Compute row-level rejected set
        error_rows = {e.row_number for e in all_errors}
        rejected = len(error_rows)
        valid = len(df) - rejected
        is_valid = len(all_errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=all_warnings,
            valid_rows=max(valid, 0),
            rejected_rows=rejected,
            total_rows=len(df),
        )

    # ------------------------------------------------------------------
    # Column checks
    # ------------------------------------------------------------------
    def _check_required_columns(self, df: pd.DataFrame) -> List[ValidationError]:
        errors: List[ValidationError] = []
        actual_cols = set(df.columns.tolist())
        for col in REQUIRED_COLUMNS:
            if col not in actual_cols:
                errors.append(ValidationError(
                    row_number=-1,
                    column_name=col,
                    error_code="MISSING_COLUMN",
                    message=f"Required column '{col}' is missing from the file.",
                    raw_value="",
                    severity="ERROR",
                ))
        return errors

    # ------------------------------------------------------------------
    # Required field checks (non-null)
    # ------------------------------------------------------------------
    def _validate_required_fields(self, df: pd.DataFrame) -> List[ValidationError]:
        errors: List[ValidationError] = []
        mandatory = ["roll_number", "student_name", "course_code", "semester", "academic_year"]
        for col in mandatory:
            if col not in df.columns:
                continue
            for idx, val in enumerate(df[col]):
                row = idx + 2  # header is row 1
                if val is None or (isinstance(val, float) and math.isnan(val)) or str(val).strip() == "":
                    errors.append(ValidationError(
                        row_number=row,
                        column_name=col,
                        error_code="MISSING_REQUIRED_FIELD",
                        message=f"'{col}' is required but empty at row {row}.",
                        raw_value=str(val),
                        severity="ERROR",
                    ))
        return errors

    # ------------------------------------------------------------------
    # Numeric marks checks
    # ------------------------------------------------------------------
    def _validate_numeric_marks(self, df: pd.DataFrame) -> List[ValidationError]:
        errors: List[ValidationError] = []
        mark_cols = {
            "internal_marks": (0.0, self.settings.INTERNAL_MAX),
            "external_marks": (0.0, self.settings.EXTERNAL_MAX),
            "total_marks": (0.0, self.settings.TOTAL_MAX),
        }
        for col, (lo, hi) in mark_cols.items():
            if col not in df.columns:
                continue
            for idx, val in enumerate(df[col]):
                row = idx + 2
                if val is None or (isinstance(val, float) and math.isnan(val)):
                    continue  # handled by required-field validator if mandatory
                try:
                    fval = float(val)
                except (ValueError, TypeError):
                    errors.append(ValidationError(
                        row_number=row,
                        column_name=col,
                        error_code="NON_NUMERIC_MARKS",
                        message=f"'{col}' value '{val}' is not a number at row {row}.",
                        raw_value=str(val),
                        severity="ERROR",
                    ))
                    continue
                if fval < lo:
                    errors.append(ValidationError(
                        row_number=row,
                        column_name=col,
                        error_code="MARKS_BELOW_MINIMUM",
                        message=f"'{col}' value {fval} is below minimum {lo} at row {row}.",
                        raw_value=str(val),
                        severity="ERROR",
                    ))
                elif fval > hi:
                    errors.append(ValidationError(
                        row_number=row,
                        column_name=col,
                        error_code="MARKS_EXCEED_MAXIMUM",
                        message=f"'{col}' value {fval} exceeds maximum {hi} at row {row}.",
                        raw_value=str(val),
                        severity="ERROR",
                    ))
        return errors

    # ------------------------------------------------------------------
    # Total = internal + external check
    # ------------------------------------------------------------------
    def _validate_totals(self, df: pd.DataFrame) -> List[ValidationError]:
        errors: List[ValidationError] = []
        needed = {"internal_marks", "external_marks", "total_marks"}
        if not needed.issubset(set(df.columns)):
            return errors
        for idx, row_data in enumerate(df.itertuples(index=False)):
            row = idx + 2
            try:
                internal = float(getattr(row_data, "internal_marks"))
                external = float(getattr(row_data, "external_marks"))
                total = float(getattr(row_data, "total_marks"))
            except (ValueError, TypeError):
                continue
            if math.isnan(internal) or math.isnan(external) or math.isnan(total):
                continue
            expected = internal + external
            if abs(expected - total) > self._tolerance:
                errors.append(ValidationError(
                    row_number=row,
                    column_name="total_marks",
                    error_code="TOTAL_MARKS_MISMATCH",
                    message=(
                        f"total_marks {total} does not equal internal_marks {internal} "
                        f"+ external_marks {external} = {expected} at row {row}."
                    ),
                    raw_value=str(total),
                    severity="ERROR",
                ))
        return errors

    # ------------------------------------------------------------------
    # Grade validity
    # ------------------------------------------------------------------
    def _validate_grades(self, df: pd.DataFrame) -> List[ValidationError]:
        errors: List[ValidationError] = []
        if "grade" not in df.columns:
            return errors
        for idx, val in enumerate(df["grade"]):
            row = idx + 2
            if val is None or (isinstance(val, float) and math.isnan(val)):
                continue
            grade = str(val).strip().upper()
            if grade not in VALID_GRADES:
                errors.append(ValidationError(
                    row_number=row,
                    column_name="grade",
                    error_code="INVALID_GRADE",
                    message=f"Grade '{val}' is not a recognised grade at row {row}. Valid grades: {sorted(VALID_GRADES)}",
                    raw_value=str(val),
                    severity="ERROR",
                ))
        return errors

    # ------------------------------------------------------------------
    # Result status validity
    # ------------------------------------------------------------------
    def _validate_result_status(self, df: pd.DataFrame) -> List[ValidationError]:
        errors: List[ValidationError] = []
        if "result_status" not in df.columns:
            return errors
        for idx, val in enumerate(df["result_status"]):
            row = idx + 2
            if val is None or (isinstance(val, float) and math.isnan(val)):
                continue
            status = str(val).strip().upper()
            if status not in RESULT_STATUSES:
                errors.append(ValidationError(
                    row_number=row,
                    column_name="result_status",
                    error_code="INVALID_RESULT_STATUS",
                    message=f"Status '{val}' is not valid at row {row}. Valid: {sorted(RESULT_STATUSES)}",
                    raw_value=str(val),
                    severity="ERROR",
                ))
        return errors

    # ------------------------------------------------------------------
    # Duplicate detection (roll_number + course_code combo)
    # ------------------------------------------------------------------
    def _validate_duplicates(self, df: pd.DataFrame) -> List[ValidationError]:
        warnings: List[ValidationError] = []
        needed = {"roll_number", "course_code"}
        if not needed.issubset(set(df.columns)):
            return warnings
        seen: dict[tuple, int] = {}
        for idx, row_data in enumerate(df.itertuples(index=False)):
            row = idx + 2
            key = (
                str(getattr(row_data, "roll_number", "")).strip(),
                str(getattr(row_data, "course_code", "")).strip(),
            )
            if key in seen:
                warnings.append(ValidationError(
                    row_number=row,
                    column_name="roll_number",
                    error_code="DUPLICATE_RECORD",
                    message=(
                        f"Duplicate entry for roll_number '{key[0]}' + course_code '{key[1]}' "
                        f"at row {row} (first seen at row {seen[key]})."
                    ),
                    raw_value=key[0],
                    severity="WARNING",
                ))
            else:
                seen[key] = row
        return warnings
