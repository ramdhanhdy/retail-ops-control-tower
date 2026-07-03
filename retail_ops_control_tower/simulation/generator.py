"""Simulation orchestrator.

Generates all 8 tables and writes JSON output. Deterministic with seed.
"""

from __future__ import annotations

import json
import os
from datetime import date

from retail_ops_control_tower.config import Config, DEFAULT_CONFIG


def run_simulation(
    stores: int = 40,
    campaign_id: str | None = None,
    skus: int = 12,
    days: int = 28,
    seed: int = 42,
    output_dir: str = "output",
    config: Config | None = None,
) -> dict[str, list]:
    """Run the full data simulation pipeline.

    Generates all 8 tables and writes them as JSON files to output_dir.
    Returns a dict mapping table names to lists of records.

    TODO: Implement actual generation logic in subsequent phases.
    """
    if config is None:
        config = DEFAULT_CONFIG

    cid = campaign_id or config.campaign_id

    # Placeholder: actual generation will be implemented in Phase 2
    tables: dict[str, list] = {
        "stores": [],
        "campaigns": [],
        "allocation_plan": [],
        "dispatch": [],
        "store_confirmations": [],
        "photo_proofs": [],
        "sales_daily": [],
        "issues": [],
    }

    # Write JSON output
    os.makedirs(output_dir, exist_ok=True)
    for table_name, records in tables.items():
        path = os.path.join(output_dir, f"{table_name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

    return tables
