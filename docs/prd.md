# Product Requirements Document: Retail Operations Control Tower

> Scope: Define the product requirements, user personas, data model overview, validation rules, exception rules, KPI definitions, dashboard pages, report sections, and test strategy for the Retail Operations Control Tower portfolio project.
>
> Source documents:
> - `docs/research/synthesis.md` (project definition, 5 components, demo story)
> - `docs/scope-guard.md` (in-scope and non-goals)
> - `docs/research/retail-campaign-execution.md` (T01: campaign workflow, 39 tracker fields, 17 failure modes)
> - `docs/research/allocation-reconciliation.md` (T02: allocation lifecycle, 45 tracker fields, 24 exception rules, 16 formulas)
> - `docs/research/ops-kpi-scorecard.md` (T03: 6 dashboard sections, 18 candidate KPIs, 10 MVP KPIs)
> - `docs/research/exception-management.md` (T04: 8-category taxonomy, severity scoring, SLA aging, action list, state machine)
>
> Companion documents:
> - `docs/data-dictionary.md` (every column, type, example, purpose for all 8 data tables)
> - `docs/implementation-plan.md` (module-to-file-path mapping, implementation phases, scripts)

## 1. Product overview

### Problem

Multi-store retail chains run seasonal limited-time-offer (LTO) campaigns that require coordinated execution across HQ planning, distribution centers, field reps, and store staff. The operational reality is that execution gaps are the default, not the exception. The specific failure modes this product addresses (synthesized from T01 and T02 research):

1. Late campaign activation: promotions activate days late in a significant percentage of outlets because there is no task assignment, verification, or escalation when a store has not executed.
2. Quantity mismatches: planned vs. shipped vs. received vs. sold quantities diverge at every handoff, and nobody reconciles them until the campaign window has closed.
3. Pencil-whipping: store teams check off tasks that were never done because checklists have no proof layer (no timestamp, no photo, no way to verify remotely).
4. Stockout and overstock risk: weeks-of-cover is not evaluated against supplier lead time, so stockouts happen mid-campaign and overstock lands at clearance.
5. No prioritized action queue: exceptions exist but are not ranked by urgency, impact, or campaign window, so the ops team does not know what to fix first.

### Product

The Retail Operations Control Tower is a Python-based dashboard application that simulates a multi-store coffee chain running a seasonal LTO campaign. It tracks the campaign from HQ planning through store execution, allocation reconciliation, and exception management. The dashboard surfaces operational gaps and generates a priority-ranked daily action list so the ops team knows what to fix first.

All data is synthetic. No real company data, internal knowledge, or real-world retail operations experience is claimed.

### Goals

| # | Goal | Success measure |
|---|------|-----------------|
| 1 | Simulate a complete campaign lifecycle | 40 stores, 1 campaign, 12 SKUs, 4-week window generated end-to-end with no manual data entry |
| 2 | Reconcile the 4-quantity lifecycle | All 16 formulas compute for every store-SKU combination; variances flagged against 24 exception rules |
| 3 | Surface exceptions with priority scores | Every exception has a priority score (1-200), an owner, an SLA deadline, and a codified next action |
| 4 | Render a 6-section dashboard | All 6 sections render with the 10 MVP KPIs and threshold color-coding |
| 5 | Generate a daily action list | Top 20 exceptions ranked by priority score, with all 18 action-list fields per row |
| 6 | Run the demo story end-to-end | Summer Peach LTO 2026 scenario runs from Day 1 launch through Day 14 action list without errors |

### Non-goals (out of scope for MVP)

Per `docs/scope-guard.md`, the following are explicitly out of scope:

- No real Tomoro scraping, real company data, or real personal/business data.
- No deep learning forecasting. Rule-based logic and deterministic formulas only.
- No ERP clone (no order management, warehouse management, financial accounting, HR, or procurement systems).
- No authentication or user management. Single-user application.
- No cloud deployment unless trivial. Runs locally.
- No real photos or image processing. Photo proof records contain metadata only.
- No real-time streaming. Data is generated in batches.
- No mobile app. Web application or notebook.
- No third-party API integrations.
- No publishing to GitHub. T21 is a separate approval gate.

Deferred to v2 (documented but not built in MVP):

1. WSSI view (Weekly Sales, Stock and Intake) - T02.
2. Transfer and markdown engine - T02. State machine supports recording but no optimization engine.
3. Performance KPIs (sales vs. target, conversion, ATV) - T03. Requires POS data source beyond MVP.
4. Sub-component compliance tiles (planogram, POSM, pricing as separate tiles) - T03. Rolled into Network Compliance composite for MVP.
5. Per-role action list filtering (7 roles) - T04. MVP shows the operator view only.

## 2. User personas

The control tower serves three primary personas. Each persona has a distinct operational question they need answered. The MVP renders the control-tower operator view (all personas see the same data); role-based filtering is a v2 UI feature.

### Persona 1: HQ Ops Analyst

