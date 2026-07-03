# Allocation and Reconciliation Research

> Scope: How multi-store retail teams plan product allocation, dispatch, store receipt, sell-through, and exception reconciliation across the supply chain. Synthesized from public sources (retail math references, allocation guides, WMS/OMS exception documentation, planning blogs). No proprietary or real company data is used or implied. All data in the downstream portfolio project will be simulated.

## Practical workflow

The allocation-to-reconciliation lifecycle is a closed-loop process that compares what was planned, what was shipped, what was actually received at the store, and what was eventually sold. Gaps between these four quantities are the raw material for exception management. The steps below are synthesized from retail allocation guides (Toolio, Uphance, RetailNorthstar), WSSI planning views (RetailNorthstar, Retail-Plan), WMS/OMS exception handling (Oracle NetSuite, Oracle Xstore, SAP EWM), and stock cover guidance (Canopy, Prediko, ReactiveSDP).

### Step 1: Planned Allocation

HQ planning builds the initial allocation - the first shipment of new products to stores. The planner decides how many units go to each store door using store size, historical sales, customer demographics, regional demand, store cluster (not just geography), and prior sell-through patterns. A high-traffic store receives more; a low-traffic kiosk receives less. The output of this step is the **allocation plan**: a per-store, per-SKU line item with planned unit counts and a planned receipt date.

Initial allocation typically happens at the start of a season or product launch. Replenishment - the second phase - happens afterward and adjusts quantities based on actual sales and on-hand. Many retailers hold back a percentage of stock in the distribution center rather than shipping everything at once, so they can reallocate based on early sell-through signals.

### Step 2: Dispatch / Shipped Quantity

The planned allocation becomes a warehouse pick instruction. The distribution center or warehouse picks, packs, and ships the units. The shipment is recorded in the WMS/OMS with **shipped quantity** per carton and per SKU. The shipped quantity can differ from the planned quantity for several reasons: the SKU was out of stock at the DC, the carton was short-picked, the carrier refused part of a pallet, or the order was split across multiple trucks arriving on different days. The shipping document is the first reconciliation checkpoint: planned vs. shipped.

### Step 3: Store Received Quantity

The store receives the shipment and runs a receiving process: scan cartons, open, count units per SKU, and post the receipt against the shipping document. The **received quantity** is what the store physically counts. The receiving process produces a receiving document (sometimes called an ASNs against receipts, or inventory document at the store) that records expected vs. received per SKU. The store can accept, reject, or partially accept the shipment. Receiving exceptions are the second reconciliation checkpoint: shipped vs. received.

Common receiving exceptions include: carton damaged in transit (partial counts), SKU substitution (store receives a different variant than shipped), overage (store receives more than the document says), shortage (store receives fewer), and refused delivery (carrier late, wrong store, damaged pallet). Each exception triggers a reconciliation event.

### Step 4: Sell-Through and On-Hand

After receipt, the inventory flows to the sales floor or back-of-house and becomes available to sell. **Sell-through** measures how much of the received quantity actually sold in a defined period. Sell-through is the headline sales performance metric for an allocation decision: it tells you whether the buy and the allocation were calibrated to real demand. Sell-through is usually tracked at multiple time grains (week, period, season) and split by full-price vs. markdown to distinguish healthy selling from clearance-driven selling.

The **on-hand quantity** at any point equals received minus sold minus shrink minus transfers out plus transfers in. The WSSI view (Weekly Sales, Stock and Intake) tracks on-hand, sales, and intake weekly: closing = opening + intake - sales.

### Step 5: Stockout and Overstock Risk

A **stockout** happens when on-hand reaches zero before the next replenishment can land. A **weeks of cover (WOC)** calculation expresses on-hand as a number of weeks of expected demand at the current rate of sale. WOC lower than supplier lead time means a stockout is imminent - the next order will not arrive in time. WOC higher than roughly twice lead time (or higher than the remaining selling window for seasonal goods) means **overstock** is building and markdown pressure is coming.

