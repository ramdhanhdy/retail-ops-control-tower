"""Weekly report generator (T12).

Produces executive-friendly weekly operations reports in Markdown. The
report synthesizes data from four upstream layers:

    - T09 validation engine  (data quality and reconciliation findings)
    - T10 exception engine   (9 exception types, action list, SLA aging)
    - T11 metrics engine     (12 dashboard-ready KPIs, AM scorecard)
    - Raw data tables         (campaigns, stores, allocation_plan, dispatch,
                              store_confirmations, photo_proofs, sales_daily)

Report sections (per task spec):

    1. Executive snapshot
    2. Campaign readiness
    3. Allocation reconciliation
    4. Exception backlog
    5. AM/store follow-up list
    6. Sales/sell-through note
    7. Recommended actions
    8. Data caveats

The report is deterministic: the same input data and aging date always
produce identical output text. All figures are derived from the live
data tables and the T09/T10/T11 engines; no values are hardcoded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from retail_ops_control_tower.exceptions import (
    EXCEPTION_TYPES,
    ExceptionEngine,
    ExceptionReport,
)
from retail_ops_control_tower.io import read_all_csv_tables
from retail_ops_control_tower.metrics import (
    ALL_KPIS,
    AMScorecardRow,
    MetricsEngine,
    MetricsSummary,
)
from retail_ops_control_tower.validation import validate_tables

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The 8 required report section headings. Tests verify each is present.
REPORT_SECTIONS: list[str] = [
    "1. Executive Snapshot",
    "2. Campaign Readiness",
    "3. Allocation Reconciliation",
    "4. Exception Backlog",
    "5. AM / Store Follow-Up List",
    "6. Sales / Sell-Through Note",
    "7. Recommended Actions",
    "8. Data Caveats",
]

# Number of top action items to surface in the report.
TOP_ACTION_ITEMS = 10

# Default aging date used by the build script. Matches T10/T11 convention.
DEFAULT_AGING_DATE = date(2026, 7, 15)

# Sentence explicitly flagging the data as simulated. Tests check for this.
SIMULATED_DATA_NOTICE = (
    "This report is generated from simulated sample data. "
    "All figures are synthetic and do not represent real operations."
)

# Placeholder strings that must never appear in the final report. Tests
# scan for these to ensure no template leftovers remain.
PLACEHOLDER_STRINGS: list[str] = [
    "TODO",
    "PLACEHOLDER",
    "Lorem ipsum",
    "TBD",
    "FIXME",
    "<fill in>",
    "[insert",
]

# KPIs considered healthy enough to not appear in the "risk" summary.
# Sell-through below target is surfaced as a risk even though the
# sell_through_rate KPI itself is just a ratio.
_SELL_THROUGH_TARGET = 0.70


# ---------------------------------------------------------------------------
# Report context
# ---------------------------------------------------------------------------

@dataclass
class ReportContext:
    """All data needed to render the weekly report.

    The context bundles the raw tables, the T10 exception report, the
    T11 metrics summary, the T11 AM scorecard, and the T09 validation
    report so the renderer can produce all 8 sections in one pass.
    """

    tables: dict[str, list[dict[str, Any]]]
    exception_report: ExceptionReport
    metrics_summary: MetricsSummary
    am_scorecard: list[AMScorecardRow]
    validation_report: Any  # ValidationReport
    aging_date: date
    week_ending: date

    # Convenience accessors ------------------------------------------------

    @property
    def campaigns(self) -> list[dict[str, Any]]:
        return self.tables.get("campaigns", [])

    @property
    def stores(self) -> list[dict[str, Any]]:
        return self.tables.get("stores", [])

    @property
    def allocation_plan(self) -> list[dict[str, Any]]:
        return self.tables.get("allocation_plan", [])

    @property
    def dispatch(self) -> list[dict[str, Any]]:
        return self.tables.get("dispatch", [])

    @property
    def store_confirmations(self) -> list[dict[str, Any]]:
        return self.tables.get("store_confirmations", [])

    @property
    def photo_proofs(self) -> list[dict[str, Any]]:
        return self.tables.get("photo_proofs", [])

    @property
    def sales_daily(self) -> list[dict[str, Any]]:
        return self.tables.get("sales_daily", [])

    @property
    def issues(self) -> list[dict[str, Any]]:
        return self.tables.get("issues", [])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct(ratio: float) -> str:
    """Format a ratio (0.0-1.0) as a percentage string with 1 decimal."""
    return f"{ratio * 100:.1f}%"


def _pct_raw(value: float) -> str:
    """Format a raw float as a percentage (value already in 0-100 scale)."""
    return f"{value:.1f}%"


def _fmt_int(value: float | int) -> str:
    """Format a numeric value as a human-readable integer string."""
    return f"{int(round(value)):,}"


def _fmt_ratio(value: float, digits: int = 3) -> str:
    """Format a ratio value."""
    return f"{value:.{digits}f}"


def _safe_get(d: dict[str, Any], key: str, default: str = "") -> str:
    """Safely get a string value from a dict."""
    v = d.get(key, default)
    if v is None:
        return default
    return str(v)


# ---------------------------------------------------------------------------
# Report generator
# ---------------------------------------------------------------------------

class WeeklyReportGenerator:
    """Generates a weekly operations report from the data tables.

    Parameters:
        tables:           Dict mapping table name to list of record dicts,
                         as produced by read_all_csv_tables.
        aging_date:      Date used for exception age and SLA calculations.
        week_ending:     The last day of the reporting week. Defaults to
                         aging_date.
    """

    def __init__(
        self,
        tables: dict[str, list[dict[str, Any]]],
        aging_date: date | None = None,
        week_ending: date | None = None,
    ) -> None:
        self.aging_date = aging_date or DEFAULT_AGING_DATE
        self.week_ending = week_ending or self.aging_date

        # Run all three engines once.
        exc_engine = ExceptionEngine(tables, self.aging_date)
        exc_report = exc_engine.detect()

        metrics_engine = MetricsEngine(
            tables, self.aging_date, exception_report=exc_report
        )
        metrics_summary = metrics_engine.compute()
        am_scorecard = metrics_engine.compute_am_scorecard()

        validation_report = validate_tables(tables)

        self._action_list = exc_engine.build_action_list(top_n=0)

        self.context = ReportContext(
            tables=tables,
            exception_report=exc_report,
            metrics_summary=metrics_summary,
            am_scorecard=am_scorecard,
            validation_report=validation_report,
            aging_date=self.aging_date,
            week_ending=self.week_ending,
        )

    # -- public API ---------------------------------------------------------

    def generate_full_report(self) -> str:
        """Generate the complete weekly operations report as Markdown."""
        lines: list[str] = []
        lines.append("# Weekly Operations Report")
        lines.append("")
        lines.append(
            f"**Week ending:** {self.week_ending.isoformat()}  "
            f"| **Aging date:** {self.aging_date.isoformat()}"
        )
        lines.append("")
        lines.append(f"> {SIMULATED_DATA_NOTICE}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(self._section_executive_snapshot())
        lines.append(self._section_campaign_readiness())
        lines.append(self._section_allocation_reconciliation())
        lines.append(self._section_exception_backlog())
        lines.append(self._section_am_followup())
        lines.append(self._section_sales_sellthrough())
        lines.append(self._section_recommended_actions())
        lines.append(self._section_data_caveats())
        return "\n".join(lines)

    def generate_executive_summary(self) -> str:
        """Generate a short executive summary (section 1 only)."""
        lines: list[str] = []
        lines.append("# Executive Summary")
        lines.append("")
        lines.append(
            f"**Week ending:** {self.week_ending.isoformat()}  "
            f"| **Aging date:** {self.aging_date.isoformat()}"
        )
        lines.append("")
        lines.append(f"> {SIMULATED_DATA_NOTICE}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(self._section_executive_snapshot())
        lines.append("")
        lines.append("## Key Actions This Week")
        lines.append("")
        lines.append(self._top_action_items_table(top_n=5))
        return "\n".join(lines)

    # -- section 1: executive snapshot --------------------------------------

    def _section_executive_snapshot(self) -> str:
        ctx = self.context
        ms = ctx.metrics_summary
        er = ctx.exception_report
        vr = ctx.validation_report

        total_allocations = len(ctx.allocation_plan)
        total_dispatches = len(ctx.dispatch)
        total_confirmations = len(ctx.store_confirmations)
        total_stores = len(ctx.stores)
        total_campaigns = len(ctx.campaigns)

        sell_through = ms.get("sell_through_rate")
        campaign_readiness = ms.get("campaign_readiness_rate")
        open_exc = int(ms.get("open_exception_count"))
        sla_breach = int(ms.get("sla_breach_count"))

        lines: list[str] = []
        lines.append("## 1. Executive Snapshot")
        lines.append("")
        lines.append("This section provides a high-level overview of campaign "
                     "execution health, operational risk, and data quality for "
                     "the reporting period.")
        lines.append("")
        lines.append("**Scope:**")
        lines.append("")
        lines.append(f"- Stores: {_fmt_int(total_stores)}")
        lines.append(f"- Campaigns: {total_campaigns}")
        lines.append(f"- Allocation lines: {_fmt_int(total_allocations)}")
        lines.append(f"- Dispatches: {_fmt_int(total_dispatches)}")
        lines.append(f"- Store confirmations: {_fmt_int(total_confirmations)}")
        lines.append("")
        lines.append("**Process health:**")
        lines.append("")
        lines.append("| KPI | Value |")
        lines.append("|-----|-------|")
        lines.append(
            f"| Campaign readiness rate | {_pct(campaign_readiness)} |"
        )
        lines.append(
            f"| Confirmation completion rate | {_pct(ms.get('confirmation_completion_rate'))} |"
        )
        lines.append(
            f"| Photo proof completion rate | {_pct(ms.get('photo_proof_completion_rate'))} |"
        )
        lines.append(
            f"| Allocation accuracy rate | {_pct(ms.get('allocation_accuracy_rate'))} |"
        )
        lines.append(
            f"| Quantity mismatch rate | {_pct(ms.get('quantity_mismatch_rate'))} |"
        )
        lines.append("")
        lines.append("**Risk and workload:**")
        lines.append("")
        lines.append("| KPI | Value |")
        lines.append("|-----|-------|")
        lines.append(f"| Total exceptions detected | {_fmt_int(er.total)} |")
        lines.append(f"| Open exceptions | {_fmt_int(open_exc)} |")
        lines.append(f"| Critical exceptions | {_fmt_int(er.critical_count)} |")
        lines.append(f"| SLA-breached exceptions | {_fmt_int(sla_breach)} |")
        lines.append(
            f"| Exception rate (per allocation) | {_fmt_ratio(ms.get('exception_rate'))} |"
        )
        lines.append(
            f"| Stockout risk stores | {_fmt_int(ms.get('stockout_risk_count'))} |"
        )
        lines.append(
            f"| Overstock risk stores | {_fmt_int(ms.get('overstock_risk_count'))} |"
        )
        lines.append(f"| Sell-through rate | {_pct(sell_through)} |")
        lines.append(f"| AM follow-up backlog | {_fmt_int(ms.get('am_follow_up_backlog'))} |")
        lines.append("")
        lines.append("**Data quality:**")
        lines.append("")
        lines.append(f"- Validation findings: {_fmt_int(vr.total)} "
                     f"({_fmt_int(vr.critical_count)} critical, "
                     f"{_fmt_int(vr.warning_count)} warning, "
                     f"{_fmt_int(vr.info_count)} info)")
        lines.append("")
        # Executive narrative
        lines.append("**Summary assessment:**")
        lines.append("")
        lines.append(self._executive_narrative())
        return "\n".join(lines)

    def _executive_narrative(self) -> str:
        """Build a 3-4 sentence narrative summarizing the week."""
        ctx = self.context
        ms = ctx.metrics_summary
        er = ctx.exception_report
        sell_through = ms.get("sell_through_rate")
        campaign_readiness = ms.get("campaign_readiness_rate")
        open_exc = int(ms.get("open_exception_count"))
        sla_breach = int(ms.get("sla_breach_count"))

        # Determine overall health signal.
        if campaign_readiness >= 0.85 and sla_breach < 20:
            health = "strong"
        elif campaign_readiness >= 0.70:
            health = "moderate"
        else:
            health = "at-risk"

        parts: list[str] = []
        parts.append(
            f"Campaign execution health is {health} this week. "
            f"Campaign readiness stands at {_pct(campaign_readiness)}, "
            f"with sell-through at {_pct(sell_through)} against a "
            f"{_pct_raw(_SELL_THROUGH_TARGET * 100)} target."
        )
        parts.append(
            f"There are {_fmt_int(open_exc)} open exceptions "
            f"({_fmt_int(er.critical_count)} critical), "
            f"of which {_fmt_int(sla_breach)} have breached SLA."
        )
        stockouts = int(ms.get("stockout_risk_count"))
        overstocks = int(ms.get("overstock_risk_count"))
        if stockouts > 0 or overstocks > 0:
            parts.append(
                f"Inventory risk is elevated: {_fmt_int(stockouts)} stores "
                f"face stockout risk and {_fmt_int(overstocks)} face overstock risk."
            )
        parts.append(
            "Priority actions for this week are listed in Section 7."
        )
        return " ".join(parts)

    # -- section 2: campaign readiness --------------------------------------

    def _section_campaign_readiness(self) -> str:
        ctx = self.context
        ms = ctx.metrics_summary

        lines: list[str] = []
        lines.append("## 2. Campaign Readiness")
        lines.append("")
        lines.append("Campaign readiness measures the fraction of allocation lines "
                     "that have a completed, on-time store confirmation with photo "
                     "proof within the campaign launch window.")
        lines.append("")
        lines.append("**Overall readiness:**")
        lines.append("")
        readiness = ms.get("campaign_readiness_rate")
        lines.append(f"- Campaign readiness rate: **{_pct(readiness)}**")
        lines.append(
            f"- Confirmation completion rate: {_pct(ms.get('confirmation_completion_rate'))}"
        )
        lines.append(
            f"- Photo proof completion rate: {_pct(ms.get('photo_proof_completion_rate'))}"
        )
        lines.append("")

        # Per-campaign breakdown.
        lines.append("**Per-campaign breakdown:**")
        lines.append("")
        lines.append("| Campaign | Type | Start | End | Status |")
        lines.append("|----------|------|-------|-----|--------|")
        for c in ctx.campaigns:
            cid = _safe_get(c, "campaign_id")
            cname = _safe_get(c, "campaign_name")
            ctype = _safe_get(c, "campaign_type")
            start = _safe_get(c, "campaign_start_date")
            end = _safe_get(c, "campaign_end_date")
            status = _safe_get(c, "campaign_status")
            lines.append(f"| {cname} ({cid}) | {ctype} | {start} | {end} | {status} |")
        lines.append("")

        # Launch window analysis.
        lines.append("**Launch window compliance:**")
        lines.append("")
        late_confirms = len(ctx.exception_report.by_type("late_confirmation"))
        missing_confirms = len(ctx.exception_report.by_type("missing_confirmation"))
        late_photos = len(ctx.exception_report.by_type("late_photo_proof"))
        missing_photos = len(ctx.exception_report.by_type("missing_photo_proof"))
        lines.append(f"- Late confirmations (after launch window): {_fmt_int(late_confirms)}")
        lines.append(f"- Missing confirmations (no matching record): {_fmt_int(missing_confirms)}")
        lines.append(f"- Late photo proofs (after launch window): {_fmt_int(late_photos)}")
        lines.append(f"- Missing photo proofs (no proof submitted): {_fmt_int(missing_photos)}")
        lines.append("")

        if late_confirms > 0 or missing_confirms > 0:
            lines.append(
                f"Action needed: {_fmt_int(late_confirms + missing_confirms)} allocations "
                f"require follow-up to achieve full campaign readiness."
            )
        else:
            lines.append("All allocations have on-time confirmations.")
        return "\n".join(lines)

    # -- section 3: allocation reconciliation --------------------------------

    def _section_allocation_reconciliation(self) -> str:
        ctx = self.context
        ms = ctx.metrics_summary
        vr = ctx.validation_report

        lines: list[str] = []
        lines.append("## 3. Allocation Reconciliation")
        lines.append("")
        lines.append("Reconciliation tracks planned vs shipped vs received quantities "
                     "across the allocation, dispatch, and confirmation tables.")
        lines.append("")

        # Summary metrics.
        accuracy = ms.get("allocation_accuracy_rate")
        mismatch = ms.get("quantity_mismatch_rate")
        lines.append("**Accuracy summary:**")
        lines.append("")
        lines.append(f"- Allocation accuracy rate (received == shipped): **{_pct(accuracy)}**")
        lines.append(f"- Quantity mismatch rate: **{_pct(mismatch)}**")
        lines.append("")

        # Validation findings related to reconciliation.
        val04 = sum(1 for f in vr.findings if f.rule_code == "VAL-04")
        val05 = sum(1 for f in vr.findings if f.rule_code == "VAL-05")
        val06 = sum(1 for f in vr.findings if f.rule_code == "VAL-06")
        val07 = sum(1 for f in vr.findings if f.rule_code == "VAL-07")
        lines.append("**Reconciliation findings (T09 validation engine):**")
        lines.append("")
        lines.append("| Rule | Description | Count |")
        lines.append("|------|-------------|-------|")
        lines.append(f"| VAL-04 | Planned vs dispatched variance | {_fmt_int(val04)} |")
        lines.append(f"| VAL-05 | Planned vs received variance | {_fmt_int(val05)} |")
        lines.append(f"| VAL-06 | Dispatch without plan | {_fmt_int(val06)} |")
        lines.append(f"| VAL-07 | Confirmation without dispatch | {_fmt_int(val07)} |")
        lines.append("")

        # Quantity mismatch exceptions.
        qty_mismatch_excs = ctx.exception_report.by_type("quantity_mismatch")
        lines.append(f"**Quantity mismatch exceptions:** {_fmt_int(len(qty_mismatch_excs))}")
        lines.append("")
        if qty_mismatch_excs:
            lines.append("Top 5 quantity mismatches by priority:")
            lines.append("")
            lines.append("| Exception | Store | AM | Shipped | Received | Variance |")
            lines.append("|-----------|-------|----|---------|----------|----------|")
            # Sort by priority score descending.
            sorted_mismatches = sorted(
                qty_mismatch_excs,
                key=lambda e: -e.priority_score,
            )[:5]
            for exc in sorted_mismatches:
                shipped, received, variance = self._extract_qty_from_message(exc.message)
                lines.append(
                    f"| {exc.exception_id} | {exc.store_id} | {exc.area_manager} "
                    f"| {shipped} | {received} | {variance} |"
                )
            lines.append("")

        # Referential integrity.
        val02 = sum(1 for f in vr.findings if f.rule_code == "VAL-02")
        val03 = sum(1 for f in vr.findings if f.rule_code == "VAL-03")
        lines.append("**Referential integrity:**")
        lines.append("")
        lines.append(f"- Duplicate primary keys (VAL-02): {_fmt_int(val02)}")
        lines.append(f"- Orphaned foreign keys (VAL-03): {_fmt_int(val03)}")
        if val02 == 0 and val03 == 0:
            lines.append("- Referential integrity is intact across all tables.")
        lines.append("")
        return "\n".join(lines)

    def _extract_qty_from_message(self, message: str) -> tuple[str, str, str]:
        """Extract shipped/received/variance from a mismatch exception message."""
        shipped = "?"
        received = "?"
        variance = "?"
        import re
        ship_match = re.search(r"shipped=(\d+)", message)
        recv_match = re.search(r"received=(\d+)", message)
        var_match = re.search(r"variance=(-?\d+)", message)
        if ship_match:
            shipped = ship_match.group(1)
        if recv_match:
            received = recv_match.group(1)
        if var_match:
            variance = var_match.group(1)
        return shipped, received, variance

    # -- section 4: exception backlog ---------------------------------------

    def _section_exception_backlog(self) -> str:
        ctx = self.context
        er = ctx.exception_report

        lines: list[str] = []
        lines.append("## 4. Exception Backlog")
        lines.append("")
        lines.append("The exception backlog summarizes all detected exceptions by type, "
                     "severity, and SLA status.")
        lines.append("")

        # By type.
        lines.append("**Exceptions by type:**")
        lines.append("")
        lines.append("| Type | Count | Critical | Owner |")
        lines.append("|------|-------|----------|-------|")
        for exc_type in EXCEPTION_TYPES:
            excs = er.by_type(exc_type)
            if not excs:
                continue
            critical = sum(1 for e in excs if e.severity == "critical")
            # Get owner from first exception or the meta.
            owner = excs[0].owner if excs else ""
            lines.append(
                f"| {exc_type} | {_fmt_int(len(excs))} | {_fmt_int(critical)} | {owner} |"
            )
        lines.append("")

        # By SLA status.
        within = sum(1 for e in er.exceptions if e.sla_status == "within")
        approaching = sum(1 for e in er.exceptions if e.sla_status == "approaching")
        breached = sum(1 for e in er.exceptions if e.sla_status == "breached")
        paused = sum(1 for e in er.exceptions if e.sla_status == "paused")
        lines.append("**SLA aging breakdown:**")
        lines.append("")
        lines.append(f"- Within SLA: {_fmt_int(within)}")
        lines.append(f"- Approaching SLA: {_fmt_int(approaching)}")
        lines.append(f"- Breached SLA: {_fmt_int(breached)}")
        lines.append(f"- Paused: {_fmt_int(paused)}")
        lines.append("")

        # Age distribution.
        lines.append("**Age distribution:**")
        lines.append("")
        age_0_5 = sum(1 for e in er.exceptions if e.age_days <= 5)
        age_6_15 = sum(1 for e in er.exceptions if 6 <= e.age_days <= 15)
        age_16_30 = sum(1 for e in er.exceptions if 16 <= e.age_days <= 30)
        age_30_plus = sum(1 for e in er.exceptions if e.age_days > 30)
        lines.append(f"| Bucket | Count |")
        lines.append(f"|--------|-------|")
        lines.append(f"| 0-5 days (fresh) | {_fmt_int(age_0_5)} |")
        lines.append(f"| 6-15 days (aging) | {_fmt_int(age_6_15)} |")
        lines.append(f"| 16-30 days (overdue) | {_fmt_int(age_16_30)} |")
        lines.append(f"| 30+ days (chronic) | {_fmt_int(age_30_plus)} |")
        lines.append("")

        # Status breakdown.
        lines.append("**Status breakdown:**")
        lines.append("")
        open_statuses = {"open", "in_progress", "raised", "escalated"}
        active = sum(1 for e in er.exceptions if e.status in open_statuses)
        resolved = sum(1 for e in er.exceptions if e.status == "resolved")
        closed = sum(1 for e in er.exceptions if e.status == "closed")
        waived = sum(1 for e in er.exceptions if e.status == "waived")
        paused_status = sum(1 for e in er.exceptions if e.status == "paused")
        lines.append(f"- Active (open/in_progress/raised/escalated): {_fmt_int(active)}")
        lines.append(f"- Resolved: {_fmt_int(resolved)}")
        lines.append(f"- Closed: {_fmt_int(closed)}")
        lines.append(f"- Waived: {_fmt_int(waived)}")
        lines.append(f"- Paused: {_fmt_int(paused_status)}")
        lines.append("")
        return "\n".join(lines)

    # -- section 5: AM/store follow-up list ---------------------------------

    def _section_am_followup(self) -> str:
        ctx = self.context
        am_rows = ctx.am_scorecard

        lines: list[str] = []
        lines.append("## 5. AM / Store Follow-Up List")
        lines.append("")
        lines.append("The area manager scorecard ranks AMs by open exception workload. "
                     "Each AM is responsible for resolving exceptions in their stores.")
        lines.append("")
        lines.append("**Area manager scorecard:**")
        lines.append("")
        lines.append(
            "| AM | Region | Stores | Allocs | Confirms | Open Exc | Critical | "
            "SLA Breach | Stockout | Overstock | Sell-Through | Exc Rate |"
        )
        lines.append(
            "|-----|--------|--------|--------|----------|----------|----------|"
            "------------|----------|-----------|---------------|----------|"
        )
        for row in am_rows:
            lines.append(
                f"| {row.area_manager} | {row.region} | {row.store_count} "
                f"| {row.allocation_count} | {row.confirmation_count} "
                f"| {row.open_exception_count} | {row.critical_count} "
                f"| {row.sla_breach_count} | {row.stockout_risk_count} "
                f"| {row.overstock_risk_count} | {_pct(row.sell_through_rate)} "
                f"| {_fmt_ratio(row.exception_rate)} |"
            )
        lines.append("")

        # Top overloaded AMs.
        if am_rows:
            top_am = am_rows[0]
            lines.append("**Highest workload:**")
            lines.append("")
            lines.append(
                f"- {top_am.area_manager} ({top_am.region}) leads with "
                f"{top_am.open_exception_count} open exceptions across "
                f"{top_am.store_count} stores."
            )
            if len(am_rows) > 1:
                second_am = am_rows[1]
                lines.append(
                    f"- {second_am.area_manager} ({second_am.region}) follows with "
                    f"{second_am.open_exception_count} open exceptions."
                )
            lines.append("")
        return "\n".join(lines)

    # -- section 6: sales / sell-through ------------------------------------

    def _section_sales_sellthrough(self) -> str:
        ctx = self.context
        ms = ctx.metrics_summary

        lines: list[str] = []
        lines.append("## 6. Sales / Sell-Through Note")
        lines.append("")
        lines.append("Sell-through rate measures units sold as a fraction of units "
                     "received. The campaign target is "
                     f"{_pct_raw(_SELL_THROUGH_TARGET * 100)}.")
        lines.append("")

        sell_through = ms.get("sell_through_rate")
        lines.append(f"- Overall sell-through rate: **{_pct(sell_through)}**")
        lines.append(
            f"- Target: {_pct_raw(_SELL_THROUGH_TARGET * 100)}"
        )

        # Compute total units.
        total_sold = sum(
            _to_int_safe(s.get("units_sold")) or 0
            for s in ctx.sales_daily
        )
        total_received = sum(
            _to_int_safe(c.get("received_quantity")) or 0
            for c in ctx.store_confirmations
        )
        lines.append(f"- Total units sold: {_fmt_int(total_sold)}")
        lines.append(f"- Total units received: {_fmt_int(total_received)}")
        lines.append("")

        # Risk signals.
        stockouts = int(ms.get("stockout_risk_count"))
        overstocks = int(ms.get("overstock_risk_count"))
        low_st_excs = ctx.exception_report.by_type("low_sell_through")
        lines.append("**Inventory risk signals:**")
        lines.append("")
        lines.append(f"- Stockout risk stores: {_fmt_int(stockouts)}")
        lines.append(f"- Overstock risk stores: {_fmt_int(overstocks)}")
        lines.append(f"- Low sell-through exceptions: {_fmt_int(len(low_st_excs))}")
        lines.append("")

        # Per-campaign sell-through.
        lines.append("**Per-campaign sell-through:**")
        lines.append("")
        lines.append("| Campaign | Units Sold | Units Received | Sell-Through |")
        lines.append("|----------|------------|----------------|--------------|")
        for c in ctx.campaigns:
            cid = _safe_get(c, "campaign_id")
            cname = _safe_get(c, "campaign_name")
            sold = sum(
                _to_int_safe(s.get("units_sold")) or 0
                for s in ctx.sales_daily
                if _safe_get(s, "campaign_id") == cid
            )
            received = sum(
                _to_int_safe(conf.get("received_quantity")) or 0
                for conf in ctx.store_confirmations
                if _safe_get(conf, "campaign_id") == cid
            )
            st = _safe_divide(sold, received)
            lines.append(
                f"| {cname} | {_fmt_int(sold)} | {_fmt_int(received)} | {_pct(st)} |"
            )
        lines.append("")

        if sell_through < _SELL_THROUGH_TARGET:
            gap = _SELL_THROUGH_TARGET - sell_through
            lines.append(
                f"Sell-through is {_pct(gap)} below the {_pct_raw(_SELL_THROUGH_TARGET * 100)} "
                f"target. Review pricing, display compliance, and inventory positioning."
            )
        else:
            lines.append(
                f"Sell-through exceeds the {_pct_raw(_SELL_THROUGH_TARGET * 100)} target."
            )
        return "\n".join(lines)

    # -- section 7: recommended actions -------------------------------------

    def _section_recommended_actions(self) -> str:
        lines: list[str] = []
        lines.append("## 7. Recommended Actions")
        lines.append("")
        lines.append(
            f"Top {TOP_ACTION_ITEMS} action items for this week, ranked by "
            f"priority score (severity, SLA age, and business impact):"
        )
        lines.append("")
        lines.append(self._top_action_items_table(top_n=TOP_ACTION_ITEMS))
        lines.append("")

        # Strategic recommendations.
        ctx = self.context
        ms = ctx.metrics_summary
        lines.append("**Strategic recommendations:**")
        lines.append("")
        recs = self._strategic_recommendations()
        for i, rec in enumerate(recs, 1):
            lines.append(f"{i}. {rec}")
        return "\n".join(lines)

    def _top_action_items_table(self, top_n: int) -> str:
        """Build the markdown table for the top N action items."""
        lines: list[str] = []
        lines.append("| # | Exception ID | Type | Severity | Store | AM | Age | SLA | Action |")
        lines.append("|---|-------------|------|----------|-------|----|-----|-----|--------|")
        items = self._action_list[:top_n]
        for i, exc in enumerate(items, 1):
            action = exc.recommended_action.replace("|", "/")
            lines.append(
                f"| {i} | {exc.exception_id} | {exc.exception_type} "
                f"| {exc.severity} | {exc.store_id} | {exc.area_manager} "
                f"| {exc.age_days}d | {exc.sla_status} | {action} |"
            )
        return "\n".join(lines)

    def _strategic_recommendations(self) -> list[str]:
        """Generate strategic recommendations based on the data."""
        ctx = self.context
        ms = ctx.metrics_summary
        er = ctx.exception_report
        recs: list[str] = []

        # Stockout risk.
        stockouts = int(ms.get("stockout_risk_count"))
        if stockouts > 0:
            recs.append(
                f"Expedite replenishment for {_fmt_int(stockouts)} stores at "
                f"stockout risk; consider transfers from overstock stores."
            )

        # Overstock risk.
        overstocks = int(ms.get("overstock_risk_count"))
        if overstocks > 0:
            recs.append(
                f"Plan markdowns or inter-store transfers for {_fmt_int(overstocks)} "
                f"stores at overstock risk to free up working capital."
            )

        # SLA breaches.
        sla_breach = int(ms.get("sla_breach_count"))
        if sla_breach > 0:
            recs.append(
                f"Escalate {_fmt_int(sla_breach)} SLA-breached exceptions to "
                f"operations leads for root-cause review this week."
            )

        # Missing confirmations.
        missing_confirms = len(er.by_type("missing_confirmation"))
        if missing_confirms > 0:
            recs.append(
                f"Follow up on {_fmt_int(missing_confirms)} missing store "
                f"confirmations; contact store PICs to verify visit completion."
            )

        # Quantity mismatches.
        qty_mismatches = len(er.by_type("quantity_mismatch"))
        if qty_mismatches > 0:
            recs.append(
                f"Reconcile {_fmt_int(qty_mismatches)} quantity mismatches with "
                f"DC operations; initiate DC count verification for high-variance lines."
            )

        # Low sell-through.
        low_st = len(er.by_type("low_sell_through"))
        if low_st > 0:
            recs.append(
                f"Review pricing and display for {_fmt_int(low_st)} low sell-through "
                f"items; consider promo acceleration or assortment changes."
            )

        # Sell-through below target.
        sell_through = ms.get("sell_through_rate")
        if sell_through < _SELL_THROUGH_TARGET:
            recs.append(
                f"Overall sell-through ({_pct(sell_through)}) is below the "
                f"{_pct_raw(_SELL_THROUGH_TARGET * 100)} target; prioritize hero SKU "
                f"visibility and POSM compliance audits."
            )

        # AM workload balancing.
        if ctx.am_scorecard:
            top_am = ctx.am_scorecard[0]
            if top_am.open_exception_count > 150:
                recs.append(
                    f"Rebalance workload from {top_am.area_manager} "
                    f"({top_am.open_exception_count} open exceptions) to AMs with "
                    f"lighter backlogs."
                )

        # Photo proof gaps.
        missing_photos = len(er.by_type("missing_photo_proof"))
        if missing_photos > 0:
            recs.append(
                f"Request field reps to re-submit {_fmt_int(missing_photos)} missing "
                f"photo proofs within 24 hours."
            )

        if not recs:
            recs.append(
                "No critical actions identified this week. Continue routine monitoring."
            )
        return recs

    # -- section 8: data caveats --------------------------------------------

    def _section_data_caveats(self) -> str:
        ctx = self.context
        vr = ctx.validation_report
        ms = ctx.metrics_summary

        lines: list[str] = []
        lines.append("## 8. Data Caveats")
        lines.append("")
        lines.append("This section documents data quality notes, limitations, and "
                     "assumptions that affect report interpretation.")
        lines.append("")
        lines.append(f"- {SIMULATED_DATA_NOTICE}")
        lines.append(
            f"- Aging date for SLA and exception age calculations: "
            f"{ctx.aging_date.isoformat()}."
        )
        lines.append(
            "- Division-by-zero in rate KPIs returns 0.0 by design (documented "
            "behavior of the T11 metrics engine)."
        )
        lines.append(
            "- Exception status values are simulated; no real workflow state "
            "transitions are tracked."
        )
        lines.append(
            "- Sell-through target of 70% is a configurable default, not a "
            "validated benchmark."
        )
        lines.append("")

        # Validation findings summary.
        lines.append("**Validation findings:**")
        lines.append("")
        lines.append(
            f"- Total findings: {_fmt_int(vr.total)} "
            f"({_fmt_int(vr.critical_count)} critical, "
            f"{_fmt_int(vr.warning_count)} warning, "
            f"{_fmt_int(vr.info_count)} info)"
        )
        if vr.critical_count == 0:
            lines.append(
                "- No critical data quality findings. Referential integrity is intact."
            )
        else:
            lines.append(
                f"- {_fmt_int(vr.critical_count)} critical findings require "
                f"immediate data remediation."
            )

        # Quantity variances caveat.
        val04 = sum(1 for f in vr.findings if f.rule_code == "VAL-04")
        val05 = sum(1 for f in vr.findings if f.rule_code == "VAL-05")
        if val04 > 0 or val05 > 0:
            lines.append(
                f"- Quantity variances (VAL-04: {_fmt_int(val04)}, "
                f"VAL-05: {_fmt_int(val05)}) are by design in the sample data "
                f"generator and feed the quantity_mismatch exception type."
            )
        lines.append("")

        # Tables covered.
        lines.append("**Tables covered:**")
        lines.append("")
        lines.append("| Table | Rows |")
        lines.append("|-------|------|")
        for name in sorted(vr.table_row_counts):
            count = vr.table_row_counts[name]
            lines.append(f"| {name} | {_fmt_int(count)} |")
        lines.append("")

        # Report generation metadata.
        lines.append("**Report generation:**")
        lines.append("")
        lines.append(f"- Report generated: {ctx.aging_date.isoformat()}")
        lines.append(f"- Week ending: {ctx.week_ending.isoformat()}")
        lines.append(
            f"- KPIs computed: {len(ms.kpis)} "
            f"({len(ms.process_kpis)} process, {len(ms.performance_kpis)} performance)"
        )
        lines.append(
            f"- Exception types detected: {len(EXCEPTION_TYPES)}"
        )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers (module-level)
# ---------------------------------------------------------------------------

def _to_int_safe(value: Any) -> int | None:
    """Coerce a value to int, returning None on failure."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None


def _safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divide safely, returning default when denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator


# ---------------------------------------------------------------------------
# Convenience entry points
# ---------------------------------------------------------------------------

def generate_weekly_report(
    tables: dict[str, list[dict[str, Any]]],
    aging_date: date | None = None,
    week_ending: date | None = None,
) -> str:
    """Generate the full weekly operations report as Markdown.

    Parameters:
        tables:       Dict of table name to list of record dicts.
        aging_date:   Date for exception age and SLA calculations.
        week_ending:  Last day of the reporting week.

    Returns:
        The full report as a Markdown string.
    """
    generator = WeeklyReportGenerator(tables, aging_date, week_ending)
    return generator.generate_full_report()


def generate_executive_summary(
    tables: dict[str, list[dict[str, Any]]],
    aging_date: date | None = None,
    week_ending: date | None = None,
) -> str:
    """Generate a short executive summary as Markdown.

    Parameters:
        tables:       Dict of table name to list of record dicts.
        aging_date:   Date for exception age and SLA calculations.
        week_ending:  Last day of the reporting week.

    Returns:
        The executive summary as a Markdown string.
    """
    generator = WeeklyReportGenerator(tables, aging_date, week_ending)
    return generator.generate_executive_summary()
