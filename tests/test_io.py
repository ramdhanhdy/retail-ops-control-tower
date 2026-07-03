"""Tests for JSON and CSV I/O layers and serializers."""

from __future__ import annotations

import csv
import json
import os
import tempfile

from retail_ops_control_tower.io.json_store import (
    read_table, write_table, read_all_tables, write_all_tables, TABLE_NAMES,
)
from retail_ops_control_tower.io.serializers import to_dict, from_dict
from retail_ops_control_tower.io.csv_store import (
    read_csv_table,
    write_csv_table,
    read_all_csv_tables,
    write_all_csv_tables,
    _coerce_value,
    _format_value,
)


def test_table_names():
    assert len(TABLE_NAMES) == 8
    assert "stores" in TABLE_NAMES
    assert "issues" in TABLE_NAMES


def test_write_and_read_table():
    with tempfile.TemporaryDirectory() as tmpdir:
        records = [{"store_id": "S001"}, {"store_id": "S002"}]
        path = write_table("stores", records, tmpdir)
        assert os.path.exists(path)

        loaded = read_table("stores", tmpdir)
        assert loaded == records


def test_read_missing_table():
    with tempfile.TemporaryDirectory() as tmpdir:
        loaded = read_table("nonexistent", tmpdir)
        assert loaded == []


def test_write_and_read_all_tables():
    with tempfile.TemporaryDirectory() as tmpdir:
        tables = {name: [{"id": i}] for i, name in enumerate(TABLE_NAMES)}
        paths = write_all_tables(tables, tmpdir)
        assert len(paths) == 8

        loaded = read_all_tables(tmpdir)
        for name in TABLE_NAMES:
            assert name in loaded


def test_to_dict_with_dataclass():
    from retail_ops_control_tower.models.stores import Store
    s = Store(
        store_id="S001", store_name="Downtown", region="north",
        area_manager="AM-001", format="flagship", city="Seattle",
        state="WA", sqft=3000, is_flagship=True, is_hero=True,
        open_date="2020-01-15", timezone="PST",
    )
    d = to_dict(s)
    assert d["store_id"] == "S001"
    assert d["is_flagship"] is True


def test_from_dict_with_dataclass():
    from retail_ops_control_tower.models.stores import Store
    data = {
        "store_id": "S001", "store_name": "Downtown", "region": "north",
        "area_manager": "AM-001", "format": "flagship", "city": "Seattle",
        "state": "WA", "sqft": 3000, "is_flagship": True, "is_hero": True,
        "open_date": "2020-01-15", "timezone": "PST",
    }
    s = from_dict(Store, data)
    assert s.store_id == "S001"


# ---------------------------------------------------------------------------
# CSV store: type coercion
# ---------------------------------------------------------------------------

class TestCoerceValue:
    """The CSV reader coerces raw strings into the appropriate Python type."""

    def test_empty_string_stays_empty(self):
        assert _coerce_value("") == ""
        assert _coerce_value(None) == ""

    def test_true_false_becomes_bool(self):
        assert _coerce_value("True") is True
        assert _coerce_value("False") is False

    def test_integer_string_becomes_int(self):
        result = _coerce_value("42")
        assert result == 42
        assert isinstance(result, int)

    def test_negative_integer_becomes_int(self):
        result = _coerce_value("-5")
        assert result == -5
        assert isinstance(result, int)

    def test_float_string_becomes_float(self):
        result = _coerce_value("3.14")
        assert result == 3.14
        assert isinstance(result, float)

    def test_float_like_not_coerced_to_int(self):
        """A string like '1.0' should become float, not int."""
        result = _coerce_value("1.0")
        assert isinstance(result, float)
        assert result == 1.0

    def test_non_numeric_stays_string(self):
        result = _coerce_value("hello")
        assert result == "hello"
        assert isinstance(result, str)

    def test_whitespace_is_stripped(self):
        assert _coerce_value("  42  ") == 42
        assert _coerce_value("  True  ") is True


