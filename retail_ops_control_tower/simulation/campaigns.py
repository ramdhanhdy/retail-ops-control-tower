"""Campaign table generator."""

from __future__ import annotations

from retail_ops_control_tower.simulation._shared import table


def generate_campaigns(seed: int = 42, campaign_count: int = 3) -> list[dict]:
    """Generate campaign master records."""
    return table("campaigns", seed=seed, campaign_count=campaign_count)
