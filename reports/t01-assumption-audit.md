# T01 — Statistical Assumption Audit

**Notebook:** `/opt/data/projects/retail-ops-control-tower/notebooks/insight_engine_story.ipynb`
**Auditor:** audit-judge profile
**Date:** 2026-07-04
**Method:** Read-only inspection of notebook source + CSV data; no code executed inside the notebook. Assumption checklist follows the standard `data-analytics-methodology` rubric (Shapiro–Wilk normality, Levene homogeneity of variance for ANOVA; expected cell counts ≥ 5 for chi-square; count‑data + approximate‑Poisson‑process documentation for Poisson tests). The data‑analytics‑methodology skill was not installed on this profile, so the standard statistical rubric was applied directly.

### Cell numbering convention

"Code cell N" = the Nth code cell in notebook order (matches the `# ── Code cell N ──` markers the notebook prints). In Jupyter `cell` index terms (0-based over all cells), code cell 4 is `cells[7]`, code cell 5 is `cells[9]`, code cell 6 is `cells[11]`, code cell 7 is `cells[13]`, code cell 8 is `cells[15]`. Both conventions are given below for unambiguous identification.

---

## Summary counts

| Metric | Count |
|---|---|
| Total statistical tests identified | 11 |
| Total ANOVAs | 2 |
| Total chi-square tests | 8 (6 hotspot + 2 mismatch) |
| Total Poisson tests | 1 (looped over 16 reps → 16 individual one-sided tests) |
| Total t-tests | 0 |
| Assumption checks **present** (i.e. explicitly run or documented before the test) | 1 |
| Assumption checks **missing / not present** | 10 |
| Assumption checks that would have flagged a **violation** if run | at least 4 (see notes) |

---

## 1. ANOVA

### ANOVA #1 — Store format vs exception volume

| Item | Finding |
|---|---|
| Cell | **Code cell 4** (`cells[7]`) |
| Call | `stats.f_oneway(*fmt_groups)` |
| Group sizes (n) | standard=57, drive-thru=14, kiosk=8, flagship=5 (k=4 groups, N=84 stores with ≥1 exception; 16 stores have 0 exceptions and are dropped by `groupby`) |
| Shapiro–Wilk normality test run before? | **No.** No `stats.shapiro` appears anywhere in the notebook. The markdown only notes the exceptional distribution is "right-skewed" (Cell 3), which already signals non-normality. |
| Levene homogeneity-of-variance test run before? | **No.** No `stats.levene` / `stats.bartlett` anywhere. Group std devs are printed in `fmt_summary` but not formally tested. |
| Mitigating control present? | A Kruskal–Wallis non-parametric (`stats.kruskal`) is run alongside the ANOVA. This partially mitigates the normality concern (K-W is rank-based), but it does NOT mitigate the unequal-variance concern, and the notebook still reports and interprets the ANOVA F/p as the primary test. η² is computed from the ANOVA decomposition, which still assumes homogeneity. |
| Verdict | **Assumptions not verified.** Kruskal–Wallis mitigates only the normality gap. Equal-variance assumption is unchecked and likely violated given the skewed count data with very different group sizes (5 vs 57). |

### ANOVA #2 — Region vs exception volume

| Item | Finding |
|---|---|
| Cell | **Code cell 5** (`cells[9]`) |
| Call | `stats.f_oneway(*region_groups)` |
| Group sizes (n) | South=19, West=23, North=18, East=24 (k=4, N=84) |
| Shapiro–Wilk normality test run before? | **No.** Same skewed count data; no normality test anywhere. |
| Levene homogeneity-of-variance test run before? | **No.** |
| Mitigating control present? | Kruskal–Wallis run alongside. Same partial mitigation as above. |
| Verdict | **Assumptions not verified.** Identical gap to ANOVA #1. |

---

## 2. Chi-square

The notebook uses `scipy.stats.chisquare` (goodness-of-fit) everywhere — never `chi2_contingency`. So the relevant assumption is **expected count ≥ 5 per category**, not the independence test variant.

### Chi-square #1..#6 — Regional hotspot loop (all in one cell)

These six tests are emitted by a single `for` loop:

