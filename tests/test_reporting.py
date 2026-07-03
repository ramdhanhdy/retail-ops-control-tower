"""Tests for the T12 weekly report generator.

Test coverage:

    - All 8 required report sections are present in the full report.
    - The executive summary contains the key section and action items.
    - Reports mention simulated data clearly.
    - The full report includes at least 10 action items.
    - No placeholder text (TODO, PLACEHOLDER, FIXME, etc.) appears.
    - Report content is data-driven (figures match the data tables).
    - Determinism: same input produces identical output.
    - Convenience functions (module-level entry points) produce
      identical output to the class-based generator.
    - Sample data integration: the generator works end-to-end on the
      real sample dataset.
"""

from __future__ import annotations

import os
from datetime import date

import pytest

from retail_ops_control_tower.io import read_all_csv_tables
from retail_ops_control_tower.reporting import (
    DEFAULT_AGING_DATE,
    PLACEHOLDER_STRINGS,
    REPORT_SECTIONS,
    SIMULATED_DATA_NOTICE,
    WeeklyReportGenerator,
    generate_executive_summary,
    generate_weekly_report,
)

AGING_DATE = date(2026, 7, 15)
WEEK_ENDING = date(2026, 7, 15)

SAMPLE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "sample",
)
REPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "reports",
)


# ---------------------------------------------------------------------------
# Fixture builders (minimal valid data for unit tests)
# ---------------------------------------------------------------------------

def _store(store_id="S-001", region="North", area_manager="AM Alpha", fmt="standard"):
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
    name="Test Campaign",
    start="2026-07-01",
    end="2026-07-28",
    hero="SKU-001",
    launch_window=7,
    target=0.70,
):
    return {
        "campaign_id": campaign_id,
        "campaign_name": name,
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
        "period_sell_through_target": target,
        "full_price_target": 0.80,
        "posm_list": "poster-A1",
    }


def _allocation(alloc_id="A-001", campaign_id="C-2026-TEST", store_id="S-001",
                sku="SKU-001", qty=100):
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


def _dispatch(ship_id="SH-001", alloc_id="A-001", campaign_id="C-2026-TEST",
              store_id="S-001", sku="SKU-001", shipped_qty=100,
              shipped_date="2026-06-25"):
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


def _confirmation(conf_id="CONF-001", alloc_id="A-001", ship_id="SH-001",
                   campaign_id="C-2026-TEST", store_id="S-001", sku="SKU-001",
                   received_qty=100, visit_date="2026-07-03",
                   received_date="2026-06-28"):
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


def _photo(photo_id="PH-001", conf_id="CONF-001", campaign_id="C-2026-TEST",
           store_id="S-001", photo_ts="2026-07-03T11:00:00-05:00"):
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


def _sales(sale_id="SALE-001", campaign_id="C-2026-TEST", store_id="S-001",
           sku="SKU-001", units_sold=50, on_hand=50):
    return {
        "sales_id": sale_id,
        "campaign_id": campaign_id,
        "store_id": store_id,
        "sku": sku,
        "sales_date": "2026-07-01",
        "day_of_campaign": 1,
        "units_sold": units_sold,
        "units_sold_full_price": units_sold,
        "units_sold_markdown": 0,
        "on_hand_quantity": on_hand,
        "on_order_quantity": 0,
        "in_transit_quantity": 0,
        "transfer_in_quantity": 0,
        "transfer_out_quantity": 0,
        "shrink_quantity": 0,
        "period_close_date": "2026-07-01",
    }


def _issue(issue_id="EX-001", exc_type="quantity_mismatch",
           campaign_id="C-2026-TEST", store_id="S-001", sku="SKU-001",
           alloc_id="A-001", conf_id="CONF-001", severity="watch",
           status="open", created="2026-07-01", due="2026-07-03"):
    return {
        "exception_id": issue_id,
        "exception_type": exc_type,
        "upstream_rule_code": "EX-05",
        "campaign_id": campaign_id,
        "store_id": store_id,
        "sku": sku,
        "allocation_id": alloc_id,
        "confirmation_id": conf_id,
        "severity": severity,
        "exception_status": status,
        "exception_owner": "DC Operations",
        "created_date": created,
        "due_date": due,
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
        "last_update_at": created,
        "last_update_type": "create",
        "corrective_action_id": "",
        "corrective_action_owner": "",
        "corrective_action_deadline": "",
        "corrective_action_status": "",
    }


