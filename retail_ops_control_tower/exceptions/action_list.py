"""Daily action list generator."""

from __future__ import annotations


def generate_action_list(issues: list, top_n: int = 20) -> list:
    """Generate top-N action list sorted by priority DESC, age DESC, ID ASC. TODO: Phase 4."""
    return sorted(
        issues,
        key=lambda i: (
            -getattr(i, "priority_score", 0),
            -getattr(i, "age_days", 0),
            getattr(i, "issue_id", ""),
        ),
    )[:top_n]
