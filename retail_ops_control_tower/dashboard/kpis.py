"""KPI computations and threshold colors for dashboard helpers."""

from __future__ import annotations

from datetime import date
from typing import Any

from retail_ops_control_tower.constants import ThresholdColor
from retail_ops_control_tower.metrics import MetricsEngine


def compute_kpi(name: str, data: dict[str, Any]) -> float:
    """Compute a KPI by name from a table mapping or KPI row mapping."""
    if "kpis" in data and isinstance(data["kpis"], dict):
        value = data["kpis"].get(name, 0.0)
        return float(getattr(value, "value", value) or 0.0)
    if name in data and isinstance(data[name], (int, float)):
        return float(data[name])
    engine = MetricsEngine(data, aging_date=date(2026, 7, 15))
    return float(engine.compute().get(name))


def threshold_color(kpi_name: str, value: float) -> ThresholdColor:
    """Return threshold color for a KPI value."""
    lower_is_worse = {
        "campaign_readiness_rate",
        "confirmation_completion_rate",
        "photo_proof_completion_rate",
        "allocation_accuracy_rate",
        "sell_through_rate",
    }
    if kpi_name in lower_is_worse:
        if value >= 0.90:
            return ThresholdColor.GREEN
        if value >= 0.75:
            return ThresholdColor.AMBER
        return ThresholdColor.RED
    if "count" in kpi_name or "backlog" in kpi_name or "rate" in kpi_name:
        if value <= 0:
            return ThresholdColor.GREEN
        if value <= 100:
            return ThresholdColor.AMBER
        return ThresholdColor.RED
    return ThresholdColor.GREEN