- **Role:** Headquarters operations analyst responsible for network-wide campaign execution monitoring.
- **Operational question:** "Is the campaign executing on plan across the network, and where are the biggest gaps?"
- **Primary dashboard sections:** Executive KPI tiles (Section 1), Campaign performance view (Section 4), Exception backlog view (Section 5).
- **Daily workflow:** Opens the dashboard at the start of the day, scans the executive tiles for red/amber indicators, drills into the exception backlog to see what aged overnight, reviews the campaign performance view for coverage and compliance trends.
- **Decision authority:** Can reassign exceptions, request corrective actions, escalate to area managers. Cannot approve waivers (requires Operations Lead).
- **MVP scope:** Full dashboard access. The daily action list is this persona's primary work queue.

### Persona 2: Area Manager

- **Role:** Regional/area manager responsible for a cluster of stores within a geographic region.
- **Operational question:** "Which stores in my region need attention today, and what is the oldest open issue?"
- **Primary dashboard sections:** Area Manager breakdowns (Section 2), Store status table (Section 3), Exception backlog view (Section 5).
- **Daily workflow:** Opens the area manager breakdown for their region, sorts by worst composite health score, drills into the store status table to see which stores are red, checks the exception backlog filtered to their region.
- **Decision authority:** Can assign corrective actions to store PICs, resolve exceptions, request resource allocation. Cannot waive exceptions (requires Operations Lead).
- **MVP scope:** Views filtered to their region. The store status table is this persona's primary view.

### Persona 3: Store PIC (Person-in-Charge)

- **Role:** Store person-in-charge responsible for in-store campaign execution, receiving, and proof submission.
- **Operational question:** "What do I need to do in my store today to keep the campaign on track?"
- **Primary dashboard sections:** Store status table (Section 3, filtered to their store), Exception backlog view (Section 5, filtered to their store).
- **Daily workflow:** Opens the store status view for their store, checks open exceptions and corrective actions assigned to them, completes setup tasks, submits photo proofs, posts receiving confirmations.
- **Decision authority:** Can mark exceptions in_progress, submit photo proofs, post receiving confirmations, resolve exceptions assigned to them. Cannot reassign or escalate.
- **MVP scope:** Views filtered to their store. The action list filtered to their store is this persona's primary work queue.

## 3. Data tables overview

The data model has 8 tables. Every column, type, example, and purpose is defined in `docs/data-dictionary.md`. This section provides the table-level overview and relationships.

| # | Table | Purpose | Source research | Approximate row count (demo) |
|---|-------|---------|-----------------|------------------------------|
| 1 | stores | Store master: one row per store with region, format, and attributes | T01 fields 9-12 | 40 |
| 2 | campaigns | Campaign master: one row per campaign with dates, status, and scope | T01 fields 1-8 | 2-3 |
| 3 | allocation_plan | Per-store, per-SKU planned allocation line items | T02 fields 1-10 | 480 (40 stores x 12 SKUs) |
| 4 | dispatch | Shipment records: one row per shipment with shipped quantities and dates | T02 fields 11-15 | 480 |
| 5 | store_confirmations | Store receiving and visit records: receipt quantities, visit status, audit results | T01 fields 15-24, T02 fields 16-20 | 480 |
| 6 | photo_proofs | Photo proof metadata records: GPS, timestamp, user ID, validation status | T01 fields 25-26 | 400 |
| 7 | sales_daily | Daily sales and on-hand records: units sold, on-hand, risk flags | T02 fields 21-30 | 13,440 (40 x 12 x 28 days) |
| 8 | issues | Exception and corrective action records: type, severity, status, priority, SLA | T01 fields 31-39, T02 fields 31-45, T04 exception model | 50-100 |

### Entity relationships

```
stores (1) ----< (M) allocation_plan
stores (1) ----< (M) store_confirmations
stores (1) ----< (M) photo_proofs
stores (1) ----< (M) sales_daily
stores (1) ----< (M) issues

campaigns (1) ----< (M) allocation_plan
campaigns (1) ----< (M) store_confirmations
campaigns (1) ----< (M) issues

allocation_plan (1) ----< (1) dispatch
allocation_plan (1) ----< (1) store_confirmations
allocation_plan (1) ----< (M) sales_daily
dispatch (1) ----< (1) store_confirmations

store_confirmations (1) ----< (M) photo_proofs
store_confirmations (1) ----< (M) issues
```

### Storage

All data is stored as in-memory Python dataclasses during a run, persisted to JSON files in an output directory. No database is required for the MVP. The simulation generates the data, the reconciliation engine enriches it, and the dashboard renders it - all in a single process or from loaded JSON.

## 4. Validation rules

Validation rules ensure data integrity at generation and computation time. The simulation layer enforces these rules; violations raise a `ValidationError` and abort the run.