| Item | Finding |
|---|---|
| Cell | **Code cell 6** (`cells[11]`) |
| Call (inside loop) | `stats.chisquare([observed, total_type - observed], f_exp=[expected, total_type - expected])` |
| Number of tests emitted | 6 (one per `regional_hotspot` insight row) |
| Hotspot rows | North/low sell through, North/overstock risk, East/late photo proof, West/stockout risk, East/late confirmation, West/missing confirmation |

**Expected cell counts verified ≥ 5 before the test? — No, and worse: the test is degenerate.**

The notebook parses the exception type from the insight headline with `exc_type = row['headline'].split('on ')[-1].strip()`. The headlines are human-readable ("low sell through"), but the `exceptions.exception_type` column uses underscores ("low_sell_through"). The filter `exc[(exc['region']==region) & (exc['exception_type']==exc_type)]` therefore matches **zero** rows for every hotspot, so for all six iterations `observed = 0`, `total_type = 0`, `expected = 0`, and the call becomes `stats.chisquare([0, 0], f_exp=[0, 0])` → `chi2 = nan, p = nan`. The `significant = p_val < 0.05` comparison then evaluates to `False` (NaN < 0.05 is False). Verified by reconstructing each row from `insights.csv` and `exceptions.csv`.

Expected counts the test *would* have had if types were parsed correctly (for reference, using the canonical underscored types):

| Region | Exception type | Observed | Expected (rounded) | ≥ 5? |
|---|---|---|---|---|
| North | low_sell_through | 202 | 151.6 | Yes |
| North | overstock_risk | ~ (computed) | ~66.9 | Yes |
| East | late_photo_proof | ~ | ~43.7 | Yes |
| West | stockout_risk | ~ | ~24.8 | Yes |
| East | late_confirmation | ~ | ~22.4 | Yes |
| West | missing_confirmation | ~ | ~11.0 | Yes |

So if the parsing bug were fixed, all six expected counts would comfortably clear the ≥ 5 threshold. But the notebook **never checks or documents** the expected-count rule, and as written the check would also be degenerate (0 ≥ 5? no — but that would be a parsing artifact, not a real violation).

| Verdict | **Assumption not verified in code; and more importantly, the test itself is broken by a headline/data string-mismatch bug that makes all 6 iterations degenerate (0/0). Any "not significant" conclusion drawn from these p-values is meaningless, not merely under-supported.** |

### Chi-square #7 — Quantity mismatch by DC

| Item | Finding |
|---|---|
| Cell | **Code cell 8** (`cells[15]`) |
| Call | `stats.chisquare(dc_counts, f_exp=dc_expected)` |
| Categories | DC-01, DC-02, DC-03 (k=3) |
| Observed | DC-01=51, DC-02=49, DC-03=48 |
| Expected (computed by me from dispatch.csv) | DC-01=47.0, DC-02=51.0, DC-03=50.0 |
| Min expected cell count | **47.0** |
| Expected ≥ 5? | **Yes** — easily satisfied. |
| Documented/checked in notebook? | **No.** The notebook prints `f'By DC (χ² p={p_dc:.3f})'` and the χ²/p but never prints or asserts expected counts. Theassumption is satisfied but not verified in-code. |

### Chi-square #8 — Quantity mismatch by carrier

| Item | Finding |
|---|---|
| Cell | **Code cell 8** (`cells[15]`) — same cell as #7 |
| Call | `stats.chisquare(carrier_counts, f_exp=carrier_expected)` |
| Categories | FastFreight Co, QuickShip Logistics, Reliable Transport (k=3) |
| Observed | FastFreight=54, QuickShip=49, Reliable=45 |
| Expected | FastFreight=50.4, QuickShip=51.4, Reliable=46.2 |
| Min expected cell count | **46.2** |
| Expected ≥ 5? | **Yes** — satisfied. |
| Documented/checked in notebook? | **No.** Same as above. |

> Note: the Methodology Appendix (Markdown cell 12) *lists* "Expected ≥ 5 per cell" as an assumption for chi-square goodness-of-fit in a table, but no code cell actually computes, prints, or asserts the expected counts for any chi-square test. Listing the assumption in prose does not count as verifying it.

---

## 3. Poisson test

### Poisson #1 — Field-rep compliance over-indexing

