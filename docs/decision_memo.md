# Decision Memo: Kopi Senja Operational Exceptions

**To:** Regional Operations Director, Kopi Senja
**From:** Retail Ops Control Tower (DPR Komisi VIII analysis)
**Date:** July 2026
**Re:** 3 recommended actions from 1,603 operational exceptions across 100 stores

---

## Summary

Analysis of 1,603 operational exceptions across 100 stores and 3 seasonal LTO campaigns identified 774 critical/breached exceptions requiring intervention. The verification module confirms interventions work: **59.9% resolution with action vs 34.3% without** (25.7pp effect, p<0.001).

Three actions address 80% of risk for an estimated $3,750 cost and $46,500 in recovered revenue (ROI 12.4x).

---

## Recommendations

### 1. Execute 15 SKU transfers for overstock/stockout rebalancing ($3,750 cost, $46,500 recovered)

**Problem:** 99 stockout-risk and 291 overstock-risk exceptions across 83 stores.
**Action:** Transfer 15 high-priority SKUs from overstock stores to stockout stores. DC count verification + dispatch within 48 hours.
**Cost:** $250 per transfer (DC labor + dispatch) = $3,750
**Revenue recovered:** $46,500 (15 transfers × $3,100 avg savings per transfer)
**ROI:** 12.4x
**Owner:** Supply chain team, coordinated with DC Jakarta

### 2. Focus on 47 watchlist stores (4 AM hours/week)

**Problem:** 651 "watch" severity exceptions not yet breached but trending toward SLA violation.
**Action:** Weekly 30-minute review with each of the 10 area managers covering their top 5 watch exceptions. Focus on `missing_photo_proof` and `late_confirmation` (highest volume, lowest intervention effect).
**Cost:** 4 AM hours/week across 10 area managers
**Why focus here:** `missing_photo_proof` shows only +4.8pp effect from intervention -- near-zero. These need process fixes, not phone calls.
**Owner:** Ops Lead

### 3. North region assortment audit (2 weeks)

**Problem:** North region has 355 `low_sell_through` exceptions (22% of total). These are the single largest exception category and show a 30.4pp intervention effect -- the highest payoff for action.
**Action:** 2-week audit of North region assortment and allocation planning. Compare sell-through rates against South/East/West benchmarks. Adjust Q3 allocation quantities.
**Cost:** 2 weeks analyst time
**Expected outcome:** 15-20% reduction in low_sell_through exceptions in Q3
**Owner:** Merchandising + North region ops

---

## What we are NOT recommending

**No per-rep performance review.** AM scorecard data exists but individual coaching is not the bottleneck. Systemic allocation and process gaps account for 70%+ of exceptions.

**No region-wide intervention.** The verification module shows interventions work for 4 of 6 exception types but show near-zero effect for `missing_photo_proof` (+4.8pp) and `late_confirmation` (+7.4pp). Blanket interventions would waste resources on exceptions that don't respond.

---

## Methodology note

Findings are from a matched comparison of 347 exception pairs (intervention vs control). The data generator injects a known 30pp effect with structured noise (8% failed actions, 5% assignment errors, 10% null results for specific types). The verification module recovers 25.7pp -- within confidence bounds [18.5pp, 32.8pp], bias -4.4pp.

**Results are from simulated data. The deliverable is the measurement methodology, not the finding.**

---

*DPR Komisi VIII -- retail operations analysis*
