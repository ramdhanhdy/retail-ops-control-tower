"""Tests for the T11 KPI metrics layer.

Each test constructs minimal fixture data (reusing the builder functions
from the T10 exception tests) and verifies that the metrics engine
correctly computes each KPI. Separate test classes cover:

    - All 12 individual KPIs (triggered / not-triggered pairs where
      applicable).
    - Division-by-zero and missing-data edge cases.
    - Process vs performance KPI separation.
    - Determinism (same input -> same output).
    - AM scorecard structure and sorting.
    - Sample data integration.
"""

from __future__ import annotations

import csv
import os
from datetime import date

import pytest

from retail_ops_control_tower.exceptions import ExceptionEngine
from retail_ops_control_tower.metrics import (
    ALL_KPIS,
    AMScorecardRow,
    KPI_META,
    KPIResult,
    MetricsEngine,
    MetricsSummary,
    PERFORMANCE_KPIS,
    PROCESS_KPIS,
    build_am_scorecard,
    compute_metrics,
)


AGING_DATE = date(2026, 7, 15)

SAMPLE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "sample",
)


# ---------------------------------------------------------------------------
# Fixture builders (mirror test_exceptions.py conventions)
# ---------------------------------------------------------------------------

def _store(store_id="S-001", region="North", area_manager="AM-1", fmt="standard"):
    return {
        "store_id": store_id,
        "store_name": "Test Store",
        "region": region,
        "store_format": fmt,
        "area_manager": area_manager,
        "field_rep": "REP-001",
        "selling_area_sqft": 1000,
        "city": "Testville",
        "state": "TS",
        "open_date": "2020-01-01",
        "is_active": True,
        "timezone": "America/Chicago",
    }


def _campaign(
    campaign_id="C-2026-TEST",
    start="2026-07-01",
    end="2026-07-28",
    hero="SKU-001",
    launch_window=7,
    sell_through_target=0.70,
):
    return {
        "campaign_id": campaign_id,
        "campaign_name": "Test Campaign",
        "campaign_type": "seasonal_lto",
        "campaign_start_date": start,
        "campaign_end_date": end,
        "campaign_status": "active",
        "hq_owner": "HQ Owner",
        "target_store_count": 10,
        "sku_list": "SKU-001;SKU-002",
        "hero_sku": hero,
        "launch_window_days": launch_window,
        "supplier_lead_time_weeks": 2,
        "period_sell_through_target": sell_through_target,
        "full_price_target": 0.80,
        "posm_list": "poster-A1",
    }


def _allocation(alloc_id="A-001", campaign_id="C-2026-TEST", store_id="S-001", sku="SKU-001", qty=100):
    return {
        "allocation_id": alloc_id,
        "campaign_id": campaign_id,
        "sku": sku,
        "store_id": store_id,
        "planned_quantity": qty,
        "planned_receipt_date": "2026-06-28",
        "allocation_phase": "initial",
        "allocation_method": "fair_share",
        "holdback_pct": 0.10,
        "planner_owner": "Planner",
    }


def _dispatch(
    ship_id="SH-001",
    alloc_id="A-001",
    campaign_id="C-2026-TEST",
    store_id="S-001",
    sku="SKU-001",
    shipped_qty=100,
    shipped_date="2026-06-25",
):
    return {
        "shipment_id": ship_id,
        "allocation_id": alloc_id,
        "campaign_id": campaign_id,
        "sku": sku,
        "store_id": store_id,
        "shipped_quantity": shipped_qty,
        "shipped_date": shipped_date,
        "expected_arrival_date": "2026-06-28",
        "carton_count": 4,
        "dc_id": "DC-01",
        "carrier": "FastFreight",
    }


