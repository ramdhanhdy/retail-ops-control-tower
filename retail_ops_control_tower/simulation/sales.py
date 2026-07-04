"""Daily sales table generator."""

from __future__ import annotations

from retail_ops_control_tower.simulation._shared import table


def generate_daily_sales(seed: int = 42) -> list[dict]:
    """Generate daily sales and on-hand records."""
    return table("sales_daily", seed=seed)
