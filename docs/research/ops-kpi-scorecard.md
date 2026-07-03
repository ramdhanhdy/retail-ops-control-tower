# Retail Operations KPI Scorecard

> Scope: Define the dashboard sections and candidate KPIs for a multi-store retail/store ops control tower. Synthesized from public sources (KPI architecture guides, retail execution platform documentation, control tower references, ITSM aging dashboards). No proprietary or real company data is used. All KPIs in the downstream portfolio project will be computed from simulated data.
>
> Related research: `docs/research/retail-campaign-execution.md` (workflow and field tracker), `docs/research/allocation-reconciliation.md` (allocation lifecycle and exception types).

## How to read this document

Each KPI is labeled with a type tag:

- `process` - measures whether a workflow step was executed on time and to standard. Lead indicator. Drives day-to-day store and field operations.
- `performance` - measures the commercial or operational outcome (sales, conversion, sell-through, traffic, labor productivity). Lag indicator. Driven by upstream `process` quality.
- `risk` - measures the likelihood or severity of an operational failure: exceptions, SLA breaches, stockouts, shrink, compliance gaps. Lead indicator for control tower action.

A well-balanced scorecard uses all three types. `process` tells you what to fix this week, `performance` tells you whether fixing it moved the business, `risk` tells you what to watch before it breaks.

## Dashboard sections

The control tower is organized into six sections. Each section is a page or panel in the dashboard, and each section has a defined primary user.

| # | Section | Primary user | Cadence | Primary KPI type mix |
|---|---------|--------------|---------|----------------------|
| 1 | Executive KPI tiles | COO, VP Operations, HQ leadership | Daily glance, weekly review | process + performance |
| 2 | Area Manager breakdowns | Regional / Area Managers | Daily stand-up, weekly | process + risk |
| 3 | Store status table | Area Managers, Store Managers | Daily | process + risk |
| 4 | Campaign performance view | Trade Marketing, HQ campaign owners | Daily during campaign, weekly | process + performance |
| 5 | Exception backlog view | Ops Control Tower team, Area Managers | Continuous (real-time) | risk |
| 6 | SLA / aging view | Ops Control Tower team, support owners | Continuous (real-time) | risk |

The hierarchy is executive (1) drills down to regional (2) drills down to store (3), while campaign (4), exception (5), and SLA (6) cut across all geographies and are organized by workflow rather than org level. This mirrors the pattern in published retail KPI architecture guides where the executive view shows outcomes against plan, the functional view shows drivers by area, and the store view shows execution-level detail (Umbrex KPI dashboard playbook; ClicData retail dashboards).

## Section 1: Executive KPI tiles

The executive tiles are the top of the system. They show network-wide performance against plan, prior period, and trend. The goal is fewer than ten tiles, each one a number an executive can defend in a sentence.

### Tile design principles

- One number per tile, with a trend arrow and a small sparkline.
- Color coded against threshold, not against gut feel. Green means on plan. Amber means within tolerance. Red means action required this week.
- Tile must support a one-click drill-down to the area, region, or store that drove the change.
- Tiles should reconcile with the other five sections. If the executive tile for "campaign compliance %" says 87% and the campaign view says 81%, the dashboard loses credibility (Umbrex, single source of truth principle).

### Candidate tiles (mapped to KPIs in the candidate table below)

1. **Network Compliance %** - composite of planogram, POSM, and pricing compliance, weighted.
2. **On-Shelf Availability (OSA) %** - share of campaign SKUs physically on the shelf at audit time.
3. **Active Exceptions** - open exception count, with red/amber breakdown.
4. **SLA Met %** - share of open work items (visits, audits, corrective actions) resolved within target.
5. **Campaign Coverage %** - planned vs. completed store visits for all active campaigns.
6. **Sales vs. Target %** - period sales as a share of plan (for portfolio use: same-store simulated sales).
7. **Stockout Risk Items** - count of SKUs below weeks-of-cover threshold.
8. **MTTR Hours** - mean time to resolve for corrective actions in the last 7 days.

## Section 2: Area Manager breakdowns

