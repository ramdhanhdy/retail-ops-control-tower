"""Tests for model dataclass construction."""

from __future__ import annotations


def test_store_construction():
    from retail_ops_control_tower.models.stores import Store
    s = Store(
        store_id="S001",
        store_name="Downtown",
        region="north",
        area_manager="AM-001",
        format="flagship",
        city="Seattle",
        state="WA",
        sqft=3000,
        is_flagship=True,
        is_hero=True,
        open_date="2020-01-15",
        timezone="America/Los_Angeles",
    )
    assert s.store_id == "S001"
    assert s.is_flagship is True


def test_campaign_construction():
    from retail_ops_control_tower.models.campaigns import Campaign
    c = Campaign(
        campaign_id="C001",
        campaign_name="Summer Peach",
        campaign_type="LTO",
        start_date="2026-07-01",
        end_date="2026-07-28",
        status="active",
        hq_owner="HQ-001",
        region_scope="all",
        store_count=40,
        sku_count=12,
        sku_ids=["SKU-001"],
        hero_sku_ids=["SKU-001"],
    )
    assert c.campaign_id == "C001"
    assert c.launch_window_days == 7


def test_allocation_plan_construction():
    from retail_ops_control_tower.models.allocation_plan import AllocationPlan
    a = AllocationPlan(
        allocation_id="A001",
        campaign_id="C001",
        store_id="S001",
        sku_id="SKU-001",
        sku_name="Peach Latte",
        is_hero_sku=True,
        planned_quantity=200,
        planned_unit_cost=2.50,
        planned_retail_price=5.95,
        allocation_date="2026-06-20",
        supplier_id="SUP-001",
        supplier_lead_time_weeks=2,
        region="north",
    )
    assert a.planned_quantity == 200


def test_dispatch_construction():
    from retail_ops_control_tower.models.dispatch import Dispatch
    d = Dispatch(
        dispatch_id="D001",
        allocation_id="A001",
        campaign_id="C001",
        store_id="S001",
        sku_id="SKU-001",
        dc_id="DC-001",
        shipped_quantity=190,
        shipped_date="2026-06-25",
        expected_delivery_date="2026-06-28",
        carrier="FastShip",
        tracking_number="TRK001",
        shipment_status="in_transit",
        shipped_unit_cost=2.50,
        region="north",
    )
    assert d.shipped_quantity == 190


def test_store_confirmation_construction():
    from retail_ops_control_tower.models.store_confirmations import StoreConfirmation
    sc = StoreConfirmation(
        confirmation_id="CF001",
        allocation_id="A001",
        campaign_id="C001",
        store_id="S001",
        sku_id="SKU-001",
        dispatch_id="D001",
        received_quantity=188,
        received_date="2026-06-28",
        visit_id="V001",
        visit_date="2026-06-28",
        visit_status="completed",
        visit_type="audit",
        field_rep_id="FR-001",
        setup_completed=True,
        setup_completion_date="2026-06-28",
        audit_level="L2",
        audit_score=95,
        audit_passed=True,
        posm_placed=True,
        planogram_compliance=True,
        pricing_accuracy=True,
        visit_start_time="2026-06-28T10:00:00",
        visit_end_time="2026-06-28T11:30:00",
        confirmation_posted_at="2026-06-28T12:00:00",
        confirmation_delay_hours=0.5,
        visit_duration_minutes=90,
        region="north",
        notes="",
    )
    assert sc.received_quantity == 188


def test_photo_proof_construction():
    from retail_ops_control_tower.models.photo_proofs import PhotoProof
    pp = PhotoProof(
        photo_id="P001",
        confirmation_id="CF001",
        visit_id="V001",
        store_id="S001",
        campaign_id="C001",
        photo_type="posm",
        photo_timestamp="2026-06-28T10:15:00",
        gps_lat=47.6062,
        gps_lon=-122.3321,
        user_id="FR-001",
        validation_status="pass",
        validation_notes="",
        file_ref="photos/P001.jpg",
    )
    assert pp.photo_id == "P001"


def test_sales_daily_construction():
    from retail_ops_control_tower.models.sales_daily import SalesDaily
    sd = SalesDaily(
        sales_id="SL001",
        campaign_id="C001",
        store_id="S001",
        sku_id="SKU-001",
        sales_date="2026-07-01",
        day_index=0,
        units_sold=10,
        units_received_today=188,
        on_hand_quantity=188,
        on_hand_eod=178,
        unit_retail_price=5.95,
        gross_sales=59.50,
        discount_amount=0.0,
        net_sales=59.50,
        sell_through_rate=0.053,
        woc_weeks=1.01,
        forward_woc_weeks=1.01,
        stockout_flag=False,
        overstock_flag=False,
        region="north",
        is_hero_sku=True,
        is_flagship_store=True,
        planned_quantity=200,
        cumulative_sold=10,
        cumulative_received=188,
    )
    assert sd.units_sold == 10


def test_issue_construction():
    from retail_ops_control_tower.models.issues import Issue
    i = Issue(
        issue_id="EX001",
        parent_id=None,
        reopen_count=0,
        campaign_id="C001",
        store_id="S001",
        sku_id="SKU-001",
        allocation_id="A001",
        dispatch_id="D001",
        confirmation_id=None,
        exception_type="quantity_mismatch",
        exception_rule_code="EX-01",
        root_cause_category="dc",
        root_cause_sub_category="short_pick",
        severity="watch",
        priority_score=265,
        business_impact="standard",
        status="open",
        raised_at="2026-07-01T08:00:00",
        last_updated_at="2026-07-01T08:00:00",
        resolved_at=None,
        resolution_time_hours=None,
        sla_deadline="2026-07-03T08:00:00",
        sla_status="within",
        aging_bucket=0,
        age_days=1,
        is_escalated=False,
        escalation_level="",
        owner="DC Operations",
        assignee="AM-001",
        next_action="Reconcile quantities",
        next_action_due="2026-07-02T08:00:00",
        planned_quantity=200,
        shipped_quantity=190,
        received_quantity=188,
        sold_quantity=None,
        variance_amount=-10.0,
        variance_pct=-5.0,
        description="Shipped quantity below planned by 5%",
        region="north",
    )
    assert i.issue_id == "EX001"
    assert i.priority_score == 265
