# T03 — Missing Analyses Gap Report

**Notebook:** `/opt/data/projects/retail-ops-control-tower/notebooks/insight_engine_story.ipynb`
**Auditor:** researcher profile
**Date:** 2026-07-04
**Method:** Read-only inspection of notebook source and CSV headers against the four analytical layers. No code was executed inside the notebook and no notebook cell was modified. Two upstream audits were consumed as inputs and are referenced (not duplicated):

- **T01 — Statistical Assumption Audit** (`reports/t01-assumption-audit.md`): established that assumption checks (Shapiro–Wilk, Levene, expected-count ≥ 5, Poisson mean=variance) are missing and that the `exc_type` parsing bug in Code cell 6 makes all six hotspot chi-squares degenerate.
- **T02 — Multiple Comparison Analysis** (`reports/t02-comparison-audit.md`): enumerated 28 tests across 5 families, recommended BH-FDR for families C (k=6) and E (k=16), and gave the exact `statsmodels.stats.multitest.multipletests` calls to insert in Code cell 6 and Code cell 7.

This report covers the *remaining* gaps — analyses and narrative improvements that T01 and T02 do **not** cover. Where a gap's framing depends on a T01/T02 finding (e.g. an interpretation that over-asserts a result that T02 showed is correction-sensitive), the gap is described as a *narrative* gap and cross-references the upstream audit rather than re-deriving the statistical finding.

### Cell-numbering convention (consistent with T01/T02)

"Code cell N" = the Nth code cell in notebook order. "Markdown cell N" = the Nth markdown cell. The 11 code cells are numbered 1–11; the 12 markdown cells are numbered 1–12. Absolute Jupyter `cells[...]` indices are given for tests already mapped by T01/T02 (Code cell 4=`cells[7]`, 5=`cells[9]`, 6=`cells[11]`, 7=`cells[13]`, 8=`cells[15]`).

### Notebook data actually referenced

The notebook loads 8 dataframes in Code cell 1 (`exc`, `insights`, `stores`, `sales`, `alloc`, `disp`, `am`, `kpis`). Grep of the source confirms:

- `sales` (sales_daily.csv) — **loaded, never referenced after Code cell 1**
- `alloc` (allocation_plan.csv) — **loaded, never referenced after Code cell 1**
- `am` (am_scorecard.csv) — **loaded, never referenced after Code cell 1**
- `kpis` (kpi_summary.csv) — **loaded, never referenced after Code cell 1**

This is itself a gap: three of the dataset layers loaded are silently discarded.

---

## Gap inventory (17 gaps, 3 categories, 3 priority tiers)

### Category A — Missing statistical enhancements

