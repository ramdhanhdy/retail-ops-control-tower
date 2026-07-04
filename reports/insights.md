# Diagnostic Insights

Generated from exception data aged as of **2026-07-15**. 14 ranked findings.

> Simulated data. Findings illustrate the diagnostic method, not any real retailer.

## Headline findings

- **47 of 100 stores (47%) drive 80% of all exceptions** (INS-001)
- **North region over-indexes 1.3x on low sell through** (INS-002)
- **North region over-indexes 1.5x on overstock risk** (INS-003)
- **East region over-indexes 1.3x on late photo proof** (INS-004)
- **8 SKUs in C-2026-BTS have both stockout and overstock stores - transfer candidates** (INS-005)

## Concentration analysis (Pareto)

### INS-001: 47 of 100 stores (47%) drive 80% of all exceptions

47 stores account for 1287 of 1603 exceptions (80%). Exception workload is 1.7x more concentrated than the store footprint. Fixing the top stores first yields outsized backlog reduction.

- **Impact score:** 3274
- **Affected:** 1287
- **Lift:** 1.71x
- **Evidence:** Top stores: S-011 (55), S-037 (55), S-058 (51), S-092 (46), S-018 (44)
- **Recommended action:** Assign a dedicated task force to the vital-few stores; run root-cause review per store before the next campaign phase.

## Regional hotspots

### INS-002: North region over-indexes 1.3x on low sell through

North holds 23% of stores but generates 31% of low_sell_through exceptions (202 of 659). A 1.3x lift indicates a localized process gap rather than a systemic one.

- **Impact score:** 521
- **Affected:** 202
- **Lift:** 1.33x
- **Evidence:** 202/659 low_sell_through exceptions in North; store share 23%
- **Recommended action:** Brief the North regional lead; audit the local workflow behind low sell through and retrain if needed.

### INS-003: North region over-indexes 1.5x on overstock risk

North holds 23% of stores but generates 35% of overstock_risk exceptions (102 of 291). A 1.5x lift indicates a localized process gap rather than a systemic one.

- **Impact score:** 155
- **Affected:** 102
- **Lift:** 1.52x
- **Evidence:** 102/291 overstock_risk exceptions in North; store share 23%
- **Recommended action:** Brief the North regional lead; audit the local workflow behind overstock risk and retrain if needed.

### INS-004: East region over-indexes 1.3x on late photo proof

East holds 27% of stores but generates 35% of late_photo_proof exceptions (57 of 162). A 1.3x lift indicates a localized process gap rather than a systemic one.

- **Impact score:** 150
- **Affected:** 57
- **Lift:** 1.30x
- **Evidence:** 57/162 late_photo_proof exceptions in East; store share 27%
- **Recommended action:** Brief the East regional lead; audit the local workflow behind late photo proof and retrain if needed.

### INS-007: West region over-indexes 1.5x on stockout risk

West holds 25% of stores but generates 36% of stockout_risk exceptions (36 of 99). A 1.5x lift indicates a localized process gap rather than a systemic one.

- **Impact score:** 124
- **Affected:** 36
- **Lift:** 1.45x
- **Evidence:** 36/99 stockout_risk exceptions in West; store share 25%
- **Recommended action:** Brief the West regional lead; audit the local workflow behind stockout risk and retrain if needed.

### INS-010: East region over-indexes 1.3x on late confirmation

East holds 27% of stores but generates 36% of late_confirmation exceptions (30 of 83). A 1.3x lift indicates a localized process gap rather than a systemic one.

- **Impact score:** 72
- **Affected:** 30
- **Lift:** 1.34x
- **Evidence:** 30/83 late_confirmation exceptions in East; store share 27%
- **Recommended action:** Brief the East regional lead; audit the local workflow behind late confirmation and retrain if needed.

### INS-013: West region over-indexes 1.6x on missing confirmation

West holds 25% of stores but generates 41% of missing_confirmation exceptions (18 of 44). A 1.6x lift indicates a localized process gap rather than a systemic one.

- **Impact score:** 37
- **Affected:** 18
- **Lift:** 1.64x
- **Evidence:** 18/44 missing_confirmation exceptions in West; store share 25%
- **Recommended action:** Brief the West regional lead; audit the local workflow behind missing confirmation and retrain if needed.

