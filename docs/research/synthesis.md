# Research Synthesis

> Scope: Merge T01-T04 research into a single project scope definition. This document is the bridge between research and implementation. It defines what the portfolio project builds, what it does not build, and how each feature traces back to a specific research finding.
>
> Source documents:
> - `docs/research/retail-campaign-execution.md` (T01)
> - `docs/research/allocation-reconciliation.md` (T02)
> - `docs/research/ops-kpi-scorecard.md` (T03)
> - `docs/research/exception-management.md` (T04)

## Project definition

The Retail Operations Control Tower is a Python-based dashboard application that simulates a multi-store coffee chain running a seasonal limited-time-offer (LTO) campaign. It tracks the campaign from HQ planning through store execution, allocation reconciliation, and exception management. The dashboard surfaces operational gaps and generates a priority-ranked daily action list so the ops team knows what to fix first.

All data is synthetic. No real company data, internal knowledge, or real-world retail operations experience is claimed.

## Minimum portfolio-grade scope

The project has five components. Each is derived directly from the research and is the minimum set that tells a complete operational story.

### 1. Data simulation layer

Generates a synthetic coffee chain: 30-80 stores across 4-6 regions, 2-3 active campaigns, 10-20 campaign SKUs, field reps with visit schedules, shipments, receipts, sales, and exceptions. Produces the four tracker schemas defined in T01 and T02 (campaign execution: 39 fields, allocation: 45 fields).

Sources: T01 "Portfolio modeling decisions" (9 safe-to-simulate categories), T02 "Portfolio modeling decisions" (10 safe-to-simulate categories).

### 2. Reconciliation engine

Computes variances across the four-quantity lifecycle (planned -> shipped -> received -> sold). Evaluates the 24 exception rules from T02 and raises exceptions using the 8-category taxonomy from T04. Computes the process compliance, sales performance, and risk metrics defined in T02.

Sources: T02 "Core formulas" (16 formulas across 3 categories), T02 "Exception rules" (EX-01 through EX-24), T04 "Exception taxonomy" (8 types).

### 3. Exception management system

Applies the severity scoring model (priority_score = severity_weight x 100 + age_pressure + business_impact + campaign_urgency, range 1-200). Manages the exception lifecycle state machine (RAISED -> OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED). Computes SLA aging buckets (0-5, 6-15, 16-30, 30+ days) and generates the daily action list.

Sources: T04 "Severity scoring" (formula, matrix, worked examples), T04 "SLA aging rules" (buckets, pause rules, auto-escalation), T04 "Daily action list" (generation algorithm, 18 fields per row), T04 "Exception lifecycle state machine".

### 4. KPI dashboard

Renders 6 dashboard sections with the 10 MVP KPIs from T03. Each KPI has threshold defaults (green/amber/red). The dashboard supports drill-down from executive tiles to area manager breakdowns to store status, and includes the exception backlog and SLA/aging views.

Sources: T03 "Dashboard sections" (6 sections with primary users and cadence), T03 "MVP recommendation" (10 KPIs: 5 process, 0 performance, 5 risk), T03 "MVP threshold defaults" (green/amber/red per KPI), T03 "Cross-section KPI mapping" (single source of truth).

### 5. Demo story runner

A script or notebook that runs the demo scenario end-to-end: a seasonal LTO campaign launches, some stores execute correctly, some have mismatches, and the dashboard surfaces what to fix. See "Demo story" section below.

Sources: T01 "Common failure modes" (17 modes), T02 "Common failure modes" (20 modes), T04 "Codified action playbook" (8 exception types with default actions).

## Traceability table: research finding to project feature

This table maps every major research finding to a concrete project feature. If a research finding does not produce a project feature, it is marked "deferred" with a reason.

### From T01: Retail Campaign Execution