def _build_minimal_tables():
    """Build a minimal but complete set of tables for unit testing."""
    store = _store()
    campaign = _campaign()
    alloc = _allocation()
    dispatch = _dispatch()
    conf = _confirmation()
    photo = _photo()
    sale = _sales()
    issue = _issue()
    return {
        "stores": [store],
        "campaigns": [campaign],
        "allocation_plan": [alloc],
        "dispatch": [dispatch],
        "store_confirmations": [conf],
        "photo_proofs": [photo],
        "sales_daily": [sale],
        "issues": [issue],
    }


# ---------------------------------------------------------------------------
# Tests: required report sections
# ---------------------------------------------------------------------------

class TestReportSections:
    """Verify all 8 required sections are present in the full report."""

    def setup_method(self):
        self.tables = _build_minimal_tables()
        self.generator = WeeklyReportGenerator(
            self.tables, aging_date=AGING_DATE, week_ending=WEEK_ENDING
        )
        self.report = self.generator.generate_full_report()

    def test_full_report_has_all_eight_sections(self):
        for section in REPORT_SECTIONS:
            assert section in self.report, (
                f"Missing required section: {section}"
            )

    def test_report_has_title(self):
        assert "# Weekly Operations Report" in self.report

    def test_section_count_matches_spec(self):
        assert len(REPORT_SECTIONS) == 8

    def test_executive_snapshot_has_kpi_table(self):
        assert "Process health:" in self.report
        assert "Campaign readiness rate" in self.report
        assert "Confirmation completion rate" in self.report

    def test_campaign_readiness_has_per_campaign_table(self):
        assert "Per-campaign breakdown:" in self.report
        assert "Summer Peach" not in self.report  # minimal data uses Test Campaign
        assert "Test Campaign" in self.report

    def test_allocation_reconciliation_has_findings(self):
        assert "Allocation Reconciliation" in self.report
        assert "VAL-04" in self.report
        assert "VAL-05" in self.report

    def test_exception_backlog_has_type_table(self):
        assert "Exceptions by type:" in self.report
        assert "SLA aging breakdown:" in self.report

    def test_am_followup_has_scorecard(self):
        assert "Area manager scorecard:" in self.report
        assert "AM Alpha" in self.report

    def test_sales_sellthrough_section(self):
        assert "Sell-through rate" in self.report
        assert "Per-campaign sell-through:" in self.report

    def test_recommended_actions_has_top_10(self):
        # The section header should mention top 10.
        assert "Top 10 action items" in self.report

    def test_data_caveats_section(self):
        assert "Data Caveats" in self.report
        assert "Validation findings:" in self.report
        assert "Tables covered:" in self.report


# ---------------------------------------------------------------------------
# Tests: simulated data notice
# ---------------------------------------------------------------------------

class TestSimulatedDataNotice:

    def setup_method(self):
        self.tables = _build_minimal_tables()
        self.generator = WeeklyReportGenerator(
            self.tables, aging_date=AGING_DATE, week_ending=WEEK_ENDING
        )

    def test_full_report_mentions_simulated(self):
        report = self.generator.generate_full_report()
        assert SIMULATED_DATA_NOTICE in report

    def test_executive_summary_mentions_simulated(self):
        summary = self.generator.generate_executive_summary()
        assert SIMULATED_DATA_NOTICE in summary

    def test_simulated_notice_explicit(self):
        report = self.generator.generate_full_report()
        assert "simulated" in report.lower()
        assert "synthetic" in report.lower()


# ---------------------------------------------------------------------------
# Tests: no placeholder text
# ---------------------------------------------------------------------------

