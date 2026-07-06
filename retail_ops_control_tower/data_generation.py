"""Deterministic sample data generator for the Retail Operations Control Tower.

Generates all 8 tables defined in ``docs/data-dictionary.md`` as CSV files.
Output is fully deterministic given the same seed.

Tables generated:
    1. stores              - store master data
    2. campaigns           - campaign master data
    3. allocation_plan     - per-store per-SKU allocation lines
    4. dispatch            - shipment records
    5. store_confirmations - receiving + visit records (with controlled exceptions)
    6. photo_proofs        - photo proof metadata
    7. sales_daily         - daily sales and on-hand records
    8. issues              - exception and corrective action records

Only *stored* (non-computed) fields are written to CSV. Computed fields
(marked ``(computed)`` in the data dictionary) are derived at runtime by the
reconciliation engine or dashboard and are intentionally omitted from the
simulation output.

Controlled exception cases are injected deterministically:
    - Missing confirmations: ~4% of allocations have no confirmation record.
    - Quantity mismatches: ~12% of confirmations have received != shipped.
    - Late setups: ~6% of confirmations have visit_date past the launch window.
    - Missing photo proofs: ~8% of confirmations have no photo_proofs row.
    - Photo validation failures: ~5% of submitted photos fail validation.
"""

from __future__ import annotations

import csv
import os
import random
from datetime import date, datetime, timedelta

import pandas as pd


# ---------------------------------------------------------------------------
# Name pools (fictional)
# ---------------------------------------------------------------------------

REGIONS = ["North", "South", "East", "West", "Central"]

REGION_TIMEZONES = {
    "North": "America/Chicago",
    "South": "America/Chicago",
    "East": "America/New_York",
    "West": "America/Los_Angeles",
    "Central": "America/Chicago",
}

REGION_OFFSETS = {
    "America/New_York": "-04:00",
    "America/Chicago": "-05:00",
    "America/Los_Angeles": "-07:00",
}

STORE_FORMATS = ["flagship", "standard", "kiosk", "drive-thru"]
FORMAT_WEIGHTS = [0.10, 0.60, 0.15, 0.15]

CAMPAIGN_TYPES = [
    "seasonal_lto",
    "product_launch",
    "promotional_pricing",
    "brand_activation",
]

CAMPAIGN_STATUSES = ["active", "completed", "active", "paused"]

AREA_MANAGER_NAMES = [
    "Sarah Chen", "James Okoro", "Maria Rodriguez", "David Park",
    "Lisa Wong", "Robert Taylor", "Emma Wilson", "Marcus Lee",
    "Jennifer Kim", "Ahmed Hassan", "Priya Sharma", "Carlos Mendez",
]

FIELD_REP_NAMES = [
    "Alex Turner", "Beth Morgan", "Chris Vega", "Dana Foster",
    "Evan Reed", "Fiona Garcia", "Greg Patel", "Hannah Brooks",
    "Ivan Petrov", "Julia Nash", "Kevin Lee", "Lara Ortiz",
    "Mike Chen", "Nora Smith", "Omar Faruk", "Pia Romano",
]

HQ_OWNERS = [
    "Maria Rodriguez", "Jennifer Kim", "Robert Taylor",
    "Sophie Laurent", "Thomas Wright",
]

PLANNER_OWNERS = [
    "David Park", "Emma Wilson", "Marcus Lee", "Nina Patel",
]

RECEIVING_OWNERS = [
    "Lisa Wong", "Tom Harris", "Rachel Green", "Ben Carter",
    "Sofia Reyes", "Mark Thompson", "Amy Davis", "Kevin Liu",
    "Jess Brooks", "Ravi Kumar",
]

# City/state pools per region (fictional)
REGION_CITIES = {
    "North": [
        ("Springfield", "IL"), ("Madison", "WI"), ("Des Moines", "IA"),
        ("Columbus", "OH"), ("Minneapolis", "MN"), ("Fargo", "ND"),
    ],
    "South": [
        ("Austin", "TX"), ("Nashville", "TN"), ("Charlotte", "NC"),
        ("Atlanta", "GA"), ("Memphis", "TN"), ("Birmingham", "AL"),
    ],
    "East": [
        ("Boston", "MA"), ("Philadelphia", "PA"), ("Newark", "NJ"),
        ("Baltimore", "MD"), ("Hartford", "CT"), ("Providence", "RI"),
    ],
    "West": [
        ("Portland", "OR"), ("Denver", "CO"), ("Phoenix", "AZ"),
        ("Las Vegas", "NV"), ("Seattle", "WA"), ("Sacramento", "CA"),
    ],
    "Central": [
        ("Kansas City", "MO"), ("Omaha", "NE"), ("Tulsa", "OK"),
        ("Wichita", "KS"), ("Little Rock", "AR"), ("St. Louis", "MO"),
    ],
}

STORE_NAME_PREFIXES = [
    "Central", "Riverside", "Sunset", "Highland", "Maple", "Oak",
    "Cedar", "Pine", "Valley", "Summit", "Harbor", "Lakeside",
    "Uptown", "Downtown", "Crossroads", "Greenwood", "Fairfield",
    "Northgate", "Southpark", "Eastgate", "Westend", "Spring",
    "Forest", "Brookside", "Midtown", "Old Town", "Plaza",
]
STORE_NAME_SUFFIXES = [
    "Plaza", "Mall", "Center", "Square", "Market", "Station",
    "Commons", "Galleria", "District", "Quarter",
]

DC_IDS = ["DC-01", "DC-02", "DC-03"]
CARRIERS = ["FastFreight Co", "QuickShip Logistics", "Reliable Transport"]

POSM_TEMPLATES = [
    "poster-A1", "standee-floor", "tent-card", "shelf-strip",
    "wobbler", "menu-board", "standee-countertop", "banner",
]

PHOTO_TYPES = ["posm_deployment", "shelf_display", "planogram", "pricing", "store_front"]

# Campaign templates for generation
CAMPAIGN_TEMPLATES = [
    {
        "campaign_id": "C-2026-PEACH",
        "campaign_name": "Summer Peach LTO 2026",
        "campaign_type": "seasonal_lto",
        "start_date": date(2026, 7, 1),
        "end_date": date(2026, 7, 28),
        "status": "active",
        "hq_owner": "Maria Rodriguez",
        "sku_prefix": "PEACH",
        "sku_count": 12,
        "hero_sku": "PEACH-001",
        "planner_owner": "David Park",
        "posm": ["poster-A1", "standee-floor", "tent-card", "menu-board-peach"],
    },
    {
        "campaign_id": "C-2026-BTS",
        "campaign_name": "Back to School Promo 2026",
        "campaign_type": "promotional_pricing",
        "start_date": date(2026, 8, 1),
        "end_date": date(2026, 8, 28),
        "status": "active",
        "hq_owner": "Jennifer Kim",
        "sku_prefix": "BTS",
        "sku_count": 10,
        "hero_sku": "BTS-001",
        "planner_owner": "Emma Wilson",
        "posm": ["poster-A2", "shelf-strip", "wobbler", "menu-board-bts"],
    },
    {
        "campaign_id": "C-2026-FCL",
        "campaign_name": "Fall Coffee Launch 2026",
        "campaign_type": "product_launch",
        "start_date": date(2026, 9, 1),
        "end_date": date(2026, 9, 28),
        "status": "active",
        "hq_owner": "Robert Taylor",
        "sku_prefix": "FCL",
        "sku_count": 10,
        "hero_sku": "FCL-001",
        "planner_owner": "Marcus Lee",
    },
    {
        "campaign_id": "C-2026-HOL",
        "campaign_name": "Holiday Brand Activation 2026",
        "campaign_type": "brand_activation",
        "start_date": date(2026, 11, 1),
        "end_date": date(2026, 11, 28),
        "status": "draft",
        "hq_owner": "Sophie Laurent",
        "sku_prefix": "HOL",
        "sku_count": 8,
        "hero_sku": "HOL-001",
        "planner_owner": "Nina Patel",
    },
]

