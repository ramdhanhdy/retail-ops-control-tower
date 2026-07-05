# Task: Retail Ops Control Tower — HTML Analytical Report

You are a senior data analyst and visual designer. Your task is to produce a
**single self-contained HTML file** that presents the full analytical findings
of a retail operations control tower project in a polished, stakeholder-friendly
format. This is a designed artifact, not a document.

## Project Background

A Python portfolio project simulates a multi-store coffee chain running a
seasonal LTO campaign. The project tracks campaigns from HQ planning through
store execution, allocation reconciliation, and exception management. All data is
simulated — no real company data is used.

The project has a complete pipeline: data generation (8 interlocking CSV
tables from a single seed), validation engine (9 data-quality rules),
exception engine (9 exception types with severity, priority, SLA, aging),
metrics layer (12 KPIs + area-manager scorecard). 327 tests pass.

The insight engine runs a four-layer statistical analysis over the exception
dataset, producing ranked, quantified findings. The statistics are correct and
final. Your job is to present them in a visually rich, professionally designed
HTML page.

## Design System

### Aesthetic
Dark minimal with tech undertones. Think Linear meets Vercel — a near-black
canvas where content emerges through subtle luminance steps, not color noise.

### Color
- Page background: `#08090a` (near-black, cool undertone)
- Panel/surface: `rgba(255,255,255,0.02)` to `rgba(255,255,255,0.05)` (translucent white over dark)
- Elevated surface: `#191a1b`
- Primary text: `#f7f8f8` (near-white, not pure white)
- Secondary text: `#d0d6e0` (silver-gray)
- Muted text: `#8a8f98`
- Subtle text: `#62666d`
- Border: `rgba(255,255,255,0.08)` (semi-transparent white, never solid dark)
- Subtle border: `rgba(255,255,255,0.05)`
- Accent: `#3b82f6` (blue-500) for interactive elements and data highlights
- Accent hover: `#60a5fa` (blue-400)
- Success: `#10b981` (emerald, sparingly for positive indicators)
- Warning: `#f59e0b` (amber, sparingly for caution)
- Danger: `#ef4444` (red, sparingly for critical)
- No pure black (`#000000`). No pure white (`#ffffff`) for text.

### Typography
- Sans: `Geist` with fallbacks to `system-ui, -apple-system, sans-serif`
- Mono: `Geist Mono` with fallbacks to `ui-monospace, monospace`
- Font loading: Google Fonts `<link>` for Geist + Geist Mono
- Display headings (48px+): weight 600, `letter-spacing: -2.4px`, `line-height: 1.0`
- Section headings (32px): weight 600, `letter-spacing: -1.28px`, `line-height: 1.2`
- Card titles (24px): weight 600, `letter-spacing: -0.96px`, `line-height: 1.33`
- Body (16px): weight 400, `line-height: 1.56`
- Small (14px): weight 400, `line-height: 1.50`
- Caption (12px): weight 500
- Mono labels (12px): weight 500, `text-transform: uppercase`, `letter-spacing: 0.05em`
- Three weights only: 400 (body), 500 (UI/labels), 600 (headings)
- OpenType features: `"liga"` on all text

### Layout
- Max content width: 1200px, centered
- Base spacing: 8px grid (8, 16, 24, 32, 48, 64, 80, 96, 120)
- Section vertical padding: 80px+ (generous whitespace)
- Cards: `rgba(255,255,255,0.02)` background, `1px solid rgba(255,255,255,0.08)` border, 8px radius
- Depth via background luminance steps, not shadows
- Shadow-as-border: `0px 0px 0px 1px rgba(255,255,255,0.08)` instead of CSS border where appropriate
- Asymmetric grids where content warrants it (not everything is a 3-column card grid)
- Section rhythm: vary layout families across sections — do not repeat the same card grid 4 times
- Hero: headline max 2 lines, subtext max 20 words, fits viewport without scroll

### Components
- Metric cards: large number (Geist 48px weight 600), label below (14px weight 500 muted), subtle border
- Data tables: no heavy borders, use `border-bottom: 1px solid rgba(255,255,255,0.05)` between rows, mono for numbers
- Pills/badges: `9999px` radius, tinted background, 12px weight 500
- Section dividers: `1px solid rgba(255,255,255,0.05)`, full width
- Charts: displayed in card containers with 12px radius, caption below
- Interactive: real hover states on cards (background opacity increase), real focus states
- Navigation: sticky top bar, `#0f1011` background, `1px solid rgba(255,255,255,0.05)` bottom border, 64px height
- Smooth scroll for anchor navigation
- `prefers-reduced-motion` respected for all transitions

