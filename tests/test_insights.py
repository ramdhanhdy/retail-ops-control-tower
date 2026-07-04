"""Tests for the T13 diagnostic insight engine."""

from __future__ import annotations

from datetime import date

import pytest

from retail_ops_control_tower.exceptions import ExceptionRecord, ExceptionReport
from retail_ops_control_tower.insights import (
    EXECUTION_EXCEPTION_TYPES,
    INSIGHT_CATEGORIES,
    Insight,
    InsightEngine,
    InsightReport,
    build_insights_markdown,
    generate_insights,
)

AGING_DATE = date(2026, 7, 15)


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------

def make_exception(
    exception_type: str = "missing_confirmation",
    severity: str = "watch",
    store_id: str = "S001",
    region: str = "North",
    campaign_id: str = "C-001",
    sku: str = "SKU-001",
    allocation_id: str = "",
) -> ExceptionRecord:
    return ExceptionRecord(
        exception_id="EXC-000",
        exception_type=exception_type,
        severity=severity,
        store_id=store_id,
        region=region,
        campaign_id=campaign_id,
        sku=sku,
        allocation_id=allocation_id,
        status="open",
    )


def make_stores(count: int = 10) -> list[dict]:
    """10 stores: S001-S002 in North with rep R1, the rest South/R2."""
    stores = []
    for i in range(1, count + 1):
        stores.append({
            "store_id": f"S{i:03d}",
            "store_name": f"Store {i}",
            "region": "North" if i <= 2 else "South",
            "area_manager": "AM-01" if i <= 5 else "AM-02",
            "field_rep": "R1" if i <= 2 else "R2",
            "store_format": "standard",
        })
    return stores


def make_report(exceptions: list[ExceptionRecord]) -> ExceptionReport:
    return ExceptionReport(
        exceptions=exceptions, aging_date=AGING_DATE.isoformat()
    )


def run_engine(
    exceptions: list[ExceptionRecord],
    tables: dict | None = None,
) -> InsightReport:
    tables = tables or {"stores": make_stores()}
    engine = InsightEngine(
        tables, AGING_DATE, exception_report=make_report(exceptions)
    )
    return engine.generate()


# ---------------------------------------------------------------------------
# General behavior
# ---------------------------------------------------------------------------

class TestGeneralBehavior:
    def test_empty_tables_produce_empty_report(self):
        report = run_engine([], tables={"stores": []})
        assert report.total == 0
        assert report.insights == []
        assert report.aging_date == AGING_DATE.isoformat()

    def test_deterministic_output(self):
        exceptions = [
            make_exception(store_id="S001") for _ in range(8)
        ] + [make_exception(store_id="S002"), make_exception(store_id="S003")]
        first = run_engine(exceptions)
        second = run_engine(exceptions)
        assert first.to_dict() == second.to_dict()

    def test_insight_ids_sequential_after_ranking(self):
        exceptions = [
            make_exception(store_id="S001") for _ in range(8)
        ] + [make_exception(store_id="S002"), make_exception(store_id="S003")]
        report = run_engine(exceptions)
        assert report.total > 0
        for idx, insight in enumerate(report.insights, start=1):
            assert insight.insight_id == f"INS-{idx:03d}"

    def test_insights_sorted_by_impact_score_desc(self):
        exceptions = [
            make_exception(store_id="S001") for _ in range(8)
        ] + [make_exception(store_id="S002"), make_exception(store_id="S003")]
        report = run_engine(exceptions)
        scores = [i.impact_score for i in report.insights]
        assert scores == sorted(scores, reverse=True)

    def test_categories_are_valid(self):
        exceptions = [
            make_exception(store_id="S001") for _ in range(8)
        ] + [make_exception(store_id="S002"), make_exception(store_id="S003")]
        report = run_engine(exceptions)
        for insight in report.insights:
            assert insight.category in INSIGHT_CATEGORIES

    def test_to_dict_has_all_fields(self):
        insight = Insight(insight_id="INS-001", category="regional_hotspot")
        row = insight.to_dict()
        for key in (
            "insight_id", "category", "headline", "detail", "metric_name",
            "metric_value", "baseline_value", "lift", "affected_count",
            "impact_score", "recommended_action", "evidence",
        ):
            assert key in row

    def test_generate_insights_convenience_function(self):
        report = generate_insights(
            {"stores": make_stores()},
            AGING_DATE,
            exception_report=make_report([]),
        )
        assert isinstance(report, InsightReport)


# ---------------------------------------------------------------------------
# 1. Pareto concentration
# ---------------------------------------------------------------------------

