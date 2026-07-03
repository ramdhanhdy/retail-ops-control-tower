"""Configuration dataclass, default values, and thresholds.

Centralizes all configurable parameters so threshold tuning happens in one
place. Values are starting defaults drawn from the PRD and research documents,
not validated benchmarks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Config:
    """Global configuration for the Retail Operations Control Tower.

    Attributes are immutable so a config instance can be safely shared across
    components.
    """

    # Simulation defaults
    store_count: int = 40
    campaign_id: str = "summer-peach-lto-2026"
    sku_count: int = 12
    campaign_days: int = 28
    seed: int = 42

    # Tolerance thresholds
    allocation_shortage_tolerance: float = 0.05
    critical_shortage_tolerance: float = 0.20
    receiving_tolerance: float = 0.10

    # WOC thresholds
    stockout_woc_multiplier: float = 1.0  # WOC < lead_time * multiplier
    overstock_woc_multiplier: float = 2.0  # WOC > lead_time * multiplier

    # Sell-through thresholds
    sellthrough_miss_threshold: float = 0.70
    critical_sellthrough_miss: float = 0.50

    # Severity SLA windows (hours)
    critical_sla_hours: int = 24
    watch_sla_hours: int = 48
    watch_sla_investigate_hours: int = 72
    info_sla_days: int = 7
    info_sla_investigate_days: int = 14

    # Aging buckets (days)
    aging_bucket_0_max: int = 5   # 0-5
    aging_bucket_1_max: int = 15  # 6-15
    aging_bucket_2_max: int = 30  # 16-30
    # bucket 3: 30+

    # Action list
    action_list_size: int = 20

    # Reopen escalation
    reopen_escalation_threshold: int = 2
    reopen_escalation_window_days: int = 30

    # SLA pause limits (hours)
    pause_vendor_max_hours: int = 72
    pause_store_max_hours: int = 48
    pause_system_grace_hours: int = 4
    pause_transit_grace_hours: int = 24


DEFAULT_CONFIG = Config()
