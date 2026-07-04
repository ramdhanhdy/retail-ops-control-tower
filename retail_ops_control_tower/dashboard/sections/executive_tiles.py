"""Dashboard section: Executive KPI Tiles."""

from __future__ import annotations

from typing import Any


def render(data: dict[str, Any], fmt: str = "text") -> str:
    """Render the executive kpi tiles section."""
    line = "Section: Executive KPI Tiles"
    if fmt == "html":
        return f"<section><h2>{line}</h2></section>"
    return line + "\n"
