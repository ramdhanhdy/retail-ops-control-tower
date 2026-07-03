"""Seeded failure mode injector.

Injects 17 T01 + 20 T02 failure modes into generated data to create a
realistic exception landscape for the demo story.
"""

from __future__ import annotations


def inject_failure_modes(tables: dict, seed: int = 42) -> dict:
    """Inject seeded failure modes into generated tables. TODO: Phase 2."""
    return tables
