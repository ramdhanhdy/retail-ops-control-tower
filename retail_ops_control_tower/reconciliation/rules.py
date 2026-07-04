"""Exception rule adapter.

The detailed exception detection rules are implemented in
``retail_ops_control_tower.exceptions.engine``. This module exposes a compact
rule-evaluation API for callers that imported the earlier reconciliation layer.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from retail_ops_control_tower.exceptions.engine import detect_exceptions


def evaluate_rules(records: dict[str, list[dict[str, Any]]] | list[dict[str, Any]], aging_date: date | None = None) -> list[dict[str, Any]]:
    """Evaluate exception rules and return exception rows as dictionaries.

    Pass the full table mapping for complete detection. Passing a list returns
    an empty result because single-table input lacks the cross-table joins that
    operational exceptions require.
    """
    if not isinstance(records, dict):
        return []
    report = detect_exceptions(records, aging_date=aging_date)
    return [exception.to_dict() for exception in report.exceptions]
