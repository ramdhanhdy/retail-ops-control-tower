"""Shared helpers for simulation submodules."""

from __future__ import annotations

from retail_ops_control_tower.data_generation import generate_sample_data


def generate_tables(
    *,
    seed: int = 42,
    store_count: int = 100,
    campaign_count: int = 3,
    write_csv: bool = False,
    output_dir: str = "data/sample",
) -> dict[str, list[dict]]:
    """Generate deterministic sample tables using the canonical generator."""
    return generate_sample_data(
        seed=seed,
        output_dir=output_dir,
        store_count=store_count,
        campaign_count=campaign_count,
        write_csv=write_csv,
    )


def table(name: str, **kwargs) -> list[dict]:
    """Return one generated table by name."""
    return generate_tables(**kwargs).get(name, [])