Stockout and overstock are the two polar risk signals in an allocation workflow. Stockout means lost sales, customer disappointment, and missed campaign moments. Overstock means cash tied up, markdown margin loss, and aged inventory that may need to be transferred, returned to vendor, or written off. The reconciliation engine should surface both as exceptions: critical (stockout imminent) and watch (overstock building).

### Step 6: Reconciliation Exceptions

Every step in the workflow can produce a variance: planned vs. shipped, shipped vs. received, received vs. sold, sold vs. forecast. Each variance is a **reconciliation exception** that the control tower must surface. Exception rules are the codified business rules that turn variances into actionable flags: severity, owner, deadline, expected action. The exception table in the section below lists the standard rules.

The reconciliation engine does three things: (1) compute the variance between two stages, (2) classify the variance using a rule (within tolerance, watch, critical), (3) raise an action item with an owner and a deadline. Severity is not just the size of the variance - it is the size of the variance relative to the lead time, the campaign window, the value of the SKU, or the strategic priority of the store.

### Step 7: Corrective Action and Close-Out

When an exception is raised, a corrective action workflow follows: issue identified, owner assigned, deadline set, resolution documented, resolution time tracked. For a shipping shortage, the owner is the DC and the resolution is a backorder or reallocation from another store. For a stockout, the owner is the replenishment planner and the resolution is an emergency order or an inter-store transfer. For an overstock, the owner is the merchant and the resolution is a markdown, a transfer, a return to vendor, or a promotion.

The reconciliation cycle closes when the variance is resolved, the exception is logged (override, goodwill, system issue), and the learning is captured for the next allocation. The metrics tracked include: exception count, exception resolution time, exception reopen rate, and the percentage of exceptions that closed before the campaign window ended.

## Tracker fields

The following fields should be tracked in an allocation and reconciliation tracker. Compiled from retail allocation platforms (Toolio, Uphance, RetailNorthstar), OMS/WMS exception documentation (Oracle NetSuite, Oracle Xstore, SAP EWM), and planning views (WSSI, OTB).

### Allocation plan fields

| # | Field | Description |
|---|-------|-------------|
| 1 | allocation_id | Unique identifier for the allocation plan line |
| 2 | campaign_id | Link to campaign (campaign, season, or product launch) |
| 3 | sku | Stock-keeping unit |
| 4 | store_id | Destination store |
| 5 | planned_quantity | Units planned for this store/SKU |
| 6 | planned_receipt_date | Date the units are expected to be received at the store |
| 7 | allocation_phase | initial, replenishment, chase, transfer |
| 8 | allocation_method | fair_share, door-index, size-curve, manual-override |
| 9 | holdback_pct | Percentage of original buy retained at DC for reallocation |
| 10 | planner_owner | HQ planner responsible for this allocation |

### Shipment and receiving fields

| # | Field | Description |
|---|-------|-------------|
| 11 | shipment_id | Unique identifier for the shipment |
| 12 | shipped_quantity | Units actually shipped from DC |
| 13 | shipped_date | Date the shipment left the DC |
| 14 | expected_arrival_date | Date the shipment is expected at the store |
| 15 | carton_count | Number of cartons in the shipment |
| 16 | received_quantity | Units counted at store receiving |
| 17 | received_date | Date the store posted the receipt |
| 18 | receipt_status | accepted, partial, rejected, pending |
| 19 | receiving_exception_type | overage, shortage, damage, substitution, refused |
| 20 | receiving_owner | Store manager or receiver who posted the receipt |

### Sales and on-hand fields

| # | Field | Description |
|---|-------|-------------|
| 21 | units_sold | Units sold in the reporting period |
| 22 | units_sold_full_price | Units sold before any markdown |
| 23 | units_sold_markdown | Units sold on markdown or promotion |
| 24 | on_hand_quantity | Units on hand at the store at period close |
| 25 | on_order_quantity | Units on order with the supplier, expected before next replenishment |
| 26 | in_transit_quantity | Units shipped but not yet received |
| 27 | transfer_in_quantity | Units received from another store |
| 28 | transfer_out_quantity | Units sent to another store |
| 29 | shrink_quantity | Units lost to theft, damage, or administrative error |
| 30 | period_close_date | Date the period (day, week) ended |

