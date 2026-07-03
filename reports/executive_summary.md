# Executive Summary

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

## Key Actions This Week

| # | Exception ID | Type | Severity | Store | AM | Age | SLA | Action |
|---|-------------|------|----------|-------|----|-----|-----|--------|
| 1 | EXC-007 | missing_confirmation | critical | S-079 | Marcus Lee | 20d | breached | Contact store PIC to post confirmation; verify visit completion. |
| 2 | EXC-159 | quantity_mismatch | critical | S-048 | David Park | 18d | breached | Reconcile planned vs shipped vs received; initiate DC count verification. |
| 3 | EXC-1598 | unresolved_issue_sla_breach | critical | S-045 | Lisa Wong | 14d | breached | Escalate to operations lead for root-cause review. |
| 4 | EXC-1600 | unresolved_issue_sla_breach | critical | S-037 | Jennifer Kim | 14d | breached | Escalate to operations lead for root-cause review. |
| 5 | EXC-1602 | unresolved_issue_sla_breach | critical | S-011 | James Okoro | 14d | breached | Escalate to operations lead for root-cause review. |