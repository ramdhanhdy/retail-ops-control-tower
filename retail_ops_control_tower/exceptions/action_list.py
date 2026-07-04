"""Daily action list generator."""

from __future__ import annotations

from typing import Any


def _get(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def generate_action_list(issues: list[Any], top_n: int = 20) -> list[Any]:
    """Return the top action items sorted by priority, age, and ID."""
    ordered = sorted(
        issues,
        key=lambda item: (
            -int(_get(item, "priority_score", 0) or 0),
            -int(_get(item, "age_days", 0) or 0),
            str(_get(item, "exception_id", _get(item, "issue_id", ""))),
        ),
    )
    return ordered[:top_n] if top_n and top_n > 0 else ordered
