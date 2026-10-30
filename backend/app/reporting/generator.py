"""
Report generation engine.
Supports PDF (via ReportLab), CSV, and Excel (via openpyxl).
Implements strict spreadsheet formula injection mitigation (CWE-1236).
"""
from __future__ import annotations

import csv
import io
import os
from datetime import datetime, timezone
from typing import Any

import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors


def sanitize_spreadsheet_cell(val: Any) -> Any:
    """
    Mitigate spreadsheet formula injection (CSV/Excel Formula Injection / CSV Injection).
    If a string starts with `=`, `+`, `-`, `@`, `\t`, or `\r`, prepend a single quote `'`.
    """
    if isinstance(val, str) and val:
        first_char = val[0]
        if first_char in ("=", "+", "-", "@", "\t", "\r"):
            return f"'{val}"
    return val


def generate_csv_report(title: str, headers: list[str], rows: list[list[Any]]) -> io.BytesIO:
    """Generate formula-injection safe CSV stream."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Header
    writer.writerow([sanitize_spreadsheet_cell(h) for h in headers])

    # Rows
    for row in rows:
        writer.writerow([sanitize_spreadsheet_cell(cell) for cell in row])

    buf = io.BytesIO()
    buf.write(output.getvalue().encode("utf-8"))
    buf.seek(0)
    return buf


def generate_excel_report(title: str, headers: list[str], rows: list[list[Any]]) -> io.BytesIO:
    """Generate formula-injection safe Excel workbook."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title[:31]

    # Write headers
    for col_num, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = str(sanitize_spreadsheet_cell(h))
        cell.font = openpyxl.styles.Font(bold=True)

    # Write rows
    for row_num, row in enumerate(rows, 2):
        for col_num, val in enumerate(row, 1):
            ws.cell(row=row_num, column=col_num, value=sanitize_spreadsheet_cell(val))

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def generate_pdf_report(
    title: str,
    headers: list[str],
    rows: list[list[Any]],
    generated_by: str,
    methodology: str = "Standard statistical evaluation and laboratory records analysis.",
) -> io.BytesIO:
    """Generate compliant laboratory PDF report with header, metadata, disclaimers, and data table."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph(f"<b>LabInsight AI — {title}</b>", styles["Title"]))
    elements.append(Spacer(1, 10))

    # Meta
    gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    meta_text = (
        f"<b>Generated At:</b> {gen_time} | <b>Operator:</b> {generated_by}<br/>"
        f"<b>Methodology:</b> {methodology}<br/>"
        "<b>Clinical Disclaimer:</b> This document contains laboratory administrative data and statistical metrics. "
        "It is NOT a medical diagnosis or therapeutic recommendation."
    )
    elements.append(Paragraph(meta_text, styles["Normal"]))
    elements.append(Spacer(1, 16))

    # Table data
    table_data = [[h for h in headers]]
    for row in rows[:150]:  # Cap at 150 records per PDF report
        table_data.append([str(c) if c is not None else "-" for c in row])

    t = Table(table_data)
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ])
    )
    elements.append(t)
    doc.build(elements)

    buf.seek(0)
    return buf