### Reconciliation and exception fields

| # | Field | Description |
|---|-------|-------------|
| 31 | planned_to_shipped_variance | shipped_quantity - planned_quantity |
| 32 | shipped_to_received_variance | received_quantity - shipped_quantity |
| 33 | received_to_sold_pct | units_sold / received_quantity (sell-through) |
| 34 | weeks_of_cover | on_hand_quantity / average_weekly_units_sold |
| 35 | stockout_risk_flag | Boolean: WOC < supplier lead time |
| 36 | overstock_risk_flag | Boolean: WOC > 2 x lead time OR WOC > remaining selling window |
| 37 | exception_id | Unique identifier for the raised exception |
| 38 | exception_type | allocation_shortage, receiving_variance, stockout, overstock, sell_through_miss |
| 39 | exception_severity | info, watch, critical |
| 40 | exception_status | open, in_progress, resolved, closed, waived |
| 41 | exception_owner | Person or role assigned to resolve |
| 42 | exception_due_date | Resolution deadline |
| 43 | resolution_time_hours | Hours from exception raised to resolved |
| 44 | waiver_reason | Reason recorded if exception is waived |
| 45 | root_cause_category | supplier, dc, store, system, customer, forecast |

## Core formulas

The portfolio project will compute the following formulas. The split separates **process compliance metrics** (did the chain execute the plan?) from **sales performance metrics** (did the plan produce the right outcome?).

### Process compliance metrics

These metrics measure whether the supply chain executed the plan correctly. They are leading indicators of operational health and they are diagnostic: a bad sell-through may be a sales miss or a process miss.

| Metric | Formula | What it measures |
|--------|---------|------------------|
| Allocation accuracy | `1 - abs(planned_quantity - received_quantity) / planned_quantity` | How closely the store received what HQ planned. Misses are either DC short-picks or store receiving errors. |
| Shipped-to-plan fill rate | `shipped_quantity / planned_quantity` | What fraction of the planned allocation actually left the DC. Below 100% means the DC was short. |
| Receiving accuracy | `1 - abs(shipped_quantity - received_quantity) / shipped_quantity` | How well the store receipt matches the shipping document. Misses are damage, miscounts, or substitution. |
| On-time receipt rate | `count(received_date <= planned_receipt_date) / count(shipments)` | Fraction of shipments that arrived on or before the planned date. |
| Inventory accuracy | `1 - abs(system_count - physical_count) / system_count` | Match between system-recorded and physical inventory. Sub-95% silently breaks every downstream decision. |
| Allocation-to-receipt cycle time | `received_date - planned_receipt_date` | Days between plan and actual receipt. Negative means early. |

### Sales performance metrics

These metrics measure whether the allocation produced the right outcome. They are lagging indicators of planning quality.

| Metric | Formula | What it measures |
|--------|---------|------------------|
| Sell-through rate | `units_sold / received_quantity x 100` | Fraction of received units sold in the period. The headline performance metric. |
| Full-price sell-through | `units_sold_full_price / received_quantity x 100` | Fraction sold at full price before any markdown. Stronger signal of right product, right place, right time. |
| Plan vs actual variance | `(actual_sales - planned_sales) / planned_sales x 100` | How actual sales compare to plan. Used to surface reallocation candidates. |
| Door index | `store_sales / average_store_sales` | Whether a store is over- or under-performing the chain average. Inputs the next allocation round. |
| Sales per square foot | `store_sales / store_selling_area_sqft` | Productivity per footprint. Allocation driver for format-specific buys. |
| Markdown intensity | `units_sold_markdown / units_sold x 100` | Fraction of sales that required a markdown. High markdown intensity means poor full-price sell-through. |

### Risk metrics

These metrics predict future trouble. They trigger exception flags before the loss is realized.

