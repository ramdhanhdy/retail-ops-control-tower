"""Dashboard section: SLA Aging."""

from __future__ import annotations

from typing import Any


def render(data: dict[str, Any], fmt: str = "text") -> str:
    """Render the sla aging section."""
    line = "Section: SLA Aging"
    if fmt == "html":
        return f"<section><h2>{line}</h2></section>"
    return line + "\n"
