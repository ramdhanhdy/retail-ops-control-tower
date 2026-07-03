"""AllocationPlan dataclass (13 fields).

Table: allocation_plan - per-store, per-SKU planned allocation line items.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AllocationPlan:
    """One row in the allocation_plan table."""

    allocation_id: str
    campaign_id: str
    store_id: str
    sku_id: str
    sku_name: str
    is_hero_sku: bool
    planned_quantity: int
    planned_unit_cost: float
    planned_retail_price: float
    allocation_date: str
    supplier_id: str
    supplier_lead_time_weeks: int
    region: str