| Metric | Formula | What it measures |
|--------|---------|------------------|
| Weeks of cover (WOC) | `on_hand_quantity / average_weekly_units_sold` | How many weeks current stock will last at current sales rate. |
| Forward weeks of cover | `(on_hand + on_order) / forecast_weekly_sales` | Cover including stock already on order. |
| Stockout risk | `1 if WOC < supplier_lead_time_weeks else 0` | Critical flag: stockout is imminent because the next order will not arrive in time. |
| Overstock risk | `1 if WOC > 2 x supplier_lead_time_weeks OR WOC > remaining_selling_window_weeks else 0` | Watch flag: cover is high enough to drive markdown pressure. |
| Reorder trigger point | `(lead_time_weeks x average_weekly_sales) + safety_stock` | Stock level at which a new order must be placed to avoid stockout. |
| Safety stock | `average_weekly_demand x safety_days_coverage / 7` | Buffer against demand spikes and supplier delays. |
| Stock-to-sales ratio | `on_hand_quantity / units_sold_this_period` | Months/weeks of cover expressed against the current period. |
| Lost sales (stockout) | `forecast_units_during_stockout_days - units_sold_during_stockout_days` | Sales lost when WOC hit zero before replenishment. |

### Worked example

A coffee chain allocates 200 units of a seasonal LTO drink kit to Store A for a 4-week campaign.

- Planned quantity: 200
- Shipped quantity (from DC): 190 (10 units short at DC)
- Received quantity (store count): 188 (2 units damaged in transit, store refused those units)
- Units sold in 4 weeks: 150
- Average weekly sales: 37.5
- On-hand at period close: 38 units
- Supplier lead time for replenishment: 2 weeks
- Remaining selling window: 3 weeks

Compute the metrics:

- Allocation accuracy: `1 - abs(200 - 188) / 200 = 1 - 6% = 94%`
- Shipped-to-plan fill rate: `190 / 200 = 95%`
- Receiving accuracy: `1 - abs(190 - 188) / 190 = 1 - 1.05% = 98.95%`
- Sell-through: `150 / 188 = 79.8%`
- WOC: `38 / 37.5 = 1.01 weeks`
- Stockout risk: `1` (WOC 1.01 < lead time 2)
- Overstock risk: `0` (WOC 1.01 < 2 x 2 = 4)

This store hits a **stockout exception** even though the sell-through is healthy. The action is a replenishment order placed this week; without it, the store runs out in 1 week and misses 1.5 weeks of campaign window. The 12-unit gap between planned and received (200 - 188) is a **process compliance miss** that may or may not affect the campaign outcome - the 79.8% sell-through is healthy enough to absorb the loss, but the next allocation should rebalance the DC shortfall.

## Exception rules

The table below lists the standard reconciliation rules for the portfolio project. Each rule has a code, a trigger condition, a severity, a default owner, and an expected resolution window. Rules are evaluated on a daily batch for the previous day's events and on a weekly batch for the trend metrics.

