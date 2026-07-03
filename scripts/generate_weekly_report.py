"""Generate the weekly operations report from sample data.

Reads the 8 data tables from data/sample/*.csv, runs the T09 validation
engine, T10 exception engine, and T11 metrics engine, and writes two
Markdown reports to reports/:

    - weekly_ops_report.md:  full 8-section weekly operations brief.
    - executive_summary.md:  short executive summary with top action items.

Usage:
    python scripts/generate_weekly_report.py
    python scripts/generate_weekly_report.py --aging-date 2026-07-15
    python scripts/generate_weekly_report.py --input-dir data/sample --output-dir reports
    python scripts/generate_weekly_report.py --week-ending 2026-07-15
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date

# Ensure the package is importable when running the script directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retail_ops_control_tower.io import read_all_csv_tables
from retail_ops_control_tower.reporting import (
    DEFAULT_AGING_DATE,
    WeeklyReportGenerator,
)

DEFAULT_INPUT_DIR = "data/sample"
DEFAULT_OUTPUT_DIR = "reports"
DEFAULT_WEEK_ENDING = "2026-07-15"

FULL_REPORT_FILENAME = "weekly_ops_report.md"
EXECUTIVE_SUMMARY_FILENAME = "executive_summary.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the weekly operations report from sample data."
    )
    parser.add_argument(
        "--input-dir",
        default=DEFAULT_INPUT_DIR,
        help="Directory containing the 8 input CSV tables (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for output Markdown reports (default: %(default)s)",
    )
    parser.add_argument(
        "--aging-date",
        default=DEFAULT_AGING_DATE.isoformat(),
        help="Aging date as YYYY-MM-DD (default: %(default)s)",
    )
    parser.add_argument(
        "--week-ending",
        default=DEFAULT_WEEK_ENDING,
        help="Week ending date as YYYY-MM-DD (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    aging_date = date.fromisoformat(args.aging_date)
    week_ending = date.fromisoformat(args.week_ending)

    print(f"Reading data from {args.input_dir}/")
    tables = read_all_csv_tables(args.input_dir)

    row_counts = {name: len(rows) for name, rows in tables.items()}
    for name in sorted(row_counts):
        print(f"  {name}: {row_counts[name]} rows")

    print(f"\nGenerating report (aging date: {aging_date}, week ending: {week_ending})")
    generator = WeeklyReportGenerator(tables, aging_date, week_ending)

    full_report = generator.generate_full_report()
    exec_summary = generator.generate_executive_summary()

    # Write reports.
    os.makedirs(args.output_dir, exist_ok=True)

    full_path = os.path.join(args.output_dir, FULL_REPORT_FILENAME)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(full_report)
    print(f"\nWrote {full_path} ({len(full_report):,} chars)")

    exec_path = os.path.join(args.output_dir, EXECUTIVE_SUMMARY_FILENAME)
    with open(exec_path, "w", encoding="utf-8") as f:
        f.write(exec_summary)
    print(f"Wrote {exec_path} ({len(exec_summary):,} chars)")

    # Print summary stats.
    ctx = generator.context
    print(f"\nReport summary:")
    print(f"  Total exceptions: {ctx.exception_report.total}")
    print(f"  Open exceptions: {ctx.exception_report.open_count}")
    print(f"  Critical: {ctx.exception_report.critical_count}")
    print(f"  SLA breached: {ctx.exception_report.breached_count}")
    print(f"  KPIs computed: {len(ctx.metrics_summary.kpis)}")
    print(f"  AM scorecard rows: {len(ctx.am_scorecard)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
