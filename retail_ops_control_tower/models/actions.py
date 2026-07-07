"""Dataclass model for the actions table (intervention records)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Action:
    action_id: str
    exception_id: str
    campaign_id: str
    store_id: str
    assigned_by: str
    assigned_to: str
    action_type: str
    action_timestamp: str
    action_status: str
    outcome: str
    time_to_action_hours: float
    notes: str
