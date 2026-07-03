# Data Dictionary

> Scope: Define every column, type, example, and purpose for all 8 data tables in the Retail Operations Control Tower.
>
> Source documents:
> - `docs/research/retail-campaign-execution.md` (T01: 39 campaign tracker fields)
> - `docs/research/allocation-reconciliation.md` (T02: 45 allocation tracker fields)
> - `docs/research/exception-management.md` (T04: exception model, severity, SLA, action list)
> - `docs/research/synthesis.md` (project definition, 5 components)
> - `docs/prd.md` (table overview, validation rules, exception rules)
>
> This document defines the complete data model. Every column that appears in any table is listed here with its data type, an example value, and its purpose. Computed fields (derived at runtime by the reconciliation engine or exception management system) are marked as such.

## Conventions

- **Type** uses Python type annotations: `str`, `int`, `float`, `bool`, `date` (ISO 8601 YYYY-MM-DD), `datetime` (ISO 8601 with timezone), `list[str]`, `enum`.
- **Example** shows a representative value from the Summer Peach LTO 2026 demo scenario.
- **Purpose** explains what the column means and how it is used.
- **Source** cites the research field number (T01 #N or T02 #N) or marks the field as computed.
- **Nullable** indicates whether the field can be null (None).
- Fields marked **(computed)** are not stored in the simulation output; they are derived at runtime by the reconciliation engine or dashboard.

---

## Table 1: stores

Store master data. One row per store. Static for the duration of a simulation run.

| # | Column | Type | Example | Nullable | Purpose | Source |
|---|--------|------|---------|----------|---------|--------|
| 1 | store_id | str | "S-001" | No | Unique store identifier | T01 #9 |
| 2 | store_name | str | "Central Plaza Cafe" | No | Human-readable store name | T01 #10 |
| 3 | region | str | "Central" | No | Geographic region (North, South, East, West, Central) | T01 #11 |
| 4 | store_format | enum | "flagship" | No | Store type: flagship, standard, kiosk, drive-thru | T01 #12 |
| 5 | area_manager | str | "Sarah Chen" | No | Area manager responsible for this store | T01 #13 (repurposed) |
| 6 | field_rep | str | "James Okoro" | Yes | Field rep assigned to this store | T01 #13 |
| 7 | selling_area_sqft | int | 1200 | No | Selling area in square feet (for sales-per-sqft) | T02 (sales per sqft) |
| 8 | city | str | "Springfield" | No | City name (fictional) | T01 #11 (extended) |
| 9 | state | str | "IL" | No | State abbreviation (fictional) | T01 #11 (extended) |
| 10 | open_date | date | "2020-03-15" | No | Store opening date | Extended |
| 11 | is_active | bool | True | No | Whether the store is currently operating | Extended |
| 12 | timezone | str | "America/Chicago" | No | Store timezone for visit/sales timestamps | Extended |

---

## Table 2: campaigns

Campaign master data. One row per campaign. Defines the campaign window, type, and scope.

| # | Column | Type | Example | Nullable | Purpose | Source |
|---|--------|------|---------|----------|---------|--------|
| 1 | campaign_id | str | "C-2026-PEACH" | No | Unique campaign identifier | T01 #1 |
| 2 | campaign_name | str | "Summer Peach LTO 2026" | No | Human-readable campaign name | T01 #2 |
| 3 | campaign_type | enum | "seasonal_lto" | No | Category: seasonal_lto, product_launch, promotional_pricing, brand_activation | T01 #3 |
| 4 | campaign_start_date | date | "2026-07-01" | No | Planned launch date | T01 #4 |
| 5 | campaign_end_date | date | "2026-07-28" | No | Planned end date | T01 #5 |
| 6 | campaign_status | enum | "active" | No | Status: draft, active, paused, completed, cancelled | T01 #6 |
| 7 | hq_owner | str | "Maria Rodriguez" | No | HQ stakeholder responsible for the campaign | T01 #7 |
| 8 | target_store_count | int | 40 | No | Number of stores in scope | T01 #8 |
| 9 | sku_list | list[str] | ["PEACH-001", "PEACH-002", ...] | No | List of campaign SKU IDs | Extended |
| 10 | hero_sku | str | "PEACH-001" | No | The hero SKU for this campaign (drives business_impact scoring) | Extended |
| 11 | launch_window_days | int | 7 | No | Number of days after start_date considered "launch window" for activation scoring | T04 campaign_urgency |
| 12 | supplier_lead_time_weeks | int | 2 | No | Supplier lead time for replenishment (weeks). Drives stockout/overstock thresholds. | T02 EX-10 |
| 13 | period_sell_through_target | float | 0.70 | No | Target sell-through rate for the campaign period | T02 EX-13 |
| 14 | full_price_target | float | 0.80 | No | Target full-price sell-through rate | T02 EX-15 |
| 15 | posm_list | list[str] | ["poster-A1", "standee-floor", "tent-card", "menu-board-peach"] | No | POSM materials assigned to this campaign | T01 #14 |

---

## Table 3: allocation_plan

Per-store, per-SKU planned allocation line items. One row per store-SKU combination per campaign.

| # | Column | Type | Example | Nullable | Purpose | Source |
|---|--------|------|---------|----------|---------|--------|
| 1 | allocation_id | str | "A-001-S-001-PEACH-001" | No | Unique allocation plan line identifier | T02 #1 |
| 2 | campaign_id | str | "C-2026-PEACH" | No | Link to campaign | T02 #2 |
| 3 | sku | str | "PEACH-001" | No | Stock-keeping unit | T02 #3 |
| 4 | store_id | str | "S-001" | No | Destination store | T02 #4 |
| 5 | planned_quantity | int | 200 | No | Units planned for this store/SKU | T02 #5 |
| 6 | planned_receipt_date | date | "2026-06-28" | No | Date units are expected to be received at the store | T02 #6 |
| 7 | allocation_phase | enum | "initial" | No | Phase: initial, replenishment, chase, transfer | T02 #7 |
| 8 | allocation_method | enum | "fair_share" | No | Method: fair_share, door_index, size_curve, manual_override | T02 #8 |
| 9 | holdback_pct | float | 0.10 | No | Percentage of original buy retained at DC for reallocation | T02 #9 |
| 10 | planner_owner | str | "David Park" | No | HQ planner responsible for this allocation | T02 #10 |
| 11 | planned_to_shipped_variance | int | -10 | Yes | (computed) shipped_quantity - planned_quantity. Negative = shortfall. | T02 #31 (computed) |
| 12 | shipped_to_plan_fill_rate | float | 0.95 | Yes | (computed) shipped_quantity / planned_quantity | T02 formula (computed) |
| 13 | allocation_accuracy | float | 0.94 | Yes | (computed) 1 - abs(planned - received) / planned | T02 formula (computed) |

---

## Table 4: dispatch

Shipment records. One row per allocation line (shipment). Records what left the DC.

| # | Column | Type | Example | Nullable | Purpose | Source |
|---|--------|------|---------|----------|---------|--------|
| 1 | shipment_id | str | "SH-001-S-001-PEACH-001" | No | Unique shipment identifier | T02 #11 |
| 2 | allocation_id | str | "A-001-S-001-PEACH-001" | No | Link to allocation plan line | T02 #1 (link) |
| 3 | campaign_id | str | "C-2026-PEACH" | No | Link to campaign | T02 #2 (link) |
| 4 | sku | str | "PEACH-001" | No | SKU being shipped | T02 #3 (link) |
| 5 | store_id | str | "S-001" | No | Destination store | T02 #4 (link) |
| 6 | shipped_quantity | int | 190 | No | Units actually shipped from DC | T02 #12 |
| 7 | shipped_date | date | "2026-06-26" | No | Date the shipment left the DC | T02 #13 |
| 8 | expected_arrival_date | date | "2026-06-28" | No | Date the shipment is expected at the store | T02 #14 |
| 9 | carton_count | int | 8 | No | Number of cartons in the shipment | T02 #15 |
| 10 | dc_id | str | "DC-01" | No | Distribution center that shipped | Extended |
| 11 | carrier | str | "FastFreight Co" | No | Carrier name (fictional) | Extended |
| 12 | shipped_to_received_variance | int | -2 | Yes | (computed) received_quantity - shipped_quantity. Negative = loss in transit. | T02 #32 (computed) |
| 13 | receiving_accuracy | float | 0.9895 | Yes | (computed) 1 - abs(shipped - received) / shipped | T02 formula (computed) |
| 14 | on_time_receipt_rate | bool | True | Yes | (computed) received_date <= planned_receipt_date | T02 formula (computed) |

---

## Table 5: store_confirmations

Store receiving and visit records. One row per allocation line (receipt) linked to a visit. Records what the store received and the visit/audit outcome.

| # | Column | Type | Example | Nullable | Purpose | Source |
|---|--------|------|---------|----------|---------|--------|
| 1 | confirmation_id | str | "CONF-001-S-001-PEACH-001" | No | Unique confirmation/receipt identifier | Extended |
| 2 | allocation_id | str | "A-001-S-001-PEACH-001" | No | Link to allocation plan line | T02 #1 (link) |
| 3 | shipment_id | str | "SH-001-S-001-PEACH-001" | No | Link to shipment | T02 #11 (link) |
| 4 | campaign_id | str | "C-2026-PEACH" | No | Link to campaign | T02 #2 (link) |
| 5 | store_id | str | "S-001" | No | Store that received | T02 #4 (link) |
| 6 | sku | str | "PEACH-001" | No | SKU received | T02 #3 (link) |
| 7 | received_quantity | int | 188 | No | Units counted at store receiving | T02 #16 |
| 8 | received_date | date | "2026-06-28" | No | Date the store posted the receipt | T02 #17 |
| 9 | receipt_status | enum | "accepted" | No | Status: accepted, partial, rejected, pending | T02 #18 |
| 10 | receiving_exception_type | enum | "shortage" | Yes | Type: overage, shortage, damage, substitution, refused, none | T02 #19 |
| 11 | receiving_owner | str | "Lisa Wong" | No | Store manager or receiver who posted the receipt | T02 #20 |
| 12 | visit_id | str | "V-001-S-001" | No | Unique visit identifier | T01 #15 |
| 13 | visit_date | date | "2026-07-01" | No | Date of field visit | T01 #16 |
| 14 | visit_timestamp | datetime | "2026-07-01T09:15:00-05:00" | No | Precise check-in/check-out time | T01 #17 |
| 15 | visit_status | enum | "completed" | No | Status: planned, in_progress, completed, missed, bypassed | T01 #18 |
| 16 | gps_coordinates | str | "39.7817,-89.6444" | Yes | Latitude/longitude at capture time | T01 #19 |
| 17 | checklist_completion_pct | float | 0.95 | Yes | Percentage of checklist items completed | T01 #20 |
| 18 | planogram_compliance | bool | True | Yes | Does shelf match planogram | T01 #21 |
| 19 | pricing_accuracy | bool | True | Yes | Are price tags correct for the promotion | T01 #22 |
| 20 | on_shelf_availability_pct | float | 0.95 | Yes | Percentage of campaign SKUs present on shelf | T01 #23 |
| 21 | training_completion_flag | bool | True | Yes | Whether store staff completed pre-launch training | T01 #24 |
| 22 | audit_level | enum | "L2" | Yes | Audit level: L1, L2, L3 | T01 #27 |
| 23 | audit_status | enum | "approved" | Yes | Status: pending, approved, rejected | T01 #28 |
| 24 | compliance_score | float | 88.5 | Yes | Numeric score (0-100) assigned during audit | T01 #29 |
| 25 | audit_comments | str | "POSM well placed, minor shelf gap" | Yes | Reviewer remarks and rejection reasons | T01 #30 |
| 26 | exception_flag | bool | True | Yes | Whether an exception was logged for this visit | T01 #31 |
| 27 | non_completion_reason | str | "" | Yes | Reason if task was not completed | T01 #32 |
| 28 | campaign_store_status | enum | "completed" | Yes | Campaign setup status for this store: not_started, in_progress, completed | T04 exception type 4 |
| 29 | confirmation_timestamp | datetime | "2026-07-01T10:30:00-05:00" | Yes | When the confirmation was posted in the system. Used for "missing confirmation" exception (V-04). | T04 exception type 1 |

---

## Table 6: photo_proofs

Photo proof metadata records. One row per photo submitted. No actual images are stored.

| # | Column | Type | Example | Nullable | Purpose | Source |
|---|--------|------|---------|----------|---------|--------|
| 1 | photo_id | str | "PH-001-V-001-S-001" | No | Unique photo proof identifier | Extended |
| 2 | confirmation_id | str | "CONF-001-S-001-PEACH-001" | No | Link to store confirmation/visit | T01 #15 (link) |
| 3 | visit_id | str | "V-001-S-001" | No | Link to visit | T01 #15 (link) |
| 4 | store_id | str | "S-001" | No | Store where photo was taken | T01 #9 (link) |
| 5 | campaign_id | str | "C-2026-PEACH" | No | Link to campaign | T01 #1 (link) |
| 6 | photo_proof_url | str | "photos/PH-001-V-001-S-001.jpg" | Yes | URL or path to photo (synthetic path, no real image) | T01 #25 |
| 7 | photo_timestamp | datetime | "2026-07-01T09:22:00-05:00" | Yes | Server-validated capture time | T01 #26 |
| 8 | photo_gps_coordinates | str | "39.7817,-89.6444" | Yes | GPS coordinates at capture time | T01 #19 (photo-specific) |
| 9 | photo_user_id | str | "REP-005" | Yes | User ID of the person who took the photo | T01 #13 (photo-specific) |
| 10 | photo_device_id | str | "TAB-005" | Yes | Device ID used to capture | Extended |
| 11 | photo_type | enum | "posm_deployment" | No | Type: posm_deployment, shelf_display, planogram, pricing, store_front | Extended |
| 12 | photo_validation_status | enum | "passed" | No | Validation status: passed, failed, missing | T04 exception type 3 |
| 13 | photo_validation_reason | str | "" | Yes | Reason if validation failed (no GPS, no timestamp, out of geofence) | Extended |

---

## Table 7: sales_daily

Daily sales and on-hand records. One row per store-SKU per day. Tracks sell-through, on-hand, and risk flags.

| # | Column | Type | Example | Nullable | Purpose | Source |
|---|--------|------|---------|----------|---------|--------|
| 1 | sales_id | str | "SALE-2026-07-01-S-001-PEACH-001" | No | Unique daily sales record identifier | Extended |
| 2 | campaign_id | str | "C-2026-PEACH" | No | Link to campaign | T02 #2 (link) |
| 3 | store_id | str | "S-001" | No | Store | T02 #4 (link) |
| 4 | sku | str | "PEACH-001" | No | SKU | T02 #3 (link) |
| 5 | sales_date | date | "2026-07-01" | No | The date of this sales record | T02 #30 (period) |
| 6 | day_of_campaign | int | 1 | No | Day number within the campaign (1 = launch day) | Extended |
| 7 | units_sold | int | 12 | No | Units sold in the reporting period (day) | T02 #21 |
| 8 | units_sold_full_price | int | 10 | No | Units sold before any markdown | T02 #22 |
| 9 | units_sold_markdown | int | 2 | No | Units sold on markdown or promotion | T02 #23 |
| 10 | on_hand_quantity | int | 176 | No | Units on hand at the store at period close | T02 #24 |
| 11 | on_order_quantity | int | 0 | Yes | Units on order with the supplier, expected before next replenishment | T02 #25 |
| 12 | in_transit_quantity | int | 0 | Yes | Units shipped but not yet received | T02 #26 |
| 13 | transfer_in_quantity | int | 0 | Yes | Units received from another store | T02 #27 |
| 14 | transfer_out_quantity | int | 0 | Yes | Units sent to another store | T02 #28 |
| 15 | shrink_quantity | int | 0 | Yes | Units lost to theft, damage, or administrative error | T02 #29 |
| 16 | period_close_date | date | "2026-07-01" | No | Date the period (day) ended | T02 #30 |
| 17 | received_to_sold_pct | float | 0.064 | Yes | (computed) units_sold / received_quantity (daily sell-through) | T02 #33 (computed) |
| 18 | cumulative_sell_through_pct | float | 0.064 | Yes | (computed) cumulative units_sold / received_quantity up to this date | T02 formula (computed) |
| 19 | weeks_of_cover | float | 14.7 | Yes | (computed) on_hand_quantity / average_weekly_units_sold | T02 #34 (computed) |
| 20 | stockout_risk_flag | bool | False | Yes | (computed) WOC < supplier_lead_time_weeks | T02 #35 (computed) |
| 21 | overstock_risk_flag | bool | False | Yes | (computed) WOC > 2 x lead_time OR WOC > remaining_selling_window_weeks | T02 #36 (computed) |
| 22 | markdown_intensity | float | 0.167 | Yes | (computed) units_sold_markdown / units_sold | T02 formula (computed) |
| 23 | full_price_sell_through | float | 0.053 | Yes | (computed) units_sold_full_price / received_quantity | T02 formula (computed) |
| 24 | door_index | float | 1.15 | Yes | (computed) store_sales / average_store_sales | T02 formula (computed) |
| 25 | stock_to_sales_ratio | float | 14.7 | Yes | (computed) on_hand_quantity / units_sold_this_period | T02 formula (computed) |

---

## Table 8: issues

Exception and corrective action records. One row per exception. Tracks the full exception lifecycle from raise to close.

| # | Column | Type | Example | Nullable | Purpose | Source |
|---|--------|------|---------|----------|---------|--------|
| 1 | exception_id | str | "EX-001" | No | Unique exception identifier | T02 #37 |
| 2 | exception_type | enum | "stockout_risk" | No | One of 8 taxonomy types: missing_confirmation, quantity_mismatch, missing_photo_proof, late_setup, stockout_risk, overstock_risk, low_sell_through, unresolved_issue_aging | T04 taxonomy |
| 3 | upstream_rule_code | str | "EX-10" | Yes | The specific rule from T02 that triggered this exception (EX-01 to EX-24) | T02 rules |
| 4 | campaign_id | str | "C-2026-PEACH" | Yes | Link to campaign (null if not campaign-related) | T02 #2 (link) |
| 5 | store_id | str | "S-001" | No | Store where the exception occurred | T02 #4 (link) |
| 6 | sku | str | "PEACH-001" | Yes | SKU involved (null if not SKU-specific) | T02 #3 (link) |
| 7 | allocation_id | str | "A-001-S-001-PEACH-001" | Yes | Link to allocation plan line (null if not allocation-related) | T02 #1 (link) |
| 8 | confirmation_id | str | "CONF-001-S-001-PEACH-001" | Yes | Link to store confirmation (null if not visit-related) | Extended (link) |
| 9 | severity | enum | "critical" | No | Severity tier: critical, watch, info | T02 #39, T04 |
| 10 | exception_status | enum | "open" | No | Lifecycle status: raised, open, in_progress, resolved, closed, paused, escalated, waived | T02 #40, T04 state machine |
| 11 | exception_owner | str | "David Park" | No | Person or role assigned to resolve | T02 #41 |
| 12 | created_date | datetime | "2026-07-01T08:00:00-05:00" | No | When the exception was raised | T04 (raise time) |
| 13 | due_date | datetime | "2026-07-02T08:00:00-05:00" | No | Resolution deadline (created_date + SLA window) | T02 #42 (computed) |
| 14 | resolved_date | datetime | None | Yes | When the exception was resolved (null if not resolved) | Extended |
| 15 | resolution_time_hours | float | None | Yes | Hours from raised to resolved. Null if not resolved. | T01 #37, T02 #43 |
| 16 | resolution_type | enum | None | Yes | How resolved: reposted, corrected, system_fix, write_off, good_will, no_action_required | T04 close-out |
| 17 | resolution_text | str | None | Yes | Resolution description (min 20 chars when resolved) | T04 close-out |
| 18 | waiver_reason | str | None | Yes | Reason recorded if exception is waived (min 30 chars) | T02 #44 |
| 19 | root_cause_category | enum | None | Yes | Root cause: supplier, dc, store, system, forecast, customer, logistics | T02 #45, T04 taxonomy |
| 20 | root_cause_subcategory | str | None | Yes | Sub-category within root cause (e.g., "short_pick") | T04 root cause |
| 21 | parent_id | str | None | Yes | Parent exception ID (set for reopens, links to original) | T04 reopen rules |
| 22 | reopen_count | int | 0 | No | Number of times this exception has been reopened | T04 reopen rules |
| 23 | priority_score | int | 400 | Yes | (computed) severity_weight x 100 + age_pressure + business_impact + campaign_urgency | T04 formula (computed) |
| 24 | age_in_days | float | 1.0 | Yes | (computed) days from created_date to aging_date | T04 (computed) |
| 25 | aging_bucket | int | 0 | Yes | (computed) 0=0-5d, 1=6-15d, 2=16-30d, 3=30+d | T04 (computed) |
| 26 | sla_status | enum | "approaching" | Yes | (computed) within, approaching, breached, paused | T04 (computed) |
| 27 | sla_window_label | str | "24 hours" | Yes | (computed) Human-readable SLA window from severity | T04 (computed) |
| 28 | sla_paused | bool | False | Yes | (computed) Whether SLA clock is currently paused | T04 (computed) |
| 29 | sla_pause_reason | str | None | Yes | Reason for SLA pause (vendor, store, system, transit) | T04 pause rules |
| 30 | sla_pause_started_at | datetime | None | Yes | When the SLA clock was paused | T04 pause rules |
| 31 | sla_pause_max_hours | int | None | Yes | Max pause duration in hours before auto-resume | T04 pause rules |
| 32 | business_impact | int | 30 | Yes | (computed) Impact score: 30 (hero/flagship), 15 (standard), 5 (low-velocity) | T04 formula (computed) |
| 33 | campaign_urgency | int | 20 | Yes | (computed) Urgency: 20 (launch window), 10 (active), 0 (no campaign) | T04 formula (computed) |
| 34 | age_pressure | float | 50.0 | Yes | (computed) (days_open / SLA_window_days) x 50, capped at 50 | T04 formula (computed) |
| 35 | last_update_at | datetime | "2026-07-01T14:00:00-05:00" | No | Date and type of last update | T04 action list field 15 |
| 36 | last_update_type | str | "comment" | Yes | Type of last update: comment, status_change, pause, resume, reassign | T04 action list field 15 |
| 37 | expected_action | str | "Place emergency replenishment order OR initiate inter-store transfer." | Yes | (computed) Codified next action from action playbook | T04 action playbook (computed) |
| 38 | corrective_action_id | str | None | Yes | ID for corrective action task (if one was created) | T01 #33 |
| 39 | corrective_action_owner | str | None | Yes | Person assigned to fix the issue | T01 #34 |
| 40 | corrective_action_deadline | date | None | Yes | Resolution due date for corrective action | T01 #35 |
| 41 | corrective_action_status | enum | None | Yes | Status: open, in_progress, resolved | T01 #36 |
| 42 | region_coverage_pct | float | None | Yes | (computed) Percentage of planned stores visited in region | T01 #38 (computed) |
| 43 | campaign_compliance_pct | float | None | Yes | (computed) Percentage of stores passing audit for this campaign | T01 #39 (computed) |

---

## Computed fields summary

The following fields are not stored in the simulation output JSON. They are derived at runtime by the reconciliation engine, exception management system, or dashboard:

**allocation_plan:** planned_to_shipped_variance (#11), shipped_to_plan_fill_rate (#12), allocation_accuracy (#13)

**dispatch:** shipped_to_received_variance (#12), receiving_accuracy (#13), on_time_receipt_rate (#14)

**sales_daily:** received_to_sold_pct (#17), cumulative_sell_through_pct (#18), weeks_of_cover (#19), stockout_risk_flag (#20), overstock_risk_flag (#21), markdown_intensity (#22), full_price_sell_through (#23), door_index (#24), stock_to_sales_ratio (#25)

**issues:** priority_score (#23), age_in_days (#24), aging_bucket (#25), sla_status (#26), sla_window_label (#27), sla_paused (#28), business_impact (#32), campaign_urgency (#33), age_pressure (#34), expected_action (#37), region_coverage_pct (#42), campaign_compliance_pct (#43)

---

## Field count reconciliation

| Table | Total fields | Stored | Computed |
|-------|-------------|--------|----------|
| stores | 12 | 12 | 0 |
| campaigns | 15 | 15 | 0 |
| allocation_plan | 13 | 10 | 3 |
| dispatch | 14 | 11 | 3 |
| store_confirmations | 29 | 29 | 0 |
| photo_proofs | 13 | 13 | 0 |
| sales_daily | 25 | 16 | 9 |
| issues | 43 | 31 | 12 |
| **Total** | **164** | **137** | **27** |

### Tracker field reconciliation

- T01 defines 39 campaign tracker fields. All 39 are represented: stores (5: fields 9-13), campaigns (9: fields 1-8, 14/posm_list), store_confirmations (16: fields 15-24, 27-32), photo_proofs (2: fields 25-26), issues (5: fields 33-37), computed rollups (2: region_coverage_pct, campaign_compliance_pct). No fields dropped.
- T02 defines 45 allocation tracker fields. All 45 are represented: allocation_plan (11: 10 stored + 1 computed), dispatch (6: 5 stored + 1 computed), store_confirmations (5: fields 16-20), sales_daily (14: 10 stored + 4 computed), issues (9: fields 37-45). No fields dropped.
- T04 exception model fields (exception_id, type, severity, status, owner, created_date, resolved_date, parent_id, root_cause_tag, resolution_type, priority_score, age, sla_status, aging_bucket) are all represented in the issues table.

---

## Data generation parameters (demo scenario)

| Parameter | Value | Source |
|-----------|-------|--------|
| Store count | 40 | synthesis.md |
| Region count | 5 (North, South, East, West, Central) | synthesis.md |
| Campaign count | 1 active (Summer Peach LTO 2026) | synthesis.md |
| SKU count | 12 | synthesis.md |
| Field rep count | 8 (each covers 5 stores) | synthesis.md |
| Campaign duration | 28 days (4 weeks) | synthesis.md |
| Planned quantity (hero SKU) | 200 units per store | synthesis.md |
| Supplier lead time | 2 weeks | synthesis.md |
| Random seed | 42 (deterministic) | test strategy |
| Expected allocation_plan rows | 480 (40 stores x 12 SKUs) | computed |
| Expected dispatch rows | 480 | computed |
| Expected store_confirmations rows | 480 | computed |
| Expected photo_proofs rows | ~400 (some stores miss photos) | synthesis.md |
| Expected sales_daily rows | ~13,440 (40 x 12 x 28) | computed |
| Expected issues rows | 50-100 | synthesis.md demo |
