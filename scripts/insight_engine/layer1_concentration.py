"""Layer 1 — Concentration analysis (Pareto + Gini).

Fixes vs the V2 notebook: the concentration statistics are computed over the
full 100-store fleet (including 16 stores with zero exceptions), not just the
84 stores that happen to appear in the exception table. Excluding
zero-exception stores understates inequality (Gini 0.356 vs the correct
0.459) and overstates the Pareto store share (56% vs the correct 47%).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.insight_engine.common import (
    N_BOOT,
    bootstrap_ci,
    export_csv,
    export_json,
    gini_coefficient,
    load_tables,
    store_exception_frame,
)


def analyze(tables: dict[str, pd.DataFrame] | None = None) -> dict:
    tables = tables or load_tables()
    frame = store_exception_frame(tables)
    values = frame["exceptions"].to_numpy()
    n_stores = len(frame)
    total_exc = int(values.sum())

    ranked = frame.sort_values(
        ["exceptions", "store_id"], ascending=[False, True]
    ).reset_index(drop=True)
    ranked["cum_share"] = ranked["exceptions"].cumsum() / total_exc
    pareto_n = int((ranked["cum_share"] < 0.80).sum()) + 1
    pareto_cum_share = float(ranked.loc[pareto_n - 1, "cum_share"])

    gini = gini_coefficient(values)
    gini_lo, gini_hi = bootstrap_ci(values, gini_coefficient)
    # Secondary view: inequality among affected stores only (V2's number).
    gini_affected = gini_coefficient(values[values > 0])

    zero_stores = int((values == 0).sum())
    result = {
        "n_stores": n_stores,
        "n_exceptions": total_exc,
        "stores_with_zero_exceptions": zero_stores,
        "mean_per_store": float(values.mean()),
        "median_per_store": float(np.median(values)),
        "max_per_store": int(values.max()),
        "pareto_n_stores": pareto_n,
        "pareto_store_share": pareto_n / n_stores,
        "pareto_exception_share": pareto_cum_share,
        "gini_full_fleet": gini,
        "gini_ci_95": [gini_lo, gini_hi],
        "gini_bootstrap_iterations": N_BOOT,
        "gini_affected_stores_only": gini_affected,
        "top5_stores": ranked.head(5)[["store_id", "exceptions"]].to_dict(
            "records"
        ),
    }
    return {"summary": result, "ranked": ranked}


def make_charts(analysis: dict) -> list[str]:
    import matplotlib.pyplot as plt

    from scripts.insight_engine.charts import PALETTE, save_chart

    ranked = analysis["ranked"]
    s = analysis["summary"]
    values = ranked["exceptions"].to_numpy()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    # Pareto curve
    rank = np.arange(1, len(ranked) + 1)
    ax1.bar(rank, values, color=PALETTE["red"], alpha=0.65, width=1.0)
    ax1b = ax1.twinx()
    ax1b.plot(rank, ranked["cum_share"] * 100, color=PALETTE["dark"], lw=2)
    ax1b.axhline(80, ls="--", color="gray", lw=1)
    ax1b.grid(False)
    ax1.axvline(s["pareto_n_stores"], ls=":", color=PALETTE["blue"], lw=1.5)
    ax1.set_title(
        f"Kurva Pareto — {s['pareto_n_stores']} dari {s['n_stores']} toko "
        f"({s['pareto_store_share']:.0%}) menyumbang 80% eksepsi"
    )
    ax1.set_xlabel("Peringkat toko (semua 100 toko, termasuk 0 eksepsi)")
    ax1.set_ylabel("Jumlah eksepsi")
    ax1b.set_ylabel("Kumulatif eksepsi (%)")
    ax1b.set_ylim(0, 105)

    # Lorenz curve
    sorted_vals = np.sort(values)
    lorenz_x = np.arange(0, len(sorted_vals) + 1) / len(sorted_vals) * 100
    lorenz_y = np.concatenate(
        [[0], np.cumsum(sorted_vals) / sorted_vals.sum() * 100]
    )
    ax2.plot(lorenz_x, lorenz_y, color=PALETTE["red"], lw=2, label="Kurva Lorenz")
    ax2.plot(
        [0, 100], [0, 100], ls="--", color="gray", lw=1,
        label="Pemerataan sempurna",
    )
    ax2.fill_between(lorenz_x, lorenz_y, lorenz_x, color=PALETTE["red"], alpha=0.12)
    ax2.set_title(
        f"Kurva Lorenz — Gini = {s['gini_full_fleet']:.3f} "
        f"(CI 95% bootstrap: [{s['gini_ci_95'][0]:.3f}, {s['gini_ci_95'][1]:.3f}])"
    )
    ax2.set_xlabel("Kumulatif toko (%)")
    ax2.set_ylabel("Kumulatif eksepsi (%)")
    ax2.legend(loc="upper left", fontsize=9)

    path = save_chart(fig, "layer1_pareto_lorenz")
    return [str(path)]


def run(export: bool = True) -> dict:
    analysis = analyze()
    charts = make_charts(analysis)
    if export:
        export_json("layer1_concentration", analysis["summary"])
        export_csv(
            "layer1_store_ranking",
            analysis["ranked"][
                ["store_id", "region", "store_format", "exceptions", "critical", "cum_share"]
            ],
        )
    analysis["charts"] = charts
    return analysis


if __name__ == "__main__":
    result = run()
    s = result["summary"]
    print(
        f"Pareto: {s['pareto_n_stores']}/{s['n_stores']} toko "
        f"({s['pareto_store_share']:.0%}) = {s['pareto_exception_share']:.1%} eksepsi"
    )
    print(
        f"Gini (armada penuh): {s['gini_full_fleet']:.3f} "
        f"CI95 [{s['gini_ci_95'][0]:.3f}, {s['gini_ci_95'][1]:.3f}] "
        f"(hanya toko terdampak: {s['gini_affected_stores_only']:.3f})"
    )
    print(f"Grafik: {result['charts']}")
