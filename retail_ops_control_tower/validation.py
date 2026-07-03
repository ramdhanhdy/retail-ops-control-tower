"""Validation and reconciliation engine.

Runs 9 data-quality and planned-vs-actual reconciliation checks across the 8
data tables. Each check returns zero or more structured :class:`ValidationFinding`
records; nothing is printed. The engine is the data-integrity layer that feeds
exception management (T10) and dashboards.

Rules implemented (per task T09):

    1. Required column checks         - every stored column is present and the
                                        value is non-empty for non-nullable fields.
    2. Duplicate key checks           - primary keys are unique per table.
    3. Foreign key checks             - every FK references an existing parent row.
    4. Planned vs dispatched variance - shipped_quantity != planned_quantity.
    5. Planned vs received variance   - received_quantity != planned_quantity.
    6. Dispatch without plan          - a dispatch row whose allocation_id is
                                        not in allocation_plan.
    7. Confirmation without dispatch  - a confirmation whose shipment_id is not
                                        in dispatch (or allocation_id not in plan).
    8. Photo proof without confirmation - a photo whose confirmation_id is not
                                        in store_confirmations.
    9. Sales record without campaign/store match - a sales row whose
                                        campaign_id/store_id/sku is unknown.

Findings are dataclasses with: severity, table, row_id, rule_code, message, and
suggested_action. ``ValidationError`` and the simple ``validate_positive`` /
``validate_non_negative`` helpers are retained for backward compatibility with
the existing PRD V-01..V-15 generation-time guards.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Column / key metadata (mirrors data_generation.TABLE_COLUMNS; duplicated here
# so the validation engine does not hard-depend on the generator module and can
# be reused on externally-supplied CSVs that follow the same schema).
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS: dict[str, list[str]] = {
    "stores": [
        "store_id", "store_name", "region", "store_format", "area_manager",
        "selling_area_sqft", "city", "state", "open_date", "is_active", "timezone",
    ],
    "campaigns": [
        "campaign_id", "campaign_name", "campaign_type", "campaign_start_date",
        "campaign_end_date", "campaign_status", "hq_owner", "target_store_count",
        "sku_list", "hero_sku", "launch_window_days",
        "supplier_lead_time_weeks", "period_sell_through_target",
        "full_price_target", "posm_list",
    ],
    "allocation_plan": [
        "allocation_id", "campaign_id", "sku", "store_id", "planned_quantity",
        "planned_receipt_date", "allocation_phase", "allocation_method",
        "holdback_pct", "planner_owner",
    ],
    "dispatch": [
        "shipment_id", "allocation_id", "campaign_id", "sku", "store_id",
        "shipped_quantity", "shipped_date", "expected_arrival_date",
        "carton_count", "dc_id", "carrier",
    ],
    "store_confirmations": [
        "confirmation_id", "allocation_id", "shipment_id", "campaign_id",
        "store_id", "sku", "received_quantity", "received_date",
        "receipt_status", "receiving_exception_type", "receiving_owner",
        "visit_id", "visit_date", "visit_timestamp", "visit_status",
        "gps_coordinates", "checklist_completion_pct", "planogram_compliance",
        "pricing_accuracy", "on_shelf_availability_pct",
        "training_completion_flag", "audit_level", "audit_status",
        "compliance_score", "audit_comments", "exception_flag",
        "non_completion_reason", "campaign_store_status",
        "confirmation_timestamp",
    ],
    "photo_proofs": [
        "photo_id", "confirmation_id", "visit_id", "store_id", "campaign_id",
        "photo_proof_url", "photo_timestamp", "photo_gps_coordinates",
        "photo_user_id", "photo_device_id", "photo_type",
        "photo_validation_status", "photo_validation_reason",
    ],
    "sales_daily": [
        "sales_id", "campaign_id", "store_id", "sku", "sales_date",
        "day_of_campaign", "units_sold", "units_sold_full_price",
        "units_sold_markdown", "on_hand_quantity", "on_order_quantity",
        "in_transit_quantity", "transfer_in_quantity",
        "transfer_out_quantity", "shrink_quantity", "period_close_date",
    ],
    "issues": [
        "exception_id", "exception_type", "upstream_rule_code",
        "campaign_id", "store_id", "sku", "allocation_id",
        "confirmation_id", "severity", "exception_status",
        "exception_owner", "created_date", "due_date", "resolved_date",
        "resolution_time_hours", "resolution_type", "resolution_text",
        "waiver_reason", "root_cause_category", "root_cause_subcategory",
        "parent_id", "reopen_count", "sla_pause_reason",
        "sla_pause_started_at", "sla_pause_max_hours", "last_update_at",
        "last_update_type", "corrective_action_id",
        "corrective_action_owner", "corrective_action_deadline",
        "corrective_action_status",
    ],
}

TABLE_NAMES: list[str] = list(REQUIRED_COLUMNS.keys())

# Nullable columns per table (per docs/data-dictionary.md "Nullable: Yes").
# Only these columns may be empty without triggering a VAL-01 finding; every
# other column in REQUIRED_COLUMNS is treated as non-nullable.
NULLABLE_COLUMNS: dict[str, set[str]] = {
    "stores": {"field_rep"},
    "campaigns": set(),
    "allocation_plan": set(),
    "dispatch": set(),
    "store_confirmations": {
        "gps_coordinates", "checklist_completion_pct", "planogram_compliance",
        "pricing_accuracy", "on_shelf_availability_pct",
        "training_completion_flag", "audit_level", "audit_status",
        "compliance_score", "audit_comments", "exception_flag",
        "non_completion_reason", "campaign_store_status",
        "confirmation_timestamp",
    },
    "photo_proofs": {
        "photo_proof_url", "photo_timestamp", "photo_gps_coordinates",
        "photo_user_id", "photo_device_id", "photo_validation_reason",
    },
    "sales_daily": {
        "on_order_quantity", "in_transit_quantity", "transfer_in_quantity",
        "transfer_out_quantity", "shrink_quantity",
    },
    "issues": {
        "upstream_rule_code", "campaign_id", "sku", "allocation_id",
        "confirmation_id", "resolved_date", "resolution_time_hours",
        "resolution_type", "resolution_text", "waiver_reason",
        "root_cause_category", "root_cause_subcategory", "parent_id",
        "sla_pause_reason", "sla_pause_started_at", "sla_pause_max_hours",
        "last_update_type", "corrective_action_id",
        "corrective_action_owner", "corrective_action_deadline",
        "corrective_action_status",
    },
}

# Primary key per table.
PRIMARY_KEYS: dict[str, str] = {
    "stores": "store_id",
    "campaigns": "campaign_id",
    "allocation_plan": "allocation_id",
    "dispatch": "shipment_id",
    "store_confirmations": "confirmation_id",
    "photo_proofs": "photo_id",
    "sales_daily": "sales_id",
    "issues": "exception_id",
}

# Foreign key relationships: child table -> list of (child_column, parent_table,
# parent_column). parent_column defaults to PRIMARY_KEYS[parent_table] when not
# given; it is specified explicitly for non-PK references such as
# photo_proofs.visit_id -> store_confirmations.visit_id.
FOREIGN_KEYS: dict[str, list[tuple[str, str, str]]] = {
    "allocation_plan": [
        ("campaign_id", "campaigns", "campaign_id"),
        ("store_id", "stores", "store_id"),
    ],
    "dispatch": [
        ("allocation_id", "allocation_plan", "allocation_id"),
        ("campaign_id", "campaigns", "campaign_id"),
        ("store_id", "stores", "store_id"),
    ],
    "store_confirmations": [
        ("allocation_id", "allocation_plan", "allocation_id"),
        ("shipment_id", "dispatch", "shipment_id"),
        ("campaign_id", "campaigns", "campaign_id"),
        ("store_id", "stores", "store_id"),
    ],
    "photo_proofs": [
        ("confirmation_id", "store_confirmations", "confirmation_id"),
        ("visit_id", "store_confirmations", "visit_id"),
        ("store_id", "stores", "store_id"),
        ("campaign_id", "campaigns", "campaign_id"),
    ],
    "sales_daily": [
        ("campaign_id", "campaigns", "campaign_id"),
        ("store_id", "stores", "store_id"),
    ],
    "issues": [
        ("campaign_id", "campaigns", "campaign_id"),
        ("store_id", "stores", "store_id"),
        ("allocation_id", "allocation_plan", "allocation_id"),
        ("confirmation_id", "store_confirmations", "confirmation_id"),
    ],
}

# Reconciliation tolerance: a variance whose absolute value exceeds this is
# flagged. Quantities are integers so a tolerance of 0 means any non-zero
# variance is flagged.
QUANTITY_VARIANCE_TOLERANCE = 0


# ---------------------------------------------------------------------------
# Finding model
# ---------------------------------------------------------------------------

@dataclass
class ValidationFinding:
    """A single structured validation finding.

    Attributes:
        severity: "critical" | "warning" | "info".
        table:    name of the table the finding applies to.
        row_id:   identifier of the offending row (the PK value, or a composite
                  when no single PK is available). "" when table-level.
        rule_code: short stable code, e.g. "VAL-01".
        message:   human-readable description of the issue.
        suggested_action: what a human should do to resolve it.
    """

    severity: str
    table: str
    row_id: str
    rule_code: str
    message: str
    suggested_action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationReport:
    """Aggregated result of running all validation rules.

    Attributes:
        findings: list of ValidationFinding, ordered by severity then table.
        table_row_counts: snapshot of row counts per table at validation time.
    """

    findings: list[ValidationFinding] = field(default_factory=list)
    table_row_counts: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return len(self.findings)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "critical")

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "info")

    def by_severity(self, severity: str) -> list[ValidationFinding]:
        return [f for f in self.findings if f.severity == severity]

    def by_table(self, table: str) -> list[ValidationFinding]:
        return [f for f in self.findings if f.table == table]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "critical": self.critical_count,
            "warning": self.warning_count,
            "info": self.info_count,
            "table_row_counts": dict(self.table_row_counts),
            "findings": [f.to_dict() for f in self.findings],
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


def _sort_findings(findings: list[ValidationFinding]) -> list[ValidationFinding]:
    return sorted(
        findings,
        key=lambda f: (_SEVERITY_ORDER.get(f.severity, 9), f.table, f.row_id),
    )


def _row_id(row: dict[str, Any], table: str) -> str:
    pk = PRIMARY_KEYS.get(table)
    if pk and pk in row:
        return str(row[pk])
    # Fall back to a composite of campaign+store+sku if present.
    parts = [str(row.get(k, "")) for k in ("campaign_id", "store_id", "sku") if row.get(k) not in (None, "")]
    if parts:
        return "|".join(parts)
    return "<unknown>"


def _is_empty(value: Any) -> bool:
    """True if a value should be considered missing for required-column checks."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


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


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ValidationEngine:
    """Runs all 9 validation rules against a dict of tables.

    ``tables`` maps table name -> list of record dicts (as produced by
    :func:`retail_ops_control_tower.io.read_all_csv_tables` or the JSON store).
    """

    def __init__(self, tables: dict[str, list[dict[str, Any]]]):
        self.tables: dict[str, list[dict[str, Any]]] = tables
        self.findings: list[ValidationFinding] = []

    # -- public API ---------------------------------------------------------

    def validate(self) -> ValidationReport:
        """Run all rules and return a :class:`ValidationReport`."""
        self.findings = []
        self._check_required_columns()
        self._check_duplicate_keys()
        self._check_foreign_keys()
        self._check_planned_vs_dispatched()
        self._check_planned_vs_received()
        self._check_dispatch_without_plan()
        self._check_confirmation_without_dispatch()
        self._check_photo_without_confirmation()
        self._check_sales_without_campaign_store_match()
        self.findings = _sort_findings(self.findings)
        row_counts = {name: len(rows) for name, rows in self.tables.items()}
        return ValidationReport(findings=list(self.findings), table_row_counts=row_counts)

    # -- rule 1: required columns ------------------------------------------

    def _check_required_columns(self) -> None:
        for table, columns in REQUIRED_COLUMNS.items():
            rows = self.tables.get(table, [])
            if not rows:
                continue
            nullable = NULLABLE_COLUMNS.get(table, set())
            sample = rows[0]
            # Header presence: every required column must be a key in row 0.
            for col in columns:
                if col not in sample:
                    self.findings.append(ValidationFinding(
                        severity="critical",
                        table=table,
                        row_id="<table>",
                        rule_code="VAL-01",
                        message=f"Required column '{col}' is missing from table '{table}'.",
                        suggested_action=f"Regenerate the '{table}' table ensuring the '{col}' column is present.",
                    ))
            # Non-empty values for non-nullable columns (every row).
            for row in rows:
                rid = _row_id(row, table)
                for col in columns:
                    if col in nullable:
                        continue
                    if col in row and _is_empty(row.get(col)):
                        self.findings.append(ValidationFinding(
                            severity="warning",
                            table=table,
                            row_id=rid,
                            rule_code="VAL-01",
                            message=f"Required column '{col}' is empty in row '{rid}' of table '{table}'.",
                            suggested_action=f"Populate '{col}' for row '{rid}' or mark the field nullable in the schema.",
                        ))

    # -- rule 2: duplicate keys --------------------------------------------

    def _check_duplicate_keys(self) -> None:
        for table, pk in PRIMARY_KEYS.items():
            rows = self.tables.get(table, [])
            seen: dict[str, int] = {}
            for row in rows:
                key = str(row.get(pk, ""))
                if key == "":
                    continue
                seen[key] = seen.get(key, 0) + 1
            for key, count in seen.items():
                if count > 1:
                    self.findings.append(ValidationFinding(
                        severity="critical",
                        table=table,
                        row_id=key,
                        rule_code="VAL-02",
                        message=f"Duplicate primary key '{key}' appears {count} times in table '{table}'.",
                        suggested_action=f"De-duplicate rows with {pk}='{key}' in '{table}'.",
                    ))

    # -- rule 3: foreign keys ----------------------------------------------

    def _check_foreign_keys(self) -> None:
        for child_table, fk_list in FOREIGN_KEYS.items():
            child_rows = self.tables.get(child_table, [])
            for child_col, parent_table, parent_col in fk_list:
                parent_keys = {
                    str(r.get(parent_col, ""))
                    for r in self.tables.get(parent_table, [])
                    if r.get(parent_col) not in (None, "")
                }
                for row in child_rows:
                    fk_value = str(row.get(child_col, ""))
                    if fk_value == "":
                        continue  # nullable FK; absence is a separate finding only when non-nullable
                    if fk_value not in parent_keys:
                        self.findings.append(ValidationFinding(
                            severity="critical",
                            table=child_table,
                            row_id=_row_id(row, child_table),
                            rule_code="VAL-03",
                            message=(
                                f"Foreign key {child_col}='{fk_value}' in '{child_table}' "
                                f"has no matching {parent_col} in '{parent_table}'."
                            ),
                            suggested_action=(
                                f"Insert a '{parent_table}' row with {parent_col}='{fk_value}' "
                                f"or correct the {child_col} value in '{child_table}'."
                            ),
                        ))

    # -- rule 4: planned vs dispatched variance ----------------------------

    def _check_planned_vs_dispatched(self) -> None:
        allocations = {r["allocation_id"]: r for r in self.tables.get("allocation_plan", []) if r.get("allocation_id")}
        for ship in self.tables.get("dispatch", []):
            alloc_id = ship.get("allocation_id")
            if not alloc_id or alloc_id not in allocations:
                continue  # handled by rule 6
            planned = _to_int(allocations[alloc_id].get("planned_quantity"))
            shipped = _to_int(ship.get("shipped_quantity"))
            if planned is None or shipped is None:
                continue
            variance = shipped - planned
            if abs(variance) > QUANTITY_VARIANCE_TOLERANCE:
                self.findings.append(ValidationFinding(
                    severity="warning",
                    table="dispatch",
                    row_id=_row_id(ship, "dispatch"),
                    rule_code="VAL-04",
                    message=(
                        f"Planned vs dispatched variance: planned={planned}, "
                        f"shipped={shipped}, variance={variance} for allocation '{alloc_id}'."
                    ),
                    suggested_action=(
                        "Review DC pick accuracy; if the shortfall is a short-ship from the "
                        "supplier, raise a quantity_mismatch exception against the allocation."
                    ),
                ))

    # -- rule 5: planned vs received variance ------------------------------

    def _check_planned_vs_received(self) -> None:
        allocations = {r["allocation_id"]: r for r in self.tables.get("allocation_plan", []) if r.get("allocation_id")}
        for conf in self.tables.get("store_confirmations", []):
            alloc_id = conf.get("allocation_id")
            if not alloc_id or alloc_id not in allocations:
                continue  # handled by rule 7
            planned = _to_int(allocations[alloc_id].get("planned_quantity"))
            received = _to_int(conf.get("received_quantity"))
            if planned is None or received is None:
                continue
            variance = received - planned
            if abs(variance) > QUANTITY_VARIANCE_TOLERANCE:
                self.findings.append(ValidationFinding(
                    severity="warning",
                    table="store_confirmations",
                    row_id=_row_id(conf, "store_confirmations"),
                    rule_code="VAL-05",
                    message=(
                        f"Planned vs received variance: planned={planned}, "
                        f"received={received}, variance={variance} for allocation '{alloc_id}'."
                    ),
                    suggested_action=(
                        "Investigate the receiving exception type on this confirmation; "
                        "recount the stock and post a corrected receipt or open an issue."
                    ),
                ))

    # -- rule 6: dispatch without plan -------------------------------------

    def _check_dispatch_without_plan(self) -> None:
        allocation_ids = {
            str(r.get("allocation_id", "")) for r in self.tables.get("allocation_plan", []) if r.get("allocation_id")
        }
        for ship in self.tables.get("dispatch", []):
            alloc_id = str(ship.get("allocation_id", ""))
            if alloc_id and alloc_id not in allocation_ids:
                self.findings.append(ValidationFinding(
                    severity="critical",
                    table="dispatch",
                    row_id=_row_id(ship, "dispatch"),
                    rule_code="VAL-06",
                    message=f"Dispatch row references allocation_id='{alloc_id}' not present in allocation_plan.",
                    suggested_action="Create the missing allocation_plan row or correct the dispatch allocation_id.",
                ))

    # -- rule 7: confirmation without dispatch -----------------------------

    def _check_confirmation_without_dispatch(self) -> None:
        shipment_ids = {
            str(r.get("shipment_id", "")) for r in self.tables.get("dispatch", []) if r.get("shipment_id")
        }
        allocation_ids = {
            str(r.get("allocation_id", "")) for r in self.tables.get("allocation_plan", []) if r.get("allocation_id")
        }
        for conf in self.tables.get("store_confirmations", []):
            ship_id = str(conf.get("shipment_id", ""))
            alloc_id = str(conf.get("allocation_id", ""))
            if ship_id and ship_id not in shipment_ids:
                self.findings.append(ValidationFinding(
                    severity="critical",
                    table="store_confirmations",
                    row_id=_row_id(conf, "store_confirmations"),
                    rule_code="VAL-07",
                    message=f"Confirmation references shipment_id='{ship_id}' not present in dispatch.",
                    suggested_action="Create the missing dispatch/shipment record or correct the confirmation shipment_id.",
                ))
            elif alloc_id and alloc_id not in allocation_ids:
                # Only flag allocation mismatch if shipment is also missing/ok,
                # to avoid duplicating rule 3's FK finding with a different code.
                self.findings.append(ValidationFinding(
                    severity="critical",
                    table="store_confirmations",
                    row_id=_row_id(conf, "store_confirmations"),
                    rule_code="VAL-07",
                    message=f"Confirmation references allocation_id='{alloc_id}' not present in allocation_plan.",
                    suggested_action="Create the missing allocation_plan row or correct the confirmation allocation_id.",
                ))

    # -- rule 8: photo proof without confirmation --------------------------

    def _check_photo_without_confirmation(self) -> None:
        confirmation_ids = {
            str(r.get("confirmation_id", "")) for r in self.tables.get("store_confirmations", []) if r.get("confirmation_id")
        }
        for photo in self.tables.get("photo_proofs", []):
            conf_id = str(photo.get("confirmation_id", ""))
            if conf_id and conf_id not in confirmation_ids:
                self.findings.append(ValidationFinding(
                    severity="critical",
                    table="photo_proofs",
                    row_id=_row_id(photo, "photo_proofs"),
                    rule_code="VAL-08",
                    message=f"Photo proof references confirmation_id='{conf_id}' not present in store_confirmations.",
                    suggested_action="Create the missing confirmation record or correct the photo's confirmation_id.",
                ))

    # -- rule 9: sales record without campaign/store match ------------------

    def _check_sales_without_campaign_store_match(self) -> None:
        campaign_ids = {
            str(r.get("campaign_id", "")) for r in self.tables.get("campaigns", []) if r.get("campaign_id")
        }
        store_ids = {
            str(r.get("store_id", "")) for r in self.tables.get("stores", []) if r.get("store_id")
        }
        # Build the set of (campaign, store, sku) tuples that the allocation
        # plan says should exist, so we can flag sales for unplanned SKUs.
        planned_combos: set[tuple[str, str, str]] = set()
        for alloc in self.tables.get("allocation_plan", []):
            planned_combos.add((
                str(alloc.get("campaign_id", "")),
                str(alloc.get("store_id", "")),
                str(alloc.get("sku", "")),
            ))

        for sale in self.tables.get("sales_daily", []):
            cid = str(sale.get("campaign_id", ""))
            sid = str(sale.get("store_id", ""))
            sku = str(sale.get("sku", ""))
            rid = _row_id(sale, "sales_daily")
            problems: list[str] = []
            if cid and cid not in campaign_ids:
                problems.append(f"campaign_id='{cid}' is not in campaigns")
            if sid and sid not in store_ids:
                problems.append(f"store_id='{sid}' is not in stores")
            if (cid or sid or sku) and (cid, sid, sku) not in planned_combos and not problems:
                # Only flag combo mismatch when the individual refs are valid
                # but the combination was never allocated.
                problems.append(f"(campaign,store,sku)=({cid},{sid},{sku}) is not in allocation_plan")
            if problems:
                self.findings.append(ValidationFinding(
                    severity="warning" if problems[0].startswith("(") else "critical",
                    table="sales_daily",
                    row_id=rid,
                    rule_code="VAL-09",
                    message=f"Sales record {rid}: {'; '.join(problems)}.",
                    suggested_action="Correct the sales record's campaign/store/sku references or extend the allocation plan.",
                ))


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------

def validate_tables(tables: dict[str, list[dict[str, Any]]]) -> ValidationReport:
    """Run all validation rules against ``tables`` and return a report."""
    return ValidationEngine(tables).validate()


# ---------------------------------------------------------------------------
# Backward-compatible generation-time guards (PRD V-01..V-15).
# Kept so existing imports of validate_positive / validate_non_negative keep
# working; they raise on violation rather than returning findings.
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when a generation-time validation rule (V-01 to V-15) is violated."""


def validate_positive(value: float, field_name: str, rule_id: str) -> None:
    """Raise ValidationError if value is not positive."""
    if value <= 0:
        raise ValidationError(f"{rule_id}: {field_name} must be > 0, got {value}")


def validate_non_negative(value: float, field_name: str, rule_id: str) -> None:
    """Raise ValidationError if value is negative."""
    if value < 0:
        raise ValidationError(f"{rule_id}: {field_name} must be >= 0, got {value}")
