"""JSON file reader/writer for all 8 tables."""

from __future__ import annotations

import json
import os
from typing import Any

TABLE_NAMES = [
    "stores",
    "campaigns",
    "allocation_plan",
    "dispatch",
    "store_confirmations",
    "photo_proofs",
    "sales_daily",
    "issues",
]


def write_table(table_name: str, records: list[dict], output_dir: str) -> str:
    """Write a table to a JSON file. Returns the file path."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{table_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    return path


def read_table(table_name: str, input_dir: str) -> list[dict]:
    """Read a table from a JSON file. Returns empty list if file missing."""
    path = os.path.join(input_dir, f"{table_name}.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_all_tables(tables: dict[str, list], output_dir: str) -> dict[str, str]:
    """Write all tables. Returns a dict of table_name -> file_path."""
    return {
        name: write_table(name, records, output_dir)
        for name, records in tables.items()
    }


def read_all_tables(input_dir: str) -> dict[str, list]:
    """Read all tables. Returns a dict of table_name -> records."""
    return {name: read_table(name, input_dir) for name in TABLE_NAMES}
