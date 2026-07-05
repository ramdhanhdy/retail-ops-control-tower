# Task: Retail Ops Control Tower — Professional Analytical Report

You are a senior data analyst and visual storyteller. Your task is to produce
a **single polished analytical report** from a retail operations control tower
project. The report must be professional, well-written, and visually rich —
suitable for a portfolio piece or a stakeholder presentation.

## Background

A Python portfolio project simulates a multi-store coffee chain running a
seasonal LTO campaign. The project tracks campaigns from HQ planning through
store execution, allocation reconciliation, and exception management. All data is
simulated — no real company data is used.

The project has a complete pipeline: data generation (8 interlocking CSV
tables from a single seed), validation engine (9 data-quality rules),
exception engine (9 exception types with severity, priority, SLA, aging),
metrics layer (12 KPIs + area-manager scorecard), and a Streamlit dashboard.
327 tests pass.

A prior agent rebuilt the analytical engine from a flawed V2
notebook. It produced modular Python scripts, chart PNGs, structured data
exports, and an Indonesian markdown narrative. That work is done and committed.
Your job is NOT to redo the analysis — the statistics are correct and final.
Your job is to **read the charts, understand the data, and write a better,
single-file report** that surpasses the existing markdown narrative in
professional quality, visual integration, and analytical depth.

## What You Have Access To

### Chart images (in `images/` directory)
1. `layer1_pareto_lorenz.png` — Pareto curve + Lorenz curve with Gini coefficient
2. `layer2_format_boxplot.png` — Exception distribution by store format (ANOVA/Kruskal-Wallis)
3. `layer2_region_boxplot.png` — Exception distribution by region
4. `layer3_hotspot_lift.png` — Regional hotspot lift analysis (binomial + BH-FDR)
5. `layer3_fieldrep_lift.png` — Field rep compliance lift (permutation test)
6. `layer3_upstream_mismatch.png` — Quantity mismatch by DC and carrier (chi-square)
7. `layer4_aging_profile.png` — Aging bucket profile (fresh/aging/overdue/chronic)
8. `layer4_financial.png` — Financial impact estimation (illustrative)
9. `layer4_rebalancing.png` — Rebalancing opportunity (stockout + overstock matches)
10. `layer4_sla_breach.png` — SLA breach rate by exception type
11. `layer4_sensitivity.png` — Sensitivity analysis on impact scoring formula

### Structured data exports (in `data/insight_exports/`)
- `layer1_concentration.json` — Gini, Pareto, bootstrap CI, top-5 stores
- `layer1_store_ranking.csv` — All 100 stores ranked by exception count
- `layer2_format.json` — Format ANOVA + Kruskal-Wallis + assumption checks + descriptives
- `layer2_format_posthoc.csv` — Pairwise Mann-Whitney with Holm correction
- `layer2_region.json` — Region ANOVA + Kruskal-Wallis + assumption checks
- `layer2_region_posthoc.csv` — Pairwise region comparisons
- `layer3_attribution.json` — Field rep permutation test, upstream chi-square, hotspot family
- `layer3_hotspots.csv` — 32-cell hotspot table with lift, CI, p-values, FDR significance
- `layer3_field_reps.csv` — 16 field reps with lift, permutation p-values, FDR
- `layer4_opportunity.json` — Rebalancing, SLA, aging, financial, sensitivity summary
- `layer4_rebalancing.csv` — Transfer candidates per campaign
- `layer4_sla_by_type.csv` — SLA breach rates with Wilson CIs per exception type
- `layer4_sensitivity.csv` — Impact score reconstruction + 3 scenarios + Spearman rho

### The existing Indonesian narrative (for reference, not for copying)
`docs/insight_engine_story.md` (547 lines) — Fable's Indonesian markdown story.
Read it to understand the analytical structure and the V2 corrections, but
your report should be a fresh, superior take.

### Portfolio summary (for project context)
`artifacts/portfolio-summary.md` — project overview, tech stack, what was built,
sample results, and positioning.

## Key Findings (Verified — Use These Numbers)

These are the **corrected** statistics from the rebuilt engine:

