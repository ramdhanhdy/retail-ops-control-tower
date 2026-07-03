# Portfolio and CV Relevance Judge Report

**Task:** T19 - Judge portfolio and CV relevance
**Date:** 2026-07-03
**Project:** Retail Operations Control Tower
**Verdict:** FAIL

---

## Summary

The project is directionally strong for the Tomoro ops-adjacent CV strategy: it is clearly framed as simulated-data portfolio work, it fits a tech-forward data and workflow analyst narrative, and it maps well to workflow tracking, allocation/campaign monitoring, reporting, stakeholder follow-up/action lists, dashboarding, and validation/reconciliation.

However, the portfolio/CV package should not pass final positioning yet because `artifacts/cv-bullets-id.md` contains a stale test-count claim of 281 tests while the verified project count is 327, and the CV project title differs from the README project title. `artifacts/demo-checklist.md` also contains the stale 281-test count. These are small but exact misleading/inconsistent artifact issues that should be fixed before using the CV bullet.

---

## Fact-check results

| Claim | Source | Status | Notes |
|---|---|---|---|
| Project uses simulated data only and claims no real company data, internal knowledge, or real-world retail ops experience | `README.md:8-9`, `README.md:358-363`, `artifacts/portfolio-summary.md:10-11`, `artifacts/cv-bullets-id.md:3-4` | PASS | Clear and repeated disclosure. |
| Project is not positioned as ops-specialist experience | `README.md:338-342`, `artifacts/portfolio-summary.md:15-18` | PASS | Wording explicitly says tech-forward data and workflow analyst, not operations specialist. |
| README does not claim real Tomoro data or internal knowledge | `README.md`, search results for Tomoro | PASS | README does not mention Tomoro. Other scope docs explicitly prohibit real Tomoro data or systems. |
| README says source install only and no PyPI package | `README.md:197-200`, `README.md:383` | PASS | Safe. No `pip install retail-ops-control-tower` claim found in README. |
| README says project is not on GitHub yet and publishing is gated | `README.md:384` | PASS | Matches global context. |
| README says 327 passing tests | `README.md:110-111`, `README.md:355-356`, `README.md:443`; parent T18 | PASS | Matches T18 verification: 327 tests pass. |
| CV bullets are in Indonesian | `artifacts/cv-bullets-id.md` | PASS | Body copy and notes are Indonesian. English technical terms are acceptable for CV context. |
| CV bullets use an English project title | `artifacts/cv-bullets-id.md:10`, `artifacts/cv-bullets-id.md:20`, `artifacts/cv-bullets-id.md:33` | PARTIAL | Title is English, but it is `Retail Campaign & Store Allocation Control Tower`, not the README/project title `Retail Operations Control Tower`. This may confuse attribution. |
| CV bullet test count is accurate | `artifacts/cv-bullets-id.md:26`; parent T18 | FAIL | It says 281 tests passed. Verified count is 327. |
| Demo checklist test count is accurate | `artifacts/demo-checklist.md:173`, `artifacts/demo-checklist.md:212`; parent T18 | FAIL | It says 281 tests passed. Verified count is 327. |
| Project maps to workflow tracking | `README.md:54-83`, `artifacts/portfolio-summary.md:76-94` | PASS | Exception engine, SLA, aging buckets, and action list support this. |
| Project maps to allocation/campaign monitoring | `README.md:54-83`, `reports/weekly_ops_report.md:52-112` | PASS | Campaign readiness and allocation reconciliation are core report sections. |
| Project maps to reporting | `README.md:81-83`, `reports/weekly_ops_report.md`, `artifacts/portfolio-summary.md:110-123` | PASS | 8-section weekly report and executive summary are generated. |
| Project maps to stakeholder follow-up/action list | `README.md:78-80`, `reports/weekly_ops_report.md:156-231` | PASS | AM follow-up list and top recommended actions are explicit. |
| Project maps to dashboarding | `README.md:107-109`, `artifacts/portfolio-summary.md:125-137` | PASS | Streamlit dashboard is documented with filters and KPI sections. |
| Project maps to validation/reconciliation | `README.md:72-77`, `reports/judge-technical-report.md:76-98` | PASS with caveat | Validation is implemented. Reconciliation is partly covered by validation and exception logic, while the standalone reconciliation package is a documented stub per T18. Do not overclaim a full 16-formula/24-rule reconciliation engine. |
| Project can be explained in 60 seconds | README and portfolio summary | PASS | A concise explanation is available from the README intro plus portfolio relevance section. |

---

## Thesis ratings

| Thesis | Rating | Reason |
|---|---|---|
| The project is safe to present as simulated-data portfolio work | strong | README, portfolio summary, CV bullets, reports, and scope docs repeatedly disclose synthetic data and deny real company/internal data. |
| The project supports a tech-forward data/workflow analyst CV strategy | strong | It demonstrates data simulation, validation, exception prioritization, SLA tracking, KPI reporting, Streamlit dashboarding, and tested Python implementation. |
| The project should be framed as retail operations specialist experience | false | The project explicitly says it is not real-world retail ops experience. This framing would be misleading. |
| The project maps to Tomoro-relevant operations-adjacent themes | strong | It covers workflow tracking, campaign/allocation monitoring, reporting, action lists, dashboarding, and validation/reconciliation. |
| The README is safe for publication from a claims perspective | strong | No real-data, PyPI, GitHub-published, production-ready, or ops-specialist overclaims found. |
| The CV artifacts are ready to use without edits | weak | They are mostly safe, but one CV option has a stale 281-test count and the English project title does not match the project name. |
| The project can be pitched in 60 seconds | strong | The scope and value proposition can be stated clearly without claiming real operations experience. |

