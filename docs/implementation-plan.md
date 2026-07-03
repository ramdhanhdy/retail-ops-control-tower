# Implementation Plan

> Scope: Map every module to its file path, define implementation phases with test targets and commit gates, and specify the CLI scripts.
>
> Source documents:
> - `docs/prd.md` (product requirements, architecture, acceptance criteria)
> - `docs/data-dictionary.md` (data model, 8 tables, 164 fields)
> - `docs/research/synthesis.md` (5 project components)
> - `docs/scope-guard.md` (in-scope and non-goals)
>
> This document is the engineering blueprint. An implementer should be able to start at Phase 1 and work through Phase 6 without needing to re-derive the architecture.

## 1. Package structure

The project is a Python package named `retail_ops_control_tower`, installed from source. The package lives at the repo root alongside tests, docs, and configuration.

```
retail-ops-control-tower/
|
|-- pyproject.toml                    # Package metadata, dependencies, CLI scripts
|-- .gitignore                        # Python/IDE/OS ignores
|-- LICENSE                           # MIT license
|-- README.md                         # Install-from-source instructions, quickstart
|
|-- retail_ops_control_tower/         # Main package
|   |-- __init__.py                   # Package version, public API exports
|   |-- __main__.py                   # `python -m retail_ops_control_tower` entry point
|   |-- cli.py                        # CLI argument parsing, command dispatch
|   |
|   |-- config.py                     # Configuration dataclass, default values, thresholds
|   |-- constants.py                  # Enums, exception type definitions, severity tiers, SLA windows
|   |
|   |-- models/                       # Data model (dataclasses for all 8 tables)
|   |   |-- __init__.py               # Model exports
|   |   |-- stores.py                 # Store dataclass
|   |   |-- campaigns.py              # Campaign dataclass
|   |   |-- allocation_plan.py        # AllocationPlan dataclass
|   |   |-- dispatch.py               # Dispatch dataclass
|   |   |-- store_confirmations.py    # StoreConfirmation dataclass
|   |   |-- photo_proofs.py           # PhotoProof dataclass
|   |   |-- sales_daily.py            # SalesDaily dataclass
|   |   |-- issues.py                 # Issue dataclass
|   |
|   |-- simulation/                   # Data simulation layer
|   |   |-- __init__.py               # Simulation exports
|   |   |-- generator.py              # Main simulation orchestrator
|   |   |-- stores.py                 # Store network generator
|   |   |-- campaigns.py              # Campaign generator
|   |   |-- allocation.py             # Allocation plan generator
|   |   |-- dispatch.py               # Dispatch/shipment generator
|   |   |-- confirmations.py          # Store confirmation/visit generator
|   |   |-- photo_proofs.py           # Photo proof metadata generator
|   |   |-- sales.py                  # Daily sales generator
|   |   |-- seed.py                   # Seeded failure mode injector (17 T01 + 20 T02 modes)
|   |
|   |-- reconciliation/              # Reconciliation engine
|   |   |-- __init__.py               # Reconciliation exports
|   |   |-- engine.py                 # Main reconciliation orchestrator
|   |   |-- formulas.py               # 16 formulas (6 process, 6 performance, 4 risk)
|   |   |-- rules.py                  # 24 exception rules (EX-01 to EX-24)
|   |   |-- taxonomy.py               # Rule-to-taxonomy mapping (24 rules -> 8 types)
|   |
|   |-- exceptions/                   # Exception management system
|   |   |-- __init__.py               # Exception exports
|   |   |-- manager.py                # Exception management orchestrator
|   |   |-- severity.py               # Severity matrix, severity assignment
|   |   |-- priority.py               # Priority score formula
|   |   |-- sla.py                    # SLA aging, buckets, status, pause logic
|   |   |-- state_machine.py          # Exception lifecycle state machine
|   |   |-- action_list.py            # Daily action list generator
|   |   |-- playbook.py               # Codified action playbook (8 types -> default actions)
|   |   |-- root_cause.py             # Root cause taxonomy
|   |
|   |-- dashboard/                    # KPI dashboard
|   |   |-- __init__.py               # Dashboard exports
|   |   |-- kpis.py                   # 10 MVP KPI computations + threshold tables
|   |   |-- sections/                 # 6 dashboard sections
|   |   |   |-- __init__.py           # Section exports
|   |   |   |-- executive_tiles.py    # Section 1: Executive KPI tiles
|   |   |   |-- area_manager.py       # Section 2: Area Manager breakdowns
|   |   |   |-- store_status.py       # Section 3: Store status table
|   |   |   |-- campaign_performance.py # Section 4: Campaign performance view
|   |   |   |-- exception_backlog.py   # Section 5: Exception backlog view
|   |   |   |-- sla_aging.py          # Section 6: SLA / aging view
|   |   |-- render.py                 # Dashboard renderer (text + HTML)
|   |
|   |-- reports/                      # Report module
|   |   |-- __init__.py               # Report exports
|   |   |-- generator.py              # Report orchestrator
|   |   |-- templates.py              # Report templates (7 types)
|   |
|   |-- demo/                         # Demo story runner
|   |   |-- __init__.py               # Demo exports
|   |   |-- story.py                  # Summer Peach LTO 2026 demo runner
|   |   |-- scenarios.py              # Day 1, Day 7, Day 14 scenario definitions
|   |
|   |-- io/                           # Data I/O
|   |   |-- __init__.py               # I/O exports
|   |   |-- json_store.py             # JSON file reader/writer for all 8 tables
|   |   |-- serializers.py            # Dataclass <-> dict serialization
|   |
|   |-- validation.py                 # Validation rules (V-01 to V-15)
|
|-- scripts/                          # Standalone scripts
|   |-- generate_demo_data.py         # Quick script to generate demo dataset
|
|-- tests/                            # Test suite
|   |-- __init__.py
|   |-- conftest.py                   # Shared fixtures, data factories, seed
|   |-- test_models.py                # T-01: model construction and validation
|   |-- test_simulation.py            # T-02: simulation generation
|   |-- test_reconciliation.py        # T-03: 16 formulas, worked example
|   |-- test_exception_rules.py       # T-04: 24 exception rules
|   |-- test_exception_taxonomy.py    # T-05: rule-to-taxonomy mapping
|   |-- test_severity.py              # T-06: priority score worked examples
|   |-- test_sla.py                   # T-07: SLA aging, status, pause
|   |-- test_state_machine.py         # T-08: state transitions
|   |-- test_action_list.py          # T-09: action list generation
|   |-- test_kpis.py                  # T-10: 10 KPI computations
|   |-- test_thresholds.py            # T-11: threshold color boundaries
|   |-- test_dashboard.py            # T-12: 6 dashboard sections render
|   |-- test_reports.py               # T-13: 7 report types generate
|   |-- test_demo.py                  # T-14: demo story end-to-end
|   |-- test_cli.py                   # T-15: CLI commands
|   |-- test_regression.py            # T-16: consistency checks
|
|-- docs/                             # Documentation
|   |-- prd.md                        # Product requirements document
|   |-- data-dictionary.md            # Data dictionary (8 tables, 164 fields)
|   |-- implementation-plan.md        # This document
|   |-- scope-guard.md                # Scope guard
|   |-- research/                     # Research documents (T01-T04)
|   |   |-- retail-campaign-execution.md
|   |   |-- allocation-reconciliation.md
|   |   |-- ops-kpi-scorecard.md
|   |   |-- exception-management.md
|   |   |-- synthesis.md
|
|-- output/                           # Generated data (gitignored)
|   |-- *.json                        # JSON output files for 8 tables
|   |-- reports/                      # Generated reports
```

