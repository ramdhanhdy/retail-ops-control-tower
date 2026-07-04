"""Store confirmation table generator."""

from __future__ import annotations

from retail_ops_control_tower.simulation._shared import table


def generate_confirmations(seed: int = 42) -> list[dict]:
    """Generate store receiving and setup confirmation records."""
    return table("store_confirmations", seed=seed)