| Code | Rule | Trigger condition | Severity | Default owner | Resolution window |
|------|------|-------------------|----------|---------------|-------------------|
| EX-01 | Allocation shortage | shipped_quantity < planned_quantity x 0.95 | watch | DC operations | 48 hours |
| EX-02 | Allocation critical shortage | shipped_quantity < planned_quantity x 0.80 | critical | DC operations + planner | 24 hours |
| EX-03 | Receiving overage | received_quantity > shipped_quantity | info | Store manager | 72 hours (investigate) |
| EX-04 | Receiving shortage | received_quantity < shipped_quantity x 0.95 | watch | Store manager | 48 hours |
| EX-05 | Receiving critical shortage | received_quantity < shipped_quantity x 0.80 | critical | Store manager + DC | 24 hours |
| EX-06 | Carton damage | any carton count discrepancy | watch | DC operations | 48 hours |
| EX-07 | Substitution on receipt | sku_received differs from sku_shipped | watch | Store manager | 48 hours |
| EX-08 | Late shipment | received_date > planned_receipt_date + 1 day | watch | Logistics | 24 hours |
| EX-09 | Critical late shipment | received_date > planned_receipt_date + 3 days | critical | Logistics + planner | 24 hours |
| EX-10 | Stockout imminent | WOC < supplier_lead_time_weeks | critical | Replenishment planner | 24 hours |
| EX-11 | Overstock - early signal | WOC > 2 x lead_time_weeks | watch | Merchant | 7 days |
| EX-12 | Overstock - late signal | WOC > remaining_selling_window_weeks | critical | Merchant | 3 days |
| EX-13 | Sell-through miss | units_sold / received_quantity < period_target x 0.70 | watch | Merchant + planner | 7 days |
| EX-14 | Critical sell-through miss | units_sold / received_quantity < period_target x 0.50 | critical | Merchant + planner | 3 days |
| EX-15 | Full-price miss | full_price_sell_through < full_price_target x 0.80 | watch | Merchant | 7 days |
| EX-16 | Inventory accuracy miss | accuracy < 0.95 | watch | Store manager | 14 days |
| EX-17 | Critical inventory accuracy | accuracy < 0.90 | critical | Operations lead | 7 days |
| EX-18 | On-hand negative | on_hand_quantity < 0 | critical | Systems + store | 24 hours |
| EX-19 | Plan vs actual > 25% | abs(actual - plan) / plan > 0.25 | watch | Planner | 7 days |
| EX-20 | Exception reopened | exception re-raised within 14 days of close | watch | Operations lead | 7 days |
| EX-21 | Exception overdue | exception open past due_date | watch | Operations lead | 24 hours (escalate) |
| EX-22 | Exception critical overdue | critical exception open past due_date | critical | Operations lead + manager | 24 hours (escalate) |
| EX-23 | Transfer mismatch | transfer_in + transfer_out mismatch > 0 | watch | Store managers (both) | 72 hours |
| EX-24 | Shrink threshold | shrink_quantity > received_quantity x 0.05 | watch | Loss prevention | 7 days |

The severity ladder is straightforward: **info** is logged but not actioned, **watch** requires a response within the resolution window, **critical** requires same-day action and an escalation path. Critical exceptions also page the on-call manager; watch exceptions go to the daily action list.

## Common failure modes

Synthesized from retail execution gap analyses (Toolio, Uphance, Yoobic, Canopy), planning guidance (ReactiveSDP, Prediko), and WMS/OMS exception documentation (Oracle, SAP).

