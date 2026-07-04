"""Allocation plan generator."""

from __future__ import annotations

from retail_ops_control_tower.simulation._shared import table


def generate_allocation_plan(seed: int = 42) -> list[dict]:
    """Generate planned allocation lines for stores, campaigns, and SKUs."""
    return table("allocation_plan", seed=seed)
