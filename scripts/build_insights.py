"""Build ranked diagnostic insights from sample data.

Reads the 8 data tables from data/sample/*.csv, runs the T10 exception
detection engine and the T13 insight engine, and writes two outputs:

    - data/processed/insights.csv: ranked diagnostic findings with
      lift, impact score, and recommended actions.
    - reports/insights.md:         human-readable diagnostic brief.

Usage:
    python scripts/build_insights.py
    python scripts/build_insights.py --aging-date 2026-07-15
    python scripts/build_insights.py --input-dir data/sample --output-dir data/processed
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
from retail_ops_control_tower.insights import (
    INSIGHT_CATEGORIES,
    InsightEngine,
    build_insights_markdown,
)

DEFAULT_INPUT_DIR = "data/sample"
DEFAULT_OUTPUT_DIR = "data/processed"
DEFAULT_REPORT_DIR = "reports"
DEFAULT_AGING_DATE = "2026-07-15"

INSIGHT_COLUMNS = [
    "insight_id",
    "category",
    "headline",
    "detail",
    "metric_name",
    "metric_value",
    "baseline_value",
    "lift",
    "affected_count",
    "impact_score",
    "recommended_action",
    "evidence",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build ranked diagnostic insights from sample data."
    )
    parser.add_argument(
        "--input-dir",
        default=DEFAULT_INPUT_DIR,
        help="Directory containing the 8 input CSV tables (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for the insights CSV (default: %(default)s)",
    )
    parser.add_argument(
        "--report-dir",
        default=DEFAULT_REPORT_DIR,
        help="Directory for the markdown brief (default: %(default)s)",
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

    # Run exception detection once and reuse for the insight engine.
    exc_engine = ExceptionEngine(tables, aging_date)
    exc_report = exc_engine.detect()

    print(f"\nException detection (aging date: {aging_date})")
    print(f"  Total exceptions: {exc_report.total}")

    engine = InsightEngine(tables, aging_date, exception_report=exc_report)
    report = engine.generate()

    print(f"\nDiagnostic insights: {report.total} ranked findings")
    for category in INSIGHT_CATEGORIES:
        findings = report.by_category(category)
        if findings:
            print(f"  {category}: {len(findings)}")

    if report.insights:
        print("\nTop findings:")
        for insight in report.insights[:5]:
            print(f"  {insight.insight_id} [{insight.impact_score}] {insight.headline}")

    # Write insights.csv
    os.makedirs(args.output_dir, exist_ok=True)
    csv_path = os.path.join(args.output_dir, "insights.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=INSIGHT_COLUMNS, extrasaction="ignore"
        )
        writer.writeheader()
        for insight in report.insights:
            row = insight.to_dict()
            writer.writerow({c: _format_value(row.get(c, "")) for c in INSIGHT_COLUMNS})
    print(f"\nWrote {csv_path} ({report.total} insights)")

    # Write insights.md
    os.makedirs(args.report_dir, exist_ok=True)
    md_path = os.path.join(args.report_dir, "insights.md")
    markdown = build_insights_markdown(report)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"Wrote {md_path} ({len(markdown):,} chars)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
