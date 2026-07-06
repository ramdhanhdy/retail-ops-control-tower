#!/usr/bin/env python3
"""Render the architecture diagram for the Retail Operations Control Tower.

Produces two outputs:
    docs/architecture.png   High-resolution PNG (>= 1600 px wide)
    docs/architecture.html   Standalone dark-themed HTML page

Usage:
    python scripts/render_architecture_diagram.py
    python scripts/render_architecture_diagram.py --output-dir docs

Requires matplotlib (included in the project venv).
The HTML output is fully self-contained with inline CSS, no external deps.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Allow running from repo root without install
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ─── Design tokens ──────────────────────────────────────────────────

BG = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
TEXT = "#e6edf3"
TEXT_DIM = "#8b949e"
ARROW_COLOR = "#484f58"

ACCENTS = [
    "#f0883e",  # 1 intake     - orange
    "#d29922",  # 2 normalize  - yellow
    "#3fb950",  # 3 validate   - green
    "#f85149",  # 4 prioritize - red
    "#58a6ff",  # 5 report     - blue
]

ACCENT_NAMES = [
    "#f0883e",
    "#d29922",
    "#3fb950",
    "#f85149",
    "#58a6ff",
]

# ─── Diagram content ───────────────────────────────────────────────

STAGES = [
    {
        "num": 1,
        "name": "Intake",
        "subtitle": "Raw Simulated Inputs",
        "lines": [
            "8 data tables (JSON)",
            "stores (40 rows)",
            "campaigns (2-3)",
            "allocation_plan (480)",
            "dispatch (480)",
            "store_confirmations (480)",
            "photo_proofs (~400)",
            "sales_daily (13,440)",
            "Deterministic, seed = 42",
        ],
    },
    {
        "num": 2,
        "name": "Normalize",
        "subtitle": "Data Validation",
        "lines": [
            "15 validation rules",
            "V-01 to V-15",
            "Uniqueness constraints",
            "Quantity range checks",
            "Date ordering checks",
            "Receiving tolerance (10%)",
            "Timestamp window checks",
            "Enum and status validation",
            "Abort on ValidationError",
        ],
    },
    {
        "num": 3,
        "name": "Validate",
        "subtitle": "Reconciliation Engine",
        "lines": [
            "16 formulas computed",
            "24 exception rules",
            "EX-01 to EX-24",
            "4-quantity variance tracking",
            "planned vs shipped",
            "shipped vs received",
            "received vs sold",
            "Source-of-truth tables",
            "27 computed fields enriched",
        ],
    },
    {
        "num": 4,
        "name": "Prioritize",
        "subtitle": "Exception Action Engine",
        "lines": [
            "8-category taxonomy",
            "3-tier severity scoring",
            "Priority score (1-200)",
            "SLA aging (4 buckets)",
            "Lifecycle state machine",
            "8 transitions enforced",
            "Action playbook",
            "Daily action list (top 20)",
        ],
    },
    {
        "num": 5,
        "name": "Report",
        "subtitle": "Metrics and Output",
        "lines": [
            "10 MVP KPIs",
            "Threshold color-coding",
            "6 dashboard sections",
            "7 weekly report types",
            "Streamlit dashboard app",
            "CLI: generate, build, report",
            "Demo: Summer Peach LTO 2026",
        ],
    },
]

TITLE = "Retail Operations Control Tower"
SUBTITLE_TEXT = "System Architecture - Simulated Campaign Execution Pipeline"
FOOTER = "All data is synthetic. No real company data claimed."


# ─── PNG renderer ──────────────────────────────────────────────────


def render_png(output_path: str) -> str:
    """Render the architecture diagram as a high-resolution PNG (>= 1600 px wide)."""
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        }
    )

    fig = plt.figure(figsize=(16, 9), dpi=150)
    fig.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # ─── Title ───────────────────────────────────────────────────
    ax.text(
        0.5,
        0.955,
        TITLE,
        fontsize=22,
        fontweight="bold",
        color=TEXT,
        ha="center",
        va="center",
    )
    ax.text(
        0.5,
        0.915,
        SUBTITLE_TEXT,
        fontsize=11,
        color=TEXT_DIM,
        ha="center",
        va="center",
    )

    # ─── Layout math ─────────────────────────────────────────────
    n = len(STAGES)
    col_w = 0.175
    margin = 0.025
    inter_gap = (1.0 - 2 * margin - n * col_w) / (n - 1)

    col_lefts = [margin + i * (col_w + inter_gap) for i in range(n)]

    box_top = 0.835
    box_bottom = 0.155
    box_height = box_top - box_bottom
    arrow_y = box_bottom + box_height * 0.55

    # ─── Stage boxes ─────────────────────────────────────────────
    for i, stage in enumerate(STAGES):
        x = col_lefts[i]
        x_right = x + col_w
        cx = x + col_w / 2
        accent = ACCENTS[i]

        # Main panel (rounded rectangle)
        box = FancyBboxPatch(
            (x, box_bottom),
            col_w,
            box_height,
            boxstyle="round,pad=0.006,rounding_size=0.010",
            facecolor=PANEL,
            edgecolor=BORDER,
            linewidth=1.2,
        )
        ax.add_patch(box)

        # Accent top strip (subtle colored header background)
        strip_h = 0.035
        strip = FancyBboxPatch(
            (x, box_top - strip_h),
            col_w,
            strip_h,
            boxstyle="round,pad=0.0,rounding_size=0.010",
            facecolor=accent,
            edgecolor="none",
            alpha=0.10,
        )
        ax.add_patch(strip)

        # Accent left edge (thin colored bar)
        edge_w = 0.004
        edge = FancyBboxPatch(
            (x, box_bottom),
            edge_w,
            box_height,
            boxstyle="square,pad=0.0",
            facecolor=accent,
            edgecolor="none",
            alpha=0.85,
        )
        ax.add_patch(edge)

        # Header (stage number + name in accent color)
        ax.text(
            cx,
            box_top - 0.022,
            f"{stage['num']}.  {stage['name'].upper()}",
            fontsize=12,
            fontweight="bold",
            color=accent,
            ha="center",
            va="center",
        )

        # Subtitle (italic, dim)
        ax.text(
            cx,
            box_top - 0.050,
            stage["subtitle"],
            fontsize=8,
            color=TEXT_DIM,
            ha="center",
            va="center",
            style="italic",
        )

        # Separator line (subtle)
        sep_y = box_top - 0.068
        ax.plot(
            [x + 0.012, x_right - 0.012],
            [sep_y, sep_y],
            color=BORDER,
            linewidth=0.6,
            alpha=0.5,
        )

        # Content lines
        line_y = sep_y - 0.032
        line_step = 0.036
        for line in stage["lines"]:
            ax.text(
                cx,
                line_y,
                line,
                fontsize=7.5,
                color=TEXT,
                ha="center",
                va="center",
            )
            line_y -= line_step

    # ─── Arrows between stages ──────────────────────────────────
    for i in range(n - 1):
        x_start = col_lefts[i] + col_w + 0.003
        x_end = col_lefts[i + 1] - 0.003
        arrow = FancyArrowPatch(
            (x_start, arrow_y),
            (x_end, arrow_y),
            arrowstyle="-|>",
            mutation_scale=16,
            color=ARROW_COLOR,
            linewidth=2.0,
        )
        ax.add_patch(arrow)

    # ─── Footer ──────────────────────────────────────────────────
    ax.text(
        0.5,
        0.012,
        FOOTER,
        fontsize=7,
        color=TEXT_DIM,
        ha="center",
        va="center",
        style="italic",
    )

    fig.savefig(
        output_path,
        dpi=150,
        facecolor=BG,
        bbox_inches="tight",
        pad_inches=0.15,
    )
    plt.close(fig)
    return output_path


# ─── HTML renderer ─────────────────────────────────────────────────


def _html_escape(text: str) -> str:
    """Escape basic HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_html(output_path: str) -> str:
    """Render the architecture diagram as a standalone HTML page."""

    stages_html: list[str] = []
    for i, stage in enumerate(STAGES):
        accent = ACCENT_NAMES[i]
        lines_html = "\n".join(
            f"            <li>{_html_escape(line)}</li>" for line in stage["lines"]
        )
        stage_block = f"""        <div class="stage" style="--accent:{accent}">
          <div class="stage-header">
            <div class="stage-num">Stage {stage['num']}</div>
            <div class="stage-name">{_html_escape(stage['name'])}</div>
            <div class="stage-subtitle">{_html_escape(stage['subtitle'])}</div>
          </div>
          <div class="stage-body">
            <ul>
{lines_html}
            </ul>
          </div>
        </div>"""
        stages_html.append(stage_block)

        if i < len(STAGES) - 1:
            stages_html.append('        <div class="arrow"><span>&#9654;</span></div>')

    pipeline_html = "\n".join(stages_html)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Retail Operations Control Tower - Architecture</title>
  <style>
    :root {{
      --bg: #0d1117;
      --panel: #161b22;
      --border: #30363d;
      --text: #e6edf3;
      --text-dim: #8b949e;
      --arrow: #484f58;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 48px 24px;
      min-height: 100vh;
    }}
    .container {{
      max-width: 1400px;
      margin: 0 auto;
    }}
    h1 {{
      text-align: center;
      font-size: 1.8rem;
      font-weight: 700;
      margin: 0 0 0.3rem 0;
      letter-spacing: -0.02em;
    }}
    .subtitle {{
      text-align: center;
      color: var(--text-dim);
      font-size: 0.95rem;
      margin: 0 0 2.5rem 0;
    }}
    .pipeline {{
      display: flex;
      align-items: stretch;
      gap: 0;
      margin-bottom: 2rem;
    }}
    .stage {{
      flex: 1;
      min-width: 0;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      border-left: 3px solid var(--accent);
    }}
    .stage-header {{
      padding: 0.75rem 1rem 0.6rem;
      border-bottom: 1px solid var(--border);
      background: color-mix(in srgb, var(--accent) 8%, transparent);
    }}
    .stage-num {{
      font-size: 0.7rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 0.15rem;
    }}
    .stage-name {{
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.02em;
    }}
    .stage-subtitle {{
      font-size: 0.82rem;
      color: var(--text-dim);
      font-style: italic;
      margin-top: 0.15rem;
    }}
    .stage-body {{
      padding: 0.75rem 1rem;
      flex: 1;
    }}
    .stage-body ul {{
      list-style: none;
      padding: 0;
      margin: 0;
    }}
    .stage-body li {{
      font-size: 0.80rem;
      padding: 0.28rem 0;
      color: var(--text);
      border-bottom: 1px solid rgba(48, 54, 61, 0.4);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .stage-body li:last-child {{
      border-bottom: none;
    }}
    .arrow {{
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0 0.4rem;
      color: var(--arrow);
      font-size: 1rem;
      flex-shrink: 0;
    }}
    .footer {{
      text-align: center;
      color: var(--text-dim);
      font-size: 0.72rem;
      margin-top: 1.5rem;
      font-style: italic;
    }}
    @media (max-width: 960px) {{
      .pipeline {{ flex-direction: column; }}
      .arrow {{ transform: rotate(90deg); padding: 0.3rem 0; }}
      .stage-body li {{ white-space: normal; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>{_html_escape(TITLE)}</h1>
    <p class="subtitle">{_html_escape(SUBTITLE_TEXT)}</p>
    <div class="pipeline">
{pipeline_html}
    </div>
    <p class="footer">{_html_escape(FOOTER)}</p>
  </div>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


# ─── CLI ────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the architecture diagram (PNG + HTML) for the Retail Ops Control Tower.",
    )
    parser.add_argument(
        "--output-dir",
        default="docs",
        help="Directory for output files (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    png_path = output_dir / "architecture.png"
    html_path = output_dir / "architecture.html"

    render_png(str(png_path))
    print(f"PNG written: {png_path}")

    render_html(str(html_path))
    print(f"HTML written: {html_path}")

    # Verify PNG dimensions
    try:
        from PIL import Image

        with Image.open(str(png_path)) as img:
            w, h = img.size
            print(f"PNG dimensions: {w} x {h} px")
            if w < 1600:
                print(f"WARNING: PNG width {w}px is below the 1600px minimum", file=sys.stderr)
    except Exception as exc:
        print(f"Could not verify PNG dimensions: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
