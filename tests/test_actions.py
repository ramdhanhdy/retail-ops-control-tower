"""Tests for the Action model and actions generation."""
from retail_ops_control_tower.models.actions import Action


def test_action_has_required_fields():
    action = Action(
        action_id="ACT-001",
        exception_id="EXC-007",
        campaign_id="C-2026-PEACH",
        store_id="S-079",
        assigned_by="Ops Lead",
        assigned_to="Marcus Lee",
        action_type="phone_call",
        action_timestamp="2026-06-26T09:00:00-05:00",
        action_status="completed",
        outcome="resolved",
        time_to_action_hours=14.0,
        notes="Called store PIC, confirmation posted same day.",
    )
    assert action.action_id == "ACT-001"
    assert action.outcome == "resolved"
