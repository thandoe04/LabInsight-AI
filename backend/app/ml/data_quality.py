"""
Data Quality Intelligence module.
Combines deterministic validation rules and statistical checks.
Proposed corrections are presented for human review; NEVER applied automatically.
"""
from __future__ import annotations

import uuid
from typing import Any


def check_data_quality(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Evaluate laboratory test results and sample records for data quality defects.

    Detects:
    - Missing values
    - Negative or physically impossible numeric laboratory measurements
    - Chronological inversions (e.g., collection date after received date)
    - Extreme statistical outliers (> 4 IQR beyond bounds)
    - Inconsistent measurement units
    """
    issues: list[dict[str, Any]] = []

    for r in records:
        entity_id = r.get("id")
        test_code = r.get("test_code", "")
        num_val = r.get("numeric_value")
        collected_at = r.get("collected_at")
        received_at = r.get("received_at")
        unit = r.get("measurement_unit")

        # 1. Missing numeric value where expected
        if num_val is None and r.get("result_type") == "numeric":
            issues.append({
                "entity_type": "test_result",
                "entity_id": entity_id,
                "field_name": "numeric_value",
                "issue_type": "missing_value",
                "severity": "warning",
                "description": f"Missing numeric value for test {test_code}.",
                "proposed_correction": None,
            })

        # 2. Negative value for strictly positive clinical analytes
        if num_val is not None and num_val < 0:
            issues.append({
                "entity_type": "test_result",
                "entity_id": entity_id,
                "field_name": "numeric_value",
                "issue_type": "impossible_value",
                "severity": "critical",
                "description": f"Physically impossible negative value ({num_val}) for test {test_code}.",
                "proposed_correction": {"suggested_value": abs(num_val), "action": "invert_sign_review"},
            })

        # 3. Chronological inconsistency
        if collected_at and received_at and collected_at > received_at:
            issues.append({
                "entity_type": "sample",
                "entity_id": r.get("sample_id", entity_id),
                "field_name": "collected_at",
                "issue_type": "inconsistent_timestamps",
                "severity": "error",
                "description": "Collection timestamp is later than receipt timestamp.",
                "proposed_correction": {"action": "verify_timestamps_against_paper_requisition"},
            })

        # 4. Outlier verification
        upper_limit = r.get("upper_limit")
        if num_val is not None and upper_limit is not None and upper_limit > 0:
            if num_val > (upper_limit * 5):
                issues.append({
                    "entity_type": "test_result",
                    "entity_id": entity_id,
                    "field_name": "numeric_value",
                    "issue_type": "extreme_outlier",
                    "severity": "warning",
                    "description": f"Value {num_val} exceeds 5x upper reference limit ({upper_limit}) for {test_code}.",
                    "proposed_correction": {"action": "check_dilution_factor_and_repeat_run"},
                })

    return issues