| # | Rule | Table(s) | Enforcement |
|---|------|----------|-------------|
| V-01 | store_id is unique across stores | stores | Raise on duplicate at generation |
| V-02 | campaign_id is unique across campaigns | campaigns | Raise on duplicate at generation |
| V-03 | campaign_end_date > campaign_start_date | campaigns | Raise if end <= start |
| V-04 | allocation_plan: planned_quantity > 0 | allocation_plan | Raise if <= 0 |
| V-05 | dispatch: shipped_quantity >= 0 | dispatch | Raise if < 0 |
| V-06 | store_confirmations: received_quantity >= 0 | store_confirmations | Raise if < 0 |
| V-07 | store_confirmations: received_quantity <= shipped_quantity + 10% tolerance | store_confirmations, dispatch | Raise if received > shipped x 1.10 (overage beyond tolerance) |
| V-08 | sales_daily: units_sold >= 0 | sales_daily | Raise if < 0 |
| V-09 | sales_daily: on_hand_quantity >= 0 | sales_daily | Raise if < 0 (triggers EX-18) |
| V-10 | sales_daily: units_sold <= on_hand_quantity + units_received_that_day | sales_daily | Raise if sold > available (cannot sell more than on-hand + received) |
| V-11 | photo_proofs: photo_timestamp is within visit window | photo_proofs, store_confirmations | Raise if timestamp outside visit start/end |
| V-12 | issues: severity in (critical, watch, info) | issues | Raise on invalid severity |
| V-13 | issues: status in (raised, open, in_progress, resolved, closed, paused, escalated, waived) | issues | Raise on invalid status |
| V-14 | issues: resolution_time_hours is null when status != resolved/closed | issues | Raise if resolved but time is null |
| V-15 | issues: parent_id is null for original exceptions, set for reopens | issues | Raise if reopen without parent_id |

## 5. Exception rules

The exception engine evaluates 24 reconciliation rules (EX-01 to EX-24) from T02 and maps them to the 8-category taxonomy from T04. Rules are evaluated on a daily batch for the previous day's events and on a weekly batch for trend metrics.

### 8-category taxonomy

| # | Exception type | Description | Default owner | SLA window |
|---|---------------|-------------|---------------|------------|
| 1 | Missing confirmation | Visit completed but no system confirmation posted within 4 hours | Field Operations | 48 hours |
| 2 | Quantity mismatch | Variance between planned/shipped/received/sold exceeds tolerance | DC Operations or Store Manager | 48 hours |
| 3 | Missing photo proof | Visit completed but photo proof missing or failed validation | Field Representative | 48 hours |
| 4 | Late setup | Campaign start date passed but store setup not completed | Store Manager | 48 hours |
| 5 | Stockout risk | WOC < supplier lead time weeks | Replenishment Planner | 24 hours |
| 6 | Overstock risk | WOC > 2x lead time OR WOC > remaining selling window | Merchant | 7 days |
| 7 | Low sell-through | Sell-through below period target threshold | Merchant + Planner | 7 days |
| 8 | Unresolved issue aging | Open exception past SLA window or aging threshold | Operations Lead | 24 hours (escalate) |

### Taxonomy to rule mapping

| Exception type | Upstream rule codes |
|---------------|---------------------|
| Missing confirmation | EX-03, EX-07 |
| Quantity mismatch | EX-01, EX-02, EX-04, EX-05, EX-06, EX-16, EX-17, EX-18, EX-23 |
| Missing photo proof | Campaign failure modes #4, #16 |
| Late setup | EX-08, EX-09, Campaign failure mode #5 |
| Stockout risk | EX-10 |
| Overstock risk | EX-11, EX-12 |
| Low sell-through | EX-13, EX-14, EX-15, EX-19 |
| Unresolved issue aging | EX-20, EX-21, EX-22 |

### Severity model

Three-tier severity assigned at raise time using the severity matrix (T04).

| Severity | Weight | SLA window | Escalation | Color |
|----------|--------|------------|------------|-------|
| Critical | 3 | 24 hours | On-call manager paged | Red |
| Watch | 2 | 48-72 hours | Daily action list, manager notified day 2 | Amber |
| Info | 1 | 7-14 days | Weekly review | Blue |

### Priority score formula

```
priority_score = (severity_weight x 100) + age_pressure + business_impact + campaign_urgency
```

- severity_weight: Critical=3, Watch=2, Info=1
- age_pressure: (days_open / SLA_window_days) x 50, capped at 50
- business_impact: hero SKU or flagship store = 30, standard = 15, low-velocity = 5
- campaign_urgency: 20 if active campaign in launch window (first 7 days), 10 if active outside launch window, 0 if no campaign

Range: 1 (minimum) to 200 (maximum).

### Exception lifecycle state machine

```
RAISED --> OPEN --> IN_PROGRESS --> RESOLVED --> CLOSED
                  --> PAUSED --> IN_PROGRESS
                  --> ESCALATED --> IN_PROGRESS
                  --> WAIVED --> CLOSED
RESOLVED --> OPEN (reopen, creates new exception_id linked to parent)
```

### SLA aging buckets

