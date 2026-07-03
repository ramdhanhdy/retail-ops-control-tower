"""Data I/O layer.

Reads and writes both JSON and CSV files for all 8 tables. The sample data
generator (T08) writes CSV; earlier scaffolding used JSON. Both are supported.

The task spec names this output ``retail_ops_control_tower/io.py``. A flat
module file cannot coexist with this package directory (the package directory
takes precedence on import), so the I/O logic lives here as a package and the
public functions are re-exported from ``__init__``. ``from
retail_ops_control_tower.io import read_csv_table`` works exactly as it would
from a flat ``io.py``.
"""

from __future__ import annotations

from retail_ops_control_tower.io.csv_store import (
    read_all_csv_tables,
    read_csv_table,
    write_all_csv_tables,
    write_csv_table,
)
from retail_ops_control_tower.io.json_store import (
    TABLE_NAMES,
    read_all_tables,
    read_table,
    write_all_tables,
    write_table,
)
from retail_ops_control_tower.io.serializers import from_dict, to_dict

__all__ = [
    "TABLE_NAMES",
    "read_table",
    "write_table",
    "read_all_tables",
    "write_all_tables",
    "read_csv_table",
    "write_csv_table",
    "read_all_csv_tables",
    "write_all_csv_tables",
    "to_dict",
    "from_dict",
]
