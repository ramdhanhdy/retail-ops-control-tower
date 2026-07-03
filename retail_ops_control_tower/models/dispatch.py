"""Dispatch dataclass (14 fields).

Table: dispatch - shipment records with shipped quantities and dates.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Dispatch:
    """One row in the dispatch table."""

    dispatch_id: str
    allocation_id: str
    campaign_id: str
    store_id: str
    sku_id: str
    dc_id: str
    shipped_quantity: int
    shipped_date: str
    expected_delivery_date: str
    carrier: str
    tracking_number: str
    shipment_status: str
    shipped_unit_cost: float
    region: str
