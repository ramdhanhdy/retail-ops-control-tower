# T17 — Final Review

**Notebook under review:** `/opt/data/projects/retail-ops-control-tower/notebooks/insight_engine_story_v2_executed.ipynb`
**Inputs consumed:** T16 verification report (`reports/notebook-verification.md`), T01 assumption audit (`reports/t01-assumption-audit.md`), T02 comparison audit (`reports/t02-comparison-audit.md`), T03 gap analysis (`reports/t03-gap-analysis.md`), v1 notebook (`notebooks/insight_engine_story.ipynb`), executive summary (`reports/executive_summary.md`).
**Reviewer:** judge profile
**Date:** 2026-07-04
**Method:** Read-only inspection of the executed v2 notebook (full 1,209-line extraction), cross-referenced against the four upstream audit reports and the v1 notebook. No modification, no re-execution — per Do-Not-Scope.

---

## 1. Statistical soundness

### What is genuinely strong

- **Effect sizes are computed and labelled.** η² is reported for both ANOVAs with small/medium/large labels (format η²=0.518 large; region η²=0.041 small). Cohen's d is computed for all 12 pairwise t-tests (6 format + 6 region) with magnitude labels. Cramér's V is computed for the two quantity-mismatch chi-squares. This is a real improvement over v1, which reported η² only.
- **Multiple-comparison correction is implemented in code, not just prose.** `multipletests(..., method='fdr_bh')` is genuinely called for the 6-hotspot family (cell 19) and the 16-rep family (cell 21); Bonferroni α/6 is applied to the 6-pair format and 6-pair region families (cells 11, 17). The T02 recommendation is realized.
- **Confidence intervals are computed.** Bootstrap percentile CI on Gini (cell 5, n=5,000, seed=42, CI [0.311, 0.391]); Poisson exact 95% CI on field-rep lift via `poisson.ppf(0.025/0.975, ...)` (cells 19, 21); Wilson CIs on the SLA breach rate and critical-share proportions (markdown cells 15, 16). The T03 G2/G4 gaps are closed.
- **The region ANOVA assumption check actually runs.** Cell 14 prints Shapiro–Wilk per group (East p=0.0056 FAIL, South p=0.0348 FAIL, West p=0.1749 PASS, North p=0.0526 PASS) and Levene (p=0.0021 FAIL), then directs the reader to Kruskal–Wallis as authoritative. This is a clean, honest execution of the T01 recommendation.
- **Standardized verification metrics are reported.** 28 individual test executions across 5 families are documented; BH-FDR drops field-rep flagged count from 4 → 1 (Nora Smith only); hotspot degeneracy is surfaced rather than hidden.

### What is broken or unverified

1. **CRITICAL — Cell 8 (format ANOVA assumption check) is dead code.** The cell references `store_exc_fmt` on line 3, but that DataFrame is constructed in the *next* code cell (cell 9). The cell raises `NameError: name 'store_exc_fmt' is not defined` before any Shapiro/Levene test runs. So the format-ANOVA assumption check — the very thing T01 demanded — is present in source but produces an error traceback in the executed notebook, not the printed PASS/FAIL table. Only the region-ANOVA check (cell 14) actually executes. **Rigor-checklist item #1 ("assumption checks executed before each ANOVA") is only half-true.**

2. **CRITICAL — Cell 37 (T11 Sensitivity Analysis) never executes.** Its entire source is a single physical line beginning with `#`, so Python treats it as a comment. The kernel visited it (`execution_count=18`) but emitted no output. Consequently the Spearman ρ across the three weight scenarios is never computed, and every "ρ ≥ 0.960 / robust" claim in markdown cells 3, 21, and the appendix's rigor-checklist item #12 is **unverified prose, not computed output**.

3. **HIGH — Power analysis is asserted in prose but never computed in code.** Across all 18 code cells there is no import of `FTestAnovaPower` / `TTestIndPower` / `GofChisquarePower`, no `solve_power` call, no normal-approximation power formula, and no assignment to a `power` variable. Every "power=1.00", "power=0.31", "power=0.98", "power ~0.05" value cited in the narrative and the appendix's Power-convention section is an assertion. The appendix *describes* the intended method ("normal approximation with the observed effect size") but the notebook does not implement it. **Rigor-checklist item #7 is not demonstrable from the executed notebook.**