### Anti-Patterns to Avoid
- No glassmorphism, no aggressive gradients, no neon glows
- No emoji in UI, no decorative SVG illustrations
- No generic SaaS card grids with icons everywhere
- No fake dashboards with arbitrary numbers
- No 3-column equal feature cards (use asymmetric, zigzag, or varied layouts)
- No em dashes (—) in visible text. Use regular hyphens (-) or commas
- No boldface overuse — bold only for genuine emphasis or table headers
- No significance inflation language ("pivotal moment," "underscores the importance of")
- No AI vocabulary: delve, tapestry, landscape (abstract), showcase, foster, seamless, robust
- No rule-of-three forcing, no "not just X, it's Y" constructions
- No signposting ("let's dive in," "here's what you need to know")
- No generic conclusions ("the future looks bright")
- No em dash overuse
- No title case in headings (use sentence case)

## Content Structure

The HTML page follows the Pyramid Principle — governing thought first, then
four analytical layers of progressively deeper evidence. Each section follows:
**Observation → Statistical Evidence → Business Interpretation → Recommended Action**

### 1. Hero / Executive Summary
- Governing thought in one paragraph with key numbers
- 6 key findings as compact metric cards:
  - 47/100 stores (47%) produce 80.3% of exceptions
  - Gini 0.459 (inequality where 0 = even, 1 = all in one store)
  - Store format is the dominant predictor (drive-thru 30.4 vs flagship 6.2)
  - No field rep is statistically significant after proper testing
  - 15 SKUs have rebalancing transfer candidates (ROI 12.4x)
  - $1,004,400 total operational exposure
- Data scope: 100 stores, 1,603 exceptions, 651 critical, 160 SLA breaches

### 2. Layer 1 — Concentration
- Pareto finding: 47 stores, 80.3% of exceptions
- Gini coefficient: 0.459, CI [0.400, 0.513]
- 16 stores with zero exceptions (included in analysis)
- Chart: `images/layer1_pareto_lorenz.png`
- Action: "Focus 47" watchlist for weekly diagnostic reviews

### 3. Layer 2 — Segmentation
- Store format: Kruskal-Wallis H=29.36, p=1.9e-6, effect size large
- Format means table: drive-thru 30.4, kiosk 29.6, standard 12.0, flagship 6.2
- Post-hoc: 4/6 pairs significant (Mann-Whitney + Holm)
- Drive-thru and kiosk statistically identical (treat as one risk class)
- Region: NOT significant (p=0.675)
- Charts: `images/layer2_format_boxplot.png`, `images/layer2_region_boxplot.png`
- Action: adjusted allocation and audit frequency for 25 drive-thru + kiosk stores

### 4. Layer 3 — Attribution
- Regional hotspots: 6 significant cells after BH-FDR
  - North overstock 1.52x, low sell-through 1.33x
  - South mirror under-index
  - 4 of 6 engine-flagged hotspots do NOT survive FDR
- Field reps: NO rep significant after permutation test (20,000 iterations)
  - Nora Smith: lift 1.93x but p-FDR=0.19 (withdrawn)
  - 46 exceptions at 13 rep-less stores were silently dropped before
- Quantity mismatch: uniform across DCs (p=0.782) and carriers (p=0.817) — systemic
- Charts: `images/layer3_hotspot_lift.png`, `images/layer3_fieldrep_lift.png`, `images/layer3_upstream_mismatch.png`
- Action: audit North assortment, fix data reconciliation layer, assign reps to 13 uncovered stores

### 5. Layer 4 — Opportunity
- Rebalancing: 15 SKUs, 64 touchpoints, ROI 12.4x
- SLA: 10.0% breach rate overall, ranges 0% to 100% by type
- Aging: 92.8% fresh, 3.9% aging, 3.3% overdue
- Financial: $1,004,400 exposure, $46,500 savings vs $3,750 cost
- Sensitivity: rankings robust (Spearman rho >= 0.960)
- Charts: `images/layer4_rebalancing.png`, `images/layer4_sla_breach.png`, `images/layer4_aging_profile.png`, `images/layer4_financial.png`, `images/layer4_sensitivity.png`
- Action: execute 15 transfers, prioritize by impact score

### 6. Action Framework
- Prioritized action table (6 items, sorted by impact)
- "Not recommended" section: no per-rep review, no volume-based region intervention

## Chart Images

Embed charts using relative paths. Each chart goes in a card container with a
caption explaining what the reader should see:

