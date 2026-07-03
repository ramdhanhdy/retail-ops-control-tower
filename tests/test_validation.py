"""Tests for the validation and reconciliation engine (T09).

Verifies:
    - Each of the 9 rules returns structured ValidationFinding records.
    - Each finding has severity, table, row_id, rule_code, message,
      and suggested_action.
    - Clean data produces zero findings.
    - The real sample dataset (data/sample/*.csv) validates without critical
      referential-integrity errors.
    - The CSV I/O round-trips with correct type coercion.
"""

from __future__ import annotations

import os
import copy

import pytest

from retail_ops_control_tower.io import (
    read_all_csv_tables,
    read_csv_table,
    write_csv_table,
)
from retail_ops_control_tower.validation import (
    PRIMARY_KEYS,
    REQUIRED_COLUMNS,
    NULLABLE_COLUMNS,
    ValidationEngine,
    ValidationFinding,
    ValidationReport,
    ValidationError,
    validate_positive,
    validate_non_negative,
    validate_tables,
)


# ---------------------------------------------------------------------------
# Minimal valid dataset factory
# ---------------------------------------------------------------------------

def _base_tables() -> dict[str, list[dict]]:
    """Return a minimal, internally consistent set of tables.

    Every FK resolves, every PK is unique, and planned == shipped == received,
    so validate_tables() returns zero findings on this dataset.
    """
    return {
        "stores": [
            {"store_id": "S-001", "store_name": "Central", "region": "North",
             "store_format": "standard", "area_manager": "AM-1", "field_rep": "",
             "selling_area_sqft": 1000, "city": "Madison", "state": "WI",
             "open_date": "2020-01-01", "is_active": True, "timezone": "America/Chicago"},
        ],
        "campaigns": [
            {"campaign_id": "C-1", "campaign_name": "Demo", "campaign_type": "seasonal_lto",
             "campaign_start_date": "2026-07-01", "campaign_end_date": "2026-07-28",
             "campaign_status": "active", "hq_owner": "HQ-1", "target_store_count": 1,
             "sku_list": "SKU-1;SKU-2", "hero_sku": "SKU-1", "launch_window_days": 7,
             "supplier_lead_time_weeks": 2, "period_sell_through_target": 0.70,
             "full_price_target": 0.80, "posm_list": "poster-A1"},
        ],
        "allocation_plan": [
            {"allocation_id": "A-1", "campaign_id": "C-1", "sku": "SKU-1",
             "store_id": "S-001", "planned_quantity": 100,
             "planned_receipt_date": "2026-06-28", "allocation_phase": "initial",
             "allocation_method": "fair_share", "holdback_pct": 0.10,
             "planner_owner": "P-1"},
        ],
        "dispatch": [
            {"shipment_id": "SH-1", "allocation_id": "A-1", "campaign_id": "C-1",
             "sku": "SKU-1", "store_id": "S-001", "shipped_quantity": 100,
             "shipped_date": "2026-06-26", "expected_arrival_date": "2026-06-28",
             "carton_count": 5, "dc_id": "DC-01", "carrier": "FastFreight"},
        ],
        "store_confirmations": [
            {"confirmation_id": "CONF-1", "allocation_id": "A-1", "shipment_id": "SH-1",
             "campaign_id": "C-1", "store_id": "S-001", "sku": "SKU-1",
             "received_quantity": 100, "received_date": "2026-06-28",
             "receipt_status": "accepted", "receiving_exception_type": "none",
             "receiving_owner": "R-1", "visit_id": "V-1", "visit_date": "2026-07-01",
             "visit_timestamp": "2026-07-01T09:00:00-05:00", "visit_status": "completed",
             "gps_coordinates": "40.0,-90.0", "checklist_completion_pct": 0.95,
             "planogram_compliance": True, "pricing_accuracy": True,
             "on_shelf_availability_pct": 0.95, "training_completion_flag": True,
             "audit_level": "L2", "audit_status": "approved", "compliance_score": 90.0,
             "audit_comments": "", "exception_flag": False, "non_completion_reason": "",
             "campaign_store_status": "completed", "confirmation_timestamp": "2026-07-01T10:00:00-05:00"},
        ],
        "photo_proofs": [
            {"photo_id": "PH-1", "confirmation_id": "CONF-1", "visit_id": "V-1",
             "store_id": "S-001", "campaign_id": "C-1", "photo_proof_url": "photos/PH-1.jpg",
             "photo_timestamp": "2026-07-01T09:10:00-05:00", "photo_gps_coordinates": "40.0,-90.0",
             "photo_user_id": "REP-1", "photo_device_id": "TAB-1", "photo_type": "posm_deployment",
             "photo_validation_status": "passed", "photo_validation_reason": ""},
        ],
        "sales_daily": [
            {"sales_id": "SALE-1", "campaign_id": "C-1", "store_id": "S-001",
             "sku": "SKU-1", "sales_date": "2026-07-01", "day_of_campaign": 1,
             "units_sold": 5, "units_sold_full_price": 4, "units_sold_markdown": 1,
             "on_hand_quantity": 95, "on_order_quantity": 0, "in_transit_quantity": 0,
             "transfer_in_quantity": 0, "transfer_out_quantity": 0,
             "shrink_quantity": 0, "period_close_date": "2026-07-01"},
        ],
        "issues": [
            {"exception_id": "EX-1", "exception_type": "quantity_mismatch",
             "upstream_rule_code": "EX-05", "campaign_id": "C-1", "store_id": "S-001",
             "sku": "SKU-1", "allocation_id": "A-1", "confirmation_id": "CONF-1",
             "severity": "watch", "exception_status": "open", "exception_owner": "DC Ops",
             "created_date": "2026-07-01T08:00:00-05:00", "due_date": "2026-07-03T08:00:00-05:00",
             "resolved_date": "", "resolution_time_hours": "", "resolution_type": "",
             "resolution_text": "", "waiver_reason": "", "root_cause_category": "",
             "root_cause_subcategory": "", "parent_id": "", "reopen_count": 0,
             "sla_pause_reason": "", "sla_pause_started_at": "", "sla_pause_max_hours": "",
             "last_update_at": "2026-07-01T09:00:00-05:00", "last_update_type": "comment",
             "corrective_action_id": "", "corrective_action_owner": "",
             "corrective_action_deadline": "", "corrective_action_status": ""},
        ],
    }