| # | Failure mode | What happens | Source signal |
|---|-------------|--------------|---------------|
| 1 | Wrong product at the wrong door | Inventory in the wrong channel or at the wrong store door underperforms. A style that sells well at urban doors allocated disproportionately to suburban doors shows lower sell-through at the chain level than underlying demand warrants. | Toolio, Uphance |
| 2 | Allocation in the same geography treated as the same demand profile | A coastal urban store and a suburban mall store in the same city may perform completely differently on the same SKU. Cluster stores by demand profile, not just geography. | Toolio |
| 3 | Late launch as default | Allocations arrive days after the campaign launch. Stores run out of POSM or hero product on day 1, miss the launch window, and never recover. | Toolio, Uphance |
| 4 | Phantom inventory in the system | System shows units that are not physically present. Allocations ship against phantom stock, triggering shorts and customer cancellations. Sub-95% inventory accuracy breaks every downstream decision. | RetailNorthstar, Canopy |
| 5 | WOC evaluated without lead time | A SKU at 4 weeks of cover with a 2-week lead time is fine. The same SKU with a 6-week lead time is a stockout in progress. WOC must be read against lead time, not as a raw number. | ReactiveSDP |
| 6 | Lookback window distorted by stockout weeks | A SKU was out of stock for 3 of the last 8 weeks. Average weekly sales is artificially depressed. The real demand was higher than what was sold. Exclude zero-sales weeks where inventory was also zero. | Canopy |
| 7 | No exception path on the rule | Every allocation rule has exceptions. A buyer calls in, a retailer asks for a partial early, a VIP orders something out of band. Without a written exception path, every exception becomes a precedent, and within two seasons the rule no longer means anything. | Uphance |
| 8 | Single inventory pool broadcast to every channel | A single inventory number sent to every channel cannot enforce an allocation rule because every channel races to claim from the same pool. Need channel-aware ATS pools where totals reconcile to on-hand but each channel sees its own gated number. | Uphance |
| 9 | Allocation logic lives only in the WMS | The WMS knows physical on-hand. It does not know commitments. If allocation logic lives only in the 3PL WMS, you cannot enforce channel priority because the WMS does not know which channel an order belongs to until it lands. Allocation rule must live in the OMS, upstream of the WMS. | Uphance |
| 10 | Markdown-driven success mistaken for chase candidate | A style at 70% total sell-through looks strong. The planner chases on it. The reorder lands. Then the markdown data reveals 45% of the original buy sold at markdown. The chase units have the same problem waiting. | RetailNorthstar |
| 11 | Missed chase window | A SKU that hits 35%+ sell-through by Week 6 of a 12-week season is a chase candidate. By Week 8 the lead time closes the window. Acting late costs the chase. | RetailNorthstar |
| 12 | End-of-season overstock | A seasonal item with 18 weeks of cover at the current sell rate and 8 weeks of selling window remaining is going to land at clearance. WOC must be evaluated against end date, not just lead time. | ReactiveSDP, Canopy |
| 13 | Reconciliation done in spreadsheets for 6+ hours a week | The reconciliation exists because nobody trusts the inventory number, and nobody trusts it because the channels are pulling from the same pool without governance. The work is a symptom of a missing rule. | Uphance |
| 14 | Chargebacks from allocation miss | Short shipment from DC triggers a chargeback from the wholesale partner. Phantom stock shown to customer triggers a cancellation. Aged inventory from over-allocation is written off. Each cost is invisible on its own; together they run into the millions. | RetailNorthstar |
| 15 | Size-level sell-through missed | A style at 70% total can be 85% on core sizes and 45% on extended sizes. The average hides the imbalance. Replenishment of extended sizes over-allocates; core sizes under-allocate. | RetailNorthstar |
| 16 | No hit-rate context | A 30% sell-through on a slow-selling basic is different from a 30% sell-through on a fashion item 4 weeks in. Reading a single number without context leads to wrong action. | RetailNorthstar |
| 17 | No full-price split | Sell-through reports show a single number. The markdown contribution is invisible until hindsight. A style at 75% total sell-through with 40% full-price is a markdown-driven success, not a real winner. | RetailNorthstar |
| 18 | Over-buying under good macro conditions | When the chain is growing 20% year over year, the buy is sized to last year's sell-through plus growth. The growth may not sustain. End-of-season markdown rates climb. | Toolio |
| 19 | Transfer decisions made late | Inventory sitting at 30% sell-through at one location can become 80% sell-through at another location if the transfer lands in time. The transfer decision made in week 8 of a 12-week season is too late. | Toolio |
| 20 | Exception rule without enforcement | A rule that is not enforced becomes a guideline. Allocation rules must be enforced by the OMS, not just stated in a planning document. | Uphance |

## Portfolio modeling decisions

This section defines what is safe to simulate for a coffee/retail chain portfolio project. The project uses simulated data only and does not claim access to any real company's data, internal systems, or operational experience.

### Safe to simulate

1. **Allocation plan**: Generate a synthetic multi-store coffee chain (30-80 stores) and simulate per-store, per-SKU allocation plans. Use door index, size curve, and holdback methods. All plans are fictional.

2. **Shipment records**: Generate synthetic shipment records with shipped quantities that differ from planned (DC short-picks, splits, substitutions). Carton counts and shipment IDs are fictional.

3. **Receiving records**: Generate synthetic store receiving records with received quantities that differ from shipped (damage, refusal, shortage, overage, substitution). Receiving status and exception types are simulated.

4. **Sales and on-hand**: Simulate daily unit sales per store, per SKU, with realistic full-price vs. markdown split. On-hand quantities are derived from received minus sold minus shrink plus transfers.

5. **Weeks of cover and risk flags**: Compute WOC from on-hand and average weekly sales. Flag stockout and overstock based on lead time and selling window. All inputs are synthetic.

