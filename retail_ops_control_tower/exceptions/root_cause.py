"""Root cause taxonomy (7 categories with sub-categories)."""

from __future__ import annotations

ROOT_CAUSE_TAXONOMY: dict[str, list[str]] = {
    "supplier": ["short_ship", "wrong_sku", "late_delivery", "quality_issue"],
    "dc": ["short_pick", "wrong_carton", "system_error", "delay"],
    "store": ["miscount", "unreported_damage", "training_gap", "space_constraint"],
    "system": ["integration_failure", "sync_delay", "rule_error", "data_quality"],
    "forecast": ["over_forecast", "under_forecast", "demand_shift"],
    "customer": ["order_change", "cancellation", "no_show", "complaint"],
    "logistics": ["carrier_delay", "route_failure", "capacity_constraint"],
}
