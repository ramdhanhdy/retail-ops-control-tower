# Retail Ops Control Tower — Closed-Loop Action & Verification Module

For Hermes: Use subagent-driven-development skill to implement this plan task-by-task.

**Fable system instructions for long runs:**
- "Before reporting any task complete, verify: the file exists, the test passes, the commit is made. If a step was skipped or a test is red, say so explicitly before moving to the next task."
- "Maintain a file at .hermes/lessons/retail-control-tower.md with one-line summaries of corrections and confirmed approaches. Update it at the end of each task batch (Day 0, Day 1, Day 2, etc.)."
- Do not auto-push. After all verifications in a task pass, present the diff for the user to review.

**Effort calibration:**
- Tasks 1, 2, 3, 4, 5, 6, 7: medium (rote TDD, well-defined acceptance criteria)
- Tasks 8, 9, 10: xhigh (deep statistical reasoning, first-shot correctness matters for methodology)
- Tasks 11, 12, 16: moderate (presentational, clear scope)
- Tasks 13, 14, 15: high (prose quality and persuasion matter)

**Goal:** Add a closed-loop action and verification layer to the Retail Ops Control Tower: simulate interventions, measure whether they worked, and cut the dashboard to 5 question-named views.

**Architecture:** Three new components: (1) an `actions` table in the data generator that simulates intervention outcomes with a known-but-noisy ground-truth effect, (2) a `verification` module that measures whether interventions worked using matched comparison + effect size recovery, and (3) one new Streamlit dashboard page — an action queue with assign/resolve state. Plus: dashboard cleanup, README rewrite as case study, decision memo, and 2-minute walkthrough video script.

**Tech Stack:** Python 3.11+, pandas, scipy, statsmodels, matplotlib, Streamlit, SQLite (for action queue state)

---

## Context

### What exists
- **Data layer**: 8 simulated CSV tables (100 stores, 3 campaigns, 1,603 exceptions)
- **Detection layer**: 9-category exception engine → `data/processed/exceptions.csv`
- **Ranking layer**: priority scoring → `data/processed/daily_action_list.csv`
- **Diagnostic layer**: 4-layer statistical insight engine (Pareto/Gini, ANOVA/Kruskal-Wallis, binomial/permutation, rebalancing/financial)
- **Dashboard**: 514-line Streamlit app with 6 views (executive tiles, campaign performance, exception backlog, store status, SLA aging, AM scorecard)
- **Reporting**: 8-section weekly report, executive summary, insights, validation summary
- **Tests**: 354 passing tests across 13 test files

### What's missing
- No action layer: exceptions are detected and ranked but never assigned, acted on, or resolved
- No verification: no way to measure whether an intervention actually worked
- Dashboard is a "reporting island" — shows data but no action capabilities
- README is feature-list, not case study
- No decision memo or walkthrough video

### Key design decisions (from Fable consultation)
1. **Simulate the action loop in the data, not the UI** — Use simulated data as a feature: inject a known intervention effect with realistic noise, then verify the analytics recover it
2. **Matched comparison, not causal inference** — Compare stores that received intervention vs. statistically similar stores that didn't. Simple t-test + effect size. No DAG, no propensity scoring
3. **Circularity disclosure as feature** — State plainly: "The intervention effect is simulated; the deliverable is the measurement methodology, not the finding." Show that the matched comparison recovers the injected effect within confidence bounds
4. **Coffee chain framing** — Fictional named Indonesian coffee chain ("Kopi Senja"), not abstract "retail operations"
5. **Dashboard: question-named views** — Each view named after the question a specific role asks at a specific time. Target ~200 lines, not 514
6. **Decision memo** — 1-page memo with 3 recommendations and money attached. Leverages DPR staff experience (briefing decision-makers)
7. **Video: one exception, cradle to grave** — Follow Store 47's quantity mismatch through the full loop, ~90 seconds, then 20 seconds on scope

---

## Scope

### In scope
- `actions` table simulation (data generation)
- `intervention_outcomes` table simulation (data generation)
- Verification analytics module (pandas/scipy)
- Methodology validation test (recovers injected effect)
- Dashboard cleanup: cut to 5 question-named views, target ~200 lines
- Dashboard: add action queue page with assign/resolve state (SQLite)
- README rewrite as case study (coffee chain framing, DPR line, loop diagram)
- Decision memo (1 page, 3 recommendations, money attached)
- Walkthrough video script (Store 47, cradle to grave)
- Limitations section (circularity disclosure)

### DISCLOSURE RULE (applies to all tasks)
Any file that displays verification results (numbers, charts, recovery rates) MUST include this sentence or a localized equivalent:
> "Results are from simulated data. The deliverable is the measurement methodology, not the finding."