---

## Overclaims or unsafe inaccuracies found

- `artifacts/cv-bullets-id.md:26` says `281 unit dan integration test lulus`, but T18 verified 327 tests. This is an inaccurate CV artifact claim.
- `artifacts/demo-checklist.md:173` and `artifacts/demo-checklist.md:212` also say 281 tests, but T18 verified 327 tests.
- `artifacts/cv-bullets-id.md` uses `Retail Campaign & Store Allocation Control Tower` as the title, while the README/project title is `Retail Operations Control Tower`. This is not a factual overclaim, but it weakens consistency and should be aligned before use.
- Avoid saying the standalone reconciliation engine is fully complete. T18 found the `reconciliation/` package is a documented stub; the safe claim is that validation and exception logic compute planned-vs-actual variances and reconciliation-style checks.

---

## Blind spots

- This judge reviewed documentation and parent technical verification, not a fresh full `pytest` or smoke run. T18 already performed the technical verification and reported 327 passing tests.
- Dashboard usability was judged from README/artifact descriptions and T18 compile/import checks, not a live browser walkthrough.
- Tomoro fit was judged against the provided strategy, not against a live job description or recruiter feedback.
- Indonesian CV tone is acceptable, but a native Indonesian reviewer could further polish wording for naturalness and ATS fit.

---

## Required edits before PASS

1. In `artifacts/cv-bullets-id.md`, replace the stale test-count phrase on line 26:
   - Current: `281 unit dan integration test lulus.`
   - Required: `327 unit dan integration test lulus.`

2. In `artifacts/demo-checklist.md`, replace both stale test-count references:
   - Line 173 current: `Semua test lulus (281 passed)`
   - Line 173 required: `Semua test lulus (327 passed)`
   - Line 212 current: `` `pytest -q` (tunjukkan 281 test lulus) ``
   - Line 212 required: `` `pytest -q` (tunjukkan 327 test lulus) ``

3. In `artifacts/cv-bullets-id.md`, align the English project title with the README project title unless there is a deliberate branding reason not to:
   - Current: `Retail Campaign & Store Allocation Control Tower`
   - Recommended: `Retail Operations Control Tower`

4. In any CV/portfolio copy, prefer this safe wording for reconciliation:
   - Safe: `validasi data dan planned-vs-actual reconciliation checks`
   - Avoid: `full reconciliation engine 16 formula dan 24 rule` unless that standalone scope is implemented.

---

## Safe claims

Claims the project can safely make after the required edits:

- This is a simulated-data portfolio project, not real Tomoro or real company operations work.
- It demonstrates a tech-forward data and workflow analyst skill set using Python and Streamlit.
- It models multi-store retail campaign execution using synthetic coffee-chain data.
- It includes deterministic sample data across 8 tables.
- It performs 9-rule data validation and planned-vs-actual variance checks.
- It detects 9 exception categories and generates a priority-ranked action list with severity, SLA status, owner, and recommended action.
- It computes 12 KPIs and an area-manager scorecard.
- It renders a Streamlit dashboard and an 8-section weekly operations report.
- It has 327 passing tests, based on T18 verification.
- It is installed from source and is not published to PyPI.

---

## Unsafe claims

Claims the project should NOT make:

- That it uses real Tomoro data, real store data, internal systems, or internal operational knowledge.
- That it proves real-world retail operations specialist experience.
- That it is production-ready.
- That it is published to GitHub before T21 approval.
- That `pip install retail-ops-control-tower` works from PyPI.
- That the standalone reconciliation package fully implements the complete 16-formula/24-rule reconciliation engine unless that is later built and verified.
- That the test count is 281.

---

## Recommended final CV bullet after edits

Retail Operations Control Tower
Mengembangkan portfolio project berbasis data simulasi untuk memodelkan workflow campaign dan store allocation pada jaringan retail multi-store, mencakup data validation, planned-vs-actual reconciliation checks, exception handling dengan severity dan SLA tracking, dashboard KPI Streamlit, priority-ranked action list, dan weekly management report menggunakan Python. Semua data bersifat simulasi dan tidak mengklaim pengalaman operasional nyata.

---

## 60-second interview explanation

Retail Operations Control Tower adalah portfolio project Python berbasis data simulasi. Saya memodelkan campaign execution untuk jaringan coffee retail multi-store, mulai dari allocation plan, dispatch, store confirmation, photo proof, sampai daily sales. Pipeline ini melakukan data validation, planned-vs-actual variance checks, exception detection, priority scoring, SLA tracking, dan menghasilkan action list untuk follow-up area manager. Output akhirnya berupa 12 KPI, scorecard, dashboard Streamlit, dan weekly operations report. Project ini saya posisikan sebagai bukti kemampuan data workflow engineering dan decision-support dashboarding, bukan klaim pengalaman operasional nyata atau akses ke data perusahaan.

---

## Acceptance result

**FAIL pending artifact edits.** The project strategy is sound, but the CV/demo artifacts need the exact corrections above before the portfolio/CV package should be approved.

## Verification

- Read and checked `README.md`.
- Read and checked parent report `reports/judge-technical-report.md`.
- Read and checked `artifacts/cv-bullets-id.md`.
- Read and checked `artifacts/portfolio-summary.md`.
- Read and checked `artifacts/demo-checklist.md`.
- Read sample generated report `reports/weekly_ops_report.md`.
- Checked common publishable docs for em dash/en dash characters: none found in README, CV bullets, portfolio summary, demo checklist, or weekly report.
- Confirmed output path: `reports/judge-portfolio-report.md`.
