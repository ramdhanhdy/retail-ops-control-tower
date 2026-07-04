"""Severity matrix and severity assignment."""

from __future__ import annotations

from retail_ops_control_tower.constants import ExceptionType, Severity

CRITICAL_TYPES = {
    ExceptionType.LATE_SETUP,
    ExceptionType.STOCKOUT_RISK,
    ExceptionType.UNRESOLVED_ISSUE_AGING,
}
WATCH_TYPES = {
    ExceptionType.MISSING_CONFIRMATION,
    ExceptionType.QUANTITY_MISMATCH,
    ExceptionType.MISSING_PHOTO_PROOF,
    ExceptionType.OVERSTOCK_RISK,
    ExceptionType.LOW_SELL_THROUGH,
}


def assign_severity(
    exception_type: ExceptionType, value: float = 0.0, threshold: float = 1.0
) -> Severity:
    """Assign severity from exception type and breach magnitude."""
    if exception_type in CRITICAL_TYPES:
        return Severity.CRITICAL
    if threshold and value >= threshold * 1.5:
        return Severity.CRITICAL
    if exception_type in WATCH_TYPES or (threshold and value >= threshold):
        return Severity.WATCH
    return Severity.INFO
