# Retail Campaign Execution Research

> Scope: How multi-store retail teams execute campaigns from HQ planning through store readiness and proof submission. Synthesized from public sources (vendor blogs, trade articles, operations guides). No proprietary or real company data is used or implied. All data in the downstream portfolio project will be simulated.

## Practical workflow

The campaign execution lifecycle follows a closed-loop process from HQ strategy to field verification and corrective action. The steps below are synthesized from retail execution platforms (1Channel, FieldPie, GoSpotCheck/FORM), trade marketing guides (Archway, Shoplworks), and field operations playbooks (Xenia, Ocasta, Umbrex).

### Step 1: HQ Planning and Campaign Setup

Headquarters builds the go-to-market strategy and configures the campaign in the execution system. Configuration includes campaign name, campaign duration (start/end dates), validation rules, target store list, POSM (point-of-sale material) list, category, and deployment type. Trade marketing creates POP kits, display guides, and training materials. For coffee chains, this is where seasonal LTO (limited-time offer) drinks are finalized: Peet's gives store teams roughly eight months of lead time, Dutch Bros about six months, and Westrock up to a year for client brands. Recipe cards and training videos are produced at this stage.

### Step 2: Asset Production and Distribution

Trade marketing and logistics teams produce and distribute physical and digital assets: POSM kits (posters, standees, tent cards, signage, shelf branding), recipe cards, and digital training content. Assets are shipped to stores or distribution centers ahead of the launch window. Timing is critical: delays in delivering promotional materials cause missed launch opportunities, especially for seasonal and holiday events. Stores report missing materials, campaigns launch late, or materials arrive after the promotional period has ended.

### Step 3: Store Assignment and Field Team Routing

Programme managers assign campaigns to specific outlets and field reps. Store lists are uploaded and tagged to the campaign. Field reps receive campaign tasks on their mobile app for assigned outlets, including visit instructions, campaign checklists, and reference images for execution guidelines. Routes are planned to cover all target stores within the campaign window. Coverage tracking begins: planned vs. completed outlets.

### Step 4: Store-Level Execution

Field reps or store staff execute the campaign in-store. On the mobile app, they start a visit, check campaign guidelines, set up displays, place signage, configure POS pricing, and build planogram-compliant shelf arrangements. For coffee chains, this includes setting up seasonal menu boards, counter displays, window clings, and promotional signage. Execution follows a structured checklist with mandatory checks: facing count, scheme activation, shelf placement, and price tag verification. Training completion is verified before launch: baristas must be trained on new recipes and promotional mechanics.

### Step 5: Proof of Execution and Image Capture

Field users capture real-time photo proof of every executed task. The mobile app binds each photo to metadata: GPS coordinates, timestamp (server and device), user ID, store code, visit ID, and task reference. Photos are taken of deployed POSM, shelf displays, end caps, and promotional fixtures. Before/after photo comparison is supported. The submission includes a completed checklist, activity completion status, and any remarks. This creates an execution record that leadership can trust, replacing subjective self-reporting with objective, time-and-location-stamped proof.

### Step 6: Multi-Level Audit and Validation

Submitted execution proof enters an audit queue. A multi-level audit workflow (L1, L2, L3) validates each submission:

- L1 Audit: Initial validation of field execution. Checks image compliance, basic placement.
- L2 Audit: Secondary quality check. Verifies shelf placement, campaign visibility, completion accuracy.
- L3 Audit: Supervisor-level verification. Assesses evidence quality, assigns compliance score.

Auditors validate image compliance, shelf placement, campaign visibility, completion accuracy, evidence quality, and allocate a score. Reviewers can approve or reject, add comments, and flag exceptions. Rejected submissions trigger corrective action. The audit workflow supports reason-for-non-completion capture, bypass approval, and exception identification.

### Step 7: Real-Time Dashboard Reporting and Compliance Scoring

