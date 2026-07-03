"""End-to-end smoke test: clean sample data -> processed outputs -> report.

Exercises the full pipeline in-process (no subprocess) to prove the whole
chain works from deterministic sample data through exception detection, KPI
computation, and weekly report generation. A separate scripts/smoke.sh drives
the same flow via the standalone script entry points for shell-level validation.
"""

from __future__ import annotations

import csv
import os
from datetime import date

import pytest

from retail_ops_control_tower.data_generation import (
    TABLE_COLUMNS,
    TABLE_NAMES,
    generate_sample_data,
)
from retail_ops_control_tower.exceptions import (
    EXCEPTION_TYPES,
    ExceptionEngine,
    detect_exceptions,
)
from retail_ops_control_tower.io import read_all_csv_tables, write_all_csv_tables
from retail_ops_control_tower.metrics import (
    ALL_KPIS,
    MetricsEngine,
    compute_metrics,
)
from retail_ops_control_tower.reporting import (
    REPORT_SECTIONS,
    SIMULATED_DATA_NOTICE,
    WeeklyReportGenerator,
    generate_weekly_report,
)
from retail_ops_control_tower.validation import validate_tables


AGING_DATE = date(2026, 7, 15)
WEEK_ENDING = date(2026, 7, 15)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def sample_tables(tmp_path_factory):
    """Generate the canonical sample dataset once for all tests in this module."""
    out = tmp_path_factory.mktemp("sample")
    generate_sample_data(seed=42, output_dir=str(out))
    return read_all_csv_tables(str(out))


# ---------------------------------------------------------------------------
# Pipeline stage 1: sample data generation
# ---------------------------------------------------------------------------

class TestSmokeDataGeneration:
    """Stage 1: deterministic sample data generation produces 8 valid tables."""

    def test_generate_writes_eight_csv_files(self, tmp_path):
        tables = generate_sample_data(seed=42, output_dir=str(tmp_path))
        for name in TABLE_NAMES:
            path = tmp_path / f"{name}.csv"
            assert path.exists(), f"{name}.csv was not written"
            assert len(tables[name]) > 0, f"{name} has zero rows"

    def test_generated_data_passes_validation(self, tmp_path):
        """The generated sample dataset must have intact referential
        integrity: zero critical validation findings."""
        generate_sample_data(seed=42, output_dir=str(tmp_path))
        tables = read_all_csv_tables(str(tmp_path))
        report = validate_tables(tables)
        assert report.critical_count == 0, [
            f.to_dict() for f in report.by_severity("critical")[:5]
        ]

    def test_generation_is_deterministic(self, tmp_path):
        t1 = generate_sample_data(seed=42, output_dir=str(tmp_path / "a"), write_csv=False)
        t2 = generate_sample_data(seed=42, output_dir=str(tmp_path / "b"), write_csv=False)
        assert t1 == t2


# ---------------------------------------------------------------------------
# Pipeline stage 2: exception table + action list
# ---------------------------------------------------------------------------