**Applies to:** README.md, dashboard/app.py (verification view), docs/decision_memo.md, any Streamlit page, and any verification output script.

### Out of scope
- Authentication / role-based access control
- Full web app (React/Vue/etc.)
- HTML mockups of role-based views
- Real-time data feeds
- Causal inference models (DAG, propensity scoring, IV)
- Mobile app
- Multi-tenant architecture
- Production deployment

---

## Assumptions
- Python 3.11+ with existing venv at `.venv/`
- Existing 354 tests continue to pass after changes
- `issues` table already has `corrective_action_*` fields that can be extended
- `stores` table has `area_manager` and `field_rep` columns for assignment
- `exceptions` table has `priority_score` for ranking
- Simulated data uses seed 42 for reproducibility
- Streamlit app runs locally (no deployment)
- Recruiter spends 6-8 minutes on the repo

---

## Risks

1. **Circularity trap** — If every intervention succeeds in the simulation, the recovery test is trivial and a technical reviewer sees it as theater. **Mitigation:** Inject failures, re-opens, and null results. The method should survive noise, not just signal.

2. **Dashboard scope creep** — Cutting 514 lines to ~200 could break existing tests or remove views that are actually useful. **Mitigation:** Keep all existing dashboard section modules in the package, only remove them from `app.py`. Tests for section modules continue to pass.

3. **README over-promising** — Writing verification claims before the module runs. **Mitigation:** Use `[placeholder: X% recovery ± Y%]` in README until Day 3, fill with real numbers after.

4. **Video quality bar** — Spending too long polishing the video instead of shipping. **Mitigation:** Script it, do 2-3 takes, don't polish beyond that. 2 minutes max.

5. **Memo prose quality** — The decision memo is the hardest artifact because it must be good prose, not just correct analysis. **Mitigation:** Budget a full day for it. If anything slips, let it be the memo, shipped excellent.

---

## Tasks

### Task 1: Reframe README — coffee chain context (Day 0)

**Objective:** Rewrite README opening with coffee chain framing, DPR differentiator, and loop diagram. Leave verification numbers as placeholders.

**Files:**
- Modify: `README.md` (lines 1-30, rewrite the opening section)

**Step 1:** Rewrite the opening paragraph:
```markdown
# Retail Ops Control Tower

A control tower for **Kopi Senja**, a fictional 100-store Indonesian coffee chain
launching three seasonal limited-time-offer campaigns. The system detects 1,603
operational exceptions across 100 stores, ranks them by business impact, and
closes the loop: detect → rank → assign → act → verify.
```

**Step 2:** Add the DPR differentiator paragraph:
```markdown
## Why this project

Built by a data analyst who has briefed Indonesian parliament decision-makers
(DPR RI, Komisi VIII) on social program outcomes. This project applies the same
skill — turning complex data into a brief a decision-maker can act on — to retail
operations. The deliverable is a decision memo, not just a dashboard.
```

**Step 3:** Add loop diagram (ASCII):
```markdown
## The closed loop

```
    Detect          Rank           Assign         Act            Verify
  (9 rules)  →  (priority)  →  (to AM/rep) → (intervention) → (did it work?)
      ↑                                                              |
      └────────────── feedback: reopen if unresolved ────────────────┘
```
```

**Step 4:** Add placeholders for verification results:
```markdown
## Verification analytics

The system includes a methodology validation: a known intervention effect
is injected into the simulated data with realistic noise (failures, re-opens,
null results). The verification module must recover the injected effect
within confidence bounds.

Results: [placeholder — fill after verification module runs]
```

**Step 5:** Add limitations section stub:
```markdown
## Limitations

- Data is simulated. The intervention effect is injected, not observed.
  The deliverable is the measurement methodology, not the finding.
- On real data, this pipeline would answer whether interventions actually work.
```

**Verify:** `head -40 README.md` shows coffee chain framing, DPR line, loop diagram, and placeholder.

---

### Task 2: Create Actions model (Day 1)

**Objective:** Add the Action dataclass model for the actions table.

**Files:**
- Create: `retail_ops_control_tower/models/actions.py`
- Modify: `retail_ops_control_tower/models/__init__.py`

**Step 1:** Write failing test:
```python
# tests/test_actions.py
from retail_ops_control_tower.models.actions import Action

def test_action_has_required_fields():
    action = Action(
        action_id="ACT-001",
        exception_id="EXC-007",
        campaign_id="C-2026-PEACH",
        store_id="S-079",
        assigned_by="Ops Lead",
        assigned_to="Marcus Lee",
        action_type="phone_call",
        action_timestamp="2026-06-26T09:00:00-05:00",
        action_status="completed",
        outcome="resolved",
        time_to_action_hours=14.0,
        notes="Called store PIC, confirmation posted same day.",
    )
    assert action.action_id == "ACT-001"
    assert action.outcome == "resolved"
```