The area manager view rolls the same executive metrics up by region or territory. It exists to answer two questions: where is the network off plan, and which areas need the manager's attention first.

### Layout

- One row per region. Columns: the same eight executive metrics, computed for that region only.
- Heatmap coloring on the worst column: the regional ranking by composite health score appears at the top so the manager sees the trouble spots first.
- Drill-through from a regional cell to a store status table filtered to that region.
- Comparative columns: "vs. last week", "vs. plan", "rank within network".

### Regional dimensions to expose

- Compliance % by area, with breakdown by sub-component (planogram, POSM, pricing).
- Coverage % by area, with breakdown by campaign and visit status.
- Exception count by severity (critical, watch, info) by area.
- MTTR and SLA breach rate by area.
- Sales vs. target by area (or simulated same-store sales by area for the portfolio).
- Stockout risk items count by area, sorted by weeks of cover.

This pattern follows the regional/territory dashboard pattern documented in Salesforce Consumer Goods Cloud Territory & Store Performance and in BigPlus regional rollups, where group views and single-store views are both one click away.

## Section 3: Store status table

The store status table is the most operational view. It is a sortable, filterable grid - one row per store - that an area manager scans daily.

### Required columns

- Store ID, store name, region, format (flagship, standard, kiosk, drive-thru).
- **Store health** (composite score 0-100, derived from the process and risk KPIs).
- **Status** (green / amber / red), computed from the store health score against threshold.
- Last visit date, last audit date, days since last audit.
- Last audit compliance % (L1, L2, L3 separately).
- OSA % at last audit.
- Open exception count (critical / watch / info).
- Open corrective action count, with oldest age in days.
- Aging bucket for the oldest open item (0-5, 6-15, 16-30, 30+ days).
- Active campaign count, and coverage % across active campaigns.
- Last sync / last data refresh timestamp (so the user trusts the data is fresh).

### Interaction patterns

- Sort by any column, with sensible defaults (red stores first, then by oldest open exception).
- Filter by region, format, area manager, campaign, status.
- Click store ID to open a single-store deep-dive page (out of scope for MVP, but the link must exist).
- Bulk action: select stores and assign to a wave, a campaign, or an escalation owner.

The column set draws on the ITSM-style aged backlog dashboards (BMC Helix, ServiceNow, Genesys), which use aging buckets and SLA status side by side, and on the store-level scorecard pattern in Moonstar's KPI guide.

## Section 4: Campaign performance view

The campaign view tracks a single campaign end-to-end: which stores are in scope, how many have been visited, what the audit outcomes are, and what the sales lift looks like. The campaign execution research in `retail-campaign-execution.md` defines the workflow this view is measuring.

### Layout

- Campaign selector at the top, defaulting to active campaigns sorted by end date.
- Campaign header: campaign name, type, start/end, store count, days remaining, HQ owner.
- Tiles for the campaign: coverage %, compliance %, OSA %, exception count, sell-through vs. forecast.
- Region-level breakdown table (similar to area manager view, but campaign-scoped).
- Store-level table for the campaign: store, visit status, audit level, audit status, compliance score, exception flag, last photo timestamp.
- Exception drill-down: list of stores with open campaign-related exceptions, with corrective action status.

### Candidate KPIs

- **Campaign coverage %** - visited stores / planned stores for the campaign.
- **Campaign compliance %** - stores passing L2 audit / stores audited.
- **On-launch activation %** - stores that executed the campaign within the launch window.
- **POSM compliance %** - stores with all required POSM materials deployed and verified.
- **Campaign sell-through %** - units sold / units received during the campaign window.
- **Training completion %** - share of assigned store staff who completed pre-launch training.
- **Pricing accuracy %** - share of audited stores where promotional price matches the offer.

This view mirrors the campaign view in Oracle Retail Insights and the active-campaigns report described in ClicData's marketing campaign performance dashboard, with execution metrics (coverage, compliance, OSA) layered on top of the standard commercial metrics (CTR, redemption, sales lift).

## Section 5: Exception backlog view