## Field rep workload

### INS-006: Field rep Nora Smith over-indexes 1.9x on proof and confirmation failures

Rep Nora Smith covers 7% of stores but accounts for 13% of confirmation and photo-proof exceptions (47 of 354). This may indicate route overload, training needs, or coverage gaps.

- **Impact score:** 132
- **Affected:** 47
- **Lift:** 1.93x
- **Evidence:** 47/354 rep-attributable exceptions vs 7% store coverage
- **Recommended action:** Review Nora Smith's route load and visit schedule; rebalance store coverage or provide refresher training on proof submission.

### INS-008: Field rep Lara Ortiz over-indexes 1.4x on proof and confirmation failures

Rep Lara Ortiz covers 8% of stores but accounts for 11% of confirmation and photo-proof exceptions (39 of 354). This may indicate route overload, training needs, or coverage gaps.

- **Impact score:** 99
- **Affected:** 39
- **Lift:** 1.37x
- **Evidence:** 39/354 rep-attributable exceptions vs 8% store coverage
- **Recommended action:** Review Lara Ortiz's route load and visit schedule; rebalance store coverage or provide refresher training on proof submission.

### INS-011: Field rep Chris Vega over-indexes 1.6x on proof and confirmation failures

Rep Chris Vega covers 3% of stores but accounts for 5% of confirmation and photo-proof exceptions (19 of 354). This may indicate route overload, training needs, or coverage gaps.

- **Impact score:** 55
- **Affected:** 19
- **Lift:** 1.56x
- **Evidence:** 19/354 rep-attributable exceptions vs 3% store coverage
- **Recommended action:** Review Chris Vega's route load and visit schedule; rebalance store coverage or provide refresher training on proof submission.

### INS-012: Field rep Ivan Petrov over-indexes 1.7x on proof and confirmation failures

Rep Ivan Petrov covers 2% of stores but accounts for 4% of confirmation and photo-proof exceptions (14 of 354). This may indicate route overload, training needs, or coverage gaps.

- **Impact score:** 42
- **Affected:** 14
- **Lift:** 1.72x
- **Evidence:** 14/354 rep-attributable exceptions vs 2% store coverage
- **Recommended action:** Review Ivan Petrov's route load and visit schedule; rebalance store coverage or provide refresher training on proof submission.

## Inventory rebalancing opportunities

### INS-005: 8 SKUs in C-2026-BTS have both stockout and overstock stores - transfer candidates

In campaign C-2026-BTS, 8 SKUs have 5 stores at stockout risk while 23 stores hold excess inventory of the same SKU. Store-to-store transfers can resolve both exposures without new intake or markdowns.

- **Impact score:** 137
- **Affected:** 109
- **Lift:** 0.00x
- **Evidence:** Top SKUs by combined exposure: BTS-008, BTS-007, BTS-003, BTS-005, BTS-009
- **Recommended action:** Generate a transfer shortlist pairing stockout and overstock stores per SKU; validate against transit time before the campaign window closes.

### INS-009: 6 SKUs in C-2026-FCL have both stockout and overstock stores - transfer candidates

In campaign C-2026-FCL, 6 SKUs have 3 stores at stockout risk while 20 stores hold excess inventory of the same SKU. Store-to-store transfers can resolve both exposures without new intake or markdowns.

- **Impact score:** 87
- **Affected:** 69
- **Lift:** 0.00x
- **Evidence:** Top SKUs by combined exposure: FCL-002, FCL-007, FCL-010, FCL-006, FCL-004
- **Recommended action:** Generate a transfer shortlist pairing stockout and overstock stores per SKU; validate against transit time before the campaign window closes.

### INS-014: 1 SKUs in C-2026-PEACH have both stockout and overstock stores - transfer candidates

In campaign C-2026-PEACH, 1 SKUs have 1 stores at stockout risk while 12 stores hold excess inventory of the same SKU. Store-to-store transfers can resolve both exposures without new intake or markdowns.

- **Impact score:** 15
- **Affected:** 13
- **Lift:** 0.00x
- **Evidence:** Top SKUs by combined exposure: PEACH-007
- **Recommended action:** Generate a transfer shortlist pairing stockout and overstock stores per SKU; validate against transit time before the campaign window closes.