## 2. CLI scripts

Three CLI commands defined in `pyproject.toml` as entry points. All three are thin wrappers around the package's public API.

### retail-ops-generate-data

```
retail-ops-generate-data [--stores N] [--campaign CAMPAIGN_ID] [--skus N] [--days N] [--seed N] [--output-dir PATH]
```

- **Module:** `retail_ops_control_tower.cli.generate_data`
- **Purpose:** Run the data simulation layer to generate all 8 tables and write JSON output.
- **Default:** 40 stores, Summer Peach LTO 2026, 12 SKUs, 28 days, seed=42, output to `./output/`.
- **Output:** 8 JSON files (`stores.json`, `campaigns.json`, `allocation_plan.json`, `dispatch.json`, `store_confirmations.json`, `photo_proofs.json`, `sales_daily.json`, `issues.json`).

### retail-ops-build-exceptions

```
retail-ops-build-exceptions [--input-dir PATH] [--output-dir PATH] [--aging-date YYYY-MM-DD]
```

- **Module:** `retail_ops_control_tower.cli.build_exceptions`
- **Purpose:** Run the reconciliation engine and exception management system on pre-generated data. Reads JSON, evaluates 24 rules, computes priority scores, generates action list.
- **Default:** Input from `./output/`, output to `./output/`, aging date = today.
- **Output:** Enriched `issues.json` with priority scores and SLA status, `action_list.json`.

