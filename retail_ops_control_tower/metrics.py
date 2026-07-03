"""KPI metrics layer (T11).

Computes dashboard-ready KPIs from the 8 processed data tables and the
T10 exception report. KPIs are split into two categories:

Process KPIs (execution quality):
    1. campaign_readiness_rate       - fraction of allocations fully ready
                                       at campaign launch.
    2. confirmation_completion_rate   - fraction of dispatches with a
                                       matching store confirmation.
    3. photo_proof_completion_rate    - fraction of confirmations with at
                                       least one photo proof.
    4. allocation_accuracy_rate       - fraction of confirmations where
                                       received quantity exactly matches
                                       shipped quantity.
    5. quantity_mismatch_rate         - fraction of confirmations with a
                                       received-vs-shipped variance.

Performance KPIs (risk and workload):
    6. exception_rate                  - total exceptions per allocation.
    7. open_exception_count            - count of active exceptions.
    8. sla_breach_count                - count of SLA-breached exceptions.
    9. sell_through_rate               - units sold / units received.
    10. stockout_risk_count            - count of stockout risk exceptions.
    11. overstock_risk_count           - count of overstock risk exceptions.
    12. am_follow_up_backlog           - active exceptions assigned to area
                                        managers for follow-up.

All rate KPIs (campaign_readiness_rate, confirmation_completion_rate,
photo_proof_completion_rate, allocation_accuracy_rate,
quantity_mismatch_rate, sell_through_rate) are stored as ratios where
0.0 = 0% and 1.0 = 100%.

exception_rate is stored as a ratio (exceptions per allocation, may
exceed 1.0).

All count KPIs (open_exception_count, sla_breach_count,
stockout_risk_count, overstock_risk_count, am_follow_up_backlog) are
stored as whole numbers.

Design notes:
    - The engine accepts an optional pre-computed ExceptionReport to avoid
      re-running detection. If none is provided, it runs the ExceptionEngine
      internally so exception-based KPIs stay consistent with exceptions.csv.
    - Division-by-zero returns 0.0 for rate KPIs (documented behavior).
    - Missing campaign or store data causes the affected records to be
      excluded from the relevant KPI's numerator and denominator.
    - All computations are deterministic: same input always produces the
      same output.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from retail_ops_control_tower.exceptions import ExceptionEngine, ExceptionReport


# ---------------------------------------------------------------------------
# KPI registry
# ---------------------------------------------------------------------------

PROCESS_KPIS: list[str] = [
    "campaign_readiness_rate",
    "confirmation_completion_rate",
    "photo_proof_completion_rate",
    "allocation_accuracy_rate",
    "quantity_mismatch_rate",
]

PERFORMANCE_KPIS: list[str] = [
    "exception_rate",
    "open_exception_count",
    "sla_breach_count",
    "sell_through_rate",
    "stockout_risk_count",
    "overstock_risk_count",
    "am_follow_up_backlog",
]

ALL_KPIS: list[str] = PROCESS_KPIS + PERFORMANCE_KPIS

# Active exception statuses (mirrors ExceptionEngine.build_action_list).
ACTIVE_STATUSES: frozenset[str] = frozenset(
    {"open", "in_progress", "raised", "escalated"}
)

# KPI metadata: category, unit, and human-readable description.
KPI_META: dict[str, dict[str, str]] = {
    "campaign_readiness_rate": {
        "category": "process",
        "unit": "ratio",
        "description": (
            "Fraction of allocations with a completed, on-time "
            "confirmation and photo proof within the campaign "
            "launch window."
        ),
    },
    "confirmation_completion_rate": {
        "category": "process",
        "unit": "ratio",
        "description": (
            "Fraction of dispatch records that have a matching "
            "store confirmation."
        ),
    },
    "photo_proof_completion_rate": {
        "category": "process",
        "unit": "ratio",
        "description": (
            "Fraction of store confirmations with at least one "
            "photo proof record."
        ),
    },
    "allocation_accuracy_rate": {
        "category": "process",
        "unit": "ratio",
        "description": (
            "Fraction of confirmations where received quantity "
            "exactly matches shipped quantity."
        ),
    },
    "quantity_mismatch_rate": {
        "category": "process",
        "unit": "ratio",
        "description": (
            "Fraction of confirmations where received quantity "
            "differs from shipped quantity."
        ),
    },
    "exception_rate": {
        "category": "performance",
        "unit": "ratio",
        "description": "Total detected exceptions per allocation.",
    },
    "open_exception_count": {
        "category": "performance",
        "unit": "count",
        "description": (
            "Number of exceptions with an active status (open, "
            "in_progress, raised, escalated)."
        ),
    },
    "sla_breach_count": {
        "category": "performance",
        "unit": "count",
        "description": "Number of exceptions whose SLA status is breached.",
    },
    "sell_through_rate": {
        "category": "performance",
        "unit": "ratio",
        "description": (
            "Total units sold divided by total units received "
            "across all stores and SKUs."
        ),
    },
    "stockout_risk_count": {
        "category": "performance",
        "unit": "count",
        "description": "Number of stockout risk exceptions detected.",
    },
    "overstock_risk_count": {
        "category": "performance",
        "unit": "count",
        "description": "Number of overstock risk exceptions detected.",
    },
    "am_follow_up_backlog": {
        "category": "performance",
        "unit": "count",
        "description": (
            "Number of active exceptions assigned to area managers "
            "for follow-up."
        ),
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class KPIResult:
    """A single computed KPI value.

    Attributes:
        name:        KPI identifier (matches a key in ALL_KPIS).
        category:    "process" or "performance".
        value:       The computed numeric value.
        unit:        "ratio" or "count".
        description: Human-readable description of what the KPI measures.
    """

    name: str
    category: str
    value: float
    unit: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MetricsSummary:
    """Aggregated KPI summary for the dashboard.

    Attributes:
        aging_date: ISO date string used for age calculations.
        kpis:       Dict mapping KPI name to KPIResult.
    """

    aging_date: str = ""
    kpis: dict[str, KPIResult] = field(default_factory=dict)

    @property
    def process_kpis(self) -> list[KPIResult]:
        """Process KPIs in canonical order."""
        return [self.kpis[n] for n in PROCESS_KPIS if n in self.kpis]

    @property
    def performance_kpis(self) -> list[KPIResult]:
        """Performance KPIs in canonical order."""
        return [self.kpis[n] for n in PERFORMANCE_KPIS if n in self.kpis]

    def get(self, name: str) -> float:
        """Get a KPI value by name. Returns 0.0 if not found."""
        result = self.kpis.get(name)
        return result.value if result is not None else 0.0

    def to_rows(self) -> list[dict[str, Any]]:
        """Return KPI rows (one dict per KPI) for CSV output.

        Each dict has keys: kpi_name, category, value, unit, description.
        """
        rows: list[dict[str, Any]] = []
        for name in ALL_KPIS:
            if name in self.kpis:
                k = self.kpis[name]
                rows.append(
                    {
                        "kpi_name": k.name,
                        "category": k.category,
                        "value": k.value,
                        "unit": k.unit,
                        "description": k.description,
                    }
                )
        return rows

    def to_dict(self) -> dict[str, Any]:
        return {
            "aging_date": self.aging_date,
            "kpis": [k.to_dict() for k in self.kpis.values()],
        }


@dataclass
class AMScorecardRow:
    """One row in the area manager scorecard.

    Attributes:
        area_manager:          Area manager name.
        region:                Geographic region.
        store_count:           Number of stores under this AM.
        allocation_count:      Number of allocations for this AM's stores.
        confirmation_count:    Number of confirmations for this AM's stores.
        open_exception_count:   Active exceptions for this AM.
        critical_count:        Critical-severity exceptions for this AM.
        sla_breach_count:      SLA-breached exceptions for this AM.
        stockout_risk_count:   Stockout risk exceptions for this AM.
        overstock_risk_count:  Overstock risk exceptions for this AM.
        am_follow_up_backlog:  Active exceptions requiring AM follow-up.
        sell_through_rate:     Units sold / units received for this AM.
        exception_rate:        Total exceptions / allocations for this AM.
    """

    area_manager: str = ""
    region: str = ""
    store_count: int = 0
    allocation_count: int = 0
    confirmation_count: int = 0
    open_exception_count: int = 0
    critical_count: int = 0
    sla_breach_count: int = 0
    stockout_risk_count: int = 0
    overstock_risk_count: int = 0
    am_follow_up_backlog: int = 0
    sell_through_rate: float = 0.0
    exception_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_int(value: Any) -> int | None:
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


def _to_float(value: Any) -> float | None:
    """Coerce a value to float, returning None on failure."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_date(value: Any) -> date | None:
    """Parse a value into a date object.

    Handles ISO date strings, ISO datetime strings, date objects, and
    datetime objects. Returns None if the value cannot be parsed.
    """
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    try:
        return date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None


