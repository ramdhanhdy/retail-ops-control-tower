# Exception Management and SLA Workflow

> Scope: Define exception categories, severity scoring, SLA aging, and daily action-list logic for the retail operations control tower. Synthesized from upstream research (`ops-kpi-scorecard.md`, `allocation-reconciliation.md`, `retail-campaign-execution.md`) and public retail execution/ITSM aging frameworks. All data in the downstream portfolio project will be simulated.
>
> Related research: `docs/research/ops-kpi-scorecard.md` (dashboard sections 5-6, aging buckets), `docs/research/allocation-reconciliation.md` (24 exception rules, failure modes), `docs/research/retail-campaign-execution.md` (campaign execution workflow, audit levels).

## How to read this document

This document provides the complete exception management model for the control tower. It defines:

- An 8-category exception taxonomy that maps to the control-tower backlog.
- A 3-tier severity model with transparent scoring logic.
- SLA aging rules with four aging buckets.
- A daily action-list generation algorithm that uses the priority formula to rank what the team handles today.
- Escalation and close-out workflows for exceptions that age past their deadline.

## Exception taxonomy

The control tower surfaces eight exception types. Each type is a distinct operational failure mode with a defined trigger condition, default owner, and SLA window.

| # | Exception type | Description | Trigger condition (when raised) | Default owner |
|---|---------------|-------------|--------------------------------|---------------|
| 1 | Missing confirmation | Planned action was executed but no confirmation record exists within the expected window | Visit completed but no system confirmation posted within 4 hours of visit close | Field Operations |
| 2 | Quantity mismatch | Actual units received, sold, or on-hand deviate from the planned/shipped/receivedQuantity variance exceeds tolerance band (see severity table below) | DC Operations or Store Manager (depending on direction) |
| 3 | Missing photo proof | Execution task completed in the system but the mandatory photo proof record is missing or fails validation | Visit status = completed AND (photo_proof_url IS NULL OR photo_validation = failed) | Field Representative |
| 4 | late setup | Campaign or POSM setup was not completed before the launch deadline | campaign_start_date passed AND campaign_store_status != completed | Store Manager |
| 5 | Stockout risk | Weeks of cover has dropped below the supplier lead time and a stockout is imminent | WOC < supplier_lead_time_weeks | Replenishment Planner |
| 6 | Overstock risk | Weeks of cover has risen above the overstock threshold and markdown pressure is building | WOC > 2 x lead_time_weeks OR WOC > remaining_selling_window_weeks | Merchant |
| 7 | Low sell-through | Units sold as a fraction of units received has fallen below the campaign/period target | units_sold / received_quantity < period_target x threshold | Merchant + Planner |
| 8 | Unresolved issue aging | An open exception has been unresolved beyond a defined aging threshold (typically the SLA window or a fixed aging band) | exception_open_days > max(SLA_window_days, aging_threshold_days) | Operations Lead (escalation) |

### Taxonomy mapping to upstream exception rules

The eight exception types consolidate the 24 granular exception rules from `allocation-reconciliation.md` into control-tower-facing categories. The mapping preserves the original rule codes so the control tower can drill down to the specific reconciliation event.

| Exception type | Upstream rule codes (allocation-reconciliation.md) | Source domain |
|---------------|---------------------------------------------------|---------------|
| Missing confirmation | EX-03 (receiving overage - info), EX-07 (substitution on receipt) | Allocation / Campaign |
| Quantity mismatch | EX-01, EX-02, EX-04, EX-05, EX-06, EX-16, EX-17, EX-18, EX-23 | Allocation |
| Missing photo proof | Campaign execution failure modes #4, #16 (pencil-whipping, photos without context) | Campaign execution |
| Late setup | EX-08, EX-09 (late shipment), Campaign failure mode #5 (late activation) | Allocation / Campaign |
| Stockout risk | EX-10 (stockout imminent), Alignment with KPI #7 (Stockout Risk Items) | Allocation |
| Overstock risk | EX-11, EX-12 (overstock signals), Alignment with KPI #6 (OOS Rate framing) | Allocation |
| Low sell-through | EX-13, EX-14, EX-15, EX-19 (plan vs actual miss) | Allocation |
| Unresolved issue aging | EX-21, EX-22 (exception overdue), EX-20 (exception reopened) | Allocation |

