"""Severity matrix and severity assignment."""

from __future__ import annotations

from retail_ops_control_tower.constants import ExceptionType, Severity


def assign_severity(
    exception_type: ExceptionType, value: float, threshold: float
) -> Severity:
    """Assign severity based on exception type and threshold breach. TODO: Phase 4."""
    if value < threshold * 0.80:
        return Severity.CRITICAL
    elif value < threshold:
        return Severity.WATCH
    return Severity.INFO