### retail-ops-report

```
retail-ops-report [--input-dir PATH] [--output-dir PATH] [--section SECTION] [--format text|html] [--aging-date YYYY-MM-DD]
```

- **Module:** `retail_ops_control_tower.cli.report`
- **Purpose:** Generate dashboard sections and reports from enriched data.
- **Default:** All sections, text format, input from `./output/`, output to `./output/reports/`.
- **Output:** Report files in `./output/reports/` (R-01 through R-07).

### python -m retail_ops_control_tower

```
python -m retail_ops_control_tower [--help] [command] [args]
```

- **Module:** `retail_ops_control_tower.__main__`
- **Purpose:** Unified entry point that dispatches to the three commands above.

## 3. Module-to-file-path mapping

This table maps every module described in the PRD architecture to its file path. An implementer uses this to find where to write each piece of logic.

| Module | Responsibility | File path |
|--------|---------------|-----------|
| Configuration | Config dataclass, defaults, thresholds | `retail_ops_control_tower/config.py` |
| Constants/Enums | Exception types, severity tiers, SLA windows, states | `retail_ops_control_tower/constants.py` |
| Store model | Store dataclass (12 fields) | `retail_ops_control_tower/models/stores.py` |
| Campaign model | Campaign dataclass (15 fields) | `retail_ops_control_tower/models/campaigns.py` |
| AllocationPlan model | Allocation dataclass (13 fields) | `retail_ops_control_tower/models/allocation_plan.py` |
| Dispatch model | Dispatch dataclass (14 fields) | `retail_ops_control_tower/models/dispatch.py` |
| StoreConfirmation model | Confirmation dataclass (29 fields) | `retail_ops_control_tower/models/store_confirmations.py` |
| PhotoProof model | Photo proof dataclass (13 fields) | `retail_ops_control_tower/models/photo_proofs.py` |
| SalesDaily model | Sales dataclass (25 fields) | `retail_ops_control_tower/models/sales_daily.py` |
| Issue model | Issue dataclass (43 fields) | `retail_ops_control_tower/models/issues.py` |
| Validation | Rules V-01 to V-15 | `retail_ops_control_tower/validation.py` |
| Simulation orchestrator | Generate all 8 tables | `retail_ops_control_tower/simulation/generator.py` |
| Store generator | Synthetic store network | `retail_ops_control_tower/simulation/stores.py` |
| Campaign generator | Synthetic campaigns | `retail_ops_control_tower/simulation/campaigns.py` |
| Allocation generator | Allocation plan lines | `retail_ops_control_tower/simulation/allocation.py` |
| Dispatch generator | Shipments | `retail_ops_control_tower/simulation/dispatch.py` |
| Confirmation generator | Receiving + visit records | `retail_ops_control_tower/simulation/confirmations.py` |
| Photo proof generator | Photo metadata | `retail_ops_control_tower/simulation/photo_proofs.py` |
| Sales generator | Daily sales + on-hand | `retail_ops_control_tower/simulation/sales.py` |
| Failure mode injector | Seed 17+20 failure modes | `retail_ops_control_tower/simulation/seed.py` |
| Reconciliation orchestrator | Run formulas + rules | `retail_ops_control_tower/reconciliation/engine.py` |
| Formulas | 16 formulas (6 process, 6 perf, 4 risk) | `retail_ops_control_tower/reconciliation/formulas.py` |
| Exception rules | 24 rules (EX-01 to EX-24) | `retail_ops_control_tower/reconciliation/rules.py` |
| Taxonomy mapping | 24 rules -> 8 types | `retail_ops_control_tower/reconciliation/taxonomy.py` |
| Exception orchestrator | Manage exception lifecycle | `retail_ops_control_tower/exceptions/manager.py` |
| Severity matrix | Assign severity at raise time | `retail_ops_control_tower/exceptions/severity.py` |
| Priority score | Priority formula (1-200) | `retail_ops_control_tower/exceptions/priority.py` |
| SLA aging | Buckets, status, pause, escalation | `retail_ops_control_tower/exceptions/sla.py` |
| State machine | Transition validation | `retail_ops_control_tower/exceptions/state_machine.py` |
| Action list | Generate top 20 | `retail_ops_control_tower/exceptions/action_list.py` |
| Action playbook | 8 types -> default actions | `retail_ops_control_tower/exceptions/playbook.py` |
| Root cause taxonomy | 7 categories + sub-categories | `retail_ops_control_tower/exceptions/root_cause.py` |
| KPI computations | 10 MVP KPIs | `retail_ops_control_tower/dashboard/kpis.py` |
| Executive tiles | Section 1 | `retail_ops_control_tower/dashboard/sections/executive_tiles.py` |
| Area manager breakdown | Section 2 | `retail_ops_control_tower/dashboard/sections/area_manager.py` |
| Store status table | Section 3 | `retail_ops_control_tower/dashboard/sections/store_status.py` |
| Campaign performance | Section 4 | `retail_ops_control_tower/dashboard/sections/campaign_performance.py` |
| Exception backlog | Section 5 | `retail_ops_control_tower/dashboard/sections/exception_backlog.py` |
| SLA/aging view | Section 6 | `retail_ops_control_tower/dashboard/sections/sla_aging.py` |
| Dashboard renderer | Text + HTML rendering | `retail_ops_control_tower/dashboard/render.py` |
| Report generator | 7 report types | `retail_ops_control_tower/reports/generator.py` |
| Report templates | Template definitions | `retail_ops_control_tower/reports/templates.py` |
| Demo story runner | Summer Peach LTO 2026 | `retail_ops_control_tower/demo/story.py` |
| Demo scenarios | Day 1, 7, 14 definitions | `retail_ops_control_tower/demo/scenarios.py` |
| JSON I/O | Read/write 8 tables | `retail_ops_control_tower/io/json_store.py` |
| Serializers | Dataclass <-> dict | `retail_ops_control_tower/io/serializers.py` |
| CLI | Argument parsing, dispatch | `retail_ops_control_tower/cli.py` |

