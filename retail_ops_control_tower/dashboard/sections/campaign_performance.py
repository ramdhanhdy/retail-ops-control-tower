"""Dashboard section: Campaign Performance."""

from __future__ import annotations

from typing import Any


def render(data: dict[str, Any], fmt: str = "text") -> str:
    """Render the campaign performance section."""
    line = "Section: Campaign Performance"
    if fmt == "html":
        return f"<section><h2>{line}</h2></section>"
    return line + "\n"
