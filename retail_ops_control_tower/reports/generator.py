"""Report orchestrator."""

from __future__ import annotations

import os
from datetime import date

from retail_ops_control_tower.io import read_all_csv_tables
from retail_ops_control_tower.reporting import WeeklyReportGenerator


def generate_reports(
    input_dir: str = "output",
    output_dir: str = "output/reports",
    section: str = "all",
    fmt: str = "text",
    aging_date: date | None = None,
) -> list[str]:
    """Generate weekly operations report files and return their paths."""
    aging_date = aging_date or date.today()
    os.makedirs(output_dir, exist_ok=True)
    tables = read_all_csv_tables(input_dir)
    generator = WeeklyReportGenerator(tables, aging_date=aging_date, week_ending=aging_date)

    paths: list[str] = []
    if section in ("all", "weekly", "full"):
        weekly_path = os.path.join(output_dir, "weekly_ops_report.md")
        with open(weekly_path, "w", encoding="utf-8") as f:
            f.write(generator.generate_full_report() + "\n")
        paths.append(weekly_path)

    if section in ("all", "executive", "summary"):
        summary_path = os.path.join(output_dir, "executive_summary.md")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(generator.generate_executive_summary() + "\n")
        paths.append(summary_path)

    if fmt == "html":
        html_path = os.path.join(output_dir, "weekly_ops_report.html")
        body = generator.generate_full_report().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(f"<pre>{body}</pre>\n")
        paths.append(html_path)

    return paths