This mapping ensures the control tower's eight-category view can be traced back to the granular reconciliation rules already defined in the upstream research.

## Severity scoring

The control tower uses a three-tier severity model. Severity determines SLA window length, escalation path, and visualization color. The scoring is deterministic and explained below.

### Severity tiers

| Severity | Label | SLA window | Escalation path | Color |
|----------|-------|------------|-----------------|-------|
| 3 | Critical | 24 hours (same-day) | On-call manager paged, Operations Lead notified within 4 hours of breach | Red |
| 2 | Watch | 48-72 hours | Goes to daily action list, owner's manager notified on day 2 if still open | Amber |
| 1 | Info | 7-14 days | Logged for weekly review, no escalation unless it ages into Watch territory | Blue |

### How severity is assigned

Severity is assigned at exception raise time based on the **severity matrix** below. The matrix combines (a) exception type and (b) the magnitude of the deviation from target.

#### Severity matrix by exception type

| Exception type | Watch threshold | Critical threshold |
|---------------|-----------------|-------------------|
| Missing confirmation | Confirmation missing > 4 hours after visit close | Confirmation missing > 24 hours after visit close |
| Quantity mismatch | Variance within tolerance band (5-20% deviation from expected) | Variance exceeds critical band (>20% deviation from expected) |
| Missing photo proof | Photo missing but visit score is passing (< 90) | Photo missing and visit score is failing (< 80), or audit rejected for missing proof |
| Late setup | Setup incomplete 0-3 days after launch | Setup incomplete > 3 days after launch |
| Stockout risk | WOC between 0.5x and 1.0x of lead time | WOC < 0.5x of lead time (stockout days away) |
| Overstock risk | WOC > 2x lead time (early signal) | WOC > remaining selling window (markdown/clearance unavoidable) |
| Low sell-through | Sell-through < 70% of target (early watch) | Sell-through < 50% of target (critical miss) |
| Unresolved issue aging | Open past SLA window but < 7 days overdue | Open past SLA window and > 7 days overdue |

#### Severity formula (priority score)

The daily action list ranks exceptions by **priority score** (higher = handle first). The formula is:

```
priority_score = (severity_weight x 100) + age_pressure + business_impact + campaign_urgency
```

Where:

| Component | Weight | How computed |
|-----------|--------|-------------|
| severity_weight | 3, 2, or 1 | From severity tier: Critical = 3, Watch = 2, Info = 1 |
| age_pressure | 0-50 | (days_open / SLA_window_days) x 50. Capped at 50. Exceptions at 100% of their SLA window get full age pressure. |
| business_impact | 0-30 | Based on SKU/store criticality: hero SKU or flagship store = 30, standard SKU/store = 15, low-velocity/non-hero = 5 |
| campaign_urgency | 0-20 | 20 if the exception is linked to an active campaign within its launch window (first 7 days), 10 if linked to active campaign outside launch window, 0 if no campaign link |

**Range:** minimum 1 (severity 1, no age pressure, no impact, no campaign), maximum 200 (severity 3/50/30/20).

**Why this formula is transparent:**
- Each component is independently explainable: "this exception is critical (300), it's at 80% of its SLA window (+40), it's a hero SKU (+30), and it's in the first 7 days of a campaign (+20) = 390."
- No hidden weights: all coefficients are visible in the formula.
- Downstream systems can recompute the score from raw data without a model.
- Users can sort by any single component (e.g., "show me all Critical exceptions" or "show me the most overdue items") without losing the composite ranking.

#### Priority score worked examples

