"""Dashboard renderer for text and HTML summaries."""

from __future__ import annotations

from datetime import date
from html import escape
from typing import Any

from retail_ops_control_tower.metrics import MetricsEngine


def render_dashboard(data: dict[str, Any], fmt: str = "text") -> str:
    """Render a compact dashboard summary from table data."""
    metrics = MetricsEngine(data, aging_date=date(2026, 7, 15)).compute()
    lines = ["Retail Operations Control Tower Dashboard", ""]
    for kpi in metrics.to_rows():
        value = kpi["value"]
        unit = kpi["unit"]
        rendered = f"{value:.1%}" if unit == "ratio" else f"{value:,.0f}"
        lines.append(f"- {kpi['kpi_name']}: {rendered}")
    text = "\n".join(lines) + "\n"
    if fmt == "html":
        return "<pre>" + escape(text) + "</pre>"
    return text
