"""Shared utilities for the insight engine scripts.

Centralizes data loading, path resolution, and statistical helpers so every
analytical layer works from the same, correctly-prepared frames.

Key data-correctness decisions (fixes for the V2 notebook):

- The store universe is ALL 100 active stores from the store master, not just
  the 84 stores that happen to have exceptions. Stores with zero exceptions
  are part of the fleet and must be included in concentration and
  segmentation statistics.
- ``created_date`` in exceptions.csv is unreliable: 1,423 of 1,603 values are
  dated AFTER the aging snapshot (2026-07-15) and contradict ``age_days``.
  The reliable temporal field is ``age_days``; event dates are reconstructed
  as ``AGING_DATE - age_days`` where needed.
- Exception-type strings are always taken from the structured
  ``exception_type`` column, never parsed from human-readable headlines.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLE_DIR = DATA_DIR / "sample"
IMAGES_DIR = ROOT / "images"
EXPORT_DIR = DATA_DIR / "insight_exports"

# Snapshot date used when the exception table was built (age_days reference).
AGING_DATE = pd.Timestamp("2026-07-15")

RNG_SEED = 42
N_BOOT = 10_000

# Exception types attributable to field-rep compliance work
# (mirrors FIELD_REP_EXCEPTION_TYPES in retail_ops_control_tower.insights).
COMPLIANCE_TYPES = [
    "missing_confirmation",
    "late_confirmation",
    "missing_photo_proof",
    "late_photo_proof",
]


def ensure_dirs() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_tables() -> dict[str, pd.DataFrame]:
    """Load every table the four layers need, with light preparation."""
    tables = {
        "exceptions": pd.read_csv(PROCESSED_DIR / "exceptions.csv"),
        "insights": pd.read_csv(PROCESSED_DIR / "insights.csv"),
        "kpi_summary": pd.read_csv(PROCESSED_DIR / "kpi_summary.csv"),
        "am_scorecard": pd.read_csv(PROCESSED_DIR / "am_scorecard.csv"),
        "stores": pd.read_csv(SAMPLE_DIR / "stores.csv"),
        "dispatch": pd.read_csv(SAMPLE_DIR / "dispatch.csv"),
        "allocation_plan": pd.read_csv(SAMPLE_DIR / "allocation_plan.csv"),
        "sales_daily": pd.read_csv(SAMPLE_DIR / "sales_daily.csv"),
    }
    exc = tables["exceptions"]
    # Reconstruct the reliable event date from age_days (see module docstring).
    exc["event_date"] = AGING_DATE - pd.to_timedelta(exc["age_days"], unit="D")
    return tables


def store_exception_frame(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Per-store exception counts over the FULL 100-store fleet.

    Stores without exceptions get an explicit count of 0 so that fleet-level
    statistics (Gini, Pareto share, ANOVA groups) are not biased.
    """
    stores = tables["stores"]
    counts = (
        tables["exceptions"].groupby("store_id").size().rename("exceptions")
    )
    frame = stores.set_index("store_id")[
        ["region", "store_format", "area_manager", "field_rep"]
    ].copy()
    frame["exceptions"] = counts.reindex(frame.index, fill_value=0).astype(int)
    critical = (
        tables["exceptions"]
        .loc[lambda d: d["severity"] == "critical"]
        .groupby("store_id")
        .size()
    )
    frame["critical"] = critical.reindex(frame.index, fill_value=0).astype(int)
    return frame.reset_index()


def gini_coefficient(values: np.ndarray) -> float:
    """Gini coefficient of a non-negative array (0 = equal, 1 = concentrated)."""
    x = np.sort(np.asarray(values, dtype=float))
    n = len(x)
    total = x.sum()
    if n == 0 or total == 0:
        return 0.0
    ranks = np.arange(1, n + 1)
    return float((2 * np.sum(ranks * x) - (n + 1) * total) / (n * total))


def bootstrap_ci(
    values: np.ndarray,
    statistic,
    n_boot: int = N_BOOT,
    seed: int = RNG_SEED,
    ci: float = 0.95,
) -> tuple[float, float]:
    """Percentile bootstrap CI for a statistic of a 1-D sample."""
    rng = np.random.default_rng(seed)
    values = np.asarray(values)
    boots = np.array(
        [
            statistic(rng.choice(values, size=len(values), replace=True))
            for _ in range(n_boot)
        ]
    )
    lo = (1 - ci) / 2 * 100
    return (
        float(np.percentile(boots, lo)),
        float(np.percentile(boots, 100 - lo)),
    )


def wilson_ci(k: int, n: int, ci: float = 0.95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    from scipy import stats

    if n == 0:
        return (0.0, 0.0)
    z = stats.norm.ppf(1 - (1 - ci) / 2)
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def export_json(name: str, payload: dict) -> Path:
    """Write a JSON export (numpy types coerced) and return its path."""
    ensure_dirs()

    def _default(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        raise TypeError(f"Not JSON serializable: {type(obj)}")

    path = EXPORT_DIR / f"{name}.json"
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=_default),
        encoding="utf-8",
    )
    return path


def export_csv(name: str, frame: pd.DataFrame) -> Path:
    ensure_dirs()
    path = EXPORT_DIR / f"{name}.csv"
    frame.to_csv(path, index=False)
    return path
