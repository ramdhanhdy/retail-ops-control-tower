"""Tests for the sample data generator.

Verifies:
    - All 8 CSV files are created.
    - Each CSV has the required stored columns per the data dictionary.
    - Row counts are within expected ranges.
    - Primary keys are unique.
    - Foreign keys align (referential integrity).
    - Controlled exception cases are present (missing, mismatch, late).
    - Output is deterministic: same seed produces identical data.
    - Different seeds produce different data.
"""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

import pytest

from retail_ops_control_tower.data_generation import (
    EXCEPTION_DEFAULTS,
    TABLE_COLUMNS,
    TABLE_NAMES,
    SampleDataGenerator,
    generate_sample_data,
    write_csv_tables,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def generated_dir(tmp_path):
    """Generate sample data to a temporary directory and return the path."""
    tables = generate_sample_data(
        seed=42,
        output_dir=str(tmp_path),
        store_count=80,
        region_count=3,
        area_manager_count=8,
        campaign_count=2,
    )
    return tmp_path, tables


def _read_csv(path: Path) -> tuple[list[str], list[dict]]:
    """Read a CSV file, returning (headers, rows_as_dicts)."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames or []
    return headers, rows


# ---------------------------------------------------------------------------
# File existence and structure
# ---------------------------------------------------------------------------

class TestFileStructure:
    def test_all_csv_files_created(self, generated_dir):
        """All 8 CSV files must exist."""
        dir_path, _ = generated_dir
        for name in TABLE_NAMES:
            assert (dir_path / f"{name}.csv").exists(), f"{name}.csv missing"

    def test_all_csvs_have_required_columns(self, generated_dir):
        """Each CSV header must match TABLE_COLUMNS exactly."""
        dir_path, _ = generated_dir
        for name in TABLE_NAMES:
            headers, _ = _read_csv(dir_path / f"{name}.csv")
            expected = TABLE_COLUMNS[name]
            assert headers == expected, (
                f"{name}: headers {headers} != expected {expected}"
            )

    def test_all_csvs_have_at_least_one_data_row(self, generated_dir):
        """Every table must have at least one row."""
        dir_path, _ = generated_dir
        for name in TABLE_NAMES:
            _, rows = _read_csv(dir_path / f"{name}.csv")
            assert len(rows) > 0, f"{name}.csv has no data rows"


# ---------------------------------------------------------------------------
# Row count ranges
# ---------------------------------------------------------------------------

class TestRowCounts:
    def test_store_count_in_range(self, generated_dir):
        _, tables = generated_dir
        assert 80 <= len(tables["stores"]) <= 150

    def test_region_count_in_range(self, generated_dir):
        _, tables = generated_dir
        regions = {s["region"] for s in tables["stores"]}
        assert 3 <= len(regions) <= 5

    def test_area_manager_count_in_range(self, generated_dir):
        _, tables = generated_dir
        managers = {s["area_manager"] for s in tables["stores"]}
        assert 8 <= len(managers) <= 12

    def test_campaign_count_in_range(self, generated_dir):
        _, tables = generated_dir
        assert 2 <= len(tables["campaigns"]) <= 4

    def test_allocation_plan_has_rows(self, generated_dir):
        _, tables = generated_dir
        assert len(tables["allocation_plan"]) > 0

    def test_dispatch_has_rows(self, generated_dir):
        _, tables = generated_dir
        assert len(tables["dispatch"]) > 0

    def test_store_confirmations_has_rows(self, generated_dir):
        _, tables = generated_dir
        assert len(tables["store_confirmations"]) > 0

    def test_photo_proofs_has_rows(self, generated_dir):
        _, tables = generated_dir
        assert len(tables["photo_proofs"]) > 0

    def test_sales_daily_has_rows(self, generated_dir):
        _, tables = generated_dir
        assert len(tables["sales_daily"]) > 0

    def test_issues_has_rows(self, generated_dir):
        _, tables = generated_dir
        assert len(tables["issues"]) > 0


# ---------------------------------------------------------------------------
# Primary key uniqueness
# ---------------------------------------------------------------------------

class TestPrimaryKeys:
    PK_FIELDS = {
        "stores": "store_id",
        "campaigns": "campaign_id",
        "allocation_plan": "allocation_id",
        "dispatch": "shipment_id",
        "store_confirmations": "confirmation_id",
        "photo_proofs": "photo_id",
        "sales_daily": "sales_id",
        "issues": "exception_id",
    }

    @pytest.mark.parametrize("table_name,pk_field", list(PK_FIELDS.items()))
    def test_primary_key_unique(self, generated_dir, table_name, pk_field):
        dir_path, _ = generated_dir
        _, rows = _read_csv(dir_path / f"{table_name}.csv")
        values = [r[pk_field] for r in rows]
        assert len(values) == len(set(values)), (
            f"{table_name}: duplicate {pk_field} values found"
        )


# ---------------------------------------------------------------------------
# Referential integrity
# ---------------------------------------------------------------------------

class TestReferentialIntegrity:
    def test_allocation_fk_to_stores_and_campaigns(self, generated_dir):
        _, tables = generated_dir
        store_ids = {s["store_id"] for s in tables["stores"]}
        campaign_ids = {c["campaign_id"] for c in tables["campaigns"]}
        for alloc in tables["allocation_plan"]:
            assert alloc["store_id"] in store_ids
            assert alloc["campaign_id"] in campaign_ids

    def test_dispatch_fk_to_allocation(self, generated_dir):
        _, tables = generated_dir
        alloc_ids = {a["allocation_id"] for a in tables["allocation_plan"]}
        for ship in tables["dispatch"]:
            assert ship["allocation_id"] in alloc_ids

    def test_dispatch_fk_match_with_allocation(self, generated_dir):
        """Dispatch row must agree with its allocation on campaign, sku, store."""
        _, tables = generated_dir
        alloc_map = {a["allocation_id"]: a for a in tables["allocation_plan"]}
        for ship in tables["dispatch"]:
            alloc = alloc_map[ship["allocation_id"]]
            assert ship["campaign_id"] == alloc["campaign_id"]
            assert ship["store_id"] == alloc["store_id"]
            assert ship["sku"] == alloc["sku"]

    def test_confirmation_fk_to_dispatch_and_allocation(self, generated_dir):
        _, tables = generated_dir
        ship_ids = {s["shipment_id"] for s in tables["dispatch"]}
        alloc_ids = {a["allocation_id"] for a in tables["allocation_plan"]}
        store_ids = {s["store_id"] for s in tables["stores"]}
        campaign_ids = {c["campaign_id"] for c in tables["campaigns"]}
        for conf in tables["store_confirmations"]:
            assert conf["shipment_id"] in ship_ids
            assert conf["allocation_id"] in alloc_ids
            assert conf["store_id"] in store_ids
            assert conf["campaign_id"] in campaign_ids

    def test_photo_fk_to_confirmation(self, generated_dir):
        _, tables = generated_dir
        conf_ids = {c["confirmation_id"] for c in tables["store_confirmations"]}
        store_ids = {s["store_id"] for s in tables["stores"]}
        campaign_ids = {c["campaign_id"] for c in tables["campaigns"]}
        for photo in tables["photo_proofs"]:
            assert photo["confirmation_id"] in conf_ids
            assert photo["store_id"] in store_ids
            assert photo["campaign_id"] in campaign_ids

    def test_sales_fk_to_stores_and_campaigns(self, generated_dir):
        _, tables = generated_dir
        store_ids = {s["store_id"] for s in tables["stores"]}
        campaign_ids = {c["campaign_id"] for c in tables["campaigns"]}
        for sale in tables["sales_daily"]:
            assert sale["store_id"] in store_ids
            assert sale["campaign_id"] in campaign_ids

    def test_issues_fk_to_stores(self, generated_dir):
        _, tables = generated_dir
        store_ids = {s["store_id"] for s in tables["stores"]}
        for issue in tables["issues"]:
            assert issue["store_id"] in store_ids

    def test_issues_allocation_fk_when_present(self, generated_dir):
        """Non-empty allocation_id in issues must reference a real allocation."""
        _, tables = generated_dir
        alloc_ids = {a["allocation_id"] for a in tables["allocation_plan"]}
        for issue in tables["issues"]:
            if issue["allocation_id"]:
                assert issue["allocation_id"] in alloc_ids

    def test_issues_campaign_fk_when_present(self, generated_dir):
        """Non-empty campaign_id in issues must reference a real campaign."""
        _, tables = generated_dir
        campaign_ids = {c["campaign_id"] for c in tables["campaigns"]}
        for issue in tables["issues"]:
            if issue["campaign_id"]:
                assert issue["campaign_id"] in campaign_ids

    def test_issues_confirmation_fk_when_present(self, generated_dir):
        """Non-empty confirmation_id in issues must reference a real confirmation."""
        _, tables = generated_dir
        conf_ids = {c["confirmation_id"] for c in tables["store_confirmations"]}
        for issue in tables["issues"]:
            if issue["confirmation_id"]:
                assert issue["confirmation_id"] in conf_ids

    def test_issues_parent_id_when_present(self, generated_dir):
        """Non-empty parent_id must reference a real exception_id."""
        _, tables = generated_dir
        exc_ids = {i["exception_id"] for i in tables["issues"]}
        for issue in tables["issues"]:
            if issue["parent_id"]:
                assert issue["parent_id"] in exc_ids


# ---------------------------------------------------------------------------
# Controlled exception cases
# ---------------------------------------------------------------------------

class TestControlledExceptions:
    def test_some_confirmations_missing(self, generated_dir):
        """Not all dispatch records have a confirmation (missing_confirmation)."""
        _, tables = generated_dir
        ship_count = len(tables["dispatch"])
        conf_count = len(tables["store_confirmations"])
        assert conf_count < ship_count, (
            "Expected some dispatch records without confirmations"
        )

    def test_some_quantity_mismatches(self, generated_dir):
        """Some confirmations should have received != shipped (quantity_mismatch)."""
        _, tables = generated_dir
        ship_map = {s["shipment_id"]: s["shipped_quantity"] for s in tables["dispatch"]}
        mismatches = [
            c for c in tables["store_confirmations"]
            if c["received_quantity"] != ship_map.get(c["shipment_id"])
        ]
        assert len(mismatches) > 0, "Expected some quantity mismatches"

    def test_some_late_setups(self, generated_dir):
        """Some confirmations should have campaign_store_status != 'completed'."""
        _, tables = generated_dir
        late = [
            c for c in tables["store_confirmations"]
            if c["campaign_store_status"] != "completed"
        ]
        assert len(late) > 0, "Expected some late setups"

    def test_some_missing_photos(self, generated_dir):
        """Some confirmations should have no photo_proofs."""
        _, tables = generated_dir
        conf_ids = {c["confirmation_id"] for c in tables["store_confirmations"]}
        photo_conf_ids = {p["confirmation_id"] for p in tables["photo_proofs"]}
        missing = conf_ids - photo_conf_ids
        assert len(missing) > 0, "Expected some confirmations without photos"

    def test_some_photo_validation_failures(self, generated_dir):
        """Some photos should have validation_status 'failed'."""
        _, tables = generated_dir
        failed = [
            p for p in tables["photo_proofs"]
            if p["photo_validation_status"] == "failed"
        ]
        # This is probabilistic (~5%); with enough photos, at least one should fail
        if len(tables["photo_proofs"]) > 50:
            assert len(failed) > 0, "Expected some photo validation failures"

    def test_issues_contain_multiple_types(self, generated_dir):
        """The issues table should contain multiple exception types."""
        _, tables = generated_dir
        types = {i["exception_type"] for i in tables["issues"]}
        assert len(types) >= 3, (
            f"Expected at least 3 exception types, got {types}"
        )

    def test_issues_contain_open_and_resolved(self, generated_dir):
        """Issues should have a mix of open and resolved statuses."""
        _, tables = generated_dir
        statuses = {i["exception_status"] for i in tables["issues"]}
        assert len(statuses) >= 2, (
            f"Expected at least 2 exception statuses, got {statuses}"
        )

    def test_resolved_issues_have_resolution_fields(self, generated_dir):
        """Resolved issues should have resolution_type and resolution_text."""
        _, tables = generated_dir
        resolved = [
            i for i in tables["issues"]
            if i["exception_status"] in ("resolved", "closed")
        ]
        if resolved:
            for issue in resolved:
                assert issue["resolution_type"], (
                    f"Resolved issue {issue['exception_id']} missing resolution_type"
                )
                assert issue["resolution_text"], (
                    f"Resolved issue {issue['exception_id']} missing resolution_text"
                )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_seed_produces_identical_data(self):
        """Same seed must produce identical output."""
        t1 = generate_sample_data(seed=42, output_dir=tempfile.mkdtemp(), write_csv=False)
        t2 = generate_sample_data(seed=42, output_dir=tempfile.mkdtemp(), write_csv=False)
        assert t1 == t2, "Same seed produced different data"

    def test_different_seeds_produce_different_data(self):
        """Different seeds should produce different output."""
        t1 = generate_sample_data(seed=42, output_dir=tempfile.mkdtemp(), write_csv=False)
        t2 = generate_sample_data(seed=99, output_dir=tempfile.mkdtemp(), write_csv=False)
        # At least the stores table should differ (names, cities, etc.)
        assert t1["stores"] != t2["stores"], "Different seeds produced identical stores"

    def test_csv_round_trip_matches_in_memory(self, tmp_path):
        """CSV output should round-trip: written CSVs match in-memory data."""
        tables = generate_sample_data(seed=42, output_dir=str(tmp_path))
        for name in TABLE_NAMES:
            _, rows = _read_csv(tmp_path / f"{name}.csv")
            assert len(rows) == len(tables[name]), (
                f"{name}: CSV row count {len(rows)} != in-memory {len(tables[name])}"
            )


# ---------------------------------------------------------------------------
# Clamping behaviour
# ---------------------------------------------------------------------------

class TestClamping:
    def test_store_count_clamped_to_min(self, tmp_path):
        tables = generate_sample_data(
            seed=42, output_dir=str(tmp_path), store_count=50, write_csv=False
        )
        assert len(tables["stores"]) == 80

    def test_store_count_clamped_to_max(self, tmp_path):
        tables = generate_sample_data(
            seed=42, output_dir=str(tmp_path), store_count=500, write_csv=False
        )
        assert len(tables["stores"]) == 150

    def test_campaign_count_clamped(self, tmp_path):
        tables = generate_sample_data(
            seed=42, output_dir=str(tmp_path), campaign_count=10, write_csv=False
        )
        assert len(tables["campaigns"]) == 4


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------

class TestDataQuality:
    def test_stores_are_active(self, generated_dir):
        """Most stores should be active."""
        _, tables = generated_dir
        active = [s for s in tables["stores"] if s["is_active"] is True]
        assert len(active) > len(tables["stores"]) * 0.9

    def test_campaign_dates_ordered(self, generated_dir):
        """Campaign end date must be after start date."""
        _, tables = generated_dir
        for c in tables["campaigns"]:
            assert c["campaign_end_date"] > c["campaign_start_date"]

    def test_sales_dates_within_campaign_window(self, generated_dir):
        """All sales dates must fall within their campaign's window."""
        _, tables = generated_dir
        campaign_map = {c["campaign_id"]: c for c in tables["campaigns"]}
        for sale in tables["sales_daily"]:
            campaign = campaign_map[sale["campaign_id"]]
            assert campaign["campaign_start_date"] <= sale["sales_date"] <= campaign["campaign_end_date"], (
                f"Sales date {sale['sales_date']} outside campaign window"
            )

    def test_sales_day_of_campaign_starts_at_1(self, generated_dir):
        """day_of_campaign should start at 1 for each store-SKU."""
        _, tables = generated_dir
        first_days = [
            s for s in tables["sales_daily"]
            if s["day_of_campaign"] == 1
        ]
        assert len(first_days) > 0, "Expected some sales records with day_of_campaign=1"

    def test_received_quantity_non_negative(self, generated_dir):
        _, tables = generated_dir
        for c in tables["store_confirmations"]:
            assert c["received_quantity"] >= 0

    def test_exception_types_valid(self, generated_dir):
        """All exception_type values must be from the 8-type taxonomy."""
        _, tables = generated_dir
        valid_types = set(EXCEPTION_DEFAULTS.keys())
        for issue in tables["issues"]:
            assert issue["exception_type"] in valid_types, (
                f"Invalid exception_type: {issue['exception_type']}"
            )

    def test_severity_values_valid(self, generated_dir):
        _, tables = generated_dir
        valid_severities = {"critical", "watch", "info"}
        for issue in tables["issues"]:
            assert issue["severity"] in valid_severities, (
                f"Invalid severity: {issue['severity']}"
            )



