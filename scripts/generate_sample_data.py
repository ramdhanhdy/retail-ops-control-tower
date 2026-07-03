"""Generate sample data for the Retail Operations Control Tower.

Writes all 8 CSV tables to the specified output directory. Output is
fully deterministic given the same seed.

Usage:
    python scripts/generate_sample_data.py --output data/sample --seed 42

Parameters can be used to scale the dataset within the supported ranges:
    --stores     80-150  (default 100)
    --regions    3-5     (default 4)
    --managers   8-12    (default 10)
    --campaigns  2-4     (default 3)
"""

from __future__ import annotations

import argparse
import sys
import os

# Allow running from repo root without install
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retail_ops_control_tower.data_generation import (
    TABLE_NAMES,
    generate_sample_data,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate sample data (8 CSV tables) for the Retail Ops Control Tower.",
    )
    parser.add_argument(
        "--output",
        default="data/sample",
        help="Output directory for CSV files (default: %(default)s)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic output (default: %(default)s)",
    )
    parser.add_argument(
        "--stores",
        type=int,
        default=100,
        help="Number of stores, clamped to 80-150 (default: %(default)s)",
    )
    parser.add_argument(
        "--regions",
        type=int,
        default=4,
        help="Number of regions, clamped to 3-5 (default: %(default)s)",
    )
    parser.add_argument(
        "--managers",
        type=int,
        default=10,
        help="Number of area managers, clamped to 8-12 (default: %(default)s)",
    )
    parser.add_argument(
        "--campaigns",
        type=int,
        default=3,
        help="Number of campaigns, clamped to 2-4 (default: %(default)s)",
    )
    args = parser.parse_args()

    tables = generate_sample_data(
        seed=args.seed,
        output_dir=args.output,
        store_count=args.stores,
        region_count=args.regions,
        area_manager_count=args.managers,
        campaign_count=args.campaigns,
    )

    print(f"Sample data generated in {args.output}/")
    print()
    for name in TABLE_NAMES:
        print(f"  {name:<25} {len(tables[name]):>6} rows")
    print()
    print(f"Seed: {args.seed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
