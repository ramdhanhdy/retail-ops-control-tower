"""CSV file reader/writer for all 8 data tables.

The sample data generator (T08) writes all 8 tables as CSV files. This module
reads them back into Python dicts with type coercion applied where possible:
``int``-like fields become ``int``, ``float``-like fields become ``float``,
``True``/``False`` strings become ``bool``, and everything else stays a string.
Empty strings are normalized to ``""`` (the convention used by
``data_generation._format_value`` when writing).

The writer mirrors ``data_generation.write_csv_tables``: it writes the stored
columns defined in ``data_generation.TABLE_COLUMNS`` for each table, ignoring
extra keys.
"""

from __future__ import annotations

import csv
import os
from typing import Any

# Import lazily at call time to avoid a hard import cycle:
# data_generation imports nothing from io, but keeping the column definitions
# local avoids the package importing data_generation at module load.


def _load_table_columns() -> dict[str, list[str]]:
    """Return the stored column definitions from the data generation module."""
    from retail_ops_control_tower.data_generation import TABLE_COLUMNS

    return TABLE_COLUMNS


def _load_table_names() -> list[str]:
    """Return the ordered list of table names."""
    from retail_ops_control_tower.data_generation import TABLE_NAMES

    return list(TABLE_NAMES)


def _load_format_value():
    """Return the canonical _format_value from data_generation (single source)."""
    from retail_ops_control_tower.data_generation import _format_value

    return _format_value


def _coerce_value(raw: str) -> Any:
    """Coerce a raw CSV string into the most appropriate Python type.

    - ``""`` stays ``""`` (empty string, the generator's null convention).
    - ``"True"``/``"False"`` become ``bool``.
    - ``int``-like strings (optionally negative) become ``int``.
    - ``float``-like strings become ``float``.
    - Everything else stays ``str``.
    """
    if raw is None:
        return ""
    s = raw.strip() if isinstance(raw, str) else raw
    if s == "":
        return ""
    if s == "True":
        return True
    if s == "False":
        return False
    # int (do not accept things like "1.0" as int)
    try:
        if "." not in s and "e" not in s and "E" not in s:
            return int(s)
    except (ValueError, TypeError):
        pass
    # float
    try:
        return float(s)
    except (ValueError, TypeError):
        pass
    return s


def read_csv_table(path: str) -> list[dict[str, Any]]:
    """Read a CSV file into a list of coerced record dicts.

    Returns an empty list if the file does not exist. Uses the header row to
    determine columns; every row is read as a dict keyed by column name, with
    values coerced via :func:`_coerce_value`.
    """
    if not os.path.exists(path):
        return []
    rows: list[dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw_row in reader:
            rows.append({k: _coerce_value(v) for k, v in raw_row.items() if k is not None})
    return rows


def write_csv_table(
    table_name: str,
    records: list[dict[str, Any]],
    output_dir: str,
    columns: list[str] | None = None,
) -> str:
    """Write a table to a CSV file. Returns the file path.

    If ``columns`` is None, the stored columns for ``table_name`` are looked up
    from ``data_generation.TABLE_COLUMNS``.
    """
    if columns is None:
        all_columns = _load_table_columns()
        if table_name not in all_columns:
            raise KeyError(f"Unknown table '{table_name}'; provide columns explicitly")
        columns = all_columns[table_name]

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{table_name}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in records:
            writer.writerow({col: _format_value(row.get(col, "")) for col in columns})
    return path


def _format_value(value: Any) -> str:
    """Format a Python value for CSV output.

    Delegates to data_generation._format_value (the canonical implementation)
    to avoid duplicating the serialization logic.
    """
    return _load_format_value()(value)


def read_all_csv_tables(input_dir: str) -> dict[str, list[dict[str, Any]]]:
    """Read all 8 tables from CSV files in ``input_dir``.

    Missing files yield an empty list for that table.
    """
    table_names = _load_table_names()
    return {
        name: read_csv_table(os.path.join(input_dir, f"{name}.csv"))
        for name in table_names
    }


def write_all_csv_tables(
    tables: dict[str, list[dict[str, Any]]],
    output_dir: str,
) -> dict[str, str]:
    """Write all tables as CSV files. Returns a dict of table_name -> file_path."""
    table_names = _load_table_names()
    all_columns = _load_table_columns()
    return {
        name: write_csv_table(name, tables.get(name, []), output_dir, all_columns[name])
        for name in table_names
    }
