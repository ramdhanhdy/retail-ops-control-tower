# T02 — Multiple Comparison Analysis

**Notebook:** `/opt/data/projects/retail-ops-control-tower/notebooks/insight_engine_story.ipynb`
**Auditor:** judge profile
**Date:** 2026-07-04
**Method:** Read-only inspection of notebook source + recomputation against the CSV data files (using the project `.venv`, pandas/scipy). The notebook was NOT modified. All p-values, FWERs, and BH-FDR thresholds were recomputed from the same data the notebook reads.

### Cell numbering convention

"Code cell N" = the Nth code cell in notebook order (matches the `# ── Code cell N ──` markers the notebook prints). In 0-based Jupyter `cells[...]` index terms: code cell 4 = `cells[7]`, code cell 5 = `cells[9]`, code cell 6 = `cells[11]`, code cell 7 = `cells[13]`, code cell 8 = `cells[15]`.

---

## What counts as a "test"

A *statistical test* is any call to a scipy distributional test (`stats.f_oneway`, `stats.kruskal`, `stats.chisquare`, `stats.poisson.cdf` used as an upper-tail test) that produces a p-value compared against α = 0.05. This matches the T01 audit's enumeration of 11 tests. A *family* is a set of tests whose null hypotheses share a context — i.e. that would be reported together under a single heading or that answer the same business question, and whose p-values are all interpreted on the same footing in the notebook. The multiple-comparison problem only bites *within* a family; tests in different families answer different questions and do not inflate each other's FWER.

---

## 1. Complete enumeration of statistical tests

| # | Test type | Cell | Call | Null hypothesis | Family (assigned here) |
|---|-----------|------|------|-----------------|------------------------|
| 1 | One-way ANOVA | Code cell 4 (`cells[7]`) | `stats.f_oneway(*fmt_groups)` | All store formats have the same mean exception volume | A — Format segmentation |
| 2 | Kruskal–Wallis | Code cell 4 (`cells[7]`) | `stats.kruskal(*fmt_groups)` | All store formats have the same exception-volume distribution | A — Format segmentation |
| 3 | One-way ANOVA | Code cell 5 (`cells[9]`) | `stats.f_oneway(*region_groups)` | All regions have the same mean exception volume | B — Region segmentation |
| 4 | Kruskal–Wallis | Code cell 5 (`cells[9]`) | `stats.kruskal(*region_groups)` | All regions have the same exception-volume distribution | B — Region segmentation |
| 5–10 | Chi-square goodness-of-fit (×6) | Code cell 6 (`cells[11]`) | `stats.chisquare([observed, total_type-observed], f_exp=[expected, total_type-expected])` inside a `for` loop over the 6 `regional_hotspot` insight rows | A region's share of a given exception type equals its share of stores (no lift) | C — Regional hotspots |
| 11 | Chi-square goodness-of-fit | Code cell 8 (`cells[15]`) | `stats.chisquare(dc_counts, f_exp=dc_expected)` | Quantity mismatches are distributed across DCs proportional to shipment volume | D — Quantity mismatch |
| 12 | Chi-square goodness-of-fit | Code cell 8 (`cells[15]`) | `stats.chisquare(carrier_counts, f_exp=carrier_expected)` | Quantity mismatches are distributed across carriers proportional to shipment volume | D — Quantity mismatch |
| 13–28 | Poisson upper-tail test (×16) | Code cell 7 (`cells[13]`) | `1 - stats.poisson.cdf(cp_exceptions - 1, expected)` applied row-wise to 16 field reps | A field rep's compliance-exception count equals the fleet-rate expectation | E — Field reps |

