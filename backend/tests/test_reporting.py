"""
Unit tests for Report Generation and CSV Formula Injection mitigation (CWE-1236).
"""
import pytest

from app.reporting.generator import (
    generate_csv_report,
    generate_excel_report,
    generate_pdf_report,
    sanitize_spreadsheet_cell,
)


def test_formula_injection_mitigation():
    """Verify malicious spreadsheet formula triggers (=, +, -, @, \t, \r) are properly neutralized."""
    malicious_inputs = [
        "=SUM(A1:A10)",
        "+cmd|' /C calc'!A0",
        "-2+3*cmd",
        "@SUM(B1:B2)",
        "\tmalicious",
        "\rmalicious",
    ]

    for val in malicious_inputs:
        sanitized = sanitize_spreadsheet_cell(val)
        assert sanitized.startswith("'"), f"Failed to prepend quote to: {val}"

    # Benign string should remain untouched
    assert sanitize_spreadsheet_cell("Normal Value") == "Normal Value"
    assert sanitize_spreadsheet_cell(123.45) == 123.45


def test_csv_report_generation():
    """Verify CSV report generator returns valid utf-8 byte buffer with sanitized content."""
    headers = ["Patient Code", "Formula Test"]
    rows = [["PAT-001", "=1+1"]]
    buf = generate_csv_report("Test Report", headers, rows)
    content = buf.getvalue().decode("utf-8")

    assert "Patient Code" in content
    assert "'=1+1" in content


def test_excel_report_generation():
    """Verify Excel report generator returns valid xlsx byte buffer."""
    headers = ["Test Name", "Value"]
    rows = [["Hemoglobin", 14.5]]
    buf = generate_excel_report("Excel Test", headers, rows)
    assert len(buf.getvalue()) > 0


def test_pdf_report_generation():
    """Verify PDF report generator builds compliant PDF stream."""
    headers = ["Test Code", "Measurement"]
    rows = [["HB", "14.2 g/dL"]]
    buf = generate_pdf_report("Clinical Summary", headers, rows, "Dr. Tester")
    assert buf.getvalue().startswith(b"%PDF")
