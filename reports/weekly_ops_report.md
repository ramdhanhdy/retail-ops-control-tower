# Weekly Operations Report

**Week ending:** 2026-07-15  | **Aging date:** 2026-07-15

> This report is generated from simulated sample data. All figures are synthetic and do not represent real operations.

---

## 1. Executive Snapshot

This section provides a high-level overview of campaign execution health, operational risk, and data quality for the reporting period.

**Scope:**

- Stores: 100
- Campaigns: 3
- Allocation lines: 1,410
- Dispatches: 1,410
- Store confirmations: 1,366

**Process health:**

| KPI | Value |
|-----|-------|
| Campaign readiness rate | 83.8% |
| Confirmation completion rate | 96.9% |
| Photo proof completion rate | 91.9% |
| Allocation accuracy rate | 89.2% |
| Quantity mismatch rate | 10.8% |

**Risk and workload:**

| KPI | Value |
|-----|-------|
| Total exceptions detected | 1,603 |
| Open exceptions | 1,603 |
| Critical exceptions | 651 |
| SLA-breached exceptions | 160 |
| Exception rate (per allocation) | 1.137 |
| Stockout risk stores | 99 |
| Overstock risk stores | 291 |
| Sell-through rate | 64.9% |
| AM follow-up backlog | 1,603 |

**Data quality:**

- Validation findings: 2,770 (0 critical, 2,770 warning, 0 info)

**Summary assessment:**

Campaign execution health is moderate this week. Campaign readiness stands at 83.8%, with sell-through at 64.9% against a 70.0% target. There are 1,603 open exceptions (651 critical), of which 160 have breached SLA. Inventory risk is elevated: 99 stores face stockout risk and 291 face overstock risk. Priority actions for this week are listed in Section 7.
## 2. Campaign Readiness

Campaign readiness measures the fraction of allocation lines that have a completed, on-time store confirmation with photo proof within the campaign launch window.

**Overall readiness:**

- Campaign readiness rate: **83.8%**
- Confirmation completion rate: 96.9%
- Photo proof completion rate: 91.9%

**Per-campaign breakdown:**

| Campaign | Type | Start | End | Status |
|----------|------|-------|-----|--------|
| Summer Peach LTO 2026 (C-2026-PEACH) | seasonal_lto | 2026-07-01 | 2026-07-28 | active |
| Back to School Promo 2026 (C-2026-BTS) | promotional_pricing | 2026-08-01 | 2026-08-28 | active |
| Fall Coffee Launch 2026 (C-2026-FCL) | product_launch | 2026-09-01 | 2026-09-28 | active |

**Launch window compliance:**

- Late confirmations (after launch window): 83
- Missing confirmations (no matching record): 44
- Late photo proofs (after launch window): 162
- Missing photo proofs (no proof submitted): 111

Action needed: 127 allocations require follow-up to achieve full campaign readiness.
## 3. Allocation Reconciliation

Reconciliation tracks planned vs shipped vs received quantities across the allocation, dispatch, and confirmation tables.

**Accuracy summary:**

- Allocation accuracy rate (received == shipped): **89.2%**
- Quantity mismatch rate: **10.8%**

**Reconciliation findings (T09 validation engine):**

| Rule | Description | Count |
|------|-------------|-------|
| VAL-04 | Planned vs dispatched variance | 1,410 |
| VAL-05 | Planned vs received variance | 1,360 |
| VAL-06 | Dispatch without plan | 0 |
| VAL-07 | Confirmation without dispatch | 0 |

**Quantity mismatch exceptions:** 148

Top 5 quantity mismatches by priority:

| Exception | Store | AM | Shipped | Received | Variance |
|-----------|-------|----|---------|----------|----------|
| EXC-159 | S-048 | David Park | 47 | 37 | -10 |
| EXC-181 | S-058 | Robert Taylor | 52 | 41 | -11 |
| EXC-210 | S-062 | Jennifer Kim | 37 | 29 | -8 |
| EXC-225 | S-013 | Sarah Chen | 48 | 38 | -10 |
| EXC-250 | S-082 | Marcus Lee | 39 | 31 | -8 |

**Referential integrity:**

