"""Constants and enumerations.

Defines exception types, severity tiers, SLA windows, and exception states
used throughout the package. Exactly 8 exception types, 3 severity tiers, and
4 aging buckets per the PRD cross-document consistency rules.
"""

from __future__ import annotations

from enum import Enum


class ExceptionType(Enum):
    """8-category exception taxonomy (PRD Section 5)."""

    MISSING_CONFIRMATION = 1
    QUANTITY_MISMATCH = 2
    MISSING_PHOTO_PROOF = 3
    LATE_SETUP = 4
    STOCKOUT_RISK = 5
    OVERSTOCK_RISK = 6
    LOW_SELL_THROUGH = 7
    UNRESOLVED_ISSUE_AGING = 8


class Severity(Enum):
    """3-tier severity model (PRD Section 5)."""

    CRITICAL = "critical"
    WATCH = "watch"
    INFO = "info"


class IssueStatus(Enum):
    """Exception lifecycle states (PRD Section 5)."""

    RAISED = "raised"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    PAUSED = "paused"
    ESCALATED = "escalated"
    WAIVED = "waived"


class AgingBucket(Enum):
    """4 SLA aging buckets (PRD Section 5)."""

    FRESH = 0       # 0-5 days
    AGING = 1       # 6-15 days
    OVERDUE = 2     # 16-30 days
    CHRONIC = 3     # 30+ days


class ThresholdColor(Enum):
    """KPI threshold color coding."""

    GREEN = "green"
    AMBER = "amber"
    RED = "red"


# Exception type default owners (PRD Section 5)
EXCEPTION_TYPE_OWNERS = {
    ExceptionType.MISSING_CONFIRMATION: "Field Operations",
    ExceptionType.QUANTITY_MISMATCH: "DC Operations",
    ExceptionType.MISSING_PHOTO_PROOF: "Field Representative",
    ExceptionType.LATE_SETUP: "Store Manager",
    ExceptionType.STOCKOUT_RISK: "Replenishment Planner",
    ExceptionType.OVERSTOCK_RISK: "Merchant",
    ExceptionType.LOW_SELL_THROUGH: "Merchant + Planner",
    ExceptionType.UNRESOLVED_ISSUE_AGING: "Operations Lead",
}

# Exception type SLA windows in hours (PRD Section 5)
EXCEPTION_TYPE_SLA_HOURS = {
    ExceptionType.MISSING_CONFIRMATION: 48,
    ExceptionType.QUANTITY_MISMATCH: 48,
    ExceptionType.MISSING_PHOTO_PROOF: 48,
    ExceptionType.LATE_SETUP: 48,
    ExceptionType.STOCKOUT_RISK: 24,
    ExceptionType.OVERSTOCK_RISK: 168,   # 7 days
    ExceptionType.LOW_SELL_THROUGH: 168,  # 7 days
    ExceptionType.UNRESOLVED_ISSUE_AGING: 24,
}

# Severity weights for priority score formula
SEVERITY_WEIGHTS = {
    Severity.CRITICAL: 3,
    Severity.WATCH: 2,
    Severity.INFO: 1,
}

# Number of exception rules (EX-01 to EX-24)
EXCEPTION_RULE_COUNT = 24

# Number of MVP KPIs
KPI_COUNT = 10

# Number of dashboard sections
DASHBOARD_SECTION_COUNT = 6

# Number of report types
REPORT_TYPE_COUNT = 7
