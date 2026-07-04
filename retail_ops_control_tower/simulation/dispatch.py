"""Dispatch table generator."""

from __future__ import annotations

from retail_ops_control_tower.simulation._shared import table


def generate_dispatch(seed: int = 42) -> list[dict]:
    """Generate dispatch records derived from the allocation plan."""
    return table("dispatch", seed=seed)
