# QA Report

## Summary

This report documents the test suite and smoke test for the Retail Operations
Control Tower project. All tests pass and the end-to-end smoke pipeline exits 0.

- **Total tests:** 327
- **Test suite result:** 327 passed in 32.98s
- **Smoke script result:** PASS (exit code 0)

## Test suite

The test suite covers all modules: generator, validation, exceptions, metrics,
report, I/O, models, constants, CLI, and imports.

| Test file | Tests | Module covered |
|-----------|-------|----------------|
| tests/test_cli.py | 5 | CLI argument parsing and dispatch |
| tests/test_constants.py | 8 | Constants and configuration |
| tests/test_data_generation.py | 53 | Sample data generator (T08) |
| tests/test_exceptions.py | 34 | Exception and action-list engine (T10) |
| tests/test_imports.py | 13 | Baseline import tests for all modules |
| tests/test_io.py | 28 | JSON store, CSV store, serializers |
| tests/test_metrics.py | 65 | KPI metrics layer (T11) |
| tests/test_models.py | 8 | Model dataclass construction |
| tests/test_reporting.py | 57 | Weekly report generator (T12) |
| tests/test_smoke.py | 24 | End-to-end pipeline integration |
| tests/test_validation.py | 32 | Validation and reconciliation engine (T09) |
| **Total** | **327** | |

### Module coverage

- **Generator (T08):** 53 tests covering file structure, row counts, primary
  key uniqueness, referential integrity, controlled exception cases,
  determinism, clamping, and data quality.
- **Validation (T09):** 32 tests covering all 9 validation rules, finding
  structure, clean data, CSV I/O round-trip, and sample data integration.
- **Exceptions (T10):** 34 tests covering all 9 exception type detectors,
  exception record structure, action list sorting, report properties, and
  convenience functions.
- **Metrics (T11):** 65 tests covering all 12 KPIs, division-by-zero edge cases,
  process vs performance separation, determinism, AM scorecard, and sample
  data integration.
- **Report (T12):** 57 tests covering all 8 report sections, simulated data
  notice, no placeholder text, action items, data-driven content, determinism,
  and convenience functions.
- **I/O:** 28 tests covering JSON store, CSV store type coercion, format
  value, read/write round-trip, and full 8-table round-trip.
- **Smoke:** 24 end-to-end integration tests covering all 4 pipeline stages.

## Smoke test

The smoke script (`scripts/smoke.sh`) runs the full pipeline from a clean
state in 5 stages:

1. Generate deterministic sample data (8 CSV tables).
2. Build exception table and daily action list.
3. Build KPI summary and AM scorecard.
4. Generate weekly operations report.
5. Run the full pytest suite.

### Smoke command

```bash
./scripts/smoke.sh
```

### Smoke result

```
=== Retail Operations Control Tower - Smoke Test ===

--- Stage 1: Generate sample data ---
All 8 sample CSV files present.

--- Stage 2: Build exception table ---
exceptions.csv: 1603 exception rows
daily_action_list.csv: 1603 action items

--- Stage 3: Build KPI summary ---
kpi_summary.csv: 12 KPI rows
am_scorecard.csv: 10 area manager rows

--- Stage 4: Generate weekly report ---
weekly_ops_report.md: 11054 bytes
executive_summary.md: 2487 bytes

--- Stage 5: Run pytest ---
327 passed in 32.78s

=== Smoke test PASSED ===
```

**Exit code:** 0

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| scripts/smoke.sh exits 0 from a clean shell | PASS |
| Test suite covers generator, validation, exceptions, metrics, report | PASS |
| No placeholder tests | PASS |
| QA report lists exact test count and smoke command result | PASS |

## Artifacts

- `tests/test_smoke.py` - 24 end-to-end integration tests
- `tests/test_io.py` - enhanced with 22 CSV store tests (was 6, now 28)
- `scripts/smoke.sh` - executable shell script, 5-stage pipeline
- `reports/qa_report.md` - this report