## 4. Implementation phases

Implementation is broken into 6 phases. Each phase has a goal, a table of tasks with test targets and done-when criteria, and a commit gate.

### Phase 1: Foundation (models, config, validation)

**Goal:** Define the data model, configuration, and validation rules. No business logic yet.

| Task | Module | Test target | Done when |
|------|--------|-------------|-----------|
| 1.1 Create pyproject.toml with package metadata, deps, CLI scripts | `pyproject.toml` | `pip install -e .` succeeds | Package installs, `retail-ops-generate-data --help` works |
| 1.2 Create config dataclass with defaults and thresholds | `config.py` | `test_config.py::test_defaults` | Config constructs with demo defaults |
| 1.3 Create constants and enums | `constants.py` | `test_constants.py::test_enums` | All enums have correct values |
| 1.4 Create 8 model dataclasses | `models/*.py` | `test_models.py::test_all_models` | Each model constructs with example data |
| 1.5 Create validation rules V-01 to V-15 | `validation.py` | `test_validation.py::test_all_rules` | Valid data passes; invalid data raises ValidationError |
| 1.6 Create JSON I/O and serializers | `io/json_store.py`, `io/serializers.py` | `test_io.py::test_roundtrip` | Dataclass -> dict -> JSON -> dict -> dataclass preserves data |

**Commit gate:** `pytest -q` passes for all foundation tests. `python -m retail_ops_control_tower --help` works.

### Phase 2: Data simulation layer

**Goal:** Generate all 8 tables with synthetic data. Deterministic with seed.

