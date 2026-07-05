"""Insight engine analysis scripts (token-efficient notebook replacement).

Modular analytical layers over the Retail Ops Control Tower data:

- ``layer1_concentration`` — Pareto + Gini (bootstrap CI) over the full fleet
- ``layer2_segmentation``  — format/region ANOVA + Kruskal-Wallis + post-hoc
- ``layer3_attribution``   — regional hotspots, field reps, upstream DC/carrier
- ``layer4_opportunity``   — rebalancing, SLA/aging profile, financial, sensitivity

Charts are written to ``images/`` and structured exports to
``data/insight_exports/``. The Indonesian narrative that embeds the charts
lives at ``docs/insight_engine_story.md``.

Typical notebook usage::

    from scripts.insight_engine import run_all
    results = run_all()
"""

from scripts.insight_engine.runner import run_all

__all__ = ["run_all"]