**Example 1: Critical stockout in launch window**
- Exception type: Stockout risk
- Severity: Critical (weight = 3)
- Days open: 1, SLA window: 1 day → age_pressure = (1/1) x 50 = 50
- SKU: Hero campaign SKU → business_impact = 30
- Campaign: Active, within launch window → campaign_urgency = 20
- **Priority score: 300 + 50 + 30 + 20 = 400**

**Example 2: Watch-level quantity mismatch, day 3**
- Exception type: Quantity mismatch
- Severity: Watch (weight = 2)
- Days open: 3, SLA window: 2 days → age_pressure = (3/2) x 50 = 75 → capped at 50
- SKU: Standard SKU → business_impact = 15
- Campaign: None → campaign_urgency = 0
- **Priority score: 200 + 50 + 15 + 0 = 265**

**Example 3: Info-level receiving variance, day 5**
- Exception type: Quantity mismatch
- Severity: Info (weight = 1)
- Days open: 5, SLA window: 7 days → age_pressure = (5/7) x 50 = 36
- SKU: Low-velocity SKU → business_impact = 5
- Campaign: None → campaign_urgency = 0
- **Priority score: 100 + 36 + 5 + 0 = 141**

**Example 4: Missing photo proof at a flagship store, day 2**
- Exception type: Missing photo proof
- Severity: Watch (weight = 2)
- Days open: 2, SLA window: 2 days (Watch threshold for missing photo) → age_pressure = 50
- Store: Flagship → business_impact = 30
- Campaign: Active, launch window → campaign_urgency = 20
- **Priority score: 200 + 50 + 30 + 20 = 300**

## SLA aging rules

The control tower tracks exception age in four aging buckets. The bucket boundaries are aligned with ITSM aging dashboards (BMC Helix, ServiceNow) documented in the upstream KPI scorecard.

### Aging buckets

| Bucket | Age range | Meaning | Count KPI |
|--------|-----------|---------|-----------|
| 0 | 0-5 days | Fresh: within normal SLA window | Open exceptions (recent) |
| 1 | 6-15 days | Aging: approaching or at SLA limit | Open exceptions (aging) |
| 2 | 16-30 days | Overdue: SLA breached, escalation active | Open exceptions (overdue) |
| 3 | 30+ days | Chronic: broken workflow, needs root-cause intervention | Aged exceptions (30+ days) |

### SLA window by severity

| Severity | SLA window | SLA clock start | SLA clock stop |
|----------|------------|-----------------|----------------|
| Critical | 24 hours | Exception raised | Exception resolved, closed, or waived |
| Watch | 48 hours (default) or 72 hours (Investigate-type) | Exception raised | Exception resolved, closed, or waived |
| Info | 7 days (default) or 14 days (investigation-type) | Exception raised | Exception resolved, closed, or waived |

### SLA pause rules

The SLA clock pauses (stops counting) in the following conditions. Pausing prevents penalizing the team when the blocker is outside their control.

| Pause condition | When applied | Max pause duration |
|----------------|--------------|--------------------|
| Awaiting vendor confirmation | Owner posts "waiting for vendor" status with a ticket/reference number | 72 hours, then auto-resumes with alert to owner's manager |
| Awaiting store response | Owner posts "waiting for store" status with a reference number | 48 hours, then auto-resumes with alert to store manager |
| System outage | Confirmed system outage affecting the exception workflow | Duration of outage + 4 hours, then auto-resumes |
| Customer/goods in transit | Goods are physically in transit and delay is confirmed by tracking | Estimated arrival + 24 hours |

### SLA status indicators

Each open exception displays one of four SLA status colors in the control tower:

| SLA status | Condition | Color | Action required |
|------------|-----------|-------|-----------------|
| Within | days_open < 60% of SLA_window | Green | None - track |
| Approaching | 60% <= days_open < 100% of SLA_window | Orange | Owner should prioritize |
| Breached | days_open > SLA_window and severity is Watch or Critical | Red | Escalation workflow activates |
| Paused | SLA clock is paused per pause rules | Gray | Review pause reason for staleness |

### Aging-triggered auto-escalation

