"""Exception management orchestrator."""

from __future__ import annotations

from datetime import date
from typing import Any

from retail_ops_control_tower.exceptions.action_list import generate_action_list
from retail_ops_control_tower.exceptions.engine import ExceptionEngine


def run_exception_management(issues: list[Any] | dict[str, list[dict]], aging_date: date | None = None) -> list[Any]:
    """Score and prioritize exceptions for operational follow-up.

    If ``issues`` is the full table mapping, the implemented exception engine is
    executed first. If it is already a list, the list is sorted as action items.
    """
    if isinstance(issues, dict):
        engine = ExceptionEngine(issues, aging_date)
        engine.detect()
        return engine.build_action_list(top_n=0)
    return generate_action_list(list(issues), top_n=0)
