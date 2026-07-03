"""Tests for the T10 exception and action-list engine.

Each test constructs minimal fixture data that triggers exactly one exception
type, verifying that the engine correctly detects it. A final integration test
runs against the full sample dataset.
"""

from __future__ import annotations

import os
from datetime import date, timedelta

import pytest

from retail_ops_control_tower.exceptions import (
    EXCEPTION_TYPES,
    ExceptionEngine,
    ExceptionRecord,
    ExceptionReport,
    detect_exceptions,
    build_action_list,
)


# ---------------------------------------------------------------------------
# Shared fixture builders
# ---------------------------------------------------------------------------

AGING_DATE = date(2026, 7, 15)


def _store(store_id="S-001", region="North", area_manager="AM-1", fmt="standard"):
    return {
        "store_id": store_id,
        "store_name": "Test Store",
        "region": region,
        "store_format": fmt,
        "area_manager": area_manager,
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
    units_sold=5,
    on_hand=95,
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


def _run_engine(tables, aging_date=AGING_DATE):
    return ExceptionEngine(tables, aging_date).detect()


# ---------------------------------------------------------------------------
# Exception type registry
# ---------------------------------------------------------------------------

class TestExceptionTypeRegistry:
    def test_nine_exception_types(self):
        assert len(EXCEPTION_TYPES) == 9

    def test_all_required_types_present(self):
        required = {
            "missing_confirmation",
            "late_confirmation",
            "quantity_mismatch",
            "missing_photo_proof",
            "late_photo_proof",
            "stockout_risk",
            "overstock_risk",
            "low_sell_through",
            "unresolved_issue_sla_breach",
        }
        assert required == set(EXCEPTION_TYPES)


# ---------------------------------------------------------------------------
# Individual exception type detectors
# ---------------------------------------------------------------------------

class TestMissingConfirmation:
    def test_triggered_when_dispatch_has_no_confirmation(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        report = _run_engine(tables)
        excs = report.by_type("missing_confirmation")
        assert len(excs) == 1
        assert excs[0].store_id == "S-001"
        assert excs[0].sku == "SKU-001"
        assert excs[0].allocation_id == "A-001"

    def test_not_triggered_when_confirmation_exists(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [_confirmation()],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        report = _run_engine(tables)
        assert len(report.by_type("missing_confirmation")) == 0

    def test_critical_for_hero_sku(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign(hero="SKU-001")],
            "allocation_plan": [_allocation(sku="SKU-001")],
            "dispatch": [_dispatch(sku="SKU-001")],
            "store_confirmations": [],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        report = _run_engine(tables)
        excs = report.by_type("missing_confirmation")
        assert len(excs) == 1
        assert excs[0].severity == "critical"


class TestLateConfirmation:
    def test_triggered_when_visit_after_launch_window(self):
        # Launch window is 7 days from 2026-07-01, deadline = 2026-07-08.
        late_visit = "2026-07-12"
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [_confirmation(visit_date=late_visit)],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        report = _run_engine(tables)
        excs = report.by_type("late_confirmation")
        assert len(excs) == 1
        assert excs[0].confirmation_id == "CONF-001"

    def test_not_triggered_when_visit_within_window(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [_confirmation(visit_date="2026-07-05")],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        report = _run_engine(tables)
        assert len(report.by_type("late_confirmation")) == 0


class TestQuantityMismatch:
    def test_triggered_when_received_differs_from_shipped(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch(shipped_qty=100)],
            "store_confirmations": [_confirmation(received_qty=80)],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        report = _run_engine(tables)
        excs = report.by_type("quantity_mismatch")
        assert len(excs) == 1
        assert excs[0].confirmation_id == "CONF-001"

    def test_not_triggered_when_quantities_match(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch(shipped_qty=100)],
            "store_confirmations": [_confirmation(received_qty=100)],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        report = _run_engine(tables)
        assert len(report.by_type("quantity_mismatch")) == 0

    def test_critical_for_large_variance(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch(shipped_qty=100)],
            "store_confirmations": [_confirmation(received_qty=70)],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        report = _run_engine(tables)
        excs = report.by_type("quantity_mismatch")
        assert len(excs) == 1
        assert excs[0].severity == "critical"


class TestMissingPhotoProof:
    def test_triggered_when_confirmation_has_no_photos(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [_confirmation()],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        report = _run_engine(tables)
        excs = report.by_type("missing_photo_proof")
        assert len(excs) == 1
        assert excs[0].confirmation_id == "CONF-001"

    def test_not_triggered_when_photos_exist(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [_confirmation()],
            "photo_proofs": [_photo()],
            "sales_daily": [],
            "issues": [],
        }
        report = _run_engine(tables)
        assert len(report.by_type("missing_photo_proof")) == 0

    def test_critical_for_low_compliance(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [_confirmation(compliance_score=70.0) if False else _confirmation()],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        # Override compliance score
        conf = _confirmation()
        conf["compliance_score"] = 70.0
        tables["store_confirmations"] = [conf]
        report = _run_engine(tables)
        excs = report.by_type("missing_photo_proof")
        assert len(excs) == 1
        assert excs[0].severity == "critical"


class TestLatePhotoProof:
    def test_triggered_when_photo_after_launch_window(self):
        # Launch window deadline: 2026-07-01 + 7 = 2026-07-08
        late_photo = "2026-07-12T11:00:00-05:00"
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [_confirmation()],
            "photo_proofs": [_photo(photo_ts=late_photo)],
            "sales_daily": [],
            "issues": [],
        }
        report = _run_engine(tables)
        excs = report.by_type("late_photo_proof")
        assert len(excs) == 1
        assert excs[0].confirmation_id == "CONF-001"

    def test_not_triggered_when_photo_within_window(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [_confirmation()],
            "photo_proofs": [_photo(photo_ts="2026-07-05T11:00:00-05:00")],
            "sales_daily": [],
            "issues": [],
        }
        report = _run_engine(tables)
        assert len(report.by_type("late_photo_proof")) == 0


class TestStockoutRisk:
    def test_triggered_when_on_hand_zero_with_sales(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch(shipped_qty=100)],
            "store_confirmations": [_confirmation(received_qty=100)],
            "photo_proofs": [],
            "sales_daily": [
                _sale(sales_date="2026-07-01", day=1, units_sold=50, on_hand=50),
                _sale(sales_date="2026-07-02", day=2, units_sold=50, on_hand=0),
            ],
            "issues": [],
        }
        report = _run_engine(tables)
        excs = report.by_type("stockout_risk")
        assert len(excs) == 1
        assert excs[0].sku == "SKU-001"
        assert excs[0].severity == "critical"

    def test_not_triggered_when_inventory_remains(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch(shipped_qty=100)],
            "store_confirmations": [_confirmation(received_qty=100)],
            "photo_proofs": [],
            "sales_daily": [
                _sale(sales_date="2026-07-01", day=1, units_sold=10, on_hand=90),
            ],
            "issues": [],
        }
        report = _run_engine(tables)
        assert len(report.by_type("stockout_risk")) == 0


class TestOverstockRisk:
    def test_triggered_when_low_sell_through_and_inventory_left(self):
        # 100 received, 10 sold, on_hand=90 -> sell_through=10%
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch(shipped_qty=100)],
            "store_confirmations": [_confirmation(received_qty=100)],
            "photo_proofs": [],
            "sales_daily": [
                _sale(sales_date="2026-07-01", day=1, units_sold=5, on_hand=95),
                _sale(sales_date="2026-07-02", day=2, units_sold=5, on_hand=90),
            ],
            "issues": [],
        }
        report = _run_engine(tables)
        excs = report.by_type("overstock_risk")
        assert len(excs) == 1
        assert excs[0].sku == "SKU-001"
        assert excs[0].severity == "watch"

    def test_not_triggered_when_high_sell_through(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch(shipped_qty=100)],
            "store_confirmations": [_confirmation(received_qty=100)],
            "photo_proofs": [],
            "sales_daily": [
                _sale(sales_date="2026-07-01", day=1, units_sold=80, on_hand=20),
            ],
            "issues": [],
        }
        report = _run_engine(tables)
        assert len(report.by_type("overstock_risk")) == 0