The aging system auto-promotes exceptions as they age. Auto-promotion does not wait for the owner to act.

| Trigger | Action |
|---------|--------|
| Any Watch exception open > 48 hours | Auto-escalate to owner's manager, severity promoted to Watch-High (no SLA change but flagged in daily brief) |
| Any exception crosses into 6-15 day bucket | Re-assigned to Operations Lead, owner retains accountability |
| Any exception crosses into 16-30 day bucket | Re-assigned to Operations Lead + Regional Manager, root-cause tag required |
| Any exception crosses into 30+ day bucket | Re-assigned to VP Operations, root-cause tag and corrective action plan required within 7 days or exception is escalated to executive dashboard |

## Daily action list

The daily action list is the control tower's primary work queue. It is recomputed at the start of each day (and available on-demand) using the priority formula to rank what the team handles today.

### Action list generation algorithm

```
FOR each open exception:
    compute priority_score using the formula above
    compute SLA status (Within / Approaching / Breached / Paused)
    
FILTER exceptions where:
    SLA status != Paused   (paused items go to a separate review queue)
    AND severity >= 1      (all non-archived exceptions)
    AND exception_status in (open, in_progress)

SORT by:
    1. priority_score DESC   (highest urgency first)
    2. age_in_days DESC       (oldest first within same score)
    3. exception_id ASC      (stable tiebreaker)

OUTPUT top N items (default N = 20) to the action list
```

### Action list fields

Each row on the daily action list displays the following fields:

| # | Field | Source / Computation |
|---|-------|----------------------|
| 1 | Rank | Position in sorted output (1 = highest priority today) |
| 2 | Exception ID | system-generated unique ID |
| 3 | Type | Exception type from taxonomy table above |
| 4 | Severity | Critical / Watch / Info |
| 5 | Priority score | Computed from formula (displayed for transparency) |
| 6 | Store | Store name + format |
| 7 | Region | Geographic region |
| 8 | Campaign (if any) | Campaign name + "launch window" tag if active within first 7 days |
| 9 | SKU / Product | Affected SKU + hero/non-hero badge |
| 10 | Owner | Assigned owner name + role |
| 11 | Age | Days open |
| 12 | SLA window | Target resolution window (hours or days) |
| 13 | SLA status | Within / Approaching / Breached |
| 14 | Deadline (computed) | Exception raised date + SLA window (accounts for pauses) |
| 15 | Last update | Date and type of last update (comment, status change, pause) |
| 16 | Root cause tag | Categorized root cause (if set) |
| 17 | Expected action | Codified next-step action (see action playbook below) |
| 18 | Controls | Buttons: update status, add comment, reassign, escalate, pause, resolve |

### Codified action playbook

Each exception type maps to a default set of expected actions. This codification ensures the action list tells the owner what to do, not just what is wrong.

| Exception type | Default expected action | If action not completed within SLA window |
|----------------|------------------------|------------------------------------------|
| Missing confirmation | Owner: locate the missing confirmation record or repost. If repost succeeds: resolve with "reposted" root cause. If not found: escalate to Field Ops. | Auto-escalate to Field Ops manager |
| Quantity mismatch | Owner: investigate source (DC short-pick, store miscount, damage, or system error). Document root cause and initiate resolution (replacement shipment, system adjustment, write-off). | Auto-promote severity to critical, escalate to shared owner (DC + Store) |
| Missing photo proof | Owner: repost compliant photo within 48 hours or document why photo is not available (system issue, access issue). Repost with compliant metadata: resolve. | If audit rejection: auto-corrective action to re-audit within 48 hours. If no repost after 72 hours: auto-escalate to Field Ops. |
| Late setup | Owner: complete setup immediately. Document root cause (materials delay, training gap, labor shortage). If setup blocked: document blocker and reassign to Logistics or L&D. | Auto-corrective action to visit store within 48 hours. Escalate to Regional Manager if campaign window closes before resolution. |
| Stockout risk | Owner: place emergency replenishment order OR initiate inter-store transfer. Document expected arrival date. Update exception with order/transfer ID. | If no order/transfer placed within 12 hours (Critical) or 24 hours (Watch): page Replenishment Manager + auto-escalate to VP if campaign-linked. |
| Overstock risk | Owner: initiate transfer, markdown, or return-to-vendor action. Document action taken and expected date. Update exception with resolution reference. | If no action within 7 days (Watch) or 3 days (Critical): escalate to Merchant Manager. |
| Low sell-through | Owner: diagnose root cause (wrong location, pricing gap, training gap, demand miss). Document chase/transfer/no-go decision. Link to allocation decision if chase or transfer approved. | If exception ages past 7 days without a documented decision: auto-promote to Planning Manager for allocation review. |
| Unresolved issue aging | Owner: document why exception is still open, what is blocking, and the new expected resolution date. If breach is legitimate: document waiver reason. If breach is not legitimate: resolve or re-escalate. | Auto-generated exception: if exception ages > 7 days past original SLA: auto-reassign to VP Operations. If > 14 days: flag on executive dashboard. |

