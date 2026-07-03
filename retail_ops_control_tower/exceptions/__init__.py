"""Exception management system.

Manages exception lifecycle, severity scoring, SLA aging, and action lists.

The T10 exception detection engine lives in ``engine.py`` within this
package. The public API is re-exported here so that
``from retail_ops_control_tower.exceptions import ExceptionEngine`` works
exactly as it would from a flat ``exceptions.py`` module.
"""

from __future__ import annotations

from retail_ops_control_tower.exceptions.engine import (
    EXCEPTION_TYPES,
    EXCEPTION_TYPE_META,
    ExceptionEngine,
    ExceptionRecord,
    ExceptionReport,
    detect_exceptions,
    build_action_list,
)

__all__ = [
    "EXCEPTION_TYPES",
    "EXCEPTION_TYPE_META",
    "ExceptionEngine",
    "ExceptionRecord",
    "ExceptionReport",
    "detect_exceptions",
    "build_action_list",
]