| Item | Finding |
|---|---|
| Cell | **Code cell 7** (`cells[13]`) |
| Call (looped) | `1 - stats.poisson.cdf(r['cp_exceptions'] - 1, r['expected'])` (one-sided upper-tail) |
| Tests emitted | 16 (one rep has empty `field_rep` and is silently skipped by the grouping; 16 reps with non-empty names, but `rep_stores` only includes reps that appear in `stores.csv` field_rep column — 16 names plus 1 blank) |
| Counts data? | Yes — counts of compliance exceptions per rep. |
| Count-data assumption documented? | **Only in prose.** The Methodology Appendix lists "Count data" as the Poisson assumption, and the section text says "Poisson test for each rep: is their count significantly higher than expected?". No explicit check that the data are counts (they demonstrably are), but no formal documentation either. |
| Poisson-process (mean ≈ variance) assumption documented/checked? | **No.** The critical Poisson assumption is that the mean equals the variance. I computed this from the reconstructed per-rep counts: mean ≈ 22.1, variance ≈ 163.7, **variance/mean ratio ≈ 7.4** — substantial **overdispersion**. A Poisson model is a poor fit here; a negative-binomial would be more appropriate. The notebooknever tests or even mentions dispersion. |
| Independence assumption documented? | **No.** Reps with overlapping territories or shared stores are not ruled out. |
| Runtime correctness | The test itself runs (no parsing bug here — `field_rep` is used directly). Reproducing the notebook's formula from `exceptions.csv` + `stores.csv`, the reps with p < 0.05 and lift > 1.0 are: **Nora Smith** (47 obs, exp 21.2, p ≈ 0.0000), **Lara Ortiz** (39 obs, exp 24.8, p ≈ 0.005), **Chris Vega** (19 obs, exp 10.6, p ≈ 0.013), **Ivan Petrov** (14 obs, exp 7.1, p ≈ 0.014). The notebook's Markdown cell 8 names "Nora Smith" as the 1.9× significant rep, and the Action Framework cell lists the count of flagged reps generically. The 4-rep result is consistent with the 4 `field_rep_workload` insight rows (Nora Smith, Ivan Petrov, Lara Ortiz, Chris Vega). |
| Verdict | **Count-data assumption is satisfied but not documented in code. The mean=variance assumption is violated (overdispersion, ratio ≈ 7.4) and is neither checked nor mentioned. Conclusion direction is robust, but the Poisson p-values are anti-conservative under this overdispersion.** |

---

## 4. Tests the task asked for but not present

| Test type | Present in notebook? |
|---|---|
| ANOVA | Yes — 2 |
| t-test (any flavor) | **None.** No `ttest_1samp`, `ttest_ind`, `ttest_rel`, or `t_test` anywhere. The markdown at cell 1 lists "ANOVA" and "Chi-square tests" under Layer 2 method, but no t-test is used. |
| Chi-square | Yes — 8 (6 hotspot, 2 mismatch). |
| Poisson | Yes — 1 (vectorized over 16 reps). |
| Kruskal–Wallis (non-parametric ANOVA analog) | Yes — 2 (run alongside each ANOVA). Not strictly requested but worth noting as the only mitigation present. |

---

## Per-test assumption scorecard

| # | Test | Cell | Shapiro–Wilk run? | Levene run? | Expected ≥ 5 checked? | Count/dispersion documented? |
|---|---|---|---|---|---|---|
| 1 | ANOVA store_format | 4 | no | no | n/a | n/a |
| 2 | ANOVA region | 5 | no | no | n/a | n/a |
| 3 | χ² hotspot North low sell-through | 6 | n/a | n/a | no (degenerate: 0/0) | n/a |
| 4 | χ² hotspot North overstock risk | 6 | n/a | n/a | no (degenerate: 0/0) | n/a |
| 5 | χ² hotspot East late photo proof | 6 | n/a | n/a | no (degenerate: 0/0) | n/a |
| 6 | χ² hotspot West stockout risk | 6 | n/a | n/a | no (degenerate: 0/0) | n/a |
| 7 | χ² hotspot East late confirmation | 6 | n/a | n/a | no (degenerate: 0/0) | n/a |
| 8 | χ² hotspot West missing confirmation | 6 | n/a | n/a | no (degenerate: 0/0) | n/a |
| 9 | χ² quantity mismatch by DC | 8 | n/a | n/a | no (satisfied: min 47.0) | n/a |
| 10 | χ² quantity mismatch by carrier | 8 | n/a | n/a | no (satisfied: min 46.2) | n/a |
| 11 | Poisson field-rep over-index | 7 | n/a | n/a | n/a | count-data yes (implicit); mean=variance **no, violated (ratio ≈ 7.4)** |

