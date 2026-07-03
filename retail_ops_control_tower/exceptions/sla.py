"""SLA aging, buckets, status, pause logic, and auto-escalation."""

from __future__ import annotations

from datetime import date, timedelta

from retail_ops_control_tower.constants import AgingBucket


def compute_aging_bucket(age_days: int) -> AgingBucket:
    """Compute aging bucket (0-3) from age in days."""
    if age_days <= 5:
        return AgingBucket.FRESH
    elif age_days <= 15:
        return AgingBucket.AGING
    elif age_days <= 30:
        return AgingBucket.OVERDUE
    else:
        return AgingBucket.CHRONIC


def compute_sla_status(
    age_hours: float, sla_window_hours: int, is_paused: bool = False
) -> str:
    """Compute SLA status string."""
    if is_paused:
        return "paused"
    if age_hours > sla_window_hours:
        return "breached"
    if age_hours > sla_window_hours * 0.75:
        return "approaching"
    return "within"