| # | Research finding | Project feature | Status |
|---|-----------------|-----------------|--------|
| 1 | 8-step campaign execution workflow (HQ planning through corrective action) | Simulation generates campaign lifecycle events following the 8 steps | In scope |
| 2 | 39 tracker fields across 5 categories (campaign, store, visit, proof, corrective) | Campaign execution data model with all 39 fields | In scope |
| 3 | Multi-level audit (L1/L2/L3) with compliance scores | Audit results simulated with level, status, score per store per campaign | In scope |
| 4 | 17 failure modes (delayed materials, pencil-whipping, late activation, etc.) | Failure modes seeded into simulation as exception triggers | In scope |
| 5 | Photo proof metadata (GPS, timestamp, user ID, store code) | Photo proof records simulated with metadata fields; no real photos | In scope |
| 6 | Real-world coffee chain patterns (PSL season, lead times, traffic spikes) | Campaign types and timing modeled on public coffee chain patterns | In scope |
| 7 | Real company data, internal knowledge, or operational experience | Not simulated; all data is synthetic | Non-goal |

### From T02: Allocation and Reconciliation

| # | Research finding | Project feature | Status |
|---|-----------------|-----------------|--------|
| 8 | 7-step allocation lifecycle (planned -> shipped -> received -> sold -> risk -> exceptions -> close-out) | Reconciliation engine computes variances at each stage transition | In scope |
| 9 | 45 tracker fields (allocation, shipment, receiving, sales, reconciliation) | Allocation data model with all 45 fields | In scope |
| 10 | 16 formulas: 6 process compliance, 6 sales performance, 4 risk | All 16 formulas implemented in the reconciliation engine | In scope |
| 11 | 24 exception rules (EX-01 through EX-24) with trigger conditions and severity | All 24 rules coded as evaluation logic in the exception engine | In scope |
| 12 | Process compliance vs. sales performance distinction | KPI dashboard separates process metrics from performance metrics (per T03 MVP) | In scope |
| 13 | Worked example (200 units planned, 190 shipped, 188 received, 150 sold) | Demo scenario includes a store matching this pattern as a stockout case | In scope |
| 14 | Weeks of cover, stockout risk, overstock risk formulas | Risk metrics computed and surfaced as exceptions | In scope |
| 15 | WSSI view (Weekly Sales, Stock and Intake) | Deferred to v2 (useful but not required for MVP dashboard) | Deferred |
| 16 | Inter-store transfers and markdown events as resolution actions | Deferred to v2 (exception state machine supports the record, but no transfer/markdown engine) | Deferred |

### From T03: Ops KPI Scorecard

| # | Research finding | Project feature | Status |
|---|-----------------|-----------------|--------|
| 17 | 6 dashboard sections (executive tiles, area manager, store status, campaign, exceptions, SLA) | All 6 sections rendered in the dashboard | In scope |
| 18 | 18 candidate KPIs tagged process/performance/risk | 10 MVP KPIs implemented; 8 deferred to v2 | In scope (MVP subset) |
| 19 | MVP set: 5 process + 5 risk KPIs, 0 performance | 10 KPIs implemented with threshold defaults | In scope |
| 20 | Cross-section KPI mapping (single source of truth) | Each KPI computed once, rolled up to consuming sections | In scope |
| 21 | Threshold defaults (green/amber/red per KPI) | Hard-coded threshold tables in dashboard layer | In scope |
| 22 | Aging buckets (0-5, 6-15, 16-30, 30+ days) from ITSM frameworks | Aging buckets computed at render time | In scope |
| 23 | Performance KPIs (sales vs. target, conversion, ATV) | Deferred to v2 (requires POS data source beyond MVP scope) | Deferred |
| 24 | Sub-component compliance (planogram, POSM, pricing as separate tiles) | Deferred to v2 (rolled into Network Compliance composite for MVP) | Deferred |

### From T04: Exception Management