- Duplicate primary keys (VAL-02): 0
- Orphaned foreign keys (VAL-03): 0
- Referential integrity is intact across all tables.

## 4. Exception Backlog

The exception backlog summarizes all detected exceptions by type, severity, and SLA status.

**Exceptions by type:**

| Type | Count | Critical | Owner |
|------|-------|----------|-------|
| missing_confirmation | 44 | 6 | Field Operations |
| late_confirmation | 83 | 42 | Store Manager |
| quantity_mismatch | 148 | 7 | DC Operations |
| missing_photo_proof | 111 | 47 | Field Representative |
| late_photo_proof | 162 | 91 | Field Representative |
| stockout_risk | 99 | 99 | Replenishment Planner |
| overstock_risk | 291 | 0 | Merchant |
| low_sell_through | 659 | 355 | Merchant + Planner |
| unresolved_issue_sla_breach | 6 | 4 | Operations Lead |

**SLA aging breakdown:**

- Within SLA: 1,435
- Approaching SLA: 8
- Breached SLA: 160
- Paused: 0

**Age distribution:**

| Bucket | Count |
|--------|-------|
| 0-5 days (fresh) | 1,488 |
| 6-15 days (aging) | 62 |
| 16-30 days (overdue) | 53 |
| 30+ days (chronic) | 0 |

**Status breakdown:**

- Active (open/in_progress/raised/escalated): 1,603
- Resolved: 0
- Closed: 0
- Waived: 0
- Paused: 0

## 5. AM / Store Follow-Up List

The area manager scorecard ranks AMs by open exception workload. Each AM is responsible for resolving exceptions in their stores.

**Area manager scorecard:**

| AM | Region | Stores | Allocs | Confirms | Open Exc | Critical | SLA Breach | Stockout | Overstock | Sell-Through | Exc Rate |
|-----|--------|--------|--------|----------|----------|----------|------------|----------|-----------|---------------|----------|
| Emma Wilson | West | 12 | 190 | 185 | 228 | 83 | 22 | 14 | 38 | 66.4% | 1.200 |
| Lisa Wong | South | 15 | 158 | 153 | 207 | 83 | 25 | 8 | 44 | 61.4% | 1.310 |
| Maria Rodriguez | West | 10 | 172 | 167 | 198 | 86 | 26 | 8 | 46 | 58.9% | 1.151 |
| Jennifer Kim | North | 11 | 148 | 144 | 184 | 75 | 14 | 8 | 47 | 64.1% | 1.243 |
| Marcus Lee | East | 12 | 152 | 146 | 161 | 69 | 17 | 8 | 25 | 67.0% | 1.059 |
| Robert Taylor | North | 8 | 138 | 136 | 158 | 71 | 17 | 15 | 20 | 67.1% | 1.145 |
| Ahmed Hassan | East | 7 | 146 | 141 | 154 | 71 | 11 | 18 | 21 | 71.8% | 1.055 |
| David Park | East | 10 | 126 | 120 | 119 | 45 | 11 | 9 | 19 | 63.7% | 0.944 |
| James Okoro | West | 7 | 84 | 81 | 106 | 37 | 8 | 4 | 21 | 62.0% | 1.262 |
| Sarah Chen | East | 8 | 96 | 93 | 88 | 31 | 9 | 7 | 10 | 65.1% | 0.917 |

**Highest workload:**

- Emma Wilson (West) leads with 228 open exceptions across 12 stores.
- Lisa Wong (South) follows with 207 open exceptions.

## 6. Sales / Sell-Through Note

Sell-through rate measures units sold as a fraction of units received. The campaign target is 70.0%.

- Overall sell-through rate: **64.9%**
- Target: 70.0%
- Total units sold: 62,357
- Total units received: 96,035

**Inventory risk signals:**

- Stockout risk stores: 99
- Overstock risk stores: 291
- Low sell-through exceptions: 659

**Per-campaign sell-through:**

| Campaign | Units Sold | Units Received | Sell-Through |
|----------|------------|----------------|--------------|
| Summer Peach LTO 2026 | 19,824 | 32,220 | 61.5% |
| Back to School Promo 2026 | 22,761 | 33,613 | 67.7% |
| Fall Coffee Launch 2026 | 19,772 | 30,202 | 65.5% |