def _safe_divide(
    numerator: float, denominator: float, default: float = 0.0
) -> float:
    """Divide safely, returning ``default`` when denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class MetricsEngine:
    """Computes dashboard-ready KPIs from processed data.

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

        # Build lookup indexes for efficient cross-referencing.
        self._stores: dict[str, dict] = {
            str(s.get("store_id", "")): s
            for s in tables.get("stores", [])
            if s.get("store_id")
        }
        self._campaigns: dict[str, dict] = {
            str(c.get("campaign_id", "")): c
            for c in tables.get("campaigns", [])
            if c.get("campaign_id")
        }
        self._dispatch_by_alloc: dict[str, dict] = {}
        for d in tables.get("dispatch", []):
            aid = str(d.get("allocation_id", ""))
            if aid:
                self._dispatch_by_alloc[aid] = d
        self._confirmations_by_alloc: dict[str, list[dict]] = {}
        for c in tables.get("store_confirmations", []):
            aid = str(c.get("allocation_id", ""))
            if aid:
                self._confirmations_by_alloc.setdefault(aid, []).append(c)
        self._photos_by_confirmation: dict[str, list[dict]] = {}
        for p in tables.get("photo_proofs", []):
            cid = str(p.get("confirmation_id", ""))
            if cid:
                self._photos_by_confirmation.setdefault(cid, []).append(p)

    # -- public API ---------------------------------------------------------

    def compute(self) -> MetricsSummary:
        """Compute all 12 KPIs and return a MetricsSummary."""
        kpis: dict[str, KPIResult] = {}

        # Process KPIs
        kpis["campaign_readiness_rate"] = self._make_kpi(
            "campaign_readiness_rate", self._campaign_readiness_rate()
        )
        kpis["confirmation_completion_rate"] = self._make_kpi(
            "confirmation_completion_rate",
            self._confirmation_completion_rate(),
        )
        kpis["photo_proof_completion_rate"] = self._make_kpi(
            "photo_proof_completion_rate",
            self._photo_proof_completion_rate(),
        )
        kpis["allocation_accuracy_rate"] = self._make_kpi(
            "allocation_accuracy_rate", self._allocation_accuracy_rate()
        )
        kpis["quantity_mismatch_rate"] = self._make_kpi(
            "quantity_mismatch_rate", self._quantity_mismatch_rate()
        )

        # Performance KPIs
        kpis["exception_rate"] = self._make_kpi(
            "exception_rate", self._exception_rate()
        )
        kpis["open_exception_count"] = self._make_kpi(
            "open_exception_count", self._open_exception_count()
        )
        kpis["sla_breach_count"] = self._make_kpi(
            "sla_breach_count", self._sla_breach_count()
        )
        kpis["sell_through_rate"] = self._make_kpi(
            "sell_through_rate", self._sell_through_rate()
        )
        kpis["stockout_risk_count"] = self._make_kpi(
            "stockout_risk_count", self._stockout_risk_count()
        )
        kpis["overstock_risk_count"] = self._make_kpi(
            "overstock_risk_count", self._overstock_risk_count()
        )
        kpis["am_follow_up_backlog"] = self._make_kpi(
            "am_follow_up_backlog", self._am_follow_up_backlog()
        )

        return MetricsSummary(
            aging_date=self.aging_date.isoformat(), kpis=kpis
        )

    def compute_am_scorecard(self) -> list[AMScorecardRow]:
        """Build per-area-manager scorecard rows, sorted by open
        exception count (descending) then area manager name.
        """
        # Group stores by area manager.
        am_stores: dict[str, list[str]] = {}
        am_regions: dict[str, str] = {}
        for store_id, store in self._stores.items():
            am = str(store.get("area_manager", ""))
            if not am:
                continue
            am_stores.setdefault(am, []).append(store_id)
            am_regions[am] = str(store.get("region", ""))

        # Group exceptions by area manager.
        am_exceptions: dict[str, list] = {}
        for exc in self._report.exceptions:
            am = exc.area_manager
            if am:
                am_exceptions.setdefault(am, []).append(exc)

        # Count allocations per AM (via store lookup).
        am_allocations: dict[str, int] = {}
        for alloc in self.tables.get("allocation_plan", []):
            store_id = str(alloc.get("store_id", ""))
            store = self._stores.get(store_id)
            if not store:
                continue
            am = str(store.get("area_manager", ""))
            if am:
                am_allocations[am] = am_allocations.get(am, 0) + 1

        # Count confirmations per AM (via store lookup).
        am_confirmations: dict[str, int] = {}
        for conf in self.tables.get("store_confirmations", []):
            store_id = str(conf.get("store_id", ""))
            store = self._stores.get(store_id)
            if not store:
                continue
            am = str(store.get("area_manager", ""))
            if am:
                am_confirmations[am] = am_confirmations.get(am, 0) + 1

        # Sum units sold per AM (via store lookup).
        am_units_sold: dict[str, int] = {}
        for sale in self.tables.get("sales_daily", []):
            store_id = str(sale.get("store_id", ""))
            store = self._stores.get(store_id)
            if not store:
                continue
            am = str(store.get("area_manager", ""))
            if am:
                sold = _to_int(sale.get("units_sold")) or 0
                am_units_sold[am] = am_units_sold.get(am, 0) + sold

        # Sum units received per AM (via store lookup).
        am_units_received: dict[str, int] = {}
        for conf in self.tables.get("store_confirmations", []):
            store_id = str(conf.get("store_id", ""))
            store = self._stores.get(store_id)
            if not store:
                continue
            am = str(store.get("area_manager", ""))
            if am:
                received = _to_int(conf.get("received_quantity")) or 0
                am_units_received[am] = am_units_received.get(am, 0) + received

        # Build rows for all AMs that appear in stores or exceptions.
        all_ams = set(am_stores.keys()) | set(am_exceptions.keys())
        rows: list[AMScorecardRow] = []
        for am in all_ams:
            excs = am_exceptions.get(am, [])
            store_ids = am_stores.get(am, [])
            open_excs = [e for e in excs if e.status in ACTIVE_STATUSES]
            critical = [e for e in excs if e.severity == "critical"]
            breached = [e for e in excs if e.sla_status == "breached"]
            stockouts = [
                e for e in excs if e.exception_type == "stockout_risk"
            ]
            overstocks = [
                e for e in excs if e.exception_type == "overstock_risk"
            ]
            alloc_count = am_allocations.get(am, 0)
            conf_count = am_confirmations.get(am, 0)
            sold = am_units_sold.get(am, 0)
            received = am_units_received.get(am, 0)

            rows.append(
                AMScorecardRow(
                    area_manager=am,
                    region=am_regions.get(am, ""),
                    store_count=len(store_ids),
                    allocation_count=alloc_count,
                    confirmation_count=conf_count,
                    open_exception_count=len(open_excs),
                    critical_count=len(critical),
                    sla_breach_count=len(breached),
                    stockout_risk_count=len(stockouts),
                    overstock_risk_count=len(overstocks),
                    am_follow_up_backlog=len(open_excs),
                    sell_through_rate=_safe_divide(sold, received),
                    exception_rate=_safe_divide(len(excs), alloc_count),
                )
            )

        # Sort: most open exceptions first, then alphabetical.
        rows.sort(key=lambda r: (-r.open_exception_count, r.area_manager))
        return rows

    # -- private: KPI construction ------------------------------------------

    def _make_kpi(self, name: str, value: float) -> KPIResult:
        meta = KPI_META[name]
        return KPIResult(
            name=name,
            category=meta["category"],
            value=value,
            unit=meta["unit"],
            description=meta["description"],
        )

    # -- private: process KPI computations ---------------------------------

    def _campaign_readiness_rate(self) -> float:
        """Fraction of allocations fully ready at campaign launch.

        An allocation is campaign-ready when at least one of its
        confirmations has:
          - visit_date within the campaign launch window
            (start_date + launch_window_days),
          - campaign_store_status == "completed" (or visit_status
            == "completed"),
          - at least one photo proof record.

        Allocations with missing campaign data are excluded from both
        numerator and denominator.
        """
        allocations = self.tables.get("allocation_plan", [])
        if not allocations:
            return 0.0

        ready = 0
        total = 0
        for alloc in allocations:
            campaign_id = str(alloc.get("campaign_id", ""))
            campaign = self._campaigns.get(campaign_id)
            if not campaign:
                continue

            start = _parse_date(campaign.get("campaign_start_date"))
            if start is None:
                continue

            launch_window = _to_int(campaign.get("launch_window_days")) or 7
            deadline = start + timedelta(days=launch_window)

            total += 1
            alloc_id = str(alloc.get("allocation_id", ""))
            confirmations = self._confirmations_by_alloc.get(alloc_id, [])

            for conf in confirmations:
                visit = _parse_date(conf.get("visit_date"))
                if visit is None or visit > deadline:
                    continue
                store_status = str(conf.get("campaign_store_status", ""))
                visit_status = str(conf.get("visit_status", ""))
                if store_status != "completed" and visit_status != "completed":
                    continue
                conf_id = str(conf.get("confirmation_id", ""))
                photos = self._photos_by_confirmation.get(conf_id, [])
                if photos:
                    ready += 1
                    break

        return _safe_divide(ready, total)

    def _confirmation_completion_rate(self) -> float:
        """Fraction of dispatch records with a matching confirmation.

        A dispatch is "confirmed" when at least one store confirmation
        exists for the same allocation_id.
        """
        dispatches = self.tables.get("dispatch", [])
        if not dispatches:
            return 0.0

        confirmation_allocs = {
            str(c.get("allocation_id", ""))
            for c in self.tables.get("store_confirmations", [])
            if c.get("allocation_id")
        }

        matched = sum(
            1
            for d in dispatches
            if str(d.get("allocation_id", "")) in confirmation_allocs
        )
        return _safe_divide(matched, len(dispatches))

    def _photo_proof_completion_rate(self) -> float:
        """Fraction of confirmations with at least one photo proof."""
        confirmations = self.tables.get("store_confirmations", [])
        if not confirmations:
            return 0.0

        with_photos = sum(
            1
            for c in confirmations
            if str(c.get("confirmation_id", ""))
            in self._photos_by_confirmation
        )
        return _safe_divide(with_photos, len(confirmations))

    def _allocation_accuracy_rate(self) -> float:
        """Fraction of confirmations where received == shipped."""
        matched, total = self._qty_match_stats()
        return _safe_divide(matched, total)

    def _quantity_mismatch_rate(self) -> float:
        """Fraction of confirmations where received != shipped."""
        matched, total = self._qty_match_stats()
        return _safe_divide(total - matched, total)

    def _qty_match_stats(self) -> tuple[int, int]:
        """Return (exact_matches, total_with_both_quantities).

        Only confirmations that have a matching dispatch record with a
        valid shipped_quantity, and a valid received_quantity, are
        counted.
        """
        matched = 0
        total = 0
        for conf in self.tables.get("store_confirmations", []):
            alloc_id = str(conf.get("allocation_id", ""))
            ship = self._dispatch_by_alloc.get(alloc_id)
            if not ship:
                continue
            shipped = _to_int(ship.get("shipped_quantity"))
            received = _to_int(conf.get("received_quantity"))
            if shipped is None or received is None:
                continue
            total += 1
            if received == shipped:
                matched += 1
        return matched, total

    # -- private: performance KPI computations ------------------------------

    def _exception_rate(self) -> float:
        """Total detected exceptions per allocation."""
        total_allocations = len(self.tables.get("allocation_plan", []))
        if total_allocations == 0:
            return 0.0
        return _safe_divide(self._report.total, total_allocations)

    def _open_exception_count(self) -> float:
        """Count of exceptions with an active status."""
        return float(
            sum(1 for e in self._report.exceptions if e.status in ACTIVE_STATUSES)
        )

    def _sla_breach_count(self) -> float:
        """Count of exceptions whose SLA status is breached."""
        return float(
            sum(1 for e in self._report.exceptions if e.sla_status == "breached")
        )

    def _sell_through_rate(self) -> float:
        """Total units sold / total units received."""
        total_sold = sum(
            _to_int(s.get("units_sold")) or 0
            for s in self.tables.get("sales_daily", [])
        )
        total_received = sum(
            _to_int(c.get("received_quantity")) or 0
            for c in self.tables.get("store_confirmations", [])
        )
        return _safe_divide(total_sold, total_received)

    def _stockout_risk_count(self) -> float:
        """Count of stockout risk exceptions."""
        return float(len(self._report.by_type("stockout_risk")))

    def _overstock_risk_count(self) -> float:
        """Count of overstock risk exceptions."""
        return float(len(self._report.by_type("overstock_risk")))

    def _am_follow_up_backlog(self) -> float:
        """Count of active exceptions assigned to area managers.

        This counts exceptions with an active status and a non-empty
        area_manager field, representing the workload that area
        managers need to follow up on.
        """
        return float(
            sum(
                1
                for e in self._report.exceptions
                if e.status in ACTIVE_STATUSES and e.area_manager
            )
        )


# ---------------------------------------------------------------------------
# Convenience entry points
# ---------------------------------------------------------------------------

def compute_metrics(
    tables: dict[str, list[dict[str, Any]]],
    aging_date: date | None = None,
    exception_report: ExceptionReport | None = None,
) -> MetricsSummary:
    """Compute all KPIs from the data tables and return a summary."""
    return MetricsEngine(tables, aging_date, exception_report).compute()


def build_am_scorecard(
    tables: dict[str, list[dict[str, Any]]],
    aging_date: date | None = None,
    exception_report: ExceptionReport | None = None,
) -> list[AMScorecardRow]:
    """Build the area manager scorecard from the data tables."""
    return MetricsEngine(tables, aging_date, exception_report).compute_am_scorecard()