### Concentration (Layer 1)
- 100 stores, 1,603 exceptions (9 types), 651 critical (40.6%), 160 SLA breaches (10.0%)
- 16 stores have zero exceptions (V2 wrongly excluded them)
- Pareto: 47/100 stores (47%) produce 80.3% of exceptions
- Gini (full fleet): 0.459, 95% CI [0.400, 0.513] (10,000 bootstrap)
- Gini excluding zero-exception stores: 0.356 (this was V2's error — understated)
- Top 5: S-011 (55), S-037 (55), S-058 (51), S-092 (46), S-018 (44)

### Segmentation (Layer 2)
- **Store format** is the dominant predictor: Kruskal-Wallis H=29.36, p=1.9e-6, ε²=0.275 (large)
- Format means: drive-thru 30.4 · kiosk 29.6 · standard 12.0 · flagship 6.2 exceptions/store
- Drive-thru and kiosk are statistically indistinguishable (p=0.977) — treat as one risk class
- 4/6 format pairs significant after Holm correction (rank-biserial 0.67-0.75, Cohen's d 1.68-1.92)
- **Region** is NOT a significant predictor of total exception volume: KW p=0.675, ε²≈0
- Power for region test (medium effect): 0.52 — underpowered, so absence of significance is not proof of absence

### Attribution (Layer 3)
- **Regional hotspots** (binomial exact + BH-FDR over 32-cell family): 6 significant cells
  - North over-indexes on overstock (1.52×, p-FDR=5.7e-5) and low sell-through (1.33×, p-FDR=7.1e-5)
  - South mirror-image under-indexes on both (overstock 0.32×, low sell-through 0.76×)
  - 4 of 6 engine-flagged hotspots do NOT survive FDR correction
- **Field reps** (store-level permutation test, 20,000 permutations + BH-FDR): NO rep is significant
  - Nora Smith: lift 1.93×, p-FDR=0.19 (V2 claimed p-FDR=0.0005 — withdrawn)
  - Overdispersion var/mean=3.6 at store level — Poisson test was invalid
  - 46 compliance exceptions at 13 rep-less stores were silently dropped by V2
- **Quantity mismatch** is uniformly distributed across DCs (χ² p=0.782, V=0.041) and carriers (p=0.817, V=0.037) — systemic, not vendor-specific

### Opportunity (Layer 4)
- **Rebalancing**: 15 SKUs across 3 campaigns have simultaneous stockout + overstock → transfer candidates, 64 store-campaign touchpoints
- **SLA breaches**: rate 10.0% overall (Wilson CI [8.6%, 11.5%]); ranges 0% (low sell-through, overstock, stockout) to 100% (unresolved issue SLA breach)
- **Aging profile**: 92.8% fresh (0-5 days), 3.9% aging (6-15), 3.3% overdue (16-30), 0% chronic
- **Financial** (illustrative): total exposure $1,004,400; rebalancing savings $46,500 vs cost $3,750 (ROI 12.4×)
- **Sensitivity**: impact score rankings robust (Spearman ρ≥0.960, p<10⁻⁷); INS-001 through INS-004 consistently top-4 across all scenarios

### V2 Corrections (6 issues found and fixed)
1. Zero-exception stores excluded (84→100 stores, Gini 0.356→0.459)
2. Hotspot chi-square zeros from headline parsing bug (rebuilt with binomial+BH-FDR)
3. Corrupted created_date (1423/1603 postdate aging snapshot; temporal trend removed)
4. Invalid Poisson field-rep test (overdispersion; no rep significant after permutation+FDR)
5. Financial model used nonexistent exception types (out_of_stock, damaged_shipment)
6. Methodology fixes (Mann-Whitney+Holm, ε² for KW, Wilson CIs actually computed)

## What to Produce

A **single markdown file** at `docs/analytical_report.md` that:

1. **Opens with a governing thought** — the single most important insight,
   stated in one paragraph, with the key numbers attached
2. **Follows the Pyramid Principle** — governing thought first, then four
   analytical layers of progressively deeper evidence
3. **Embeds chart images** using markdown image syntax with relative paths:
   ```markdown
   ![Caption describing what the chart shows](../images/layer1_pareto_lorenz.png)
   ```
4. **Each section follows**: Observation → Statistical Evidence (with numbers) →
   Business Interpretation → Recommended Action
5. **Reads like a professional analyst wrote it** — not an AI, not a textbook,
   not a listicle. Direct, confident, with stated confidence levels.
6. **Is self-contained** — a reader can follow the full analytical narrative
   by reading the markdown and viewing the charts, without needing to run
   any code

## Writing Standards

- **Language: English** (the existing Fable narrative is Indonesian; this is a
  separate English-language report for a broader audience)
- **Numbers: Exact** — use the verified statistics above, read from the data
  exports. Do not round unless the precision is noise
- **Charts: Embedded** — every chart must appear in the relevant section with
  a caption that explains what the reader should see in it
- **Tables: Use markdown tables** for structured comparisons (post-hoc pairs,
  financial breakdown, action framework)
- **Length: Comprehensive** — this is a full analytical report, not a summary.
  Each layer deserves substantial treatment. Target 3000-5000 words.
- **Structure: Varied section lengths** — don't make every section the same
  length. Some findings are more important and deserve more depth.
- **No filler** — every paragraph must contain substance. No "in conclusion,"
  no restating the intro, no padding.

### Communication style: stakeholder-friendly

This report will be read by operations leaders, area managers, and campaign
coordinators — not statisticians. Write for them.

- **Lead with the business implication, not the statistical method.** A
  stakeholder needs to know "drive-thru and kiosk formats generate 2.5x more
  exceptions" before they need to know "Kruskal-Wallis H=29.36, p=1.9e-6."
  State the finding in plain language first, then attach the statistical
  evidence as support — not the other way around.
- **Translate every statistical term on first use.** "Gini coefficient of
  0.459 (a measure of inequality where 0 = perfectly even and 1 = all
  exceptions in one store)" — not just "Gini 0.459." After the first
  translation, the term can stand alone.
- **No p-values in topic sentences.** They belong in the evidence paragraph,
  not the opening line. "Store format is the strongest predictor of exception
  volume" is the finding. "Kruskal-Wallis H=29.36, p=1.9×10⁻⁶" is the proof.
- **One number per sentence in prose.** If a sentence has three statistics,
  split it or use a table. Dense number-stew paragraphs are unreadable to
  non-analysts.
- **Always answer "so what?"** Every finding must connect to a decision or
  action. If the reader can't tell what to do after reading a section, the
  section failed.
- **Use active voice and concrete subjects.** "Drive-thru stores generate
  30 exceptions on average" — not "exceptions are generated at a higher rate
  by the drive-thru format."
- **Flag uncertainty honestly but briefly.** "Region is not a significant
  predictor, though the test was underpowered (power=0.52)" — one clause,
  then move on. Don't belabor methodological caveats.
- **Avoid analyst jargon.** "Over-indexes" → "has a higher share than expected."
  "Lift" → "X times the baseline rate." "BH-FDR correction" → "after
  adjusting for false positives across 32 tests." The stakeholder doesn't
  need to know the method name — they need to trust the result.
- **Recommended actions must be specific and owned.** "Assign a dedicated
  task force to the 47 highest-exception stores for weekly diagnostic reviews"
  — not "consider targeted intervention."

## Visual Quality

- You have **vision capabilities**. Read each chart image before writing about it.
- Your chart descriptions should reflect what the chart actually shows —
  not what you assume it shows based on the data alone.
- If a chart has a title, axis labels, or annotations, reference them in your
  narrative.
- If you notice something in a chart that the data exports don't capture
  (a visual pattern, an outlier, an asymmetry), mention it.

## Discretion

You have full discretion over:
- Report structure (as long as it follows the Pyramid Principle)
- Section headings and organization
- How much depth to give each finding
- What to emphasize vs. what to mention briefly
- Whether to include appendices
- Writing style and voice (within the professional analyst tone)

The only constraints are: English, single markdown file, embedded charts,
verified numbers, and the quality bar above.

## Working Directory

```
/opt/data/projects/retail-ops-control-tower/
```

Read the chart images in `images/`, the data exports in `data/insight_exports/`,
the existing Indonesian narrative in `docs/insight_engine_story.md`, and the
portfolio summary in `artifacts/portfolio-summary.md`. Then write the report to
`docs/analytical_report.md`.
