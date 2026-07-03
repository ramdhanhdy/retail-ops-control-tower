"""Issue dataclass (43 fields).

Table: issues - exception and corrective action records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Issue:
    """One row in the issues table.

    Enriched by the exception management system with priority scores, SLA
    status, and aging buckets.
    """

    # Core identification
    issue_id: str
    parent_id: str | None  # None for original, set for reopens
    reopen_count: int

    # Source linkage
    campaign_id: str
    store_id: str
    sku_id: str | None
    allocation_id: str | None
    dispatch_id: str | None
    confirmation_id: str | None

    # Classification
    exception_type: str  # one of 8 category names
    exception_rule_code: str  # EX-01 to EX-24
    root_cause_category: str
    root_cause_sub_category: str

    # Severity and priority
    severity: str  # critical, watch, info
    priority_score: int  # 1-200
    business_impact: str  # hero, flagship, standard, low-velocity

    # Lifecycle
    status: str  # raised, open, in_progress, resolved, closed, paused, escalated, waived
    raised_at: str  # ISO datetime
    last_updated_at: str
    resolved_at: str | None
    resolution_time_hours: float | None

    # SLA
    sla_deadline: str
    sla_status: str  # within, approaching, breached, paused
    aging_bucket: int  # 0-3
    age_days: int
    is_escalated: bool
    escalation_level: str

    # Ownership
    owner: str
    assignee: str

    # Action
    next_action: str
    next_action_due: str

    # Quantities (for context)
    planned_quantity: int | None
    shipped_quantity: int | None
    received_quantity: int | None
    sold_quantity: int | None

    # Variance details
    variance_amount: float
    variance_pct: float
    description: str

    # Metadata
    region: str
    tags: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