class TestParetoConcentration:
    def test_concentrated_backlog_is_reported(self):
        # S001 holds 8 of 10 exceptions -> 1 of 10 stores covers 80%.
        exceptions = [
            make_exception(store_id="S001") for _ in range(8)
        ] + [make_exception(store_id="S002"), make_exception(store_id="S003")]
        report = run_engine(exceptions)
        findings = report.by_category("pareto_concentration")
        assert len(findings) == 1
        insight = findings[0]
        assert insight.affected_count == 8
        assert insight.metric_value == pytest.approx(0.8)
        assert insight.baseline_value == pytest.approx(0.1)
        assert insight.lift == pytest.approx(8.0)
        assert "S001" in insight.evidence

    def test_even_backlog_is_not_reported(self):
        # 10 exceptions spread evenly over 10 stores: 8 stores needed to
        # reach 80%, above the PARETO_MAX_STORE_SHARE cutoff.
        exceptions = [
            make_exception(store_id=f"S{i:03d}") for i in range(1, 11)
        ]
        report = run_engine(exceptions)
        assert report.by_category("pareto_concentration") == []

    def test_no_stores_no_finding(self):
        exceptions = [make_exception(store_id="S001")]
        report = run_engine(exceptions, tables={"stores": []})
        assert report.by_category("pareto_concentration") == []


# ---------------------------------------------------------------------------
# 2. Regional hotspots
# ---------------------------------------------------------------------------

class TestRegionalHotspots:
    def test_over_indexed_region_is_flagged(self):
        # North has 20% of stores but 100% of the 8 missing_confirmation
        # exceptions -> lift 5.0.
        exceptions = [
            make_exception(store_id="S001", region="North")
            for _ in range(8)
        ]
        report = run_engine(exceptions)
        findings = report.by_category("regional_hotspot")
        assert len(findings) == 1
        insight = findings[0]
        assert "North" in insight.headline
        assert insight.lift == pytest.approx(5.0)
        assert insight.affected_count == 8

    def test_small_groups_are_not_flagged(self):
        # Below MIN_GROUP_EXCEPTIONS.
        exceptions = [
            make_exception(store_id="S001", region="North")
            for _ in range(5)
        ]
        report = run_engine(exceptions)
        assert report.by_category("regional_hotspot") == []

    def test_proportional_region_is_not_flagged(self):
        # South holds 80% of stores and 80% of exceptions -> lift 1.0.
        exceptions = [
            make_exception(store_id=f"S{i:03d}", region="South")
            for i in range(3, 11)
        ] + [
            make_exception(store_id="S001", region="North"),
            make_exception(store_id="S002", region="North"),
        ]
        report = run_engine(exceptions)
        flagged_regions = [
            i.headline for i in report.by_category("regional_hotspot")
            if "South" in i.headline
        ]
        assert flagged_regions == []


# ---------------------------------------------------------------------------
# 3. Upstream attribution
# ---------------------------------------------------------------------------

class TestUpstreamAttribution:
    def make_dispatch_tables(self) -> dict:
        # 10 shipments: 2 from DC-9, 8 from DC-1, all one carrier.
        dispatch = []
        for i in range(1, 11):
            dispatch.append({
                "allocation_id": f"A{i:03d}",
                "dc_id": "DC-9" if i <= 2 else "DC-1",
                "carrier": "CARRIER-X",
            })
        return {"stores": make_stores(), "dispatch": dispatch}

    def test_over_indexed_dc_is_flagged(self):
        # All 8 mismatches route to DC-9 which has 20% shipment share.
        exceptions = [
            make_exception(
                exception_type="quantity_mismatch",
                store_id="S001",
                allocation_id="A001" if i % 2 == 0 else "A002",
            )
            for i in range(8)
        ]
        report = run_engine(exceptions, tables=self.make_dispatch_tables())
        findings = report.by_category("upstream_attribution")
        dc_findings = [f for f in findings if "DC-9" in f.headline]
        assert len(dc_findings) == 1
        assert dc_findings[0].lift == pytest.approx(5.0)

    def test_single_carrier_not_flagged(self):
        # The only carrier has lift 1.0 and must not be flagged.
        exceptions = [
            make_exception(
                exception_type="quantity_mismatch",
                store_id="S001",
                allocation_id="A001",
            )
            for _ in range(8)
        ]
        report = run_engine(exceptions, tables=self.make_dispatch_tables())
        carrier_findings = [
            f for f in report.by_category("upstream_attribution")
            if "CARRIER-X" in f.headline
        ]
        assert carrier_findings == []

    def test_no_dispatch_data_no_finding(self):
        exceptions = [
            make_exception(
                exception_type="quantity_mismatch", allocation_id="A001"
            )
            for _ in range(8)
        ]
        report = run_engine(exceptions)
        assert report.by_category("upstream_attribution") == []


# ---------------------------------------------------------------------------
# 4. Execution vs sales
# ---------------------------------------------------------------------------