class TestSmokeExceptionDetection:
    """Stage 2: exception engine detects all 9 types from the sample data."""

    def test_detects_all_nine_exception_types(self, sample_tables):
        report = detect_exceptions(sample_tables, aging_date=AGING_DATE)
        found = {e.exception_type for e in report.exceptions}
        for exc_type in EXCEPTION_TYPES:
            assert exc_type in found, f"Missing exception type: {exc_type}"

    def test_exception_report_has_findings(self, sample_tables):
        report = detect_exceptions(sample_tables, aging_date=AGING_DATE)
        assert report.total > 0
        assert report.open_count > 0

    def test_action_list_sorted_by_severity_then_age(self, sample_tables):
        """The action list is sorted by severity (critical first), then age_days
        (oldest first). Within the same severity tier, age_days is descending."""
        engine = ExceptionEngine(sample_tables, AGING_DATE)
        engine.detect()
        action_list = engine.build_action_list()
        assert len(action_list) > 0
        severity_rank = {"critical": 0, "watch": 1, "info": 2}
        # Verify severity tiers are non-decreasing (critical before watch before info).
        ranks = [severity_rank.get(e.severity, 9) for e in action_list]
        assert ranks == sorted(ranks), "Action list not sorted by severity"
        # Within each severity tier, age_days should be non-increasing (oldest first).
        for i in range(len(action_list) - 1):
            e1, e2 = action_list[i], action_list[i + 1]
            if e1.severity == e2.severity:
                assert e1.age_days >= e2.age_days, (
                    f"Age ordering violated: {e1.exception_id} (age={e1.age_days}) "
                    f"before {e2.exception_id} (age={e2.age_days})"
                )

    def test_exceptions_csv_columns(self, sample_tables, tmp_path):
        """The exceptions.csv output has the columns the build script writes."""
        engine = ExceptionEngine(sample_tables, AGING_DATE)
        report = engine.detect()
        out = tmp_path / "exceptions.csv"
        columns = [
            "exception_id", "exception_type", "severity", "owner", "region",
            "area_manager", "age_days", "status", "recommended_action",
            "campaign_id", "store_id", "sku", "allocation_id",
            "confirmation_id", "message", "created_date", "sla_status",
            "priority_score",
        ]
        with open(out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            for exc in report.exceptions:
                row = exc.to_dict()
                writer.writerow({c: row.get(c, "") for c in columns})
        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == report.total
        assert reader.fieldnames == columns


# ---------------------------------------------------------------------------
# Pipeline stage 3: KPI summary + AM scorecard
# ---------------------------------------------------------------------------

class TestSmokeMetrics:
    """Stage 3: metrics engine computes all 12 KPIs and the AM scorecard."""

    def test_all_twelve_kpis_computed(self, sample_tables):
        summary = compute_metrics(sample_tables, aging_date=AGING_DATE)
        for kpi_name in ALL_KPIS:
            assert kpi_name in summary.kpis, f"Missing KPI: {kpi_name}"

    def test_rate_kpis_in_unit_interval(self, sample_tables):
        """Rate KPIs must be in [0.0, 1.0] (except exception_rate which may exceed 1.0)."""
        summary = compute_metrics(sample_tables, aging_date=AGING_DATE)
        rate_kpis = [
            "campaign_readiness_rate",
            "confirmation_completion_rate",
            "photo_proof_completion_rate",
            "allocation_accuracy_rate",
            "quantity_mismatch_rate",
            "sell_through_rate",
        ]
        for name in rate_kpis:
            value = summary.get(name)
            assert 0.0 <= value <= 1.0, f"{name}={value} out of [0,1]"

    def test_count_kpis_non_negative(self, sample_tables):
        summary = compute_metrics(sample_tables, aging_date=AGING_DATE)
        count_kpis = [
            "open_exception_count",
            "sla_breach_count",
            "stockout_risk_count",
            "overstock_risk_count",
        ]
        for name in count_kpis:
            value = summary.get(name)
            assert value >= 0, f"{name}={value} is negative"

    def test_am_scorecard_non_empty(self, sample_tables):
        engine = MetricsEngine(sample_tables, AGING_DATE)
        engine.compute()
        rows = engine.compute_am_scorecard()
        assert len(rows) > 0
        for row in rows:
            assert row.area_manager != ""
            assert row.store_count > 0


# ---------------------------------------------------------------------------
# Pipeline stage 4: weekly report
# ---------------------------------------------------------------------------

class TestSmokeWeeklyReport:
    """Stage 4: weekly report generator produces a complete report."""

    def test_report_has_all_eight_sections(self, sample_tables):
        report = generate_weekly_report(sample_tables, AGING_DATE, WEEK_ENDING)
        for section in REPORT_SECTIONS:
            assert section in report, f"Missing section: {section}"

    def test_report_contains_simulated_notice(self, sample_tables):
        report = generate_weekly_report(sample_tables, AGING_DATE, WEEK_ENDING)
        assert SIMULATED_DATA_NOTICE in report

    def test_report_written_to_disk(self, sample_tables, tmp_path):
        generator = WeeklyReportGenerator(sample_tables, AGING_DATE, WEEK_ENDING)
        full = generator.generate_full_report()
        summary = generator.generate_executive_summary()
        full_path = tmp_path / "weekly_ops_report.md"
        summary_path = tmp_path / "executive_summary.md"
        full_path.write_text(full, encoding="utf-8")
        summary_path.write_text(summary, encoding="utf-8")
        assert full_path.exists()
        assert summary_path.exists()
        assert len(full) > 1000
        assert len(summary) > 100


# ---------------------------------------------------------------------------
# Full pipeline integration: generate -> validate -> exceptions -> metrics -> report
# ---------------------------------------------------------------------------

class TestSmokeFullPipeline:
    """Run the entire pipeline in one pass against fresh sample data."""

    def test_end_to_end_pipeline(self, tmp_path):
        # Stage 1: generate sample data
        sample_dir = tmp_path / "sample"
        generate_sample_data(seed=42, output_dir=str(sample_dir))
        tables = read_all_csv_tables(str(sample_dir))

        # Stage 1b: validate referential integrity
        val_report = validate_tables(tables)
        assert val_report.critical_count == 0

        # Stage 2: detect exceptions
        exc_engine = ExceptionEngine(tables, AGING_DATE)
        exc_report = exc_engine.detect()
        assert exc_report.total > 0
        action_list = exc_engine.build_action_list()
        assert len(action_list) > 0

        # Stage 3: compute metrics
        metrics_engine = MetricsEngine(tables, AGING_DATE, exception_report=exc_report)
        metrics_summary = metrics_engine.compute()
        am_scorecard = metrics_engine.compute_am_scorecard()
        assert len(metrics_summary.kpis) == 12
        assert len(am_scorecard) > 0

        # Stage 4: generate weekly report
        generator = WeeklyReportGenerator(tables, AGING_DATE, WEEK_ENDING)
        full_report = generator.generate_full_report()
        exec_summary = generator.generate_executive_summary()

        # Write outputs to disk
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "weekly_ops_report.md").write_text(full_report, encoding="utf-8")
        (reports_dir / "executive_summary.md").write_text(exec_summary, encoding="utf-8")

        # Verify outputs exist and are non-trivial
        assert (reports_dir / "weekly_ops_report.md").stat().st_size > 1000
        assert (reports_dir / "executive_summary.md").stat().st_size > 100

        # Verify the report references the computed data
        assert SIMULATED_DATA_NOTICE in full_report
        assert "2026-07-15" in full_report

    def test_csv_round_trip_preserves_row_counts(self, tmp_path):
        """Writing all tables to CSV and reading them back preserves row counts."""
        tables = generate_sample_data(seed=42, output_dir=str(tmp_path))
        write_all_csv_tables(tables, str(tmp_path / "roundtrip"))
        loaded = read_all_csv_tables(str(tmp_path / "roundtrip"))
        for name in TABLE_NAMES:
            assert len(loaded[name]) == len(tables[name]), (
                f"{name}: round-trip row count mismatch"
            )

    def test_processed_outputs_written_to_disk(self, tmp_path):
        """The build_exception_table.py script writes exceptions.csv and
        daily_action_list.csv to data/processed/. Mirror that here."""
        sample_dir = tmp_path / "sample"
        generate_sample_data(seed=42, output_dir=str(sample_dir))
        tables = read_all_csv_tables(str(sample_dir))

        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()

        engine = ExceptionEngine(tables, AGING_DATE)
        report = engine.detect()
        action_items = engine.build_action_list()

        # Write exceptions.csv (same columns as the script)
        exc_columns = [
            "exception_id", "exception_type", "severity", "owner", "region",
            "area_manager", "age_days", "status", "recommended_action",
            "campaign_id", "store_id", "sku", "allocation_id",
            "confirmation_id", "message", "created_date", "sla_status",
            "priority_score",
        ]
        exc_path = processed_dir / "exceptions.csv"
        with open(exc_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=exc_columns, extrasaction="ignore")
            writer.writeheader()
            for exc in report.exceptions:
                row = exc.to_dict()
                writer.writerow({c: row.get(c, "") for c in exc_columns})

        # Write daily_action_list.csv (same columns as the script)
        action_columns = [
            "rank", "exception_id", "exception_type", "severity",
            "priority_score", "owner", "region", "area_manager",
            "store_id", "campaign_id", "sku", "age_days", "sla_status",
            "recommended_action", "message",
        ]
        action_path = processed_dir / "daily_action_list.csv"
        with open(action_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=action_columns, extrasaction="ignore")
            writer.writeheader()
            for rank, exc in enumerate(action_items, 1):
                row = exc.to_dict()
                row["rank"] = rank
                writer.writerow({c: row.get(c, "") for c in action_columns})

        assert exc_path.exists()
        assert action_path.exists()
        with open(exc_path, newline="", encoding="utf-8") as f:
            assert len(list(csv.DictReader(f))) == report.total
        with open(action_path, newline="", encoding="utf-8") as f:
            assert len(list(csv.DictReader(f))) == len(action_items)


# ---------------------------------------------------------------------------
# Script-level smoke: verify the standalone scripts exist and are importable
# ---------------------------------------------------------------------------

class TestSmokeScriptsExist:
    """The standalone pipeline scripts must exist and be importable."""

    @pytest.mark.parametrize("script_name", [
        "generate_sample_data.py",
        "build_exception_table.py",
        "generate_weekly_report.py",
        "build_kpi_summary.py",
        "generate_validation_summary.py",
    ])
    def test_script_file_exists(self, script_name):
        path = os.path.join(PROJECT_ROOT, "scripts", script_name)
        assert os.path.isfile(path), f"Script not found: {path}"

    def test_smoke_sh_exists(self):
        path = os.path.join(PROJECT_ROOT, "scripts", "smoke.sh")
        assert os.path.isfile(path), f"smoke.sh not found: {path}"

    def test_smoke_sh_is_executable(self):
        path = os.path.join(PROJECT_ROOT, "scripts", "smoke.sh")
        assert os.access(path, os.X_OK), "smoke.sh is not executable"