# Exception type -> default owner and SLA (hours)
EXCEPTION_DEFAULTS = {
    "missing_confirmation": {"owner": "Field Operations", "sla_hours": 48, "rule_code": "EX-01"},
    "quantity_mismatch": {"owner": "DC Operations", "sla_hours": 48, "rule_code": "EX-05"},
    "missing_photo_proof": {"owner": "Field Representative", "sla_hours": 48, "rule_code": "EX-09"},
    "late_setup": {"owner": "Store Manager", "sla_hours": 48, "rule_code": "EX-03"},
    "stockout_risk": {"owner": "Replenishment Planner", "sla_hours": 24, "rule_code": "EX-10"},
    "overstock_risk": {"owner": "Merchant", "sla_hours": 168, "rule_code": "EX-13"},
    "low_sell_through": {"owner": "Merchant + Planner", "sla_hours": 168, "rule_code": "EX-15"},
    "unresolved_issue_aging": {"owner": "Operations Lead", "sla_hours": 24, "rule_code": "EX-24"},
}

SEVERITY_BY_TYPE = {
    "missing_confirmation": "watch",
    "quantity_mismatch": "watch",
    "missing_photo_proof": "watch",
    "late_setup": "critical",
    "stockout_risk": "critical",
    "overstock_risk": "watch",
    "low_sell_through": "watch",
    "unresolved_issue_aging": "info",
}

ROOT_CAUSE_CATEGORIES = ["supplier", "dc", "store", "system", "forecast", "customer", "logistics"]
ROOT_CAUSE_SUBCATEGORIES = {
    "supplier": ["late_delivery", "short_pick", "quality_defect", "capacity"],
    "dc": ["mislabel", "packing_error", "dispatch_delay", "carton_damage"],
    "store": ["receiving_error", "staff_absence", "training_gap", "space_constraint"],
    "system": ["sync_failure", "data_entry", "integration_timeout"],
    "forecast": ["demand_overestimate", "demand_underestimate", "seasonality_shift"],
    "customer": ["low_footfall", "preference_shift", "price_sensitivity"],
    "logistics": ["transit_damage", "route_delay", "carrier_loss", "address_error"],
}

RESOLUTION_TYPES = ["reposted", "corrected", "system_fix", "write_off", "good_will", "no_action_required"]
RESOLUTION_TEXTS = {
    "reposted": "Confirmation reposted by field rep after initial system error.",
    "corrected": "Quantity corrected after recount at store receiving dock.",
    "system_fix": "Integration patch deployed; data pipeline resynced successfully.",
    "write_off": "Damaged units written off after store-level damage assessment.",
    "good_will": "Good will credit issued to store for the shortfall in shipment.",
    "no_action_required": "Within tolerance threshold; no corrective action needed.",
}

WAIVER_REASONS = [
    "Waived due to system outage affecting all stores in the region that day.",
    "Store was closed for renovation; exception is not operationally actionable.",
    "Within acceptable variance tolerance per revised business rules.",
    "Duplicate of another tracked exception; merged into parent record.",
]

PAUSE_REASONS = ["vendor", "store", "system", "transit"]
PAUSE_MAX_HOURS = {"vendor": 72, "store": 48, "system": 4, "transit": 24}

CORRECTIVE_ACTION_STATUSES = ["open", "in_progress", "resolved"]


# ---------------------------------------------------------------------------
# Stored column definitions (excludes computed fields per data dictionary)
# ---------------------------------------------------------------------------

