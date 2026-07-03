"""Tests for constants and configuration."""

from __future__ import annotations


def test_exception_type_count():
    from retail_ops_control_tower.constants import ExceptionType
    assert len(list(ExceptionType)) == 8


def test_severity_count():
    from retail_ops_control_tower.constants import Severity
    assert len(list(Severity)) == 3


def test_aging_bucket_count():
    from retail_ops_control_tower.constants import AgingBucket
    assert len(list(AgingBucket)) == 4


def test_severity_weights():
    from retail_ops_control_tower.constants import SEVERITY_WEIGHTS, Severity
    assert SEVERITY_WEIGHTS[Severity.CRITICAL] == 3
    assert SEVERITY_WEIGHTS[Severity.WATCH] == 2
    assert SEVERITY_WEIGHTS[Severity.INFO] == 1


def test_exception_type_owners():
    from retail_ops_control_tower.constants import (
        EXCEPTION_TYPE_OWNERS, ExceptionType,
    )
    assert len(EXCEPTION_TYPE_OWNERS) == 8
    for et in ExceptionType:
        assert et in EXCEPTION_TYPE_OWNERS


def test_exception_type_sla_hours():
    from retail_ops_control_tower.constants import (
        EXCEPTION_TYPE_SLA_HOURS, ExceptionType,
    )
    assert len(EXCEPTION_TYPE_SLA_HOURS) == 8
    assert EXCEPTION_TYPE_SLA_HOURS[ExceptionType.STOCKOUT_RISK] == 24
    assert EXCEPTION_TYPE_SLA_HOURS[ExceptionType.OVERSTOCK_RISK] == 168


def test_config_defaults():
    from retail_ops_control_tower.config import DEFAULT_CONFIG
    assert DEFAULT_CONFIG.store_count == 40
    assert DEFAULT_CONFIG.sku_count == 12
    assert DEFAULT_CONFIG.campaign_days == 28
    assert DEFAULT_CONFIG.seed == 42
    assert DEFAULT_CONFIG.action_list_size == 20


def test_config_immutable():
    from retail_ops_control_tower.config import DEFAULT_CONFIG
    import dataclasses
    assert dataclasses.is_dataclass(DEFAULT_CONFIG)
    # frozen=True means setattr should fail
    try:
        DEFAULT_CONFIG.store_count = 99
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass  # frozen dataclasses raise AttributeError on set
