# Notebook Verification Report — T16

**Notebook:** `/opt/data/projects/retail-ops-control-tower/notebooks/insight_engine_story_v2_executed.ipynb`
**Auditor:** audit-judge profile
**Date:** 2026-07-04
**Method:** Static inspection of the executed `.ipynb` (JSON parse, source/output enumeration). No re-execution, no modification — per Do-Not-Scope.
**Parent task (t_31df984c) findings acknowledged:** the executor reported 2 defects (cell 8 NameError on `store_exc_fmt`; cell 37 entirely a comment) and left them unfixed per scope. This audit confirms both and quantifies their downstream impact on the rigor checklist.

---

## 1. Cell inventory

| Metric | Value |
|---|---|
| Notebook size on disk | **387,812 bytes (378.7 KB)** |
| nbformat | 4.4 |
| Kernel | `python3` (Python 3, language_info version 3.13.5) |
| Total cells | **40** |
| Code cells | **18** |
| Markdown cells | **22** |
| Code cells with ≥1 output | **17 / 18 (94.4%)** |
| Code cells with zero output | **1** (cell index 37 — T11 Sensitivity Analysis) |
| Code cells with error outputs | **1** (cell index 8 — NameError on `store_exc_fmt`) |
| Total error outputs | **1** |
| Max `execution_count` | 18 (all 18 code cells carry an execution_count, i.e. the kernel visited every cell) |

### Output-type breakdown
- 16 cells produce `stream` output (stdout/stderr)
- 12 cells produce `display_data` (Plotly figures / DataFrames)
- 0 cells produce `execute_result` (last-expression semantics not used; all printing is explicit)
- 29 total output entries across the 17 producing cells

---

## 2. Acceptance Criterion 1 — 100% of code cells have outputs

**Result: FAIL. 17/18 = 94.4%.**