**Step 2:** Run test, verify failure:
```
.venv/bin/pytest tests/test_actions.py::test_action_has_required_fields -v
```
Expected: FAIL — `ModuleNotFoundError`

**Step 3:** Write the model:
```python
# retail_ops_control_tower/models/actions.py
"""Dataclass model for the actions table (intervention records)."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Action:
    action_id: str
    exception_id: str
    campaign_id: str
    store_id: str
    assigned_by: str
    assigned_to: str
    action_type: str
    action_timestamp: str
    action_status: str
    outcome: str
    time_to_action_hours: float
    notes: str
```

**Step 4:** Export from `__init__.py`, run test, verify pass:
```
.venv/bin/pytest tests/test_actions.py::test_action_has_required_fields -v
```
Expected: PASS

**Step 5:** Commit:
Stage and commit when ready:
```bash
git add retail_ops_control_tower/models/actions.py retail_ops_control_tower/models/__init__.py tests/test_actions.py
git commit -m "feat: add Action dataclass model"
```
(Do not push. After all verifications pass, present the diff for user review.)

---

### Task 3: Implement `generate_actions` function (Day 1)

**Objective:** Add the actions generation function to `data_generation.py`.

**Files:**
- Modify: `retail_ops_control_tower/data_generation.py`
- Modify: `tests/test_actions.py` (add generation tests)

**Step 1:** Write failing tests:
```python
# tests/test_actions.py (append)
import pandas as pd
from retail_ops_control_tower.data_generation import generate_actions

def test_actions_generated_for_breached_exceptions():
    exceptions = pd.read_csv("data/processed/exceptions.csv")
    actions = generate_actions(exceptions, seed=42)
    assert len(actions) > 0
    assert "action_id" in actions.columns
    assert "outcome" in actions.columns

def test_actions_have_realistic_outcomes():
    exceptions = pd.read_csv("data/processed/exceptions.csv")
    actions = generate_actions(exceptions, seed=42)
    outcomes = actions["outcome"].value_counts()
    assert "resolved" in outcomes.index
    assert "unresolved" in outcomes.index
    resolved_share = outcomes.get("resolved", 0) / len(actions)
    assert 0.40 < resolved_share < 0.85
```

**Step 2:** Run tests, verify failure:
```
.venv/bin/pytest tests/test_actions.py -v -k "generated or realistic"
```
Expected: FAIL — `ImportError: cannot import name 'generate_actions'`

**Step 3:** Implement `generate_actions`:

Logic:
- For each exception with `sla_status == "breached"` OR `priority_score >= 200`, create 1-2 actions
- `action_type` mapped from `exception_type` (see ACTION_TYPE_MAP in plan)
- `assigned_to` = `area_manager` from store record
- `time_to_action_hours` = log-normal, mean by severity (critical=4h, high=12h, medium=24h)
- `outcome` = probabilistic with known injected effect:
  - Baseline (no action): 30% resolve
  - Intervention: 60% resolve (known effect = +30pp)
  - 5% of resolved reopen within 48h
  - 10% of actions fail
- `notes` = templated string by action type + outcome

**Step 4:** Run tests, verify pass:
```
.venv/bin/pytest tests/test_actions.py -v
```
Expected: 3 passed

**Step 5:** Commit:
Stage and commit when ready:
```bash
git add retail_ops_control_tower/data_generation.py tests/test_actions.py
git commit -m "feat: implement generate_actions with known intervention effect"
```
(Do not push. After all verifications pass, present the diff for user review.)

---

### Task 4: Generate `actions.csv` and wire into pipeline (Day 1)

**Objective:** Generate the actual CSV file and add to the pipeline.

**Files:**
- Create: `data/sample/actions.csv` (generated)
- Modify: `scripts/generate_sample_data.py` (add actions generation call)

**Step 1:** Generate the CSV:
```bash
.venv/bin/python -c "
from retail_ops_control_tower.data_generation import generate_actions
import pandas as pd
exceptions = pd.read_csv('data/processed/exceptions.csv')
actions = generate_actions(exceptions, seed=42)
actions.to_csv('data/sample/actions.csv', index=False)
print(f'Generated {len(actions)} actions')
print(actions['outcome'].value_counts())
"
```
Expected: ~400-600 actions, ~55-65% resolved

**Step 2:** Add to `generate_sample_data.py`:
```python
# After existing table generation, add:
from retail_ops_control_tower.data_generation import generate_actions
import pandas as pd
exceptions = pd.read_csv(str(PROCESSED_DIR / "exceptions.csv"))
actions = generate_actions(exceptions, seed=42)
actions.to_csv(str(SAMPLE_DIR / "actions.csv"), index=False)
```

