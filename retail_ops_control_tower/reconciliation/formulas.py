"""Reconciliation formulas used by the control tower."""

from __future__ import annotations


def _safe_ratio(numerator: float, denominator: float) -> float:
    """Return numerator / denominator with zero-denominator protection."""
    return 0.0 if denominator == 0 else numerator / denominator


def allocation_accuracy(shipped: int | float, planned: int | float) -> float:
    """Return shipped quantity divided by planned quantity."""
    return _safe_ratio(float(shipped), float(planned))


def fill_rate(shipped: int | float, planned: int | float) -> float:
    """Return shipped-to-plan fill rate."""
    return allocation_accuracy(shipped, planned)


def receiving_accuracy(received: int | float, shipped: int | float) -> float:
    """Return received quantity divided by shipped quantity."""
    return _safe_ratio(float(received), float(shipped))


def sell_through(sold: int | float, received: int | float) -> float:
    """Return sold quantity divided by received quantity."""
    return _safe_ratio(float(sold), float(received))


def on_hand(received: int | float, sold: int | float) -> float:
    """Return current on-hand quantity after sales."""
    return max(float(received) - float(sold), 0.0)


def weeks_of_cover(on_hand_qty: int | float, sold: int | float, days: int = 7) -> float:
    """Return weeks of cover based on sales velocity over ``days``."""
    sold = float(sold)
    if sold <= 0:
        return float("inf")
    daily_velocity = sold / max(days, 1)
    return float(on_hand_qty) / daily_velocity / 7


def variance(actual: int | float, expected: int | float) -> float:
    """Return actual minus expected."""
    return float(actual) - float(expected)


def variance_rate(actual: int | float, expected: int | float) -> float:
    """Return (actual - expected) / expected."""
    return _safe_ratio(variance(actual, expected), float(expected))