class TestNoPlaceholders:

    def setup_method(self):
        self.tables = _build_minimal_tables()
        self.generator = WeeklyReportGenerator(
            self.tables, aging_date=AGING_DATE, week_ending=WEEK_ENDING
        )

    def test_full_report_has_no_placeholders(self):
        report = self.generator.generate_full_report()
        for placeholder in PLACEHOLDER_STRINGS:
            assert placeholder not in report, (
                f"Placeholder text found in report: {placeholder}"
            )

    def test_executive_summary_has_no_placeholders(self):
        summary = self.generator.generate_executive_summary()
        for placeholder in PLACEHOLDER_STRINGS:
            assert placeholder not in summary, (
                f"Placeholder text found in summary: {placeholder}"
            )


# ---------------------------------------------------------------------------
# Tests: action items
# ---------------------------------------------------------------------------

class TestActionItems:

    def setup_method(self):
        self.tables = _build_minimal_tables()
        self.generator = WeeklyReportGenerator(
            self.tables, aging_date=AGING_DATE, week_ending=WEEK_ENDING
        )

    def test_recommended_actions_table_present(self):
        report = self.generator.generate_full_report()
        assert "| # | Exception ID | Type | Severity |" in self.generator.generate_full_report()

    def test_executive_summary_has_top_5_actions(self):
        summary = self.generator.generate_executive_summary()
        assert "Key Actions This Week" in summary

    def test_strategic_recommendations_present(self):
        report = self.generator.generate_full_report()
        assert "Strategic recommendations:" in report


# ---------------------------------------------------------------------------
# Tests: data-driven content
# ---------------------------------------------------------------------------

class TestDataDriven:

    def setup_method(self):
        self.tables = _build_minimal_tables()
        self.generator = WeeklyReportGenerator(
            self.tables, aging_date=AGING_DATE, week_ending=WEEK_ENDING
        )

    def test_report_contains_store_count(self):
        report = self.generator.generate_full_report()
        assert "Stores: 1" in report

    def test_report_contains_campaign_count(self):
        report = self.generator.generate_full_report()
        assert "Campaigns: 1" in report

    def test_report_contains_allocation_count(self):
        report = self.generator.generate_full_report()
        assert "Allocation lines: 1" in report

    def test_report_contains_aging_date(self):
        report = self.generator.generate_full_report()
        assert "2026-07-15" in report

    def test_report_contains_am_name(self):
        report = self.generator.generate_full_report()
        assert "AM Alpha" in report

    def test_report_contains_campaign_name(self):
        report = self.generator.generate_full_report()
        assert "Test Campaign" in report

    def test_sell_through_percentage_present(self):
        report = self.generator.generate_full_report()
        # Sell-through should have a percentage sign.
        assert "%" in report
        assert "Sell-through rate" in report


# ---------------------------------------------------------------------------
# Tests: determinism
# ---------------------------------------------------------------------------

class TestDeterminism:

    def test_same_input_same_output_full_report(self):
        tables = _build_minimal_tables()
        gen1 = WeeklyReportGenerator(tables, AGING_DATE, WEEK_ENDING)
        gen2 = WeeklyReportGenerator(tables, AGING_DATE, WEEK_ENDING)
        assert gen1.generate_full_report() == gen2.generate_full_report()

    def test_same_input_same_output_summary(self):
        tables = _build_minimal_tables()
        gen1 = WeeklyReportGenerator(tables, AGING_DATE, WEEK_ENDING)
        gen2 = WeeklyReportGenerator(tables, AGING_DATE, WEEK_ENDING)
        assert gen1.generate_executive_summary() == gen2.generate_executive_summary()


# ---------------------------------------------------------------------------
# Tests: convenience functions
# ---------------------------------------------------------------------------

