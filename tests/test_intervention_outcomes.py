"""Tests for the InterventionOutcome model and outcomes generation."""
import pandas as pd

from retail_ops_control_tower.models.intervention_outcomes import InterventionOutcome
from retail_ops_control_tower.data_generation import generate_intervention_outcomes


def test_outcome_has_required_fields():
    outcome = InterventionOutcome(
        outcome_id="OUT-001",
        exception_id="EXC-007",
        action_id="ACT-001",
        store_id="S-079",
        exception_type="missing_confirmation",
        received_intervention=True,
        matched_control_store_id="S-045",
        matched_control_exception_id="EXC-045",
        resolved=True,
        control_resolved=False,
        days_to_resolution=1,
        control_days_to_resolution=14,
        revenue_impact_usd=2400.0,
        counterfactual_revenue_loss_usd=4200.0,
    )
    assert outcome.received_intervention is True
    assert outcome.matched_control_store_id == "S-045"


def test_outcomes_have_matched_pairs():
    actions = pd.read_csv("data/sample/actions.csv")
    exceptions = pd.read_csv("data/processed/exceptions.csv")
    stores = pd.read_csv("data/sample/stores.csv")
    outcomes = generate_intervention_outcomes(actions, exceptions, stores, seed=42)
    assert len(outcomes) > 0
    assert outcomes["matched_control_store_id"].notna().all()


def test_intervention_effect_is_visible():
    actions = pd.read_csv("data/sample/actions.csv")
    exceptions = pd.read_csv("data/processed/exceptions.csv")
    stores = pd.read_csv("data/sample/stores.csv")
    outcomes = generate_intervention_outcomes(actions, exceptions, stores, seed=42)
    assert outcomes["resolved"].mean() > outcomes["control_resolved"].mean()
    assert 0.45 < outcomes["resolved"].mean() < 0.75
    assert 0.15 < outcomes["control_resolved"].mean() < 0.45