4. **Carried forward from v1 — Chi-square hotspot degeneracy (T01 critical).** Cell 19 still parses the exception type from the human-readable headline (`row['headline'].split('on ')[-1].strip()`) and matches it against the underscored `exception_type` column. All six iterations produce `observed=0, expected=0, p=nan`. The bug is now *acknowledged* in markdown cell 11 and the action-framework note demotes the "North region assortment deep-dive", which is honest — but the test is still degenerate and no regional hotspot is statistically significant as shipped.

5. **Carried forward from v1 — Poisson overdispersion (T01 finding #3).** The per-rep compliance counts have variance/mean ≈ 7.0. This is now *acknowledged* in markdown cell 12 ("a negative-binomial model would be more honest") but not remediated; the Poisson p-values remain anti-conservative. Nora Smith's BH-FDR margin (p=0.0005) is wide enough that the direction survives, so the headline finding is robust, but the raw p-value magnitude is not reliable.

### Statistical-soundness verdict

**NEEDS REVISION.** The effect-size, multiple-comparison, and CI machinery is genuinely implemented and is a substantial improvement over v1. But three of the six rigor-checklist items the appendix marks ✓ do not actually pass in the executed notebook: assumption checks (cell 8 errors), sensitivity analysis (cell 37 dead), and power analysis (no code). The notebook asserts rigor it has not demonstrated.

---

## 2. Narrative coherence

### Strengths

- **Pyramid Principle is well executed.** The governing thought (markdown cell 1) is stated first with concrete numbers (Gini 0.356, CI [0.311, 0.391]; Kruskal–Wallis p=4.06×10⁻⁸, η²=0.52; Nora Smith BH-FDR p=0.0005, lift 1.93×, CI [1.39, 2.50]) and the four-layer framework flows logically from concentration → segmentation → attribution → opportunity.
- **Transition paragraphs were added in v2.** Each layer now explicitly bridges to the next ("Knowing *that* risk is concentrated tells us where to focus. The next question is *why*..."). v1 had no such scaffolding; v2 reads as a connected argument.
- **Honest hedging.** Markdown cell 11 directly tells the reader the hotspot chi-squares are degenerate and cannot be called significant; markdown cell 12 acknowledges Poisson overdispersion; markdown cell 17 frames the flat temporal trend as "may be underpowered" rather than "no trend"; the action framework demotes the North-region action pending the parsing fix. This is a real tone shift from v1, which asserted "Red = statistically significant" above NaN bars.
- **Negative findings are framed.** The region ANOVA non-significance (markdown cell 9) and the quantity-mismatch null (markdown cell 13) are both framed with the "may be underpowered" caveat rather than read as proof of no effect — directly addressing T03 gap G16.

### Weaknesses

- **The narrative cites numbers the code does not produce.** "Power=1.00", "power=0.31", "power=0.98", and "Spearman ρ=0.960" appear throughout the markdown, but no code cell computes any of them. A reader who trusts the notebook as the source of truth is being told values that are asserted, not computed. This undermines the otherwise-strong honesty framing.
- **The appendix's 15-item rigor checklist marks three items ✓ that do not pass in execution** (assumption checks — cell 8 errors; sensitivity analysis — cell 37 dead; power — not computed). The checklist presents as a verification artifact; marking unpassed items as passed is an integrity issue, not just a bug.
- **The "Focus 47" headline is updated to "47 of 84 stores (56%)"** (markdown cell 1, 3, 4) but the action framework still says "Focus 47" — the rebrand is partial. Minor, but a coherence gap.

### Narrative-coherence verdict

**Strong in structure, weak in numeric discipline.** The flow, hedging, and layer transitions are professional-grade. But the narrative repeats power and ρ values the notebook does not compute, and the appendix asserts rigor that the executed cells do not demonstrate. These are not cosmetic — they are the kind of assertion a careful reviewer will catch and a stakeholder may rely on.

---

## 3. Business relevance

### Strengths

- **The four diagnostic layers map cleanly to operational levers.** Concentration → "where to focus" (Focus 47 watchlist). Segmentation → "which lever to pull" (format-specific SLA thresholds). Attribution → "who needs support" (rep territory review, data reconciliation audit). Opportunity → "what to do right now" (inter-store transfers, 12.4× ROI). Each finding translates to a concrete action with an owner, effort, and time-to-value.
- **Financial impact estimation was added (T03 G9).** The illustrative $1.04M exposure, $240K SLA penalty line, and 12.4× rebalancing ROI give a finance audience a dollar frame. The "illustrative — calibrate with finance" caveat is prominent and honest.
- **Temporal trend analysis was added (T03 G6).** The "flat trend, may be underpowered" reading tells operations the exception rate is not obviously growing, so capacity expansion is not the first lever — a genuinely useful operational signal.
- **The action framework is re-ranked by evidence strength.** v1's action #3 (North region deep-dive) rested on degenerate chi-squares; v2 demotes it with an explicit note that the parsing bug must be fixed first. This is the right call.
- **Rebalancing census framing is correct.** Markdown cell 14 explicitly says the 8 SKUs / 109 touchpoints are "exhaustive facts from the current dataset" and that no inferential test applies — avoiding the v1-era temptation to attach a p-value to a census count.

### Weaknesses

- **The area-manager layer (T03 G10, CRITICAL) is still missing.** `am_scorecard.csv` is loaded in cell 1 and never referenced again. For a "control tower" product, the AM tier is the layer ops management actually acts on, and the notebook analyzes formats, regions, reps, DCs, and carriers but skips the management tier entirely. v2 did not close this gap.
- **Aging buckets (T03 G7, HIGH) are still missing.** `age_days` is available but unused; the only aging signal is the "8 approaching" count. For an SLA-focused control tower, the age distribution by type is a foundational view that remains absent.
- **Three of the originally loaded-but-unused datasets are still loaded but unused** (`sales`, `alloc`, `kpis` — `am` is also unused, tied to G10). The appendix now documents this in the Data Scope table, which is honest, but the data is still loaded and silently discarded.

### Business-relevance verdict

**Good.** The action framework, financial frame, and temporal analysis make this a usable OPS review deliverable. The missing AM layer and aging buckets are real gaps for a control-tower product but are scope decisions, not errors.

---

## 4. Professional quality

### Strengths

- **Methodology appendix is extensive and well-structured.** 21,059 characters across 8 tables: Data scope, Reproducibility & determinism, Statistical methods, Sensitivity-correction tests, Multiple-comparison corrections, Dropped assumptions & known instrumentation corrections, Power convention, Financial model assumptions, and a 15-item Statistical rigor checklist. This is the kind of appendix a methods reviewer expects to see.
- **Plotly visualizations are professional.** Pareto + Lorenz dual chart with Gini CI in the title; box plots with ANOVA p and η² in the title; hotspot lift bars with BH-FDR colouring; field-rep lift bars with significance colouring; grouped observed-vs-expected bars for quantity mismatch; financial exposure breakdown bar. All carry titles, axis labels, and legends.
- **Determinism is documented.** Seed (42), bootstrap iterations (5,000), PRNG API (`default_rng`), software version pins, and the cell-execution-order caveat are all in the Reproducibility table.
- **Dollar figures are labelled illustrative everywhere they appear.** The Financial Model Assumptions table gives the default value, driver, and "illustrative" caveat for every parameter — a finance reviewer can swap constants without changing the structure.

### Weaknesses

- **The rigor checklist over-claims.** Item #1 (assumption checks) is marked ✓ but cell 8 errors; only the region check runs. Item #7 (power for non-significant inferences) is marked ✓ but no code computes power. Item #12 (sensitivity analysis with ρ ≥ 0.8 threshold) is marked ✓ but cell 37 is a comment. A reviewer or auditor who reads the checklist and trusts it will propagate these unverified claims downstream. This is the most serious professional-quality issue: the appendix is a self-audit artifact, and three of its pass marks are not earned by the executed notebook.
- **One error output ships in the notebook.** Cell 8 raises `NameError` and the traceback is in the executed outputs. A clean execution is a baseline expectation for a deliverable notebook.
- **One code cell ships with zero output.** Cell 37 runs (execution_count=18) but emits nothing because the entire source is a single comment line. A reviewer scanning the notebook sees a cell that "ran" but produced nothing — the T11 sensitivity analysis is effectively missing.
- **The "T11 Sensitivity Analysis" section header** (markdown cell 20) promises a robustness verdict, and markdown cell 21 delivers one ("ρ=0.960 ... ROBUST"), but the code that would substantiate it never executes. The section reads as complete but is not.

### Professional-quality verdict

**Strong on surface, undercut by the rigor-checklist over-claim.** The appendix, visualizations, and determinism documentation are professional-grade. But a self-audit checklist that marks three unpassed items as ✓ is a credibility hit. The error traceback (cell 8) and the dead cell (cell 37) are also below the bar for a delivered notebook.

---

## 5. v2 vs v1 comparison

### Added in v2 (new)

| What | Where | Closes |
|---|---|---|
| Shapiro–Wilk + Levene assumption check cells (format in cell 8, region in cell 14) | Code cells 4, 7 | T01 findings #2 |
| Bootstrap percentile CI on Gini (n=5,000, seed=42) | Code cell 3 | T03 G2 (partial) |
| Post-hoc pairwise t-tests with Bonferroni α/6 + Cohen's d (format, region) | Code cells 6, 9 | T03 G1 |
| BH-FDR correction on 6-hotspot family and 16-rep family | Code cells 10, 11 | T02 families C, E |
| Poisson exact 95% CI on field-rep and hotspot lift | Code cells 10, 11 | T03 G4 |
| Cramér's V effect size on quantity-mismatch chi-squares | Code cell 12 | T03 G2 (chi-square side) |
| Temporal trend analysis (daily counts, 7-day rolling, linregress slope test) | Code cell 16, markdown 17 | T03 G6 |
| Financial impact estimation (illustrative $, ROI 12.4×) | Code cell 17, markdown 18-19 | T03 G9 |
| Sensitivity analysis section header + interpretation | Markdown 20-21 | T03 G11 (claimed but cell dead) |
| Wilson score 95% CI on breach rate and critical share | Markdown 15-16 | (implicit) |
| Methodology appendix (8 tables, 15-item rigor checklist) | Markdown 22 | T03 G14, G15 |
| Transition paragraphs between layers | Markdown 4, 9, 13 | T03 G13 (narrative) |
| Executive-summary CIs and effect sizes | Markdown 1, 3 | T03 G13 |
| Explicit caveat on hotspot degeneracy and Poisson overdispersion | Markdown 11, 12 | T03 G13 |

### Improved in v2

- **Executive summary** now carries CIs (Gini [0.311, 0.391], lift [1.39, 2.50]) and effect sizes (η²=0.52), not just point estimates.
- **Format/region interpretation** now discusses assumption failures and defers to Kruskal–Wallis when assumptions fail — v1 never mentioned assumptions.
- **Field-rep analysis** now applies BH-FDR, reducing the flagged count from 4 → 1 (Nora Smith only). v1 asserted "4 reps" with no correction; v2's "1 rep after BH-FDR" is defensible.
- **Hotspot analysis** now acknowledges the degeneracy in-markdown rather than asserting significance over NaN bars (v1's "Red = statistically significant" was misleading).
- **Power discussion** appears in narrative (markdown 7, 9, 10, 17) with the "may be underpowered" framing — directly addressing T03 G16. However, the values are not computed (see above).
- **Negative findings are framed** as "informative but possibly underpowered" rather than "proof of no effect" (markdown 9, 13).

### Unchanged from v1 (carried forward)

- **Chi-square hotspot parsing bug** (T01 critical) — still present in cell 19; all six p-values are NaN. Now acknowledged, not fixed.
- **Poisson overdispersion** (T01 finding #3) — still present; variance/mean ≈ 7.0. Now acknowledged, not remediated.
- **Four-layer framework structure** — Concentration / Segmentation / Attribution / Opportunity. Deliberately preserved.
- **Area-manager analysis (T03 G10, CRITICAL)** — still missing; `am_scorecard.csv` still loaded and unused.
- **Aging buckets (T03 G7, HIGH)** — still missing; `age_days` still unused.
- **Residual hotspot sweep (T03 G5)** — still missing; only the 6 flagged rows are tested.
- **`sales`, `alloc`, `kpis` datasets** — still loaded and unused (now documented in the appendix Data Scope table, but the analysis is not added).

---

## 6. Remaining gaps and issues

### Blocking (must fix before delivery)

1. **Cell 8 NameError — `store_exc_fmt` not defined.** Reorder so the `store_exc_fmt.merge(...)` construction (currently cell 9) runs before the format-ANOVA assumption check (cell 8), or inline the merge into cell 8. Until fixed, the rigor-checklist claim "assumption checks executed before each ANOVA" is only half-true (region only).

2. **Cell 37 dead code — T11 Sensitivity Analysis is a single comment line.** Reformat the source so the Spearman ρ computation runs on real physical lines, then re-execute to produce the output that substantiates the "ρ ≥ 0.960, ROBUST" claim. Until fixed, rigor-checklist item #12 and the entire Sensitivity Analysis section verdict are unverified.

3. **Power analysis not implemented in code.** Add an actual power computation (e.g. `statsmodels.stats.power.FTestAnovaPower.solve_power` or `TTestIndPower.solve_power`, or a normal-approximation `norm.cdf`/`norm.sf` calc) for every non-significant inference the appendix labels with "power=N". Alternatively, remove the power column from the appendix and the power values from the narrative, and explicitly say power was not computed. Until fixed, rigor-checklist item #7 is not demonstrable.

### Non-blocking (scope decisions, not errors)

4. **Rigor-checklist over-claim.** Items #1 (assumption checks), #7 (power), and #12 (sensitivity) are marked ✓ but do not pass in execution. Once items 1-3 above are fixed, these marks become accurate; until then, mark them ✗ or ⚠ to match the executed state.

5. **Area-manager analysis (T03 G10, CRITICAL) still missing.** Consider adding a one-way ANOVA / chi-square across the 10 AMs on `exception_rate` and `sla_breach_count`. Not a blocker if scope was consciously deferred, but it is the most conspicuous remaining T03 gap.

6. **Aging buckets (T03 G7, HIGH) still missing.** Extend the SLA cell with a `pd.cut(age_days, bins=[0,7,14,30,1e6])` × `exception_type` crosstab. Useful for an SLA-focused control tower.

7. **Chi-square hotspot parsing bug (T01 critical) still present.** The honest acknowledgement in markdown cell 11 is good, but the test is still degenerate. Fixing it (normalizing headline tokens to `exception_type` strings) would re-activate 5 of 6 hotspots under BH-FDR per the T02 analysis and strengthen Action #3.

8. **Three loaded-but-unused datasets** (`sales`, `alloc`, `kpis`). Now documented in the appendix, which is honest, but the analysis is not added. Either add the day-of-campaign analysis (T03 G8) or the AM analysis (T03 G10) to use `sales`/`am`, or drop the unused loads.

---

## 7. Overall verdict

### **NEEDS REVISION**

The notebook is substantially stronger than v1 — it adds effect sizes, multiple-comparison correction, confidence intervals, assumption checks (in source), a temporal analysis, a financial frame, and a rigorous methodology appendix. The narrative honesty (acknowledging the hotspot degeneracy, the Poisson overdispersion, and demoting the under-evidenced action) is a real tone shift in the right direction.

However, three blocking defects prevent delivery:

1. **Cell 8 raises NameError** — the format-ANOVA assumption check is dead code.
2. **Cell 37 is a comment** — the entire T11 Sensitivity Analysis never executes, and its "ρ ≥ 0.96, ROBUST" verdict is unverified prose.
3. **Power analysis is asserted but never computed** — every "power=N" value in the narrative is an assertion, not a computation.

Additionally, the appendix rigor checklist marks three unpassed items as ✓, which is an integrity issue: a self-audit artifact that overstates what the executed notebook demonstrates. Once items 1-3 are fixed, the ✓ marks become accurate; until then they mislead a downstream reviewer.

### Items to fix (in priority order)

1. Reorder cells 8-9 so `store_exc_fmt` exists before the format-ANOVA assumption check runs. Re-execute.
2. Reformat cell 37 so the T11 Spearman ρ sensitivity analysis runs on real physical lines. Re-execute to produce the ρ output.
3. Add a code-level power computation (`FTestAnovaPower.solve_power` / `TTestIndPower.solve_power` or normal-approximation) for every non-significant inference currently labelled with "power=N" in prose. Alternatively, remove the power values and the power column from the appendix and state power was not computed.
4. After 1-3, re-audit the appendix rigor checklist and align the ✓ / ✗ marks with the executed state.

Once those four are addressed, the notebook would clear the bar for delivery. Until then, it is not ready for delivery.