### Action list views for different roles

The same priority-ranked list is filtered differently for each control-tower role:

| Role | Filter | Focus |
|------|--------|-------|
| Control Tower Operator | All regions, all exception types | Network-wide triage |
| Regional Manager | Region = assigned region, severity >= Watch | Regional accountability |
| Store Manager | Store = assigned store | Store-specific action |
| Field Operations Lead | Type in (Missing confirmation, Missing photo proof, Late setup) | Field execution gaps |
| Replenishment Planner | Type in (Stockout risk, Overstock risk, Low sell-through) | Inventory and allocation health |
| Merchant | Type in (Low sell-through, Overstock risk) | Commercial performance |
| Operations Lead | SLA status = Breached OR Age bucket >= 16-30 days | Escalation and chronic issues |

### Action list output format

The daily action list is generated as a structured artifact consumed by the dashboard. The output schema:

```json
{
  "generated_at": "ISO-8601 timestamp",
  "aging_date": "YYYY-MM-DD (the date used for age calculations)",
  "total_open_exceptions": "integer",
  "breached_count": "integer",
  "critical_count": "integer",
  "items": [
    {
      "rank": "integer",
      "exception_id": "string",
      "type": "string (one of 8 taxonomy types)",
      "severity": "critical | watch | info",
      "priority_score": "integer",
      "sla_status": "within | approaching | breached | paused",
      "age_in_days": "float",
      "sla_window_label": "string (e.g., '24 hours', '48 hours')",
      "deadline": "ISO-8601 timestamp",
      "expected_action": "string (from action playbook)",
      "owner": "string",
      "store": "string",
      "region": "string",
      "campaign": "string|null",
      "sku": "string|null",
      "last_update_at": "ISO-8601 timestamp",
      "root_cause_tag": "string|null"
    }
  ]
}
```

## Exception lifecycle state machine

Every exception follows the same state machine:

```
RAISED (auto, from reconciliation engine or campaign tracker)
  --> OPEN (initial state)
    --> IN_PROGRESS (owner has started work)
      --> RESOLVED (resolution documented, hours recorded)
        --> CLOSED (system auto-closes 24h after RESOLVED if no reopen)
    --> PAUSED (owner requests pause per pause rules)
      --> IN_PROGRESS (when pause expires or owner resumes)
    --> ESCALATED (auto-escalation or manual escalation)
      --> IN_PROGRESS (new owner takes over)
    --> WAIVED (valid documented reason; requires manager approval)
      --> CLOSED
```

### State transitions and permissions

