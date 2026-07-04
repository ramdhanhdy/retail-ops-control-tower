"""Failure-mode injection helpers.

The canonical sample generator already injects deterministic operational
failure modes. This helper is kept as a stable API for callers that want an
explicit hook before writing custom scenario data.
"""

from __future__ import annotations


def inject_failure_modes(tables: dict[str, list[dict]], seed: int = 42) -> dict[str, list[dict]]:
    """Return ``tables`` unchanged after the deterministic generation step.

    The function intentionally has no side effect. Custom experiments can wrap
    it to add more failure cases while preserving the default portfolio data.
    """
    return tables
