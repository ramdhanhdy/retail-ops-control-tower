"""Build KPI summary and AM scorecard from sample data.

Reads the 8 data tables from data/sample/*.csv, runs the T10 exception
detection engine, and writes two output files to data/processed/:

    - kpi_summary.csv: 12 dashboard-ready KPIs split into process and
      performance categories.
    - am_scorecard.csv: per-area-manager scorecard with exception
      workload, risk counts, and sell-through.

Usage:
    python scripts/build_kpi_summary.py
    python scripts/build_kpi_summary.py --aging-date 2026-07-15
    python scripts/build_kpi_summary.py --input-dir data/sample --output-dir data/processed
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import date

# Ensure the package is importable when running the script directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retail_ops_control_tower.exceptions import ExceptionEngine
from retail_ops_control_tower.io import read_all_csv_tables
from retail_ops_control_tower.data_generation import _format_value
from retail_ops_control_tower.metrics import (
    ALL_KPIS,
    MetricsEngine,
)

DEFAULT_INPUT_DIR = "data/sample"
DEFAULT_OUTPUT_DIR = "data/processed"
DEFAULT_AGING_DATE = "2026-07-15"

KPI_SUMMARY_COLUMNS = [
    "kpi_name",
    "category",
    "value",
    "unit",
    "description",
]

AM_SCORECARD_COLUMNS = [
    "area_manager",
    "region",
    "store_count",
    "allocation_count",
    "confirmation_count",
    "open_exception_count",
    "critical_count",
    "sla_breach_count",
    "stockout_risk_count",
    "overstock_risk_count",
    "am_follow_up_backlog",
    "sell_through_rate",
    "exception_rate",
]



def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build KPI summary and AM scorecard from sample data."
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
    args = parser.parse_args(argv)

    aging_date = date.fromisoformat(args.aging_date)

    print(f"Reading data from {args.input_dir}/")
    tables = read_all_csv_tables(args.input_dir)

    row_counts = {name: len(rows) for name, rows in tables.items()}
    for name in sorted(row_counts):
        print(f"  {name}: {row_counts[name]} rows")

    # Run exception detection once and reuse for both KPIs and AM scorecard.
    exc_engine = ExceptionEngine(tables, aging_date)
    exc_report = exc_engine.detect()

    print(f"\nException detection (aging date: {aging_date})")
    print(f"  Total exceptions: {exc_report.total}")
    print(f"  Open/active: {exc_report.open_count}")
    print(f"  SLA breached: {exc_report.breached_count}")

    metrics_engine = MetricsEngine(
        tables, aging_date, exception_report=exc_report
    )
    summary = metrics_engine.compute()
    am_rows = metrics_engine.compute_am_scorecard()

    print("\nKPI Summary:")
    for kpi_name in ALL_KPIS:
        if kpi_name in summary.kpis:
            k = summary.kpis[kpi_name]
            print(f"  {kpi_name}: {k.value:.4f} ({k.category}/{k.unit})")

    print(f"\nAM Scorecard: {len(am_rows)} area managers")

    # Write kpi_summary.csv
    os.makedirs(args.output_dir, exist_ok=True)
    kpi_path = os.path.join(args.output_dir, "kpi_summary.csv")
    with open(kpi_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=KPI_SUMMARY_COLUMNS, extrasaction="ignore"
        )
        writer.writeheader()
        for row in summary.to_rows():
            writer.writerow({c: _format_value(row.get(c, "")) for c in KPI_SUMMARY_COLUMNS})
    print(f"\nWrote {kpi_path} ({len(summary.kpis)} KPIs)")

    # Write am_scorecard.csv
    am_path = os.path.join(args.output_dir, "am_scorecard.csv")
    with open(am_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=AM_SCORECARD_COLUMNS, extrasaction="ignore"
        )
        writer.writeheader()
        for row in am_rows:
            writer.writerow(
                {c: _format_value(row.to_dict().get(c, "")) for c in AM_SCORECARD_COLUMNS}
            )
    print(f"Wrote {am_path} ({len(am_rows)} area managers)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