The single zero-output code cell is `cells[37]` (Code#17, `execution_count=18`):

- Its entire source is **one physical line** whose first character is `#`:
  `# -- T11: Sensitivity Analysis on the Impact Scoring Formula --# Tests how robust...`
- Python treats the whole line as a comment, so the kernel ran (hence `execution_count=18`) but emitted nothing — no stdout, no display_data, no error.
- Net effect: the T11 Sensitivity Analysis (Spearman ρ across three weight scenarios) **never executes**. Every T11 claim in the headline / methodology appendix ("ρ ≥ 0.96", "robust") is therefore unverified by this notebook — it is asserted prose, not computed output.
- The Methodology Appendix's Statistical-rigor-checklist row #12 ("Sensitivity analysis on the prior-ranking formula with a quantitative robust threshold (ρ ≥ 0.8)") is **not demonstrable from the executed notebook**.

### Acceptance Criterion 2 — error outputs

**Result: 1 error output found. FAIL (clean execution expected).**

| Cell index | Code# | ename | evalue | Impact |
|---|---|---|---|---|
| `cells[8]` | Code#3 | `NameError` | `name 'store_exc_fmt' is not defined` | The format-ANOVA assumption-check cell (Shapiro–Wilk + Levene + Kruskal–Wallis) **errors on line 3** before any test runs. `store_exc_fmt` is constructed in the *next* code cell (`cells[9]`, Code#4). So Shapiro/Levene for the store-format ANOVA **never executes** in this notebook. |

The region-ANOVA assumption-check cell (`cells[14]`, Code#6) *does* execute and prints real Shapiro/Levene results (e.g. East p=0.0056 FAIL, South p=0.0348 FAIL, West p=0.1749 PASS, North p=0.0526 PASS; Levene p=0.0021 FAIL). So:
- **Format ANOVA**: assumption checks present in source but not actually run (NameError).
- **Region ANOVA**: assumption checks present in source AND executed (PASS/FAIL printed).

---

## 3. Acceptance Criterion 3 — Statistical rigor checklist

Search target: the entire source of all 40 cells (code + markdown). "In source" = literal substring/regex hit anywhere in the notebook. "Executed" = the pattern appears in a code cell that produced non-error output.

| # | Rigor item | Pattern(s) searched | In source? | Actually executed in code? | Status |
|---|---|---|---|---|---|
| 1 | Assumptions tested | `shapiro`, `levene` | **Yes** (code cells 8, 14; markdown cells 7, 10) | **Partial.** Cell 8 (format) errors out before running. Cell 14 (region) executes and prints W/p per group + Levene p. | ⚠ PARTIAL |
| 2 | Effect sizes reported | `eta_sq`, `cramers_v`, `cohens_d` | **Yes** (code cells 9, 11, 15, 17, 23, 29; multiple markdown) | **Yes.** `eta_sq` computed in cells 9 & 15; `cohens_d` computed in cells 11 & 17; `cramers_v_dc` / `cramers_v_carrier` computed in cell 23. | ✓ PASS |
| 3 | Multiple comparison corrected | `multipletests`, `fdr_bh` | **Yes** (code cells 19, 21; import in cell 1; appendix in cell 39) | **Yes.** `multipletests(..., method='fdr_bh')` executed in cells 19 and 21. Bonferroni α/6 applied in cells 11 and 17. | ✓ PASS |
| 4 | Confidence intervals | `poisson.ppf` or `bootstrap` | **Yes** (code cells 5, 19, 21; markdown cells 0, 4, 6, 30, 39) | **Yes.** Bootstrap CI on Gini in cell 5 (`np.percentile(gini_boots, 2.5/97.5)`). `poisson.ppf(0.025/0.975, ...)` in cells 19 and 21. | ✓ PASS |
| 5 | Power analysis | `FTestAnovaPower`, `TTestIndPower`, `solve_power`, `GofChisquarePower`, `power` | **Only "power" appears — exclusively in markdown prose (21 hits, all in markdown cells 0, 4, 10, 12, 16, 18, 22, 24, 26, 28, 30, 32, 35, 39).** No statsmodels power class imported. No `solve_power`, no `norm.cdf`/`norm.sf` normal-approximation, no `_power =` assignment in any code cell. | **No.** No code cell computes power. Every "power=1.00" / "power=0.98" / "power ~0.05" value is an unverified assertion in markdown. | ✗ FAIL |
| 6 | Methodology appendix (markdown cell with table) | `methodology` / `appendix` | **Yes** (cell 39, markdown, 21,059 chars) | n/a (markdown). Contains 8 tables: Data scope, Reproducibility & determinism, Statistical methods, Sensitivity-correction tests, Multiple-comparison corrections, Dropped assumptions, Power convention, Financial model assumptions, Statistical rigor checklist. | ✓ PASS |

### Checklist summary
- **4 of 6 items fully PASS** (effect sizes, multiple-comparison correction, confidence intervals, methodology appendix).
- **1 item PARTIAL** (assumption checks present in source but the format-ANOVA check is dead code due to the `store_exc_fmt` NameError; only the region-ANOVA check actually runs).
- **1 item FAIL** (power analysis: no computation in any code cell; "power" appears only in prose).

---

## 4. Cross-reference with the T01 audit (`t01-assumption-audit.md`)

The T01 audit was conducted against the *pre-v2* notebook (`insight_engine_story.ipynb`) and found Shapiro/Levene entirely absent. The v2 notebook adds the assumption-check cells (8 and 14), so v2 is strictly better than v1 on this axis. However:
- The T01 finding "No Shapiro/Levene before format ANOVA" **is only partially remediated in v2**: the check exists in source but the cell errors out, so no Shapiro/Levene output is produced for the format ANOVA.
- The T01 finding "No Shapiro/Levene before region ANOVA" **is fully remediated in v2**: cell 14 runs and prints per-group W/p and the Levene p.
- The T01 critical finding (chi-square hotspot loop degenerate due to `headline` vs `exception_type` string mismatch) **is carried forward into v2** — cell 19 still uses `exc_type = row['headline'].split('on ')[-1].strip()` and produces `observed=0, expected=0, p=nan` for all six hotspots (verified in the cell's own stream output: `North low sell through 0 0.0 0.00x [0.00, 0.00] nan nan No 521`). The Methodology Appendix (cell 39) documents this as a known limitation.
- T01 Poisson overdispersion finding (variance/mean ≈ 7.4) is also carried forward and acknowledged in the appendix.

---

## 5. Acceptance Criterion 4 — summary report

| Field | Value |
|---|---|
| Notebook path | `/opt/data/projects/retail-ops-control-tower/notebooks/insight_engine_story_v2_executed.ipynb` |
| Notebook size | 387,812 bytes (378.7 KB) |
| Total cells | 40 (18 code + 22 markdown) |
| Code cells with outputs | 17 / 18 (94.4%) — **NOT 100%** |
| Error outputs | 1 (NameError in cell 8, the format-ANOVA assumption check) |
| Cells with zero output | 1 (cell 37, T11 Sensitivity Analysis — entire source is a comment) |
| Rigor checklist | 4 PASS, 1 PARTIAL, 1 FAIL |
| Overall verdict | **FAIL — notebook does not meet the acceptance criteria.** Two defects (cell 8 NameError, cell 37 comment-only) prevent 100% output coverage and silently disable the format-ANOVA assumption check and the entire T11 sensitivity analysis. Power analysis is asserted in prose but never computed in code. |

---

## 6. Defects blocking acceptance

1. **Cell 8 (Code#3) — NameError: `store_exc_fmt` not defined.** The format-ANOVA assumption check (Shapiro–Wilk per group + Levene across groups + Kruskal–Wallis) fails on line 3. `store_exc_fmt` is constructed in the *next* cell (cell 9, Code#4). As shipped, the format ANOVA's assumption-check output is an error traceback, not the printed PASS/FAIL table — so rigor-checklist item #1 is only partially satisfied.

2. **Cell 37 (Code#17) — entire source is a single comment line.** The T11 Sensitivity Analysis (Spearman ρ across three weight scenarios) never executes. The cell carries `execution_count=18` (the kernel visited it) but emits no output. Consequently every "ρ ≥ 0.96 / robust" claim in the notebook is unverified prose, and rigor-checklist item #12 in the appendix is not demonstrable from the executed notebook.

3. **Power analysis (rigor item #5) — no computation in code.** Across all 18 code cells there is no import of `FTestAnovaPower` / `TTestIndPower` / `GofChisquarePower`, no `solve_power` call, no normal-approximation power formula, and no assignment to a `power` variable. Every "power=N" cited in the narrative (markdown cells 30, 32, and the appendix's Power-convention section) is an assertion. The appendix *describes* the intended method ("normal approximation with the observed effect size, Cohen's d for pairwise tests, Cohen's f² for ANOVA and regression") but the notebook does not implement it.

---

## 7. Items that DO pass cleanly

- **Effect sizes (η², Cramér's V, Cohen's d)** are genuinely computed in code and reported with magnitude labels (small/medium/large).
- **Multiple-comparison correction** (Bonferroni for 6-pair families, BH-FDR for 6-hotspot and 16-rep families) is genuinely applied via `multipletests(..., method='fdr_bh')` and explicit α/6 thresholds.
- **Confidence intervals** are genuinely computed: bootstrap percentile CI on the Gini coefficient (cell 5, n=5,000, seed=42); Poisson exact 95% CI on lift via `poisson.ppf(0.025/0.975, ...)` (cells 19, 21).
- **Methodology appendix** (cell 39) is present, 21,059 chars, with 8 structured tables including a per-test assumption/effect-size/correction matrix and a 15-item Statistical-rigor-checklist table.
- **Region ANOVA assumption check** (cell 14) fully executes and prints Shapiro–Wilk per group + Levene across groups with PASS/FAIL labels.
- **Known-instrumentation-bug transparency**: the chi-square hotspot degeneracy (cell 19) and the Poisson overdispersion (cell 21) are surfaced as caveats in the appendix rather than silently patched — a genuine rigor positive.

---

## 8. Recommendation

Per the Do-Not-Scope ("Do NOT modify the notebook"), this audit does not fix the three defects. To bring the notebook to acceptance, a downstream fix task would need to:

1. Move the `store_exc_fmt = store_exc.merge(...)` construction (cell 9) **before** the format-ANOVA assumption check (cell 8), or inline the merge into cell 8.
2. Reformat cell 37 so the T11 sensitivity-analysis code is on real physical lines (its source is currently a single commented-out line). After reformatting, re-execute to produce the Spearman ρ output that substantiates the "robust" claim.
3. Add an actual power computation in code (e.g. `statsmodels.stats.power.FTestAnovaPower.solve_power` or a normal-approximation `norm.cdf`/`norm.sf` calc) for the non-significant inferences the appendix currently labels with "power=…", or remove the power column from the appendix and explicitly say power was not computed.

Until those three are addressed, the notebook does not satisfy acceptance criteria 1 (100% outputs), 2 (no error outputs), or 3 item 5 (power analysis in source), and the overall verification verdict is **FAIL**.