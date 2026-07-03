"""StoreConfirmation dataclass (29 fields).

Table: store_confirmations - store receiving and visit records.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StoreConfirmation:
    """One row in the store_confirmations table."""

    confirmation_id: str
    allocation_id: str
    campaign_id: str
    store_id: str
    sku_id: str
    dispatch_id: str
    received_quantity: int
    received_date: str
    visit_id: str
    visit_date: str
    visit_status: str
    visit_type: str
    field_rep_id: str
    setup_completed: bool
    setup_completion_date: str
    audit_level: str  # L1, L2, L3
    audit_score: int
    audit_passed: bool
    posm_placed: bool
    planogram_compliance: bool
    pricing_accuracy: bool
    visit_start_time: str
    visit_end_time: str
    confirmation_posted_at: str
    confirmation_delay_hours: float
    visit_duration_minutes: int
    region: str
    notes: str
