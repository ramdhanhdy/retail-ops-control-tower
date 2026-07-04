"""Diagnostic insight engine (T13).

Mines the exception table and the raw data tables for quantified,
ranked root-cause findings. Where the exception engine (T10) answers
"what is broken right now", this layer answers "why is it happening,
where is it concentrated, and what is it costing us".

Insight categories (6):

    1. pareto_concentration   - the vital-few stores that drive the bulk
       of the exception backlog (80/20 analysis).
    2. regional_hotspot       - region x exception-type combinations that
       over-index against the store-footprint baseline (lift analysis).
    3. upstream_attribution   - distribution centers and carriers whose
       shipments over-index on quantity mismatches.
    4. execution_sales_gap    - quantified sell-through gap (percentage
       points) between stores with execution failures and clean stores.
    5. field_rep_workload     - field reps whose stores over-index on
       confirmation / photo-proof failures.
    6. rebalancing_opportunity - SKUs with simultaneous stockout-risk and
       overstock-risk stores in the same campaign (transfer candidates).

Every insight carries a deterministic impact score so findings can be
ranked and worked top-down, mirroring the priority-score approach used
by the exception action list.

Design notes:
    - The engine accepts an optional pre-computed ExceptionReport to
      avoid re-running detection (same pattern as MetricsEngine).
    - Pure rule-based arithmetic: shares, lifts, and gaps. No ML, no
      forecasting, consistent with the project scope guard.
    - All computations are deterministic: same input data and aging
      date always produce identical insights in identical order.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any

from retail_ops_control_tower.exceptions import ExceptionEngine, ExceptionReport

# ---------------------------------------------------------------------------
# Registry and thresholds
# ---------------------------------------------------------------------------

INSIGHT_CATEGORIES: list[str] = [
    "pareto_concentration",
    "regional_hotspot",
    "upstream_attribution",
    "execution_sales_gap",
    "field_rep_workload",
    "rebalancing_opportunity",
]

# Pareto: cumulative exception share targeted by the "vital few" analysis.
PARETO_TARGET_SHARE = 0.80

# Pareto: only report if the vital few are at most this fraction of stores.
PARETO_MAX_STORE_SHARE = 0.60

# Lift analyses: minimum observed lift before a group is flagged.
MIN_LIFT = 1.30

# Lift analyses: minimum exceptions in a group before it can be flagged
# (guards against small-sample noise).
MIN_GROUP_EXCEPTIONS = 8

# Execution-vs-sales: minimum sell-through gap (percentage points) to report.
MIN_SELL_THROUGH_GAP_PP = 3.0

# Exception types considered "execution failures" for the sales-gap analysis.
EXECUTION_EXCEPTION_TYPES: frozenset[str] = frozenset(
    {
        "missing_confirmation",
        "late_confirmation",
        "quantity_mismatch",
        "missing_photo_proof",
        "late_photo_proof",
    }
)

# Exception types attributable to field reps.
FIELD_REP_EXCEPTION_TYPES: frozenset[str] = frozenset(
    {
        "missing_confirmation",
        "late_confirmation",
        "missing_photo_proof",
        "late_photo_proof",
    }
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class Insight:
    """A single quantified diagnostic finding.

    Attributes:
        insight_id:      unique sequential ID (INS-NNN).
        category:        one of INSIGHT_CATEGORIES.
        headline:        one-line summary suitable for an executive brief.
        detail:          longer explanation with the supporting numbers.
        metric_name:     name of the primary metric behind the finding.
        metric_value:    observed value of the primary metric.
        baseline_value:  comparison baseline (share, rate, or mean).
        lift:            metric_value / baseline_value (0.0 when undefined).
        affected_count:  number of exceptions (or stores) behind the finding.
        impact_score:    deterministic ranking score (higher = act first).
        recommended_action: codified next step.
        evidence:        compact supporting-data summary string.
    """

    insight_id: str = ""
    category: str = ""
    headline: str = ""
    detail: str = ""
    metric_name: str = ""
    metric_value: float = 0.0
    baseline_value: float = 0.0
    lift: float = 0.0
    affected_count: int = 0
    impact_score: int = 0
    recommended_action: str = ""
    evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class InsightReport:
    """Aggregated result of running the insight engine.

    Attributes:
        insights:   list of Insight, sorted by impact score descending.
        aging_date: ISO date used for the underlying exception detection.
    """

    insights: list[Insight] = field(default_factory=list)
    aging_date: str = ""

    @property
    def total(self) -> int:
        return len(self.insights)

    def by_category(self, category: str) -> list[Insight]:
        return [i for i in self.insights if i.category == category]

    def to_dict(self) -> dict[str, Any]:
        return {
            "aging_date": self.aging_date,
            "total": self.total,
            "insights": [i.to_dict() for i in self.insights],
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _round(value: float, digits: int = 4) -> float:
    return round(value + 0.0, digits)


def _impact_score(affected_count: int, lift: float, critical_count: int) -> int:
    """Deterministic ranking score for an insight.

    score = affected_count * min(lift, 3.0) + critical_count * 2

    - affected_count anchors the score to backlog volume.
    - lift rewards concentration (capped at 3.0 so one extreme group
      cannot dominate purely on ratio).
    - critical exceptions get double weight.
    """
    capped_lift = min(max(lift, 1.0), 3.0)
    return max(1, int(affected_count * capped_lift + critical_count * 2))


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class InsightEngine:
    """Generates ranked diagnostic insights from processed data.

    Parameters:
        tables:           Dict mapping table name to list of record dicts,
                          as produced by read_all_csv_tables.
        aging_date:       Date used for exception age calculations.
                          Defaults to today.
        exception_report: Pre-computed ExceptionReport. If None, the engine
                          runs ExceptionEngine internally to produce one.
    """

    def __init__(
        self,
        tables: dict[str, list[dict[str, Any]]],
        aging_date: date | None = None,
        exception_report: ExceptionReport | None = None,
    ) -> None:
        self.tables = tables
        self.aging_date = aging_date or date.today()

        if exception_report is not None:
            self._report = exception_report
        else:
            engine = ExceptionEngine(tables, self.aging_date)
            self._report = engine.detect()

        self._insights: list[Insight] = []
        self._seq = 0

        # Lookup indexes.
        self._stores: dict[str, dict] = {
            str(s.get("store_id", "")): s
            for s in tables.get("stores", [])
            if s.get("store_id")
        }
        self._dispatch_by_alloc: dict[str, dict] = {}
        for d in tables.get("dispatch", []):
            aid = str(d.get("allocation_id", ""))
            if aid:
                self._dispatch_by_alloc[aid] = d

    # -- public API ---------------------------------------------------------

    def generate(self) -> InsightReport:
        """Run all 6 insight analyses and return a ranked InsightReport."""
        self._insights = []
        self._seq = 0

        self._analyze_pareto_concentration()
        self._analyze_regional_hotspots()
        self._analyze_upstream_attribution()
        self._analyze_execution_sales_gap()
        self._analyze_field_rep_workload()
        self._analyze_rebalancing_opportunity()

        # Rank: impact score descending; category then headline as
        # deterministic tie-breakers. IDs are re-assigned post-sort so
        # INS-001 is always the top finding.
        self._insights.sort(
            key=lambda i: (-i.impact_score, i.category, i.headline)
        )
        for idx, insight in enumerate(self._insights, start=1):
            insight.insight_id = f"INS-{idx:03d}"

        return InsightReport(
            insights=self._insights,
            aging_date=self.aging_date.isoformat(),
        )

    # -- shared helpers -----------------------------------------------------

    def _add(self, insight: Insight) -> None:
        self._insights.append(insight)

    def _exceptions(self) -> list:
        return self._report.exceptions

    # -- 1. Pareto concentration --------------------------------------------

    def _analyze_pareto_concentration(self) -> None:
        """Find the smallest set of stores driving PARETO_TARGET_SHARE of
        exceptions. Reported when that set is a minority of stores."""
        exceptions = [e for e in self._exceptions() if e.store_id]
        total = len(exceptions)
        store_universe = len(self._stores)
        if total == 0 or store_universe == 0:
            return

        counts: dict[str, int] = {}
        critical: dict[str, int] = {}
        for e in exceptions:
            counts[e.store_id] = counts.get(e.store_id, 0) + 1
            if e.severity == "critical":
                critical[e.store_id] = critical.get(e.store_id, 0) + 1

        # Sort stores by exception count desc, store_id asc for determinism.
        ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

        cumulative = 0
        vital_few: list[tuple[str, int]] = []
        for store_id, count in ranked:
            cumulative += count
            vital_few.append((store_id, count))
            if cumulative / total >= PARETO_TARGET_SHARE:
                break

        store_share = len(vital_few) / store_universe
        if store_share > PARETO_MAX_STORE_SHARE:
            return

        exception_share = cumulative / total
        critical_in_set = sum(critical.get(sid, 0) for sid, _ in vital_few)
        top5 = ", ".join(
            f"{sid} ({cnt})" for sid, cnt in vital_few[:5]
        )
        lift = (
            (exception_share / store_share) if store_share > 0 else 0.0
        )
        self._add(Insight(
            category="pareto_concentration",
            headline=(
                f"{len(vital_few)} of {store_universe} stores "
                f"({store_share:.0%}) drive {exception_share:.0%} "
                f"of all exceptions"
            ),
            detail=(
                f"{len(vital_few)} stores account for {cumulative} of "
                f"{total} exceptions ({exception_share:.0%}). Exception "
                f"workload is {lift:.1f}x more concentrated than the "
                f"store footprint. Fixing the top stores first yields "
                f"outsized backlog reduction."
            ),
            metric_name="exception_share_of_vital_few",
            metric_value=_round(exception_share),
            baseline_value=_round(store_share),
            lift=_round(lift, 2),
            affected_count=cumulative,
            impact_score=_impact_score(cumulative, lift, critical_in_set),
            recommended_action=(
                "Assign a dedicated task force to the vital-few stores; "
                "run root-cause review per store before the next campaign "
                "phase."
            ),
            evidence=f"Top stores: {top5}",
        ))

    # -- 2. Regional hotspots -------------------------------------------------

    def _analyze_regional_hotspots(self) -> None:
        """Flag region x exception-type cells whose share of that exception
        type over-indexes the region's share of the store footprint."""
        store_universe = len(self._stores)
        if store_universe == 0:
            return

        region_store_share: dict[str, float] = {}
        for store in self._stores.values():
            region = str(store.get("region", ""))
            if region:
                region_store_share[region] = (
                    region_store_share.get(region, 0.0) + 1.0
                )
        for region in region_store_share:
            region_store_share[region] /= store_universe

        # Group exceptions by (type, region).
        by_type: dict[str, dict[str, list]] = {}
        for e in self._exceptions():
            if not e.region:
                continue
            by_type.setdefault(e.exception_type, {}).setdefault(
                e.region, []
            ).append(e)

        for exc_type in sorted(by_type):
            regions = by_type[exc_type]
            type_total = sum(len(v) for v in regions.values())
            if type_total == 0:
                continue
            for region in sorted(regions):
                group = regions[region]
                baseline = region_store_share.get(region, 0.0)
                if baseline <= 0 or len(group) < MIN_GROUP_EXCEPTIONS:
                    continue
                share = len(group) / type_total
                lift = share / baseline
                if lift < MIN_LIFT:
                    continue
                critical_count = sum(
                    1 for e in group if e.severity == "critical"
                )
                self._add(Insight(
                    category="regional_hotspot",
                    headline=(
                        f"{region} region over-indexes {lift:.1f}x on "
                        f"{exc_type.replace('_', ' ')}"
                    ),
                    detail=(
                        f"{region} holds {baseline:.0%} of stores but "
                        f"generates {share:.0%} of {exc_type} exceptions "
                        f"({len(group)} of {type_total}). A {lift:.1f}x "
                        f"lift indicates a localized process gap rather "
                        f"than a systemic one."
                    ),
                    metric_name=f"{exc_type}_share_in_region",
                    metric_value=_round(share),
                    baseline_value=_round(baseline),
                    lift=_round(lift, 2),
                    affected_count=len(group),
                    impact_score=_impact_score(
                        len(group), lift, critical_count
                    ),
                    recommended_action=(
                        f"Brief the {region} regional lead; audit the "
                        f"local workflow behind {exc_type.replace('_', ' ')} "
                        f"and retrain if needed."
                    ),
                    evidence=(
                        f"{len(group)}/{type_total} {exc_type} exceptions "
                        f"in {region}; store share {baseline:.0%}"
                    ),
                ))

    # -- 3. Upstream attribution ----------------------------------------------

    def _analyze_upstream_attribution(self) -> None:
        """Attribute quantity mismatches to DCs and carriers whose share of
        mismatches over-indexes their share of shipments."""
        mismatches = [
            e for e in self._exceptions()
            if e.exception_type == "quantity_mismatch" and e.allocation_id
        ]
        dispatch_rows = list(self._dispatch_by_alloc.values())
        if not mismatches or not dispatch_rows:
            return

        for dim, label in (("dc_id", "DC"), ("carrier", "carrier")):
            shipment_counts: dict[str, int] = {}
            for d in dispatch_rows:
                key = str(d.get(dim, ""))
                if key:
                    shipment_counts[key] = shipment_counts.get(key, 0) + 1
            total_shipments = sum(shipment_counts.values())
            if total_shipments == 0:
                continue

            mismatch_groups: dict[str, list] = {}
            for e in mismatches:
                dispatch = self._dispatch_by_alloc.get(e.allocation_id)
                if not dispatch:
                    continue
                key = str(dispatch.get(dim, ""))
                if key:
                    mismatch_groups.setdefault(key, []).append(e)
            total_mismatches = sum(
                len(v) for v in mismatch_groups.values()
            )
            if total_mismatches == 0:
                continue

            for key in sorted(mismatch_groups):
                group = mismatch_groups[key]
                if len(group) < MIN_GROUP_EXCEPTIONS:
                    continue
                mismatch_share = len(group) / total_mismatches
                shipment_share = shipment_counts.get(key, 0) / total_shipments
                if shipment_share <= 0:
                    continue
                lift = mismatch_share / shipment_share
                if lift < MIN_LIFT:
                    continue
                critical_count = sum(
                    1 for e in group if e.severity == "critical"
                )
                self._add(Insight(
                    category="upstream_attribution",
                    headline=(
                        f"{label} {key} over-indexes {lift:.1f}x on "
                        f"quantity mismatches"
                    ),
                    detail=(
                        f"{label} {key} handles {shipment_share:.0%} of "
                        f"shipments but accounts for {mismatch_share:.0%} "
                        f"of quantity mismatches ({len(group)} of "
                        f"{total_mismatches}). The variance likely "
                        f"originates upstream of the store."
                    ),
                    metric_name=f"mismatch_share_by_{dim}",
                    metric_value=_round(mismatch_share),
                    baseline_value=_round(shipment_share),
                    lift=_round(lift, 2),
                    affected_count=len(group),
                    impact_score=_impact_score(
                        len(group), lift, critical_count
                    ),
                    recommended_action=(
                        f"Initiate a pick-pack audit with {label} {key}; "
                        f"compare carton counts against shipped "
                        f"quantities for recent dispatches."
                    ),
                    evidence=(
                        f"{len(group)}/{total_mismatches} mismatches vs "
                        f"{shipment_share:.0%} shipment share"
                    ),
                ))

    # -- 4. Execution vs sales ------------------------------------------------

    def _analyze_execution_sales_gap(self) -> None:
        """Quantify the sell-through gap between stores with execution
        failures and clean stores."""
        flagged_stores: set[str] = set()
        exception_count = 0
        critical_count = 0
        for e in self._exceptions():
            if e.exception_type in EXECUTION_EXCEPTION_TYPES and e.store_id:
                flagged_stores.add(e.store_id)
                exception_count += 1
                if e.severity == "critical":
                    critical_count += 1
        if not flagged_stores:
            return

        received: dict[str, float] = {}
        for c in self.tables.get("store_confirmations", []):
            sid = str(c.get("store_id", ""))
            qty = _to_float(c.get("received_quantity"))
            if sid and qty is not None:
                received[sid] = received.get(sid, 0.0) + qty

        sold: dict[str, float] = {}
        for s in self.tables.get("sales_daily", []):
            sid = str(s.get("store_id", ""))
            qty = _to_float(s.get("units_sold"))
            if sid and qty is not None:
                sold[sid] = sold.get(sid, 0.0) + qty

        flagged_rates: list[float] = []
        clean_rates: list[float] = []
        for sid in sorted(self._stores):
            recv = received.get(sid, 0.0)
            if recv <= 0:
                continue
            rate = sold.get(sid, 0.0) / recv
            if sid in flagged_stores:
                flagged_rates.append(rate)
            else:
                clean_rates.append(rate)
        if not flagged_rates or not clean_rates:
            return

        flagged_mean = sum(flagged_rates) / len(flagged_rates)
        clean_mean = sum(clean_rates) / len(clean_rates)
        gap_pp = (clean_mean - flagged_mean) * 100
        if gap_pp < MIN_SELL_THROUGH_GAP_PP:
            return

        lift = (clean_mean / flagged_mean) if flagged_mean > 0 else 0.0
        self._add(Insight(
            category="execution_sales_gap",
            headline=(
                f"Stores with execution failures sell through "
                f"{gap_pp:.1f}pp worse than clean stores"
            ),
            detail=(
                f"{len(flagged_rates)} stores with execution exceptions "
                f"(missing/late confirmations, photo proofs, or quantity "
                f"mismatches) average {flagged_mean:.1%} sell-through vs "
                f"{clean_mean:.1%} for {len(clean_rates)} clean stores - "
                f"a {gap_pp:.1f} percentage-point gap. Execution "
                f"discipline is directly correlated with campaign sales "
                f"outcomes."
            ),
            metric_name="sell_through_gap_pp",
            metric_value=_round(flagged_mean),
            baseline_value=_round(clean_mean),
            lift=_round(lift, 2),
            affected_count=len(flagged_rates),
            impact_score=_impact_score(
                exception_count, lift, critical_count
            ),
            recommended_action=(
                "Use the sell-through gap to prioritize execution "
                "follow-ups; quantify recovered revenue when presenting "
                "the exception backlog to leadership."
            ),
            evidence=(
                f"flagged {flagged_mean:.1%} (n={len(flagged_rates)}) vs "
                f"clean {clean_mean:.1%} (n={len(clean_rates)})"
            ),
        ))

    # -- 5. Field rep workload --------------------------------------------------

    def _analyze_field_rep_workload(self) -> None:
        """Flag field reps whose stores over-index on confirmation and
        photo-proof failures relative to their store coverage."""
        rep_store_counts: dict[str, int] = {}
        for store in self._stores.values():
            rep = str(store.get("field_rep", ""))
            if rep:
                rep_store_counts[rep] = rep_store_counts.get(rep, 0) + 1
        total_stores = sum(rep_store_counts.values())
        if total_stores == 0:
            return

        rep_groups: dict[str, list] = {}
        for e in self._exceptions():
            if e.exception_type not in FIELD_REP_EXCEPTION_TYPES:
                continue
            store = self._stores.get(e.store_id)
            if not store:
                continue
            rep = str(store.get("field_rep", ""))
            if rep:
                rep_groups.setdefault(rep, []).append(e)
        total_rep_exceptions = sum(len(v) for v in rep_groups.values())
        if total_rep_exceptions == 0:
            return

        for rep in sorted(rep_groups):
            group = rep_groups[rep]
            if len(group) < MIN_GROUP_EXCEPTIONS:
                continue
            exc_share = len(group) / total_rep_exceptions
            store_share = rep_store_counts.get(rep, 0) / total_stores
            if store_share <= 0:
                continue
            lift = exc_share / store_share
            if lift < MIN_LIFT:
                continue
            critical_count = sum(
                1 for e in group if e.severity == "critical"
            )
            self._add(Insight(
                category="field_rep_workload",
                headline=(
                    f"Field rep {rep} over-indexes {lift:.1f}x on "
                    f"proof and confirmation failures"
                ),
                detail=(
                    f"Rep {rep} covers {store_share:.0%} of stores but "
                    f"accounts for {exc_share:.0%} of confirmation and "
                    f"photo-proof exceptions ({len(group)} of "
                    f"{total_rep_exceptions}). This may indicate route "
                    f"overload, training needs, or coverage gaps."
                ),
                metric_name="field_rep_exception_share",
                metric_value=_round(exc_share),
                baseline_value=_round(store_share),
                lift=_round(lift, 2),
                affected_count=len(group),
                impact_score=_impact_score(len(group), lift, critical_count),
                recommended_action=(
                    f"Review {rep}'s route load and visit schedule; "
                    f"rebalance store coverage or provide refresher "
                    f"training on proof submission."
                ),
                evidence=(
                    f"{len(group)}/{total_rep_exceptions} rep-attributable "
                    f"exceptions vs {store_share:.0%} store coverage"
                ),
            ))


    # -- 6. Rebalancing opportunity ---------------------------------------------

    def _analyze_rebalancing_opportunity(self) -> None:
        """Find SKUs within a campaign that simultaneously have
        stockout-risk stores and overstock-risk stores. Those SKUs are
        candidates for store-to-store transfers instead of new intake
        or markdowns."""
        stockout: dict[tuple[str, str], list] = {}
        overstock: dict[tuple[str, str], list] = {}
        for e in self._exceptions():
            if not (e.campaign_id and e.sku and e.store_id):
                continue
            key = (e.campaign_id, e.sku)
            if e.exception_type == "stockout_risk":
                stockout.setdefault(key, []).append(e)
            elif e.exception_type == "overstock_risk":
                overstock.setdefault(key, []).append(e)

        matched = sorted(set(stockout) & set(overstock))
        if not matched:
            return

        # One insight per campaign for actionable granularity.
        by_campaign: dict[str, list[tuple[str, str]]] = {}
        for key in matched:
            by_campaign.setdefault(key[0], []).append(key)

        for campaign_id in sorted(by_campaign):
            keys = by_campaign[campaign_id]
            exceptions = [
                e for key in keys for e in stockout[key] + overstock[key]
            ]
            stockout_stores = len(
                {e.store_id for key in keys for e in stockout[key]}
            )
            overstock_stores = len(
                {e.store_id for key in keys for e in overstock[key]}
            )
            critical_count = sum(
                1 for e in exceptions if e.severity == "critical"
            )
            top_skus = sorted(
                keys,
                key=lambda k: -(len(stockout[k]) + len(overstock[k])),
            )[:5]
            sku_list = ", ".join(k[1] for k in top_skus)
            self._add(Insight(
                category="rebalancing_opportunity",
                headline=(
                    f"{len(keys)} SKUs in {campaign_id} have both "
                    f"stockout and overstock stores - transfer candidates"
                ),
                detail=(
                    f"In campaign {campaign_id}, {len(keys)} SKUs have "
                    f"{stockout_stores} stores at stockout risk while "
                    f"{overstock_stores} stores hold excess inventory of "
                    f"the same SKU. Store-to-store transfers can resolve "
                    f"both exposures without new intake or markdowns."
                ),
                metric_name="rebalancing_sku_count",
                metric_value=float(len(keys)),
                baseline_value=0.0,
                lift=0.0,
                affected_count=len(exceptions),
                impact_score=_impact_score(
                    len(exceptions), 1.0, critical_count
                ),
                recommended_action=(
                    "Generate a transfer shortlist pairing stockout and "
                    "overstock stores per SKU; validate against transit "
                    "time before the campaign window closes."
                ),
                evidence=(
                    f"Top SKUs by combined exposure: {sku_list}"
                ),
            ))