| Task | Module | Test target | Done when |
|------|--------|-------------|-----------|
| 2.1 Store network generator (40 stores, 5 regions) | `simulation/stores.py` | `test_simulation.py::test_stores` | 40 stores, 5 regions, 4 formats |
| 2.2 Campaign generator | `simulation/campaigns.py` | `test_simulation.py::test_campaigns` | 1 campaign with correct dates and SKU list |
| 2.3 Allocation plan generator (480 rows) | `simulation/allocation.py` | `test_simulation.py::test_allocation` | 480 rows, planned_quantity > 0, hero SKU flagged |
| 2.4 Dispatch generator (shipments) | `simulation/dispatch.py` | `test_simulation.py::test_dispatch` | 480 shipments, shipped_quantity varies from planned |
| 2.5 Confirmation generator (receipts + visits) | `simulation/confirmations.py` | `test_simulation.py::test_confirmations` | 480 confirmations, visit_status varies, audit scores 0-100 |
| 2.6 Photo proof generator | `simulation/photo_proofs.py` | `test_simulation.py::test_photo_proofs` | ~400 proofs, some missing (triggers exception type 3) |
| 2.7 Sales generator (13,440 rows) | `simulation/sales.py` | `test_simulation.py::test_sales` | ~13K rows, units_sold >= 0, on_hand >= 0 |
| 2.8 Failure mode injector | `simulation/seed.py` | `test_simulation.py::test_failure_modes` | Failure modes seeded: late setup, missing photo, quantity mismatch, stockout, low sell-through |
| 2.9 Simulation orchestrator | `simulation/generator.py` | `test_simulation.py::test_full_generation` | All 8 tables generated, JSON written, deterministic with seed=42 |

**Commit gate:** `retail-ops-generate-data --seed 42` produces 8 JSON files with correct row counts. Re-running with same seed produces identical output.

### Phase 3: Reconciliation engine

**Goal:** Compute all 16 formulas and evaluate all 24 exception rules.

| Task | Module | Test target | Done when |
|------|--------|-------------|-----------|
| 3.1 Implement 6 process compliance formulas | `reconciliation/formulas.py` | `test_reconciliation.py::test_process_formulas` | Allocation accuracy, fill rate, receiving accuracy, on-time receipt, inventory accuracy, cycle time |
| 3.2 Implement 6 sales performance formulas | `reconciliation/formulas.py` | `test_reconciliation.py::test_performance_formulas` | Sell-through, full-price, plan vs actual, door index, sales/sqft, markdown intensity |
| 3.3 Implement 4 risk formulas | `reconciliation/formulas.py` | `test_reconciliation.py::test_risk_formulas` | WOC, forward WOC, stockout risk, overstock risk |
| 3.4 Test worked example (200/190/188/150) | `reconciliation/formulas.py` | `test_reconciliation.py::test_worked_example` | 94% accuracy, 95% fill, 98.95% receiving, 79.8% sell-through, 1.01 WOC |
| 3.5 Implement 24 exception rules (EX-01 to EX-24) | `reconciliation/rules.py` | `test_exception_rules.py::test_all_24_rules` | Each rule triggers with known inputs |
| 3.6 Implement taxonomy mapping | `reconciliation/taxonomy.py` | `test_exception_taxonomy.py::test_mapping` | All 24 rules map to correct 8-type taxonomy |
| 3.7 Reconciliation orchestrator | `reconciliation/engine.py` | `test_reconciliation.py::test_engine` | Engine enriches allocation_plan, dispatch, sales_daily with computed fields |

**Commit gate:** All 16 formulas produce correct results on the worked example. All 24 rules trigger correctly. Taxonomy mapping is complete.

### Phase 4: Exception management system

**Goal:** Manage exception lifecycle, scoring, SLA, and action list.