| Bucket | Age range | Meaning |
|--------|-----------|---------|
| 0 | 0-5 days | Fresh: within normal SLA window |
| 1 | 6-15 days | Aging: approaching or at SLA limit |
| 2 | 16-30 days | Overdue: SLA breached, escalation active |
| 3 | 30+ days | Chronic: broken workflow, needs root-cause intervention |

### SLA pause conditions

| Condition | Max pause duration |
|-----------|-------------------|
| Awaiting vendor confirmation | 72 hours, then auto-resumes |
| Awaiting store response | 48 hours, then auto-resumes |
| System outage | Duration + 4 hours, then auto-resumes |
| Goods in transit | Estimated arrival + 24 hours |

### Root cause taxonomy

| Category | Sub-categories |
|----------|---------------|
| supplier | short_ship, wrong_sku, late_delivery, quality_issue |
| dc | short_pick, wrong_carton, system_error, delay |
| store | miscount, unreported_damage, training_gap, space_constraint |
| system | integration_failure, sync_delay, rule_error, data_quality |
| forecast | over_forecast, under_forecast, demand_shift |
| customer | order_change, cancellation, no_show, complaint |
| logistics | carrier_delay, route_failure, capacity_constraint |

## 6. KPI definitions

The MVP implements 10 KPIs from T03 (5 process, 0 performance, 5 risk). Each KPI has a threshold table (green/amber/red).

### MVP KPI catalog

| # | KPI | Type | Formula | Threshold | Sections |
|---|-----|------|---------|-----------|----------|
| 1 | Network Compliance % | process | Composite of L2 audit pass rate, weighted | G>=90, A 80-90, R<80 | 1, 2, 3 |
| 2 | OSA % | process | Campaign SKUs on shelf at audit / total campaign SKUs | G>=95, A 90-95, R<90 | 1, 2, 3, 4 |
| 3 | Campaign Coverage % | process | Visits completed / visits planned | G>=95, A 85-95, R<85 | 1, 2, 3, 4 |
| 4 | Campaign Compliance % | process | Stores passing L2 audit / stores audited | G>=90, A 80-90, R<80 | 1, 2, 4 |
| 5 | On-Launch Activation % | process | Stores executed within launch window / total stores | G>=90, A 75-90, R<75 | 4 |
| 6 | Stockout Risk Items Count | risk | Count of SKUs where WOC < lead time | G=0, A 1-5, R>5 | 1, 2 |
| 7 | Open Exception Count | risk | Total open exceptions by severity | G<=50, A 50-150, R>150 | 1, 2, 5 |
| 8 | Aged Exception Count (30+) | risk | Open exceptions older than 30 days | G=0, A 1-5, R>5 | 1, 2, 5 |
| 9 | MTTR (hours) | risk | Mean time to resolve for closed items in period | G<=24, A 24-72, R>72 | 1, 2, 5, 6 |
| 10 | SLA Met % | risk | Closed items resolved within target / total closed | G>=90, A 80-90, R<80 | 1, 2, 5, 6 |

### Cross-section KPI mapping

Each KPI is computed once and rolled up to consuming sections (single source of truth).

| KPI | Sec 1 (Tiles) | Sec 2 (Area Mgr) | Sec 3 (Store) | Sec 4 (Campaign) | Sec 5 (Exceptions) | Sec 6 (SLA) |
|-----|---|---|---|---|---|---|
| 1 Network Compliance | x | x | x | . | . | . |
| 2 OSA | x | x | x | x | . | . |
| 3 Campaign Coverage | x | x | x | x | . | . |
| 4 Campaign Compliance | x | x | . | x | . | . |
| 5 On-Launch Activation | . | . | . | x | . | . |
| 6 Stockout Risk Items | x | x | . | . | . | . |
| 7 Open Exception Count | x | x | . | . | x | . |
| 8 Aged Exception Count | x | x | . | . | x | . |
| 9 MTTR | x | x | . | . | x | x |
| 10 SLA Met % | x | x | . | . | x | x |

### Deferred KPIs (v2)

- Sales vs. Target %, Conversion Rate, ATV (performance) - requires POS data source.
- Planogram Compliance, POSM Compliance, Pricing Accuracy (sub-components) - rolled into Network Compliance composite for MVP.
- OOS Rate, Training Completion % - secondary metrics.
- Exception Reopen Rate, MTTD, SLA Pause Rate - v2 view refinements.

## 7. Dashboard pages

The dashboard has 6 sections. Each section is a page or panel with a defined primary user and cadence. The hierarchy is executive (1) drills down to regional (2) drills down to store (3), while campaign (4), exception (5), and SLA (6) cut across all geographies.

### Section 1: Executive KPI tiles

- **Primary user:** HQ Ops Analyst
- **Cadence:** Daily glance, weekly review
- **Layout:** Up to 10 tiles, each showing one number with trend arrow and sparkline. Color-coded against threshold (green/amber/red). One-click drill-down to the area, region, or store that drove the change.
- **Tiles:** Network Compliance %, OSA %, Campaign Coverage %, Campaign Compliance %, Stockout Risk Items, Open Exception Count, Aged Exception Count, MTTR, SLA Met %. (On-Launch Activation appears in Section 4.)