The exception backlog is the heart of the control tower. Every reconciliation event (planned vs. shipped, shipped vs. received, received vs. sold, audit fail, SLA miss) raises an exception. The backlog view exists to ensure no exception sits in the queue past its deadline.

### Layout

- Stack-ranked list of open exceptions, sorted by severity then age.
- Filter bar: severity, owner, exception type, region, campaign, store, date raised.
- Aging buckets at the top: 0-5 days, 6-15 days, 16-30 days, 30+ days, with a count and % in each.
- Per row: exception ID, type, store, campaign (if any), severity, owner, age in days, deadline, SLA status (within / approaching / breached / paused), last update, link to source record.
- Side panel: trend chart of new vs. resolved exceptions over the last 30 days, broken out by severity.

### Aging bucket rationale

The 0-5 / 6-15 / 16-30 / 30+ bucket structure is the same one used in ITSM aged backlog dashboards (BMC Helix Incident Aged Backlog Analysis, ServiceNow incident aging, Genesys Task Age). The bucket boundaries match common SLA cadences in retail operations: 5 days for an in-week fix, 15 days for a campaign-window fix, 30 days for a quarter-window fix, beyond 30 days for chronic issues that need escalation.

### Candidate KPIs

- **Open exception count** - total open exceptions, broken out by severity.
- **Aged exception count** - exceptions older than 30 days.
- **New vs. resolved trend** - daily inflow vs. outflow.
- **Exception reopen rate** - share of resolved exceptions that were reopened within 7 days.
- **Critical exception MTTR** - mean time to resolve for critical-severity exceptions.

## Section 6: SLA / aging view

The SLA / aging view is closely related to the exception backlog but is organized around service levels and time-based performance rather than individual records. It answers the question: are we meeting our commitments, and where is the queue growing?

### Layout

- Tiles at the top: SLA Met %, SLA Breach %, MTTR (hours), MTTD (hours), Avg Active Age (days).
- SLA breakdown by work item type: visits, audits, corrective actions, exceptions, escalations.
- SLA breakdown by priority: critical, high, medium, low.
- Trend chart: SLA Met % and MTTR over the last 12 weeks, with the SLA target line.
- Per-owner table: owner, items open, items within SLA, items approaching SLA, items breached, average age.
- Aging distribution chart: bar chart of open items by aging bucket (0-5, 6-15, 16-30, 30+ days), per work item type.

### Candidate KPIs

- **SLA Met %** - share of closed work items that resolved within target.
- **SLA Breach %** - share of closed work items that missed target.
- **MTTR (hours)** - mean time to resolve for closed items in the period.
- **MTTD (hours)** - mean time to detect from anomaly occurrence to exception raised.
- **Average active age (days)** - average age of all open items.
- **SLA pause rate** - share of items with paused SLA clocks (e.g., awaiting customer or vendor input).
- **Reopen rate** - share of resolved items reopened within 7 days.

The layout and metric set mirror the major-incident delivery performance dashboard in Digital.ai and the SLA performance tab in ServiceNow Account 360, adapted from ITSM into a retail-ops context.

## Candidate KPI catalog (18 KPIs)

The catalog below lists 18 candidate KPIs, each tagged with type, owner, source data, threshold guidance, and which dashboard sections use it. The acceptance criterion is at least 15 candidate KPIs; the table provides 18 to give downstream tasks room to select.

