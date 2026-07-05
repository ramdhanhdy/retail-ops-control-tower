"""Implementation of ``run_all``: run all four insight-engine layers.

Invoke via ``python -m scripts.insight_engine.run_all`` (thin shim module)
or ``from scripts.insight_engine import run_all``. Produces all chart PNGs
in ``images/`` and all structured exports in ``data/insight_exports/``.
"""

from __future__ import annotations


def run_all(export: bool = True) -> dict:
    """Run every analytical layer; returns a dict of per-layer results."""
    # Imported lazily so that running a single layer standalone
    # (`python -m scripts.insight_engine.layer1_concentration`) does not
    # pre-import every layer through the package __init__.
    from scripts.insight_engine import (
        layer1_concentration,
        layer2_segmentation,
        layer3_attribution,
        layer4_opportunity,
    )

    results = {}
    for name, module in (
        ("layer1_concentration", layer1_concentration),
        ("layer2_segmentation", layer2_segmentation),
        ("layer3_attribution", layer3_attribution),
        ("layer4_opportunity", layer4_opportunity),
    ):
        print(f"── Menjalankan {name} ...")
        results[name] = module.run(export=export)
        for chart in results[name]["charts"]:
            print(f"   grafik: {chart}")
    print("Selesai: semua layer berhasil dijalankan.")
    return results


if __name__ == "__main__":
    run_all()