6. **Exception events**: Generate synthetic exceptions with type, severity, owner, and resolution time. Code against the 24 exception rules above. All IDs and timestamps are simulated.

7. **Replenishment and chase decisions**: Simulate a replenishment planner workflow: trigger point calculation, replenishment order, expected arrival. All decisions are driven by simulated data.

8. **Transfer and markdown events**: Simulate inter-store transfers and markdown events as resolution actions for overstock exceptions. All events are synthetic.

9. **WSSI view**: Model a Weekly Sales, Stock and Intake view per store, per SKU: opening stock, sales, intake, closing stock, weeks of cover. All numbers are computed from synthetic data.

10. **Reconciliation dashboards**: Roll up the exceptions, variances, and risk flags into a control tower view by region, store, and SKU. All rollups are computed from simulated data.

### Do not simulate or claim

- Real company data, internal knowledge, or real-world retail operations experience.
- Real Tomoro data or access to Tomoro internal systems.
- That `pip install retail-ops-control-tower` works from PyPI (source install only).
- Real customer data, real sales figures, or real store locations.
- Any implication that the project is connected to a real coffee chain.

### Modeling rationale

The allocation and reconciliation workflow is well-suited for this portfolio project because:

- The four quantities (planned, shipped, received, sold) are well-documented in public retail math references, and the formulas for allocation accuracy, sell-through, WOC, and risk flags are stable across the industry.
- Coffee chains run predictable, calendar-driven seasonal campaigns (LTOs, holiday menus) with structured allocation and replenishment cycles, making the workflow realistic without requiring proprietary data.
- Exception management is a clear, rule-based domain that maps cleanly to a portfolio engine: code, severity, owner, deadline, resolution.
- The split between process compliance metrics and sales performance metrics is a real and useful distinction: a 95% sell-through is good only if the 5% that did not sell is explainable; a 95% receiving accuracy is meaningless if the underlying allocation was wrong.
- Risk metrics (stockout, overstock) translate cleanly into action items: a stockout exception pages the replenishment planner, an overstock exception pages the merchant.

## Source notes

All sources are public web pages accessed on 2026-07-03. URLs are provided for verification.

1. RetailNorthstar - "Retail Math Formulas for Allocators in Apparel" - https://retailnorthstar.ai/resources/formulas/role/allocator
   - Ten retail math formulas for allocators: door-level demand index, fair-share allocation, fill rate, sell-through, WOS, FWOS, safety stock, inventory accuracy, replenishment trigger, size curve. Worked examples and benchmark ranges.

2. RetailNorthstar - "Sell-Through Rate Formula" - https://retailnorthstar.ai/resources/formulas/sell-through-rate
   - Sell-through formula and the full-price vs. markdown split. In-season read points: 20-25% by Week 3 is strong on a 12-week season; 35%+ by Week 6 warrants a chase. Benchmark ranges: DTC 50-70%+, wholesale 60-80%+, luxury 55-70%+.

3. RetailNorthstar - "Inventory Accuracy Formula" - https://retailnorthstar.ai/resources/formulas/inventory-accuracy
   - Inventory accuracy formula. Sub-95% silently breaks allocation. Accuracy compounds: short shipment, phantom stock, over-stocked SKU, safety-stock buffer consumed invisibly. Benchmark ranges by channel.

4. Toolio - "The Ultimate Guide to Retail Allocation" - https://www.toolio.com/post/the-ultimate-guide-to-retail-allocation
   - Initial allocation vs. replenishment phases. Sell-through formula, low/high sell-through interpretation, stock-to-sales ratio, weeks of supply. Cluster stores by demand profile, not just geography. Track channel-level STR separately.

5. Toolio - "Sell-Through Rate: Formula, Benchmarks and Strategies" - https://www.toolio.com/post/sell-through-rate-how-to-calculate-and-5-strategies-to-optimize
   - Sell-through formula with worked example. Most common causes: inaccurate forecasting, incorrect pricing, assortment-customer mismatch, inventory in the wrong location, poor merchandising. Diagnose at SKU and store level, not category.