# ---------------------------------------------------------------------------
# Convenience API
# ---------------------------------------------------------------------------

def generate_insights(
    tables: dict[str, list[dict[str, Any]]],
    aging_date: date | None = None,
    exception_report: ExceptionReport | None = None,
) -> InsightReport:
    """Run the insight engine and return a ranked InsightReport."""
    engine = InsightEngine(tables, aging_date, exception_report)
    return engine.generate()


def build_insights_markdown(report: InsightReport) -> str:
    """Render an InsightReport as a human-readable markdown brief."""
    lines: list[str] = []
    lines.append("# Diagnostic Insights")
    lines.append("")
    lines.append(
        f"Generated from exception data aged as of "
        f"**{report.aging_date}**. {report.total} ranked findings."
    )
    lines.append("")
    lines.append(
        "> Simulated data. Findings illustrate the diagnostic method, "
        "not any real retailer."
    )
    lines.append("")

    if not report.insights:
        lines.append("No findings met the reporting thresholds.")
        lines.append("")
        return "\n".join(lines)

    lines.append("## Headline findings")
    lines.append("")
    for insight in report.insights[:5]:
        lines.append(f"- **{insight.headline}** ({insight.insight_id})")
    lines.append("")

    category_titles = {
        "pareto_concentration": "Concentration analysis (Pareto)",
        "regional_hotspot": "Regional hotspots",
        "upstream_attribution": "Upstream attribution (DC / carrier)",
        "execution_sales_gap": "Execution-to-sales linkage",
        "field_rep_workload": "Field rep workload",
        "rebalancing_opportunity": "Inventory rebalancing opportunities",
    }
    for category in INSIGHT_CATEGORIES:
        findings = report.by_category(category)
        if not findings:
            continue
        lines.append(f"## {category_titles[category]}")
        lines.append("")
        for insight in findings:
            lines.append(f"### {insight.insight_id}: {insight.headline}")
            lines.append("")
            lines.append(insight.detail)
            lines.append("")
            lines.append(f"- **Impact score:** {insight.impact_score}")
            lines.append(f"- **Affected:** {insight.affected_count}")
            lines.append(f"- **Lift:** {insight.lift:.2f}x")
            lines.append(f"- **Evidence:** {insight.evidence}")
            lines.append(
                f"- **Recommended action:** {insight.recommended_action}"
            )
            lines.append("")

    return "\n".join(lines)
