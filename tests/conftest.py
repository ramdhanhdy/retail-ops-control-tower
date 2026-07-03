"""Shared fixtures and data factories for the test suite."""

from __future__ import annotations

import sys
import os
from datetime import date

import pytest

# Ensure package is importable when running without install
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def seed() -> int:
    """Default deterministic seed for all tests."""
    return 42


@pytest.fixture
def today() -> date:
    """Fixed 'today' for aging tests."""
    return date(2026, 7, 15)


@pytest.fixture
def sample_store_data():
    """Minimal valid store record."""
    return {
        "store_id": "S001",
        "store_name": "Downtown Flagship",
        "region": "north",
        "area_manager": "AM-001",
        "format": "flagship",
        "city": "Seattle",
        "state": "WA",
        "sqft": 3000,
        "is_flagship": True,
        "is_hero": True,
        "open_date": "2020-01-15",
        "timezone": "America/Los_Angeles",
    }


@pytest.fixture
def sample_campaign_data():
    """Minimal valid campaign record."""
    return {
        "campaign_id": "summer-peach-lto-2026",
        "campaign_name": "Summer Peach LTO 2026",
        "campaign_type": "LTO",
        "start_date": "2026-07-01",
        "end_date": "2026-07-28",
        "status": "active",
        "hq_owner": "HQ-OPS-001",
        "region_scope": "all",
        "store_count": 40,
        "sku_count": 12,
        "sku_ids": [f"SKU-{i:03d}" for i in range(1, 13)],
        "hero_sku_ids": ["SKU-001", "SKU-002"],
        "launch_window_days": 7,
        "target_sell_through": 0.80,
        "created_at": "2026-06-15T09:00:00",
    }
