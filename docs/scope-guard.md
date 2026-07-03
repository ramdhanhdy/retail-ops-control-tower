# Scope Guard

> This document defines what is in scope and what is explicitly out of scope for the Retail Operations Control Tower portfolio project. It is intentionally short and strict. If a feature is not listed here as in scope, it is out of scope.

## In scope

1. Simulated data only. A synthetic coffee chain with 30-80 stores, 2-3 campaigns, 10-20 SKUs, field reps, visits, shipments, receipts, sales, and exceptions. All data is fictional.

2. Campaign execution tracking. The 39-field campaign execution tracker from T01, including visits, photo proof metadata, L1/L2/L3 audits, and compliance scores.

3. Allocation reconciliation. The 45-field allocation tracker from T02, the 4-quantity lifecycle (planned -> shipped -> received -> sold), and all 16 formulas (6 process compliance, 6 sales performance, 4 risk).

4. Exception engine. All 24 exception rules (EX-01 to EX-24) from T02, mapped to the 8-category taxonomy from T04. Severity scoring using the priority formula. SLA aging with 4 buckets. Exception lifecycle state machine. Daily action list generation. Root cause tagging. Reopen tracking.

5. KPI dashboard. 6 sections (executive tiles, area manager breakdowns, store status, campaign performance, exception backlog, SLA/aging). 10 MVP KPIs with threshold defaults. Drill-down from executive to area to store.

6. Demo story. A script or notebook that runs the "Summer Peach LTO 2026" scenario: campaign launches, some stores execute, some mismatch, dashboard surfaces what to fix, action list prioritizes the work.

7. Source install. The project is installed from source. No PyPI package. No claim that `pip install retail-ops-control-tower` works.

## Non-goals (explicitly out of scope)

1. No real Tomoro scraping. The project does not scrape, access, or reference Tomoro systems, data, or internal knowledge.

2. No real personal or business data. No real store locations, real sales figures, real customer data, or real employee information. All data is synthetic.

3. No deep learning forecasting. The project uses rule-based logic and deterministic formulas. No neural networks, no ML model training, no time-series forecasting models. Weeks-of-cover and risk flags are computed from formulas, not predictions.

4. No ERP clone. The project is not a full ERP. It does not attempt to replicate order management, warehouse management, financial accounting, HR, or procurement systems. It models the retail ops control-tower workflow only.

5. No authentication or user management. No login system, no user accounts, no role-based access control, no permissions. The dashboard is a single-user application. Role-based action list filtering is a v2 UI feature, not an auth system.

6. No cloud deployment unless trivial. The project runs locally. No Kubernetes, no Terraform, no cloud infrastructure. A Dockerfile for local development is acceptable if it simplifies setup. No CI/CD pipeline unless it is a single GitHub Action that runs tests.

7. No real photos or image processing. Photo proof records contain metadata (GPS, timestamp, user ID) but no actual images are stored or processed. No computer vision, no image recognition.

8. No real-time streaming. Data is generated in batches (daily or on-demand). No Kafka, no WebSocket streams, no event sourcing infrastructure.

9. No mobile app. The dashboard is a web application or notebook. No native mobile app, no React Native, no app store deployment.

10. No third-party API integrations. No calls to external retail APIs, weather APIs, mapping APIs, or payment APIs. All data is internally generated.

11. No publishing to GitHub. The project stays local. T21 is a separate approval gate for any publishing decision.

## Scope enforcement rules

- If a task or feature is not in the "In scope" list above, it requires explicit approval before implementation.
- If a research finding suggests a feature that conflicts with a non-goal, the non-goal wins. Example: T02 mentions WSSI views and transfer engines, but both are deferred per the synthesis.
- If the implementation grows beyond the 5 components defined in `docs/research/synthesis.md`, stop and re-read this document.
- The demo story in `docs/research/synthesis.md` is the acceptance scenario. If the project does not support that story, it is incomplete.