| # | Research finding | Project feature | Status |
|---|-----------------|-----------------|--------|
| 25 | 8-category exception taxonomy | Exception engine classifies events into 8 types | In scope |
| 26 | Mapping of 24 rules (EX-01 to EX-24) to 8 taxonomy types | Traceability maintained from dashboard exception to source rule | In scope |
| 27 | 3-tier severity model (Critical/Watch/Info) with SLA windows | Severity assigned at raise time using the severity matrix | In scope |
| 28 | Priority score formula (severity_weight x 100 + age_pressure + business_impact + campaign_urgency) | Formula implemented; score displayed per exception | In scope |
| 29 | SLA aging rules with 4 buckets, pause rules, auto-escalation | Aging, pause, and auto-escalation logic implemented | In scope |
| 30 | Daily action list generation algorithm (filter, sort, output top 20) | Action list generated on-demand and daily | In scope |
| 31 | Exception lifecycle state machine (RAISED -> OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED) | State machine implemented with transition validation | In scope |
| 32 | Codified action playbook (8 exception types with default actions) | Action playbook displayed per exception in the action list | In scope |
| 33 | Root cause taxonomy (7 categories: supplier, dc, store, system, forecast, customer, logistics) | Root cause tagging on exception close-out | In scope |
| 34 | Reopen rules (new exception_id linked to parent, escalation after 2 reopens) | Reopen tracking implemented | In scope |
| 35 | SLA pause conditions (vendor, store, system, transit) | Pause logic implemented with max-duration auto-resume | In scope |
| 36 | Per-role action list filtering (7 roles) | Deferred to v2 (MVP shows the operator view; role filtering is a UI layer addition) | Deferred |

## Feature summary

| Component | Features in scope | Features deferred |
|-----------|-------------------|-------------------|
| Data simulation | Store network, campaigns, SKUs, visits, shipments, receipts, sales, exceptions, photo metadata | Real-time streaming |
| Reconciliation engine | 16 formulas, 24 exception rules, 4-quantity variance tracking | WSSI view, transfer/markdown engine |
| Exception management | 8-category taxonomy, severity scoring, SLA aging, state machine, action list, root cause tagging, reopen tracking | Per-role filtered views |
| KPI dashboard | 6 sections, 10 MVP KPIs, threshold tables, drill-down, aging buckets | Performance KPIs, sub-component compliance tiles |
| Demo story | Campaign launch, store execution, mismatches, exception surfacing, action list | - |

## Deferred items and rationale

Items marked "deferred" above are not dropped. They are explicitly out of scope for the MVP but documented so a v2 plan can pick them up without re-research.

1. **WSSI view** (T02): A weekly trading view is useful but not required for the MVP. The reconciliation engine already computes on-hand and weeks of cover; the WSSI presentation layer can be added later.

2. **Transfer and markdown engine** (T02): The exception state machine supports recording a transfer or markdown as a resolution, but there is no standalone engine that optimizes transfer decisions or markdown pricing. This is a v2 feature.

3. **Performance KPIs** (T03): Sales vs. target, conversion rate, and ATV require a POS data source that the MVP does not simulate. The simulation produces unit sales (for sell-through), but not transaction-level POS data. v2 adds this.

4. **Sub-component compliance tiles** (T03): Planogram, POSM, and pricing compliance are rolled into the Network Compliance composite for the MVP. Exposing them as separate tiles is a UI-layer addition.

5. **Per-role action list filtering** (T04): The MVP renders the control-tower operator view. Filtering by role (regional manager, store manager, field ops lead, etc.) is a UI parameterization on top of the same data.

## Demo story

The demo runs a single seasonal LTO campaign end-to-end. The scenario is designed to exercise every major feature in the project.

### Setup

- Synthetic coffee chain: 40 stores across 5 regions (North, South, East, West, Central).
- Campaign: "Summer Peach LTO 2026", a 4-week seasonal campaign with 12 campaign SKUs.
- Stores assigned: all 40. Field reps: 8, each covering 5 stores.
- Allocation plan: 200 units per store of the hero SKU, scaled by store format.

### Day 1: Campaign launch

The campaign goes live. The simulation generates visit records for all 40 stores.