### Section 2: Area Manager breakdowns

- **Primary user:** Area Manager
- **Cadence:** Daily stand-up, weekly
- **Layout:** One row per region. Columns: the same executive metrics computed for that region only. Heatmap coloring on the worst column. Regional ranking by composite health score at top. Drill-through from a regional cell to a store status table filtered to that region. Comparative columns: vs. last week, vs. plan, rank within network.

### Section 3: Store status table

- **Primary user:** Area Manager, Store PIC
- **Cadence:** Daily
- **Layout:** Sortable, filterable grid, one row per store. Columns: store ID, name, region, format, store health (composite 0-100), status (green/amber/red), last visit date, last audit date, days since last audit, last audit compliance % (L1/L2/L3), OSA %, open exception count (critical/watch/info), open corrective action count with oldest age, aging bucket for oldest open item, active campaign count, coverage %, last sync timestamp.
- **Defaults:** Sort red stores first, then by oldest open exception.

### Section 4: Campaign performance view

- **Primary user:** HQ Ops Analyst, Trade Marketing
- **Cadence:** Daily during campaign, weekly
- **Layout:** Campaign selector (defaults to active campaigns sorted by end date). Campaign header: name, type, start/end, store count, days remaining, HQ owner. Tiles: coverage %, compliance %, OSA %, exception count, sell-through vs. forecast, on-launch activation %. Region-level breakdown table. Store-level table: store, visit status, audit level, audit status, compliance score, exception flag, last photo timestamp. Exception drill-down: stores with open campaign-related exceptions.

### Section 5: Exception backlog view

- **Primary user:** HQ Ops Analyst, Area Manager
- **Cadence:** Continuous (real-time)
- **Layout:** Stack-ranked list of open exceptions sorted by severity then age. Filter bar: severity, owner, exception type, region, campaign, store, date raised. Aging buckets at top: 0-5, 6-15, 16-30, 30+ days with count and %. Per row: exception ID, type, store, campaign, severity, owner, age in days, deadline, SLA status (within/approaching/breached/paused), last update, link to source record. Side panel: trend chart of new vs. resolved over last 30 days by severity.

### Section 6: SLA / aging view

- **Primary user:** HQ Ops Analyst, support owners
- **Cadence:** Continuous (real-time)
- **Layout:** Tiles at top: SLA Met %, SLA Breach %, MTTR, MTTD, Avg Active Age. SLA breakdown by work item type (visits, audits, corrective actions, exceptions, escalations). SLA breakdown by priority (critical, high, medium, low). Trend chart: SLA Met % and MTTR over last 12 weeks with target line. Per-owner table: owner, items open, within SLA, approaching, breached, average age. Aging distribution chart: bar chart of open items by aging bucket per work item type.

## 8. Report sections

The report module generates structured text/HTML reports for each dashboard section. Reports are designed to be machine-generated and human-readable.

| # | Report | Sections covered | Output format | Primary user |
|---|--------|-----------------|----------------|---------------|
| R-01 | Executive summary | Section 1 | Text + table | HQ Ops Analyst |
| R-02 | Area manager breakdown | Section 2 | Text + table | Area Manager |
| R-03 | Store status report | Section 3 | Table (sortable) | Area Manager, Store PIC |
| R-04 | Campaign performance report | Section 4 | Text + table | HQ Ops Analyst, Trade Marketing |
| R-05 | Exception backlog report | Section 5 | Table + aging summary | HQ Ops Analyst |
| R-06 | SLA / aging report | Section 6 | Text + table + trend | HQ Ops Analyst |
| R-07 | Daily action list | Action list | Table (top 20 ranked) | HQ Ops Analyst |

Each report includes:
- Header: report name, generated_at timestamp, aging_date, data freshness.
- Body: the section's KPIs and data tables.
- Footer: source data file references, row counts, threshold definitions used.

## 9. Test strategy

The test strategy ensures every formula, rule, and workflow path is verified against known inputs and expected outputs. Tests use synthetic data with deterministic seeds.

### Test layers