```
images/layer1_pareto_lorenz.png    — Pareto curve + Lorenz with Gini
images/layer2_format_boxplot.png   — Exception distribution by store format
images/layer2_region_boxplot.png   — Exception distribution by region
images/layer3_hotspot_lift.png     — Regional hotspot lift analysis
images/layer3_fieldrep_lift.png    — Field rep compliance lift
images/layer3_upstream_mismatch.png — Quantity mismatch by DC and carrier
images/layer4_aging_profile.png    — Aging bucket profile
images/layer4_financial.png        — Financial impact estimation
images/layer4_rebalancing.png      — Rebalancing opportunity
images/layer4_sla_breach.png       — SLA breach rate by exception type
images/layer4_sensitivity.png      — Sensitivity analysis on scoring
```

## Writing Standards

### Stakeholder-friendly communication

This report will be read by operations leaders, area managers, and campaign
coordinators — not statisticians. Write for them.

1. Lead with the business implication, not the statistical method. A
   stakeholder needs to know "drive-thru and kiosk formats generate 2.5x more
   exceptions" before they need to know "Kruskal-Wallis H=29.36, p=1.9e-6."
   State the finding in plain language first, then attach the statistical
   evidence as support.

2. Translate every statistical term on first use. "Gini coefficient of 0.459
   (a measure of inequality where 0 = perfectly even and 1 = all exceptions in
   one store)" — not just "Gini 0.459." After the first translation, the term
   can stand alone.

3. No p-values in topic sentences. They belong in the evidence section, not
   the opening line. "Store format is the strongest predictor of exception
   volume" is the finding. "Kruskal-Wallis H=29.36, p=1.9e-6" is the proof.

4. One number per sentence in prose. If a sentence has three statistics, split
   it or use a table.

5. Always answer "so what?" Every finding must connect to a decision or action.

6. Use active voice and concrete subjects. "Drive-thru stores generate 30
   exceptions on average" — not "exceptions are generated at a higher rate by
   the drive-thru format."

7. Flag uncertainty honestly but briefly. One clause, then move on.

8. Avoid analyst jargon. "Over-indexes" becomes "has a higher share than
   expected." "Lift" becomes "X times the baseline rate." "BH-FDR correction"
   becomes "after adjusting for false positives across 32 tests."

9. Recommended actions must be specific and owned. "Assign a dedicated task
   force to the 47 highest-exception stores for weekly diagnostic reviews" —
   not "consider targeted intervention."

### Anti-AI-slop writing rules

1. No significance inflation. No "marks a pivotal moment," "underscores the
   importance of," "serves as a testament to."
2. No -ing tacking. No "highlighting the need for...", "ensuring alignment..."
3. No AI vocabulary: delve, tapestry, landscape, showcase, foster, seamless,
   robust, comprehensive, pivotal, intricate, interplay, vibrant.
4. No copula avoidance. Use "is" and "are." Not "serves as," "stands as,"
   "represents a," "boasts."
5. No negative parallelisms or contrast inversions:
   - "It's not X, it's Y" / "It's not just X, it's Y"
   - "Not only X, but also Y" / "Less about X, more about Y"
   - "X, not Y" as a tail / "X rather than Y" / "X, no Y" clipped closers
   State what something is, directly. Use "but" or "however" for genuine contrast.
6. No rule-of-three forcing. Only group in threes when there are actually three.
7. No filler openers: "it is worth noting that," "in order to," "due to the
   fact that."
8. No generic conclusions: "the future looks bright," "exciting times ahead."
9. No signposting: "let's dive in," "here's what you need to know."
10. No fragmented headers (heading followed by one-line restatement).
11. Vary sentence rhythm. Mix short and long. Don't let every sentence have
    the same structure.
12. Have opinions. React to findings. "This is the single largest lever in the
    analysis" is better than "this finding is significant."
13. Be specific about feelings. Not "this is concerning" but "this is the kind
    of gap that compounds quietly until a campaign window closes."

## Deliverable

A single self-contained HTML file at `docs/analytical_report.html` with:
- All CSS embedded in `<style>` tags
- All JS embedded in `<script>` tags (minimal: smooth scroll, nav active state)
- Google Fonts loaded via `<link>` (Geist + Geist Mono)
- Chart images referenced via relative paths (`../images/layer1_pareto_lorenz.png`)
- Responsive behavior (mobile single-column, desktop multi-column)
- `prefers-reduced-motion` handling
- No external dependencies beyond Google Fonts and the chart images
- Navigation: sticky top bar with section anchors
- Print-friendly (charts and text render properly in print)

## Working Directory

```
/opt/data/projects/retail-ops-control-tower/
```

Read the chart images in `images/`, the data exports in `data/insight_exports/`,
and the existing Indonesian narrative in `docs/insight_engine_story.md` for
reference. Write the HTML file to `docs/analytical_report.html`.
