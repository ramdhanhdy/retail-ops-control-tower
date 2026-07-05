# Fable 5 Task: Retail Ops Control Tower — Insight Engine Rebuild

## Context

You are working inside the **Retail Ops Control Tower** project — a Python
portfolio project that simulates a multi-store coffee chain running a seasonal
LTO campaign. The project tracks campaigns from HQ planning through store
execution, allocation reconciliation, and exception management. All data is
simulated. The repo is at `/opt/data/projects/retail-ops-control-tower/`.

The project has a complete pipeline: data generation (8 interlocking CSV
tables from a single seed), validation engine (9 data-quality rules),
exception engine (9 exception types with severity, priority, SLA, aging),
metrics layer (12 KPIs + area-manager scorecard), Streamlit dashboard, and
a weekly operations report. 327 tests pass.

An existing **"Insight Engine" notebook** (`notebooks/insight_engine_story_v2.ipynb`,
42 cells, ~1388 lines) was built by a kanban pipeline to tell the analytical
story across 4 layers:

1. **Concentration** — Pareto analysis, Gini coefficient + bootstrap CI
2. **Segmentation** — ANOVA with assumption checks, Tukey HSD, Kruskal-Wallis
3. **Attribution** — Chi-square with Cramér's V, Poisson tests, BH-FDR correction
4. **Opportunity** — Rebalancing gap analysis, SLA risk profile, financial impact

The notebook follows the Pyramid Principle: governing thought first, then
progressively deeper evidence. Each section goes
Observation → Statistical Evidence → Business Interpretation → Recommended Action.

## The Problem

The V2 notebook has **several mistakes** — statistical, structural, and data
issues. You will find and fix them yourself. We are not listing them all; that
would limit your scope. One visible symptom: some values that should be
meaningful come out as **zeros** in certain sections. That is one example, not
the full picture. Audit the existing notebook and the underlying data, find
what is wrong, and produce a corrected version.

## What to Build

Replace the monolithic notebook with a **token-efficient architecture**:

### 1. Python scripts (the analytical engine)

A set of Python scripts under `scripts/insight_engine/` that:

- Load data from `data/processed/` and `data/sample/`
- Run all analyses (concentration, segmentation, attribution, opportunity)
- Produce **chart images** (PNG) into an `images/` directory
- Export structured results (JSON or CSV) for each analytical layer
- Are importable and callable from a thin Jupyter notebook wrapper

The scripts should be modular: one module per analytical layer, a shared
data-loading module, and a main entry point that runs everything. Each
script should be runnable standalone (`python -m scripts.insight_engine.layer1_concentration`)
and produce its charts + data exports.

### 2. Markdown story (the narrative)

A **markdown file** (`docs/insight_engine_story.md`) that tells the full
analytical story in **Indonesian**, with embedded chart images referenced
from the `images/` directory via standard markdown image syntax:

```markdown
![Pareto curve and Gini coefficient](images/layer1_pareto_lorenz.png)
```

The story follows the same Pyramid Principle: governing thought first, then
four analytical layers, each with the structure:
Observation → Statistical Evidence → Business Interpretation → Recommended Action.

All prose, headings, labels, and interpretive text in **Indonesian**. Chart
titles and axis labels should also be in Indonesian where it makes sense
(they are produced by the scripts, so set the language there).

### 3. Thin Jupyter notebook (the wrapper, produced by a later agent)

You do NOT need to create the notebook. Another agent will produce it later.
Your job is to create the scripts and the markdown. The notebook will simply
import your scripts, call them, and display the charts inline alongside
the markdown narrative. Design your scripts so that a notebook can:

```python
from scripts.insight_engine import run_all
run_all()  # produces all charts + data exports
```

## Data Available

All data is in the repo at `/opt/data/projects/retail-ops-control-tower/data/`:

**Sample data** (`data/sample/`):
- `stores.csv` (100 rows) — store master: region, format, area manager, field rep
- `campaigns.csv` (3 rows) — campaign master: dates, SKUs, hero SKU, POSM, targets
- `allocation_plan.csv` (1410 rows) — per-store per-SKU planned quantities
- `dispatch.csv` (1410 rows) — shipment records: shipped qty, DC, carrier
- `store_confirmations.csv` (1366 rows) — receiving + visit records
- `photo_proofs.csv` (3091 rows) — photo metadata: GPS, timestamp, validation
- `sales_daily.csv` (39480 rows) — daily sales: units, on-hand, transfers, shrink
- `issues.csv` (123 rows) — pre-seeded exception and corrective action records

**Processed data** (`data/processed/`):
- `exceptions.csv` (1603 rows) — detected exceptions with severity, priority, SLA, aging
- `insights.csv` (14 rows) — ranked insights with impact scores and lift
- `kpi_summary.csv` (12 rows) — 12 KPI metrics with threshold colors
- `am_scorecard.csv` (10 rows) — area-manager scorecard
- `daily_action_list.csv` (1603 rows) — priority-ranked action list

## Existing Code to Reference

- `retail_ops_control_tower/insights.py` — the insight engine that generates `insights.csv`
- `retail_ops_control_tower/constants.py` — exception types, severity tiers, SLA windows
- `retail_ops_control_tower/metrics.py` — KPI computation
- `retail_ops_control_tower/reporting.py` — weekly report generation
- `scripts/build_notebook_v2.py` — the script that built the V2 notebook (reference for what the notebook does, not how to do it)

Read these to understand the data model, the exception taxonomy, and the
analytical framework. The existing notebook is at
`notebooks/insight_engine_story_v2.ipynb` — read it to understand the current
story structure and find the mistakes.

## Quality Bar

- All statistical tests must have assumption checks before they run
- All multiple-comparison scenarios must use correction (Bonferroni or BH-FDR)
- All effect sizes must be reported alongside p-values
- All confidence intervals must be computed with correct methods
- Charts must be saved as PNG files with readable titles, labels, and legends
- The markdown story must be self-contained — a reader can follow the full
  analytical narrative just by reading the markdown and viewing the charts
- The scripts must run without errors on the existing data
- No fabricated numbers — every statistic in the story must come from running
  the scripts against the actual data

## Definition of Done

1. `scripts/insight_engine/` contains modular Python scripts
2. `scripts/insight_engine/__init__.py` exposes a `run_all()` function
3. Running `python -m scripts.insight_engine.run_all` produces all charts in
   `images/` and all structured data in `data/insight_exports/`
4. `docs/insight_engine_story.md` tells the full story in Indonesian with
   embedded chart references
5. All mistakes from the V2 notebook are corrected — you identified them,
   you fixed them, and the numbers are now correct

## Discretion

You have full discretion over:
- Script architecture and module breakdown
- Statistical method choices (as long as they are defensible)
- Chart types and visual design
- How many scripts/modules to create
- File naming conventions
- Whether to use matplotlib, plotly, or seaborn for charts (but charts must
  be saved as static PNG files for markdown embedding)
- How to structure the Indonesian narrative
- What the "correct" version of each analysis looks like

The only constraints are the quality bar above and the output format
(scripts + markdown, not a notebook). Everything else is your call.

## Working Directory

```
/opt/data/projects/retail-ops-control-tower/
```

Start by reading the existing notebook and the data files. Find the problems.
Then build the replacement.