---

## Highest-priority findings

1. **CRITICAL — Chi-square hotspot loop (Cell 6) is degenerate due to a string-mismatch bug.** `exc_type` is parsed from the human-readable headline ("low sell through") but matched against `exceptions.exception_type`, which uses underscores ("low_sell_through"). Every iteration sees 0 observations and 0 expected → `chisquare([0,0], f_exp=[0,0])` → `(nan, nan)`. None of the six regional "hotspot" p-values are real. The accompanying lift chart, the "Red = statistically significant" coloring, and the downstream "North region assortment deep-dive" action item (priority #3 in the Action Framework) rely on these values. If the bug were fixed, the expected counts all clear ≥ 5, but that fix has not been made in the notebook as shipped.

2. **HIGH — No ANOVA assumption checks (Cells 4 & 5).** No Shapiro–Wilk, no Levene. Kruskal–Wallis is the only mitigation and only covers the normality concern, not the homogeneity-of-variance concern. Group sizes are unbalanced (5, 8, 14, 57 stores; 18–24 per region), which makes the equal-variance assumption material.

3. **HIGH — Poisson overdispersion (Cell 7) unflagged.** Reconstructed counts show variance/mean ≈ 7.4. The Poisson p-values are therefore anti-conservative; a negative-binomial or a quasi-Poisson would be more honest. The count-data nature of the variable is obvious and satisfied, but the notebook doesn't say so.

4. **MEDIUM — No expected-count check printed for the quantity-mismatch chi-squares (Cell 8).** The assumption is actually satisfied (min expected ≈ 46–47), so no real violation — but it is never verified in code, only asserted in a prose table in the appendix.

5. **LOW — η² effect-size labels applied without checking ANOVA validity.** η² is computed from the ANOVA SS decomposition regardless of whether the ANOVA assumptions hold. Under the likely overdispersion and unequal variances, the η² magnitudes ("large"), and the "format-level structural risk" interpretation hanging off them, are overstated.

---

## Verification of acceptance criteria

1. Every ANOVA identified with cell number? **Yes** — Code cell 4 (format), Code cell 5 (region).
2. For each ANOVA: Shapiro–Wilk run before? **No for both.**
3. For each ANOVA: Levene run before? **No for both.**
4. Every chi-square identified with cell number? **Yes** — 6 in Code cell 6 (hotspot loop), 2 in Code cell 8 (mismatch by DC and by carrier).
5. For each chi-square: expected cell counts verified ≥ 5? **No, not checked anywhere.** For the 6 hotspot tests the computation is degenerate (0/0). For the 2 mismatch tests the assumption is satisfied (min ≈ 46–47) but never computed or asserted in the notebook.
6. Every Poisson test identified with cell number? **Yes** — Code cell 7 (looped over 16 reps).
7. For the Poisson test: is the count-data assumption documented? **Partially** — stated in the prose appendix table but not verified in code; the mean=variance assumption is violated (~7.4×) and not mentioned.
8. Summary count present? **Yes** — see Summary counts table above.

### Verification floor from task body
- "At least 3 ANOVAs and 2 chi-square tests identified" — there are only 2 ANOVAs in the notebook (3 was an over-estimate by the task author); 8 chi-square tests identified (well above the floor of 2). The ANOVA count is a function of the notebook content, not of the audit; the audit correctly reports the 2 that exist.

---

## Important caveat

This audit is based on **static inspection** of the notebook source plus recomputation against the CSV data files, exactly as required by the Do-Not-Scope ("Do NOT modify the notebook", "Do NOT write code"). None of the notebook's outputs were re-executed inside the notebook itself, because that would require code execution and could mutate outputs. The reconstruction of chi-square values, Poisson p-values, and group sizes was done via independent scripts reading the same CSVs the notebook reads, so the conclusions above (especially the chi-square bug and the Poisson overdispersion) reflect what the notebook would produce if executed as written against the supplied data.