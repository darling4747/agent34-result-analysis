"""PDF report generator using ReportLab."""
from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..config import Settings
from ..utils.helpers import format_academic_period


class ReportGenerator:
    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(
        self,
        metrics: dict,
        run_id: int,
        academic_year: str,
        semester: int,
        department: str = "All Departments",
        institution_name: str = "Vignan University",
    ) -> str:
        """Generate a multi-section PDF and return the file path."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"report_{run_id}_{timestamp}.pdf"
        os.makedirs(self.settings.REPORT_DIR, exist_ok=True)
        filepath = os.path.join(self.settings.REPORT_DIR, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            title=f"Result Analysis Report — {format_academic_period(semester, academic_year)}",
        )

        styles = getSampleStyleSheet()
        h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceAfter=6)
        h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceAfter=4)
        normal = styles["Normal"]
        small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8)
        center = ParagraphStyle("Center", parent=styles["Normal"], alignment=TA_CENTER)
        draft_style = ParagraphStyle("Draft", parent=styles["Normal"], fontSize=20, textColor=colors.lightgrey, alignment=TA_CENTER)

        story = []

        # ---- Cover Page ----
        story.append(Spacer(1, 2 * cm))
        story.append(Paragraph("DRAFT — PENDING HUMAN REVIEW", draft_style))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(f"<b>{institution_name}</b>", ParagraphStyle("InstName", parent=styles["Normal"], fontSize=18, alignment=TA_CENTER)))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("<b>Agent 34 — Result Analysis Report</b>", ParagraphStyle("Title", parent=styles["Title"], alignment=TA_CENTER)))
        story.append(Spacer(1, 0.3 * cm))
        period_str = format_academic_period(semester, academic_year)
        story.append(Paragraph(f"Period: {period_str}", center))
        story.append(Paragraph(f"Department: {department}", center))
        story.append(Spacer(1, 0.3 * cm))
        gen_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        story.append(Paragraph(f"Generated: {gen_ts}", center))
        story.append(Paragraph(f"Analysis Run ID: {run_id}", center))
        story.append(Paragraph(f"Metric Version: 1.0", center))
        story.append(PageBreak())

        # ---- 1. Executive Summary ----
        story.append(Paragraph("1. Executive Summary", h1))
        story.append(HRFlowable(width="100%"))
        summary = metrics.get("summary", {})
        kpis = [
            ["KPI", "Value"],
            ["Total Students", str(summary.get("total_students", "N/A"))],
            ["Total Results", str(summary.get("total_results", "N/A"))],
            ["Pass Count", str(summary.get("pass_count", "N/A"))],
            ["Fail Count", str(summary.get("fail_count", "N/A"))],
            ["Absent Count", str(summary.get("absent_count", "N/A"))],
            ["Pass Percentage", _fmt_pct(summary.get("pass_percentage"))],
            ["Failure Percentage", _fmt_pct(summary.get("failure_percentage"))],
            ["Average Marks", _fmt_float(summary.get("average_marks"))],
            ["Median Marks", _fmt_float(summary.get("median_marks"))],
            ["Average GPA", _fmt_float(summary.get("average_gpa"))],
            ["Previous Pass %", _fmt_pct(summary.get("previous_pass_percentage"))],
        ]
        story.append(_make_table(kpis))
        story.append(Spacer(1, 0.5 * cm))

        # ---- 2. Reconciliation ----
        story.append(Paragraph("2. Student / Result Reconciliation", h1))
        story.append(HRFlowable(width="100%"))
        recon = metrics.get("reconciliation", {})
        recon_data = [
            ["Metric", "Value"],
            ["Total Expected", str(recon.get("total_expected", "N/A"))],
            ["Total Uploaded", str(recon.get("total_uploaded", "N/A"))],
            ["Matched", str(recon.get("matched", "N/A"))],
            ["Unmatched", str(recon.get("unmatched", "N/A"))],
            ["Reconciliation Score", _fmt_pct(recon.get("reconciliation_score"))],
        ]
        story.append(_make_table(recon_data))
        story.append(Spacer(1, 0.5 * cm))

        # ---- 3. Grade Distribution ----
        story.append(Paragraph("3. Grade Distribution", h1))
        story.append(HRFlowable(width="100%"))
        grade_dist = metrics.get("grade_distribution", [])
        if grade_dist:
            gd_data = [["Grade", "Count", "Percentage", "Cumulative %", "Grade Point"]]
            for g in grade_dist:
                gd_data.append([
                    g.get("grade", ""),
                    str(g.get("count", 0)),
                    _fmt_pct(g.get("percentage")),
                    _fmt_pct(g.get("cumulative_percentage")),
                    str(g.get("grade_point", "")),
                ])
            story.append(_make_table(gd_data))
        else:
            story.append(Paragraph("No grade data available.", normal))
        story.append(Spacer(1, 0.5 * cm))

        # ---- 4. Course-wise Analysis ----
        story.append(Paragraph("4. Course-wise Analysis", h1))
        story.append(HRFlowable(width="100%"))
        courses = metrics.get("courses", [])
        if courses:
            cd_data = [["Course", "Students", "Pass%", "Fail%", "Avg Marks", "Avg GPA", "Priority"]]
            for c in courses:
                cd_data.append([
                    f"{c.get('course_code','')} — {c.get('course_name','')}",
                    str(c.get("total_students", 0)),
                    _fmt_pct(c.get("pass_percentage")),
                    _fmt_pct(c.get("failure_percentage")),
                    _fmt_float(c.get("average_marks")),
                    _fmt_float(c.get("average_gpa")),
                    c.get("priority_level", ""),
                ])
            story.append(_make_table(cd_data))
        else:
            story.append(Paragraph("No course data available.", normal))
        story.append(Spacer(1, 0.5 * cm))

        # ---- 5. Section Comparison ----
        story.append(Paragraph("5. Section Comparison", h1))
        story.append(HRFlowable(width="100%"))
        sections = metrics.get("sections", [])
        if sections:
            sec_data = [["Section", "Students", "Pass%", "Fail%", "Avg Marks", "Deviation"]]
            for s in sections:
                sec_data.append([
                    s.get("section", ""),
                    str(s.get("student_count", 0)),
                    _fmt_pct(s.get("pass_rate")),
                    _fmt_pct(s.get("failure_rate")),
                    _fmt_float(s.get("avg_marks")),
                    _fmt_float(s.get("section_deviation")),
                ])
            story.append(_make_table(sec_data))
        else:
            story.append(Paragraph("No section data available.", normal))
        story.append(Spacer(1, 0.5 * cm))
        story.append(PageBreak())

        # ---- 6. Faculty Contextual Analysis ----
        story.append(Paragraph("6. Faculty Contextual Analysis", h1))
        story.append(HRFlowable(width="100%"))
        story.append(Paragraph(
            "Note: Faculty data is provided for contextual review only. "
            "No individual ranking or evaluation is implied.",
            ParagraphStyle("Note", parent=styles["Normal"], fontSize=9, textColor=colors.grey),
        ))
        faculty_list = metrics.get("faculty", [])
        if faculty_list:
            fac_data = [["Faculty", "Courses", "Students", "Pass%", "Baseline%", "Deviation"]]
            for f in faculty_list:
                fac_data.append([
                    f.get("faculty_name", ""),
                    str(f.get("courses_handled", 0)),
                    str(f.get("total_students", 0)),
                    _fmt_pct(f.get("pass_rate")),
                    _fmt_pct(f.get("historical_baseline")),
                    _fmt_float(f.get("deviation")),
                ])
            story.append(_make_table(fac_data))
        else:
            story.append(Paragraph("No faculty data available.", normal))
        story.append(Spacer(1, 0.5 * cm))

        # ---- 7. Merit List (Top 10) ----
        story.append(Paragraph("7. Merit List — Top 10", h1))
        story.append(HRFlowable(width="100%"))
        merit = metrics.get("merit", [])[:10]
        if merit:
            m_data = [["Rank", "Roll No.", "Name", "Programme", "Section", "SGPA", "Status"]]
            for m in merit:
                m_data.append([
                    str(m.get("rank", "")),
                    m.get("roll_number", ""),
                    m.get("student_name", ""),
                    m.get("programme", ""),
                    m.get("section", ""),
                    str(m.get("sgpa", "")),
                    m.get("status", ""),
                ])
            story.append(_make_table(m_data))
        else:
            story.append(Paragraph("No merit data available.", normal))
        story.append(Spacer(1, 0.5 * cm))

        # ---- 8. Internal vs External Correlation ----
        story.append(Paragraph("8. Internal vs External Correlation", h1))
        story.append(HRFlowable(width="100%"))
        corr_list = metrics.get("correlation", [])
        if corr_list:
            c_data = [["Course", "Int. Avg", "Ext. Avg", "Pearson r", "n", "Interpretation", "Flags"]]
            for c in corr_list:
                c_data.append([
                    c.get("course_code", ""),
                    _fmt_float(c.get("internal_average")),
                    _fmt_float(c.get("external_average")),
                    _fmt_float(c.get("pearson_correlation")),
                    str(c.get("sample_size", "")),
                    c.get("interpretation", ""),
                    ", ".join(c.get("flags", [])),
                ])
            story.append(_make_table(c_data))
        else:
            story.append(Paragraph("No correlation data available.", normal))
        story.append(Spacer(1, 0.5 * cm))

        # ---- 9. Historical Comparison ----
        story.append(Paragraph("9. Historical Comparison", h1))
        story.append(HRFlowable(width="100%"))
        hist_list = metrics.get("historical", [])
        if hist_list:
            h_data = [["Course", "Current Pass%", "Previous Pass%", "Hist. Avg%", "Deviation", "Trend"]]
            for h in hist_list:
                h_data.append([
                    h.get("course_code", ""),
                    _fmt_pct(h.get("current_pass_rate")),
                    _fmt_pct(h.get("previous_pass_rate")),
                    _fmt_pct(h.get("historical_average")),
                    _fmt_float(h.get("deviation_from_average")),
                    h.get("trend", ""),
                ])
            story.append(_make_table(h_data))
        else:
            story.append(Paragraph("No historical data available.", normal))
        story.append(Spacer(1, 0.5 * cm))
        story.append(PageBreak())

        # ---- 10. Intervention Priorities ----
        story.append(Paragraph("10. Intervention Priorities", h1))
        story.append(HRFlowable(width="100%"))
        int_list = metrics.get("interventions", [])
        if int_list:
            i_data = [["Course", "Failure%", "Priority", "Score", "Suggested Action"]]
            for i in int_list:
                i_data.append([
                    i.get("course_code", ""),
                    _fmt_pct(i.get("failure_rate")),
                    i.get("priority_level", ""),
                    str(i.get("priority_score", "")),
                    Paragraph(i.get("suggested_action", ""), small),
                ])
            story.append(_make_table(i_data))
        else:
            story.append(Paragraph("No intervention data available.", normal))
        story.append(Spacer(1, 0.5 * cm))

        # ---- 11. Key Observations (Narrative) ----
        story.append(Paragraph("11. Key Observations", h1))
        story.append(HRFlowable(width="100%"))
        narrative = metrics.get("narrative", {})
        if narrative.get("summary"):
            story.append(Paragraph(narrative["summary"], normal))
            story.append(Spacer(1, 0.3 * cm))
        if narrative.get("key_findings"):
            story.append(Paragraph("<b>Key Findings:</b>", normal))
            for finding in narrative["key_findings"]:
                story.append(Paragraph(f"• {finding}", normal))
        if narrative.get("recommendations"):
            story.append(Spacer(1, 0.2 * cm))
            story.append(Paragraph("<b>Recommendations:</b>", normal))
            for rec in narrative["recommendations"]:
                story.append(Paragraph(f"• {rec}", normal))
        if narrative.get("disclaimer"):
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph(
                f"<i>Disclaimer: {narrative['disclaimer']}</i>",
                ParagraphStyle("Disc", parent=styles["Normal"], fontSize=8, textColor=colors.grey),
            ))
        story.append(Spacer(1, 0.5 * cm))

        # ---- 12. Data Quality Notes ----
        story.append(Paragraph("12. Data Quality Notes", h1))
        story.append(HRFlowable(width="100%"))
        dq = metrics.get("data_quality", {})
        dq_data = [
            ["Metric", "Value"],
            ["Overall Score", _fmt_pct(dq.get("overall_score"))],
            ["Total Records", str(dq.get("total_records", "N/A"))],
            ["Complete Records", str(dq.get("complete_records", "N/A"))],
            ["Missing Fields", str(dq.get("missing_fields_count", "N/A"))],
            ["Duplicate Records", str(dq.get("duplicate_records", "N/A"))],
            ["Grade/Total Mismatches", str(dq.get("grade_total_mismatches", "N/A"))],
        ]
        story.append(_make_table(dq_data))
        story.append(Spacer(1, 0.5 * cm))

        # ---- 13. Human Review / Approval ----
        story.append(Paragraph("13. Human Review & Approval", h1))
        story.append(HRFlowable(width="100%"))
        story.append(Paragraph(
            "This report is marked as DRAFT. It must be reviewed and approved by a qualified academic officer "
            "before being used for official purposes.",
            normal,
        ))
        story.append(Spacer(1, 1.5 * cm))
        story.append(Paragraph("Reviewed by: _______________________________", normal))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Designation: ______________________________", normal))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Date: _____________________________________", normal))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Signature: ________________________________", normal))

        doc.build(story)
        return filepath


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_float(val, decimals: int = 2) -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val):.{decimals}f}"
    except (TypeError, ValueError):
        return str(val)


def _fmt_pct(val) -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val):.2f}%"
    except (TypeError, ValueError):
        return str(val)


def _make_table(data: list[list]) -> Table:
    col_count = max(len(row) for row in data)
    col_width = (A4[0] - 4 * cm) / col_count
    tbl = Table(data, colWidths=[col_width] * col_count, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tbl
