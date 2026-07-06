"""Tests for the Action model and actions generation."""
import pandas as pd

from retail_ops_control_tower.models.actions import Action
from retail_ops_control_tower.data_generation import generate_actions


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


def test_actions_generated_for_breached_exceptions():
    exceptions = pd.read_csv("data/processed/exceptions.csv")
    actions = generate_actions(exceptions, seed=42)
    assert len(actions) > 0
    assert "action_id" in actions.columns
    assert "outcome" in actions.columns


def test_actions_have_realistic_outcomes():
    exceptions = pd.read_csv("data/processed/exceptions.csv")
    actions = generate_actions(exceptions, seed=42)
    outcomes = actions["outcome"].value_counts()
    assert "resolved" in outcomes.index
    assert "unresolved" in outcomes.index
    resolved_share = outcomes.get("resolved", 0) / len(actions)
    assert 0.40 < resolved_share < 0.85