class TestExecutionSalesGap:
    def make_sales_tables(self) -> dict:
        # Every store received 100 units. Flagged stores (S001-S005)
        # sold 50; clean stores (S006-S010) sold 80.
        confirmations = [
            {"store_id": f"S{i:03d}", "received_quantity": "100"}
            for i in range(1, 11)
        ]
        sales = [
            {
                "store_id": f"S{i:03d}",
                "units_sold": "50" if i <= 5 else "80",
            }
            for i in range(1, 11)
        ]
        return {
            "stores": make_stores(),
            "store_confirmations": confirmations,
            "sales_daily": sales,
        }

    def test_gap_is_reported(self):
        exceptions = [
            make_exception(
                exception_type="missing_photo_proof",
                store_id=f"S{(i % 5) + 1:03d}",
            )
            for i in range(10)
        ]
        report = run_engine(exceptions, tables=self.make_sales_tables())
        findings = report.by_category("execution_sales_gap")
        assert len(findings) == 1
        insight = findings[0]
        assert insight.metric_value == pytest.approx(0.5)
        assert insight.baseline_value == pytest.approx(0.8)
        assert "30.0pp" in insight.headline

    def test_no_gap_not_reported(self):
        # All stores sell identically -> gap 0 < threshold.
        tables = self.make_sales_tables()
        for row in tables["sales_daily"]:
            row["units_sold"] = "70"
        exceptions = [
            make_exception(
                exception_type="missing_photo_proof",
                store_id=f"S{(i % 5) + 1:03d}",
            )
            for i in range(10)
        ]
        report = run_engine(exceptions, tables=tables)
        assert report.by_category("execution_sales_gap") == []

    def test_non_execution_exceptions_do_not_trigger(self):
        exceptions = [
            make_exception(
                exception_type="low_sell_through", store_id="S001"
            )
            for _ in range(10)
        ]
        assert "low_sell_through" not in EXECUTION_EXCEPTION_TYPES
        report = run_engine(exceptions, tables=self.make_sales_tables())
        assert report.by_category("execution_sales_gap") == []


# ---------------------------------------------------------------------------
# 5. Field rep workload
# ---------------------------------------------------------------------------

class TestFieldRepWorkload:
    def test_over_indexed_rep_is_flagged(self):
        # R1 covers 20% of stores but drives all 8 photo failures.
        exceptions = [
            make_exception(
                exception_type="missing_photo_proof", store_id="S001"
            )
            for _ in range(8)
        ]
        report = run_engine(exceptions)
        findings = report.by_category("field_rep_workload")
        assert len(findings) == 1
        insight = findings[0]
        assert "R1" in insight.headline
        assert insight.lift == pytest.approx(5.0)

    def test_non_rep_exceptions_do_not_count(self):
        exceptions = [
            make_exception(
                exception_type="stockout_risk", store_id="S001"
            )
            for _ in range(8)
        ]
        report = run_engine(exceptions)
        assert report.by_category("field_rep_workload") == []


# ---------------------------------------------------------------------------
# 6. Rebalancing opportunity
# ---------------------------------------------------------------------------

class TestRebalancingOpportunity:
    def test_matched_sku_produces_finding(self):
        exceptions = [
            make_exception(
                exception_type="stockout_risk",
                store_id="S001",
                campaign_id="C-001",
                sku="SKU-001",
                severity="critical",
            ),
            make_exception(
                exception_type="overstock_risk",
                store_id="S002",
                campaign_id="C-001",
                sku="SKU-001",
            ),
        ]
        report = run_engine(exceptions)
        findings = report.by_category("rebalancing_opportunity")
        assert len(findings) == 1
        insight = findings[0]
        assert "C-001" in insight.headline
        assert insight.metric_value == pytest.approx(1.0)
        assert insight.affected_count == 2
        assert "SKU-001" in insight.evidence

    def test_unmatched_skus_produce_no_finding(self):
        exceptions = [
            make_exception(
                exception_type="stockout_risk", sku="SKU-001",
                store_id="S001",
            ),
            make_exception(
                exception_type="overstock_risk", sku="SKU-002",
                store_id="S002",
            ),
        ]
        report = run_engine(exceptions)
        assert report.by_category("rebalancing_opportunity") == []

    def test_one_finding_per_campaign(self):
        exceptions = []
        for campaign in ("C-001", "C-002"):
            exceptions.extend([
                make_exception(
                    exception_type="stockout_risk",
                    store_id="S001",
                    campaign_id=campaign,
                    sku="SKU-001",
                ),
                make_exception(
                    exception_type="overstock_risk",
                    store_id="S002",
                    campaign_id=campaign,
                    sku="SKU-001",
                ),
            ])
        report = run_engine(exceptions)
        assert len(report.by_category("rebalancing_opportunity")) == 2


# ---------------------------------------------------------------------------
# Markdown brief
# ---------------------------------------------------------------------------

class TestMarkdownBrief:
    def test_empty_report_renders(self):
        markdown = build_insights_markdown(
            InsightReport(insights=[], aging_date=AGING_DATE.isoformat())
        )
        assert "# Diagnostic Insights" in markdown
        assert "No findings" in markdown

    def test_findings_render_with_sections(self):
        exceptions = [
            make_exception(store_id="S001") for _ in range(8)
        ] + [make_exception(store_id="S002"), make_exception(store_id="S003")]
        report = run_engine(exceptions)
        markdown = build_insights_markdown(report)
        assert "## Headline findings" in markdown
        assert "INS-001" in markdown
        assert "Concentration analysis (Pareto)" in markdown
        assert "Recommended action" in markdown

    def test_markdown_is_deterministic(self):
        exceptions = [
            make_exception(store_id="S001") for _ in range(8)
        ] + [make_exception(store_id="S002")]
        first = build_insights_markdown(run_engine(exceptions))
        second = build_insights_markdown(run_engine(exceptions))
        assert first == second
