"""Summer Peach LTO 2026 demo runner."""

from __future__ import annotations

from datetime import date

from retail_ops_control_tower.data_generation import generate_sample_data
from retail_ops_control_tower.demo.scenarios import SCENARIOS
from retail_ops_control_tower.exceptions.engine import ExceptionEngine
from retail_ops_control_tower.metrics import MetricsEngine


def run_demo(seed: int = 42) -> dict:
    """Run the Day 1, Day 7, and Day 14 demo story in memory."""
    tables = generate_sample_data(seed=seed, write_csv=False)
    aging_date = date(2026, 7, 15)
    exception_engine = ExceptionEngine(tables, aging_date)
    exception_report = exception_engine.detect()
    metrics = MetricsEngine(tables, aging_date, exception_report=exception_report).compute()
    return {
        "status": "completed",
        "days_run": len(SCENARIOS),
        "scenarios": list(SCENARIOS.keys()),
        "exceptions": exception_report.total,
        "critical_exceptions": exception_report.critical_count,
        "kpis": {row["kpi_name"]: row["value"] for row in metrics.to_rows()},
    }