| From | To | Who can trigger | Required input |
|------|----|-----------------|----------------|
| RAISED | OPEN | System (auto) | None |
| OPEN | IN_PROGRESS | Assigned owner or Operations Lead | Comment field (min 10 chars) |
| IN_PROGRESS | RESOLVED | Assigned owner | Resolution text (min 20 chars), resolution type (reposted, corrected, transferred, written_off, system_fix, no_action_required) |
| IN_PROGRESS | PAUSED | Assigned owner or Operations Lead | Pause reason (must match pause rules), expected resume date |
| IN_PROGRESS | ESCALATED | System (auto) or Operations Lead | New owner assignment, escalation reason |
| IN_PROGRESS | WAIVED | Operations Lead or above | Waiver reason (min 30 chars), root cause tag, approving manager name |
| RESOLVED | CLOSED | System (auto after 24h) | None |
| RESOLVED | OPEN (reopen) | Assigned owner, auditor, or Operations Lead | Reopen reason (min 20 chars). Triggers EX-20 upstream rule. |
| PAUSED | IN_PROGRESS | System (auto on expiry) or assigned owner | Comment field |
| ESCALATED | IN_PROGRESS | New assigned owner | Comment field |

### Reopen rules

- Reopening a resolved exception creates a NEW exception_id that links to the original (parent_id).
- The reopened exception inherits the original's severity but with age_pressure set to 0 (clean slate for the new owner).
- The original exception's reopen_count increments by 1.
- If an exception is reopened more than twice within 30 days, it auto-escalates to Operations Lead with a "chronic issue" tag.
- Exception reopen rate is tracked as a KPI: share of resolved exceptions reopened within 7 days.

## Close-out workflow

### Resolution resolution types

When an owner marks an exception RESOLVED, they must select a resolution type. Resolution types drive downstream learning and reporting.

| Resolution type | Meaning | Next step |
|----------------|---------|-----------|
| reposted | Confirmation or photo was reposted and validated | System re-validates the repost; auto-close on validation success |
| corrected | Physical correction made (replacement shipment, transfer, markdown executed) | System logs the corrective action and links to allocation transfer record |
| system_fix | The exception was caused by a system error and fixed in the system | System logs the fix; root cause tag set to "system" |
| write_off | Variance was small enough to write off; no further action | Write-off logged to inventory accuracy record; exception closed |
| good_will | Customer-facing goodwill resolution (credit, coupon, manual override) | Logged for margin impact tracking |
| no_action_required | Investigation found the exception was a false positive or within tolerance | Exception closed; false-positive flag set for rule tuning |

### Close-out checklist

Before an exception can be CLOSED (auto or manual), the following conditions must be met:

1. Status = RESOLVED with a resolution type selected.
2. Resolution text >= 20 characters.
3. Root cause tag assigned (see root cause taxonomy below).
4. Resolution time (hours from open to resolved) is recorded.
5. If exception is campaign-linked: campaign owner confirms the resolution or auto-confirms after 24h.
6. No pending reopen by the same owner within the last hour.

### Root cause taxonomy

Each closed exception must be tagged with a root cause. The taxonomy is:

| Root cause category | Sub-categories |
|--------------------|----------------|
| supplier | short_ship, wrong_sku, late_delivery, quality_issue |
| dc | short_pick, wrong_carton, system_error, delay |
| store | miscount, unreported_damage, training_gap, space_constraint |
| system | integration_failure, sync_delay, rule_error, data_quality |
| forecast | over_forecast, under_forecast, demand_shift |
| customer | order_change, cancellation, no_show, complaint |
| logistics | carrier_delay, route_failure, capacity_constraint |

## Modeling notes for downstream tasks

### What the simulation must support

- Daily batch generation of exception events from the allocation reconciliation rules (EX-01 through EX-24) mapped to the 8-category taxonomy above.
- Exception records with: exception_id, type, severity, status, owner, created_date, resolved_date, parent_id (for reopen tracking), root_cause_tag, resolution_type.
- SLA pause records linked to exceptions.
- Action list computed from the priority formula using simulated severity, age, business_impact, and campaign_urgency.
- Aging bucket re-computation as days pass.
- Reopen tracking with parent_id linkages.

### Safe to simulate