**Step 3:** Verify:
```bash
.venv/bin/python scripts/generate_sample_data.py && wc -l data/sample/actions.csv
```
Expected: CSV regenerated with correct row count

**Step 4:** Commit:
Stage and commit when ready:
```bash
git add data/sample/actions.csv scripts/generate_sample_data.py
git commit -m "feat: generate actions.csv and wire into pipeline"
```
(Do not push. After all verifications pass, present the diff for user review.)

---

### Task 5: Create InterventionOutcome model (Day 1)

**Objective:** Add the InterventionOutcome dataclass model.

**Files:**
- Create: `retail_ops_control_tower/models/intervention_outcomes.py`
- Modify: `retail_ops_control_tower/models/__init__.py`
- Create: `tests/test_intervention_outcomes.py`

**Step 1:** Write failing test:
```python
# tests/test_intervention_outcomes.py
from retail_ops_control_tower.models.intervention_outcomes import InterventionOutcome

def test_outcome_has_required_fields():
    outcome = InterventionOutcome(
        outcome_id="OUT-001",
        exception_id="EXC-007",
        action_id="ACT-001",
        store_id="S-079",
        exception_type="missing_confirmation",
        received_intervention=True,
        matched_control_store_id="S-045",
        matched_control_exception_id="EXC-045",
        resolved=True,
        control_resolved=False,
        days_to_resolution=1,
        control_days_to_resolution=14,
        revenue_impact_usd=2400.0,
        counterfactual_revenue_loss_usd=4200.0,
    )
    assert outcome.received_intervention is True
    assert outcome.matched_control_store_id == "S-045"
```

**Step 2:** Run test, verify failure:
```
.venv/bin/pytest tests/test_intervention_outcomes.py::test_outcome_has_required_fields -v
```
Expected: FAIL — `ModuleNotFoundError`

**Step 3:** Write the model:
```python
# retail_ops_control_tower/models/intervention_outcomes.py
"""Dataclass model for intervention outcomes table."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class InterventionOutcome:
    outcome_id: str
    exception_id: str
    action_id: str
    store_id: str
    exception_type: str
    received_intervention: bool
    matched_control_store_id: str
    matched_control_exception_id: str
    resolved: bool
    control_resolved: bool
    days_to_resolution: int
    control_days_to_resolution: int
    revenue_impact_usd: float
    counterfactual_revenue_loss_usd: float
```

**Step 4:** Export, run test, verify pass:
```
.venv/bin/pytest tests/test_intervention_outcomes.py::test_outcome_has_required_fields -v
```
Expected: PASS

**Step 5:** Commit:
Stage and commit when ready:
```bash
git add retail_ops_control_tower/models/intervention_outcomes.py retail_ops_control_tower/models/__init__.py tests/test_intervention_outcomes.py
git commit -m "feat: add InterventionOutcome dataclass model"
```
(Do not push. After all verifications pass, present the diff for user review.)

---

### Task 6: Implement `generate_intervention_outcomes` (Day 1)

**Objective:** Add the outcomes generation function with matched control stores.

**Files:**
- Modify: `retail_ops_control_tower/data_generation.py`
- Modify: `tests/test_intervention_outcomes.py` (add generation tests)

**Step 1:** Write failing tests:
```python
# tests/test_intervention_outcomes.py (append)
import pandas as pd
from retail_ops_control_tower.data_generation import generate_intervention_outcomes

def test_outcomes_have_matched_pairs():
    actions = pd.read_csv("data/sample/actions.csv")
    exceptions = pd.read_csv("data/processed/exceptions.csv")
    stores = pd.read_csv("data/sample/stores.csv")
    outcomes = generate_intervention_outcomes(actions, exceptions, stores, seed=42)
    assert len(outcomes) > 0
    assert outcomes["matched_control_store_id"].notna().all()

def test_intervention_effect_is_visible():
    actions = pd.read_csv("data/sample/actions.csv")
    exceptions = pd.read_csv("data/processed/exceptions.csv")
    stores = pd.read_csv("data/sample/stores.csv")
    outcomes = generate_intervention_outcomes(actions, exceptions, stores, seed=42)
    assert outcomes["resolved"].mean() > outcomes["control_resolved"].mean()
    assert 0.45 < outcomes["resolved"].mean() < 0.75
    assert 0.15 < outcomes["control_resolved"].mean() < 0.45
```

**Step 2:** Run tests, verify failure:
```
.venv/bin/pytest tests/test_intervention_outcomes.py -v -k "matched or effect"
```
Expected: FAIL — `ImportError`

**Step 3:** Implement `generate_intervention_outcomes`:

