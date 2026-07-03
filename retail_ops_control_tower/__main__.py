"""Entry point for ``python -m retail_ops_control_tower``.

Dispatches to the three CLI commands: generate-data, build-exceptions, report.
"""

from __future__ import annotations

import sys

from retail_ops_control_tower.cli import build_parser, main

if __name__ == "__main__":
    sys.exit(main())
