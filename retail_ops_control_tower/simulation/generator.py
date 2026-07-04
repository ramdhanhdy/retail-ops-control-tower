"""Simulation orchestrator.

Generates all 8 sample tables with the canonical deterministic data generator.
This module keeps the original JSON-oriented CLI contract while the portfolio
pipeline uses CSV files for analytics.
"""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Any

from retail_ops_control_tower.config import Config, DEFAULT_CONFIG
from retail_ops_control_tower.simulation._shared import generate_tables


def _json_safe(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    return value


def run_simulation(
    stores: int = 40,
    campaign_id: str | None = None,
    skus: int = 12,
    days: int = 28,
    seed: int = 42,
    output_dir: str = "output",
    config: Config | None = None,
) -> dict[str, list[dict]]:
    """Generate all 8 tables and write them as JSON files.

    Parameters such as ``campaign_id``, ``skus``, and ``days`` are accepted for
    CLI compatibility. The canonical sample generator controls the campaign and
    SKU templates so that the whole portfolio remains deterministic.
    """
    config = config or DEFAULT_CONFIG
    table_data = generate_tables(
        seed=seed,
        store_count=stores,
        campaign_count=1 if campaign_id or config.campaign_id else 3,
        write_csv=False,
    )

    if campaign_id:
        campaigns = table_data.get("campaigns", [])
        if campaigns:
            original = campaigns[0].get("campaign_id")
            campaigns[0]["campaign_id"] = campaign_id
            for records in table_data.values():
                for row in records:
                    if row.get("campaign_id") == original:
                        row["campaign_id"] = campaign_id

    os.makedirs(output_dir, exist_ok=True)
    for table_name, records in table_data.items():
        path = os.path.join(output_dir, f"{table_name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False, default=_json_safe)

    return table_data