class TestConvenienceFunctions:

    def test_generate_weekly_report_matches_class(self):
        tables = _build_minimal_tables()
        gen = WeeklyReportGenerator(tables, AGING_DATE, WEEK_ENDING)
        assert generate_weekly_report(tables, AGING_DATE, WEEK_ENDING) == gen.generate_full_report()

    def test_generate_executive_summary_matches_class(self):
        tables = _build_minimal_tables()
        gen = WeeklyReportGenerator(tables, AGING_DATE, WEEK_ENDING)
        assert generate_executive_summary(tables, AGING_DATE, WEEK_ENDING) == gen.generate_executive_summary()

    def test_default_aging_date_is_used(self):
        tables = _build_minimal_tables()
        report = generate_weekly_report(tables)
        assert DEFAULT_AGING_DATE.isoformat() in report


# ---------------------------------------------------------------------------
# Tests: executive summary structure
# ---------------------------------------------------------------------------

class TestExecutiveSummary:

    def setup_method(self):
        self.tables = _build_minimal_tables()
        self.generator = WeeklyReportGenerator(
            self.tables, aging_date=AGING_DATE, week_ending=WEEK_ENDING
        )

    def test_has_title(self):
        summary = self.generator.generate_executive_summary()
        assert "# Executive Summary" in summary

    def test_has_executive_snapshot(self):
        summary = self.generator.generate_executive_summary()
        assert "## 1. Executive Snapshot" in summary

    def test_has_week_ending(self):
        summary = self.generator.generate_executive_summary()
        assert "Week ending" in summary

    def test_has_summary_assessment(self):
        summary = self.generator.generate_executive_summary()
        assert "Summary assessment:" in summary


# ---------------------------------------------------------------------------
# Tests: edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_empty_tables_produce_valid_report(self):
        tables = {
            "stores": [], "campaigns": [], "allocation_plan": [],
            "dispatch": [], "store_confirmations": [], "photo_proofs": [],
            "sales_daily": [], "issues": [],
        }
        generator = WeeklyReportGenerator(tables, AGING_DATE, WEEK_ENDING)
        report = generator.generate_full_report()
        # All sections should still be present.
        for section in REPORT_SECTIONS:
            assert section in report

    def test_no_placeholder_on_empty_data(self):
        tables = {
            "stores": [], "campaigns": [], "allocation_plan": [],
            "dispatch": [], "store_confirmations": [], "photo_proofs": [],
            "sales_daily": [], "issues": [],
        }
        generator = WeeklyReportGenerator(tables, AGING_DATE, WEEK_ENDING)
        report = generator.generate_full_report()
        for placeholder in PLACEHOLDER_STRINGS:
            assert placeholder not in report

    def test_custom_week_ending_appears(self):
        tables = _build_minimal_tables()
        custom_week = date(2026, 7, 21)
        gen = WeeklyReportGenerator(tables, AGING_DATE, custom_week)
        report = gen.generate_full_report()
        assert "2026-07-21" in report


# ---------------------------------------------------------------------------
# Tests: report context
# ---------------------------------------------------------------------------

class TestReportContext:

    def test_context_has_all_engines(self):
        tables = _build_minimal_tables()
        gen = WeeklyReportGenerator(tables, AGING_DATE, WEEK_ENDING)
        ctx = gen.context
        assert ctx.exception_report is not None
        assert ctx.metrics_summary is not None
        assert ctx.am_scorecard is not None
        assert ctx.validation_report is not None
        assert ctx.tables is tables

    def test_context_aging_date(self):
        tables = _build_minimal_tables()
        gen = WeeklyReportGenerator(tables, AGING_DATE, WEEK_ENDING)
        assert gen.context.aging_date == AGING_DATE

    def test_context_week_ending(self):
        tables = _build_minimal_tables()
        gen = WeeklyReportGenerator(tables, AGING_DATE, WEEK_ENDING)
        assert gen.context.week_ending == WEEK_ENDING


# ---------------------------------------------------------------------------
# Tests: sample data integration
# ---------------------------------------------------------------------------

