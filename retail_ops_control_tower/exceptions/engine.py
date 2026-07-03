"""Exception detection and action-list engine (T10).

Scans the 8 data tables (stores, campaigns, allocation_plan, dispatch,
store_confirmations, photo_proofs, sales_daily, issues) and converts
validations, confirmations, proof data, and sales patterns into an
actionable exception table.

The task spec names this output ``retail_ops_control_tower/exceptions.py``.
A flat module file cannot coexist with the existing ``exceptions/`` package
directory (the package directory takes precedence on import), so the engine
logic lives here as ``exceptions/engine.py`` and the public API is
re-exported from ``exceptions/__init__.py``. ``from
retail_ops_control_tower.exceptions import ExceptionEngine`` works exactly
as it would from a flat ``exceptions.py``.

Exception types (9):

    1. missing_confirmation        - dispatch has no matching confirmation.
    2. late_confirmation           - confirmation posted after launch window.
    3. quantity_mismatch           - received != shipped quantity.
    4. missing_photo_proof         - confirmation has no photo proof records.
    5. late_photo_proof            - photo submitted after launch window.
    6. stockout_risk               - on-hand depleted to zero with prior sales.
    7. overstock_risk              - sell-through below 30% with inventory left.
    8. low_sell_through             - sell-through below 50% of target.
    9. unresolved_issue_sla_breach  - open issue past its SLA due date.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any

# ---------------------------------------------------------------------------
# Exception type registry
# ---------------------------------------------------------------------------

EXCEPTION_TYPES: list[str] = [
    "missing_confirmation",
    "late_confirmation",
    "quantity_mismatch",
    "missing_photo_proof",
    "late_photo_proof",
    "stockout_risk",
    "overstock_risk",
    "low_sell_through",
    "unresolved_issue_sla_breach",
]

# Default metadata for each exception type.
EXCEPTION_TYPE_META: dict[str, dict[str, Any]] = {
    "missing_confirmation": {
        "owner": "Field Operations",
        "sla_hours": 48,
        "default_severity": "watch",
        "recommended_action": (
            "Contact store PIC to post confirmation; verify visit completion."
        ),
    },
    "late_confirmation": {
        "owner": "Store Manager",
        "sla_hours": 48,
        "default_severity": "critical",
        "recommended_action": (
            "Dispatch field rep to complete setup; escalate to area manager."
        ),
    },
    "quantity_mismatch": {
        "owner": "DC Operations",
        "sla_hours": 48,
        "default_severity": "watch",
        "recommended_action": (
            "Reconcile planned vs shipped vs received; initiate DC count verification."
        ),
    },
    "missing_photo_proof": {
        "owner": "Field Representative",
        "sla_hours": 48,
        "default_severity": "watch",
        "recommended_action": (
            "Request field rep to re-submit photo proof within 24h."
        ),
    },
    "late_photo_proof": {
        "owner": "Field Representative",
        "sla_hours": 48,
        "default_severity": "watch",
        "recommended_action": (
            "Review photo submission process; ensure timely upload within launch window."
        ),
    },
    "stockout_risk": {
        "owner": "Replenishment Planner",
        "sla_hours": 24,
        "default_severity": "critical",
        "recommended_action": (
            "Expedite replenishment from DC; consider allocation transfer from overstock stores."
        ),
    },
    "overstock_risk": {
        "owner": "Merchant",
        "sla_hours": 168,
        "default_severity": "watch",
        "recommended_action": (
            "Plan markdown or transfer to high-velocity stores."
        ),
    },
    "low_sell_through": {
        "owner": "Merchant + Planner",
        "sla_hours": 168,
        "default_severity": "watch",
        "recommended_action": (
            "Review pricing and display; consider promo acceleration."
        ),
    },
    "unresolved_issue_sla_breach": {
        "owner": "Operations Lead",
        "sla_hours": 24,
        "default_severity": "critical",
        "recommended_action": (
            "Escalate to operations lead for root-cause review."
        ),
    },
}

# Severity ordering for sorting (lower = higher priority).
_SEVERITY_RANK = {"critical": 0, "watch": 1, "info": 2}

# Sell-through thresholds.
STOCKOUT_ON_HAND_THRESHOLD = 0
OVERSTOCK_SELL_THROUGH_THRESHOLD = 0.30
LOW_SELL_THROUGH_THRESHOLD = 0.50

# SLA breach: days past due date before auto-escalation to critical.
SLA_BREACH_CRITICAL_DAYS = 7

# Photo proof grace period (days after visit date before photo is "late").
PHOTO_PROOF_GRACE_DAYS = 0


# ---------------------------------------------------------------------------
# Exception record model
# ---------------------------------------------------------------------------

@dataclass
class ExceptionRecord:
    """A single actionable exception detected from the data tables.

    Attributes:
        exception_id:       unique sequential ID (EXC-NNN).
        exception_type:     one of the 9 type strings in EXCEPTION_TYPES.
        severity:           "critical", "watch", or "info".
        owner:              default owner role for this exception type.
        region:             geographic region of the affected store.
        area_manager:       area manager responsible for the store (AM).
        age_days:           days since the exception was first detectable.
        status:             lifecycle status ("open", "in_progress", etc.).
        recommended_action: codified next-step action from the playbook.
        campaign_id:        linked campaign ID (may be empty).
        store_id:           affected store ID (may be empty).
        sku:                affected SKU (may be empty).
        allocation_id:      linked allocation ID (may be empty).
        confirmation_id:    linked confirmation ID (may be empty).
        message:            human-readable description of the exception.
        created_date:       ISO date when the exception condition arose.
        sla_status:         "within", "approaching", "breached", or "paused".
        priority_score:     computed priority score (higher = handle first).
    """

    exception_id: str = ""
    exception_type: str = ""
    severity: str = "watch"
    owner: str = ""
    region: str = ""
    area_manager: str = ""
    age_days: int = 0
    status: str = "open"
    recommended_action: str = ""
    campaign_id: str = ""
    store_id: str = ""
    sku: str = ""
    allocation_id: str = ""
    confirmation_id: str = ""
    message: str = ""
    created_date: str = ""
    sla_status: str = "within"
    priority_score: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Exception report
# ---------------------------------------------------------------------------

@dataclass
class ExceptionReport:
    """Aggregated result of running the exception detection engine.

    Attributes:
        exceptions: list of ExceptionRecord, sorted for the action list.
        aging_date: the date used for age calculations.
        total: total number of exceptions detected.
    """

    exceptions: list[ExceptionRecord] = field(default_factory=list)
    aging_date: str = ""

    @property
    def total(self) -> int:
        return len(self.exceptions)

    @property
    def critical_count(self) -> int:
        return sum(1 for e in self.exceptions if e.severity == "critical")

    @property
    def watch_count(self) -> int:
        return sum(1 for e in self.exceptions if e.severity == "watch")

    @property
    def info_count(self) -> int:
        return sum(1 for e in self.exceptions if e.severity == "info")

    @property
    def open_count(self) -> int:
        return sum(
            1 for e in self.exceptions
            if e.status in ("open", "in_progress", "raised", "escalated")
        )

    @property
    def breached_count(self) -> int:
        return sum(1 for e in self.exceptions if e.sla_status == "breached")

    def by_type(self, exc_type: str) -> list[ExceptionRecord]:
        return [e for e in self.exceptions if e.exception_type == exc_type]

    def by_severity(self, severity: str) -> list[ExceptionRecord]:
        return [e for e in self.exceptions if e.severity == severity]

    def to_dict(self) -> dict[str, Any]:
        return {
            "aging_date": self.aging_date,
            "total": self.total,
            "critical": self.critical_count,
            "watch": self.watch_count,
            "info": self.info_count,
            "open": self.open_count,
            "breached": self.breached_count,
            "exceptions": [e.to_dict() for e in self.exceptions],
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_int(value: Any) -> int | None:
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
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_date(value: Any) -> date | None:
    """Parse a value into a date object. Handles ISO date or datetime strings."""
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    # Try full ISO datetime first (e.g. "2026-07-01T09:30:00-05:00")
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    # Fall back to date-only
    try:
        return date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None


def _compute_sla_status(
    age_days: int, sla_hours: int, status: str
) -> str:
    """Compute SLA status from age and SLA window."""
    if status == "paused":
        return "paused"
    sla_days = sla_hours / 24.0
    if sla_days <= 0:
        return "breached"
    if age_days > sla_days:
        return "breached"
    if age_days > sla_days * 0.75:
        return "approaching"
    return "within"


def _compute_priority_score(
    severity: str,
    age_days: int,
    sla_hours: int,
    is_hero_sku: bool,
    is_flagship: bool,
    campaign_active: bool,
    in_launch_window: bool,
) -> int:
    """Compute a priority score for sorting the action list.

    score = severity_weight * 100 + age_pressure + business_impact + campaign_urgency

    - severity_weight: critical=3, watch=2, info=1
    - age_pressure: (age_days / sla_days) * 50, capped at 50
    - business_impact: hero/flagship=30, standard=15, low-velocity=5
    - campaign_urgency: 20 if in launch window, 10 if active, 0 otherwise
    """
    sev_weight = {"critical": 3, "watch": 2, "info": 1}.get(severity, 1)
    sla_days = max(sla_hours / 24.0, 1)
    age_pressure = min((age_days / sla_days) * 50, 50)

    if is_hero_sku or is_flagship:
        impact = 30
    elif severity == "info":
        impact = 5
    else:
        impact = 15

    if in_launch_window:
        urgency = 20
    elif campaign_active:
        urgency = 10
    else:
        urgency = 0

    return max(1, int(sev_weight * 100 + age_pressure + impact + urgency))


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ExceptionEngine:
    """Detects exceptions from the 8 data tables.

    ``tables`` maps table name -> list of record dicts (as produced by
    :func:`retail_ops_control_tower.io.read_all_csv_tables`).

    Parameters:
        tables: dict of table name -> list of record dicts.
        aging_date: the date used for age calculations. Defaults to today.
    """

    def __init__(
        self,
        tables: dict[str, list[dict[str, Any]]],
        aging_date: date | None = None,
    ):
        self.tables = tables
        self.aging_date = aging_date or date.today()
        self._exceptions: list[ExceptionRecord] = []
        self._seq = 0

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
        self._allocations: dict[str, dict] = {
            str(a.get("allocation_id", "")): a
            for a in tables.get("allocation_plan", [])
            if a.get("allocation_id")
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

    def detect(self) -> ExceptionReport:
        """Run all 9 exception detectors and return an ExceptionReport."""
        self._exceptions = []
        self._seq = 0

        self._detect_missing_confirmation()
        self._detect_late_confirmation()
        self._detect_quantity_mismatch()
        self._detect_missing_photo_proof()
        self._detect_late_photo_proof()
        self._detect_stockout_risk()
        self._detect_overstock_risk()
        self._detect_low_sell_through()
        self._detect_unresolved_issue_sla_breach()

        # Sort: severity (critical first), then age_days (oldest first).
        self._exceptions.sort(
            key=lambda e: (
                _SEVERITY_RANK.get(e.severity, 9),
                -e.age_days,
                e.exception_id,
            )
        )

        return ExceptionReport(
            exceptions=list(self._exceptions),
            aging_date=self.aging_date.isoformat(),
        )

    def build_action_list(self, top_n: int = 0) -> list[ExceptionRecord]:
        """Build the daily action list.

        Filters to open/in_progress/raised/escalated exceptions, sorts by
        severity (critical first) then SLA age (oldest first), and returns
        the top N items. If top_n is 0, returns all matching items.
        """
        open_statuses = {"open", "in_progress", "raised", "escalated"}
        action_items = [
            e for e in self._exceptions if e.status in open_statuses
        ]
        action_items.sort(
            key=lambda e: (
                _SEVERITY_RANK.get(e.severity, 9),
                -e.age_days,
                e.exception_id,
            )
        )
        if top_n > 0:
            return action_items[:top_n]
        return action_items

    # -- private: record creation ------------------------------------------

    def _add_exception(
        self,
        exc_type: str,
        message: str,
        campaign_id: str = "",
        store_id: str = "",
        sku: str = "",
        allocation_id: str = "",
        confirmation_id: str = "",
        created_date: str = "",
        severity: str | None = None,
        status: str = "open",
    ) -> None:
        """Create and register an ExceptionRecord."""
        self._seq += 1
        meta = EXCEPTION_TYPE_META.get(exc_type, {})
        sev = severity or meta.get("default_severity", "watch")
        owner = meta.get("owner", "")
        sla_hours = meta.get("sla_hours", 48)
        action = meta.get("recommended_action", "Review and assign owner.")

        # Look up store for region and area_manager.
        store = self._stores.get(store_id, {})
        region = str(store.get("region", ""))
        area_manager = str(store.get("area_manager", ""))

        # Compute age_days from created_date.
        created = _parse_date(created_date)
        if created is not None:
            age_days = max(0, (self.aging_date - created).days)
        else:
            age_days = 0

        sla_status = _compute_sla_status(age_days, sla_hours, status)

        # Compute business impact and campaign urgency for priority score.
        campaign = self._campaigns.get(campaign_id, {})
        hero_sku = str(campaign.get("hero_sku", ""))
        is_hero = sku != "" and sku == hero_sku
        is_flagship = str(store.get("store_format", "")) == "flagship"

        campaign_active = False
        in_launch_window = False
        if campaign_id and campaign:
            start = _parse_date(campaign.get("campaign_start_date"))
            end = _parse_date(campaign.get("campaign_end_date"))
            launch_window = int(campaign.get("launch_window_days", 7))
            if start and end:
                if start <= self.aging_date <= end:
                    campaign_active = True
                if start <= self.aging_date <= start.replace(
                    year=start.year
                ) + __import__("datetime").timedelta(days=launch_window):
                    in_launch_window = True

        priority = _compute_priority_score(
            sev, age_days, sla_hours, is_hero, is_flagship,
            campaign_active, in_launch_window,
        )

        record = ExceptionRecord(
            exception_id=f"EXC-{self._seq:03d}",
            exception_type=exc_type,
            severity=sev,
            owner=owner,
            region=region,
            area_manager=area_manager,
            age_days=age_days,
            status=status,
            recommended_action=action,
            campaign_id=campaign_id,
            store_id=store_id,
            sku=sku,
            allocation_id=allocation_id,
            confirmation_id=confirmation_id,
            message=message,
            created_date=created_date,
            sla_status=sla_status,
            priority_score=priority,
        )
        self._exceptions.append(record)

    # -- detector 1: missing_confirmation -----------------------------------

    def _detect_missing_confirmation(self) -> None:
        """Dispatch row exists but no matching confirmation record."""
        confirmation_allocs = {
            str(c.get("allocation_id", ""))
            for c in self.tables.get("store_confirmations", [])
            if c.get("allocation_id")
        }
        for ship in self.tables.get("dispatch", []):
            alloc_id = str(ship.get("allocation_id", ""))
            if alloc_id and alloc_id not in confirmation_allocs:
                # Determine severity: critical if hero SKU.
                campaign_id = str(ship.get("campaign_id", ""))
                sku = str(ship.get("sku", ""))
                campaign = self._campaigns.get(campaign_id, {})
                hero_sku = str(campaign.get("hero_sku", ""))
                sev = "critical" if sku and sku == hero_sku else "watch"

                created_date = str(ship.get("shipped_date", ""))
                self._add_exception(
                    exc_type="missing_confirmation",
                    message=(
                        f"Allocation {alloc_id} (shipment "
                        f"{ship.get('shipment_id', '')}) has no store "
                        f"confirmation record."
                    ),
                    campaign_id=campaign_id,
                    store_id=str(ship.get("store_id", "")),
                    sku=sku,
                    allocation_id=alloc_id,
                    created_date=created_date,
                    severity=sev,
                )

    # -- detector 2: late_confirmation -------------------------------------

    def _detect_late_confirmation(self) -> None:
        """Confirmation posted after the campaign launch window."""
        for conf in self.tables.get("store_confirmations", []):
            campaign_id = str(conf.get("campaign_id", ""))
            campaign = self._campaigns.get(campaign_id, {})
            if not campaign:
                continue
            start = _parse_date(campaign.get("campaign_start_date"))
            launch_window = int(campaign.get("launch_window_days", 7))
            visit = _parse_date(conf.get("visit_date"))
            if start is None or visit is None:
                continue
            deadline = start + __import__("datetime").timedelta(
                days=launch_window
            )
            if visit > deadline:
                days_late = (visit - deadline).days
                sev = "critical" if days_late > 3 else "watch"
                self._add_exception(
                    exc_type="late_confirmation",
                    message=(
                        f"Confirmation {conf.get('confirmation_id', '')} "
                        f"posted on {conf.get('visit_date', '')}, "
                        f"{days_late} days after the launch window "
                        f"deadline ({deadline.isoformat()})."
                    ),
                    campaign_id=campaign_id,
                    store_id=str(conf.get("store_id", "")),
                    sku=str(conf.get("sku", "")),
                    allocation_id=str(conf.get("allocation_id", "")),
                    confirmation_id=str(conf.get("confirmation_id", "")),
                    created_date=str(conf.get("visit_date", "")),
                    severity=sev,
                )

    # -- detector 3: quantity_mismatch -------------------------------------

    def _detect_quantity_mismatch(self) -> None:
        """Received quantity differs from shipped quantity."""
        for conf in self.tables.get("store_confirmations", []):
            alloc_id = str(conf.get("allocation_id", ""))
            ship = self._dispatch_by_alloc.get(alloc_id)
            if not ship:
                continue
            shipped = _to_int(ship.get("shipped_quantity"))
            received = _to_int(conf.get("received_quantity"))
            if shipped is None or received is None:
                continue
            variance = received - shipped
            if variance != 0:
                pct = abs(variance) / shipped * 100 if shipped else 0
                sev = "critical" if pct > 20 else "watch"
                self._add_exception(
                    exc_type="quantity_mismatch",
                    message=(
                        f"Quantity mismatch for confirmation "
                        f"{conf.get('confirmation_id', '')}: shipped="
                        f"{shipped}, received={received}, variance="
                        f"{variance} ({pct:.1f}%)."
                    ),
                    campaign_id=str(conf.get("campaign_id", "")),
                    store_id=str(conf.get("store_id", "")),
                    sku=str(conf.get("sku", "")),
                    allocation_id=alloc_id,
                    confirmation_id=str(conf.get("confirmation_id", "")),
                    created_date=str(conf.get("received_date", "")),
                    severity=sev,
                )

    # -- detector 4: missing_photo_proof -----------------------------------

    def _detect_missing_photo_proof(self) -> None:
        """Confirmation exists but has no photo proof records."""
        for conf in self.tables.get("store_confirmations", []):
            conf_id = str(conf.get("confirmation_id", ""))
            if not conf_id:
                continue
            photos = self._photos_by_confirmation.get(conf_id, [])
            if not photos:
                # Severity: critical if compliance score is low.
                compliance = _to_float(conf.get("compliance_score"))
                sev = "critical" if compliance is not None and compliance < 80 else "watch"
                self._add_exception(
                    exc_type="missing_photo_proof",
                    message=(
                        f"Confirmation {conf_id} has no photo proof records."
                    ),
                    campaign_id=str(conf.get("campaign_id", "")),
                    store_id=str(conf.get("store_id", "")),
                    sku=str(conf.get("sku", "")),
                    allocation_id=str(conf.get("allocation_id", "")),
                    confirmation_id=conf_id,
                    created_date=str(conf.get("visit_date", "")),
                    severity=sev,
                )

    # -- detector 5: late_photo_proof --------------------------------------

    def _detect_late_photo_proof(self) -> None:
        """Photo proof submitted after the campaign launch window."""
        for photo in self.tables.get("photo_proofs", []):
            campaign_id = str(photo.get("campaign_id", ""))
            campaign = self._campaigns.get(campaign_id, {})
            if not campaign:
                continue
            start = _parse_date(campaign.get("campaign_start_date"))
            launch_window = int(campaign.get("launch_window_days", 7))
            photo_date = _parse_date(photo.get("photo_timestamp"))
            if start is None or photo_date is None:
                continue
            deadline = start + __import__("datetime").timedelta(
                days=launch_window + PHOTO_PROOF_GRACE_DAYS
            )
            if photo_date > deadline:
                days_late = (photo_date - deadline).days
                sev = "critical" if days_late > 3 else "watch"
                self._add_exception(
                    exc_type="late_photo_proof",
                    message=(
                        f"Photo proof {photo.get('photo_id', '')} submitted "
                        f"on {photo.get('photo_timestamp', '')}, {days_late} "
                        f"days after the launch window deadline "
                        f"({deadline.isoformat()})."
                    ),
                    campaign_id=campaign_id,
                    store_id=str(photo.get("store_id", "")),
                    confirmation_id=str(photo.get("confirmation_id", "")),
                    created_date=str(photo.get("photo_timestamp", "")),
                    severity=sev,
                )

    # -- detector 6: stockout_risk ----------------------------------------

    def _detect_stockout_risk(self) -> None:
        """On-hand quantity depleted to zero with prior sales."""
        # Group sales by (campaign_id, store_id, sku) and find stockouts.
        sales_groups: dict[tuple[str, str, str], list[dict]] = {}
        for sale in self.tables.get("sales_daily", []):
            key = (
                str(sale.get("campaign_id", "")),
                str(sale.get("store_id", "")),
                str(sale.get("sku", "")),
            )
            sales_groups.setdefault(key, []).append(sale)

        for (cid, sid, sku), sales in sales_groups.items():
            # Find the last sales record for this group.
            last_sale = max(
                sales,
                key=lambda s: str(s.get("sales_date", "")),
            )
            on_hand = _to_int(last_sale.get("on_hand_quantity"))
            total_sold = sum(
                _to_int(s.get("units_sold", 0)) or 0 for s in sales
            )
            if on_hand is not None and on_hand <= STOCKOUT_ON_HAND_THRESHOLD and total_sold > 0:
                self._add_exception(
                    exc_type="stockout_risk",
                    message=(
                        f"Stockout risk for SKU {sku} at store {sid}: "
                        f"on-hand={on_hand}, total sold={total_sold}."
                    ),
                    campaign_id=cid,
                    store_id=sid,
                    sku=sku,
                    created_date=str(last_sale.get("sales_date", "")),
                    severity="critical",
                )

    # -- detector 7: overstock_risk ---------------------------------------

    def _detect_overstock_risk(self) -> None:
        """Sell-through below 30% with significant remaining inventory."""
        sales_groups: dict[tuple[str, str, str], list[dict]] = {}
        for sale in self.tables.get("sales_daily", []):
            key = (
                str(sale.get("campaign_id", "")),
                str(sale.get("store_id", "")),
                str(sale.get("sku", "")),
            )
            sales_groups.setdefault(key, []).append(sale)

        for (cid, sid, sku), sales in sales_groups.items():
            total_sold = sum(
                _to_int(s.get("units_sold", 0)) or 0 for s in sales
            )
            # Look up received quantity from confirmations.
            received = self._get_received_quantity(cid, sid, sku)
            if received is None or received <= 0:
                continue
            sell_through = total_sold / received
            last_sale = max(
                sales,
                key=lambda s: str(s.get("sales_date", "")),
            )
            on_hand = _to_int(last_sale.get("on_hand_quantity")) or 0
            if sell_through < OVERSTOCK_SELL_THROUGH_THRESHOLD and on_hand > 0:
                self._add_exception(
                    exc_type="overstock_risk",
                    message=(
                        f"Overstock risk for SKU {sku} at store {sid}: "
                        f"sell-through={sell_through:.1%}, on-hand={on_hand}."
                    ),
                    campaign_id=cid,
                    store_id=sid,
                    sku=sku,
                    created_date=str(last_sale.get("sales_date", "")),
                    severity="watch",
                )

    # -- detector 8: low_sell_through --------------------------------------

    def _detect_low_sell_through(self) -> None:
        """Sell-through below 50% of the campaign target."""
        sales_groups: dict[tuple[str, str, str], list[dict]] = {}
        for sale in self.tables.get("sales_daily", []):
            key = (
                str(sale.get("campaign_id", "")),
                str(sale.get("store_id", "")),
                str(sale.get("sku", "")),
            )
            sales_groups.setdefault(key, []).append(sale)

        for (cid, sid, sku), sales in sales_groups.items():
            total_sold = sum(
                _to_int(s.get("units_sold", 0)) or 0 for s in sales
            )
            received = self._get_received_quantity(cid, sid, sku)
            if received is None or received <= 0:
                continue
            sell_through = total_sold / received
            campaign = self._campaigns.get(cid, {})
            target = _to_float(campaign.get("period_sell_through_target")) or 0.70
            if sell_through < LOW_SELL_THROUGH_THRESHOLD:
                last_sale = max(
                    sales,
                    key=lambda s: str(s.get("sales_date", "")),
                )
                sev = "critical" if sell_through < target * 0.50 else "watch"
                self._add_exception(
                    exc_type="low_sell_through",
                    message=(
                        f"Low sell-through for SKU {sku} at store {sid}: "
                        f"sell-through={sell_through:.1%} vs target "
                        f"{target:.0%}."
                    ),
                    campaign_id=cid,
                    store_id=sid,
                    sku=sku,
                    created_date=str(last_sale.get("sales_date", "")),
                    severity=sev,
                )

    # -- detector 9: unresolved_issue_sla_breach ---------------------------

    def _detect_unresolved_issue_sla_breach(self) -> None:
        """Open issue past its SLA due date."""
        open_statuses = {"raised", "open", "in_progress", "escalated"}
        for issue in self.tables.get("issues", []):
            status = str(issue.get("exception_status", ""))
            if status not in open_statuses:
                continue
            due_date_str = str(issue.get("due_date", ""))
            due = _parse_date(due_date_str)
            if due is None:
                continue
            if self.aging_date > due:
                days_overdue = (self.aging_date - due).days
                sev = "critical" if days_overdue > SLA_BREACH_CRITICAL_DAYS else "watch"
                created_date_str = str(issue.get("created_date", ""))
                self._add_exception(
                    exc_type="unresolved_issue_sla_breach",
                    message=(
                        f"Issue {issue.get('exception_id', '')} "
                        f"({issue.get('exception_type', '')}) is "
                        f"{days_overdue} days past its SLA due date "
                        f"({due_date_str})."
                    ),
                    campaign_id=str(issue.get("campaign_id", "")),
                    store_id=str(issue.get("store_id", "")),
                    sku=str(issue.get("sku", "")),
                    allocation_id=str(issue.get("allocation_id", "")),
                    confirmation_id=str(issue.get("confirmation_id", "")),
                    created_date=created_date_str,
                    severity=sev,
                    status=status,
                )

    # -- helper: get received quantity for a campaign/store/sku -----------

    def _get_received_quantity(
        self, campaign_id: str, store_id: str, sku: str
    ) -> int | None:
        """Look up the received quantity for a campaign/store/sku combination."""
        for conf in self.tables.get("store_confirmations", []):
            if (
                str(conf.get("campaign_id", "")) == campaign_id
                and str(conf.get("store_id", "")) == store_id
                and str(conf.get("sku", "")) == sku
            ):
                return _to_int(conf.get("received_quantity"))
        return None


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------

def detect_exceptions(
    tables: dict[str, list[dict[str, Any]]],
    aging_date: date | None = None,
) -> ExceptionReport:
    """Run all exception detectors against ``tables`` and return a report."""
    return ExceptionEngine(tables, aging_date).detect()


def build_action_list(
    tables: dict[str, list[dict[str, Any]]],
    aging_date: date | None = None,
    top_n: int = 0,
) -> list[ExceptionRecord]:
    """Detect exceptions and return the sorted daily action list."""
    engine = ExceptionEngine(tables, aging_date)
    engine.detect()
    return engine.build_action_list(top_n=top_n)
