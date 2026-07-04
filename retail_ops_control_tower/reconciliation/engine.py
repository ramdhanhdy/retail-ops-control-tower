"""Reconciliation orchestrator.

Reads sample CSV or JSON data, runs the implemented exception engine, and
writes action-ready exception outputs.
"""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Any

from retail_ops_control_tower.exceptions.engine import ExceptionEngine
from retail_ops_control_tower.io import read_all_csv_tables, read_all_tables, write_csv_table


def _read_tables(input_dir: str) -> dict[str, list[dict[str, Any]]]:
    has_csv = any(name.endswith(".csv") for name in os.listdir(input_dir)) if os.path.isdir(input_dir) else False
    if has_csv:
        return read_all_csv_tables(input_dir)
    return read_all_tables(input_dir)


def run_reconciliation(
    input_dir: str = "output",
    output_dir: str = "output",
    aging_date: date | None = None,
) -> dict[str, Any]:
    """Run exception detection and write reconciliation outputs.

    Outputs:
    - ``exceptions.csv``
    - ``daily_action_list.csv``
    - ``reconciliation_summary.json``
    """
    aging_date = aging_date or date.today()
    tables = _read_tables(input_dir)
    engine = ExceptionEngine(tables, aging_date)
    report = engine.detect()
    action_items = engine.build_action_list(top_n=0)

    os.makedirs(output_dir, exist_ok=True)
    exception_rows = [item.to_dict() for item in report.exceptions]
    action_rows = [item.to_dict() for item in action_items]

    if exception_rows:
        write_csv_table("exceptions", exception_rows, output_dir, list(exception_rows[0].keys()))
    else:
        write_csv_table("exceptions", [], output_dir, ["exception_id", "exception_type", "severity", "status"])
    if action_rows:
        write_csv_table("daily_action_list", action_rows, output_dir, list(action_rows[0].keys()))
    else:
        write_csv_table("daily_action_list", [], output_dir, ["exception_id", "exception_type", "severity", "status"])

    summary = {
        "formulas_computed": 8,
        "rules_evaluated": 9,
        "exceptions_raised": report.total,
        "critical": report.critical_count,
        "watch": report.watch_count,
        "info": report.info_count,
        "open": report.open_count,
        "sla_breached": report.breached_count,
        "aging_date": aging_date.isoformat(),
    }
    with open(os.path.join(output_dir, "reconciliation_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return summary