- 32 stores complete setup within the launch window: visit completed, photo proof submitted, L1 audit passed, compliance score >= 85.
- 5 stores have late setup: POSM materials delayed, visit status = completed but campaign_store_status = incomplete. The exception engine raises "Late setup" exceptions (taxonomy type 4), severity Watch.
- 2 stores have missing photo proof: visit marked completed but photo_proof_url is null. The exception engine raises "Missing photo proof" exceptions (taxonomy type 3), severity Watch.
- 1 store has a quantity mismatch: 200 units planned, 170 shipped (DC short-pick), 168 received (2 damaged). The exception engine raises "Quantity mismatch" (taxonomy type 2), severity Watch, and evaluates EX-01 (allocation shortage) and EX-04 (receiving shortage).

### Day 7: Mid-campaign

Sales data is generated for the first week.

- 28 stores have healthy sell-through (>= 60% of target).
- 5 stores show low sell-through (< 50% of target). The exception engine raises "Low sell-through" exceptions (taxonomy type 7), severity Critical for the worst 2, Watch for the other 3.
- 3 stores hit stockout risk: weeks of cover dropped below supplier lead time (2 weeks). The exception engine raises "Stockout risk" exceptions (taxonomy type 5), severity Critical. These link to EX-10.

### Day 14: Exception backlog

The dashboard now shows:

- Executive tiles: Network Compliance 78% (red), OSA 91% (amber), Campaign Coverage 80% (amber), Stockout Risk Items 3 (red), Open Exception Count 18 (amber).
- Area Manager breakdown: Central region is worst (3 critical exceptions, 2 aged). Drill-down shows 2 stores driving most of the backlog.
- Store status table: 5 red stores, 8 amber, 27 green. Red stores sorted first.
- Campaign performance: coverage 80%, compliance 76%, on-launch activation 80%.
- Exception backlog: 18 open exceptions (3 critical, 10 watch, 5 info). Aging: 12 in 0-5 days, 4 in 6-15 days, 2 in 16-30 days.
- SLA/aging: SLA Met 72% (red), MTTR 38 hours (amber).

### Day 14: Daily action list

The action list generator produces the top 20 exceptions ranked by priority score. The top 5:

1. Stockout risk, Store C-12, Central region, Critical, priority 400 (hero SKU, launch window, day 1 of SLA). Expected action: place emergency replenishment order or inter-store transfer.
2. Stockout risk, Store C-07, Central region, Critical, priority 390. Same action.
3. Low sell-through, Store S-03, South region, Critical, priority 370. Expected action: diagnose root cause (wrong location, pricing gap, training gap).
4. Late setup, Store N-04, North region, Watch, priority 295. Expected action: complete setup, document root cause.
5. Quantity mismatch, Store E-02, East region, Watch, priority 265. Expected action: investigate source, initiate replacement or write-off.

### The story the demo tells

A campaign launches. Most stores execute correctly, but the control tower catches the ones that did not: late setups, missing photo proof, quantity mismatches, stockouts, and low sell-through. Each exception has a priority score, an owner, an SLA deadline, and a codified next action. The ops team works the action list, closes exceptions, and the dashboard updates. The story demonstrates that the control tower turns raw operational data into a prioritized, actionable work queue - not just a status report.

## Cross-document consistency checks

The following consistency rules must hold across the four research documents and the project implementation:

1. Exception type count: T04 defines 8 types. The project implements 8 types. No more, no less.
2. Exception rule count: T02 defines 24 rules (EX-01 to EX-24). The project evaluates all 24. T04 maps them to the 8 taxonomy types. The project preserves this mapping.
3. KPI count: T03 defines 18 candidate KPIs and recommends 10 for MVP. The project implements the 10 MVP KPIs. The 8 deferred KPIs are documented.
4. Aging buckets: T03 and T04 both use 0-5 / 6-15 / 16-30 / 30+ days. The project uses the same buckets.
5. Severity tiers: T02 defines info/watch/critical. T04 defines Critical/Watch/Info with SLA windows. The project uses the T04 severity model.
6. Tracker fields: T01 defines 39 campaign fields. T02 defines 45 allocation fields. The project implements both schemas. No fields are dropped.
7. Simulated data only: All four docs state "no real company data." The project uses only synthetic data. This is enforced in the scope guard.
