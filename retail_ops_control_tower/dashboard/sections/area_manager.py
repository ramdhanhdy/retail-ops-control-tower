"""Dashboard section: Area Manager Breakdown."""

from __future__ import annotations

from typing import Any


def render(data: dict[str, Any], fmt: str = "text") -> str:
    """Render the area manager breakdown section."""
    line = "Section: Area Manager Breakdown"
    if fmt == "html":
        return f"<section><h2>{line}</h2></section>"
    return line + "\n"
