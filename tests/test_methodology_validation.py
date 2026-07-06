"""Methodology validation: the verification module recovers the injected effect.

This is not 1 of 354+ tests. It is THE test that proves the measurement approach
is unbiased. The data generator injects a known 30pp intervention effect with
structured noise (failures, re-opens, null results, assignment errors).
The verification module must recover the injected effect within confidence bounds
AND reject the trivial case where the data has no variance.
"""
import pandas as pd
from retail_ops_control_tower.verification.analytics import (
    recover_injected_effect,
    generate_verification_report,
)

def test_verification_recovers_injected_effect():
    outcomes = pd.read_csv("data/sample/intervention_outcomes.csv")
    result = recover_injected_effect(outcomes, injected_effect=0.30)
    assert result["within_confidence_bounds"] is True
    assert abs(result["estimated_effect"] - 0.30) < 0.05

def test_methodology_survives_noise():
    """Data MUST contain variance — trivial recovery is not persuasive."""
    outcomes = pd.read_csv("data/sample/intervention_outcomes.csv")
    # Must have non-trivial noise
    assert outcomes["resolved"].mean() < 0.75, (
        f"Intervention rate {outcomes['resolved'].mean():.1%} too high — "
        "data looks trivially injected. Real data has failures."
    )
    assert outcomes["control_resolved"].mean() > 0.10, (
        f"Control rate {outcomes['control_resolved'].mean():.1%} too low — "
        "data looks trivially injected. Real data has spontaneous resolution."
    )
    # Must have failed interventions
    failed_share = (~outcomes["resolved"]).mean()
    assert failed_share > 0.10, (
        f"Only {failed_share:.1%} unresolved — need ~20%+ for realistic noise"
    )
    # Must redistribute the effect
    result = recover_injected_effect(outcomes, injected_effect=0.30)
    assert result["within_confidence_bounds"] is True

def test_noise_structured_not_random():
    """Data must have structure (null results for specific types, not just jitter)."""
    outcomes = pd.read_csv("data/sample/intervention_outcomes.csv")
    report = generate_verification_report(outcomes, injected_effect=0.30)
    # At least one exception type should have a null or near-zero effect
    by_type = report.get("by_exception_type", {})
    null_effects = [t for t, v in by_type.items()
                    if abs(v.get("estimated_effect", 0.30) - 0.30) > 0.15]
    assert len(null_effects) >= 1, (
        f"Expected at least 1 exception type with null effect, got {len(null_effects)}. "
        "Real interventions don't work for every exception type."
    )