def _confirmation(
    conf_id="CONF-001",
    alloc_id="A-001",
    ship_id="SH-001",
    campaign_id="C-2026-TEST",
    store_id="S-001",
    sku="SKU-001",
    received_qty=100,
    visit_date="2026-07-03",
    received_date="2026-06-28",
):
    return {
        "confirmation_id": conf_id,
        "allocation_id": alloc_id,
        "shipment_id": ship_id,
        "campaign_id": campaign_id,
        "store_id": store_id,
        "sku": sku,
        "received_quantity": received_qty,
        "received_date": received_date,
        "receipt_status": "accepted",
        "receiving_exception_type": "none",
        "receiving_owner": "Receiver",
        "visit_id": "V-001",
        "visit_date": visit_date,
        "visit_timestamp": f"{visit_date}T10:00:00-05:00",
        "visit_status": "completed",
        "gps_coordinates": "40.0,-90.0",
        "checklist_completion_pct": 0.95,
        "planogram_compliance": True,
        "pricing_accuracy": True,
        "on_shelf_availability_pct": 0.95,
        "training_completion_flag": True,
        "audit_level": "L1",
        "audit_status": "approved",
        "compliance_score": 90.0,
        "audit_comments": "",
        "exception_flag": False,
        "non_completion_reason": "",
        "campaign_store_status": "completed",
        "confirmation_timestamp": f"{visit_date}T10:30:00-05:00",
    }


def _photo(
    photo_id="PH-001",
    conf_id="CONF-001",
    campaign_id="C-2026-TEST",
    store_id="S-001",
    photo_ts="2026-07-03T11:00:00-05:00",
):
    return {
        "photo_id": photo_id,
        "confirmation_id": conf_id,
        "visit_id": "V-001",
        "store_id": store_id,
        "campaign_id": campaign_id,
        "photo_proof_url": f"photos/{photo_id}.jpg",
        "photo_timestamp": photo_ts,
        "photo_gps_coordinates": "40.0,-90.0",
        "photo_user_id": "REP-001",
        "photo_device_id": "TAB-001",
        "photo_type": "posm_deployment",
        "photo_validation_status": "passed",
        "photo_validation_reason": "",
    }


def _sale(
    campaign_id="C-2026-TEST",
    store_id="S-001",
    sku="SKU-001",
    sales_date="2026-07-01",
    day=1,
    units_sold=60,
    on_hand=40,
):
    return {
        "sales_id": f"SALE-{sales_date}-{store_id}-{sku}",
        "campaign_id": campaign_id,
        "store_id": store_id,
        "sku": sku,
        "sales_date": sales_date,
        "day_of_campaign": day,
        "units_sold": units_sold,
        "units_sold_full_price": units_sold,
        "units_sold_markdown": 0,
        "on_hand_quantity": on_hand,
        "on_order_quantity": 0,
        "in_transit_quantity": 0,
        "transfer_in_quantity": 0,
        "transfer_out_quantity": 0,
        "shrink_quantity": 0,
        "period_close_date": sales_date,
    }


def _issue(
    exception_id="EX-001",
    exc_type="quantity_mismatch",
    status="open",
    created_date="2026-07-01T08:00:00-05:00",
    due_date="2026-07-03T08:00:00-05:00",
    campaign_id="C-2026-TEST",
    store_id="S-001",
    sku="SKU-001",
):
    return {
        "exception_id": exception_id,
        "exception_type": exc_type,
        "upstream_rule_code": "EX-05",
        "campaign_id": campaign_id,
        "store_id": store_id,
        "sku": sku,
        "allocation_id": "A-001",
        "confirmation_id": "CONF-001",
        "severity": "watch",
        "exception_status": status,
        "exception_owner": "DC Operations",
        "created_date": created_date,
        "due_date": due_date,
        "resolved_date": "",
        "resolution_time_hours": "",
        "resolution_type": "",
        "resolution_text": "",
        "waiver_reason": "",
        "root_cause_category": "",
        "root_cause_subcategory": "",
        "parent_id": "",
        "reopen_count": 0,
        "sla_pause_reason": "",
        "sla_pause_started_at": "",
        "sla_pause_max_hours": "",
        "last_update_at": "",
        "last_update_type": "",
        "corrective_action_id": "",
        "corrective_action_owner": "",
        "corrective_action_deadline": "",
        "corrective_action_status": "",
    }


def _full_tables(**overrides):
    """Return a tables dict with one complete happy-path record set."""
    tables = {
        "stores": [_store()],
        "campaigns": [_campaign()],
        "allocation_plan": [_allocation()],
        "dispatch": [_dispatch()],
        "store_confirmations": [_confirmation()],
        "photo_proofs": [_photo()],
        "sales_daily": [_sale()],
        "issues": [],
    }
    tables.update(overrides)
    return tables


def _run_metrics(tables, aging_date=AGING_DATE):
    engine = MetricsEngine(tables, aging_date)
    return engine.compute()


