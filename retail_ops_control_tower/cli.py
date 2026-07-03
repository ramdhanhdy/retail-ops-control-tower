"""CLI argument parsing and command dispatch.

Three commands are exposed as console scripts (defined in pyproject.toml) and
also accessible via ``python -m retail_ops_control_tower``:

    - generate-data:   Run the data simulation layer.
    - build-exceptions: Run the reconciliation engine and exception management.
    - report:           Generate dashboard sections and reports.

Each command function is a thin wrapper that imports lazily so the package
imports cleanly even before downstream modules (simulation, reconciliation,
dashboard) are implemented.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from typing import Sequence

DEFAULT_STORES = 40
DEFAULT_SKUS = 12
DEFAULT_DAYS = 28
DEFAULT_SEED = 42
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_INPUT_DIR = "output"


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add arguments common to all commands (input/output dirs)."""
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for output files (default: %(default)s)",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="retail-ops-control-tower",
        description="Retail Operations Control Tower - "
        "simulated multi-store campaign execution monitoring.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate-data
    gen = subparsers.add_parser(
        "generate-data",
        help="Generate simulated campaign data (8 JSON tables).",
    )
    gen.add_argument("--stores", type=int, default=DEFAULT_STORES,
                     help="Number of stores (default: %(default)s)")
    gen.add_argument("--campaign", default=None,
                     help="Campaign ID (default: auto-generated)")
    gen.add_argument("--skus", type=int, default=DEFAULT_SKUS,
                     help="Number of SKUs (default: %(default)s)")
    gen.add_argument("--days", type=int, default=DEFAULT_DAYS,
                     help="Number of days in the campaign window (default: %(default)s)")
    gen.add_argument("--seed", type=int, default=DEFAULT_SEED,
                     help="Random seed for deterministic output (default: %(default)s)")
    gen.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                     help="Output directory (default: %(default)s)")
    gen.set_defaults(func=generate_data)

    # build-exceptions
    exc = subparsers.add_parser(
        "build-exceptions",
        help="Run reconciliation engine and exception management.",
    )
    exc.add_argument("--input-dir", default=DEFAULT_INPUT_DIR,
                     help="Input directory with JSON data (default: %(default)s)")
    exc.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                     help="Output directory (default: %(default)s)")
    exc.add_argument("--aging-date", default=None,
                     help="Aging date as YYYY-MM-DD (default: today)")
    exc.set_defaults(func=build_exceptions)

    # report
    rep = subparsers.add_parser(
        "report",
        help="Generate dashboard sections and reports.",
    )
    rep.add_argument("--input-dir", default=DEFAULT_INPUT_DIR,
                     help="Input directory with enriched data (default: %(default)s)")
    rep.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR + "/reports",
                     help="Output directory for reports (default: %(default)s)")
    rep.add_argument("--section", default="all",
                     help="Dashboard section to render (default: all)")
    rep.add_argument("--format", choices=["text", "html"], default="text",
                     help="Output format (default: %(default)s)")
    rep.add_argument("--aging-date", default=None,
                     help="Aging date as YYYY-MM-DD (default: today)")
    rep.set_defaults(func=report)

    return parser


def generate_data(args: argparse.Namespace | None = None) -> int:
    """Run the data simulation layer to generate all 8 tables."""
    if args is None:
        parser = build_parser()
        args = parser.parse_args(["generate-data"] + sys.argv[1:])

    from retail_ops_control_tower.simulation.generator import run_simulation

    run_simulation(
        stores=args.stores,
        campaign_id=args.campaign,
        skus=args.skus,
        days=args.days,
        seed=args.seed,
        output_dir=args.output_dir,
    )
    print(f"Data generated in {args.output_dir}/")
    return 0


def build_exceptions(args: argparse.Namespace | None = None) -> int:
    """Run the reconciliation engine and exception management system."""
    if args is None:
        parser = build_parser()
        args = parser.parse_args(["build-exceptions"] + sys.argv[1:])

    from retail_ops_control_tower.reconciliation.engine import run_reconciliation

    aging_date = _parse_date(args.aging_date)

    run_reconciliation(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        aging_date=aging_date,
    )
    print(f"Exceptions built in {args.output_dir}/")
    return 0


def report(args: argparse.Namespace | None = None) -> int:
    """Generate dashboard sections and reports."""
    if args is None:
        parser = build_parser()
        args = parser.parse_args(["report"] + sys.argv[1:])

    from retail_ops_control_tower.reports.generator import generate_reports

    aging_date = _parse_date(args.aging_date)

    generate_reports(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        section=args.section,
        fmt=args.format,
        aging_date=aging_date,
    )
    print(f"Reports generated in {args.output_dir}/")
    return 0


def _parse_date(value: str | None) -> date:
    """Parse a YYYY-MM-DD string, returning today if None."""
    if value is None:
        return date.today()
    return date.fromisoformat(value)


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
