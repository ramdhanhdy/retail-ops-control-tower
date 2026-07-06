"""Tests for the verification analytics module."""
import pandas as pd

from retail_ops_control_tower.verification.analytics import (
    compute_resolution_rates,
    compute_effect_size,
    recover_injected_effect,
)


def test_resolution_rates():
    outcomes = pd.read_csv("data/sample/intervention_outcomes.csv")
    rates = compute_resolution_rates(outcomes)
    assert rates["intervention_rate"] > rates["control_rate"]
    assert "absolute_effect" in rates


def test_effect_size():
    outcomes = pd.read_csv("data/sample/intervention_outcomes.csv")
    result = compute_effect_size(outcomes)
    assert "cohens_h" in result
    assert result["cohens_h"] > 0.3


def test_recover_injected_effect():
    outcomes = pd.read_csv("data/sample/intervention_outcomes.csv")
    recovery = recover_injected_effect(outcomes, injected_effect=0.30)
    assert recovery["within_confidence_bounds"] is True
    assert abs(recovery["estimated_effect"] - 0.30) < 0.08