# ---------------------------------------------------------------------------
# KPI registry tests
# ---------------------------------------------------------------------------

class TestKPIRegistry:
    def test_all_twelve_kpis_present(self):
        assert len(ALL_KPIS) == 12

    def test_process_kpis_count(self):
        assert len(PROCESS_KPIS) == 5

    def test_performance_kpis_count(self):
        assert len(PERFORMANCE_KPIS) == 7

    def test_process_and_performance_disjoint(self):
        assert set(PROCESS_KPIS).isdisjoint(set(PERFORMANCE_KPIS))

    def test_all_kpis_in_registry(self):
        for kpi in ALL_KPIS:
            assert kpi in KPI_META
            assert "category" in KPI_META[kpi]
            assert "unit" in KPI_META[kpi]
            assert "description" in KPI_META[kpi]

    def test_required_kpis_present(self):
        required = {
            "campaign_readiness_rate",
            "confirmation_completion_rate",
            "photo_proof_completion_rate",
            "allocation_accuracy_rate",
            "quantity_mismatch_rate",
            "exception_rate",
            "open_exception_count",
            "sla_breach_count",
            "sell_through_rate",
            "stockout_risk_count",
            "overstock_risk_count",
            "am_follow_up_backlog",
        }
        assert required == set(ALL_KPIS)


# ---------------------------------------------------------------------------
# Process KPI tests
# ---------------------------------------------------------------------------

class TestCampaignReadinessRate:
    def test_full_readiness(self):
        """Allocation with on-time confirmation + photo = 100% ready."""
        summary = _run_metrics(_full_tables())
        assert summary.get("campaign_readiness_rate") == 1.0

    def test_not_ready_when_no_confirmation(self):
        tables = _full_tables(store_confirmations=[])
        summary = _run_metrics(tables)
        assert summary.get("campaign_readiness_rate") == 0.0

    def test_not_ready_when_visit_after_launch_window(self):
        """Visit date after launch window deadline = not ready."""
        conf = _confirmation(visit_date="2026-07-20")
        tables = _full_tables(store_confirmations=[conf])
        summary = _run_metrics(tables)
        assert summary.get("campaign_readiness_rate") == 0.0

    def test_not_ready_when_no_photo(self):
        tables = _full_tables(photo_proofs=[])
        summary = _run_metrics(tables)
        assert summary.get("campaign_readiness_rate") == 0.0

    def test_partial_readiness(self):
        """One ready, one not ready = 50%."""
        tables = _full_tables(
            allocation_plan=[
                _allocation(alloc_id="A-001"),
                _allocation(alloc_id="A-002"),
            ],
            dispatch=[
                _dispatch(ship_id="SH-001", alloc_id="A-001"),
                _dispatch(ship_id="SH-002", alloc_id="A-002"),
            ],
            store_confirmations=[
                _confirmation(conf_id="CONF-001", alloc_id="A-001"),
                _confirmation(conf_id="CONF-002", alloc_id="A-002"),
            ],
            photo_proofs=[
                _photo(photo_id="PH-001", conf_id="CONF-001"),
            ],
        )
        summary = _run_metrics(tables)
        assert summary.get("campaign_readiness_rate") == 0.5


class TestConfirmationCompletionRate:
    def test_full_completion(self):
        summary = _run_metrics(_full_tables())
        assert summary.get("confirmation_completion_rate") == 1.0

    def test_no_completion(self):
        tables = _full_tables(store_confirmations=[])
        summary = _run_metrics(tables)
        assert summary.get("confirmation_completion_rate") == 0.0

    def test_partial_completion(self):
        tables = _full_tables(
            dispatch=[
                _dispatch(ship_id="SH-001", alloc_id="A-001"),
                _dispatch(ship_id="SH-002", alloc_id="A-002"),
            ],
            store_confirmations=[
                _confirmation(conf_id="CONF-001", alloc_id="A-001"),
            ],
        )
        summary = _run_metrics(tables)
        assert summary.get("confirmation_completion_rate") == 0.5


