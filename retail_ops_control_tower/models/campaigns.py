"""Campaign dataclass (15 fields).

Table: campaigns - campaign master with dates, status, and scope.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Campaign:
    """One row in the campaigns table."""

    campaign_id: str
    campaign_name: str
    campaign_type: str  # e.g. "LTO", "seasonal", "promo"
    start_date: str  # ISO date string
    end_date: str  # ISO date string
    status: str
    hq_owner: str
    region_scope: str  # "all", "north", etc.
    store_count: int
    sku_count: int
    sku_ids: list[str] = field(default_factory=list)
    hero_sku_ids: list[str] = field(default_factory=list)
    launch_window_days: int = 7
    target_sell_through: float = 0.80
    created_at: str = ""
