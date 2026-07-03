"""Quick script to generate demo dataset.

Usage:
    python scripts/generate_demo_data.py [--seed 42] [--output-dir output]
"""

from __future__ import annotations

import sys
import os

# Allow running from repo root without install
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retail_ops_control_tower.simulation.generator import run_simulation


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate demo dataset")
    parser.add_argument("--stores", type=int, default=40)
    parser.add_argument("--skus", type=int, default=12)
    parser.add_argument("--days", type=int, default=28)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    run_simulation(
        stores=args.stores,
        skus=args.skus,
        days=args.days,
        seed=args.seed,
        output_dir=args.output_dir,
    )
    print(f"Demo data generated in {args.output_dir}/")


if __name__ == "__main__":
    main()