@pytest.fixture
def base_tables():
    """Deep copy of the minimal valid dataset so tests can mutate safely."""
    return copy.deepcopy(_base_tables())


def _findings_for(report, rule_code):
    return [f for f in report.findings if f.rule_code == rule_code]


# ---------------------------------------------------------------------------
# Finding structure
# ---------------------------------------------------------------------------

class TestFindingStructure:
    def test_finding_has_all_required_fields(self):
        f = ValidationFinding(
            severity="warning", table="dispatch", row_id="SH-1",
            rule_code="VAL-04", message="m", suggested_action="a",
        )
        assert f.severity == "warning"
        assert f.table == "dispatch"
        assert f.row_id == "SH-1"
        assert f.rule_code == "VAL-04"
        assert f.message == "m"
        assert f.suggested_action == "a"

    def test_finding_to_dict_roundtrip(self):
        f = ValidationFinding("critical", "stores", "S-1", "VAL-02", "m", "a")
        d = f.to_dict()
        assert set(d.keys()) == {"severity", "table", "row_id", "rule_code", "message", "suggested_action"}

    def test_report_counts(self):
        report = ValidationReport(findings=[
            ValidationFinding("critical", "stores", "S-1", "VAL-02", "m", "a"),
            ValidationFinding("warning", "stores", "S-2", "VAL-01", "m", "a"),
            ValidationFinding("info", "stores", "S-3", "VAL-01", "m", "a"),
        ])
        assert report.total == 3
        assert report.critical_count == 1
        assert report.warning_count == 1
        assert report.info_count == 1


