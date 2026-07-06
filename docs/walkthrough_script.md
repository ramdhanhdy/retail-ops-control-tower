# Walkthrough Video Script: One Exception Through the Loop

**Duration:** 2 minutes
**Store:** S-048, Brookside Galleria (South region, AM: David Park)
**Exception:** EXC-159, quantity_mismatch, 47 shipped vs 37 received (21.3% variance)

---

## 0:00-0:10 -- Opening

> 100 stores. 1,603 exceptions. 3 seasonal campaigns. This is how we caught one.

[Show: dashboard overview, KPI tiles, "What needs attention today?" view]

---

## 0:10-0:30 -- The exception

> Store S-048, Brookside Galleria. The DC shipped 47 units of a seasonal SKU. The store received 37. That's a 21% variance -- priority score 375, severity critical, SLA breached.

[Show: exception board filtered to EXC-159, highlight the message field, show priority_score and sla_status columns]

---

## 0:30-0:50 -- The ranking

> Out of 1,603 exceptions, this one ranked #2 in priority. Assigned to David Park, area manager for the South region. The recommended action: DC count verification.

[Show: "What do I fix first?" view, daily action list, highlight rank #2, point to David Park and recommended_action column]

---

## 0:50-1:10 -- The intervention

> An action was logged: DC count verification. The mismatch was confirmed -- 10 units lost in transit. Resolution took 5 days. Without intervention, the matched control store took 43 days to resolve the same type of exception.

[Show: action queue view, show the assign form, then show the matched pair in intervention_outcomes.csv -- days_to_resolution=5 vs control_days_to_resolution=43]

---

## 1:10-1:30 -- The verification

> Across 347 matched pairs, interventions resolved 60% of exceptions vs 34% for controls. That's a 26 percentage point effect, statistically significant. The injected effect was 30pp -- our methodology recovered it within confidence bounds.

[Show: "Did interventions work?" view, the three metric tiles (60% vs 34%, +26pp), then the effect-by-type bar chart]

---

## 1:30-2:00 -- The loop and close

> Detect, rank, act, verify. That's the loop. The full decision memo with 3 recommendations -- 15 SKU transfers, 47-store watchlist focus, North region assortment audit -- is linked below.

[Show: loop diagram from README, then link to docs/decision_memo.md]

> Results are from simulated data. The deliverable is the measurement methodology, not the finding.

[End]