| # | Layer | What it tests | Test count target |
|---|-------|--------------|-------------------|
| T-01 | Unit: models | Dataclass construction, field validation, type checking | 8+ (one per table) |
| T-02 | Unit: simulation | Data generation produces correct row counts, valid ranges, deterministic with seed | 8+ |
| T-03 | Unit: reconciliation formulas | Each of the 16 formulas computes correctly against the worked example from T02 | 16 |
| T-04 | Unit: exception rules | Each of the 24 rules (EX-01 to EX-24) triggers correctly with known inputs | 24 |
| T-05 | Unit: exception taxonomy | All 24 rules map to the correct taxonomy type | 1 |
| T-06 | Unit: severity scoring | Priority score formula computes correctly for the 4 worked examples from T04 | 4 |
| T-07 | Unit: SLA aging | Aging buckets, SLA status, pause logic, auto-escalation triggers | 8+ |
| T-08 | Unit: state machine | All valid state transitions succeed; all invalid transitions raise | 10+ |
| T-09 | Unit: action list | Action list generation: filter, sort, output top 20 with correct fields | 3+ |
| T-10 | Unit: KPI computation | Each of the 10 MVP KPIs computes correctly against known data | 10 |
| T-11 | Unit: thresholds | Each KPI returns correct color (green/amber/red) for boundary values | 10 |
| T-12 | Unit: dashboard sections | Each of the 6 sections renders without error and contains expected data | 6 |
| T-13 | Unit: reports | Each of the 7 report types generates without error and contains expected sections | 7 |
| T-14 | Integration: demo story | Demo story runs end-to-end from Day 1 through Day 14 without errors | 1 |
| T-15 | Integration: CLI | Each CLI command (generate-data, build-exceptions, report) runs and produces expected output files | 3 |
| T-16 | Regression: consistency checks | All 7 cross-document consistency checks pass (exception count, rule count, KPI count, aging buckets, severity tiers, tracker fields, synthetic data) | 7 |

### Worked example for testing (from T02)

The allocation accuracy and sell-through formulas are tested against the T02 worked example:
- Planned: 200, Shipped: 190, Received: 188, Sold: 150, On-hand: 38, Lead time: 2 weeks.
- Allocation accuracy: 94%
- Shipped-to-plan fill rate: 95%
- Receiving accuracy: 98.95%
- Sell-through: 79.8%
- WOC: 1.01 weeks
- Stockout risk: 1 (WOC < lead time)

### Priority score worked examples for testing (from T04)

1. Critical stockout in launch window: severity 3, age 1/1, hero SKU, active launch = 400.
2. Watch quantity mismatch, day 3: severity 2, age 3/2 (capped 50), standard SKU, no campaign = 265.
3. Info receiving variance, day 5: severity 1, age 5/7, low-velocity SKU, no campaign = 141.
4. Missing photo proof at flagship, day 2: severity 2, age 2/2, flagship store, active launch = 300.

### Test conventions

- All tests use `pytest` with deterministic random seeds (`random.seed(42)` or equivalent).
- Test fixtures provide synthetic data factories that generate minimal valid records for each table.
- No external network calls. No file system writes outside the test temp directory.
- Tests run in under 30 seconds for the full suite.

## 10. MVP scope

### What the MVP ships

| Component | MVP scope | Deferred |
|-----------|-----------|----------|
| Data simulation | Store network (40 stores), campaigns (2-3), SKUs (12), visits, shipments, receipts, sales, exceptions, photo metadata | Real-time streaming |
| Reconciliation engine | 16 formulas, 24 exception rules, 4-quantity variance tracking | WSSI view, transfer/markdown engine |
| Exception management | 8-category taxonomy, severity scoring, SLA aging, state machine, action list, root cause tagging, reopen tracking | Per-role filtered views |
| KPI dashboard | 6 sections, 10 MVP KPIs, threshold tables, drill-down, aging buckets | Performance KPIs, sub-component compliance tiles |
| Demo story | Campaign launch, store execution, mismatches, exception surfacing, action list | - |
| Reports | 7 report types (executive, area, store, campaign, exceptions, SLA, action list) | - |

### Deliverables

1. Python package `retail_ops_control_tower` installable from source.
2. CLI commands: `retail-ops-generate-data`, `retail-ops-build-exceptions`, `retail-ops-report`.
3. Demo story script that runs the Summer Peach LTO 2026 scenario end-to-end.
4. JSON output files for all 8 data tables.
5. Dashboard rendered as text or HTML.
6. Test suite covering all 16 test layers.
7. Documentation: PRD, data dictionary, implementation plan, README.

### Acceptance criteria

**AC-1: Data simulation generates a complete campaign dataset.**
- Input: Configuration with 40 stores, 1 campaign, 12 SKUs, 28-day window, seed=42.
- Output: JSON files for all 8 tables with row counts matching expected values.
- Verify: `test_simulation.py::test_full_generation`

**AC-2: Reconciliation engine computes all 16 formulas.**
- Input: The T02 worked example (planned 200, shipped 190, received 188, sold 150).
- Output: Allocation accuracy 94%, fill rate 95%, receiving accuracy 98.95%, sell-through 79.8%, WOC 1.01.
- Verify: `test_reconciliation.py::test_worked_example`

**AC-3: Exception engine evaluates all 24 rules.**
- Input: Store-SKU records with known variances triggering each rule.
- Output: Exceptions raised with correct type, severity, and taxonomy mapping.
- Verify: `test_exceptions.py::test_all_24_rules`

**AC-4: Priority score computes correctly for worked examples.**
- Input: The 4 worked examples from T04.
- Output: Scores 400, 265, 141, 300.
- Verify: `test_exceptions.py::test_priority_score_worked_examples`