# ---------------------------------------------------------------------------
# Clean data produces no findings
# ---------------------------------------------------------------------------

class TestCleanData:
    def test_clean_data_has_zero_findings(self, base_tables):
        report = validate_tables(base_tables)
        assert report.total == 0, [f.to_dict() for f in report.findings]

    def test_report_records_row_counts(self, base_tables):
        report = validate_tables(base_tables)
        assert report.table_row_counts["stores"] == 1
        assert report.table_row_counts["sales_daily"] == 1
        assert report.table_row_counts["issues"] == 1


# ---------------------------------------------------------------------------
# Rule 1: required column checks
# ---------------------------------------------------------------------------

class TestRequiredColumns:
    def test_missing_column_flagged(self, base_tables):
        del base_tables["stores"][0]["region"]
        report = validate_tables(base_tables)
        vals = _findings_for(report, "VAL-01")
        assert any(f.table == "stores" and "region" in f.message for f in vals)

    def test_empty_non_nullable_flagged(self, base_tables):
        base_tables["stores"][0]["store_name"] = ""
        report = validate_tables(base_tables)
        vals = _findings_for(report, "VAL-01")
        assert any("store_name" in f.message for f in vals)

    def test_nullable_empty_not_flagged(self, base_tables):
        # field_rep is nullable for stores; an empty value must NOT raise VAL-01.
        base_tables["stores"][0]["field_rep"] = ""
        report = validate_tables(base_tables)
        assert _findings_for(report, "VAL-01") == []


# ---------------------------------------------------------------------------
# Rule 2: duplicate key checks
# ---------------------------------------------------------------------------

class TestDuplicateKeys:
    def test_duplicate_pk_flagged(self, base_tables):
        dup = copy.deepcopy(base_tables["stores"][0])
        base_tables["stores"].append(dup)
        report = validate_tables(base_tables)
        vals = _findings_for(report, "VAL-02")
        assert len(vals) == 1
        assert vals[0].severity == "critical"
        assert vals[0].row_id == "S-001"


# ---------------------------------------------------------------------------
# Rule 3: foreign key checks
# ---------------------------------------------------------------------------

class TestForeignKeys:
    def test_unknown_campaign_fk_flagged(self, base_tables):
        base_tables["allocation_plan"][0]["campaign_id"] = "C-NONEXIST"
        report = validate_tables(base_tables)
        vals = _findings_for(report, "VAL-03")
        assert len(vals) == 1
        assert vals[0].severity == "critical"
        assert "campaign_id='C-NONEXIST'" in vals[0].message

    def test_unknown_store_fk_flagged(self, base_tables):
        base_tables["dispatch"][0]["store_id"] = "S-NONEXIST"
        report = validate_tables(base_tables)
        vals = _findings_for(report, "VAL-03")
        assert any("store_id='S-NONEXIST'" in f.message for f in vals)

    def test_visit_id_fk_uses_visit_id_not_confirmation_id(self, base_tables):
        """photo_proofs.visit_id must resolve against store_confirmations.visit_id,
        not against confirmation_id."""
        # Give the photo a visit_id that exists but a confirmation_id that does not.
        base_tables["photo_proofs"][0]["visit_id"] = "V-1"  # exists
        base_tables["photo_proofs"][0]["confirmation_id"] = "CONF-NONEXIST"  # missing
        report = validate_tables(base_tables)
        vals = _findings_for(report, "VAL-03")
        # Should flag the confirmation_id FK but NOT the visit_id FK.
        assert any("confirmation_id='CONF-NONEXIST'" in f.message for f in vals)
        assert not any("visit_id='V-1'" in f.message for f in vals)