| # | KPI | Type | Owner | Source data | Threshold guidance | Sections |
|---|-----|------|-------|-------------|---------------------|----------|
| 1 | Network Compliance % (composite) | process | VP Operations | L1/L2/L3 audit results | Green >= 90, Amber 80-90, Red < 80 | 1, 2, 3 |
| 2 | Planogram Compliance % | process | Merchandising | L1 audit, planogram file | Green >= 95, Amber 85-95, Red < 85 | 1, 2, 3, 4 |
| 3 | POSM Compliance % | process | Trade Marketing | L1/L2 audit, POSM list | Green >= 95, Amber 85-95, Red < 85 | 1, 2, 3, 4 |
| 4 | Pricing Accuracy % | process | Trade Marketing | L1 audit, price file | Green >= 98, Amber 95-98, Red < 95 | 1, 2, 3, 4 |
| 5 | On-Shelf Availability (OSA) % | process | Replenishment | L1/L2 audit, SKU catalog | Green >= 95, Amber 90-95, Red < 90 | 1, 2, 3, 4 |
| 6 | Out-of-Stock (OOS) Rate | risk | Replenishment | L1 audit, SKU catalog | Green <= 5, Amber 5-10, Red > 10 | 1, 2, 3 |
| 7 | Stockout Risk Items Count | risk | Replenishment | WSSI, weeks-of-cover | Green = 0, Amber 1-5, Red > 5 | 1, 2 |
| 8 | Campaign Coverage % | process | Trade Marketing | Visit tracker, campaign scope | Green >= 95, Amber 85-95, Red < 85 | 1, 2, 3, 4 |
| 9 | On-Launch Activation % | process | Trade Marketing | Visit tracker, campaign dates | Green >= 90 within launch window, Amber 75-90, Red < 75 | 4 |
| 10 | Campaign Compliance % | process | Trade Marketing | L2 audit results, campaign store list | Green >= 90, Amber 80-90, Red < 80 | 1, 2, 4 |
| 11 | Training Completion % | process | L&D / Operations | Training records | Green >= 95, Amber 85-95, Red < 85 | 3, 4 |
| 12 | Sales vs. Target % (simulated same-store) | performance | COO | POS, store targets | Green >= 100, Amber 95-100, Red < 95 | 1, 2 |
| 13 | Conversion Rate | performance | Store Manager | Traffic counter, POS | Trend-based; flag > 100 bps drop WoW | 1, 2, 3 |
| 14 | Average Transaction Value (ATV) | performance | Store Manager | POS | Trend-based; flag > 5% drop WoW | 1, 2, 3 |
| 15 | Open Exception Count | risk | Control Tower | Exception log | Green <= 50, Amber 50-150, Red > 150 | 1, 2, 5 |
| 16 | Aged Exception Count (30+ days) | risk | Control Tower | Exception log | Green = 0, Amber 1-5, Red > 5 | 1, 2, 5 |
| 17 | MTTR (hours) | risk | Control Tower owner | Corrective action log | Green <= 24, Amber 24-72, Red > 72 | 1, 2, 5, 6 |
| 18 | SLA Met % | risk | Control Tower owner | Work item log | Green >= 90, Amber 80-90, Red < 80 | 1, 2, 5, 6 |

### KPI type distribution

