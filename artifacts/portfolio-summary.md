# Portfolio Summary: Retail Operations Control Tower

## Project

A Python control tower for multi-store retail campaign execution. It simulates a
coffee chain running a seasonal LTO campaign, validates the data, detects
exceptions, ranks them by priority, and renders a Streamlit dashboard plus a
weekly operations report.

All data is simulated. No real company data, internal knowledge, or real-world
retail operations experience is claimed.

---

## Positioning

Tech-forward data and workflow analyst. Not an operations specialist claim.

The project shows the ability to:

- Build a deterministic data simulation that produces realistic, interlocking
  operational data across 8 tables (100 stores, 3 campaigns, 39K daily sales
  rows).
- Implement a validation and reconciliation engine that enforces data integrity
  and computes planned-vs-actual variances across the four-quantity lifecycle
  (planned, shipped, received, sold).
- Design an exception management system with severity scoring, SLA tracking,
  aging buckets, and a priority-ranked action list.
- Compute a 12-KPI metrics layer with threshold color-coding and an area-manager
  scorecard.
- Render an interactive Streamlit dashboard and a structured 8-section weekly
  report.
- Write 327 passing tests covering models, validation, exceptions, metrics,
  reporting, I/O, CLI, and constants.

---

## What was built

### Data simulation (T08)

A deterministic generator produces 8 interlocking CSV tables from a single seed:

| Table | Rows | Purpose |
|-------|------|---------|
| stores | 100 | Store master: region, format, area manager, field rep |
| campaigns | 3 | Campaign master: dates, SKUs, hero SKU, POSM, targets |
| allocation_plan | 1,410 | Per-store per-SKU planned quantities |
| dispatch | 1,410 | Shipment records: shipped qty, DC, carrier |
| store_confirmations | 1,366 | Receiving + visit records, audit results, compliance |
| photo_proofs | 3,091 | Photo metadata: GPS, timestamp, validation status |
| sales_daily | 39,480 | Daily sales: units sold, on-hand, transfers, shrink |
| issues | 123 | Pre-seeded exception and corrective action records |

Controlled exception cases are injected deterministically: missing
confirmations (~4%), quantity mismatches (~12%), late setups (~6%), missing
photo proofs (~8%), and photo validation failures (~5%).

### Validation engine (T09)

9 data-quality and reconciliation rules:

1. Required column checks
2. Duplicate key checks
3. Foreign key checks
4. Planned vs dispatched variance
5. Planned vs received variance
6. Dispatch without plan
7. Confirmation without dispatch
8. Photo proof without confirmation
9. Sales record without campaign/store match

Each finding is a structured record with severity, table, row ID, rule code,
message, and suggested action.

### Exception engine (T10)

9 exception types detected automatically:

- missing_confirmation, late_confirmation, quantity_mismatch,
  missing_photo_proof, late_photo_proof, stockout_risk, overstock_risk,
  low_sell_through, unresolved_issue_sla_breach

Each exception gets:

- A severity tier (critical, watch, info)
- A priority score (severity weight x 100 + age pressure + business impact +
  campaign urgency)
- An SLA deadline and status (within, approaching, breached, paused)
- An aging bucket (fresh, aging, overdue, chronic)
- A recommended action from the playbook

The daily action list ranks exceptions by priority score, with the top items
surfaced for immediate attention.

### Metrics layer (T11)

12 KPIs in two categories:

- **Process (5):** campaign readiness rate, confirmation completion rate, photo
  proof completion rate, allocation accuracy rate, quantity mismatch rate.
- **Performance (7):** exception rate, open exception count, SLA breach count,
  sell-through rate, stockout risk count, overstock risk count, AM follow-up
  backlog.

Plus an area-manager scorecard with per-AM store counts, allocation counts,
open exceptions, critical count, SLA breaches, stockout/overstock risk, and
sell-through.

### Weekly report (T12)

An 8-section weekly operations report:

1. Executive snapshot
2. Campaign readiness
3. Allocation reconciliation
4. Exception backlog
5. AM / store follow-up list
6. Sales / sell-through note
7. Recommended actions (top 10 ranked)
8. Data caveats

Plus a short executive summary with the top 5 action items.

### Streamlit dashboard (T13)

An interactive dashboard with:

- KPI tiles (process and performance)
- Campaign readiness table
- Allocation reconciliation table
- Exception backlog with severity and SLA filters
- AM scorecard
- Sell-through analysis
- Full weekly report rendered inline

Filterable by campaign, region, and area manager.

### Architecture diagram (T14)

A dark-themed architecture diagram (PNG + interactive HTML) showing the
5-stage pipeline: intake > normalize > validate > prioritize > report.

### Testing

327 passing tests covering:

- Models (8 tables, field validation, type checking)
- Simulation (row counts, ranges, determinism with seed)
- Validation (9 rules, findings, report structure)
- Exception engine (9 types, severity, priority, SLA, action list)
- Metrics (12 KPIs, AM scorecard)
- Reporting (weekly report, executive summary)
- I/O (CSV roundtrip, serializers)
- CLI (argument parsing, command dispatch)
- Constants (enums, counts)

---

## Sample results (default 100-store, 3-campaign dataset)

| Metric | Value |
|--------|-------|
| Stores | 100 |
| Campaigns | 3 |
| Allocation lines | 1,410 |
| Total exceptions detected | 1,603 |
| Critical exceptions | 651 |
| SLA-breached exceptions | 160 |
| Campaign readiness rate | 83.8% |
| Confirmation completion rate | 96.9% |
| Photo proof completion rate | 91.9% |
| Allocation accuracy rate | 89.2% |
| Sell-through rate | 64.9% |
| Stockout risk stores | 99 |
| Overstock risk stores | 291 |

---

## Tech stack

- Python 3.11+
- pandas (data manipulation)
- Streamlit (dashboard)
- Plotly (dashboard charts)
- matplotlib (architecture diagram rendering)
- pytest (testing)
- uv (dependency management)

---

## How to run

```bash
# Install from source
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Generate data and run the pipeline
python scripts/generate_sample_data.py
python scripts/build_exception_table.py --aging-date 2026-07-15
python scripts/build_kpi_summary.py --aging-date 2026-07-15
python scripts/generate_weekly_report.py --aging-date 2026-07-15

# Run the dashboard
streamlit run dashboard/app.py

# Run tests
pytest -q
```

---

## What this project does not claim

- Real-world retail operations experience.
- Access to any real company's data or internal systems.
- A production-ready system. This is a portfolio project with simulated data.
- PyPI availability. Install from source only.
- Real photos or image processing. Photo proof records contain metadata only.
- Deep learning or ML forecasting. Rule-based logic and deterministic formulas
  only.