- Generate synthetic events that follow the severity matrix, state machine, and scoring formula above. All data is fictional.
- Business_impact can be simulated with a simple lookup: hero SKU flag from the SKU catalog, store_format from the store master.
- Campaign_urgency can be computed from the campaign start date (active = today between start and end, launch_window = today <= start + 7).
- Age_pressure, SLA status, and aging buckets are deterministic computations from created_date and the current aging date.
- Reopen events can be simulated at a stochastic rate (e.g., 5-10% of resolved exceptions are reopened within 7 days) but the rule-based consequences (escalation after 2 reopens, KPI tracking) are deterministic.

### Do not claim

- Real SLA performance from any real retailer.
- That the priority formula is industry-standard. It is a transparent, explainable portfolio model derived from the upstream research rules.
- That the aging bucket boundaries are universal. They follow ITSM conventions documented in BMC Helix and ServiceNow dashboards, adapted for retail ops.
- Real reopen rates, resolution time distributions, or breach rates. These should be simulated from reasonable portfolio assumptions.

### Cross-references to upstream research

This document consolidates and extends the following upstream content:

- **ops-kpi-scorecard.md**: Sections 5-6 (Exception Backlog and SLA/aging view layout), KPI #15-18 (Open Exception Count, Aged Exception Count, MTTR, SLA Met %), aging bucket structure (0-5 / 6-15 / 16-30 / 30+).
- **allocation-reconciliation.md**: 24 exception rules (EX-01 to EX-24) mapped to the 8-category taxonomy above; exception fields #31-45 (reconciliation fields); failure modes mapped to root cause categories.
- **retail-campaign-execution.md**: Campaign execution workflow linked to exception types (Missing photo proof, Late setup, Missing confirmation); audit levels (L1/L2/L3) linked to exception severity; corrective action workflow linked to exception state machine.

## Source notes

All sources are public web pages accessed on 2026-07-03. URLs are provided for verification.

1. BMC Helix ITSM - "Incident Aged Backlog Analysis Dashboard" - https://docs.bmc.com/xwiki/bin/view/Helix-Common-Services/Dashboards-Reports/BMC-Helix-Dashboards/BHD234/Viewing-out-of-the-box-dashboards/BMC-Helix-ITSM-dashboards/BMC-Helix-ITSM-Incident-Aged-Backlog-Analysis-dashboard/
   - Aging buckets 0-5, 6-15, 16-30, 30+ days.
   - SLA status color coding: red breached, orange approaching, green ongoing, blue paused.
   - Average age of incidents by priority and assigned group.

2. ServiceNow - "Account 360 Analytics Dashboard" - https://github.com/ServiceNow/ServiceNowDocs/blob/australia/markdown/proactive-service-exp-workflows/product-support-for-technology/account-360-analytics-dashboard.md
   - SLA performance tab: team overdue SLAs, team average SLAs age, overall SLA analysis achieved/breached.
   - Incident reopen rate as a quality metric.

3. Digital.ai - "Major Incident Delivery Performance Dashboard" - https://infosys.intelligence.digital.ai/Web/Help/MSTRWeb/WebHelp/Lang_1033/r-smpo-mi-inc-delv-perf.htm
   - MTTR, Composite opportunity rank combining incident count, SLA, MTTR, handle time.

4. Genesys - "Task Age Dashboard" - https://all.docs.genesys.com/PEC-REP/Current/RPRT/HRCXIiWDTskAgeDshbrd
   - Task age by department and process.

5. Moonstar - "Retail Performance Dashboard: The 10 KPIs Every Store Manager Should Track" - https://moonstar.ai/retail-performance-dashboard-10-kpis-store-manager/
   - Store-level scorecard pattern with aging and SLA status side by side.

6. OMSPro - "Resources Retail Control Tower" - https://omspropro.com/pages/resources-retail-control-tower
   - Control tower functional pillars; operational KPIs: MTTD, MTTR.

7. SysGenPro - "Retail ERP Reporting Frameworks" - https://sysgenpro.com/industries/retail-erp-reporting-frameworks-for-better-inventory-decisions-and-store-operations
   - Operational control tower concept: detects exceptions, prioritizes actions, coordinates responses.