| Task | Module | Test target | Done when |
|------|--------|-------------|-----------|
| 4.1 Severity matrix and assignment | `exceptions/severity.py` | `test_severity.py::test_severity_matrix` | Severity assigned correctly for all 8 types at watch/critical thresholds |
| 4.2 Priority score formula | `exceptions/priority.py` | `test_severity.py::test_priority_score` | 4 worked examples: 400, 265, 141, 300 |
| 4.3 SLA aging (buckets, status, pause) | `exceptions/sla.py` | `test_sla.py::test_aging_buckets` | 4 buckets correct; SLA status correct; pause logic correct |
| 4.4 SLA auto-escalation | `exceptions/sla.py` | `test_sla.py::test_auto_escalation` | Watch > 48h escalates; 30+ days -> VP |
| 4.5 State machine | `exceptions/state_machine.py` | `test_state_machine.py::test_transitions` | Valid transitions succeed; invalid raise InvalidTransition |
| 4.6 Reopen logic | `exceptions/state_machine.py` | `test_state_machine.py::test_reopen` | Reopen creates new ID, links parent, increments reopen_count |
| 4.7 Action list generator | `exceptions/action_list.py` | `test_action_list.py::test_generation` | Top 20 sorted by priority DESC, age DESC, ID ASC; 18 fields per row |
| 4.8 Action playbook | `exceptions/playbook.py` | `test_action_list.py::test_playbook` | 8 types -> correct default action |
| 4.9 Root cause taxonomy | `exceptions/root_cause.py` | `test_action_list.py::test_root_cause` | 7 categories with sub-categories |
| 4.10 Exception orchestrator | `exceptions/manager.py` | `test_exceptions.py::test_manager` | Manager raises, scores, and manages exceptions from reconciliation output |

**Commit gate:** Priority scores match worked examples. State machine rejects invalid transitions. Action list generates top 20 with all 18 fields.

### Phase 5: KPI dashboard and reports

**Goal:** Compute 10 KPIs, render 6 sections, generate 7 reports.

| Task | Module | Test target | Done when |
|------|--------|-------------|-----------|
| 5.1 KPI computations (10 KPIs) | `dashboard/kpis.py` | `test_kpis.py::test_all_10_kpis` | Each KPI returns numeric value |
| 5.2 Threshold tables | `dashboard/kpis.py` | `test_thresholds.py::test_boundaries` | Green/amber/red correct at boundaries |
| 5.3 Section 1: Executive tiles | `dashboard/sections/executive_tiles.py` | `test_dashboard.py::test_section_1` | Renders tiles with KPI values and colors |
| 5.4 Section 2: Area manager | `dashboard/sections/area_manager.py` | `test_dashboard.py::test_section_2` | Renders per-region breakdown |
| 5.5 Section 3: Store status | `dashboard/sections/store_status.py` | `test_dashboard.py::test_section_3` | Renders store table with health scores |
| 5.6 Section 4: Campaign performance | `dashboard/sections/campaign_performance.py` | `test_dashboard.py::test_section_4` | Renders campaign tiles and store table |
| 5.7 Section 5: Exception backlog | `dashboard/sections/exception_backlog.py` | `test_dashboard.py::test_section_5` | Renders ranked exceptions with aging buckets |
| 5.8 Section 6: SLA/aging | `dashboard/sections/sla_aging.py` | `test_dashboard.py::test_section_6` | Renders SLA tiles and aging distribution |
| 5.9 Dashboard renderer (text + HTML) | `dashboard/render.py` | `test_dashboard.py::test_render` | Both text and HTML render without error |
| 5.10 Report generator (7 types) | `reports/generator.py`, `reports/templates.py` | `test_reports.py::test_all_reports` | 7 reports generate with expected sections |

**Commit gate:** All 6 sections render. All 7 reports generate. All 10 KPIs compute with correct thresholds.

### Phase 6: Demo story and CLI integration

**Goal:** Run the Summer Peach LTO 2026 demo end-to-end. Wire up CLI commands.

| Task | Module | Test target | Done when |
|------|--------|-------------|-----------|
| 6.1 Demo scenario definitions (Day 1, 7, 14) | `demo/scenarios.py` | `test_demo.py::test_scenarios` | 3 scenarios defined with correct parameters |
| 6.2 Demo story runner | `demo/story.py` | `test_demo.py::test_demo_story_e2e` | Day 1 -> Day 14 runs without errors; action list produced |
| 6.3 CLI: generate-data command | `cli.py` | `test_cli.py::test_generate_data` | Command produces 8 JSON files |
| 6.4 CLI: build-exceptions command | `cli.py` | `test_cli.py::test_build_exceptions` | Command enriches issues and produces action list |
| 6.5 CLI: report command | `cli.py` | `test_cli.py::test_report` | Command produces 7 report files |
| 6.6 CLI: python -m entry point | `__main__.py` | `test_cli.py::test_module_entry` | `python -m retail_ops_control_tower --help` works |
| 6.7 Regression: consistency checks | `tests/test_regression.py` | `test_regression.py::test_consistency_checks` | 8 types, 24 rules, 10 KPIs, 4 buckets, 3 tiers, all fields, synthetic |
| 6.8 README and documentation | `README.md` | Manual review | Install instructions, quickstart, demo command |