class TestPhotoProofCompletionRate:
    def test_full_completion(self):
        summary = _run_metrics(_full_tables())
        assert summary.get("photo_proof_completion_rate") == 1.0

    def test_no_photos(self):
        tables = _full_tables(photo_proofs=[])
        summary = _run_metrics(tables)
        assert summary.get("photo_proof_completion_rate") == 0.0

    def test_partial_completion(self):
        tables = _full_tables(
            store_confirmations=[
                _confirmation(conf_id="CONF-001", alloc_id="A-001"),
                _confirmation(conf_id="CONF-002", alloc_id="A-002"),
            ],
            photo_proofs=[
                _photo(photo_id="PH-001", conf_id="CONF-001"),
            ],
        )
        summary = _run_metrics(tables)
        assert summary.get("photo_proof_completion_rate") == 0.5


class TestAllocationAccuracyRate:
    def test_exact_match(self):
        summary = _run_metrics(_full_tables())
        assert summary.get("allocation_accuracy_rate") == 1.0

    def test_mismatch(self):
        conf = _confirmation(received_qty=90)
        tables = _full_tables(store_confirmations=[conf])
        summary = _run_metrics(tables)
        assert summary.get("allocation_accuracy_rate") == 0.0

    def test_partial_accuracy(self):
        tables = _full_tables(
            dispatch=[
                _dispatch(ship_id="SH-001", alloc_id="A-001"),
                _dispatch(ship_id="SH-002", alloc_id="A-002"),
            ],
            store_confirmations=[
                _confirmation(conf_id="CONF-001", alloc_id="A-001", received_qty=100),
                _confirmation(conf_id="CONF-002", alloc_id="A-002", received_qty=90),
            ],
        )
        summary = _run_metrics(tables)
        assert summary.get("allocation_accuracy_rate") == 0.5


