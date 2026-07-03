"""SalesDaily dataclass (25 fields).

Table: sales_daily - daily sales and on-hand records.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SalesDaily:
    """One row in the sales_daily table."""

    sales_id: str
    campaign_id: str
    store_id: str
    sku_id: str
    sales_date: str
    day_index: int  # 0-based day within campaign
    units_sold: int
    units_received_today: int
    on_hand_quantity: int
    on_hand_eod: int
    unit_retail_price: float
    gross_sales: float
    discount_amount: float
    net_sales: float
    sell_through_rate: float
    woc_weeks: float
    forward_woc_weeks: float
    stockout_flag: bool
    overstock_flag: bool
    region: str
    is_hero_sku: bool
    is_flagship_store: bool
    planned_quantity: int
    cumulative_sold: int
    cumulative_received: int