class TestSampleDataIntegration:

    def _sample_tables(self):
        return read_all_csv_tables(SAMPLE_DIR)

    def test_sample_report_generates_without_error(self):
        gen = WeeklyReportGenerator(self._sample_tables(), AGING_DATE, WEEK_ENDING)
        report = gen.generate_full_report()
        assert len(report) > 5000  # Should be a substantial report.

    def test_sample_report_has_all_sections(self):
        gen = WeeklyReportGenerator(self._sample_tables(), AGING_DATE, WEEK_ENDING)
        report = gen.generate_full_report()
        for section in REPORT_SECTIONS:
            assert section in report

    def test_sample_report_has_100_stores(self):
        gen = WeeklyReportGenerator(self._sample_tables(), AGING_DATE, WEEK_ENDING)
        report = gen.generate_full_report()
        assert "Stores: 100" in report

    def test_sample_report_has_3_campaigns(self):
        gen = WeeklyReportGenerator(self._sample_tables(), AGING_DATE, WEEK_ENDING)
        report = gen.generate_full_report()
        assert "Campaigns: 3" in report

    def test_sample_report_has_10_ams(self):
        gen = WeeklyReportGenerator(self._sample_tables(), AGING_DATE, WEEK_ENDING)
        report = gen.generate_full_report()
        # 10 AMs in the scorecard.
        assert "Emma Wilson" in report
        assert "Sarah Chen" in report

    def test_sample_report_mentions_campaign_names(self):
        gen = WeeklyReportGenerator(self._sample_tables(), AGING_DATE, WEEK_ENDING)
        report = gen.generate_full_report()
        assert "Summer Peach LTO 2026" in report
        assert "Back to School Promo 2026" in report

    def test_sample_report_no_placeholders(self):
        gen = WeeklyReportGenerator(self._sample_tables(), AGING_DATE, WEEK_ENDING)
        report = gen.generate_full_report()
        for placeholder in PLACEHOLDER_STRINGS:
            assert placeholder not in report

    def test_sample_report_has_10_action_items(self):
        gen = WeeklyReportGenerator(self._sample_tables(), AGING_DATE, WEEK_ENDING)
        report = gen.generate_full_report()
        # Count rows in the action items table (rows start with "| N |").
        import re
        action_rows = re.findall(r"\| \d+ \| EXC-", report)
        assert len(action_rows) == 10

    def test_sample_executive_summary_has_actions(self):
        gen = WeeklyReportGenerator(self._sample_tables(), AGING_DATE, WEEK_ENDING)
        summary = gen.generate_executive_summary()
        assert "Key Actions This Week" in summary

    def test_sample_report_has_sell_through_below_target(self):
        gen = WeeklyReportGenerator(self._sample_tables(), AGING_DATE, WEEK_ENDING)
        report = gen.generate_full_report()
        assert "below the 70.0% target" in report


# ---------------------------------------------------------------------------
# Tests: generated report files exist
# ---------------------------------------------------------------------------

class TestReportFiles:
    """Verify the generated report files exist and are non-empty."""

    def test_weekly_ops_report_exists(self):
        path = os.path.join(REPORTS_DIR, "weekly_ops_report.md")
        assert os.path.exists(path), f"Report file not found: {path}"
        assert os.path.getsize(path) > 5000

    def test_executive_summary_exists(self):
        path = os.path.join(REPORTS_DIR, "executive_summary.md")
        assert os.path.exists(path), f"Summary file not found: {path}"
        assert os.path.getsize(path) > 1000

    def test_weekly_report_has_all_sections(self):
        path = os.path.join(REPORTS_DIR, "weekly_ops_report.md")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        for section in REPORT_SECTIONS:
            assert section in content, f"Missing section in file: {section}"

    def test_weekly_report_mentions_simulated(self):
        path = os.path.join(REPORTS_DIR, "weekly_ops_report.md")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert SIMULATED_DATA_NOTICE in content

    def test_weekly_report_no_placeholders(self):
        path = os.path.join(REPORTS_DIR, "weekly_ops_report.md")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        for placeholder in PLACEHOLDER_STRINGS:
            assert placeholder not in content

    def test_weekly_report_has_10_action_items(self):
        path = os.path.join(REPORTS_DIR, "weekly_ops_report.md")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        import re
        action_rows = re.findall(r"\| \d+ \| EXC-", content)
        assert len(action_rows) == 10
