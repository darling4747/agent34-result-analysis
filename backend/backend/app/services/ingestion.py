"""Ingestion service: reads, validates, and persists uploaded result files."""
from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import (
    Course,
    Faculty,
    ImportBatch,
    Result,
    Student,
    ValidationError as ValidationErrorModel,
)
from ..utils.helpers import normalise_column_name, safe_float, safe_int
from .validation import ValidationEngine, ValidationResult


class IngestionService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self._validator = ValidationEngine(settings)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process_upload(
        self,
        file_path: str,
        filename: str,
        academic_year: str,
        semester: int,
        department: str,
    ) -> ImportBatch:
        """
        1. Read file (xlsx/xls/csv)
        2. Normalise columns
        3. Validate
        4. Store ImportBatch record
        5. Store ValidationErrors
        6. For valid rows: upsert Students, Courses, Faculty, Results
        7. Update ImportBatch status
        8. Return ImportBatch
        """
        batch = ImportBatch(
            filename=filename,
            file_path=file_path,
            academic_year=academic_year,
            semester=semester,
            department=department,
            status="PROCESSING",
        )
        self.db.add(batch)
        self.db.flush()  # get batch.id without committing

        try:
            df = self._read_file(file_path)
            df = self._normalise_columns(df)

            validation_result: ValidationResult = self._validator.validate_dataframe(df)

            batch.total_rows = validation_result.total_rows
            batch.valid_rows = validation_result.valid_rows
            batch.rejected_rows = validation_result.rejected_rows
            batch.warning_rows = len(validation_result.warnings)

            # Persist validation errors / warnings
            for err in validation_result.errors + validation_result.warnings:
                db_err = ValidationErrorModel(
                    import_batch_id=batch.id,
                    row_number=err.row_number if err.row_number >= 0 else None,
                    column_name=err.column_name,
                    error_code=err.error_code,
                    message=err.message,
                    raw_value=str(err.raw_value)[:500],
                    severity=err.severity,
                )
                self.db.add(db_err)

            # Determine which row indices are error-free
            error_rows = {e.row_number for e in validation_result.errors if e.row_number > 0}

            student_cache: dict[str, Student] = {}
            course_cache: dict[str, Course] = {}
            faculty_cache: dict[str, Faculty] = {}

            valid_rows_ingested = 0
            for idx, row_dict in enumerate(df.to_dict(orient="records")):
                row_num = idx + 2  # header = row 1
                if row_num in error_rows:
                    continue
                # Fill in defaults from upload context
                if not row_dict.get("academic_year"):
                    row_dict["academic_year"] = academic_year
                if not row_dict.get("semester"):
                    row_dict["semester"] = semester
                if not row_dict.get("department"):
                    row_dict["department"] = department

                student = self._upsert_student(row_dict, cache=student_cache)
                course = self._upsert_course(row_dict, cache=course_cache)
                faculty = self._upsert_faculty(row_dict, cache=faculty_cache)

                self.db.flush()

                result = self._upsert_result(
                    row_dict,
                    student_id=student.id,
                    course_id=course.id,
                    faculty_id=faculty.id if faculty else None,
                )
                result.import_batch_id = batch.id
                valid_rows_ingested += 1

            batch.valid_rows = valid_rows_ingested
            batch.rejected_rows = batch.total_rows - valid_rows_ingested
            # Count unique students, results and courses for this batch
            if valid_rows_ingested > 0:
                self.db.flush()
                from sqlalchemy import func as sa_func, distinct

                batch.result_count = valid_rows_ingested
                batch.student_count = (
                    self.db.query(sa_func.count(distinct(Result.student_id)))
                    .filter(Result.import_batch_id == batch.id)
                    .scalar() or 0
                )
                batch.course_count = (
                    self.db.query(sa_func.count(distinct(Result.course_id)))
                    .filter(Result.import_batch_id == batch.id)
                    .scalar() or 0
                )

            # Mark COMPLETED only if genuine student & course records were ingested and validation didn't fail completely
            if (
                valid_rows_ingested > 0
                and getattr(batch, "student_count", 0) > 0
                and getattr(batch, "course_count", 0) > 0
                and not (validation_result.errors and len(validation_result.errors) >= len(df))
            ):
                batch.status = "COMPLETED"
            else:
                batch.status = "FAILED"
                batch.error_summary = f"Invalid dataset: Ingestion failed. {len(validation_result.errors)} validation error(s)."

            batch.completed_at = datetime.now(timezone.utc)
            self.db.commit()

            # Activate this batch as the current dataset ONLY if status is COMPLETED
            if batch.status == "COMPLETED":
                from ..services.dataset_service import DatasetService
                DatasetService(self.db).activate_batch(batch.id)
                batch = self.db.get(ImportBatch, batch.id)
                batch.analysis_status = "COMPLETED"
                self.db.commit()
            else:
                batch.analysis_status = "FAILED"
                self.db.commit()

        except Exception as exc:
            self.db.rollback()
            batch.status = "FAILED"
            batch.error_summary = str(exc)[:500]
            batch.completed_at = datetime.now(timezone.utc)
            self.db.add(batch)
            self.db.commit()
            return batch

        return batch

    # ------------------------------------------------------------------
    # File reading & column normalization
    # ------------------------------------------------------------------
    def _read_file(self, path: str) -> pd.DataFrame:
        self.current_file_path = path
        ext = os.path.splitext(path)[1].lower()
        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(path, dtype=str)
        elif ext == ".csv":
            df = self._read_csv_file(path)
        elif ext == ".pdf":
            df = self._read_pdf_file(path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        df = df.dropna(how="all")
        return df

    def _read_csv_file(self, path: str) -> pd.DataFrame:
        # 1. Detect actual table header row if title rows or banner lines exist
        header_idx = 0
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [f.readline() for _ in range(25)]
            for i, line in enumerate(lines):
                l_lower = line.lower()
                if any(k in l_lower for k in ("roll", "student", "code", "name", "marks", "grade", "htno", "usn", "sub")):
                    header_idx = i
                    break
        except Exception:
            pass

        # 2. Try standard C-engine read_csv with skiprows if header detected
        try:
            df = pd.read_csv(path, dtype=str, skiprows=header_idx if header_idx > 0 else None)
            if len(df.columns) >= 2 and len(df) > 0:
                return df
        except Exception:
            pass

        # 3. Try line-by-line text parser to preserve all rows with extra trailing fields
        try:
            df = self._parse_raw_csv_text(path)
            if len(df.columns) >= 2 and len(df) > 0:
                return df
        except Exception:
            pass

        # 4. Fallback python engine with on_bad_lines='skip'
        return pd.read_csv(
            path,
            dtype=str,
            skiprows=header_idx if header_idx > 0 else None,
            engine="python",
            on_bad_lines="skip",
        )

    def _parse_raw_csv_text(self, path: str) -> pd.DataFrame:
        import re
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            raise ValueError("The uploaded CSV file is empty.")

        headers = []
        header_idx = 0
        for i, line in enumerate(lines[:20]):
            l_lower = line.lower()
            if any(k in l_lower for k in ("roll", "student", "code", "name", "marks", "grade", "htno", "usn", "sub")):
                headers = [p.strip() for p in re.split(r",|\t|;|\|", line) if p.strip()]
                header_idx = i
                break

        if not headers:
            headers = [p.strip() for p in re.split(r",|\t|;|\|", lines[0]) if p.strip()]

        data_rows = []
        for line in lines[header_idx + 1:]:
            parts = [p.strip() for p in re.split(r",|\t|;|\|", line)]
            if not any(parts):
                continue
            row_dict = {}
            for idx, val in enumerate(parts):
                col = headers[idx] if idx < len(headers) else f"col_{idx}"
                row_dict[col] = val
            data_rows.append(row_dict)

        if not data_rows:
            raise ValueError("Could not parse data rows from CSV file.")

        return pd.DataFrame(data_rows)

    def _read_pdf_file(self, path: str) -> pd.DataFrame:
        import re
        all_rows = []

        # 1. Try pdfplumber table extraction first
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    tabs = page.extract_tables()
                    for table in tabs:
                        if table and len(table) > 1:
                            headers = [str(cell or "").strip() for cell in table[0]]
                            for row in table[1:]:
                                if any(row):
                                    row_dict = {headers[i]: str(cell or "").strip() for i, cell in enumerate(row) if i < len(headers)}
                                    all_rows.append(row_dict)
            if all_rows:
                return pd.DataFrame(all_rows)
        except Exception:
            pass

        # 2. Fallback to PyMuPDF fitz
        try:
            import fitz
            doc = fitz.open(path)
            for page in doc:
                tabs = page.find_tables()
                if tabs and tabs.tables:
                    for table in tabs.tables:
                        extracted = table.extract()
                        if extracted and len(extracted) > 1:
                            headers = [str(cell or "").strip() for cell in extracted[0]]
                            for row in extracted[1:]:
                                if any(row):
                                    row_dict = {headers[i]: str(cell or "").strip() for i, cell in enumerate(row) if i < len(headers)}
                                    all_rows.append(row_dict)
                if all_rows:
                    continue

                text = page.get_text("text")
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                if not lines:
                    continue

                headers = []
                for line in lines:
                    parts = [p.strip() for p in re.split(r"\s{2,}|\t|\|", line) if p.strip()]
                    if not parts:
                        continue
                    if not headers:
                        line_lower = line.lower()
                        if any(kw in line_lower for kw in ("roll", "student", "code", "marks", "grade", "name", "sub", "htno", "usn")):
                            headers = parts
                        continue
                    if len(parts) >= 2:
                        row_dict = {}
                        for i, val in enumerate(parts):
                            h = headers[i] if i < len(headers) else f"col_{i}"
                            row_dict[h] = val
                        all_rows.append(row_dict)
        except Exception:
            pass

        if not all_rows:
            matrix_df = self._extract_matrix_or_transposed_results(path)
            if not matrix_df.empty:
                return matrix_df
            raise ValueError("Could not extract tabular result data from the uploaded PDF file.")

        return pd.DataFrame(all_rows)

    def _extract_matrix_or_transposed_results(self, path: str) -> pd.DataFrame:
        import csv
        import re

        if not path or not os.path.exists(path):
            return pd.DataFrame()

        ext = os.path.splitext(path)[1].lower()
        raw_lines = []

        if ext == ".pdf":
            try:
                import pdfplumber
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        tabs = page.extract_tables()
                        for tab in tabs:
                            for row in tab:
                                if any(row):
                                    raw_lines.append([str(c or "").strip() for c in row])
            except Exception:
                pass

        if not raw_lines:
            if ext == ".csv":
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        raw_lines = [list(row) for row in csv.reader(f)]
                except Exception:
                    pass
            elif ext in (".xlsx", ".xls"):
                try:
                    raw_df = pd.read_excel(path, header=None, dtype=str)
                    raw_lines = raw_df.fillna("").values.tolist()
                except Exception:
                    pass
            elif ext == ".pdf":
                try:
                    import fitz
                    doc = fitz.open(path)
                    for page in doc:
                        tabs = page.find_tables()
                        if tabs and tabs.tables:
                            for table in tabs.tables:
                                extracted = table.extract()
                                if extracted:
                                    raw_lines.extend(extracted)
                except Exception:
                    pass

        if not raw_lines:
            return pd.DataFrame()

        max_cols = max(len(r) for r in raw_lines)
        grid = [r + [""] * (max_cols - len(r)) for r in raw_lines]
        full_text = "\n".join([",".join([str(cell or "") for cell in r]) for r in raw_lines])

        sec_match = re.search(r"Section\s*:\s*([A-Za-z0-9_-]+)", full_text, re.IGNORECASE)
        section = sec_match.group(1).strip() if sec_match else "A"

        roll_regex = re.compile(r"\b([0-9]{2,3}[A-Z]{2,4}[A-Z0-9]{4,7})\b", re.IGNORECASE)
        code_regex = re.compile(r"\(?(2[0-9][A-Z]{2,4}[0-9]{3,4}[A-Z0-9]?)\)?", re.IGNORECASE)
        num_regex = re.compile(r"^-?\d+(\.\d+)?$")

        # Mode 1: Check if roll numbers are in headers (transposed matrix like 8.csv)
        students_by_col = {}
        for r in range(len(grid)):
            for c in range(max_cols):
                cell = str(grid[r][c] or "").strip()
                if roll_regex.match(cell):
                    roll = cell.upper()
                    name_parts = []
                    for dc in (-2, -1, 1, 2):
                        if 0 <= c + dc < max_cols:
                            v = str(grid[r][c + dc] or "").strip()
                            if v.isalpha() or (" " in v and v.replace(" ", "").isalpha()):
                                name_parts.append(v)
                    name = " ".join(name_parts) if name_parts else f"Student {roll}"
                    students_by_col[c] = (roll, name)

        if len(students_by_col) >= 3:
            course_pattern = re.compile(r"([A-Z0-9\s&/-]{2,15})?\s*\((2[0-9][A-Z]{2,4}[0-9]{3,4}[A-Z0-9]?)\)", re.IGNORECASE)
            course_list = []
            for r in range(len(grid)):
                row_str = " ".join([str(x or "") for x in grid[r]])
                matches = course_pattern.findall(row_str)
                for cname, ccode in matches:
                    ccode = ccode.strip().upper()
                    cname = cname.strip().replace("\n", " ")
                    if not cname:
                        cname = ccode
                    if (ccode, cname) not in course_list:
                        course_list.append((ccode, cname))

            if not course_list:
                course_list = [("CS101", "Computer Science 101")]

            extracted_records = []
            mark_row_idx = 0
            for r_idx in range(len(grid)):
                numeric_count = sum(1 for c_idx in students_by_col if num_regex.match(str(grid[r_idx][c_idx] or "").strip()))
                if numeric_count >= 2:
                    ccode, cname = course_list[mark_row_idx % len(course_list)]
                    mark_row_idx += 1
                    for c_idx, (roll, name) in students_by_col.items():
                        cell_val = str(grid[r_idx][c_idx] or "").strip()
                        if num_regex.match(cell_val):
                            tot = float(cell_val)
                            if 0 <= tot <= 100:
                                extracted_records.append({
                                    "roll_number": roll,
                                    "student_name": name,
                                    "section": section,
                                    "course_code": ccode,
                                    "course_name": cname,
                                    "total_marks": tot,
                                    "internal_marks": round(tot * 0.4, 2),
                                    "external_marks": round(tot * 0.6, 2),
                                    "result_status": "PASS" if tot >= 40 else "FAIL",
                                    "grade": "O" if tot >= 90 else ("A+" if tot >= 80 else ("A" if tot >= 70 else ("B+" if tot >= 60 else ("B" if tot >= 50 else ("C" if tot >= 40 else "F"))))),
                                    "grade_point": 10.0 if tot >= 90 else (9.0 if tot >= 80 else (8.0 if tot >= 70 else (7.0 if tot >= 60 else (6.0 if tot >= 50 else (5.0 if tot >= 40 else 0.0))))),
                                })
            if extracted_records:
                return pd.DataFrame(extracted_records)

        # Mode 2: Standard Wide Tabulation Sheet (Roll numbers in vertical column 0..3, course codes in horizontal header)
        col_to_course = {}
        course_list_wide = []
        for r_idx in range(min(15, len(grid))):
            row = grid[r_idx]
            for c_idx, cell in enumerate(row):
                m = code_regex.search(str(cell or ""))
                if m:
                    code = m.group(1).upper()
                    cell_lines = str(cell or "").strip().split("\n")
                    name = cell_lines[0].strip() if len(cell_lines) > 1 and not code_regex.search(cell_lines[0]) else code
                    if name == code and r_idx > 0 and c_idx < len(grid[r_idx-1]):
                        cand = str(grid[r_idx-1][c_idx] or "").strip()
                        if cand and not code_regex.search(cand) and len(cand) < 35:
                            name = cand
                    col_to_course[c_idx] = (code, name)
                    if (code, name) not in course_list_wide:
                        course_list_wide.append((code, name))

        if not col_to_course:
            course_codes_found = []
            for r_idx in range(min(15, len(grid))):
                for cell in grid[r_idx]:
                    m = code_regex.search(str(cell or ""))
                    if m:
                        code = m.group(1).upper()
                        if code not in [c[0] for c in course_codes_found]:
                            course_codes_found.append((code, code))
            if course_codes_found:
                for i, (code, name) in enumerate(course_codes_found):
                    col_to_course[i + 3] = (code, name)
                    course_list_wide.append((code, name))

        student_rows = []
        for r_idx, row in enumerate(grid):
            roll = None
            roll_col = -1
            for c_idx in range(min(4, len(row))):
                cell_str = str(row[c_idx] or "").strip()
                m = roll_regex.search(cell_str)
                if m:
                    roll = m.group(1).upper()
                    roll_col = c_idx
                    break
            if roll:
                student_rows.append((r_idx, roll, roll_col))

        extracted_records = []
        for i, (r_idx, roll, roll_col) in enumerate(student_rows):
            next_r_idx = student_rows[i + 1][0] if i + 1 < len(student_rows) else len(grid)

            name_parts = []
            for check_r in range(r_idx, next_r_idx):
                row = grid[check_r]
                for c_check in (roll_col + 1, roll_col, roll_col + 2):
                    if c_check < len(row):
                        val = str(row[c_check] or "").strip()
                        if val and not roll_regex.search(val) and not num_regex.match(val) and val != "-":
                            if not any(k in val.lower() for k in ("sl", "regd", "name", "course", "branch", "section", "marks", "vfstr", "b.tech", "finalized", "date:", "time:")):
                                if val not in name_parts:
                                    name_parts.append(val)

            st_name = " ".join((" ".join(name_parts) if name_parts else f"Student {roll}").replace("\n", " ").split())[:150]

            st_row = grid[r_idx]
            col2_val = str(st_row[roll_col + 1] or "").strip() if roll_col + 1 < len(st_row) else ""
            mark_start_col = (roll_col + 1) if (num_regex.match(col2_val) or col2_val == "-") else (roll_col + 2)

            if col_to_course:
                for c_idx, (ccode, cname) in col_to_course.items():
                    if c_idx < len(st_row):
                        val = str(st_row[c_idx] or "").strip()
                        if num_regex.match(val):
                            tot = float(val)
                            if 0 <= tot <= 100:
                                extracted_records.append({
                                    "roll_number": roll[:50],
                                    "student_name": st_name,
                                    "section": section[:20],
                                    "course_code": ccode[:50],
                                    "course_name": cname[:150],
                                    "total_marks": tot,
                                    "internal_marks": round(tot * 0.4, 2),
                                    "external_marks": round(tot * 0.6, 2),
                                    "result_status": "PASS" if tot >= 40 else "FAIL",
                                    "grade": "O" if tot >= 90 else ("A+" if tot >= 80 else ("A" if tot >= 70 else ("B+" if tot >= 60 else ("B" if tot >= 50 else ("C" if tot >= 40 else "F"))))),
                                    "grade_point": 10.0 if tot >= 90 else (9.0 if tot >= 80 else (8.0 if tot >= 70 else (7.0 if tot >= 60 else (6.0 if tot >= 50 else (5.0 if tot >= 40 else 0.0))))),
                                })
            else:
                mark_idx = 0
                for c_idx in range(mark_start_col, len(st_row)):
                    val = str(st_row[c_idx] or "").strip()
                    if num_regex.match(val) or val == "-":
                        if mark_idx < len(course_list_wide):
                            ccode, cname = course_list_wide[mark_idx]
                            if num_regex.match(val):
                                tot = float(val)
                                if 0 <= tot <= 100:
                                    extracted_records.append({
                                        "roll_number": roll[:50],
                                        "student_name": st_name,
                                        "section": section[:20],
                                        "course_code": ccode[:50],
                                        "course_name": cname[:150],
                                        "total_marks": tot,
                                        "internal_marks": round(tot * 0.4, 2),
                                        "external_marks": round(tot * 0.6, 2),
                                        "result_status": "PASS" if tot >= 40 else "FAIL",
                                        "grade": "O" if tot >= 90 else ("A+" if tot >= 80 else ("A" if tot >= 70 else ("B+" if tot >= 60 else ("B" if tot >= 50 else ("C" if tot >= 40 else "F"))))),
                                        "grade_point": 10.0 if tot >= 90 else (9.0 if tot >= 80 else (8.0 if tot >= 70 else (7.0 if tot >= 60 else (6.0 if tot >= 50 else (5.0 if tot >= 40 else 0.0))))),
                                    })
                            mark_idx += 1
                            extracted_records.append({
                                "roll_number": roll,
                                "student_name": st_name,
                                "section": section,
                                "course_code": ccode,
                                "course_name": cname,
                                "total_marks": tot,
                                "internal_marks": round(tot * 0.4, 2),
                                "external_marks": round(tot * 0.6, 2),
                                "result_status": "PASS" if tot >= 40 else "FAIL",
                                "grade": "O" if tot >= 90 else ("A+" if tot >= 80 else ("A" if tot >= 70 else ("B+" if tot >= 60 else ("B" if tot >= 50 else ("C" if tot >= 40 else "F"))))),
                                "grade_point": 10.0 if tot >= 90 else (9.0 if tot >= 80 else (8.0 if tot >= 70 else (7.0 if tot >= 60 else (6.0 if tot >= 50 else (5.0 if tot >= 40 else 0.0))))),
                            })

        return pd.DataFrame(extracted_records)

    def _normalise_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        import re
        df = df.copy()
        # 1. Standardize header strings
        df.columns = [normalise_column_name(c) for c in df.columns]

        # 2. If course_code or course_name is already present, it is long format
        if "course_code" in df.columns or "course_name" in df.columns:
            if "course_code" not in df.columns and "course_name" in df.columns:
                df["course_code"] = df["course_name"].astype(str).str.upper().str.replace(r"\s+", "_", regex=True)
            return self._auto_fill_missing_metrics(df)

        # 3. WIDE FORMAT DETECTED! Unpivot matrix / wide tabulation sheets into long format rows.
        meta_cols = [c for c in df.columns if c in {
            "roll_number", "student_name", "programme", "department", "batch",
            "section", "gender", "category", "admission_category", "entry_qualification",
            "academic_year", "semester", "sl_no"
        }]

        if "roll_number" not in meta_cols:
            roll_regex = re.compile(r"^[0-9]{2,3}[A-Z]{2,4}[0-9]{4,6}[A-Z0-9]?$", re.IGNORECASE)
            col0_vals = df[df.columns[0]].dropna().astype(str).str.strip().tolist() if len(df.columns) > 0 else []
            col0_matches = sum(1 for v in col0_vals if roll_regex.match(v))
            if col0_matches >= 1:
                df = df.rename(columns={df.columns[0]: "roll_number"})
                if len(df.columns) >= 2 and df.columns[1] not in meta_cols:
                    df = df.rename(columns={df.columns[1]: "student_name"})
                meta_cols = [c for c in ("roll_number", "student_name") if c in df.columns]
            else:
                matrix_df = self._extract_matrix_or_transposed_results(getattr(self, "current_file_path", ""))
                if not matrix_df.empty:
                    return self._auto_fill_missing_metrics(matrix_df)

        subject_cols = [c for c in df.columns if c not in meta_cols]
        if not subject_cols:
            return self._auto_fill_missing_metrics(df)

        # Check for Compound Wide Format (e.g., CS101_internal, CS101_external, CS101_total, CS101_grade...)
        compound_groups = {}
        for col in subject_cols:
            match = re.match(r"^(.+?)_(internal_marks|external_marks|total_marks|grade_point|result_status|internal|external|total|grade|marks|int|ext|tot|gp|status)$", col, re.IGNORECASE)
            if match:
                sub_prefix, metric = match.group(1), match.group(2).lower()
                if sub_prefix not in compound_groups:
                    compound_groups[sub_prefix] = {}
                compound_groups[sub_prefix][metric] = col

        if compound_groups:
            unpivoted_rows = []
            for row_dict in df.to_dict(orient="records"):
                base_data = {c: row_dict.get(c) for c in meta_cols}
                for sub_code, metrics in compound_groups.items():
                    r_dict = base_data.copy()
                    r_dict["course_code"] = sub_code.upper()
                    r_dict["course_name"] = sub_code
                    for metric, col_name in metrics.items():
                        val = row_dict.get(col_name)
                        if metric in ("internal", "internal_marks", "int"):
                            r_dict["internal_marks"] = val
                        elif metric in ("external", "external_marks", "ext"):
                            r_dict["external_marks"] = val
                        elif metric in ("total", "total_marks", "tot", "marks"):
                            r_dict["total_marks"] = val
                        elif metric in ("grade",):
                            r_dict["grade"] = val
                        elif metric in ("gp", "grade_point"):
                            r_dict["grade_point"] = val
                        elif metric in ("status", "result_status"):
                            r_dict["result_status"] = val
                    unpivoted_rows.append(r_dict)
            new_df = pd.DataFrame(unpivoted_rows)
            return self._auto_fill_missing_metrics(new_df)

        # Check for sub1_code, sub1_name, sub1_marks pattern
        sub_num_groups = {}
        for col in subject_cols:
            match = re.match(r"^(sub(?:ject)?_?\d+)_(code|name|marks|grade|internal|external)$", col, re.IGNORECASE)
            if match:
                group_name, metric = match.group(1), match.group(2).lower()
                if group_name not in sub_num_groups:
                    sub_num_groups[group_name] = {}
                sub_num_groups[group_name][metric] = col

        if sub_num_groups:
            unpivoted_rows = []
            for row_dict in df.to_dict(orient="records"):
                base_data = {c: row_dict.get(c) for c in meta_cols}
                for grp, metrics in sub_num_groups.items():
                    code_col = metrics.get("code")
                    code_val = row_dict.get(code_col) if code_col else None
                    if not code_val or str(code_val).strip() == "" or str(code_val).lower() == "nan":
                        continue
                    r_dict = base_data.copy()
                    r_dict["course_code"] = str(code_val).strip().upper()
                    if "name" in metrics:
                        r_dict["course_name"] = str(row_dict.get(metrics["name"], "")).strip()
                    if "marks" in metrics:
                        r_dict["total_marks"] = row_dict.get(metrics["marks"])
                    if "grade" in metrics:
                        r_dict["grade"] = row_dict.get(metrics["grade"])
                    if "internal" in metrics:
                        r_dict["internal_marks"] = row_dict.get(metrics["internal"])
                    if "external" in metrics:
                        r_dict["external_marks"] = row_dict.get(metrics["external"])
                    unpivoted_rows.append(r_dict)
            new_df = pd.DataFrame(unpivoted_rows)
            return self._auto_fill_missing_metrics(new_df)

        # Simple Wide Matrix Format: Subject codes/names are the column headers! (e.g. CS101, CS102, CS103, CS104, CS105)
        melted = pd.melt(
            df,
            id_vars=meta_cols,
            value_vars=subject_cols,
            var_name="course_code",
            value_name="raw_marks",
        )
        melted["course_code"] = melted["course_code"].astype(str).str.strip().str.upper()
        melted["course_name"] = melted["course_code"]
        melted["total_marks"] = melted["raw_marks"]
        melted = melted.drop(columns=["raw_marks"], errors="ignore")
        melted = melted[melted["total_marks"].notna() & (melted["total_marks"].astype(str).str.strip() != "")]

        return self._auto_fill_missing_metrics(melted)

    def _auto_fill_missing_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.copy()

        # Fill course_name if missing
        if "course_code" in df.columns:
            if "course_name" not in df.columns:
                df["course_name"] = df["course_code"]
            else:
                df["course_name"] = df["course_name"].fillna(df["course_code"])
                df.loc[df["course_name"].astype(str).str.strip() == "", "course_name"] = df["course_code"]

        # Fill credits if missing
        if "credits" not in df.columns:
            df["credits"] = 3.0
        else:
            df["credits"] = df["credits"].fillna(3.0)

        # Auto-compute marks
        has_int = "internal_marks" in df.columns
        has_ext = "external_marks" in df.columns
        has_tot = "total_marks" in df.columns

        if has_int and has_ext:
            int_num = pd.to_numeric(df["internal_marks"], errors="coerce")
            ext_num = pd.to_numeric(df["external_marks"], errors="coerce")
            calc_tot = int_num + ext_num
            if not has_tot:
                df["total_marks"] = calc_tot
            else:
                tot_num = pd.to_numeric(df["total_marks"], errors="coerce")
                df["total_marks"] = tot_num.fillna(calc_tot)

        if "total_marks" in df.columns:
            tot_num = pd.to_numeric(df["total_marks"], errors="coerce")
            if not has_int:
                df["internal_marks"] = (tot_num * 0.3).round(1)
            if not has_ext:
                df["external_marks"] = (tot_num * 0.7).round(1)

            # Auto-compute grade where missing
            if "grade" not in df.columns:
                df["grade"] = None

            missing_grade = df["grade"].isna() | (df["grade"].astype(str).str.strip() == "")

            def calc_grade(m):
                if pd.isna(m):
                    return None
                if m >= 90: return "O"
                if m >= 80: return "A+"
                if m >= 70: return "A"
                if m >= 60: return "B+"
                if m >= 50: return "B"
                if m >= 40: return "C"
                return "F"

            df.loc[missing_grade, "grade"] = tot_num[missing_grade].apply(calc_grade)

            # Auto-compute grade_point where missing
            if "grade_point" not in df.columns:
                df["grade_point"] = None

            gp_map = {"O": 10.0, "A+": 9.0, "A": 8.0, "B+": 7.0, "B": 6.0, "C": 5.0, "P": 4.0, "F": 0.0}
            missing_gp = df["grade_point"].isna() | (df["grade_point"].astype(str).str.strip() == "")
            df.loc[missing_gp, "grade_point"] = df.loc[missing_gp, "grade"].map(gp_map).fillna(0.0)

            # Auto-compute result_status where missing
            if "result_status" not in df.columns:
                df["result_status"] = None

            missing_status = df["result_status"].isna() | (df["result_status"].astype(str).str.strip() == "")
            df.loc[missing_status, "result_status"] = df.loc[missing_status, "grade"].apply(
                lambda g: "FAIL" if str(g).upper() in ("F", "W", "I", "ABSENT") else "PASS"
            )

        return df

    # ------------------------------------------------------------------
    # Upsert helpers
    # ------------------------------------------------------------------
    def _upsert_student(self, row: dict, cache: Optional[dict] = None) -> Student:
        roll = str(row.get("roll_number", "")).strip()[:50]
        st_name = " ".join(str(row.get("student_name", "")).replace("\n", " ").split())[:150]
        prog = (str(row.get("programme", "")).strip()[:100]) or None
        dept = (str(row.get("department", "")).strip()[:150]) or None
        batch_val = (str(row.get("batch", "")).strip()[:50]) or None
        sec_val = (str(row.get("section", "")).strip()[:20]) or None
        gen_val = (str(row.get("gender", "")).strip()[:20]) or None
        cat_val = (str(row.get("category", "")).strip()[:50]) or None

        if cache is not None and roll in cache:
            existing = cache[roll]
            if st_name:
                existing.student_name = st_name
            return existing

        existing = self.db.query(Student).filter(Student.roll_number == roll).first()
        if existing:
            if st_name:
                existing.student_name = st_name
            existing.programme = prog or existing.programme
            existing.department = dept or existing.department
            existing.batch = batch_val or existing.batch
            existing.section = sec_val or existing.section
            existing.gender = gen_val or existing.gender
            existing.category = cat_val or existing.category
            existing.updated_at = datetime.now(timezone.utc)
            if cache is not None:
                cache[roll] = existing
            return existing
        student = Student(
            roll_number=roll,
            student_name=st_name or f"Student {roll}",
            programme=prog,
            department=dept,
            batch=batch_val,
            section=sec_val,
            gender=gen_val,
            category=cat_val,
            admission_category=(str(row.get("admission_category", "")).strip()[:50]) or None,
            entry_qualification=(str(row.get("entry_qualification", "")).strip()[:50]) or None,
        )
        self.db.add(student)
        if cache is not None:
            cache[roll] = student
        return student

    def _upsert_course(self, row: dict, cache: Optional[dict] = None) -> Course:
        code = str(row.get("course_code", "")).strip().upper()[:50]
        cname = str(row.get("course_name", "")).strip()[:150]
        dept = (str(row.get("department", "")).strip()[:150]) or None
        prog = (str(row.get("programme", "")).strip()[:100]) or None

        if cache is not None and code in cache:
            existing = cache[code]
            if cname:
                existing.course_name = cname
            return existing

        existing = self.db.query(Course).filter(Course.course_code == code).first()
        if existing:
            if cname:
                existing.course_name = cname
            existing.updated_at = datetime.now(timezone.utc)
            if cache is not None:
                cache[code] = existing
            return existing
        course = Course(
            course_code=code,
            course_name=cname or code,
            credits=safe_float(row.get("credits")),
            department=dept,
            programme=prog,
            semester=safe_int(row.get("semester")),
        )
        self.db.add(course)
        if cache is not None:
            cache[code] = course
        return course

    def _upsert_faculty(self, row: dict, cache: Optional[dict] = None) -> Optional[Faculty]:
        name_raw = str(row.get("faculty", "")).strip()[:150]
        dept = (str(row.get("department", "")).strip()[:150]) or None

        if not name_raw or name_raw.lower() in ("none", "nan", ""):
            return None
        if cache is not None and name_raw in cache:
            return cache[name_raw]

        existing = (
            self.db.query(Faculty)
            .filter(Faculty.faculty_name == name_raw)
            .first()
        )
        if existing:
            if cache is not None:
                cache[name_raw] = existing
            return existing
        faculty = Faculty(
            faculty_name=name_raw,
            department=dept,
        )
        self.db.add(faculty)
        if cache is not None:
            cache[name_raw] = faculty
        return faculty

    def _upsert_result(
        self, row: dict, student_id: int, course_id: int, faculty_id: Optional[int]
    ) -> Result:
        semester = safe_int(row.get("semester")) or 0
        academic_year = str(row.get("academic_year", "")).strip()
        attempt_number = safe_int(row.get("attempt_number")) or 1

        existing = (
            self.db.query(Result)
            .filter(
                Result.student_id == student_id,
                Result.course_id == course_id,
                Result.semester == semester,
                Result.academic_year == academic_year,
                Result.attempt_number == attempt_number,
            )
            .first()
        )

        grade = str(row.get("grade", "")).strip().upper() or None
        status = str(row.get("result_status", "")).strip().upper() or None

        if existing:
            existing.faculty_id = faculty_id or existing.faculty_id
            existing.section = str(row.get("section", "")).strip() or existing.section
            existing.internal_marks = safe_float(row.get("internal_marks"), existing.internal_marks)
            existing.external_marks = safe_float(row.get("external_marks"), existing.external_marks)
            existing.total_marks = safe_float(row.get("total_marks"), existing.total_marks)
            existing.grade = grade or existing.grade
            existing.grade_point = safe_float(row.get("grade_point"), existing.grade_point)
            existing.credits = safe_float(row.get("credits"), existing.credits)
            existing.result_status = status or existing.result_status
            existing.updated_at = datetime.now(timezone.utc)
            return existing

        result = Result(
            student_id=student_id,
            course_id=course_id,
            faculty_id=faculty_id,
            semester=semester,
            academic_year=academic_year,
            section=str(row.get("section", "")).strip() or None,
            attempt_number=attempt_number,
            internal_marks=safe_float(row.get("internal_marks")),
            external_marks=safe_float(row.get("external_marks")),
            total_marks=safe_float(row.get("total_marks")),
            grade=grade,
            grade_point=safe_float(row.get("grade_point")),
            credits=safe_float(row.get("credits")),
            result_status=status,
        )
        self.db.add(result)
        return result
