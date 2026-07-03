"""Baseline import tests for all package modules.

Verifies that the package and all submodules import cleanly.
"""

from __future__ import annotations


def test_package_import():
    """Package imports and exposes __version__."""
    import retail_ops_control_tower
    assert hasattr(retail_ops_control_tower, "__version__")
    assert retail_ops_control_tower.__version__ == "0.1.0"


def test_config_import():
    from retail_ops_control_tower.config import Config, DEFAULT_CONFIG
    assert DEFAULT_CONFIG.store_count == 40
    assert DEFAULT_CONFIG.seed == 42


def test_constants_import():
    from retail_ops_control_tower.constants import (
        ExceptionType, Severity, IssueStatus, AgingBucket, ThresholdColor,
    )
    # 8 exception types
    assert len(list(ExceptionType)) == 8
    # 3 severity tiers
    assert len(list(Severity)) == 3
    # 4 aging buckets
    assert len(list(AgingBucket)) == 4
    # 8 issue statuses
    assert len(list(IssueStatus)) == 8


def test_validation_import():
    from retail_ops_control_tower.validation import ValidationError
    assert issubclass(ValidationError, Exception)


def test_models_import():
    from retail_ops_control_tower.models.stores import Store
    from retail_ops_control_tower.models.campaigns import Campaign
    from retail_ops_control_tower.models.allocation_plan import AllocationPlan
    from retail_ops_control_tower.models.dispatch import Dispatch
    from retail_ops_control_tower.models.store_confirmations import StoreConfirmation
    from retail_ops_control_tower.models.photo_proofs import PhotoProof
    from retail_ops_control_tower.models.sales_daily import SalesDaily
    from retail_ops_control_tower.models.issues import Issue


def test_simulation_import():
    from retail_ops_control_tower.simulation.generator import run_simulation
    assert callable(run_simulation)


def test_reconciliation_import():
    from retail_ops_control_tower.reconciliation.engine import run_reconciliation
    from retail_ops_control_tower.reconciliation.formulas import allocation_accuracy
    from retail_ops_control_tower.reconciliation.taxonomy import RULE_TO_TAXONOMY
    assert callable(run_reconciliation)
    assert len(RULE_TO_TAXONOMY) == 23  # 24 rules, 1 maps to missing photo (campaign modes)


def test_exceptions_import():
    from retail_ops_control_tower.exceptions.priority import compute_priority_score
    from retail_ops_control_tower.exceptions.sla import compute_aging_bucket
    from retail_ops_control_tower.exceptions.state_machine import can_transition
    from retail_ops_control_tower.exceptions.action_list import generate_action_list
    from retail_ops_control_tower.exceptions.playbook import get_default_action
    from retail_ops_control_tower.exceptions.root_cause import ROOT_CAUSE_TAXONOMY
    assert len(ROOT_CAUSE_TAXONOMY) == 7


def test_dashboard_import():
    from retail_ops_control_tower.dashboard.kpis import compute_kpi
    from retail_ops_control_tower.dashboard.render import render_dashboard
    assert callable(compute_kpi)
    assert callable(render_dashboard)


def test_reports_import():
    from retail_ops_control_tower.reports.generator import generate_reports
    from retail_ops_control_tower.reports.templates import REPORT_TYPES
    assert len(REPORT_TYPES) == 7


def test_demo_import():
    from retail_ops_control_tower.demo.story import run_demo
    from retail_ops_control_tower.demo.scenarios import SCENARIOS
    assert len(SCENARIOS) == 3


def test_io_import():
    from retail_ops_control_tower.io.json_store import (
        read_table, write_table, read_all_tables, write_all_tables,
    )
    from retail_ops_control_tower.io.serializers import to_dict, from_dict
    assert callable(read_table)
    assert callable(write_table)


def test_cli_import():
    from retail_ops_control_tower.cli import build_parser, main
    assert callable(build_parser)
    assert callable(main)