**Commit gate:** Demo story runs end-to-end. All CLI commands work. All regression tests pass. Full test suite passes in under 30 seconds.

## 5. Dependency list

Dependencies are documented in `pyproject.toml`. The project uses only the Python standard library for the MVP, with `pytest` as the only development dependency.

| Dependency | Type | Purpose | Required |
|------------|------|---------|----------|
| Python 3.11+ | Runtime | Language | Yes |
| pytest | Dev | Testing | Yes (dev) |
| dataclasses | Stdlib | Data models | Yes (stdlib) |
| json | Stdlib | Data I/O | Yes (stdlib) |
| argparse | Stdlib | CLI | Yes (stdlib) |
| random | Stdlib | Seeded generation | Yes (stdlib) |
| datetime | Stdlib | Date/time handling | Yes (stdlib) |
| enum | Stdlib | Enumerations | Yes (stdlib) |
| dataclasses | Stdlib | Dataclass support | Yes (stdlib) |

No external runtime dependencies for the MVP. This keeps the install simple and the project self-contained.

## 6. Risk register

### Technical risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Sales_daily table is large (13K rows) and slow to process | Low | Medium | Use dict-based lookups; SQLite fallback if needed |
| Exception rules have edge cases not covered by research | Medium | Low | Test against worked examples; document assumptions |
| State machine transitions are incomplete | Low | High | Exhaustive transition matrix test (all from->to pairs) |
| Threshold values need tuning | High | Low | Centralize in config.py; document as defaults |

### Scope risks

| Risk | Mitigation |
|------|------------|
| Scope creep into v2 features (WSSI, transfers, performance KPIs) | Scope guard enforced; v2 items documented but not built |
| Demo story requires manual data tuning | Use seeded failure mode injector; deterministic scenarios |
| Report format requirements unclear | Start with text; HTML is optional layer on top |

### Methodological risks

| Risk | Mitigation |
|------|------------|
| Simulated data does not reflect real retail patterns | Document as synthetic; cite public sources for patterns |
| Threshold defaults are arbitrary | Cite T03 research; document as starting points, not benchmarks |
| Priority formula is not validated against real ops | Document as portfolio model; cite T04 derivation |

## 7. Cross-document consistency

The implementation plan maintains the following consistency rules with the research documents and PRD:

1. **8 exception types:** `constants.py` defines exactly 8 types. No more, no less.
2. **24 exception rules:** `reconciliation/rules.py` implements exactly EX-01 to EX-24.
3. **10 MVP KPIs:** `dashboard/kpis.py` implements exactly the 10 from T03 MVP.
4. **4 aging buckets:** `exceptions/sla.py` uses 0-5 / 6-15 / 16-30 / 30+.
5. **3 severity tiers:** `constants.py` defines critical, watch, info.
6. **39 + 45 tracker fields:** `models/` implements all fields from T01 and T02. Field count reconciliation in `data-dictionary.md`.
7. **Synthetic data only:** No external data sources, no API calls, no real company references.

## 8. Definition of done

The project is done when:

1. All 6 phases are complete and their commit gates pass.
2. The full test suite (`pytest -q`) passes with 0 failures.
3. The demo story runs end-to-end without errors.
4. All 3 CLI commands work and produce expected output.
5. All 8 data tables are generated with correct row counts.
6. All 16 formulas compute correctly on the worked example.
7. All 24 exception rules trigger correctly.
8. All 10 MVP KPIs compute with correct thresholds.
9. All 6 dashboard sections render without error.
10. All 7 report types generate without error.
11. All 7 cross-document consistency checks pass.
12. No hardcoded `/opt/data` paths in package code.
13. No em dashes or en dashes in published docs (use normal hyphens).
14. README has install-from-source instructions (no PyPI claim).
