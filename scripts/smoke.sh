#!/usr/bin/env bash
#
# smoke.sh - End-to-end pipeline smoke test.
#
# Runs the full Retail Operations Control Tower pipeline from a clean state:
#
#   1. Generate deterministic sample data (8 CSV tables).
#   2. Build the exception table and daily action list.
#   3. Build the KPI summary and AM scorecard.
#   4. Generate the weekly operations report.
#   5. Build the diagnostic insights.
#   6. Run the full pytest suite.
#
# The script exits 0 on success, non-zero on any failure. It is designed to
# run from the project root with no prior state (data/sample, data/processed,
# and reports/ are regenerated in place).
#
# Usage:
#   ./scripts/smoke.sh
#
set -euo pipefail

# Resolve the project root from the script location so the script works
# regardless of the calling directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Detect the Python executable. Prefer the active venv, then the project
# .venv, then fall back to system python3.
if [ -n "${VIRTUAL_ENV:-}" ]; then
    PYTHON="python"
elif [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.venv/bin/activate"
    PYTHON="python"
else
    PYTHON="python3"
fi

echo "=== Retail Operations Control Tower - Smoke Test ==="
echo "Python: $($PYTHON --version 2>&1)"
echo "Project root: $PROJECT_ROOT"
echo ""

# --------------------------------------------------------------------------
# Stage 1: Generate sample data
# --------------------------------------------------------------------------
echo "--- Stage 1: Generate sample data ---"
$PYTHON scripts/generate_sample_data.py --output data/sample --seed 42

# Verify all 8 CSV files were created.
for table in stores campaigns allocation_plan dispatch store_confirmations photo_proofs sales_daily issues; do
    if [ ! -f "data/sample/${table}.csv" ]; then
        echo "FAIL: data/sample/${table}.csv was not created" >&2
        exit 1
    fi
done
echo "All 8 sample CSV files present."
echo ""

# --------------------------------------------------------------------------
# Stage 2: Build exception table and daily action list
# --------------------------------------------------------------------------
echo "--- Stage 2: Build exception table ---"
$PYTHON scripts/build_exception_table.py \
    --input-dir data/sample \
    --output-dir data/processed \
    --aging-date 2026-07-15

if [ ! -f "data/processed/exceptions.csv" ]; then
    echo "FAIL: data/processed/exceptions.csv was not created" >&2
    exit 1
fi
if [ ! -f "data/processed/daily_action_list.csv" ]; then
    echo "FAIL: data/processed/daily_action_list.csv was not created" >&2
    exit 1
fi
EXCEPTION_COUNT=$(tail -n +2 data/processed/exceptions.csv | wc -l)
echo "exceptions.csv: ${EXCEPTION_COUNT} exception rows"
ACTION_COUNT=$(tail -n +2 data/processed/daily_action_list.csv | wc -l)
echo "daily_action_list.csv: ${ACTION_COUNT} action items"
echo ""

# --------------------------------------------------------------------------
# Stage 3: Build KPI summary and AM scorecard
# --------------------------------------------------------------------------
echo "--- Stage 3: Build KPI summary ---"
$PYTHON scripts/build_kpi_summary.py \
    --input-dir data/sample \
    --output-dir data/processed \
    --aging-date 2026-07-15

if [ ! -f "data/processed/kpi_summary.csv" ]; then
    echo "FAIL: data/processed/kpi_summary.csv was not created" >&2
    exit 1
fi
if [ ! -f "data/processed/am_scorecard.csv" ]; then
    echo "FAIL: data/processed/am_scorecard.csv was not created" >&2
    exit 1
fi
KPI_COUNT=$(tail -n +2 data/processed/kpi_summary.csv | wc -l)
echo "kpi_summary.csv: ${KPI_COUNT} KPI rows"
AM_COUNT=$(tail -n +2 data/processed/am_scorecard.csv | wc -l)
echo "am_scorecard.csv: ${AM_COUNT} area manager rows"
echo ""

# --------------------------------------------------------------------------
# Stage 4: Generate weekly operations report
# --------------------------------------------------------------------------
echo "--- Stage 4: Generate weekly report ---"
$PYTHON scripts/generate_weekly_report.py \
    --input-dir data/sample \
    --output-dir reports \
    --aging-date 2026-07-15 \
    --week-ending 2026-07-15

if [ ! -f "reports/weekly_ops_report.md" ]; then
    echo "FAIL: reports/weekly_ops_report.md was not created" >&2
    exit 1
fi
if [ ! -f "reports/executive_summary.md" ]; then
    echo "FAIL: reports/executive_summary.md was not created" >&2
    exit 1
fi
REPORT_SIZE=$(wc -c < reports/weekly_ops_report.md)
SUMMARY_SIZE=$(wc -c < reports/executive_summary.md)
echo "weekly_ops_report.md: ${REPORT_SIZE} bytes"
echo "executive_summary.md: ${SUMMARY_SIZE} bytes"
echo ""

# --------------------------------------------------------------------------
# Stage 5: Build diagnostic insights
# --------------------------------------------------------------------------
echo "--- Stage 5: Build diagnostic insights ---"
$PYTHON scripts/build_insights.py \
    --input-dir data/sample \
    --output-dir data/processed \
    --report-dir reports \
    --aging-date 2026-07-15

if [ ! -f "data/processed/insights.csv" ]; then
    echo "FAIL: data/processed/insights.csv was not created" >&2
    exit 1
fi
if [ ! -f "reports/insights.md" ]; then
    echo "FAIL: reports/insights.md was not created" >&2
    exit 1
fi
INSIGHT_COUNT=$(tail -n +2 data/processed/insights.csv | wc -l)
echo "insights.csv: ${INSIGHT_COUNT} insight rows"
echo ""

# --------------------------------------------------------------------------
# Stage 6: Run the full pytest suite
# --------------------------------------------------------------------------
echo "--- Stage 6: Run pytest ---"
$PYTHON -m pytest -q
echo ""

echo "=== Smoke test PASSED ==="