# ---------------------------------------------------------------------------
# Rule 4: planned vs dispatched variance
# ---------------------------------------------------------------------------

class TestPlannedVsDispatched:
    def test_shipped_less_than_planned_flagged(self, base_tables):
        base_tables["dispatch"][0]["shipped_quantity"] = 90  # planned 100
        report = validate_tables(base_tables)
        vals = _findings_for(report, "VAL-04")
        assert len(vals) == 1
        assert "variance=-10" in vals[0].message
        assert vals[0].severity == "warning"

    def test_shipped_equals_planned_not_flagged(self, base_tables):
        report = validate_tables(base_tables)
        assert _findings_for(report, "VAL-04") == []


# ---------------------------------------------------------------------------
# Rule 5: planned vs received variance
# ---------------------------------------------------------------------------

class TestPlannedVsReceived:
    def test_received_less_than_planned_flagged(self, base_tables):
        base_tables["store_confirmations"][0]["received_quantity"] = 88  # planned 100
        report = validate_tables(base_tables)
        vals = _findings_for(report, "VAL-05")
        assert len(vals) == 1
        assert "variance=-12" in vals[0].message

    def test_received_overage_flagged(self, base_tables):
        base_tables["store_confirmations"][0]["received_quantity"] = 105
        report = validate_tables(base_tables)
        assert len(_findings_for(report, "VAL-05")) == 1


# ---------------------------------------------------------------------------
# Rule 6: dispatch without plan
# ---------------------------------------------------------------------------

class TestDispatchWithoutPlan:
    def test_dispatch_with_unknown_allocation_flagged(self, base_tables):
        base_tables["dispatch"][0]["allocation_id"] = "A-NONEXIST"
        report = validate_tables(base_tables)
        vals = _findings_for(report, "VAL-06")
        assert len(vals) == 1
        assert vals[0].severity == "critical"
        assert "A-NONEXIST" in vals[0].message


# ---------------------------------------------------------------------------
# Rule 7: confirmation without dispatch
# ---------------------------------------------------------------------------

class TestConfirmationWithoutDispatch:
    def test_confirmation_with_unknown_shipment_flagged(self, base_tables):
        base_tables["store_confirmations"][0]["shipment_id"] = "SH-NONEXIST"
        report = validate_tables(base_tables)
        vals = _findings_for(report, "VAL-07")
        assert len(vals) == 1
        assert "SH-NONEXIST" in vals[0].message

    def test_confirmation_with_unknown_allocation_flagged(self, base_tables):
        # Keep shipment valid so only the allocation branch fires.
        base_tables["store_confirmations"][0]["allocation_id"] = "A-NONEXIST"
        report = validate_tables(base_tables)
        vals = _findings_for(report, "VAL-07")
        assert any("A-NONEXIST" in f.message for f in vals)


# ---------------------------------------------------------------------------
# Rule 8: photo proof without confirmation
# ---------------------------------------------------------------------------

class TestPhotoWithoutConfirmation:
    def test_photo_with_unknown_confirmation_flagged(self, base_tables):
        base_tables["photo_proofs"][0]["confirmation_id"] = "CONF-NONEXIST"
        report = validate_tables(base_tables)
        vals = _findings_for(report, "VAL-08")
        assert len(vals) == 1
        assert vals[0].severity == "critical"
        assert "CONF-NONEXIST" in vals[0].message


# ---------------------------------------------------------------------------
# Rule 9: sales record without campaign/store match
# ---------------------------------------------------------------------------