class TestFormatValue:
    """The CSV writer formats Python values back to strings."""

    def test_none_becomes_empty(self):
        assert _format_value(None) == ""

    def test_empty_string_stays_empty(self):
        assert _format_value("") == ""

    def test_bool_becomes_capitalized_string(self):
        assert _format_value(True) == "True"
        assert _format_value(False) == "False"

    def test_int_becomes_string(self):
        assert _format_value(42) == "42"
        assert _format_value(-5) == "-5"

    def test_float_becomes_string(self):
        assert _format_value(3.14) == "3.14"

    def test_string_unchanged(self):
        assert _format_value("hello") == "hello"


# ---------------------------------------------------------------------------
# CSV store: read / write round-trip
# ---------------------------------------------------------------------------

class TestCsvReadWrite:

    def test_write_and_read_csv_table(self, tmp_path):
        records = [
            {"store_id": "S001", "store_name": "Downtown", "region": "north"},
            {"store_id": "S002", "store_name": "Uptown", "region": "south"},
        ]
        path = write_csv_table("stores", records, str(tmp_path))
        assert os.path.exists(path)
        loaded = read_csv_table(path)
        assert len(loaded) == 2
        assert loaded[0]["store_id"] == "S001"
        assert loaded[1]["store_name"] == "Uptown"

    def test_read_missing_csv_returns_empty(self, tmp_path):
        assert read_csv_table(str(tmp_path / "nonexistent.csv")) == []

    def test_csv_round_trip_preserves_types(self, tmp_path):
        """int, float, bool, and str survive a write -> read cycle."""
        records = [
            {"store_id": "S001", "selling_area_sqft": 1000, "is_active": True, "name": "Downtown"},
        ]
        write_csv_table("stores", records, str(tmp_path), columns=list(records[0].keys()))
        loaded = read_csv_table(str(tmp_path / "stores.csv"))
        assert loaded[0]["store_id"] == "S001"
        assert loaded[0]["selling_area_sqft"] == 1000
        assert isinstance(loaded[0]["selling_area_sqft"], int)
        assert loaded[0]["is_active"] is True
        assert isinstance(loaded[0]["is_active"], bool)

    def test_write_with_explicit_columns(self, tmp_path):
        """When columns are provided, only those keys are written."""
        records = [{"a": 1, "b": 2, "c": 3}]
        path = write_csv_table("custom", records, str(tmp_path), columns=["a", "b"])
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == ["a", "b"]
            rows = list(reader)
        assert rows[0]["a"] == "1"
        assert "c" not in rows[0]

    def test_write_unknown_table_raises_without_columns(self, tmp_path):
        """Writing a table name not in TABLE_COLUMNS without explicit columns raises KeyError."""
        try:
            write_csv_table("nonexistent_table", [{"x": 1}], str(tmp_path))
            assert False, "Should have raised KeyError"
        except KeyError:
            pass

    def test_write_all_csv_tables_creates_eight_files(self, tmp_path):
        from retail_ops_control_tower.data_generation import TABLE_NAMES
        tables = {name: [{"_id": i}] for i, name in enumerate(TABLE_NAMES)}
        paths = write_all_csv_tables(tables, str(tmp_path))
        assert len(paths) == 8
        for name in TABLE_NAMES:
            assert os.path.exists(paths[name])

    def test_read_all_csv_tables_handles_missing_files(self, tmp_path):
        """Missing CSV files yield an empty list, not an error."""
        from retail_ops_control_tower.data_generation import TABLE_NAMES
        loaded = read_all_csv_tables(str(tmp_path))
        for name in TABLE_NAMES:
            assert name in loaded
            assert loaded[name] == []

    def test_round_trip_all_eight_tables(self, tmp_path):
        """Write all 8 tables from the generator, read them back, verify row counts match."""
        from retail_ops_control_tower.data_generation import (
            TABLE_NAMES,
            generate_sample_data,
        )
        tables = generate_sample_data(seed=42, output_dir=str(tmp_path / "gen"))
        write_all_csv_tables(tables, str(tmp_path / "rt"))
        loaded = read_all_csv_tables(str(tmp_path / "rt"))
        for name in TABLE_NAMES:
            assert len(loaded[name]) == len(tables[name]), (
                f"{name}: row count mismatch after round-trip"
            )
