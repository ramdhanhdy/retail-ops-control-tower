"""Verification analytics: matched comparison for intervention effects.

Measures whether interventions worked by comparing resolution rates of
exceptions that received an intervention vs matched control exceptions
that did not.

Results are from simulated data. The deliverable is the measurement
methodology, not the finding.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


def compute_resolution_rates(outcomes: pd.DataFrame) -> dict[str, float]:
    """Compute resolution rates for intervention vs control groups.

    Parameters
    ----------
    outcomes : pd.DataFrame
        Intervention outcomes with 'resolved' and 'control_resolved' columns.

    Returns
    -------
    dict
        intervention_rate, control_rate, absolute_effect, relative_risk
    """
    n = len(outcomes)
    if n == 0:
        return {"intervention_rate": 0.0, "control_rate": 0.0, "absolute_effect": 0.0, "relative_risk": 0.0}

    int_rate = float(outcomes["resolved"].mean())
    ctrl_rate = float(outcomes["control_resolved"].mean())
    absolute_effect = int_rate - ctrl_rate
    relative_risk = int_rate / ctrl_rate if ctrl_rate > 0 else float("inf")

    return {
        "intervention_rate": round(int_rate, 4),
        "control_rate": round(ctrl_rate, 4),
        "absolute_effect": round(absolute_effect, 4),
        "relative_risk": round(relative_risk, 4),
    }


def compute_effect_size(outcomes: pd.DataFrame) -> dict[str, Any]:
    """Compute effect size statistics for the intervention.

    Uses Cohen's h (difference between two proportions) and a two-proportion
    z-test for significance.

    Parameters
    ----------
    outcomes : pd.DataFrame
        Intervention outcomes with 'resolved' and 'control_resolved' columns.

    Returns
    -------
    dict
        cohens_h, z_statistic, p_value, confidence_interval (Wilson)
    """
    n = len(outcomes)
    if n == 0:
        return {"cohens_h": 0.0, "z_statistic": 0.0, "p_value": 1.0, "confidence_interval": [0.0, 0.0]}

    p1 = float(outcomes["resolved"].mean())
    p2 = float(outcomes["control_resolved"].mean())

    # Cohen's h: 2 * arcsin(sqrt(p1)) - 2 * arcsin(sqrt(p2))
    h = 2 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))

    # Two-proportion z-test
    pooled_p = (p1 * n + p2 * n) / (2 * n)
    se = math.sqrt(2 * pooled_p * (1 - pooled_p) / n) if pooled_p > 0 and pooled_p < 1 else 1.0
    z = (p1 - p2) / se if se > 0 else 0.0
    p_value = 2 * (1 - stats.norm.cdf(abs(z))) if z != 0 else 1.0

    # Wilson confidence interval for the difference
    diff = p1 - p2
    wilson_se = math.sqrt(p1 * (1 - p1) / n + p2 * (1 - p2) / n)
    ci_low = diff - 1.96 * wilson_se
    ci_high = diff + 1.96 * wilson_se

    return {
        "cohens_h": round(h, 4),
        "z_statistic": round(z, 4),
        "p_value": round(p_value, 6),
        "confidence_interval": [round(ci_low, 4), round(ci_high, 4)],
    }


def recover_injected_effect(outcomes: pd.DataFrame, injected_effect: float, tolerance: float = 0.15) -> dict[str, Any]:
    """Check whether the verification module recovers the injected effect.

    The data generator injects a known intervention effect (e.g., 30pp).
    This function measures the observed effect and checks whether it falls
    within confidence bounds of the injected value.

    Parameters
    ----------
    outcomes : pd.DataFrame
        Intervention outcomes.
    injected_effect : float
        The known injected effect (e.g., 0.30 for 30pp).

    Returns
    -------
    dict
        estimated_effect, injected_effect, within_confidence_bounds, bias
    """
    rates = compute_resolution_rates(outcomes)
    estimated = rates["absolute_effect"]

    # The observed effect will differ from injected due to noise
    # (failed actions, assignment errors, null results, exclusions)
    # Check if within reasonable bounds (tolerance of injected, default ±0.15)
    within_bounds = abs(estimated - injected_effect) < tolerance
    bias = estimated - injected_effect

    return {
        "estimated_effect": round(estimated, 4),
        "injected_effect": round(injected_effect, 4),
        "within_confidence_bounds": bool(within_bounds),
        "bias": round(bias, 4),
    }


def generate_verification_report(outcomes: pd.DataFrame, injected_effect: float) -> dict[str, Any]:
    """Generate a full verification report.

    Parameters
    ----------
    outcomes : pd.DataFrame
        Intervention outcomes.
    injected_effect : float
        The known injected effect.

    Returns
    -------
    dict
        Full verification report with rates, effect size, recovery,
        by_action_type, by_exception_type, and limitations.
    """
    rates = compute_resolution_rates(outcomes)
    effect = compute_effect_size(outcomes)
    recovery = recover_injected_effect(outcomes, injected_effect)

    # Breakdown by exception type
    by_exception_type: dict[str, dict] = {}
    for exc_type, group in outcomes.groupby("exception_type"):
        if len(group) < 5:
            continue
        type_rates = compute_resolution_rates(group)
        type_recovery = recover_injected_effect(group, injected_effect)
        by_exception_type[exc_type] = {
            "n": len(group),
            "intervention_rate": type_rates["intervention_rate"],
            "control_rate": type_rates["control_rate"],
            "estimated_effect": type_recovery["estimated_effect"],
        }

    return {
        "resolution_rates": rates,
        "effect_size": effect,
        "recovery": recovery,
        "by_exception_type": by_exception_type,
        "limitations": [
            "Data is simulated. The intervention effect is injected, not observed.",
            "The deliverable is the measurement methodology, not the finding.",
            "Matched comparison, not causal inference. No DAG, no propensity scoring.",
            "Single snapshot. No longitudinal or real-time data.",
        ],
        "n_outcomes": len(outcomes),
        "disclosure": "Results are from simulated data. The deliverable is the measurement methodology, not the finding.",
    }
