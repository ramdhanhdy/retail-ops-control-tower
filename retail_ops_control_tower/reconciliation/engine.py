"""Reconciliation orchestrator.

Reads simulated data, computes 16 formulas, evaluates 24 exception rules,
and enriches the issues table.
"""

from __future__ import annotations

import json
import os
from datetime import date


def run_reconciliation(
    input_dir: str = "output",
    output_dir: str = "output",
    aging_date: date | None = None,
) -> dict:
    """Run the reconciliation pipeline.

    Reads JSON from input_dir, evaluates formulas and rules, writes enriched
    output to output_dir.

    TODO: Implement actual reconciliation logic in Phase 3.
    """
    if aging_date is None:
        aging_date = date.today()

    # Load input tables
    tables: dict[str, list] = {}
    for table_name in [
        "stores", "campaigns", "allocation_plan", "dispatch",
        "store_confirmations", "photo_proofs", "sales_daily", "issues",
    ]:
        path = os.path.join(input_dir, f"{table_name}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                tables[table_name] = json.load(f)
        else:
            tables[table_name] = []

    # Placeholder: actual reconciliation in Phase 3
    result: dict = {
        "formulas_computed": 0,
        "rules_evaluated": 0,
        "exceptions_raised": 0,
        "aging_date": aging_date.isoformat(),
    }

    return result