**AC-5: State machine enforces valid transitions.**
- Input: Sequence of valid and invalid state transitions.
- Output: Valid transitions succeed; invalid transitions raise `InvalidTransition`.
- Verify: `test_exceptions.py::test_state_machine`

**AC-6: SLA aging computes correct buckets and status.**
- Input: Exceptions with known ages and SLA windows.
- Output: Correct aging bucket (0-3) and SLA status (within/approaching/breached/paused).
- Verify: `test_exceptions.py::test_sla_aging`

**AC-7: Action list generates top 20 ranked exceptions.**
- Input: Set of open exceptions with varying priority scores.
- Output: Top 20 sorted by priority_score DESC, age DESC, exception_id ASC, with all 18 fields per row.
- Verify: `test_exceptions.py::test_action_list`

**AC-8: All 10 MVP KPIs compute correctly.**
- Input: Known dataset with calculable KPI values.
- Output: Each KPI returns a numeric value and a threshold color.
- Verify: `test_dashboard.py::test_all_10_kpis`

**AC-9: All 6 dashboard sections render without error.**
- Input: Generated dataset.
- Output: Each section renders and contains expected data structures.
- Verify: `test_dashboard.py::test_all_sections_render`

**AC-10: All 7 report types generate without error.**
- Input: Generated dataset.
- Output: Each report type produces a readable output with expected sections.
- Verify: `test_reports.py::test_all_reports`

**AC-11: Demo story runs end-to-end.**
- Input: Summer Peach LTO 2026 configuration.
- Output: Day 1 through Day 14 execution without errors; action list produced.
- Verify: `test_demo.py::test_demo_story_e2e`

**AC-12: CLI commands work.**
- Input: CLI invocation with valid arguments.
- Output: Expected output files generated.
- Verify: `test_cli.py::test_generate_data`, `test_build_exceptions`, `test_report`

**AC-13: Cross-document consistency checks pass.**
- Input: Full generated dataset.
- Output: 8 exception types, 24 rules evaluated, 10 KPIs computed, 4 aging buckets, 3 severity tiers, all tracker fields present, synthetic data only.
- Verify: `test_regression.py::test_consistency_checks`

## 11. Architecture

### System diagram

```
+-------------------+     +----------------------+     +------------------------+
|  Configuration    |     |  Data Simulation     |     |  Reconciliation Engine |
|  (config.py)      |---->|  Layer               |---->|                        |
|                   |     |  - stores             |     |  - 16 formulas         |
|  - store count    |     |  - campaigns          |     |  - 4-qty variance      |
|  - campaign params|     |  - allocation_plan    |     |  - 24 exception rules  |
|  - SKU count      |     |  - dispatch           |     |                        |
|  - seed           |     |  - store_confirmations |     +------------------------+
|  - thresholds     |     |  - photo_proofs       |                |
+-------------------+     |  - sales_daily        |                v
                          |  - issues (seeded)    |     +------------------------+
                          +----------------------+     |  Exception Management   |
                                       |               |  System                 |
                                       |               |  - 8-cat taxonomy       |
                                       v               |  - severity scoring     |
                          +----------------------+     |  - priority score       |
                          |  JSON Output          |     |  - state machine       |
                          |  (output/*.json)      |     |  - SLA aging            |
                          +----------------------+     |  - action list          |
                                       |               |  - action playbook       |
                                       |               +------------------------+
                                       v                               |
                          +----------------------+                    |
                          |  KPI Dashboard        |<-------------------+
                          |  - 10 MVP KPIs        |
                          |  - 6 sections         |
                          |  - threshold tables   |
                          |  - drill-down          |
                          +----------------------+
                                       |
                                       v
                          +----------------------+
                          |  Reports              |
                          |  - 7 report types     |
                          |  - daily action list  |
                          +----------------------+
                                       |
                                       v
                          +----------------------+
                          |  Demo Story Runner    |
                          |  (Summer Peach LTO)   |
                          +----------------------+
```

### Data flow

1. Configuration defines store count, campaign parameters, SKU count, seed, and thresholds.
2. Data simulation layer generates 8 tables and writes JSON output files.
3. Reconciliation engine reads the simulated data, computes 16 formulas, evaluates 24 exception rules, and enriches the issues table.
4. Exception management system computes priority scores, SLA status, aging buckets, and generates the daily action list.
5. KPI dashboard reads the enriched data, computes 10 MVP KPIs, applies thresholds, and renders 6 sections.
6. Reports module generates 7 report types from the dashboard data.
7. Demo story runner orchestrates steps 1-6 for the Summer Peach LTO 2026 scenario across Day 1 to Day 14.

### Component descriptions

