"""Store table generator."""

from __future__ import annotations

from retail_ops_control_tower.simulation._shared import table


def generate_stores(seed: int = 42, store_count: int = 100) -> list[dict]:
    """Generate the store master table."""
    return table("stores", seed=seed, store_count=store_count)
