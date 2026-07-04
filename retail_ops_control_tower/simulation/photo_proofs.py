"""Photo proof table generator."""

from __future__ import annotations

from retail_ops_control_tower.simulation._shared import table


def generate_photo_proofs(seed: int = 42) -> list[dict]:
    """Generate photo proof metadata records."""
    return table("photo_proofs", seed=seed)