class TestSalesWithoutMatch:
    def test_sales_unknown_campaign_flagged(self, base_tables):
        base_tables["sales_daily"][0]["campaign_id"] = "C-NONEXIST"
        report = validate_tables(base_tables)
        vals = _findings_for(report, "VAL-09")
        assert len(vals) == 1
        assert "campaign_id='C-NONEXIST'" in vals[0].message

    def test_sales_unknown_store_flagged(self, base_tables):
        base_tables["sales_daily"][0]["store_id"] = "S-NONEXIST"
        report = validate_tables(base_tables)
        vals = _findings_for(report, "VAL-09")
        assert any("store_id='S-NONEXIST'" in f.message for f in vals)

    def test_sales_unplanned_combo_flagged(self, base_tables):
        # All refs valid individually, but the (campaign, store, sku) tuple was
        # never allocated.
        base_tables["sales_daily"][0]["sku"] = "SKU-UNPLANNED"
        report = validate_tables(base_tables)
        vals = _findings_for(report, "VAL-09")
        assert len(vals) == 1
        assert "allocation_plan" in vals[0].message


# ---------------------------------------------------------------------------
# CSV I/O round-trip and type coercion
# ---------------------------------------------------------------------------

class TestCsvIO:
    def test_read_csv_coerces_types(self, tmp_path):
        write_csv_table("stores", _base_tables()["stores"], str(tmp_path))
        rows = read_csv_table(str(tmp_path / "stores.csv"))
        assert rows[0]["selling_area_sqft"] == 1000
        assert isinstance(rows[0]["selling_area_sqft"], int)
        assert rows[0]["is_active"] is True
        assert isinstance(rows[0]["is_active"], bool)
        assert rows[0]["store_id"] == "S-001"

    def test_read_missing_csv_returns_empty(self, tmp_path):
        assert read_csv_table(str(tmp_path / "nope.csv")) == []

    def test_roundtrip_preserves_data(self, tmp_path):
        tables = _base_tables()
        from retail_ops_control_tower.io import write_all_csv_tables
        paths = write_all_csv_tables(tables, str(tmp_path))
        assert len(paths) == 8
        loaded = read_all_csv_tables(str(tmp_path))
        assert loaded["stores"][0]["store_id"] == "S-001"
        assert loaded["dispatch"][0]["shipped_quantity"] == 100


# ---------------------------------------------------------------------------
# Real sample data integration
# ---------------------------------------------------------------------------

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample")


class TestSampleDataIntegration:
    def test_sample_data_has_no_critical_findings(self):
        """The sample dataset must have intact referential integrity:
        no duplicate keys, no orphan FKs, no dispatch without plan, no
        confirmation without dispatch, no photo without confirmation."""
        if not os.path.exists(SAMPLE_DIR):
            pytest.skip("sample data not generated yet")
        tables = read_all_csv_tables(SAMPLE_DIR)
        report = validate_tables(tables)
        assert report.critical_count == 0, [
            f.to_dict() for f in report.by_severity("critical")[:5]
        ]

    def test_sample_data_has_expected_variance_findings(self):
        """The generator deliberately short-ships and records quantity
        mismatches, so VAL-04 and VAL-05 warnings are expected."""
        if not os.path.exists(SAMPLE_DIR):
            pytest.skip("sample data not generated yet")
        tables = read_all_csv_tables(SAMPLE_DIR)
        report = validate_tables(tables)
        rule_codes = {f.rule_code for f in report.findings}
        assert "VAL-04" in rule_codes  # planned vs dispatched
        assert "VAL-05" in rule_codes  # planned vs received


# ---------------------------------------------------------------------------
# Backward-compatible generation-time guards
# ---------------------------------------------------------------------------

class TestGenerationGuards:
    def test_validate_positive_raises(self):
        with pytest.raises(ValidationError):
            validate_positive(0, "planned_quantity", "V-04")

    def test_validate_positive_passes(self):
        validate_positive(5, "planned_quantity", "V-04")  # no raise

    def test_validate_non_negative_raises(self):
        with pytest.raises(ValidationError):
            validate_non_negative(-1, "shipped_quantity", "V-05")

    def test_validate_non_negative_passes(self):
        validate_non_negative(0, "shipped_quantity", "V-05")  # no raise
