"""Build the exception table and daily action list from sample data.

Reads the 8 data tables from data/sample/*.csv, runs the T10 exception
detection engine, and writes two output files to data/processed/:

    - exceptions.csv:        full exception table with all detected exceptions.
    - daily_action_list.csv: sorted, filtered action list for daily operations.

Usage:
    python scripts/build_exception_table.py
    python scripts/build_exception_table.py --aging-date 2026-07-15
    python scripts/build_exception_table.py --input-dir data/sample --output-dir data/processed
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import date

# Ensure the package is importable when running the script directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retail_ops_control_tower.io import read_all_csv_tables
from retail_ops_control_tower.data_generation import _format_value
from retail_ops_control_tower.exceptions import (
    ExceptionEngine,
    EXCEPTION_TYPES,
)

DEFAULT_INPUT_DIR = "data/sample"
DEFAULT_OUTPUT_DIR = "data/processed"
DEFAULT_AGING_DATE = "2026-07-15"

EXCEPTION_COLUMNS = [
    "exception_id",
    "exception_type",
    "severity",
    "owner",
    "region",
    "area_manager",
    "age_days",
    "status",
    "recommended_action",
    "campaign_id",
    "store_id",
    "sku",
    "allocation_id",
    "confirmation_id",
    "message",
    "created_date",
    "sla_status",
    "priority_score",
]

ACTION_LIST_COLUMNS = [
    "rank",
    "exception_id",
    "exception_type",
    "severity",
    "priority_score",
    "owner",
    "region",
    "area_manager",
    "store_id",
    "campaign_id",
    "sku",
    "age_days",
    "sla_status",
    "recommended_action",
    "message",
]



def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build exception table and daily action list from sample data."
    )
    parser.add_argument(
        "--input-dir",
        default=DEFAULT_INPUT_DIR,
        help="Directory containing the 8 input CSV tables (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for output CSV files (default: %(default)s)",
    )
    parser.add_argument(
        "--aging-date",
        default=DEFAULT_AGING_DATE,
        help="Aging date as YYYY-MM-DD (default: %(default)s)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=0,
        help="Maximum number of action list items (0 = all, default: %(default)s)",
    )
    args = parser.parse_args(argv)

    aging_date = date.fromisoformat(args.aging_date)

    print(f"Reading data from {args.input_dir}/")
    tables = read_all_csv_tables(args.input_dir)

    row_counts = {name: len(rows) for name, rows in tables.items()}
    for name in sorted(row_counts):
        print(f"  {name}: {row_counts[name]} rows")

    print(f"\nDetecting exceptions (aging date: {aging_date})")
    engine = ExceptionEngine(tables, aging_date)
    report = engine.detect()

    print(f"  Total exceptions: {report.total}")
    print(f"  Critical: {report.critical_count}")
    print(f"  Watch: {report.watch_count}")
    print(f"  Info: {report.info_count}")
    print(f"  Open/active: {report.open_count}")
    print(f"  SLA breached: {report.breached_count}")

    print("\nExceptions by type:")
    for exc_type in EXCEPTION_TYPES:
        count = len(report.by_type(exc_type))
        print(f"  {exc_type}: {count}")

    # Write exceptions.csv
    os.makedirs(args.output_dir, exist_ok=True)
    exceptions_path = os.path.join(args.output_dir, "exceptions.csv")
    with open(exceptions_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXCEPTION_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for exc in report.exceptions:
            row = exc.to_dict()
            writer.writerow({col: _format_value(row.get(col, "")) for col in EXCEPTION_COLUMNS})
    print(f"\nWrote {exceptions_path} ({report.total} exceptions)")

    # Build and write daily_action_list.csv
    action_items = engine.build_action_list(top_n=args.top_n)
    action_list_path = os.path.join(args.output_dir, "daily_action_list.csv")
    with open(action_list_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ACTION_LIST_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for rank, exc in enumerate(action_items, 1):
            row = exc.to_dict()
            row["rank"] = rank
            writer.writerow({col: _format_value(row.get(col, "")) for col in ACTION_LIST_COLUMNS})
    print(f"Wrote {action_list_path} ({len(action_items)} action items)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