class TestQuantityMismatchRate:
    def test_no_mismatch(self):
        summary = _run_metrics(_full_tables())
        assert summary.get("quantity_mismatch_rate") == 0.0

    def test_full_mismatch(self):
        conf = _confirmation(received_qty=90)
        tables = _full_tables(store_confirmations=[conf])
        summary = _run_metrics(tables)
        assert summary.get("quantity_mismatch_rate") == 1.0

    def test_accuracy_plus_mismatch_sum_to_one(self):
        """allocation_accuracy_rate + quantity_mismatch_rate == 1.0."""
        tables = _full_tables(
            dispatch=[
                _dispatch(ship_id="SH-001", alloc_id="A-001"),
                _dispatch(ship_id="SH-002", alloc_id="A-002"),
            ],
            store_confirmations=[
                _confirmation(conf_id="CONF-001", alloc_id="A-001", received_qty=100),
                _confirmation(conf_id="CONF-002", alloc_id="A-002", received_qty=90),
            ],
        )
        summary = _run_metrics(tables)
        acc = summary.get("allocation_accuracy_rate")
        mis = summary.get("quantity_mismatch_rate")
        assert abs((acc + mis) - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# Performance KPI tests
# ---------------------------------------------------------------------------

class TestExceptionRate:
    def test_with_exceptions(self):
        """Missing confirmation triggers an exception; rate = 1/1."""
        tables = _full_tables(store_confirmations=[])
        summary = _run_metrics(tables)
        assert summary.get("exception_rate") == 1.0

    def test_no_exceptions(self):
        summary = _run_metrics(_full_tables())
        assert summary.get("exception_rate") == 0.0


class TestOpenExceptionCount:
    def test_zero_when_no_exceptions(self):
        summary = _run_metrics(_full_tables())
        assert summary.get("open_exception_count") == 0.0

    def test_counts_active_exceptions(self):
        # Missing confirmation produces one open exception.
        tables = _full_tables(store_confirmations=[])
        summary = _run_metrics(tables)
        assert summary.get("open_exception_count") == 1.0


class TestSLABreachCount:
    def test_zero_when_no_breaches(self):
        summary = _run_metrics(_full_tables())
        assert summary.get("sla_breach_count") == 0.0

    def test_counts_breached(self):
        # Missing confirmation with old shipped_date -> SLA breached.
        ship = _dispatch(shipped_date="2026-06-01")
        tables = _full_tables(
            store_confirmations=[],
            dispatch=[ship],
        )
        summary = _run_metrics(tables)
        assert summary.get("sla_breach_count") >= 1.0


class TestSellThroughRate:
    def test_with_sales_and_received(self):
        # received=100, sold=60 -> 0.60
        summary = _run_metrics(_full_tables())
        assert abs(summary.get("sell_through_rate") - 0.60) < 1e-9

    def test_no_sales(self):
        tables = _full_tables(sales_daily=[])
        summary = _run_metrics(tables)
        assert summary.get("sell_through_rate") == 0.0


class TestStockoutRiskCount:
    def test_zero_when_no_stockout(self):
        summary = _run_metrics(_full_tables())
        assert summary.get("stockout_risk_count") == 0.0

    def test_counts_stockout(self):
        # on_hand=0 with prior sales triggers stockout_risk.
        sales = [
            _sale(sales_date="2026-07-01", units_sold=5, on_hand=95),
            _sale(sales_date="2026-07-02", units_sold=5, on_hand=0),
        ]
        tables = _full_tables(sales_daily=sales)
        summary = _run_metrics(tables)
        assert summary.get("stockout_risk_count") == 1.0


class TestOverstockRiskCount:
    def test_zero_when_no_overstock(self):
        summary = _run_metrics(_full_tables())
        assert summary.get("overstock_risk_count") == 0.0

    def test_counts_overstock(self):
        # Low sell-through with remaining on_hand triggers overstock.
        sales = [
            _sale(sales_date="2026-07-01", units_sold=1, on_hand=95),
            _sale(sales_date="2026-07-02", units_sold=1, on_hand=94),
        ]
        tables = _full_tables(sales_daily=sales)
        summary = _run_metrics(tables)
        assert summary.get("overstock_risk_count") == 1.0


class TestAMFollowUpBacklog:
    def test_zero_when_no_exceptions(self):
        summary = _run_metrics(_full_tables())
        assert summary.get("am_follow_up_backlog") == 0.0

    def test_counts_active_with_am(self):
        # Missing confirmation produces an open exception with area_manager.
        tables = _full_tables(store_confirmations=[])
        summary = _run_metrics(tables)
        assert summary.get("am_follow_up_backlog") == 1.0


# ---------------------------------------------------------------------------
# Division-by-zero and missing data edge cases
# ---------------------------------------------------------------------------

class TestDivisionByZero:
    def test_empty_tables_all_rates_zero(self):
        """All rate KPIs return 0.0 when there is no data."""
        tables = {
            "stores": [],
            "campaigns": [],
            "allocation_plan": [],
            "dispatch": [],
            "store_confirmations": [],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        summary = _run_metrics(tables)
        for kpi in PROCESS_KPIS:
            assert summary.get(kpi) == 0.0, f"{kpi} should be 0.0"
        assert summary.get("exception_rate") == 0.0
        assert summary.get("sell_through_rate") == 0.0

    def test_no_dispatches_confirmation_rate_zero(self):
        tables = _full_tables(dispatch=[])
        summary = _run_metrics(tables)
        assert summary.get("confirmation_completion_rate") == 0.0

    def test_no_confirmations_photo_rate_zero(self):
        tables = _full_tables(store_confirmations=[])
        summary = _run_metrics(tables)
        assert summary.get("photo_proof_completion_rate") == 0.0

    def test_no_received_quantity_sell_through_zero(self):
        tables = _full_tables(store_confirmations=[])
        summary = _run_metrics(tables)
        assert summary.get("sell_through_rate") == 0.0


class TestMissingData:
    def test_missing_campaign_excluded_from_readiness(self):
        """Allocation without a campaign is excluded from readiness."""
        alloc = _allocation(alloc_id="A-002", campaign_id="C-UNKNOWN")
        tables = _full_tables(allocation_plan=[_allocation(), alloc])
        # Only the known-campaign allocation counts.
        summary = _run_metrics(tables)
        assert summary.get("campaign_readiness_rate") == 1.0

    def test_missing_store_id_in_exception(self):
        """Exception with empty area_manager not counted in AM backlog."""
        store = _store(store_id="S-001", area_manager="")
        tables = _full_tables(
            stores=[store],
            store_confirmations=[],
        )
        summary = _run_metrics(tables)
        # Missing confirmation exception has no area_manager.
        assert summary.get("am_follow_up_backlog") == 0.0

    def test_none_quantity_values_handled(self):
        """None/empty quantity values are treated as 0, not crash."""
        conf = _confirmation()
        conf["received_quantity"] = ""
        conf["shipped_quantity"] = ""  # Not used directly but defensive.
        tables = _full_tables(store_confirmations=[conf])
        summary = _run_metrics(tables)
        # No valid quantity pairs -> accuracy/mismatch rates are 0.
        assert summary.get("allocation_accuracy_rate") == 0.0
        assert summary.get("quantity_mismatch_rate") == 0.0


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_input_same_output(self):
        tables = _full_tables(
            dispatch=[
                _dispatch(ship_id="SH-001", alloc_id="A-001"),
                _dispatch(ship_id="SH-002", alloc_id="A-002"),
            ],
            store_confirmations=[
                _confirmation(conf_id="CONF-001", alloc_id="A-001"),
                _confirmation(conf_id="CONF-002", alloc_id="A-002", received_qty=90),
            ],
        )
        s1 = _run_metrics(tables)
        s2 = _run_metrics(tables)
        for kpi in ALL_KPIS:
            assert s1.get(kpi) == s2.get(kpi), f"{kpi} not deterministic"

    def test_all_kpis_present(self):
        summary = _run_metrics(_full_tables())
        for kpi in ALL_KPIS:
            assert kpi in summary.kpis, f"{kpi} missing from summary"


# ---------------------------------------------------------------------------
# Summary structure
# ---------------------------------------------------------------------------

class TestMetricsSummary:
    def test_process_kpis_ordered(self):
        summary = _run_metrics(_full_tables())
        names = [k.name for k in summary.process_kpis]
        assert names == PROCESS_KPIS

    def test_performance_kpis_ordered(self):
        summary = _run_metrics(_full_tables())
        names = [k.name for k in summary.performance_kpis]
        assert names == PERFORMANCE_KPIS

    def test_get_returns_zero_for_unknown(self):
        summary = _run_metrics(_full_tables())
        assert summary.get("nonexistent_kpi") == 0.0

    def test_aging_date_set(self):
        summary = _run_metrics(_full_tables())
        assert summary.aging_date == AGING_DATE.isoformat()

    def test_to_rows_has_correct_keys(self):
        summary = _run_metrics(_full_tables())
        rows = summary.to_rows()
        assert len(rows) == 12
        for row in rows:
            assert "kpi_name" in row
            assert "category" in row
            assert "value" in row
            assert "unit" in row
            assert "description" in row


# ---------------------------------------------------------------------------
# AM scorecard
# ---------------------------------------------------------------------------

class TestAMScorecard:
    def test_returns_list_of_rows(self):
        tables = _full_tables()
        engine = MetricsEngine(tables, AGING_DATE)
        rows = engine.compute_am_scorecard()
        assert isinstance(rows, list)
        assert all(isinstance(r, AMScorecardRow) for r in rows)

    def test_one_am_in_simple_data(self):
        tables = _full_tables()
        engine = MetricsEngine(tables, AGING_DATE)
        rows = engine.compute_am_scorecard()
        assert len(rows) == 1
        assert rows[0].area_manager == "AM-1"

    def test_sorted_by_open_exceptions_desc(self):
        """Area managers with more open exceptions come first."""
        stores = [
            _store(store_id="S-001", area_manager="AM-A"),
            _store(store_id="S-002", area_manager="AM-B"),
        ]
        # AM-A: dispatch without confirmation -> 1 missing_confirmation.
        # AM-B: fully confirmed with photo, no exceptions.
        tables = _full_tables(
            stores=stores,
            allocation_plan=[
                _allocation(alloc_id="A-001", store_id="S-001"),
                _allocation(alloc_id="A-002", store_id="S-002"),
            ],
            dispatch=[
                _dispatch(ship_id="SH-001", alloc_id="A-001", store_id="S-001"),
                _dispatch(ship_id="SH-002", alloc_id="A-002", store_id="S-002"),
            ],
            store_confirmations=[
                # Confirm A-002 (AM-B), leave A-001 (AM-A) missing.
                _confirmation(conf_id="CONF-002", alloc_id="A-002", store_id="S-002"),
            ],
            photo_proofs=[
                _photo(photo_id="PH-002", conf_id="CONF-002", store_id="S-002"),
            ],
            sales_daily=[
                _sale(store_id="S-002", units_sold=60, on_hand=40),
            ],
        )
        engine = MetricsEngine(tables, AGING_DATE)
        rows = engine.compute_am_scorecard()
        assert rows[0].area_manager == "AM-A"
        assert rows[0].open_exception_count == 1
        assert rows[1].area_manager == "AM-B"
        assert rows[1].open_exception_count == 0

    def test_am_with_no_exceptions_still_listed(self):
        """An AM with stores but no exceptions appears with zero counts."""
        tables = _full_tables()
        engine = MetricsEngine(tables, AGING_DATE)
        rows = engine.compute_am_scorecard()
        assert len(rows) == 1
        assert rows[0].open_exception_count == 0


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

class TestConvenienceFunctions:
    def test_compute_metrics(self):
        summary = compute_metrics(_full_tables(), AGING_DATE)
        assert isinstance(summary, MetricsSummary)
        assert len(summary.kpis) == 12

    def test_build_am_scorecard(self):
        rows = build_am_scorecard(_full_tables(), AGING_DATE)
        assert isinstance(rows, list)


# ---------------------------------------------------------------------------
# Pre-computed exception report reuse
# ---------------------------------------------------------------------------

class TestExceptionReportReuse:
    def test_precomputed_report_used(self):
        """Engine uses the provided exception report instead of re-running."""
        tables = _full_tables(store_confirmations=[])
        report = ExceptionEngine(tables, AGING_DATE).detect()
        engine = MetricsEngine(tables, AGING_DATE, exception_report=report)
        summary = engine.compute()
        # Should match running without pre-computed report.
        summary2 = _run_metrics(tables)
        for kpi in ALL_KPIS:
            assert summary.get(kpi) == summary2.get(kpi)


# ---------------------------------------------------------------------------
# Sample data integration
# ---------------------------------------------------------------------------

class TestSampleDataIntegration:
    """Run the metrics engine against the full sample dataset."""

    def _compute_summary(self):
        from retail_ops_control_tower.io import read_all_csv_tables

        tables = read_all_csv_tables(SAMPLE_DIR)
        return compute_metrics(tables, AGING_DATE)

    def test_all_kpis_computed(self):
        summary = self._compute_summary()
        for kpi in ALL_KPIS:
            assert kpi in summary.kpis

    def test_rates_in_valid_range(self):
        summary = self._compute_summary()
        rate_kpis = [
            "campaign_readiness_rate",
            "confirmation_completion_rate",
            "photo_proof_completion_rate",
            "allocation_accuracy_rate",
            "quantity_mismatch_rate",
            "sell_through_rate",
        ]
        for kpi in rate_kpis:
            v = summary.get(kpi)
            assert 0.0 <= v <= 1.0, f"{kpi}={v} out of [0, 1]"

    def test_counts_non_negative(self):
        summary = self._compute_summary()
        count_kpis = [
            "open_exception_count",
            "sla_breach_count",
            "stockout_risk_count",
            "overstock_risk_count",
            "am_follow_up_backlog",
        ]
        for kpi in count_kpis:
            assert summary.get(kpi) >= 0.0

    def test_exception_rate_positive(self):
        summary = self._compute_summary()
        assert summary.get("exception_rate") > 0.0

    def test_sample_am_scorecard(self):
        from retail_ops_control_tower.io import read_all_csv_tables

        tables = read_all_csv_tables(SAMPLE_DIR)
        rows = build_am_scorecard(tables, AGING_DATE)
        assert len(rows) > 0
        for row in rows:
            assert row.area_manager != ""
            assert row.region != ""
            assert row.store_count > 0


# ---------------------------------------------------------------------------
# CSV output verification
# ---------------------------------------------------------------------------

class TestCSVOutput:
    def test_kpi_summary_csv_exists_and_valid(self):
        csv_path = os.path.join(
            os.path.dirname(SAMPLE_DIR), "processed", "kpi_summary.csv"
        )
        assert os.path.exists(csv_path), f"{csv_path} not found"
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 12
        names = {r["kpi_name"] for r in rows}
        assert names == set(ALL_KPIS)

    def test_am_scorecard_csv_exists_and_valid(self):
        csv_path = os.path.join(
            os.path.dirname(SAMPLE_DIR), "processed", "am_scorecard.csv"
        )
        assert os.path.exists(csv_path), f"{csv_path} not found"
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) > 0
        for row in rows:
            assert row["area_manager"] != ""
            assert "sell_through_rate" in row
            assert "exception_rate" in row