Execution data flows into real-time dashboards. HQ, regional managers, and supervisors see live metrics: campaign coverage %, compliance %, visibility %, total visits, planned vs. completed outlets, pending outlets, region-wise performance, and outlet-level execution scores. Compliance scorecards track parameter-wise compliance across stores and regions. Reports include store visit summaries, outlet photo reports, campaign compliance reports, merchandising productivity reports, and pending outlet reports.

### Step 8: Corrective Action and Close-Out

When execution gaps are identified, a corrective action workflow is triggered: issue identified, task created, owner assigned, deadline set, resolution documented with follow-up photo, resolution time tracked. Exceptions auto-escalate. The goal is to close gaps during the campaign window, not after it. At close-out, exceptions are logged (overrides, goodwill, system issues), handover notes are written for the next shift, and learning capture records what worked and what did not. For digital audit programs using image recognition, the correction loop can run from shelf photo to gap list to rep action within 90 seconds, all before the rep leaves the aisle.

## Tracker fields

The following fields should be tracked in a campaign execution tracker. Compiled from retail execution platforms (1Channel, GoSpotCheck/FORM, FieldPie, EasyCheck) and field operations guides.

### Campaign-level fields

| # | Field | Description |
|---|-------|-------------|
| 1 | campaign_id | Unique identifier for the campaign |
| 2 | campaign_name | Human-readable campaign name (e.g., "Summer Peach LTO 2026") |
| 3 | campaign_type | Category: seasonal_lto, product_launch, promotional_pricing, brand_activation |
| 4 | campaign_start_date | Planned launch date |
| 5 | campaign_end_date | Planned end date |
| 6 | campaign_status | draft, active, paused, completed, cancelled |
| 7 | hq_owner | HQ stakeholder responsible for the campaign |
| 8 | target_store_count | Number of stores in scope |

### Store and assignment fields

| # | Field | Description |
|---|-------|-------------|
| 9 | store_id | Unique store identifier |
| 10 | store_name | Store name or label |
| 11 | region | Geographic region or territory |
| 12 | store_format | Store type: flagship, standard, kiosk, drive-thru |
| 13 | assigned_field_rep | Field rep responsible for this store/campaign |
| 14 | posm_list | POSM materials assigned: posters, standees, tent cards, signage, shelf branding, menu boards, window clings |

### Visit and execution fields

| # | Field | Description |
|---|-------|-------------|
| 15 | visit_id | Unique visit identifier |
| 16 | visit_date | Date of field visit |
| 17 | visit_timestamp | Precise check-in/check-out time |
| 18 | visit_status | planned, in_progress, completed, missed, bypassed |
| 19 | gps_coordinates | Latitude/longitude at capture time |
| 20 | checklist_completion_pct | Percentage of checklist items completed |
| 21 | planogram_compliance | Boolean or score: does shelf match planogram |
| 22 | pricing_accuracy | Boolean: are price tags correct for the promotion |
| 23 | on_shelf_availability | Percentage of campaign SKUs present on shelf |
| 24 | training_completion_flag | Whether store staff completed pre-launch training |

### Proof and audit fields

| # | Field | Description |
|---|-------|-------------|
| 25 | photo_proof_url | URL or path to captured execution photo |
| 26 | photo_timestamp | Server-validated capture time |
| 27 | audit_level | L1, L2, or L3 |
| 28 | audit_status | pending, approved, rejected |
| 29 | compliance_score | Numeric score (0-100) assigned during audit |
| 30 | audit_comments | Reviewer remarks and rejection reasons |
| 31 | exception_flag | Boolean: was an exception logged |
| 32 | non_completion_reason | Reason if task was not completed |

### Corrective action and rollup fields