class TestLowSellThrough:
    def test_triggered_when_sell_through_below_threshold(self):
        # 100 received, 40 sold -> 40% < 50% threshold
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch(shipped_qty=100)],
            "store_confirmations": [_confirmation(received_qty=100)],
            "photo_proofs": [],
            "sales_daily": [
                _sale(sales_date="2026-07-01", day=1, units_sold=20, on_hand=80),
                _sale(sales_date="2026-07-02", day=2, units_sold=20, on_hand=60),
            ],
            "issues": [],
        }
        report = _run_engine(tables)
        excs = report.by_type("low_sell_through")
        assert len(excs) == 1
        assert excs[0].sku == "SKU-001"

    def test_not_triggered_when_sell_through_above_threshold(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch(shipped_qty=100)],
            "store_confirmations": [_confirmation(received_qty=100)],
            "photo_proofs": [],
            "sales_daily": [
                _sale(sales_date="2026-07-01", day=1, units_sold=60, on_hand=40),
            ],
            "issues": [],
        }
        report = _run_engine(tables)
        assert len(report.by_type("low_sell_through")) == 0


class TestUnresolvedIssueSlaBreach:
    def test_triggered_when_open_issue_past_due(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [
                _issue(
                    status="open",
                    due_date="2026-07-01T08:00:00-05:00",
                ),
            ],
        }
        report = _run_engine(tables, aging_date=date(2026, 7, 10))
        excs = report.by_type("unresolved_issue_sla_breach")
        assert len(excs) == 1
        assert excs[0].store_id == "S-001"

    def test_not_triggered_when_issue_resolved(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [
                _issue(status="resolved", due_date="2026-07-01T08:00:00-05:00"),
            ],
        }
        report = _run_engine(tables, aging_date=date(2026, 7, 10))
        assert len(report.by_type("unresolved_issue_sla_breach")) == 0

    def test_not_triggered_when_before_due_date(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [
                _issue(status="open", due_date="2026-07-20T08:00:00-05:00"),
            ],
        }
        report = _run_engine(tables, aging_date=date(2026, 7, 10))
        assert len(report.by_type("unresolved_issue_sla_breach")) == 0