Sell-through is 5.1% below the 70.0% target. Review pricing, display compliance, and inventory positioning.
## 7. Recommended Actions

Top 10 action items for this week, ranked by priority score (severity, SLA age, and business impact):

| # | Exception ID | Type | Severity | Store | AM | Age | SLA | Action |
|---|-------------|------|----------|-------|----|-----|-----|--------|
| 1 | EXC-007 | missing_confirmation | critical | S-079 | Marcus Lee | 20d | breached | Contact store PIC to post confirmation; verify visit completion. |
| 2 | EXC-159 | quantity_mismatch | critical | S-048 | David Park | 18d | breached | Reconcile planned vs shipped vs received; initiate DC count verification. |
| 3 | EXC-1598 | unresolved_issue_sla_breach | critical | S-045 | Lisa Wong | 14d | breached | Escalate to operations lead for root-cause review. |
| 4 | EXC-1600 | unresolved_issue_sla_breach | critical | S-037 | Jennifer Kim | 14d | breached | Escalate to operations lead for root-cause review. |
| 5 | EXC-1602 | unresolved_issue_sla_breach | critical | S-011 | James Okoro | 14d | breached | Escalate to operations lead for root-cause review. |
| 6 | EXC-1603 | unresolved_issue_sla_breach | critical | S-011 | James Okoro | 14d | breached | Escalate to operations lead for root-cause review. |
| 7 | EXC-277 | missing_photo_proof | critical | S-092 | Maria Rodriguez | 14d | breached | Request field rep to re-submit photo proof within 24h. |
| 8 | EXC-280 | missing_photo_proof | critical | S-016 | Emma Wilson | 13d | breached | Request field rep to re-submit photo proof within 24h. |
| 9 | EXC-276 | missing_photo_proof | critical | S-014 | Marcus Lee | 12d | breached | Request field rep to re-submit photo proof within 24h. |
| 10 | EXC-287 | missing_photo_proof | critical | S-099 | Robert Taylor | 12d | breached | Request field rep to re-submit photo proof within 24h. |

**Strategic recommendations:**

1. Expedite replenishment for 99 stores at stockout risk; consider transfers from overstock stores.
2. Plan markdowns or inter-store transfers for 291 stores at overstock risk to free up working capital.
3. Escalate 160 SLA-breached exceptions to operations leads for root-cause review this week.
4. Follow up on 44 missing store confirmations; contact store PICs to verify visit completion.
5. Reconcile 148 quantity mismatches with DC operations; initiate DC count verification for high-variance lines.
6. Review pricing and display for 659 low sell-through items; consider promo acceleration or assortment changes.
7. Overall sell-through (64.9%) is below the 70.0% target; prioritize hero SKU visibility and POSM compliance audits.
8. Rebalance workload from Emma Wilson (228 open exceptions) to AMs with lighter backlogs.
9. Request field reps to re-submit 111 missing photo proofs within 24 hours.
## 8. Data Caveats

This section documents data quality notes, limitations, and assumptions that affect report interpretation.

- This report is generated from simulated sample data. All figures are synthetic and do not represent real operations.
- Aging date for SLA and exception age calculations: 2026-07-15.
- Division-by-zero in rate KPIs returns 0.0 by design (documented behavior of the T11 metrics engine).
- Exception status values are simulated; no real workflow state transitions are tracked.
- Sell-through target of 70% is a configurable default, not a validated benchmark.

**Validation findings:**

- Total findings: 2,770 (0 critical, 2,770 warning, 0 info)
- No critical data quality findings. Referential integrity is intact.
- Quantity variances (VAL-04: 1,410, VAL-05: 1,360) are by design in the sample data generator and feed the quantity_mismatch exception type.

**Tables covered:**

| Table | Rows |
|-------|------|
| allocation_plan | 1,410 |
| campaigns | 3 |
| dispatch | 1,410 |
| issues | 123 |
| photo_proofs | 3,091 |
| sales_daily | 39,480 |
| store_confirmations | 1,366 |
| stores | 100 |

**Report generation:**

- Report generated: 2026-07-15
- Week ending: 2026-07-15
- KPIs computed: 12 (5 process, 7 performance)
- Exception types detected: 9