| # | Field | Description |
|---|-------|-------------|
| 33 | corrective_action_id | ID for corrective action task |
| 34 | corrective_action_owner | Person assigned to fix the issue |
| 35 | corrective_action_deadline | Resolution due date |
| 36 | corrective_action_status | open, in_progress, resolved |
| 37 | resolution_time_hours | Hours from issue detection to resolution |
| 38 | region_coverage_pct | Percentage of planned stores visited in region |
| 39 | campaign_compliance_pct | Percentage of stores passing audit |

## Common failure modes

Synthesized from retail execution gap analyses (Yoobic, ThirdChannel, Xenia), store rollout guides (Shoplworks, Archway), and audit execution frameworks (VisionGroup, FieldAssist).

| # | Failure mode | What happens | Source signal |
|---|-------------|--------------|---------------|
| 1 | Delayed or missing campaign materials | POSM kits, signage, or promotional assets arrive late or not at all. Stores report missing materials; campaigns launch late or materials arrive after the promotional window. | Archway |
| 2 | Unclear execution guidelines | Store teams receive marketing materials without detailed guidance on display setup, signage placement, or campaign timing. Results in incorrect displays, varied launch times, inconsistent brand messaging. | Archway |
| 3 | Poor coordination between marketing and store teams | Marketing and store teams use separate systems. Miscommunication about timelines, delays in promotional materials, confusion over priorities. | Archway, Yoobic |
| 4 | Pencil-whipping and self-reported compliance | Store teams check off tasks that were never done because checklists have no proof layer. Compliance data looks healthy while stores are not. No timestamp, no photo, no way to verify remotely. | Xenia |
| 5 | Late campaign activation | A promotion activates days late in a significant percentage of outlets. The failure is structural: no task assignment, no verification, no escalation when a store has not executed. Late launches are the default, not the exception. | FieldAssist |
| 6 | No real-time visibility into in-store execution | HQ relies on delayed reporting from store visits, field audits, or mystery shopping. By the time issues surface, the campaign window has closed. Problems cannot be fixed early. | Shoplworks, Yoobic |
| 7 | Audit data arrives after campaign window closes | If the audit schedule delivers compliance data at the end of the campaign rather than during it, there is no operational use for that data. The campaign window has already closed. | VisionGroup |
| 8 | Planogram non-compliance and incorrect shelf placement | Products in wrong positions, missing facings, competitor SKUs drifting into allocated space. Manual audits are slow and by the time data reaches a manager, the window to act has closed. | VisionGroup, FieldAssist |
| 9 | Missing price tags and pricing errors | Price tags missing, promotional pricing not configured in POS, signage conflicts with offer terms. Customers charged wrong price or promotion does not ring up. | VisionGroup, Ocasta |
| 10 | POSM not deployed or incorrectly placed | Display is built but header card is missing, wobbler is turned the wrong way, floor decal is partially covered. POSM compliance is one of the hardest pillars to verify manually at scale. | VisionGroup |
| 11 | Training gaps before launch | Store staff not trained on new recipes, promotional mechanics, or customer handling before launch day. Leads to inconsistent execution, customer confusion, and incorrect promotion application. | Shoplworks, Axonify |
| 12 | Stockouts and on-shelf availability failures | Hero or promotional product sells out before lunchtime. Replenishment plan not confirmed. Out-of-stocks not logged or communicated. Lost sales during the campaign window. | Ocasta |
| 13 | No structured escalation path for issues | Store associate notices a broken display fixture but there is no system to flag it, assign it, and track the fix. Issue is mentioned verbally or ignored. | Xenia |
| 14 | Workforce turnover and new staff unfamiliarity | Rapidly changing frontline workforce. New staff unfamiliar with campaign standards, brand guidelines, or execution procedures. Structural issue that makes consistent execution difficult. | Yoobic |
| 15 | Paper-based and outdated operational tools | Paper checklists signed off tell you someone held a pen, not whether the task was done. No proof layer, no structured escalation, no cross-location visibility. | Xenia |
| 16 | Photos without context or chain-of-custody | Photos exist but prove nothing: no timestamp, no location, no context. Generic camera photos cannot guarantee chain-of-custody for brand compliance checks or partner audits. | EasyCheck, MyFieldHeroes |
| 17 | Compliance treated as the finish line (compliance vs. execution gap) | Compliance confirms an action occurred but does not confirm the outcome was achieved. A promotion runs by compliance standards but barely shows up by execution standards because staff did not understand the goal. | ThirdChannel |

