"""10 MVP KPI computations and threshold tables.

KPIs (5 process, 5 risk):
    1. Network Compliance %
    2. OSA %
    3. Campaign Coverage %
    4. Campaign Compliance %
    5. On-Launch Activation %
    6. Stockout Risk Items Count
    7. Open Exception Count
    8. Aged Exception Count (30+)
    9. MTTR (hours)
    10. SLA Met %
"""

from __future__ import annotations

from retail_ops_control_tower.constants import ThresholdColor


def compute_kpi(name: str, data: dict) -> float:
    """Compute a KPI by name. TODO: Phase 5."""
    return 0.0


def threshold_color(kpi_name: str, value: float) -> ThresholdColor:
    """Return threshold color for a KPI value. TODO: Phase 5."""
    return ThresholdColor.GREEN
