"""Store dataclass (12 fields).

Table: stores - store master with region, format, and attributes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Store:
    """One row in the stores table."""

    store_id: str
    store_name: str
    region: str
    area_manager: str
    format: str  # e.g. "flagship", "standard", "express", "kiosk"
    city: str
    state: str
    sqft: int
    is_flagship: bool
    is_hero: bool
    open_date: str  # ISO date string
    timezone: str