## Portfolio modeling decisions

This section defines what is safe to simulate for a coffee/retail chain portfolio project. The project uses simulated data only and does not claim access to any real company's data, internal systems, or operational experience.

### Safe to simulate

1. **Store network**: Generate a synthetic multi-store coffee chain with 30-80 stores across 4-6 regions. Store formats: flagship, standard, kiosk, drive-thru. All store IDs, names, and addresses are fictional.

2. **Campaigns**: Model seasonal LTO campaigns inspired by publicly documented coffee chain patterns (Pumpkin Spice Latte season, Holiday Menu, Summer Peach LTO). Campaign types: seasonal_lto, product_launch, promotional_pricing. All campaign data is synthetic.

3. **POSM materials**: Simulate POSM types relevant to coffee retail: counter displays, menu boards, window clings, shelf talkers, tent cards, and digital screen content. POSM IDs and descriptions are fictional.

4. **Field reps and visit schedules**: Generate synthetic field reps with assigned territories and planned visit routes. Visit timestamps, GPS coordinates (within plausible geographic clusters), and check-in/check-out times are simulated.

5. **Photo proof metadata**: Generate simulated photo proof records with metadata fields (GPS coordinates, timestamps, user ID, store code, visit ID). No real photos are used. The metadata structure mirrors real field execution platforms but contains only synthetic values.

6. **Compliance scores and audit outcomes**: Simulate L1/L2/L3 audit results with compliance scores (0-100), audit statuses (approved/rejected), and reviewer comments. Score distributions should be realistic but are entirely synthetic.

7. **Exception and corrective action records**: Generate synthetic exception flags, non-completion reasons, and corrective action tasks with owners, deadlines, and resolution times.

8. **Workflow state transitions**: Model the full lifecycle state machine: campaign draft, active, paused, completed. Visit states: planned, in_progress, completed, missed. Audit states: pending, approved, rejected. Corrective action states: open, in_progress, resolved.

9. **Dashboard metrics**: Compute rollup metrics from simulated records: coverage %, compliance %, visibility %, region performance, pending outlets, corrective action resolution time.

### Do not simulate or claim

- Real company data, internal knowledge, or real-world retail operations experience.
- Real Tomoro data or access to Tomoro internal systems.
- That `pip install retail-ops-control-tower` works from PyPI (source install only).
- Real customer data, real sales figures, or real store locations.
- Any implication that the project is connected to a real coffee chain.

### Modeling rationale

The coffee/retail chain context is well-suited for this portfolio project because:

