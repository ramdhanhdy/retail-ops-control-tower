"""Codified action playbook (8 types -> default actions)."""

from __future__ import annotations

from retail_ops_control_tower.constants import ExceptionType

PLAYBOOK: dict[ExceptionType, str] = {
    ExceptionType.MISSING_CONFIRMATION: "Contact store PIC to post confirmation; verify visit completion.",
    ExceptionType.QUANTITY_MISMATCH: "Reconcile planned vs shipped vs received; initiate DC count verification.",
    ExceptionType.MISSING_PHOTO_PROOF: "Request field rep to re-submit photo proof within 24h.",
    ExceptionType.LATE_SETUP: "Dispatch field rep to complete setup; escalate to area manager.",
    ExceptionType.STOCKOUT_RISK: "Expedite replenishment from DC; consider allocation transfer from overstock stores.",
    ExceptionType.OVERSTOCK_RISK: "Plan markdown or transfer to high-velocity stores.",
    ExceptionType.LOW_SELL_THROUGH: "Review pricing and display; consider promo acceleration.",
    ExceptionType.UNRESOLVED_ISSUE_AGING: "Escalate to operations lead for root-cause review.",
}


def get_default_action(exception_type: ExceptionType) -> str:
    """Get the default action for an exception type."""
    return PLAYBOOK.get(exception_type, "Review and assign owner.")