6. ReactiveSDP - "Weeks of Cover: The Key Metric for Retail Buyers" - https://reactivesdp.com/blog/weeks-of-cover-retail-planning.html
   - WOC formula and the WOC vs. lead time decision table. WOC < lead time means critical (place emergency order). WOC > 2x lead time for end-of-season items means possible over-buy. WOC must be read against end date for seasonal items.

7. RetailNorthstar - "WSSI Calculator (Weekly Sales, Stock and Intake)" - https://retail-plan.com/tools/wssi-calculator
   - WSSI view: closing = opening + intake - sales. WSSI vs. OTB distinction. WSSI is the trading view, OTB is the budget view. WSSI tracks the season as it actually trades.

8. Retail-Plan - "Weeks of Supply Calculator" - https://retail-plan.com/tools/weeks-of-supply-calculator
   - Weeks of supply = current inventory / average weekly sales. Cover should comfortably exceed replenishment lead time. Refresh the average weekly sales figure as demand trends shift. Translate low/high cover into OTB, replenishment, or allocation action.

9. Canopy - "Weeks Cover in Stock Management" - https://www.canopyinventory.com/blog/weeks-cover-stock-management-explained
   - WOC formula and target ranges by supplier lead time: domestic (1-2 week) 4-8 weeks target, European (3-6 week) 8-14 weeks target, Asia sea freight (16-27 week) 20-35 weeks target. Exclude stockout weeks from the average.

10. Prediko - "Weeks of Supply Formula" - https://www.prediko.io/blog/weeks-of-supply-formula
    - WOS formula, target WOS = lead time + safety stock, monitoring cadence by product velocity. Forward WOS based on forecast is more reliable than historical alone. Static WOS can be misleadingly high right after a sales dip.

11. NetSuite - "Supply Allocation Exceptions Management" - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_159181096597.html
    - Exception lists, reallocation recommendations, supply required by date, allocation strategies, fill rate optimization. Late order allocation alerts. Reallocation across orders to meet high-priority demand.

12. Oracle Xstore - "Shipping/Receiving Exception Reports" - https://docs.oracle.com/en/industries/retail/retail-xstore-point-of-service/21.0/rpsug/shipping-receiving-exception-reports.htm
    - Shipping and receiving exception reports: expected, shipped, difference per document. Report types: summary, detail, summary and detail. Criteria: report date, document number, carton number, document type. Expected count comes from the inventory document, not the store.

13. Uphance - "What Is an Allocation Rule and How to Write One" - https://www.uphance.com/blog/what-is-an-allocation-rule-and-how-to-write-a-good-one/
    - Allocation rule components: priority, channel split, exception path, enforcement, reconciliation. Channel-aware ATS pools. Allocation logic in the OMS, not the WMS. The exception path: who can override, what is logged. Without an exception path, every exception becomes a precedent.

14. Oracle Retail RMS - "Transfers, Allocation, and RTV" - https://docs.oracle.com/cd/E79623_01/rms/pdf/160027/html/operations_guide1/rms-trans_alloc_rtv.htm
    - Allocation close process. Carton dummy IDs for damaged barcodes. Overdue transfer detection. Book transfer creation for same-warehouse allocations. Reconciliation logic across PO, transfer, allocation, ASN, and BOL.

15. SAP - "Quantity Differences for Stock Transfer Orders" - https://help.sap.com/saphelp_SCM700_ehp02/helpdata/en/fe/cccb53ad377114e10000000a174cb4/content.htm?no_cache=true
    - Quantity excess and shortage handling. Process codes for who caused the variance. Correction deliveries. Difference analyzer for clearing. Internal vs. external quantity differences.

16. Oracle Retail - "Appendix: Measure Calculations" - https://docs.oracle.com/cd/E75764_01/pdf/cloud/180/html/retail_user_guide/output/appendix_calculations.htm
    - EOP formula, receipt formula, sell-through formula, stock-to-sales ratio, WSSI components, OTB, forward cover, on-order, fulfillment metrics. Formulas are expressed in retail value (R), cost (C), and units (U) triples.