- Coffee chains run predictable, calendar-driven seasonal campaigns (PSL, holiday menus, summer LTOs) documented in public sources, making the campaign types realistic without requiring proprietary data.
- Coffee chains experience traffic spikes tied to seasonal launches (e.g., 7 Brew's Jackpot Day generated a 47.1% traffic lift), which creates natural operational pressure scenarios to model.
- The multi-store rollout pattern (HQ planning, trade marketing, field distribution, store execution, proof, audit) maps cleanly to the campaign execution workflow researched above.
- Barista training and recipe card distribution are well-documented public practices that can be modeled as training completion rates in the tracker.

## Source notes

All sources are public web pages accessed on 2026-07-03. URLs are provided for verification.

1. Shoplworks - "5 Common Mistakes in Store Rollout" - https://www.shoplworks.com/en/blog-insight/retail-rollout-mistakes-execution-kpis
   - Multi-phase rollout process (HQ Planning, Trade Marketing, Field Operations, Store Staff, Shopper). Execution KPIs: store readiness by date, timely POSM delivery, material acknowledgment rate, training completion, on-shelf availability, store compliance rate by stage.

2. 1Channel - "Understanding In-Store Execution Tracking in Retail Operations" - https://www.1channel.co/blog/understanding-in-store-execution-tracking-in-retail-operations
   - Closed-loop workflow: campaign/POSM setup, store-level execution, image-based proof, multi-level audit (L1/L2/L3), dashboard reporting. Tracker fields: campaign name, duration, validation rules, store list, POSM list, visit details, image submission, GPS tagging, timestamp logging, compliance score, exception reporting.

3. Xenia - "Retail Execution Guide for Multi-Location Brands" - https://www.xenia.team/articles/retail-execution-guide
   - Mobile inspections with photo verification, clear task assignment, side-by-side image comparison, real-time corrective actions. Corrective action workflow: issue identified, task created, manager assigned, deadline set, photo verification, resolution tracked.

4. Archway - "A Brand Manager's Guide to Stronger In-Store Campaign Execution" - https://archway.com/blog/in-store-campaign/
   - Three key failure causes: lack of clear execution guidelines, poor coordination between marketing and retail teams, delays in campaign materials and logistics. Need for centralized collaboration platform.

5. Meegle - "Retail Activation Execution Audit Checklist" - https://www.meegle.com/en_us/advanced-templates/consumer_goods_marketing_management/retail_activation_execution_audit_checklist
   - Structured audit framework for retail activation: store setup, marketing material deployment, customer engagement activities. Roles: regional managers, marketing coordinators, auditors.

6. Ocasta - "Promotion Launch Readiness Checklist" - https://ocasta.com/resources/checklists/promotion-launch-readiness-checklist/
   - Three-pass checklist: before opening (promotion basics, stock, signage, team briefing, till test), first hour (live transaction check, refill, customer questions), end of shift (log exceptions, handover notes, learning capture). Escalation criteria.

7. Umbrex - "Execution Across Channels" - https://umbrex.com/resources/retail-industry-playbooks/the-promotion-strategy-promo-planning-playbook/execution-across-channels/
   - Pre-launch promotion execution readiness checklist: inventory position, store readiness (signage, displays, planograms, labor guidance, price files, POS setup, associate communication, escalation paths), digital readiness, systems testing, customer service readiness, measurement setup.

8. Gopazo - "Retail Execution Monitoring: A Guide to Achieving Consistency Across Stores" - https://www.gopazo.com/blog/retail-execution-and-monitoring
   - Real-time visibility, photo/video-based execution proof, store-wise compliance scoring, centralized SOPs, SLA for every task, promotion activation time metric, deviation alerts.

9. ThirdChannel - "Compliance isn't execution: why retail programs break down in stores" - https://blog.thirdchannel.com/compliance-isnt-execution-why-retail-programs-break-down-in-stores
   - Compliance vs. execution distinction. Compliance confirms an action occurred; execution requires ownership of the outcome. Field reps as partners vs. auditors. Gift-with-purchase example.

10. VisionGroup - "Retail Audit: What It Is, How to Run One" - https://visiongroupretail.com/blog/retail-audit-execution-guide
    - Five execution categories. Digital audit using image recognition: 90-second gap list delivery to rep's phone. Before-and-after shelf state. Correction loop speed difference between manual and digital audit programs.

11. FieldAssist - "How CPG Brands Improve In-Store Execution and Shelf Compliance" - https://www.fieldassist.com/blog/perfect-store-execution-framework
    - Perfect store framework: 5Ps (Product, Placement, Price, Promotion, Presence). Planogram compliance as weekly discipline. Promotion tracking as discrete verifiable tasks. Late launch as structural failure.

12. EasyCheck - "Retail Execution Verification" - https://easycheck.io/use-cases/retail-execution-verification/
    - Photo evidence, timestamped, location verified, linked to store and visit. Verification of task completion, display placement, shelf condition, promotional execution, compliance to plan.

13. Yoobic - "How Retail Execution Gaps Cost Retailers $10M-$40M a Year" - https://yoobic.com/blog/the-retail-execution-gap/
    - Real compliance rate 55-65% (not the assumed higher rate). Three structural gaps: communication breakdowns, productivity friction, workforce turnover. Limited visibility, outdated tools, changing workforce.

14. Xenia - "Retail Operations Execution: The Field Leader's Complete Guide" - https://www.xenia.team/articles/retail-operations-execution
    - Paper-based processes have no proof layer. Pencil-whipping. No structured escalation path. Promotional rollouts rely on trust, not verification. Closed-loop corrective action workflow.

15. MyFieldHeroes - "Field Staff Tracking App for POSM Audits: Photo & Geo-Tag Proof" - https://myfieldheroes.com/field-staff-tracking-app-posm-audits-photo-geo-tag-proof/
    - Photo metadata: GPS coordinates, timestamp, device ID, user ID, store code, planogram ID, task reference. Chain-of-custody for audit photos. Geofence enforcement.

16. 1Channel - "POSM Tracking & Proof of Execution" - https://www.1channel.co/posm-tracking-proof-of-execution
    - Campaign-based execution tracking, photo proof of execution, image-based verification, multi-level audits (L1, L2, L3), real-time tracking and visibility. Before/after photo comparison.

17. 1Channel - "Store Audit & Compliance" - https://www.1channel.co/store-audit-compliance
    - Audit parameters: visibility, placement, hygiene, execution standards. Scoring logic: binary, weighted, or percentage-based. Audit reports, compliance reporting, audit quality reports, coverage reports, audit productivity reports.

18. Restaurant Dive - "How do coffee chains design, market and analyze their seasonal LTOs?" - https://www.restaurantdive.com/news/coffee-chains-design-market-and-analyze-holiday-seasonal-ltos-peets-dutch-bros-westrock/733136/
    - Dutch Bros: ~6 months from concept to deployment. Peet's: ~8 months lead time for product teams. Westrock: up to 1 year. Recipe cards and training videos distributed to stores. Barista training before launch. Active sampling in-store at season launch.

19. Vixxo - "Predictable Coffee Traffic Spikes Are Testing Facilities Readiness" - https://www.vixxo.com/facilities-management-news/predictable-coffee-traffic-spikes-are-testing-facilities-readiness
    - Calendar-driven demand: PSL launches, 7 Brew Jackpot Day (47.1% traffic lift). Predictable spikes visible weeks/months in advance. Facilities readiness aligned to commercial calendar. Preventive maintenance as revenue enabler.

20. Axonify - "Seasonal Retail Planning 2025" - https://axonify.com/blog/retail-seasonal-planning/
    - Frontline readiness as core driver. Agile training, real-time communication, in-the-moment support. Faster rollout of promotions, stronger compliance. Unite Operations and L&D.

21. Barista Life - "Coffee Shop Holiday Marketing Strategy" - https://baristalife.co/blogs/blog/coffee-shop-holiday-marketing
    - Staffing and operational considerations: seasonal staff training, inventory management, extended hours, queue management, stress management, backup planning for equipment failures and supply chain disruptions. Planning begins late August/early September.

22. BIGGBY Coffee (PR Newswire) - Summer 2026 seasonal menu announcement - https://www.prnewswire.com/news-releases/biggby-coffee-is-bringing-the-summer-fun-with-toasted-campfire-flavors-refreshing-peach-sips-and-fun-for-the-whole-family-302795672.html
    - Example of a real coffee chain seasonal campaign: campfire flavors, peach creations, summer LTOs running June-August. 460+ locations across 13 states. App-exclusive promotions, BOGO offers, holiday-specific drink lineups.