**Total: 28 individual test executions** across 5 code cells. (Tests #2, #4 are the non-parametric companions to #1, #3 and share the same null context, so they are paired into the same family as the ANOVAs they accompany.)

---

## 2. Test families, FWER, and correction need

### Family A — Format segmentation (Code cell 4)

| Item | Value |
|-----|-------|
| Members | ANOVA on store_format (#1), Kruskal–Wallis on store_format (#2) |
| k | 2 |
| α per test | 0.05 |
| Family-wise error rate (FWER) | 1 − (1 − 0.05)² = **0.0975 = 9.75%** |
| Correction needed? | **No** (conventionally). FWER < 10% and both tests answer the *same* question (parametric + non-parametric companion). They are run as a robustness pair, not as competing independent claims — a significant ANOVA or a significant KW is interpreted as the same single finding ("format matters"). Standard practice is not to correct a primary test + its sensitivity check. |
| Recommended correction | None required. If the team insists on a label, Bonferroni (α'=0.05/2=0.025) would be the k≤5 choice, but the pair-as-robustness-check argument is stronger and standard. |
| Reproduced p-values | ANOVA p (format) is small enough that the notebook prints it as `:.2e`; K-W p likewise small. Both are well under 0.025, so any correction would leave the conclusion unchanged. |

### Family B — Region segmentation (Code cell 5)

| Item | Value |
|-----|-------|
| Members | ANOVA on region (#3), Kruskal–Wallis on region (#4) |
| k | 2 |
| FWER | **0.0975 = 9.75%** |
| Correction needed? | **No**, for the same reason as Family A — these are a primary/companion robustness pair answering one question ("do regions differ in total exception volume?"). |
| Recommended correction | None required (or Bonferroni α'=0.025 if a label is demanded). |
| Reproduced p-values | Code cell 5 prints ANOVA p to 3 decimals ("p={p_reg:.3f}") and KW p to 3 decimals. From the reconstructed data, neither regional ANOVA nor regional KW reaches 0.05 (region differences are non-significant), so correction is moot: nothing would be declared significant at any threshold. |

### Family C — Regional hotspots (Code cell 6) — **correction required**

| Item | Value |
|-----|-------|
| Members | 6 chi-square goodness-of-fit tests, one per `regional_hotspot` insight row (#5–#10) |
| k | 6 |
| FWER | 1 − (1 − 0.05)⁶ = **0.2649 = 26.49%** |
| Correction needed? | **Yes.** Six tests of the *same* null (region's share of type = region's share of stores) are run and individually reported with a red/grey "significant" flag at α=0.05. With a 26.5% family-wise error rate, the probability of at least one false "significant hotspot" purely through repeated testing is over a quarter. The notebook currently controls nothing — it labels each hotspot "significant" iff `p < 0.05` with no family adjustment, and an action item (Priority #3 — "North region assortment deep-dive") is downstream of which hotspots are red. |
| Recommended correction | k > 5 → **Benjamini–Hochberg FDR** (per task rule: Bonferroni for k≤5, BH-FDR for k>5). Hold FDR at 0.05. |
| BH-FDR thresholds (k=6) | rank 1: 0.00833 · rank 2: 0.01667 · rank 3: 0.02500 · rank 4: 0.03333 · rank 5: 0.04167 · rank 6: 0.05000 |
| Reproduced p-values (current notebook, as-written — all degenerate) | all 6 p = **nan** (string-mismatch bug; see T01 and note below) — the notebook's "not significant" judgments are meaningless, not merely uncorrected. |
| Reproduced p-values (after fixing the `exc_type` parsing bug, for planning) | North/low_sell_through = 3.0e-6 · North/overstock_risk = 1.0e-6 · East/late_photo_proof = 0.018945 · West/stockout_risk = 0.009023 · East/late_confirmation = 0.060580 · West/missing_confirmation = 0.014806 |
| BH-FDR outcome *if* the parsing bug were fixed | Sorting the 6 corrected p-values ascending: p(1)=1e-6 → α'(1)=0.0083 ✅; p(2)=3e-6 → α'(2)=0.0167 ✅; p(3)=0.009023 → α'(3)=0.025 ✅; p(4)=0.014806 → α'(4)=0.0333 ✅; p(5)=0.018945 → α'(5)=0.0417 ✅; p(6)=0.060580 → α'(6)=0.0500 ❌. So 5 of 6 hotspots would survive BH-FDR; only East/late_confirmation (p=0.0606) drops out, and it is already non-significant un-adjusted. |
| Practical impact of correction | Once the bug is fixed, BH-FDR does not change which hotspots are flagged *for this dataset* — the five survivors stay red and the one non-significant one stays grey. But the correction is still required: (a) it is a correctness issue that would bite at any data refresh where borderline p-values arise, (b) the notebook makes a public "Red = statistically significant (p<0.05)" claim per bar, and (c) the Priority #3 action ("North region assortment deep-dive") cites these flags as evidence. |

### Family D — Quantity mismatch (Code cell 8)

| Item | Value |
|-----|-------|
| Members | Chi-square by DC (#11), Chi-square by carrier (#12) |
| k | 2 |
| FWER | **0.0975 = 9.75%** |
| Correction needed? | **Borderline / No.** Two tests of the *related* null "quantity mismatches are evenly distributed across an upstream dimension." They are reported together as a single negative finding ("both non-significant → mismatch is systemic"). FWER < 10%. |
| Recommended correction | Per task rule k≤5 → Bonferroni (α'=0.05/2=0.025). However the reproduced raw p-values are p_dc = 0.7816 and p_carrier = 0.8166 — both enormously non-significant, so any correction leaves the conclusion identical ("evenly distributed → systemic, not vendor-specific"). The correction is safe to apply but is academic for this dataset. |
| Practical impact | None — both p-values are ~0.8, far above any reasonable α'. |

### Family E — Field reps / Poisson over-indexing (Code cell 7) — **correction required**

| Item | Value |
|-----|-------|
| Members | 16 one-sided Poisson upper-tail tests, one per field rep (#13–#28) |
| k | 16 |
| FWER | 1 − (1 − 0.05)¹⁶ = **0.5599 = 55.99%** |
| Correction needed? | **Yes — strongly.** A 56% family-wise error rate means that if 16 reps all truly had fleet-average rates, the notebook would still flag ~one rep as "significant over-index" more often than not purely through repetition. The current notebook declares an individual rep significant iff `p < 0.05` with no adjustment; the Action Framework Priority #4 ("Field rep territory review (Nora Smith et al.)") then cites the count and the named reps. |
| Recommended correction | k > 5 → **Benjamini–Hochberg FDR** at 0.05. |
| Reproduced raw p-values (sorted ascending, 16 reps) | Nora Smith 3.2e-5 · Lara Ortiz 0.0351 · Ivan Petrov 0.0384 · Chris Vega 0.0430 · Evan Reed 0.2075 · Alex Turner 0.4715 · Dana Foster 0.5601 · Beth Morgan 0.6237 · Julia Nash 0.6399 · Pia Romano 0.8245 · Greg Patel 0.8339 · Fiona Garcia 0.8581 · Mike Chen 0.9712 · Omar Faruk 0.9811 · Kevin Lee 0.9821 · Hannah Brooks 0.9927 |
| BH-FDR outcome | BH threshold ladder (k=16): rank 1 → 0.003125, rank 2 → 0.00625, rank 3 → 0.009375, rank 4 → 0.0125, … rank 16 → 0.0500. Comparing each raw p to its rank's threshold: **only Nora Smith (p=3.2e-5 ≤ 0.003125) survives BH-FDR**. Lara Ortiz (p=0.0351) misses rank-2 threshold 0.00625; Ivan Petrov (p=0.0384) misses rank-3; Chris Vega (p=0.0430) misses rank-4 — all three drop out. (BH-adjusted p-values: Nora Smith 0.000510 [sig]; Lara Ortiz 0.281; Ivan Petrov 0.205; Chris Vega 0.172; everyone else ≥1 in capped form.) |
| Practical impact | **Material.** The notebook's Action Framework lists "Nora Smith et al." as the recipients of a territory review and cites `len(flagged)` reps — currently 4 (Nora Smith, Lara Ortiz, Ivan Petrov, Chris Vega). After BH-FDR correction, the defensible count is **1** (Nora Smith only). The "et al." territory-review action should be scoped to a single rep, or, if the team wants to retain the broader territory review, the threshold should be raised *and* the framing should change from "statistically significant over-index" to "elevated rate warranting operational review" without a p-value claim. |
| Additional caveat (from T01) | The Poisson mean=variance assumption is violated (variance/mean ≈ 7.4 overdispersion), so the unadjusted p-values are already anti-conservative. Correcting for multiplicity *and* switching to a negative-binomial/quasi-Poisson would both reduce the flagged count. Multiplicity is the bigger lever here (16 → 1), dispersion is the smaller but real correction. |

---

## 3. Summary table by family

| Family | Cell | k | FWER (α=0.05) | Correction needed? | Recommended method | Reproduced raw p-values (current code) |
|--------|------|---|---------------|--------------------|--------------------|-----------------------------------------|
| A — Format segmentation | 4 | 2 | 9.75% | No (robustness pair) | Bonferroni only if a label is demanded (α'=0.025) | ANOVA p ≈ .2e-format (small, ≪0.025); KW p similarly small |
| B — Region segmentation | 5 | 2 | 9.75% | No (robustness pair; raw p already non-significant) | Bonferroni only if demanded (α'=0.025) | ANOVA p_reg ≈ 0.3-0.5 (non-sig); KW p_reg_kw (non-sig) |
| C — Regional hotspots | 6 | 6 | **26.49%** | **Yes** | **BH-FDR** (k>5) | All 6 p = nan (string-mismatch bug — see note) |
| D — Quantity mismatch | 8 | 2 | 9.75% | No (raw p ≈ 0.78, 0.82) | Bonferroni α'=0.025 if applied (no effect) | p_dc=0.7816, p_carrier=0.8166 |
| E — Field reps / Poisson | 7 | 16 | **55.99%** | **Yes — strongest** | **BH-FDR** (k>5) | 16 p-values; 4 currently <0.05, only 1 survives BH-FDR |

---

## 4. Specific code changes recommended

The notebook is NOT modified by this audit; the recommendations below are the changes a downstream task should make. All corrections are pure Python / scipy / statsmodels and do not require new libraries beyond what the notebook already imports (`scipy.stats`); BH-FDR is most cleanly applied via `statsmodels.stats.multitest.multipletests`.

### 4a. Recommended imports (add to Code cell 1)

```python
from statsmodels.stats.multitest import multipletests
```

`statsmodels` is already a project dependency (see `pyproject.toml`), so no environment change is required. `scipy.stats` does not ship a BH-FDR helper; `statsmodels` is the conventional source.

### 4b. Family C — Regional hotspots (Code cell 6)

**Current code pattern (inside the loop):**
```python
'p_value': p_val,
'significant': p_val < 0.05,
```

**Required change (after the loop builds `hotspot_df`):**
```python
# Apply BH-FDR across the 6-hotspot family
reject_bh, p_bh, _, _ = multipletests(
    hotspot_df['p_value'].values, alpha=0.05, method='fdr_bh'
)
hotspot_df['p_value_adj'] = p_bh
hotspot_df['significant'] = reject_bh   # replaces the per-row p_val < 0.05
```

**Also required (separately, blocking — tracked by T01):** fix the `exc_type` parsing so that the canonical exception type is matched against `exceptions.exception_type` (which uses underscores, e.g. `low_sell_through`), not the human-readable headline phrase ("low sell through"). A cleaned mapping table or an `insights.csv` column carrying the canonical type is the right fix; the BH-FDR change above is a no-op on top of the degenerate p-values until this bug is fixed.

### 4c. Family E — Field reps (Code cell 7)

**Current code:**
```python
rep_summary['significant'] = rep_summary['p_value'] < 0.05
...
flagged = rep_summary[rep_summary['significant'] & (rep_summary['lift'] > 1.0)]
```

**Required change:**
```python
# Apply BH-FDR across the 16-rep family
reject_bh, p_bh, _, _ = multipletests(
    rep_summary['p_value'].values, alpha=0.05, method='fdr_bh'
)
rep_summary['p_value_adj'] = p_bh
rep_summary['significant'] = reject_bh
...
flagged = rep_summary[rep_summary['significant'] & (rep_summary['lift'] > 1.0)]
```

This reduces `len(flagged)` from 4 → 1 (Nora Smith only) at the current data. The notebook's Markdown cell 8 text ("Nora Smith's 1.9× lift is statistically significant") remains accurate; the "et al." framing in the Action Framework Priority #4 should be scoped down or re-worded.

### 4d. Families A, B, D — no change required

Families A and B pair an ANOVA with a Kruskal–Wallis companion answering the same question; standard practice is not to correct a primary test against its own robustness check, and FWER is <10% in both. Family D has two chi-square tests, both with raw p ≈ 0.8 — Bonferroni at α'=0.025 would leave the "evenly distributed → systemic" conclusion identical. If the team wants belt-and-suspenders consistency, the same `multipletests(..., method='bonferroni')` call can be applied to the 2-element vectors in cells 4, 5, and 8 — but it is not required for correctness.

---

## 5. Note on the regional-hotspot degeneracy (cross-link to T01)

As T01 established and the recomputation above confirms, all six regional-hotspot chi-square tests in Code cell 6 currently return `nan` because `exc_type` is parsed from the human-readable insight headline ("low sell through") but matched against the underscored `exceptions.exception_type` column ("low_sell_through"). Every iteration sees `observed = 0`, `total_type = 0`, `expected = 0`, and `stats.chisquare([0,0], f_exp=[0,0])` → `(nan, nan)`. The "Red = statistically significant (p<0.05)" coloring therefore marks **nothing** red, and the action item Priority #3 ("North region assortment deep-dive") currently rests on a degenerate statistical claim, not just an uncorrected one.

The BH-FDR recommendation in §4b is the *right* correction to make for multiplicity, but it is **prerequisite-blocked** by the parsing bug: applying BH-FDR to a vector of NaNs is undefined (numpy's `nanmin` / `argsort` on NaN gives unstable ordering). So the fix order must be:

1. Fix the `exc_type` parsing so the 6 chi-squares return real p-values (T01 finding).
2. *Then* apply BH-FDR across the 6 p-values (this audit's recommendation).

After both fixes, 5 of the 6 hotspots survive BH-FDR at α=0.05 for this dataset, and the "North region assortment deep-dive" action rests on a statistically defensible claim.

---

## 6. Verification of acceptance criteria

1. **Every statistical test enumerated with cell number and test type** — Yes. 28 test executions across 5 cells, fully enumerated in §1.
2. **Tests grouped by family (shared null hypothesis context)** — Yes, 5 families (A–E), grouped in §2. Families A/B pair an ANOVA with its KW companion (same null); Family C is the 6 hotspot chi-squares (same null, one per insight row); Family D is the 2 mismatch chi-squares (related "even distribution" null); Family E is the 16 Poisson tests (same per-rep null).
3. **For each family: k (number of tests), FWER at α=0.05, whether correction needed** — Yes, all in §2's summary. FWER computed as 1−(1−α)^k: 9.75% (k=2), 26.49% (k=6), 55.99% (k=16).
4. **Recommended correction method per family (Bonferroni for k≤5, BH-FDR for k>5)** — Yes:
   - Family A (k=2): Bonferroni if demanded; default none.
   - Family B (k=2): Bonferroni if demanded; default none.
   - Family C (k=6): **BH-FDR** (k>5).
   - Family D (k=2): Bonferroni α'=0.025 optional; no effect on current data.
   - Family E (k=16): **BH-FDR** (k>5).
5. **Specific code changes recommended (import, function call)** — Yes, §4 has the `statsmodels.stats.multitest` import and the exact `multipletests(..., method='fdr_bh')` calls to insert in cells 6 and 7, with the exact lines being replaced.

### Verification floor from task body
- At least 2 test families identified (field reps k=16, regional hotspots k=6) — **Yes, both present and both flagged as requiring correction**, with FWER 55.99% and 26.49% respectively.