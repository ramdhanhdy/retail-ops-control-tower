"""Dataclass model for intervention outcomes table."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class InterventionOutcome:
    outcome_id: str
    exception_id: str
    action_id: str
    store_id: str
    exception_type: str
    received_intervention: bool
    matched_control_store_id: str
    matched_control_exception_id: str
    resolved: bool
    control_resolved: bool
    days_to_resolution: int
    control_days_to_resolution: int
    revenue_impact_usd: float
    counterfactual_revenue_loss_usd: float
