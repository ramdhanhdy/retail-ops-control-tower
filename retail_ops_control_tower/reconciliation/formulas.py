"""16 reconciliation formulas (6 process, 6 performance, 4 risk).

See PRD Section 9 worked example:
    Planned: 200, Shipped: 190, Received: 188, Sold: 150, On-hand: 38, Lead time: 2 weeks.
    Allocation accuracy: 94%, Fill rate: 95%, Receiving accuracy: 98.95%,
    Sell-through: 79.8%, WOC: 1.01 weeks, Stockout risk: 1.
"""

from __future__ import annotations


def allocation_accuracy(shipped: int, planned: int) -> float:
    """Allocation accuracy: shipped / planned. TODO: Phase 3."""
    if planned == 0:
        return 0.0
    return shipped / planned


def fill_rate(shipped: int, planned: int) -> float:
    """Shipped-to-plan fill rate. TODO: Phase 3."""
    if planned == 0:
        return 0.0
    return shipped / planned


def receiving_accuracy(received: int, shipped: int) -> float:
    """Receiving accuracy. TODO: Phase 3."""
    if shipped == 0:
        return 0.0
    return received / shipped


def sell_through(sold: int, received: int) -> float:
    """Sell-through rate. TODO: Phase 3."""
    if received == 0:
        return 0.0
    return sold / received


def weeks_of_cover(on_hand: int, sold: int, days: int = 7) -> float:
    """Weeks of cover. TODO: Phase 3."""
    if sold == 0:
        return float("inf")
    return (on_hand / sold) * (days / 7)
