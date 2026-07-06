"""Tests for the InterventionOutcome model and outcomes generation."""
from retail_ops_control_tower.models.intervention_outcomes import InterventionOutcome


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