TABLE_COLUMNS: dict[str, list[str]] = {
    "stores": [
        "store_id", "store_name", "region", "store_format", "area_manager",
        "field_rep", "selling_area_sqft", "city", "state", "open_date",
        "is_active", "timezone",
    ],
    "campaigns": [
        "campaign_id", "campaign_name", "campaign_type", "campaign_start_date",
        "campaign_end_date", "campaign_status", "hq_owner", "target_store_count",
        "sku_list", "hero_sku", "launch_window_days", "supplier_lead_time_weeks",
        "period_sell_through_target", "full_price_target", "posm_list",
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

TABLE_NAMES = list(TABLE_COLUMNS.keys())


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class SampleDataGenerator:
    """Deterministic generator for all 8 data tables.

    Parameters are clamped to the ranges specified in the task:
        - 80-150 stores
        - 3-5 regions
        - 8-12 area managers
        - 2-4 campaigns
    """

    def __init__(
        self,
        seed: int = 42,
        store_count: int = 100,
        region_count: int = 4,
        area_manager_count: int = 10,
        campaign_count: int = 3,
    ):
        self.seed = seed
        self.rng = random.Random(seed)
        self.store_count = max(80, min(150, store_count))
        self.region_count = max(3, min(5, region_count))
        self.area_manager_count = max(8, min(12, area_manager_count))
        self.campaign_count = max(2, min(4, campaign_count))

        self._regions = REGIONS[: self.region_count]
        self._area_managers = AREA_MANAGER_NAMES[: self.area_manager_count]
        self._campaign_templates = CAMPAIGN_TEMPLATES[: self.campaign_count]
        self._exception_events: list[dict] = []
        self._store_index: dict[str, dict] = {}
        self._allocation_index: dict[str, dict] = {}
        self._confirmation_index: dict[str, dict] = {}
        self._allocation_by_store: dict[str, list[dict]] = {}

    # -- public API ---------------------------------------------------------

    def generate(self) -> dict[str, list[dict]]:
        """Generate all 8 tables. Returns a dict mapping table name to list of record dicts."""
        self._exception_events = []

        stores = self._generate_stores()
        campaigns = self._generate_campaigns()
        allocation_plan = self._generate_allocation_plan(stores, campaigns)
        dispatch = self._generate_dispatch(allocation_plan)
        confirmations = self._generate_confirmations(dispatch, campaigns)
        photos = self._generate_photos(confirmations)
        sales = self._generate_sales(allocation_plan, confirmations, campaigns)
        issues = self._generate_issues()

        return {
            "stores": stores,
            "campaigns": campaigns,
            "allocation_plan": allocation_plan,
            "dispatch": dispatch,
            "store_confirmations": confirmations,
            "photo_proofs": photos,
            "sales_daily": sales,
            "issues": issues,
        }

    # -- table generators ---------------------------------------------------

    def _generate_stores(self) -> list[dict]:
        """Generate the stores table (80-150 rows)."""
        stores: list[dict] = []
        used_names: set[str] = set()

        for i in range(1, self.store_count + 1):
            store_id = f"S-{i:03d}"
            region = self.rng.choice(self._regions)
            tz = REGION_TIMEZONES[region]
            store_format = self.rng.choices(STORE_FORMATS, weights=FORMAT_WEIGHTS, k=1)[0]

            # Unique store name
            for _ in range(50):
                name = f"{self.rng.choice(STORE_NAME_PREFIXES)} {self.rng.choice(STORE_NAME_SUFFIXES)}"
                if name not in used_names:
                    used_names.add(name)
                    break

            city, state = self.rng.choice(REGION_CITIES[region])

            sqft_by_format = {
                "flagship": self.rng.randint(3000, 6000),
                "standard": self.rng.randint(800, 2500),
                "kiosk": self.rng.randint(100, 400),
                "drive-thru": self.rng.randint(400, 1200),
            }

            open_year = self.rng.randint(2018, 2025)
            open_month = self.rng.randint(1, 12)
            open_day = self.rng.randint(1, 28)

            store = {
                "store_id": store_id,
                "store_name": name,
                "region": region,
                "store_format": store_format,
                "area_manager": self.rng.choice(self._area_managers),
                "field_rep": self.rng.choice(FIELD_REP_NAMES) if self.rng.random() > 0.1 else "",
                "selling_area_sqft": sqft_by_format[store_format],
                "city": city,
                "state": state,
                "open_date": f"{open_year}-{open_month:02d}-{open_day:02d}",
                "is_active": self.rng.random() > 0.03,
                "timezone": tz,
            }
            stores.append(store)
            self._store_index[store_id] = store

        return stores

    def _generate_campaigns(self) -> list[dict]:
        """Generate the campaigns table (2-4 rows)."""
        campaigns: list[dict] = []
        for tmpl in self._campaign_templates:
            sku_count = tmpl["sku_count"]
            sku_list = [f"{tmpl['sku_prefix']}-{i:03d}" for i in range(1, sku_count + 1)]
            posm = tmpl.get("posm", POSM_TEMPLATES[:4])

            # target_store_count filled after allocation; use estimate
            # ~35-50% of stores per campaign
            est_target = int(self.store_count * self.rng.uniform(0.35, 0.50))

            campaign = {
                "campaign_id": tmpl["campaign_id"],
                "campaign_name": tmpl["campaign_name"],
                "campaign_type": tmpl["campaign_type"],
                "campaign_start_date": tmpl["start_date"].isoformat(),
                "campaign_end_date": tmpl["end_date"].isoformat(),
                "campaign_status": tmpl["status"],
                "hq_owner": tmpl["hq_owner"],
                "target_store_count": est_target,
                "sku_list": ";".join(sku_list),
                "hero_sku": tmpl["hero_sku"],
                "launch_window_days": 7,
                "supplier_lead_time_weeks": 2,
                "period_sell_through_target": round(self.rng.uniform(0.65, 0.75), 2),
                "full_price_target": round(self.rng.uniform(0.75, 0.85), 2),
                "posm_list": ";".join(posm),
            }
            campaigns.append(campaign)

        return campaigns

    def _generate_allocation_plan(
        self, stores: list[dict], campaigns: list[dict]
    ) -> list[dict]:
        """Generate the allocation_plan table (per store-SKU-campaign)."""
        allocation_plan: list[dict] = []
        seq = 0

        for campaign in campaigns:
            cid = campaign["campaign_id"]
            sku_list = campaign["sku_list"].split(";")
            hero_sku = campaign["hero_sku"]
            planner = self._campaign_templates[
                [t["campaign_id"] for t in self._campaign_templates].index(cid)
            ]["planner_owner"]

            # Select stores for this campaign (~35-50% of total)
            target_pct = self.rng.uniform(0.35, 0.50)
            n_stores = max(10, int(self.store_count * target_pct))
            campaign_stores = self.rng.sample(stores, n_stores)

            # Update target_store_count to actual
            campaign["target_store_count"] = n_stores

            for store in campaign_stores:
                store_id = store["store_id"]
                for sku in sku_list:
                    seq += 1
                    is_hero = sku == hero_sku

                    if is_hero:
                        planned_qty = self.rng.choice([180, 200, 220])
                    else:
                        fmt = store["store_format"]
                        if fmt == "flagship":
                            planned_qty = self.rng.randint(80, 150)
                        elif fmt == "standard":
                            planned_qty = self.rng.randint(40, 100)
                        else:
                            planned_qty = self.rng.randint(15, 60)

                    start_date = date.fromisoformat(campaign["campaign_start_date"])
                    receipt_date = start_date - timedelta(days=self.rng.randint(2, 5))

                    allocation = {
                        "allocation_id": f"A-{seq:03d}-{store_id}-{sku}",
                        "campaign_id": cid,
                        "sku": sku,
                        "store_id": store_id,
                        "planned_quantity": planned_qty,
                        "planned_receipt_date": receipt_date.isoformat(),
                        "allocation_phase": self.rng.choices(
                            ["initial", "replenishment", "chase", "transfer"],
                            weights=[0.80, 0.12, 0.05, 0.03],
                        )[0],
                        "allocation_method": self.rng.choice(
                            ["fair_share", "door_index", "size_curve", "manual_override"]
                        ),
                        "holdback_pct": round(self.rng.uniform(0.05, 0.15), 2),
                        "planner_owner": planner,
                    }
                    allocation_plan.append(allocation)
                    self._allocation_index[allocation["allocation_id"]] = allocation

                    if store_id not in self._allocation_by_store:
                        self._allocation_by_store[store_id] = []
                    self._allocation_by_store[store_id].append(allocation)

        return allocation_plan

    def _generate_dispatch(self, allocation_plan: list[dict]) -> list[dict]:
        """Generate the dispatch table (one shipment per allocation line)."""
        dispatch_records: list[dict] = []

        for alloc in allocation_plan:
            alloc_id = alloc["allocation_id"]
            store = self._store_index[alloc["store_id"]]
            planned_qty = alloc["planned_quantity"]

            # Shipped quantity: 88-100% of planned (some short ships)
            fill = self.rng.uniform(0.88, 1.0)
            shipped_qty = int(planned_qty * fill)

            receipt_date = date.fromisoformat(alloc["planned_receipt_date"])
            shipped_date = receipt_date - timedelta(days=self.rng.randint(2, 4))

            shipment = {
                "shipment_id": f"SH-{alloc_id.split('-', 1)[1]}",
                "allocation_id": alloc_id,
                "campaign_id": alloc["campaign_id"],
                "sku": alloc["sku"],
                "store_id": alloc["store_id"],
                "shipped_quantity": shipped_qty,
                "shipped_date": shipped_date.isoformat(),
                "expected_arrival_date": receipt_date.isoformat(),
                "carton_count": max(1, shipped_qty // 24),
                "dc_id": self.rng.choice(DC_IDS),
                "carrier": self.rng.choice(CARRIERS),
            }
            dispatch_records.append(shipment)

        return dispatch_records

    def _generate_confirmations(
        self, dispatch: list[dict], campaigns: list[dict]
    ) -> list[dict]:
        """Generate store_confirmations with controlled late/missing/mismatch cases."""
        confirmations: list[dict] = []
        campaign_map = {c["campaign_id"]: c for c in campaigns}
        seq = 0

        for ship in dispatch:
            # ~4% of allocations have NO confirmation (missing_confirmation)
            if self.rng.random() < 0.04:
                self._exception_events.append({
                    "type": "missing_confirmation",
                    "campaign_id": ship["campaign_id"],
                    "store_id": ship["store_id"],
                    "sku": ship["sku"],
                    "allocation_id": ship["allocation_id"],
                    "confirmation_id": "",
                    "shipment_id": ship["shipment_id"],
                    "severity": "critical" if ship["sku"] == campaign_map[ship["campaign_id"]]["hero_sku"] else "watch",
                    "created_offset_days": 0,
                })
                continue

            seq += 1
            ship_id_parts = ship["shipment_id"]
            confirmation_id = f"CONF-{seq:03d}-{ship['store_id']}-{ship['sku']}"
            visit_id = f"V-{seq:03d}-{ship['store_id']}"

            campaign = campaign_map[ship["campaign_id"]]
            start_date = date.fromisoformat(campaign["campaign_start_date"])
            launch_window = campaign["launch_window_days"]
            tz = self._store_index[ship["store_id"]]["timezone"]
            tz_offset = REGION_OFFSETS.get(tz, "-05:00")

            expected_arrival = date.fromisoformat(ship["expected_arrival_date"])
            shipped_qty = ship["shipped_quantity"]

            # ~12% have quantity mismatches
            mismatch_roll = self.rng.random()
            if mismatch_roll < 0.06:
                # Shortage
                received_qty = int(shipped_qty * self.rng.uniform(0.80, 0.94))
                receipt_status = "partial"
                receiving_exception = "shortage"
            elif mismatch_roll < 0.09:
                # Overage
                received_qty = int(shipped_qty * self.rng.uniform(1.02, 1.10))
                receipt_status = "partial"
                receiving_exception = "overage"
            elif mismatch_roll < 0.11:
                # Damage
                received_qty = int(shipped_qty * self.rng.uniform(0.85, 0.95))
                receipt_status = "partial"
                receiving_exception = "damage"
            elif mismatch_roll < 0.12:
                # Substitution
                received_qty = shipped_qty
                receipt_status = "accepted"
                receiving_exception = "substitution"
            else:
                # Normal
                received_qty = shipped_qty
                receipt_status = "accepted"
                receiving_exception = "none"

            # ~6% are late setups (visit_date past launch window)
            is_late = self.rng.random() < 0.06
            if is_late:
                visit_date = start_date + timedelta(days=self.rng.randint(launch_window + 1, 14))
                campaign_store_status = self.rng.choice(["in_progress", "not_started"])
                visit_status = self.rng.choice(["completed", "in_progress"])
            else:
                visit_date = start_date + timedelta(days=self.rng.randint(0, launch_window))
                campaign_store_status = "completed"
                visit_status = "completed"

            received_date = expected_arrival + timedelta(days=self.rng.randint(0, 2))

            # Visit timestamp
            visit_hour = self.rng.randint(8, 17)
            visit_minute = self.rng.choice([0, 15, 30, 45])
            visit_ts = f"{visit_date}T{visit_hour:02d}:{visit_minute:02d}:00{tz_offset}"

            # Confirmation timestamp (shortly after visit)
            conf_hour = visit_hour + self.rng.randint(0, 3)
            if conf_hour > 23:
                conf_hour = 23
            conf_minute = self.rng.choice([0, 15, 30, 45])
            conf_ts = f"{visit_date}T{conf_hour:02d}:{conf_minute:02d}:00{tz_offset}"

            has_exception = (
                receiving_exception != "none" or is_late
            )

            # GPS coordinates (fictional, roughly mapped to region)
            store = self._store_index[ship["store_id"]]
            lat = round(self.rng.uniform(25.0, 48.0), 4)
            lon = round(self.rng.uniform(-120.0, -70.0), 4)
            gps = f"{lat},{lon}"

            checklist_pct = round(self.rng.uniform(0.80, 1.00), 2) if not is_late else round(self.rng.uniform(0.50, 0.79), 2)
            planogram = self.rng.random() > 0.08
            pricing = self.rng.random() > 0.06
            on_shelf = round(self.rng.uniform(0.80, 1.00), 2) if not is_late else round(self.rng.uniform(0.40, 0.79), 2)
            training = self.rng.random() > 0.05
            audit_level = self.rng.choices(["L1", "L2", "L3"], weights=[0.70, 0.20, 0.10])[0]

            if has_exception and self.rng.random() < 0.3:
                audit_status = "rejected"
                compliance = round(self.rng.uniform(40, 69), 1)
            elif self.rng.random() < 0.10:
                audit_status = "pending"
                compliance = round(self.rng.uniform(60, 85), 1)
            else:
                audit_status = "approved"
                compliance = round(self.rng.uniform(70, 98), 1)

            audit_comments = ""
            if audit_status == "rejected":
                if is_late:
                    audit_comments = "Campaign setup not completed by launch date."
                elif receiving_exception == "shortage":
                    audit_comments = "Significant shortage in received quantity."
                elif receiving_exception == "damage":
                    audit_comments = "Damaged units found during receiving check."
                else:
                    audit_comments = "Multiple compliance issues identified."
            elif receiving_exception != "none":
                audit_comments = f"Minor {receiving_exception} noted during receiving."

            non_completion_reason = ""
            if campaign_store_status == "not_started":
                non_completion_reason = "Store did not begin setup; staff absence."
            elif campaign_store_status == "in_progress":
                non_completion_reason = "Setup in progress; awaiting POSM delivery."

            confirmation = {
                "confirmation_id": confirmation_id,
                "allocation_id": ship["allocation_id"],
                "shipment_id": ship["shipment_id"],
                "campaign_id": ship["campaign_id"],
                "store_id": ship["store_id"],
                "sku": ship["sku"],
                "received_quantity": received_qty,
                "received_date": received_date.isoformat(),
                "receipt_status": receipt_status,
                "receiving_exception_type": receiving_exception,
                "receiving_owner": self.rng.choice(RECEIVING_OWNERS),
                "visit_id": visit_id,
                "visit_date": visit_date.isoformat(),
                "visit_timestamp": visit_ts,
                "visit_status": visit_status,
                "gps_coordinates": gps,
                "checklist_completion_pct": checklist_pct,
                "planogram_compliance": planogram,
                "pricing_accuracy": pricing,
                "on_shelf_availability_pct": on_shelf,
                "training_completion_flag": training,
                "audit_level": audit_level,
                "audit_status": audit_status,
                "compliance_score": compliance,
                "audit_comments": audit_comments,
                "exception_flag": has_exception,
                "non_completion_reason": non_completion_reason,
                "campaign_store_status": campaign_store_status,
                "confirmation_timestamp": conf_ts,
            }
            confirmations.append(confirmation)
            self._confirmation_index[confirmation_id] = confirmation

            # Record exception events for issue generation
            if receiving_exception != "none":
                self._exception_events.append({
                    "type": "quantity_mismatch",
                    "campaign_id": ship["campaign_id"],
                    "store_id": ship["store_id"],
                    "sku": ship["sku"],
                    "allocation_id": ship["allocation_id"],
                    "confirmation_id": confirmation_id,
                    "shipment_id": ship["shipment_id"],
                    "severity": "watch",
                    "created_offset_days": 0,
                })

            if is_late:
                self._exception_events.append({
                    "type": "late_setup",
                    "campaign_id": ship["campaign_id"],
                    "store_id": ship["store_id"],
                    "sku": ship["sku"],
                    "allocation_id": ship["allocation_id"],
                    "confirmation_id": confirmation_id,
                    "shipment_id": ship["shipment_id"],
                    "severity": "critical",
                    "created_offset_days": (visit_date - start_date).days,
                })

        return confirmations

    def _generate_photos(self, confirmations: list[dict]) -> list[dict]:
        """Generate photo_proofs table (1-4 photos per confirmation, some missing)."""
        photos: list[dict] = []
        seq = 0

        for conf in confirmations:
            # ~8% of confirmations have NO photos (missing_photo_proof)
            if self.rng.random() < 0.08:
                self._exception_events.append({
                    "type": "missing_photo_proof",
                    "campaign_id": conf["campaign_id"],
                    "store_id": conf["store_id"],
                    "sku": conf["sku"],
                    "allocation_id": conf["allocation_id"],
                    "confirmation_id": conf["confirmation_id"],
                    "shipment_id": "",
                    "severity": "watch",
                    "created_offset_days": 0,
                })
                continue

            # 1-4 photos per confirmation
            n_photos = self.rng.randint(1, 4)
            for _ in range(n_photos):
                seq += 1
                photo_id = f"PH-{seq:03d}-{conf['visit_id']}"

                # ~5% of photos fail validation
                if self.rng.random() < 0.05:
                    validation_status = "failed"
                    validation_reason = self.rng.choice([
                        "no GPS coordinates captured",
                        "no timestamp recorded",
                        "out of geofence",
                        "image quality too low",
                    ])
                else:
                    validation_status = "passed"
                    validation_reason = ""

                store = self._store_index[conf["store_id"]]
                lat = round(self.rng.uniform(25.0, 48.0), 4)
                lon = round(self.rng.uniform(-120.0, -70.0), 4)

                visit_date = date.fromisoformat(conf["visit_date"])
                photo_hour = self.rng.randint(8, 18)
                photo_min = self.rng.choice([0, 15, 30, 45])
                tz_offset = REGION_OFFSETS.get(store["timezone"], "-05:00")
                photo_ts = f"{visit_date}T{photo_hour:02d}:{photo_min:02d}:00{tz_offset}"

                photo = {
                    "photo_id": photo_id,
                    "confirmation_id": conf["confirmation_id"],
                    "visit_id": conf["visit_id"],
                    "store_id": conf["store_id"],
                    "campaign_id": conf["campaign_id"],
                    "photo_proof_url": f"photos/{photo_id}.jpg",
                    "photo_timestamp": photo_ts,
                    "photo_gps_coordinates": f"{lat},{lon}",
                    "photo_user_id": f"REP-{self.rng.randint(1, 16):03d}",
                    "photo_device_id": f"TAB-{self.rng.randint(1, 20):03d}",
                    "photo_type": self.rng.choice(PHOTO_TYPES),
                    "photo_validation_status": validation_status,
                    "photo_validation_reason": validation_reason,
                }
                photos.append(photo)

        return photos

    def _generate_sales(
        self,
        allocation_plan: list[dict],
        confirmations: list[dict],
        campaigns: list[dict],
    ) -> list[dict]:
        """Generate daily sales table (per store-SKU per day per campaign)."""
        sales: list[dict] = []
        campaign_map = {c["campaign_id"]: c for c in campaigns}

        # Build received quantity lookup: (allocation_id) -> received_qty
        received_map: dict[str, int] = {}
        for conf in confirmations:
            received_map[conf["allocation_id"]] = conf["received_quantity"]

        for alloc in allocation_plan:
            alloc_id = alloc["allocation_id"]
            campaign = campaign_map[alloc["campaign_id"]]
            start_date = date.fromisoformat(campaign["campaign_start_date"])
            end_date = date.fromisoformat(campaign["campaign_end_date"])
            campaign_days = (end_date - start_date).days + 1
            store = self._store_index[alloc["store_id"]]

            # Use received qty if available, else shipped (fallback: planned * 0.9)
            received_qty = received_map.get(alloc_id, int(alloc["planned_quantity"] * 0.9))
            if received_qty <= 0:
                continue

            is_hero = alloc["sku"] == campaign["hero_sku"]
            fmt = store["store_format"]

            # Daily demand model
            base_demand = alloc["planned_quantity"] / campaign_days
            fmt_mult = {"flagship": 1.4, "standard": 1.0, "kiosk": 0.6, "drive-thru": 0.8}[fmt]
            hero_mult = 1.3 if is_hero else 0.8
            daily_demand = base_demand * fmt_mult * hero_mult

            # Some stores sell faster (stockout), some slower (overstock)
            velocity = self.rng.uniform(0.7, 1.4)

            inventory = received_qty
            cumulative_sold = 0

            for day_num in range(1, campaign_days + 1):
                sales_date = start_date + timedelta(days=day_num - 1)

                # Demand curve: ramp up (days 1-7), peak (8-21), decline (22+)
                if day_num <= 7:
                    curve = 0.40 + (day_num / 7.0) * 0.60
                elif day_num <= 21:
                    curve = 1.0 + self.rng.uniform(-0.1, 0.2)
                else:
                    remaining = campaign_days - day_num + 1
                    curve = max(0.3, remaining / 7.0)

                noise = self.rng.uniform(0.80, 1.20)
                demand = max(0, int(daily_demand * velocity * curve * noise))

                if inventory <= 0:
                    units_sold = 0
                else:
                    units_sold = min(demand, inventory)

                inventory -= units_sold
                cumulative_sold += units_sold

                # Markdown increases later in campaign
                if day_num > 14:
                    markdown_pct = self.rng.uniform(0.05, 0.25)
                else:
                    markdown_pct = self.rng.uniform(0.0, 0.05)
                units_markdown = int(units_sold * markdown_pct)
                units_full_price = units_sold - units_markdown

                # Mostly-zero optional fields with occasional non-zero values
                on_order = 0
                if inventory < 20 and self.rng.random() < 0.15:
                    on_order = self.rng.randint(20, 60)

                transfer_in = self.rng.randint(0, 10) if self.rng.random() < 0.05 else 0
                transfer_out = self.rng.randint(0, 10) if self.rng.random() < 0.05 else 0
                shrink = self.rng.randint(0, 2) if self.rng.random() < 0.03 else 0
                in_transit = 0

                on_hand = max(0, inventory + transfer_in - transfer_out - shrink)

                sales_id = (
                    f"SALE-{sales_date.isoformat()}-{alloc['store_id']}-{alloc['sku']}"
                )

                record = {
                    "sales_id": sales_id,
                    "campaign_id": alloc["campaign_id"],
                    "store_id": alloc["store_id"],
                    "sku": alloc["sku"],
                    "sales_date": sales_date.isoformat(),
                    "day_of_campaign": day_num,
                    "units_sold": units_sold,
                    "units_sold_full_price": units_full_price,
                    "units_sold_markdown": units_markdown,
                    "on_hand_quantity": on_hand,
                    "on_order_quantity": on_order,
                    "in_transit_quantity": in_transit,
                    "transfer_in_quantity": transfer_in,
                    "transfer_out_quantity": transfer_out,
                    "shrink_quantity": shrink,
                    "period_close_date": sales_date.isoformat(),
                }
                sales.append(record)

            # Record stockout/overstock exceptions
            sell_through = cumulative_sold / received_qty if received_qty > 0 else 0
            if inventory <= 0 and cumulative_sold > 0:
                self._exception_events.append({
                    "type": "stockout_risk",
                    "campaign_id": alloc["campaign_id"],
                    "store_id": alloc["store_id"],
                    "sku": alloc["sku"],
                    "allocation_id": alloc_id,
                    "confirmation_id": "",
                    "shipment_id": "",
                    "severity": "critical",
                    "created_offset_days": campaign_days,
                })
            elif sell_through < 0.30 and campaign_days > 0:
                self._exception_events.append({
                    "type": "overstock_risk",
                    "campaign_id": alloc["campaign_id"],
                    "store_id": alloc["store_id"],
                    "sku": alloc["sku"],
                    "allocation_id": alloc_id,
                    "confirmation_id": "",
                    "shipment_id": "",
                    "severity": "watch",
                    "created_offset_days": campaign_days,
                })

            if sell_through < 0.50 and campaign_days > 0:
                self._exception_events.append({
                    "type": "low_sell_through",
                    "campaign_id": alloc["campaign_id"],
                    "store_id": alloc["store_id"],
                    "sku": alloc["sku"],
                    "allocation_id": alloc_id,
                    "confirmation_id": "",
                    "shipment_id": "",
                    "severity": "watch",
                    "created_offset_days": campaign_days,
                })

        return sales

    def _generate_issues(self) -> list[dict]:
        """Generate the issues table from tracked exception events."""
        issues: list[dict] = []
        seq = 0

        # Add some unresolved aging issues (old open issues)
        for _ in range(self.rng.randint(5, 12)):
            self._exception_events.append({
                "type": "unresolved_issue_aging",
                "campaign_id": "",
                "store_id": self.rng.choice(list(self._store_index.keys())),
                "sku": "",
                "allocation_id": "",
                "confirmation_id": "",
                "shipment_id": "",
                "severity": "info",
                "created_offset_days": -self.rng.randint(35, 60),
            })

        # Deduplicate events by type+store+sku+allocation to avoid excessive issues
        seen: set[str] = set()
        unique_events: list[dict] = []
        for evt in self._exception_events:
            key = f"{evt['type']}:{evt['store_id']}:{evt['sku']}:{evt['allocation_id']}"
            if key not in seen:
                seen.add(key)
                unique_events.append(evt)

        # Limit total issues to keep the table manageable
        if len(unique_events) > 120:
            unique_events = self.rng.sample(unique_events, 120)

        for evt in unique_events:
            seq += 1
            exception_id = f"EX-{seq:03d}"
            defaults = EXCEPTION_DEFAULTS[evt["type"]]
            severity = evt.get("severity", SEVERITY_BY_TYPE[evt["type"]])

            store = self._store_index.get(evt["store_id"], {})
            tz = store.get("timezone", "America/Chicago")
            tz_offset = REGION_OFFSETS.get(tz, "-05:00")

            campaign = None
            if evt["campaign_id"]:
                # Find campaign start date
                for tmpl in self._campaign_templates:
                    if tmpl["campaign_id"] == evt["campaign_id"]:
                        campaign = tmpl
                        break

            if campaign:
                base_date = campaign["start_date"]
            else:
                base_date = date(2026, 7, 15)

            created_dt = base_date + timedelta(days=evt.get("created_offset_days", 0))
            created_hour = self.rng.randint(7, 18)
            created_min = self.rng.choice([0, 15, 30, 45])
            created_date = f"{created_dt}T{created_hour:02d}:{created_min:02d}:00{tz_offset}"

            sla_hours = defaults["sla_hours"]
            due_dt = created_dt + timedelta(hours=sla_hours)
            due_date = f"{due_dt}T{created_hour:02d}:{created_min:02d}:00{tz_offset}"

            # Determine lifecycle status
            status_roll = self.rng.random()
            if status_roll < 0.25:
                exception_status = "resolved"
            elif status_roll < 0.35:
                exception_status = "closed"
            elif status_roll < 0.50:
                exception_status = "in_progress"
            elif status_roll < 0.60:
                exception_status = "open"
            elif status_roll < 0.70:
                exception_status = "raised"
            elif status_roll < 0.80:
                exception_status = "escalated"
            elif status_roll < 0.88:
                exception_status = "paused"
            else:
                exception_status = "waived"

            resolved_date = ""
            resolution_time_hours = ""
            resolution_type = ""
            resolution_text = ""
            waiver_reason = ""
            sla_pause_reason = ""
            sla_pause_started_at = ""
            sla_pause_max_hours = ""

            if exception_status in ("resolved", "closed"):
                resolve_days = self.rng.randint(1, max(1, sla_hours // 24))
                resolve_dt = created_dt + timedelta(days=resolve_days)
                resolve_hour = self.rng.randint(8, 18)
                resolve_min = self.rng.choice([0, 15, 30, 45])
                resolved_date = f"{resolve_dt}T{resolve_hour:02d}:{resolve_min:02d}:00{tz_offset}"
                total_hours = (resolve_dt - created_dt).total_seconds() / 3600 + (resolve_hour - created_hour)
                resolution_time_hours = round(max(0.5, total_hours), 1)
                resolution_type = self.rng.choice(RESOLUTION_TYPES)
                resolution_text = RESOLUTION_TEXTS[resolution_type]

            if exception_status == "waived":
                waiver_reason = self.rng.choice(WAIVER_REASONS)

            if exception_status == "paused":
                sla_pause_reason = self.rng.choice(PAUSE_REASONS)
                pause_start = created_dt + timedelta(hours=self.rng.randint(1, 12))
                pause_hour = self.rng.randint(8, 18)
                pause_min = self.rng.choice([0, 15, 30, 45])
                sla_pause_started_at = f"{pause_start}T{pause_hour:02d}:{pause_min:02d}:00{tz_offset}"
                sla_pause_max_hours = PAUSE_MAX_HOURS[sla_pause_reason]

            # Last update
            last_update_offset = self.rng.randint(0, 5)
            last_update_dt = created_dt + timedelta(days=last_update_offset)
            last_update_hour = self.rng.randint(8, 18)
            last_update_min = self.rng.choice([0, 15, 30, 45])
            last_update_at = f"{last_update_dt}T{last_update_hour:02d}:{last_update_min:02d}:00{tz_offset}"
            last_update_type = self.rng.choice(
                ["comment", "status_change", "pause", "resume", "reassign"]
            )

            # Root cause
            root_cause_cat = ""
            root_cause_sub = ""
            if exception_status in ("resolved", "closed", "in_progress"):
                root_cause_cat = self.rng.choice(ROOT_CAUSE_CATEGORIES)
                root_cause_sub = self.rng.choice(ROOT_CAUSE_SUBCATEGORIES[root_cause_cat])

            # Corrective action (for some issues)
            ca_id = ""
            ca_owner = ""
            ca_deadline = ""
            ca_status = ""
            if exception_status in ("in_progress", "escalated") and self.rng.random() < 0.5:
                ca_id = f"CA-{seq:03d}"
                ca_owner = self.rng.choice(RECEIVING_OWNERS)
                ca_deadline = (created_dt + timedelta(days=self.rng.randint(3, 14))).isoformat()
                ca_status = self.rng.choice(CORRECTIVE_ACTION_STATUSES)

            issue = {
                "exception_id": exception_id,
                "exception_type": evt["type"],
                "upstream_rule_code": defaults["rule_code"],
                "campaign_id": evt["campaign_id"] or "",
                "store_id": evt["store_id"],
                "sku": evt["sku"] or "",
                "allocation_id": evt["allocation_id"] or "",
                "confirmation_id": evt["confirmation_id"] or "",
                "severity": severity,
                "exception_status": exception_status,
                "exception_owner": defaults["owner"],
                "created_date": created_date,
                "due_date": due_date,
                "resolved_date": resolved_date,
                "resolution_time_hours": resolution_time_hours,
                "resolution_type": resolution_type,
                "resolution_text": resolution_text,
                "waiver_reason": waiver_reason,
                "root_cause_category": root_cause_cat,
                "root_cause_subcategory": root_cause_sub,
                "parent_id": "",
                "reopen_count": 0,
                "sla_pause_reason": sla_pause_reason,
                "sla_pause_started_at": sla_pause_started_at,
                "sla_pause_max_hours": sla_pause_max_hours,
                "last_update_at": last_update_at,
                "last_update_type": last_update_type,
                "corrective_action_id": ca_id,
                "corrective_action_owner": ca_owner,
                "corrective_action_deadline": ca_deadline,
                "corrective_action_status": ca_status,
            }
            issues.append(issue)

        # Add a few reopened issues (parent-child)
        if len(issues) >= 5:
            n_reopens = min(3, len(issues) // 10)
            for _ in range(n_reopens):
                parent = self.rng.choice(issues[:len(issues) // 2])
                parent["reopen_count"] = 1
                seq += 1
                child_id = f"EX-{seq:03d}"
                child = dict(parent)
                child["exception_id"] = child_id
                child["parent_id"] = parent["exception_id"]
                child["exception_status"] = "open"
                child["resolved_date"] = ""
                child["resolution_time_hours"] = ""
                child["resolution_type"] = ""
                child["resolution_text"] = ""
                child["waiver_reason"] = ""
                issues.append(child)

        return issues


# ---------------------------------------------------------------------------
# CSV writer
# ---------------------------------------------------------------------------

def _format_value(value) -> str:
    """Format a value for CSV output."""
    if value is None or value == "":
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        return str(value)
    return str(value)


def write_csv_tables(
    tables: dict[str, list[dict]], output_dir: str
) -> list[str]:
    """Write all tables as CSV files to ``output_dir``.

    Returns a list of written file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    written: list[str] = []

    for table_name in TABLE_NAMES:
        columns = TABLE_COLUMNS[table_name]
        records = tables.get(table_name, [])
        path = os.path.join(output_dir, f"{table_name}.csv")

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=columns, extrasaction="ignore"
            )
            writer.writeheader()
            for row in records:
                writer.writerow({col: _format_value(row.get(col, "")) for col in columns})

        written.append(path)

    return written


def generate_sample_data(
    seed: int = 42,
    output_dir: str = "data/sample",
    store_count: int = 100,
    region_count: int = 4,
    area_manager_count: int = 10,
    campaign_count: int = 3,
    write_csv: bool = True,
) -> dict[str, list[dict]]:
    """Generate sample data and optionally write CSVs.

    Parameters
    ----------
    seed : int
        Random seed for deterministic output.
    output_dir : str
        Directory to write CSV files (created if it does not exist).
    store_count : int
        Number of stores (clamped to 80-150).
    region_count : int
        Number of regions (clamped to 3-5).
    area_manager_count : int
        Number of area managers (clamped to 8-12).
    campaign_count : int
        Number of campaigns (clamped to 2-4).
    write_csv : bool
        Whether to write CSV files to ``output_dir``.

    Returns
    -------
    dict[str, list[dict]]
        Mapping of table name to list of record dicts.
    """
    gen = SampleDataGenerator(
        seed=seed,
        store_count=store_count,
        region_count=region_count,
        area_manager_count=area_manager_count,
        campaign_count=campaign_count,
    )
    tables = gen.generate()
    if write_csv:
        write_csv_tables(tables, output_dir)
    return tables


# ---------------------------------------------------------------------------
# Actions table generation (closed-loop module)
# ---------------------------------------------------------------------------

ACTION_TYPE_MAP: dict[str, str] = {
    "missing_confirmation": "phone_call",
    "late_confirmation": "phone_call",
    "quantity_mismatch": "dc_count_verification",
    "missing_photo_proof": "site_visit",
    "late_photo_proof": "site_visit",
    "stockout_risk": "sku_transfer",
    "overstock_risk": "sku_transfer",
    "low_sell_through": "sku_transfer",
    "unresolved_issue_sla_breach": "escalation",
}

# Mean time-to-action by severity (hours)
SEVERITY_ACTION_HOURS: dict[str, float] = {
    "critical": 4.0,
    "watch": 12.0,
    "info": 24.0,
}

# Known injected intervention effect: 75% resolve with action vs 30% baseline
# (set above 60% to compensate for noise: 8% failed, 5% assignment errors, null effects)
# Net observed effect after noise should be ~30pp
INTERVENTION_RESOLVE_RATE = 0.75
BASELINE_RESOLVE_RATE = 0.30


def generate_actions(exceptions: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Generate intervention actions for critical or breached exceptions.

    Injects a known effect: raw 75% resolve rate with intervention (net ~60%
    after noise) vs 30% baseline.
    Noise: 8% failed actions, 5% assignment errors, 5% reopen within 48h.

    Parameters
    ----------
    exceptions : pd.DataFrame
        The exceptions table (data/processed/exceptions.csv).
    seed : int
        Random seed for deterministic output.

    Returns
    -------
    pd.DataFrame
        Actions table with one row per intervention action.
    """
    import numpy as np

    rng = np.random.RandomState(seed)

    # Select exceptions eligible for action: critical severity or SLA breached
    mask = (exceptions["severity"] == "critical") | (exceptions["sla_status"] == "breached")
    eligible = exceptions[mask].copy()

    if eligible.empty:
        return pd.DataFrame(columns=[
            "action_id", "exception_id", "campaign_id", "store_id",
            "assigned_by", "assigned_to", "action_type", "action_timestamp",
            "action_status", "outcome", "time_to_action_hours", "notes",
        ])

    records: list[dict] = []
    for i, (_, row) in enumerate(eligible.iterrows()):
        action_id = f"ACT-{i + 1:04d}"
        exc_type = row["exception_type"]
        action_type = ACTION_TYPE_MAP.get(exc_type, "phone_call")
        assigned_to = row.get("area_manager", "Unassigned")
        campaign_id = row.get("campaign_id", "")
        store_id = row.get("store_id", "")
        exception_id = row.get("exception_id", "")

        # Time to action: log-normal, mean by severity
        severity = row.get("severity", "watch")
        mean_hours = SEVERITY_ACTION_HOURS.get(severity, 12.0)
        time_to_action = float(rng.lognormal(mean=np.log(mean_hours), sigma=0.5))

        # Timestamp: created_date + time_to_action
        created = str(row.get("created_date", "2026-06-25"))
        try:
            base_dt = datetime.fromisoformat(created)
            action_dt = base_dt + timedelta(hours=time_to_action)
            action_timestamp = action_dt.isoformat()
        except ValueError:
            action_timestamp = created

        # Determine outcome with known injected effect
        # 5% assignment error -> unresolved
        if rng.random() < 0.05:
            outcome = "unresolved"
            action_status = "completed"
            notes = f"Assignment error: action routed to wrong rep. {exc_type} remains open."
        # 8% failed action
        elif rng.random() < 0.08:
            outcome = "failed"
            action_status = "completed"
            notes = f"Action attempted but failed. {exc_type} not resolved by {action_type}."
        else:
            # Raw 75% resolve rate (INTERVENTION_RESOLVE_RATE), net ~60% after noise
            if rng.random() < INTERVENTION_RESOLVE_RATE:
                # 5% of resolved reopen within 48h
                if rng.random() < 0.05:
                    outcome = "reopened"
                    action_status = "completed"
                    notes = f"Initially resolved via {action_type}, but exception reopened within 48h."
                else:
                    outcome = "resolved"
                    action_status = "completed"
                    notes = f"{action_type.replace('_', ' ').title()} completed. {exc_type} resolved."
            else:
                outcome = "unresolved"
                action_status = "completed"
                notes = f"Action completed but {exc_type} remains unresolved."

        records.append({
            "action_id": action_id,
            "exception_id": exception_id,
            "campaign_id": campaign_id,
            "store_id": store_id,
            "assigned_by": "Ops Lead",
            "assigned_to": assigned_to,
            "action_type": action_type,
            "action_timestamp": action_timestamp,
            "action_status": action_status,
            "outcome": outcome,
            "time_to_action_hours": round(time_to_action, 1),
            "notes": notes,
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Intervention outcomes table generation (closed-loop module)
# ---------------------------------------------------------------------------

# Exception types where intervention genuinely doesn't work (null result)
NULL_EFFECT_TYPES = {"low_sell_through"}

# Daily revenue per store for impact calculation
DAILY_REVENUE_PER_STORE = 4200.0


def generate_intervention_outcomes(
    actions: pd.DataFrame,
    exceptions: pd.DataFrame,
    stores: pd.DataFrame,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate intervention outcomes with matched control stores.

    For each action, find a matched control exception from a store that
    received no intervention. Compare resolution rates to measure the
    intervention effect.

    Matching hierarchy:
    1. Exact: store_format + region + exception_type + priority +/- 50
    2. Relaxed: store_format + region + exception_type + priority +/- 100
    3. Minimal: store_format + exception_type (drop region/priority)
    4. No match: exclude from analysis (tracked)

    Noise injection:
    - 3-5% of exception types: null result (intervention doesn't work)
    - Control resolution: 30% baseline (no intervention effect)

    Parameters
    ----------
    actions : pd.DataFrame
        The actions table (data/sample/actions.csv).
    exceptions : pd.DataFrame
        The exceptions table (data/processed/exceptions.csv).
    stores : pd.DataFrame
        The stores table (data/sample/stores.csv).
    seed : int
        Random seed for deterministic output.

    Returns
    -------
    pd.DataFrame
        Intervention outcomes table with matched pairs.
    """
    import numpy as np

    rng = np.random.RandomState(seed)

    # Merge store info into exceptions for matching
    exc_with_store = exceptions.merge(
        stores[["store_id", "store_format", "region"]],
        on="store_id",
        how="left",
        suffixes=("", "_store"),
    )

    # Identify exceptions that received actions (intervention group)
    action_exc_ids = set(actions["exception_id"].unique())

    # Control pool: exceptions that did NOT receive any action
    control_pool = exc_with_store[~exc_with_store["exception_id"].isin(action_exc_ids)].copy()

    # Track used control exceptions to avoid reuse
    used_control_exc_ids: set[str] = set()

    records: list[dict] = []
    excluded = 0
    match_levels = {"exact": 0, "relaxed": 0, "minimal": 0}

    for i, (_, action) in enumerate(actions.iterrows()):
        action_id = action["action_id"]
        exc_id = action["exception_id"]
        store_id = action["store_id"]
        exc_type = action.get("action_type", "")

        # Get the original exception details
        orig_exc = exc_with_store[exc_with_store["exception_id"] == exc_id]
        if orig_exc.empty:
            excluded += 1
            continue

        orig = orig_exc.iloc[0]
        exc_type_real = orig["exception_type"]
        store_format = orig["store_format"]
        region = orig["region"]
        priority = orig["priority_score"]

        # Try matching hierarchy
        match_found = False
        control_row = None
        match_level = "none"

        for level, mask_fn in [
            ("exact", lambda df: (
                (df["store_format"] == store_format)
                & (df["region"] == region)
                & (df["exception_type"] == exc_type_real)
                & (df["priority_score"].between(priority - 50, priority + 50))
            )),
            ("relaxed", lambda df: (
                (df["store_format"] == store_format)
                & (df["region"] == region)
                & (df["exception_type"] == exc_type_real)
                & (df["priority_score"].between(priority - 100, priority + 100))
            )),
            ("minimal", lambda df: (
                (df["store_format"] == store_format)
                & (df["exception_type"] == exc_type_real)
            )),
        ]:
            available = control_pool[
                mask_fn(control_pool)
                & ~control_pool["exception_id"].isin(used_control_exc_ids)
            ]
            if not available.empty:
                # Pick the closest priority match
                available = available.copy()
                available["priority_diff"] = (available["priority_score"] - priority).abs()
                control_row = available.sort_values("priority_diff").iloc[0]
                used_control_exc_ids.add(control_row["exception_id"])
                match_found = True
                match_level = level
                match_levels[level] += 1
                break

        if not match_found:
            excluded += 1
            continue

        # Determine intervention outcome from the action
        action_outcome = action["outcome"]
        received_intervention = True

        # Resolved = action outcome was "resolved"
        resolved = action_outcome == "resolved"

        # Null effect: for certain exception types, intervention has reduced effectiveness
        # (~10% chance the intervention doesn't work for this type)
        if exc_type_real in NULL_EFFECT_TYPES and rng.random() < 0.10:
            resolved = False

        # Control resolution: 30% baseline (no intervention effect)
        control_resolved = bool(rng.random() < BASELINE_RESOLVE_RATE)

        # Days to resolution
        if resolved:
            days_to_resolution = int(max(1, rng.lognormal(mean=1.5, sigma=0.7)))
        else:
            days_to_resolution = 14  # default unresolved

        if control_resolved:
            control_days_to_resolution = int(max(1, rng.lognormal(mean=2.5, sigma=0.8)))
        else:
            control_days_to_resolution = 14

        # Revenue impact
        days_saved = max(0, control_days_to_resolution - days_to_resolution) if resolved else 0
        revenue_impact = DAILY_REVENUE_PER_STORE * days_saved
        counterfactual_loss = DAILY_REVENUE_PER_STORE * control_days_to_resolution

        records.append({
            "outcome_id": f"OUT-{i + 1:04d}",
            "exception_id": exc_id,
            "action_id": action_id,
            "store_id": store_id,
            "exception_type": exc_type_real,
            "received_intervention": received_intervention,
            "matched_control_store_id": control_row["store_id"],
            "matched_control_exception_id": control_row["exception_id"],
            "resolved": resolved,
            "control_resolved": control_resolved,
            "days_to_resolution": days_to_resolution,
            "control_days_to_resolution": control_days_to_resolution,
            "revenue_impact_usd": round(revenue_impact, 2),
            "counterfactual_revenue_loss_usd": round(counterfactual_loss, 2),
        })

    print(f"INTERVENTION_OUTCOMES generated={len(records)} excluded={excluded} "
          f"match_levels={match_levels}", flush=True)

    return pd.DataFrame(records)
