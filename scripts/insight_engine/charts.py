"""Matplotlib chart helpers with Indonesian labeling conventions.

All charts are saved as static PNG files under ``images/`` so they can be
embedded in the markdown story and displayed inline by a notebook wrapper.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from scripts.insight_engine.common import IMAGES_DIR, ensure_dirs

PALETTE = {
    "red": "#c0392b",
    "orange": "#e67e22",
    "blue": "#2e6da4",
    "green": "#27ae60",
    "gray": "#95a5a6",
    "dark": "#2c3e50",
}

plt.rcParams.update(
    {
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "figure.autolayout": True,
    }
)


def save_chart(fig: plt.Figure, name: str) -> Path:
    """Save a figure to images/<name>.png and close it."""
    ensure_dirs()
    path = IMAGES_DIR / f"{name}.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path