- **Data simulation layer:** Generates synthetic coffee chain data. Input: configuration. Output: 8 JSON files. Key behavior: deterministic with seed, enforces validation rules V-01 to V-15.
- **Reconciliation engine:** Computes variances and formulas. Input: simulated data. Output: enriched allocation_plan, dispatch, store_confirmations, sales_daily records with computed fields. Key behavior: evaluates all 24 exception rules on each pass.
- **Exception management system:** Manages exception lifecycle. Input: enriched data with exception triggers. Output: issues table with priority scores, SLA status, aging buckets, and daily action list. Key behavior: state machine enforces valid transitions, SLA pauses, auto-escalation.
- **KPI dashboard:** Renders 6 sections with 10 KPIs. Input: enriched data. Output: dashboard sections (text or HTML). Key behavior: single source of truth, threshold color-coding, drill-down.
- **Reports module:** Generates structured reports. Input: dashboard data. Output: 7 report types. Key behavior: machine-generated, human-readable.
- **Demo story runner:** Orchestrates the full pipeline. Input: Summer Peach LTO 2026 configuration. Output: Day 1 to Day 14 results. Key behavior: exercises every major feature.

## 12. Tech stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.11+ | Required by project; widely available |
| Package manager | uv | Per global context; fast, venv-aware |
| Data structures | dataclasses | Native, typed, serializable to JSON |
| CLI | argparse | Standard library, no extra dependency |
| Dashboard rendering | text + optional HTML | MVP keeps it simple; no web framework needed |
| Testing | pytest | Standard, good fixture support |
| Data persistence | JSON files | No database needed for MVP; human-readable |
| Random generation | random module with seed | Deterministic, reproducible |

### Key thresholds

| Threshold | Value | Source |
|-----------|-------|--------|
| Store count (demo) | 40 | synthesis.md demo story |
| Campaign SKU count (demo) | 12 | synthesis.md demo story |
| Campaign duration (demo) | 4 weeks (28 days) | synthesis.md demo story |
| Field rep count (demo) | 8 | synthesis.md demo story |
| Allocation shortage tolerance | 5% (shipped < planned x 0.95) | T02 EX-01 |
| Critical shortage tolerance | 20% (shipped < planned x 0.80) | T02 EX-02 |
| Stockout risk WOC threshold | WOC < supplier_lead_time_weeks | T02 EX-10 |
| Overstock early signal | WOC > 2 x lead_time_weeks | T02 EX-11 |
| Overstock late signal | WOC > remaining_selling_window_weeks | T02 EX-12 |
| Sell-through miss threshold | < 70% of target | T02 EX-13 |
| Critical sell-through miss | < 50% of target | T02 EX-14 |
| Action list size | Top 20 | T04 action list algorithm |
| Critical SLA window | 24 hours | T04 severity tiers |
| Watch SLA window | 48 hours (default), 72 hours (investigate) | T04 severity tiers |
| Info SLA window | 7 days (default), 14 days (investigation) | T04 severity tiers |
| Aging buckets | 0-5, 6-15, 16-30, 30+ days | T03, T04 |
| Reopen escalation threshold | > 2 reopens within 30 days | T04 reopen rules |
| SLA pause max (vendor) | 72 hours | T04 pause rules |
| SLA pause max (store) | 48 hours | T04 pause rules |

## 13. Self-review

### Are acceptance criteria testable?

Yes. Each AC specifies input (configuration, dataset, or known values), output (numeric values, file existence, error behavior), and verification (named pytest test). AC-2 through AC-6 test against published worked examples from the research, which have deterministic expected outputs.

### Is the architecture clear?

Yes. The system diagram shows all 6 components and their data flow. The data flow traces from configuration through simulation, reconciliation, exception management, dashboard, reports, and demo story. Each component has a defined input, output, and key behavior. The separation between reconciliation engine (formulas and rules) and exception management (taxonomy, severity, lifecycle) is intentional: reconciliation detects variances, exception management triages them.

### Is the MVP scope realistic?

Yes. The MVP implements 10 KPIs (not 18), 24 exception rules (mapped to 8 types, not 24 separate workflows), and 6 dashboard sections with text/HTML rendering (not a web framework). The deferred items (WSSI, transfer/markdown engine, performance KPIs, sub-component tiles, per-role filtering) are documented with rationale. The demo story is the acceptance scenario per the scope guard.

### Gaps

- No cost estimates (portfolio project, no budget).
- No v2 architecture (deferred items documented but not designed).
- No CI/CD integration (scope guard allows a single GitHub Action for tests, but T21 gates publishing).
- Assumption: JSON file persistence is sufficient for 40 stores x 12 SKUs x 28 days = ~13K sales_daily rows. If performance is an issue, SQLite can be added without changing the data model.

## 14. Open questions

1. Should the dashboard render as terminal text, HTML files, or both? (PRD assumes both; implementation plan should confirm.)
2. Should the demo story runner produce a Jupyter notebook or a Python script? (Synthesis says "script or notebook"; T07 CLI suggests script.)
3. What is the default output directory for JSON files? (PRD assumes `output/` relative to the project root.)
4. Should the threshold values be configurable via a YAML file or hard-coded in `config.py`? (PRD assumes hard-coded with a note that they are starting defaults.)
