"""Report orchestrator."""

from __future__ import annotations

import os
from datetime import date


def generate_reports(
    input_dir: str = "output",
    output_dir: str = "output/reports",
    section: str = "all",
    fmt: str = "text",
    aging_date: date | None = None,
) -> list[str]:
    """Generate reports. TODO: Phase 5/6.

    Returns list of generated report file paths.
    """
    if aging_date is None:
        aging_date = date.today()

    os.makedirs(output_dir, exist_ok=True)
    return []