- `process`: 9 KPIs (#1-5, 8-11) - execution and quality metrics.
- `performance`: 3 KPIs (#12-14) - commercial outcome metrics.
- `risk`: 6 KPIs (#6, 7, 15-18) - control tower and operational risk metrics.

### Cross-section KPI mapping

The 18 KPIs map across the six sections as follows. A single KPI can appear in multiple sections, which is the point: a metric is computed once and rolled up to wherever it is consumed (single source of truth principle).

| KPI | Section 1 (Tiles) | Section 2 (Area Mgr) | Section 3 (Store) | Section 4 (Campaign) | Section 5 (Exceptions) | Section 6 (SLA) |
|-----|-------------------|---------------------|-------------------|----------------------|------------------------|-----------------|
| 1 Network Compliance % | x | x | x | . | . | . |
| 2 Planogram Compliance % | . | x | x | x | . | . |
| 3 POSM Compliance % | . | x | x | x | . | . |
| 4 Pricing Accuracy % | . | x | x | x | . | . |
| 5 OSA % | x | x | x | x | . | . |
| 6 OOS Rate | . | x | x | . | . | . |
| 7 Stockout Risk Items | x | x | . | . | . | . |
| 8 Campaign Coverage % | x | x | x | x | . | . |
| 9 On-Launch Activation % | . | . | . | x | . | . |
| 10 Campaign Compliance % | x | x | . | x | . | . |
| 11 Training Completion % | . | . | x | x | . | . |
| 12 Sales vs. Target | x | x | . | . | . | . |
| 13 Conversion Rate | x | x | x | . | . | . |
| 14 ATV | x | x | x | . | . | . |
| 15 Open Exception Count | x | x | . | . | x | . |
| 16 Aged Exception Count | x | x | . | . | x | . |
| 17 MTTR | x | x | . | . | x | x |
| 18 SLA Met % | x | x | . | . | x | x |

## MVP recommendation: 10 KPIs to ship first

The MVP must be useful on day one but small enough to build, test, and validate. The recommendation is ten KPIs, biased toward `process` and `risk` because those are the ones the simulated data can reliably produce from the campaign and allocation trackers already specified in `retail-campaign-execution.md` and `allocation-reconciliation.md`.

### Selected MVP KPIs

| # | KPI | Type | Why this one |
|---|-----|------|--------------|
| 1 | Network Compliance % (composite) | process | Headline executive metric. Combines the three execution pillars in one number. Computed from L2 audit results. |
| 2 | On-Shelf Availability (OSA) % | process | Strongest documented link between execution and sales. Both research files cite it. Computed from L1 audit results against the campaign SKU list. |
| 3 | Campaign Coverage % | process | Visits completed vs. planned for the active campaign window. Most actionable field metric. Drives the "where do we send the rep today" decision. |
| 4 | Campaign Compliance % | process | L2 audit pass rate at the campaign level. The "did the campaign actually happen correctly" question. |
| 5 | On-Launch Activation % | process | Share of stores that executed within the launch window. Late launch is a structural failure, and this is the metric that catches it. |
| 6 | Stockout Risk Items Count | risk | Weeks-of-cover below threshold. One of the two polar risk signals in allocation. Prevents lost sales during the campaign window. |
| 7 | Open Exception Count | risk | Total open exceptions. The control tower's "how much work is in the queue" headline. |
| 8 | Aged Exception Count (30+ days) | risk | Share of open exceptions that are chronic. The single best signal of a broken process - if exceptions are aging past 30 days, the corrective action workflow is not closing. |
| 9 | MTTR (hours) | risk | Mean time to resolve for corrective actions. The control tower's "how fast do we close the loop" headline. |
| 10 | SLA Met % | risk | Share of work items resolved within target. The headline for the SLA/aging view. |

### What is in and what is out for MVP

**In (10 KPIs):** 5 `process` (network compliance, OSA, campaign coverage, campaign compliance, on-launch activation), 0 `performance` (commercial outcome), 5 `risk` (stockout risk, open exception count, aged exception count, MTTR, SLA met %).

**Out for MVP but planned for v2:**

- **Sales vs. Target, Conversion, ATV** (`performance`). The portfolio project uses simulated sales data, but for an MVP focused on ops control, the commercial outcomes are a second-layer view. They depend on a POS data source that the MVP scope does not require. v2 should add these once the ops data is validated.
- **Planogram Compliance, POSM Compliance, Pricing Accuracy** (sub-components of Network Compliance %). In the MVP, these are rolled up into the composite. v2 should expose them as separate tiles and as columns in the area manager view.
- **OOS Rate, Training Completion %**. Useful but secondary. OOS rate is a different framing of OSA. Training completion is well-served by the existing campaign execution tracker, but exposing it as a standalone tile is a v2 job.
- **Exception Reopen Rate, MTTD, SLA Pause Rate**. v2 view refinements once the SLA view is being used daily.

### Why this MVP set is the right starting point

1. **It is computable from the existing trackers.** All ten KPIs are derived from the campaign execution tracker, the allocation tracker, the audit log, and the corrective action log - all four of which are already defined in the upstream research files. No new data sources needed.
2. **It is balanced across the three types.** 5 process, 0 performance, 5 risk. Performance is intentionally deferred to v2 so the MVP stays focused on the control-tower value proposition: catching execution gaps and closing them fast.
3. **It covers all six dashboard sections.** Each section has at least one MVP KPI: tiles (1, 2, 6, 7, 9, 10), area manager (1, 2, 3, 4, 6, 7, 8, 9, 10), store (1, 2, 3, 4, 5), campaign (2, 3, 4, 5), exception (7, 8, 9), SLA (9, 10).
4. **It is small enough to test.** Ten KPIs means ten threshold tables, ten definitions to validate, ten mock datasets to build. That fits the smoke-test budget for the MVP.
5. **It tells a coherent operational story.** Each KPI answers a question an ops leader actually asks. The composite compliance % answers "are we executing". The OSA % answers "is the product on the shelf". The campaign coverage % answers "did the field team visit the stores". The activation % answers "did it launch on time". The stockout risk count answers "what is about to break". The exception, aged exception, MTTR, and SLA met % together answer "are we closing the loop". And the network compliance % rolls it all up.

### MVP threshold defaults (proposed)

The portfolio project uses simulated data, but the threshold logic must be defined up front so the dashboard behaves consistently.

| KPI | Green | Amber | Red |
|-----|-------|-------|-----|
| Network Compliance % | >= 90 | 80-90 | < 80 |
| OSA % | >= 95 | 90-95 | < 90 |
| Campaign Coverage % | >= 95 | 85-95 | < 85 |
| Campaign Compliance % | >= 90 | 80-90 | < 80 |
| On-Launch Activation % | >= 90 (within launch window) | 75-90 | < 75 |
| Stockout Risk Items | 0 | 1-5 | > 5 |
| Open Exception Count | <= 50 | 50-150 | > 150 |
| Aged Exception Count (30+ days) | 0 | 1-5 | > 5 |
| MTTR (hours) | <= 24 | 24-72 | > 72 |
| SLA Met % | >= 90 | 80-90 | < 80 |

These are starting defaults. They should be reviewed and tuned against the first 4-8 weeks of simulated data before being treated as authoritative.

## Modeling notes for downstream tasks

### What the simulated data must support

- Per-store, per-campaign audit results with compliance score (0-100) and audit level (L1/L2/L3).
- Per-store, per-campaign visit timestamps and statuses (planned, in_progress, completed, missed, bypassed).
- Per-SKU, per-store on-shelf availability flags from L1 audits.
- Weeks-of-cover per SKU per store from the allocation tracker.
- Exception records with severity, owner, age, deadline, and SLA status.
- Corrective action records with open/close timestamps for MTTR.
- Aging buckets computed from the current date minus the exception raise date.

### Safe to simulate (consistent with the upstream research files)

- All KPIs above can be computed from the simulated data in `retail-campaign-execution.md` and `allocation-reconciliation.md`. No new data structures are required.
- Threshold values can be hard-coded in the dashboard layer; no external lookup needed.
- Aging buckets can be computed at render time. No need to persist them.

### Do not claim

- Real company KPIs, real threshold values, or real SLA performance from any retailer.
- That the threshold defaults above are industry standards; they are reasonable starting points for a simulated portfolio, not benchmarks.
- That the MVP KPI set is exhaustive. It is a starting point that the v2 expansion above will extend.

## Source notes

All sources are public web pages accessed on 2026-07-03. URLs are provided for verification.

1. Umbrex - "Retail KPI Architecture and Metric Definitions" - https://umbrex.com/resources/retail-industry-playbooks/retail-kpi-dashboard-weekly-business-review-playbook/retail-kpi-architecture-and-metric-definitions/
   - Three-level KPI architecture: executive outcome metrics, driver metrics, diagnostic metrics. KPI tree principle: each metric should either measure an outcome, explain a driver, or trigger a management action. Distinction between commercial, inventory, merchandising, store operations, labor, customer, and digital metrics.

2. Umbrex - "Designing the Retail KPI Dashboard" - https://umbrex.com/resources/retail-industry-playbooks/retail-kpi-dashboard-weekly-business-review-playbook/designing-the-retail-kpi-dashboard/
   - Dashboard design principles. Executive view, functional view, store view, category view. Single source of truth requirement. Threshold definition as a governance requirement. Recommendation: 5-6 core KPIs on a single dashboard with drill-down for depth.

3. SysGenPro - "Retail ERP Reporting Frameworks for Better Inventory Decisions and Store Operations" - https://sysgenpro.com/industries/retail-erp-reporting-frameworks-for-better-inventory-decisions-and-store-operations
   - Operational control tower concept: detects exceptions, prioritizes actions, coordinates responses. Recommended starting KPI set: inventory accuracy, stockout rate, OSA, sell-through, replenishment exception rate, transfer cycle time, supplier OTIF, shrink variance, gross margin impact.

4. OMSPro - "Resources Retail Control Tower" - https://omspropro.com/pages/resources-retail-control-tower (URL as returned by search)
   - Control tower five functional pillars. Cadence definitions: continuous real-time, daily stand-up, weekly review, campaign war room, strategic review. Operational KPIs: MTTD, MTTR, stockout duration reduction, oversell rate, forecast accuracy. Strategic KPIs: inventory turns, contribution margin %, revenue per SKU per channel, customer satisfaction.

5. ThoughtSpot - "Retail KPIs: 10 Key Metrics For Retail Benchmarking" - https://www.thoughtspot.com/data-trends/analytics/retail-kpis-and-metrics
   - Dashboard design principle: group KPIs by category, use KPI tiles with time comparisons, keep it scannable. 5-6 core KPIs per dashboard with drill-down for depth.

6. EasyCheck - "Top 7 Retail Execution KPIs You Should Be Tracking" - https://easycheck.io/resources/blog/top-7-retail-execution-kpis-you-should-be-tracking/
   - Seven execution KPIs: On-Shelf Availability, Planogram Compliance, POS Material Compliance, Execution Score by Rep or Route, Time to Resolve Field Issues, Promo Compliance Rate, Store Coverage Rate.

7. Amply - "Retail Operations KPIs: For Store Managers & Most Important" - https://www.getamply.co/blog/retail-store-operation-efficiency-metrics-kpi/
   - Combination of conversion rate, OSA, and planogram compliance score as the clearest operational efficiency signal. Five store-manager KPIs: conversion rate, planogram compliance, OSA, units per transaction, sales per employee. Distinction between lag and lead KPIs.

8. VisionGroup - "Retail Audit: What It Is, How to Run One" - https://visiongroupretail.com/blog/retail-audit-execution-guide
   - Five audit categories: on-shelf availability, planogram compliance, pricing accuracy, promotional execution, competitive intelligence. Digital audit programs: 90-second gap list delivery. Image recognition reads brand, SKU, facing count, shelf height, price tag, POSM presence.

9. Pazo (Gopazo) - "Retail Audit Checklist: 40+ Advanced Metrics for Perfect Store Execution" - https://www.gopazo.com/blog/retail-audit-checklist
   - Audit checklist categories: product availability, backroom inventory, damaged products, shelf tags, planogram compliance, shelf positioning, product blocking, location accuracy, promotional metrics, competitive intelligence, stock availability and replenishment. Mobile-first apps, image recognition, dashboards, automated alerts.

10. GoodsChecker - "Merchandising KPIs: Metrics That Truly Drive Retail Performance" - https://goodschecker.com/blog/merchandising-kpis/
    - Highest-priority merchandising KPIs: OSA, OOS rate, planogram compliance, share of shelf, sales per facing or per linear meter. Three-level hierarchy: executive (outcomes), management (execution), field (per-visit). NielsenIQ-cited link between planogram compliance and sell-out.

11. ClicData - "Retail Store Performance: 3 Must-Have Dashboards" - https://www.clicdata.com/blog/retail-store-performance-dashboard-examples-and-kpis/
    - Three core dashboards: store revenue performance, customer engagement, marketing campaign performance. Sales against target, sales variance, ATV, inventory turnover, sales per square foot. Campaign metrics: CTR, conversion, foot traffic, coupon redemption, local sales lift, ROI.

12. Moonstar - "Retail Performance Dashboard: The 10 KPIs Every Store Manager Should Track" - https://moonstar.ai/retail-performance-dashboard-10-kpis-store-manager/
    - Ten KPIs: sales vs. target, conversion, ATV, units per transaction, attachment rate, sales per labor hour, stock availability, promotional execution, customer feedback, coaching follow-through. Lag vs. lead KPI distinction. Weekly manager rhythm.

13. IBM - "Manager Dashboard" - https://www.ibm.com/docs/en/store-engagement?topic=overview-manager-dashboard
    - Store manager dashboard pattern: order status and SLA charts, BOPIS and ship-from-store fulfillment, total orders, orders by status, orders by SLA priority. Real-time store-level consolidated view.

14. Oracle Retail Insights Cloud - "Predefined Retail Insights Reports" - https://docs.oracle.com/en/industries/retail/retail-insights-cloud/23.1.101.0/rinug/predefined-retail-insights-reports.htm
    - Dashboard, Sales Performance, Inventory Aging, Promotion and Clearance (Active Campaigns, Backorders), Stores Dashboards (store/day KPIs). Aging inventory, markdowns, liquidation candidates. Store-level performance review with location filters.

15. BMC Helix ITSM - "Incident Aged Backlog Analysis Dashboard" - https://docs.bmc.com/xwiki/bin/view/Helix-Common-Services/Dashboards-Reports/BMC-Helix-Dashboards/BHD234/Viewing-out-of-the-box-dashboards/BMC-Helix-ITSM-dashboards/BMC-Helix-ITSM-Incident-Aged-Backlog-Analysis-dashboard/
    - Aging buckets 0-5, 6-15, 16-30, 30+ days. SLA status color coding: red breached, orange approaching, green ongoing, blue paused. Average age of incidents (days). Open incident aging by priority, by assigned group.

16. ServiceNow - "Account 360 Analytics Dashboard" - https://github.com/ServiceNow/ServiceNowDocs/blob/australia/markdown/proactive-service-exp-workflows/product-support-for-technology/account-360-analytics-dashboard.md
    - SLA performance tab: team overdue SLAs, team SLAs expiring today, team average SLAs age, overall SLA analysis achieved, SLAs expiring today, overall SLA analysis breached. Service management tab: incident reopen rate, average reassignment count, average active case age.

17. Digital.ai - "Major Incident Delivery Performance Dashboard" - https://infosys.intelligence.digital.ai/Web/Help/MSTRWeb/WebHelp/Lang_1033/r-smpo-mi-inc-delv-perf.htm
    - Metrics: MTTR (hours), Avg. Handle Time, Major Incident SLA %, Minor Incident SLA %. Group and individual incident performance. Composite opportunity rank combining incident count, SLA, MTTR, handle time.

18. Genesys - "Task Age Dashboard" - https://all.docs.genesys.com/PEC-REP/Current/RPRT/HRCXIiWDTskAgeDshbrd
    - Task age by department and process. Aging analysis: finished, pending pre-SLA, pending overdue, pending. Aging range granularity 15 min, 1 hour, 1 day.

19. ShelfMind - "Retail and Planogram Intelligence Platform" - https://shelfmind.io/solutions/retail-leadership
    - Fleet-wide compliance, drill-down to region, identify chronic problem stores. Compliance and revenue lift tracked over time. Measure ROI of training and operational resets.

20. Salesforce Consumer Goods Cloud - "Maximize Territory & Store Performance Insights" - https://trailhead.salesforce.com/content/learn/modules/tableau-crm-dashboards-for-consumer-goods-cloud/evaluate-insights-on-territory-and-store-performance
    - Sales Manager dashboards: Home, Territory Performance, Store Performance (Performance + Correlation views). Compare stores, change in performance, trend. Correlate out-of-stock compliance with revenue. Drill from region to store to visit history.

21. BigPlus - "Real Time Retail Reporting & Dashboards" - https://bigplushq.com/reporting/
    - Live dashboards across sales, stock, customers. Group all locations into one live view, drill into single store, region, or category. FIFO-tracked inventory. Low-stock and overstock alerts. Hour x weekday heatmap. Role-based permissions for regional managers.

22. Scoop Analytics - "Scaling Your Best Regional Manager's Judgment to Every Store, Every Week" - https://www.scoopanalytics.com/blog/scaling-retail-district-manager-expertise
    - District manager judgment pattern: mid-tier stores quietly drifting, store manager instincts vs. data, patterns only visible across region, early warnings. Store-level diagnosis, district and regional rollups, weekly executive briefings.
