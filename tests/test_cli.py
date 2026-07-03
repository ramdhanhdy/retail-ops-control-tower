"""Tests for CLI argument parsing and dispatch."""

from __future__ import annotations

import subprocess
import sys


def test_build_parser_has_three_commands():
    from retail_ops_control_tower.cli import build_parser
    parser = build_parser()
    # Find subparsers action
    subparsers_found = []
    for action in parser._actions:
        if hasattr(action, "choices") and isinstance(action.choices, dict):
            subparsers_found = list(action.choices.keys())
    assert "generate-data" in subparsers_found
    assert "build-exceptions" in subparsers_found
    assert "report" in subparsers_found


def test_module_help_works():
    """python -m retail_ops_control_tower --help should work."""
    result = subprocess.run(
        [sys.executable, "-m", "retail_ops_control_tower", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "Retail Operations Control Tower" in result.stdout or \
           "retail-ops-control-tower" in result.stdout.lower()


def test_generate_data_help():
    result = subprocess.run(
        [sys.executable, "-m", "retail_ops_control_tower", "generate-data", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "--stores" in result.stdout
    assert "--seed" in result.stdout


def test_build_exceptions_help():
    result = subprocess.run(
        [sys.executable, "-m", "retail_ops_control_tower", "build-exceptions", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "--input-dir" in result.stdout


def test_report_help():
    result = subprocess.run(
        [sys.executable, "-m", "retail_ops_control_tower", "report", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "--format" in result.stdout