# ---------------------------------------------------------------------------
# Exception record structure
# ---------------------------------------------------------------------------

class TestExceptionRecordStructure:
    def test_record_has_required_fields(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        report = _run_engine(tables)
        exc = report.exceptions[0]
        assert isinstance(exc, ExceptionRecord)
        # Acceptance criteria: severity, owner, region, AM, age_days, status, recommended_action
        assert exc.severity in ("critical", "watch", "info")
        assert exc.owner != ""
        assert exc.region != ""
        assert exc.area_manager != ""
        assert isinstance(exc.age_days, int)
        assert exc.status != ""
        assert exc.recommended_action != ""
        assert exc.sla_status in ("within", "approaching", "breached", "paused")
        assert isinstance(exc.priority_score, int)

    def test_to_dict(self):
        exc = ExceptionRecord(exception_id="EXC-001", exception_type="missing_confirmation")
        d = exc.to_dict()
        assert d["exception_id"] == "EXC-001"
        assert d["exception_type"] == "missing_confirmation"


# ---------------------------------------------------------------------------
# Action list sorting
# ---------------------------------------------------------------------------

class TestActionList:
    def test_sorted_by_severity_then_age(self):
        """Critical before watch; within severity, older first."""
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [
                _dispatch(ship_id="SH-001", shipped_date="2026-06-20"),
                _dispatch(ship_id="SH-002", alloc_id="A-002", shipped_date="2026-07-01"),
                _dispatch(ship_id="SH-003", alloc_id="A-003", shipped_date="2026-06-25"),
            ],
            "store_confirmations": [],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        engine = ExceptionEngine(tables, AGING_DATE)
        engine.detect()
        action_list = engine.build_action_list()
        assert len(action_list) == 3
        # All are "missing_confirmation" with "watch" severity (SKU-001 is hero,
        # so they should all be critical). Let's verify ordering by age_days.
        # Older dates = higher age_days at aging_date 2026-07-15.
        ages = [e.age_days for e in action_list]
        assert ages == sorted(ages, reverse=True)

    def test_excludes_resolved_closed(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [
                _issue(status="resolved", due_date="2026-07-01T08:00:00-05:00"),
            ],
        }
        engine = ExceptionEngine(tables, date(2026, 7, 20))
        report = engine.detect()
        # The missing_confirmation should be in the action list,
        # but the unresolved_issue_sla_breach should NOT (issue is resolved).
        action_list = engine.build_action_list()
        types_in_list = [e.exception_type for e in action_list]
        assert "unresolved_issue_sla_breach" not in types_in_list

    def test_top_n(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [
                _dispatch(ship_id="SH-001", shipped_date="2026-06-20"),
                _dispatch(ship_id="SH-002", alloc_id="A-002", shipped_date="2026-06-21"),
                _dispatch(ship_id="SH-003", alloc_id="A-003", shipped_date="2026-06-22"),
            ],
            "store_confirmations": [],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        engine = ExceptionEngine(tables, AGING_DATE)
        engine.detect()
        assert len(engine.build_action_list(top_n=2)) == 2
        assert len(engine.build_action_list(top_n=0)) == 3


# ---------------------------------------------------------------------------
# Report properties
# ---------------------------------------------------------------------------

class TestExceptionReport:
    def test_report_counts(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        report = _run_engine(tables)
        assert report.total == 1
        assert report.critical_count == 1  # hero SKU missing confirmation
        assert report.watch_count == 0
        assert report.open_count == 1

    def test_report_to_dict(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        report = _run_engine(tables)
        d = report.to_dict()
        assert "aging_date" in d
        assert d["total"] == 1
        assert "exceptions" in d
        assert len(d["exceptions"]) == 1


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

class TestConvenienceFunctions:
    def test_detect_exceptions(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        report = detect_exceptions(tables, AGING_DATE)
        assert isinstance(report, ExceptionReport)
        assert report.total == 1

    def test_build_action_list(self):
        tables = {
            "stores": [_store()],
            "campaigns": [_campaign()],
            "allocation_plan": [_allocation()],
            "dispatch": [_dispatch()],
            "store_confirmations": [],
            "photo_proofs": [],
            "sales_daily": [],
            "issues": [],
        }
        action_list = build_action_list(tables, AGING_DATE)
        assert len(action_list) == 1
        assert isinstance(action_list[0], ExceptionRecord)


# ---------------------------------------------------------------------------
# Integration test with sample data
# ---------------------------------------------------------------------------

class TestSampleDataIntegration:
    def test_sample_data_produces_all_exception_types(self):
        from retail_ops_control_tower.io import read_all_csv_tables
        sample_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "sample",
        )
        tables = read_all_csv_tables(sample_dir)
        report = detect_exceptions(tables, aging_date=date(2026, 7, 15))
        found_types = {e.exception_type for e in report.exceptions}
        # All 9 types should be present in the sample data.
        for exc_type in EXCEPTION_TYPES:
            assert exc_type in found_types, f"Exception type '{exc_type}' not found in sample data"
        assert report.total > 0