| ID | Priority | Gap | What to add | Cell placement | Est. LOC |
|----|----------|-----|-------------|----------------|----------|
| **G1** | **CRITICAL** | **Post-hoc pairwise comparisons after the format ANOVA.** The ANOVA (Code cell 4) only rejects "all groups have the same mean"; markdown cell 5 then makes a *specific* pairwise claim — "Drive-thru and kiosk formats are structurally more exception-prone." That pairwise claim is not tested anywhere. Without a Tukey HSD (parametric) and Dunn's test (non-parametric companion, matching the Kruskal–Wallis already in the cell), the strongest actionable interpretation in Layer 2 is unsupported. | Add a Tukey HSD block and a Dunn's-test block to **Code cell 4**; render the pairwise p-value matrix (format × format) and add a 1-line "which formats differ from which" print. Mirror the same two blocks in **Code cell 5** for region. | Code cell 4 (formats), Code cell 5 (regions) | ~25 (Tukey HSD via `statsmodels.stats.multicomp.pairwise_tukeyhsd` + scikit-posthocs Dunn) × 2 cells ≈ **~50 LOC total** |
| **G2** | MEDIUM | **Effect-size confidence intervals.** η² is reported in Code cells 4 and 5 as a point estimate ("η² = 0.XX", labelled "large") with no interval. The "large effect size ⇒ format-level structural risk" interpretation in markdown cells 5 and 6 hangs on that point estimate. A noncentral-F-based or bootstrap CI on η² would show whether the lower bound still clears the 0.14 "large" threshold. | After the η² computation in each ANOVA cell, add a bootstrap CI (1k resamples of the residual, recompute η², take 2.5/97.5 percentiles) or a noncentral-F CI (`scipy.stats.ncf`). Print `η² = X.XX [L, U]`. | Code cell 4, Code cell 5 | **~15 LOC** |
| **G3** | HIGH | **Power analysis for the ANOVA / non-significant tests.** The region ANOVA (Code cell 5) is non-significant; markdown cell 6 treats this as "regional differences are within sampling variation" — but power is never reported, so the reader cannot tell whether the negative result is informative or merely underpowered. With k=4, n≈18–24/group, α=0.05, and the observed η²_reg, the achieved power should be reported; if it is low, the "regions do not differ" framing is unsafe. | Compute post-hoc achieved power for each ANOVA using `statsmodels.stats.power.FTestAnovaPower.power(...)` with the observed effect size, n, k, α. Print power alongside the p-value. Especially important for Code cell 5 (region, non-sig). | Code cell 4, Code cell 5 (cell 5 is the priority) | **~12 LOC** |
| **G4** | MEDIUM | **Confidence interval on the field-rep lift / rate ratio.** Code cell 7 reports point lifts ("1.9×") and the Poisson p-value, but no interval on the lift. A 95% CI on the observed/expected ratio (Byar's or exact Poisson interval on the rate) would show whether Nora Smith's 1.9× lower bound still exceeds 1.0 — which matters because T02 showed only Nora Smith survives BH-FDR. | For each rep in `rep_summary`, compute a 95% CI on the rate `cp_exceptions / store_count` (exact Poisson on the count) and on the lift = rate / fleet_rate. Print lift as `1.9× [1.5, 2.4]`. | Code cell 7 | **~18 LOC** |
| **G5** | MEDIUM | **Systematic hotspot sweep (residual analysis).** The hotspot chi-square loop (Code cell 6) tests only the 6 rows `insights.csv` flagged as `regional_hotspot` — it never asks whether *other* region × exception-type cells (4 regions × 9 exception types = 36 cells) would also be significant. Without a full residual sweep, the notebook cannot say the 6 flagged hotspots are the *only* ones; a data refresh could surface unflagged hotspots that the loop would silently miss. (Prerequisite: same `exc_type` parsing bug flagged by T01 must be fixed first.) | After the existing 6-row loop in Code cell 6, build the full 4×9 observed/expected matrix, compute standardized Pearson residuals per cell, flag |residual| > 1.96, and report any cells that are significant but not in `insights.csv`'s hotspot list. | Code cell 6 | **~22 LOC** |

### Category B — Missing analytical depth (temporal, financial, sensitivity)

| ID | Priority | Gap | What to add | Cell placement | Est. LOC |
|----|----------|-----|-------------|----------------|----------|
| **G6** | HIGH | **Temporal exception-arrival trend.** `exceptions.csv` carries `created_date` (2026-07-XX → 2026-09-28) and `age_days`, but the notebook never charts exceptions over time. For a control-tower audience, "is the exception rate accelerating or decelerating through the campaign window?" is a foundational question that the four-layer framework skips entirely. | New code cell between current Code cell 10 (SLA) and Code cell 11 (Action Framework): group `exc` by `created_date` (daily or weekly), chart the arrivals series with a 7-day rolling mean and a campaign-phase colour band, and flag the peak week. New markdown interpretation cell. | New code cell (Code cell 10.5) + new markdown cell | **~30 LOC** + ~6 lines MD |
| **G7** | HIGH | **Exception aging buckets.** `age_days` is available but unused. The notebook reports SLA breach *counts* (Code cell 10) but never buckets open exceptions by age (0–7, 8–14, 15–30, 30+ days) and never asks which exception *types* age fastest. The "8 exceptions in approaching status" callout in markdown cell 11 is the only aging signal, and it is a count, not a distribution. | Extend Code cell 10 (SLA) with an aging-bucket crosstab: `pd.cut(age_days, bins=[0,7,14,30,1e6])` × `exception_type`, rendered as a stacked bar. Print the top-3 exception types by 30+ day count. | Code cell 10 (extend) | **~20 LOC** |
| **G8** | MEDIUM | **Day-of-campaign pattern.** `sales_daily.csv` carries `day_of_campaign` (1–28), `units_sold`, `units_sold_full_price`, `units_sold_markdown`, `on_hand_quantity`. The notebook never asks whether exception rates track campaign lifecycle stage — e.g. whether stockout and overstock exceptions cluster in the launch ramp vs the steady-state vs teardown. This is the natural join between Layer 3 (attribution) and the sales data the notebook loads but discards. | New code cell after the rebalancing analysis (Code cell 9): merge `exc` → `sales` on `(store_id, sku)` within a campaign, aggregate `exception_rate = exceptions / day_of_campaign`, chart exception arrival rate vs `day_of_campaign` with campaign facets. | New code cell (after Code cell 9) | **~28 LOC** |
| **G9** | **CRITICAL** | **Financial impact quantification.** The entire notebook — including the Action Framework — quantifies "impact" in *exception counts*, never in dollars. `sales_daily.csv` has `units_sold_full_price`, `units_sold_markdown`, `on_hand_quantity`, `shrink_quantity`; the stockout and overstock findings describe *operational* risk but never translate it to lost full-price revenue (`on_hand_quantity` → stockout days × `units_sold_full_price` lost) or markdown loss (`units_sold_markdown` discount). The "zero-cost win" framing of the rebalancing layer (markdown cell 10) is unsubstantiated without a dollar estimate. | New code cell in Layer 4 (after the rebalancing cell, Code cell 9): for each rebalancing SKU, estimate lost full-price revenue on the stockout side and markdown/holding cost on the overstock side; print a small P&L table (`campaign × lost_full_price_revenue × markdown_loss × net_transfer_benefit`). Add a markdown cell interpreting the dollarised opportunity. | New code cell (Code cell 9.5) + new markdown cell | **~45 LOC** + ~8 lines MD |
| **G10** | **CRITICAL** | **Area-manager performance analysis (entire management layer missing).** `am_scorecard.csv` is loaded in Code cell 1 with `exception_rate`, `sell_through_rate`, `sla_breach_count`, `critical_count`, `store_count` per area manager — and then never referenced again. The notebook analyzes store *formats* (Layer 2), *regions* (Layer 2), *field reps* (Layer 3), and *DCs/carriers* (Layer 3), but skips the *area manager* tier entirely. For a "control tower" product this is the layer ops management actually acts on. | New code cell in Layer 2 (after Code cell 5, region): one-way ANOVA or chi-square across the 10 area managers on `exception_rate` and on `sla_breach_count`, with a rank-ordered bar of AMs by exception_rate and a "who is above fleet" table. New markdown cell interpreting the AM tier. | New code cell (after Code cell 5) + new markdown cell | **~35 LOC** + ~6 lines MD |
| **G11** | MEDIUM | **Sensitivity of the Pareto / "Focus 47" threshold.** The "Focus 47" watchlist and Priority #1 action hinge on an 80% concentration cutoff (markdown cell 4, Code cell 3). The notebook never shows how the watchlist size changes if the cutoff moves to 70% or 90%. For an action that reassigns review cadence across the fleet, the stability of the watchlist under threshold perturbation should be made explicit. | Extend Code cell 3 with a small sensitivity line: loop cutoff ∈ {70, 75, 80, 85, 90}%, record `pareto_n` and the Jaccard overlap with the 80% set; print the table. | Code cell 3 (extend) | **~15 LOC** |
| **G12** | HIGH | **Sensitivity of conclusions to α / multiplicity correction.** T02 established that applying BH-FDR to the field-rep family drops `len(flagged)` from 4 → 1, but the notebook's narrative (markdown cell 8 and the Action Framework priority #4) still asserts "4 reps" and "et al." This is a *narrative* gap, not a statistical-method gap: a small table showing "flagged rep count at α ∈ {0.01, 0.05, 0.10}, raw vs BH-FDR" would make the sensitivity explicit so a refresh or a new audience can see it. | Add a 4-row sensitivity mini-table to Code cell 7 (after the flagged-reps print): for each α in {0.01, 0.05, 0.10}, report both the raw `len(flagged)` and the BH-FDR-corrected count, so the dependency is visible in the notebook itself. (Cross-references T02 without re-running its analysis.) | Code cell 7 (extend) | **~18 LOC** |

### Category C — Missing narrative improvements

| ID | Priority | Gap | What to add | Cell placement | Est. LOC |
|----|----------|-----|-------------|----------------|----------|
| **G13** | **CRITICAL** | **Interpretation hedging to match T01/T02 findings.** The interpretive markdown cells currently over-assert: markdown cell 5 says "format explains a substantial proportion of variance" with η² labelled "large" but (per T01) the ANOVA assumptions are unchecked and (per G2) no CI is given; markdown cell 7 says "Red = statistically significant (p<0.05)" above bars whose p-values are `nan` (per T01 — degenerate chi-square); markdown cell 8 says "Nora Smith's 1.9× lift is statistically significant — her stores genuinely produce more compliance failures" without mentioning that (a) only Nora Smith survives BH-FDR (T02) and (b) the Poisson model is overdispersed (T01, variance/mean ≈ 7.4). A reader of the notebook alone is misled. (This is a narrative gap — the statistical fixes themselves are owned by T01/T02.) | Edit markdown cells 5, 6, 7, 8 to add explicit hedges: "under the ANOVA model (assumptions not formally verified — see audit)", "p-values for the six hotspot bars are currently degenerate pending a parsing fix — see audit", "only Nora Smith survives multiple-comparison correction — the 'et al.' framing in the Action Framework should be scoped down". | Markdown cells 5, 6, 7, 8 | **~20 lines** of prose edits (no code) |
| **G14** | HIGH | **Methodology Appendix completeness.** Markdown cell 12 lists tests and assumptions in a prose table, but omits: (a) the multiple-comparison strategy (which families are corrected, which are not, and why — the substance of T02); (b) the rationale for α = 0.05 (and the implicit claim that it is the operating threshold for every test); (c) the *data scope of each test* — e.g. that 16 stores with 0 exceptions are silently dropped from the format/region ANOVAs because `groupby` drops zero-count groups; (d) the software and library versions used. | Rewrite Markdown cell 12 to add: a "Multiple-comparison strategy" subsection, an "α threshold" note, a per-test "data scope" column (which rows are included/excluded), and a "Software" line (`scipy.stats`, `statsmodels`, `pandas`, `plotly` versions). | Markdown cell 12 | **~40 lines** of prose |
| **G15** | MEDIUM | **Reproducibility / data lineage.** Markdown cell 12 says "All data is deterministically generated from a fixed seed. Running `scripts/build_insights.py` regenerates insights.csv" but never documents: the seed value, the dependence on the aging date (2026-07-15) and how results shift if the aging date moves, the cell execution order assumption, and the fact that `sales_daily.csv`, `allocation_plan.csv`, `am_scorecard.csv`, and `kpi_summary.csv` are loaded in Code cell 1 but never used (so a reader may believe a sales analysis was done when it was not). | Add a "Reproducibility" subsection to Markdown cell 12: seed, aging-date dependency, execution-order assumption, and an explicit "Loaded but not analysed" list (`sales`, `alloc`, `am`, `kpis`) so the silence is documented. | Markdown cell 12 | **~15 lines** of prose |
| **G16** | MEDIUM | **Negative-findings framing.** The region ANOVA (Code cell 5 / markdown cell 6) and the quantity-mismatch chi-squares (Code cell 8 / markdown cell 9) are non-significant, and the notebook correctly does not claim significance — but it never frames these as *informative negative results*. Without a power statement (G3) and an explicit "we tested X; the test had power Y to detect effect Z; the negative result points to W" sentence, a reader cannot tell "no evidence of effect" from "evidence of no effect". | Add two short "Negative finding" paragraphs — one in markdown cell 6 (region) and one in markdown cell 9 (quantity mismatch) — explicitly stating what was tested, the power to detect an effect of a named size, and the operational implication of the negative result. Depends on G3 for the power numbers. | Markdown cells 6 and 9 | **~12 lines** of prose |
| **G17** | MEDIUM | **Limitations section.** There is no explicit Limitations section. For a deliverable framed as a "Strategic Findings Review" for management, the absence of a limitations block is a professional-quality gap: synthetic-data caveat, static aging date, no causal identification (every test is associational; no IV, no diff-in-diff, no natural experiment), no CIs on effect sizes (G2), and the loaded-but-unused datasets (G15) all belong in a labelled Limitations section, not buried in the appendix. | Insert a new "## Limitations" markdown cell immediately before the Methodology Appendix (between Code cell 11's action framework and Markdown cell 12). Bullet list: synthetic data, static aging date, associational-only inference, missing CIs, multiplicity not yet corrected, and the four loaded-but-unused datasets. | New markdown cell (between MD11 action header content and MD12 appendix) | **~18 lines** of prose |

---

## Priority rollup

| Priority | Count | IDs |
|----------|-------|-----|
| **CRITICAL** | 4 | G1 (post-hoc pairwise), G9 (financial impact), G10 (AM layer), G13 (interpretation hedging) |
| **HIGH** | 5 | G3 (power analysis), G6 (temporal trend), G7 (aging buckets), G12 (α sensitivity), G14 (appendix completeness) |
| **MEDIUM** | 8 | G2 (effect-size CI), G4 (lift CI), G5 (hotspot residual sweep), G8 (day-of-campaign), G11 (Pareto threshold sensitivity), G15 (lineage), G16 (negative-findings framing), G17 (limitations section) |
| **Total** | **17** | ≥ 10 floor satisfied; ≥ 1 in each of the 3 required categories |

## Cell-placement summary

| Type of placement | Gap IDs |
|-------------------|---------|
| Extend existing code cell | G2 (cells 4,5), G3 (cells 4,5), G4 (cell 7), G5 (cell 6), G7 (cell 10), G11 (cell 3), G12 (cell 7) |
| New code cell(s) | G6 (new, post-cell-10), G8 (new, post-cell-9), G9 (new, post-cell-9), G10 (new, post-cell-5) |
| Edit existing markdown cell | G13 (MD 5,6,7,8), G14 (MD 12), G15 (MD 12), G16 (MD 6,9) |
| New markdown cell | G6 (new MD), G8 (new MD), G9 (new MD), G10 (new MD), G17 (new MD pre-appendix) |

## Estimated total effort

If all 17 gaps were implemented: ~**320 LOC** of new/extended code plus ~**130 lines** of new/edited markdown prose. The CRITICAL tier alone (G1 + G9 + G10 + G13) is ~**150 LOC** of new/extended code plus ~**20 lines** of prose edits — roughly one focused work session.

---

## Verification against acceptance criteria

1. **Missing statistical enhancements listed (post-hoc tests, effect sizes, CIs, power analysis)** — ✅ Category A covers all four: post-hoc (G1), effect sizes (G2), CIs (G2, G4), power analysis (G3). Plus residual sweep (G5).
2. **Missing analytical depth listed (temporal, financial, sensitivity)** — ✅ Category B covers all three: temporal (G6, G7, G8), financial (G9) plus the AM layer (G10) which carries `sell_through_rate` and `exception_rate` from `am_scorecard.csv`, and sensitivity (G11, G12).
3. **Missing narrative improvements listed (interpretation quality, methodology appendix)** — ✅ Category C covers interpretation quality (G13, G16) and methodology appendix (G14, G15) plus a Limitations section (G17).
4. **Each gap prioritized CRITICAL / HIGH / MEDIUM** — ✅ see Priority rollup.
5. **Each gap has: what to add, which cell, estimated LOC** — ✅ every row in all three tables carries all three fields.
6. **At least 10 gaps identified across all priorities** — ✅ 17 gaps: 4 CRITICAL, 5 HIGH, 8 MEDIUM.
7. **Each gap has cell placement** — ✅ see Cell-placement summary.

### Do-Not-Scope adherence

- The notebook was **not modified** — this report is read-only and recommend-only.
- T01 and T02 findings are **not duplicated**. The two occasions where this report touches a T01/T02 result (G12 and G13) are framed as *narrative* gaps ("the notebook's markdown does not acknowledge what T02 found") and cross-reference the upstream audit rather than re-deriving the statistical conclusion.