Matching logic with fallback hierarchy (use and log each):
```
1. Exact match: store_format + region + exception_type + priority ±50
2. Relaxed: store_format + region + exception_type + priority ±100
3. Minimal: store_format + exception_type (drop region/priority)
4. No match: exclude outcome from analysis (track count excluded)

Log exclusion rates. If >10% excluded, fail the test in Task 10 with a
clear message about selection bias.
```

**Noise injection (required, not optional):**
- 8% of actions: `outcome="failed"` (intervention wrong/wasted)
- 6% of resolved cases: `reopen=True` within 48h
- For `exception_type == "missing_receipts"` + `store.has_third_party_logistics == False`: `outcome="unresolved"` (intervention can't work here)
- 5% random assignment errors (assigned to wrong rep) → `outcome="unresolved"`
- 3-5% of exception types: null result (intervention genuinely doesn't work for that type)

Other logic:
- Control store must NOT have any action in `actions` table
- Control resolution simulated with baseline rate (30%), no intervention effect
- `revenue_impact_usd` = `$4,200 * days_saved`
- `counterfactual_revenue_loss_usd` = `$4,200 * control_days_to_resolution`

**Step 4:** Run tests, verify pass:
```
.venv/bin/pytest tests/test_intervention_outcomes.py -v
```
Expected: 3 passed

**Step 5:** Commit:
Stage and commit when ready:
```bash
git add retail_ops_control_tower/data_generation.py tests/test_intervention_outcomes.py
git commit -m "feat: implement generate_intervention_outcomes with matched controls"
```
(Do not push. After all verifications pass, present the diff for user review.)

---

### Task 7: Generate `intervention_outcomes.csv` (Day 1)

**Objective:** Generate the CSV and wire into pipeline.

**Files:**
- Create: `data/sample/intervention_outcomes.csv` (generated)
- Modify: `scripts/generate_sample_data.py`

**Step 1:** Generate the CSV:
```bash
.venv/bin/python -c "
from retail_ops_control_tower.data_generation import generate_intervention_outcomes
import pandas as pd
actions = pd.read_csv('data/sample/actions.csv')
exceptions = pd.read_csv('data/processed/exceptions.csv')
stores = pd.read_csv('data/sample/stores.csv')
outcomes = generate_intervention_outcomes(actions, exceptions, stores, seed=42)
outcomes.to_csv('data/sample/intervention_outcomes.csv', index=False)
print(f'Generated {len(outcomes)} outcomes')
print(f'Intervention: {outcomes[\"resolved\"].mean():.1%}, Control: {outcomes[\"control_resolved\"].mean():.1%}')
"
```
Expected: ~300-500 outcomes, intervention ~55-65% (noise reduces from 60%), control ~25-35%

**Step 2:** Add to `generate_sample_data.py` (after actions generation):
```python
outcomes = generate_intervention_outcomes(actions, exceptions, stores, seed=42)
outcomes.to_csv(str(SAMPLE_DIR / "intervention_outcomes.csv"), index=False)
```

**Step 3:** Verify:
```bash
.venv/bin/python scripts/generate_sample_data.py && wc -l data/sample/intervention_outcomes.csv
```

**Step 4:** Commit:
Stage and commit when ready:
```bash
git add data/sample/intervention_outcomes.csv scripts/generate_sample_data.py
git commit -m "feat: generate intervention_outcomes.csv and wire into pipeline"
```
(Do not push. After all verifications pass, present the diff for user review.)

---

### Task 8: Build verification analytics module (Day 2)

**Objective:** Create the `verification` package with matched comparison analytics.

**Files:**
- Create: `retail_ops_control_tower/verification/__init__.py`
- Create: `retail_ops_control_tower/verification/analytics.py`
- Create: `tests/test_verification.py`

**Step 1:** Write failing tests:
```python
# tests/test_verification.py
import pandas as pd
from retail_ops_control_tower.verification.analytics import (
    compute_resolution_rates,
    compute_effect_size,
    recover_injected_effect,
)

def test_resolution_rates():
    outcomes = pd.read_csv("data/sample/intervention_outcomes.csv")
    rates = compute_resolution_rates(outcomes)
    assert rates["intervention_rate"] > rates["control_rate"]
    assert "absolute_effect" in rates

def test_effect_size():
    outcomes = pd.read_csv("data/sample/intervention_outcomes.csv")
    result = compute_effect_size(outcomes)
    assert "cohens_h" in result
    assert result["cohens_h"] > 0.3

def test_recover_injected_effect():
    outcomes = pd.read_csv("data/sample/intervention_outcomes.csv")
    recovery = recover_injected_effect(outcomes, injected_effect=0.30)
    assert recovery["within_confidence_bounds"] is True
    assert abs(recovery["estimated_effect"] - 0.30) < 0.08
```

**Step 2:** Run tests, verify failure:
```
.venv/bin/pytest tests/test_verification.py -v
```
Expected: FAIL — `ModuleNotFoundError`

**Step 3:** Implement `verification/analytics.py`:

Functions:
- `compute_resolution_rates(outcomes)` → dict with intervention_rate, control_rate, absolute_effect, relative_risk
- `compute_effect_size(outcomes)` → dict with cohens_h, t_statistic, p_value, confidence_interval (Wilson)
- `recover_injected_effect(outcomes, injected_effect)` → dict with estimated_effect, injected_effect, within_confidence_bounds, bias
- `generate_verification_report(outcomes, injected_effect)` → dict with all results + by_action_type, by_exception_type, limitations

**Step 4:** Run tests, verify pass:
```
.venv/bin/pytest tests/test_verification.py -v
```
Expected: 3 passed

**Step 5:** Commit:
Stage and commit when ready:
```bash
git add retail_ops_control_tower/verification/ tests/test_verification.py
git commit -m "feat: add verification analytics module with matched comparison"
```
(Do not push. After all verifications pass, present the diff for user review.)

---

### Task 9: Add verification report generation script (Day 2)

**Objective:** Add CLI script that runs the verification pipeline and outputs JSON.

**Files:**
- Create: `scripts/build_verification.py`
- Create: `data/processed/verification_results.json` (generated)

**Step 1:** Write the script:
```python
# scripts/build_verification.py
"""Build verification analytics from intervention outcomes."""
import json, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from retail_ops_control_tower.verification.analytics import generate_verification_report

def main():
    outcomes = pd.read_csv(ROOT / "data" / "sample" / "intervention_outcomes.csv")
    report = generate_verification_report(outcomes, injected_effect=0.30)
    output_path = ROOT / "data" / "processed" / "verification_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Written to {output_path}")
    print(f"Intervention: {report['resolution_rates']['intervention_rate']:.1%}")
    print(f"Control: {report['resolution_rates']['control_rate']:.1%}")
    print(f"Recovery: {report['recovery']['estimated_effect']:.1%} (injected: 30%)")

if __name__ == "__main__":
    main()
```

**Step 2:** Run it:
```bash
.venv/bin/python scripts/build_verification.py
```
Expected: JSON written, summary printed

**Step 3:** Commit:
Stage and commit when ready:
```bash
git add scripts/build_verification.py data/processed/verification_results.json
git commit -m "feat: add verification build script and generate results JSON"
```
(Do not push. After all verifications pass, present the diff for user review.)

---

### Task 10: Add methodology validation test (Day 2)

**Objective:** Write THE test that validates the simulation's known-effect recovery.

**Files:**
- Create: `tests/test_methodology_validation.py`

**Step 1:** Write the test:
```python
# tests/test_methodology_validation.py
"""Methodology validation: the verification module recovers the injected effect.

This is not 1 of 354+ tests. It is THE test that proves the measurement approach
is unbiased. The data generator injects a known 30pp intervention effect with
structured noise (failures, re-opens, null results, assignment errors).
The verification module must recover the injected effect within confidence bounds
AND reject the trivial case where the data has no variance.
"""
import pandas as pd
from retail_ops_control_tower.verification.analytics import (
    recover_injected_effect,
    generate_verification_report,
)

def test_verification_recovers_injected_effect():
    outcomes = pd.read_csv("data/sample/intervention_outcomes.csv")
    result = recover_injected_effect(outcomes, injected_effect=0.30)
    assert result["within_confidence_bounds"] is True
    assert abs(result["estimated_effect"] - 0.30) < 0.05

def test_methodology_survives_noise():
    """Data MUST contain variance — trivial recovery is not persuasive."""
    outcomes = pd.read_csv("data/sample/intervention_outcomes.csv")
    # Must have non-trivial noise
    assert outcomes["resolved"].mean() < 0.75, (
        f"Intervention rate {outcomes['resolved'].mean():.1%} too high — "
        "data looks trivially injected. Real data has failures."
    )
    assert outcomes["control_resolved"].mean() > 0.10, (
        f"Control rate {outcomes['control_resolved'].mean():.1%} too low — "
        "data looks trivially injected. Real data has spontaneous resolution."
    )
    # Must have failed interventions
    failed_share = (outcomes["resolved"] == False).mean()
    assert failed_share > 0.10, (
        f"Only {failed_share:.1%} unresolved — need ~20%+ for realistic noise"
    )
    # Must redistribute the effect
    result = recover_injected_effect(outcomes, injected_effect=0.30)
    assert result["within_confidence_bounds"] is True

def test_noise_structured_not_random():
    """Data must have structure (null results for specific types, not just jitter)."""
    outcomes = pd.read_csv("data/sample/intervention_outcomes.csv")
    report = generate_verification_report(outcomes, injected_effect=0.30)
    # At least one exception type should have a null or near-zero effect
    by_type = report.get("by_exception_type", {})
    null_effects = [t for t, v in by_type.items()
                    if abs(v.get("estimated_effect", 0.30) - 0.30) > 0.15]
    assert len(null_effects) >= 1, (
        f"Expected at least 1 exception type with null effect, got {len(null_effects)}. "
        "Real interventions don't work for every exception type."
    )
```

**Step 2:** Run test:
```
.venv/bin/pytest tests/test_methodology_validation.py -v
```
Expected: 2 passed

**Step 3:** Commit:
Stage and commit when ready:
```bash
git add tests/test_methodology_validation.py
git commit -m "test: add methodology validation — recovers injected effect within bounds"
```
(Do not push. After all verifications pass, present the diff for user review.)

---

### Task 11: Cut dashboard to 5 question-named views (Day 4)

**Objective:** Rewrite `dashboard/app.py` from 514 lines to ~200 lines with question-named views.

**Files:**
- Modify: `dashboard/app.py` (rewrite, ~200 lines)

**UI labeling rule:**
Each view sidebar label MUST be the question, not the chart title.
- Correct: "What needs attention today?" | "What do I fix first?"
- Wrong: "Exception Backlog" | "AM Performance"

Any view exceeding 50 lines of inline code must be refactored into a section module.

**Step 1:** Rewrite `app.py` with 5 views (~200 lines):

| View # | Sidebar label (question) | Role | When |
|---|---|---|---|
| 1 | "What needs attention today?" | Ops Lead | Morning |
| 2 | "What do I fix first?" | Ops Lead | Daily |
| 3 | "What's about to breach?" | Ops Lead | Hourly |
| 4 | "Which AM needs a call?" | Ops Lead | Weekly |
| 5 | "Are campaigns on track?" | Ops Lead | Weekly |

Keep section modules in `retail_ops_control_tower/dashboard/sections/*.py` unchanged. Only change what `app.py` renders.

**Step 2:** Run existing tests:
```bash
.venv/bin/pytest tests/test_smoke.py -v
```
Expected: PASS

**Step 3:** Verify dashboard runs and views are question-named:
```bash
.venv/bin/streamlit run dashboard/app.py --server.headless true
```
Expected: No errors on startup, sidebar shows 6 entries starting with question marks (e.g. "What needs attention today?")

**Step 3b:** Verify disclosure rule compliance:
```bash
grep -A 0 -n "measurement methodology" dashboard/app.py
```
Expected: At least one match in the verification view section

**Step 4:** Commit:
Stage and commit when ready:
```bash
git add dashboard/app.py
git commit -m "refactor: cut dashboard to 5 question-named views"
```
(Do not push. After all verifications pass, present the diff for user review.)

---

### Task 12: Add action queue page to dashboard (Day 5)

**Objective:** Add one new Streamlit page: action queue with assign/resolve state via SQLite.

**Files:**
- Create: `retail_ops_control_tower/dashboard/action_queue.py`
- Modify: `dashboard/app.py` (add View 6)
- Create: `tests/test_action_queue.py`

**Step 1:** Write failing test:
```python
# tests/test_action_queue.py
import sqlite3
from retail_ops_control_tower.dashboard.action_queue import init_db, assign_exception, resolve_exception, get_queue

def test_assign_and_resolve():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    assign_exception(conn, "EXC-007", "Marcus Lee", "phone_call")
    queue = get_queue(conn)
    assert len(queue) == 1
    assert queue[0]["status"] == "assigned"
    resolve_exception(conn, "EXC-007", "resolved", "Confirmed via phone")
    queue = get_queue(conn, status="resolved")
    assert len(queue) == 1
    assert queue[0]["status"] == "resolved"
```

**Step 2:** Run test, verify failure:
```
.venv/bin/pytest tests/test_action_queue.py -v
```
Expected: FAIL — `ModuleNotFoundError`

**Step 3:** Implement `action_queue.py` (SQLite-backed assign/resolve/get functions, ~40 lines)

**Step 4:** Run test, verify pass:
```
.venv/bin/pytest tests/test_action_queue.py -v
```
Expected: 1 passed

**Step 5:** Add View 6 to `app.py` (action queue UI with assign form + queue table + resolve form, ~40 lines)

**Step 6:** Run all tests:
```bash
.venv/bin/pytest tests/ -v --tb=short
```
Expected: All pass

**Step 7:** Commit:
Stage and commit when ready:
```bash
git add retail_ops_control_tower/dashboard/action_queue.py dashboard/app.py tests/test_action_queue.py
git commit -m "feat: add action queue page with assign/resolve state"
```
(Do not push. After all verifications pass, present the diff for user review.)

---

### Task 13: Fill README verification placeholders (Day 3)

**Objective:** Replace `[placeholder]` in README with real verification results from the JSON.

**Files:**
- Modify: `README.md`

**Step 1:** Read verification results:
```bash
.venv/bin/python -c "import json; print(json.dumps(json.load(open('data/processed/verification_results.json')), indent=2))"
```

**Step 2:** Replace placeholder in README with actual numbers (intervention rate, control rate, estimated effect, Cohen's h, pass/fail)

**Step 3:** Expand limitations section with 4 bullet points (simulated data, no causal inference, single snapshot, no real-time feeds)

**Step 4:** Commit:
Stage and commit when ready:
```bash
git add README.md
git commit -m "docs: fill verification results and expand limitations section"
```
(Do not push. After all verifications pass, present the diff for user review.)

---

### Task 14: Write decision memo (Day 6)

**Objective:** Write 1-page decision memo with 3 recommendations and money attached.

**Files:**
- Create: `docs/decision_memo.md`

**Step 1:** Write the memo with structure:
- To/From/Date/Re header
- Summary (3 actions, $3,750 cost, 80% risk addressed)
- 3 recommendations: (1) 15 SKU transfers ($3,750 → $46,500, ROI 12.4×), (2) Focus 47 watchlist (4 AM hours/week), (3) North region assortment audit (2 weeks)
- "What we are NOT recommending" section (no per-rep review, no region-wide intervention)
- Methodology note (matched comparison, 30pp effect recovered)
- DPR signature line

**Step 2:** Commit:
Stage and commit when ready:
```bash
git add docs/decision_memo.md
git commit -m "docs: add 1-page decision memo with 3 recommendations"
```
(Do not push. After all verifications pass, present the diff for user review.)

---

### Task 15: Write walkthrough video script (Day 7)

**Objective:** Script for 2-minute video: Store S-048 quantity mismatch through the full loop.

**Files:**
- Create: `docs/walkthrough_script.md`

**Step 1:** Write the script with 6 sections:
- Opening (0:00-0:10): "100 stores, 1,603 exceptions, this is how we caught one"
- The exception (0:10-0:30): Store S-048, 47 shipped vs 37 received, 21% variance
- The ranking (0:30-0:50): Priority #2, assigned to David Park
- The intervention (0:50-1:10): DC count action, resolved in 1 day, control took 14
- The verification (1:10-1:30): 58% vs 29%, 30pp effect recovered
- The loop + close (1:30-2:00): loop diagram, link to decision memo

**Step 2:** Commit:
Stage and commit when ready:
```bash
git add docs/walkthrough_script.md
git commit -m "docs: add 2-minute walkthrough video script"
```
(Do not push. After all verifications pass, present the diff for user review.)

---

### Task 16: Final README pass and push (Day 7)

**Objective:** Final README polish — cross-link memo and video, verify all numbers are real, update test count.

**Files:**
- Modify: `README.md`

**Step 1:** Add artifacts section to README with links to:
- Decision memo (`docs/decision_memo.md`)
- Walkthrough script (`docs/walkthrough_script.md`)
- Analytical report (`docs/analytical_report_hermes.html`)
- Insight engine narrative (`docs/insight_engine_story.md`)

**Step 2:** Update test count in README to reflect new tests (354 + methodology validation + action queue + verification)

**Step 3:** Run full test suite:
```bash
.venv/bin/pytest tests/ -v --tb=short
```
Expected: All pass

**Step 4:** Commit and push:
```bash
git add README.md
git commit -m "docs: final README pass — cross-link artifacts and update test count"
(Push only after user approves the final diff.)
```

**Verify:** `git log --oneline` shows all task commits on current branch.

---

## Verification
**Verify:**
- [ ] `data/sample/actions.csv` exists with ~400-600 rows, outcomes show ~55-65% resolved
- [ ] `data/sample/intervention_outcomes.csv` exists with matched pairs, intervention rate ~55-65%, control ~25-35%
- [ ] `data/processed/verification_results.json` exists with recovery within bounds
- [ ] `tests/test_methodology_validation.py` passes all 3 tests (recovery + structured noise + by-type variance)
- [ ] `dashboard/app.py` is ~200 lines with 5 question-named views + 1 action queue view
- [ ] Action queue page works: can assign and resolve exceptions
- [ ] `docs/decision_memo.md` exists with 3 recommendations and money attached
- [ ] `docs/walkthrough_script.md` exists with 2-minute Store 47 script
- [ ] README has coffee chain framing, DPR line, loop diagram, real verification numbers, limitations section
- [ ] All 360+ tests pass (added 6 methodology + 4 new tests)
- [ ] All verification-displaying files contain the disclosure sentence (see DISCLOSURE RULE)
- [ ] `.hermes/lessons/retail-control-tower.md` exists with session summaries
