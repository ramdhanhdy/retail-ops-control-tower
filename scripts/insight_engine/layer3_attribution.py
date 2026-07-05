"""Layer 3 — Attribution analysis.

Three questions:
1. Regional hotspots — do specific exception types over-index in specific
   regions relative to the regional store footprint?
2. Field reps — do specific reps over-index on compliance exceptions
   (confirmations & photo proofs) relative to their store coverage?
3. Upstream — do quantity mismatches trace to specific DCs or carriers?

Fixes vs the V2 notebook:
- Hotspots are computed directly from the structured ``exception_type`` and
  ``region`` columns. The V2 notebook parsed the type out of a human-readable
  headline ("low sell through") and matched it against the underscore form
  ("low_sell_through"), so every observed count was ZERO and all chi-square
  p-values were NaN. Here every region x type cell with an adequate expected
  count is tested with an exact binomial test and BH-FDR corrected across the
  full screened family (not just the 6 cells the heuristic engine flagged).
- Field-rep counts are overdispersed relative to Poisson (variance/mean ~ 7
  at store level), so instead of a Poisson exact test we use a store-level
  permutation test (label exchange over stores), which respects store-level
  clustering. Lift CIs come from a store-level bootstrap. Exceptions at the
  13 stores without an assigned rep are excluded and disclosed.
- Upstream chi-square tests keep the V2 approach (it was sound) but report
  the correct df (3 DCs / 3 carriers -> df=2) and Cramer's V with the
  expected-count assumption check.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from scripts.insight_engine.common import (
    COMPLIANCE_TYPES,
    RNG_SEED,
    export_csv,
    export_json,
    load_tables,
    wilson_ci,
)

ALPHA = 0.05
MIN_EXPECTED = 5.0
N_PERMUTATIONS = 20_000
N_BOOT = 5_000


# ---------------------------------------------------------------------------
# 3.1 Regional hotspots
# ---------------------------------------------------------------------------

def analyze_hotspots(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    exc, stores = tables["exceptions"], tables["stores"]
    store_share = stores["region"].value_counts(normalize=True)

    rows = []
    for exc_type, type_df in exc.groupby("exception_type"):
        n_type = len(type_df)
        counts = type_df["region"].value_counts()
        for region, share in store_share.items():
            expected = n_type * share
            if expected < MIN_EXPECTED:
                continue  # screened out: binomial approximation unreliable
            observed = int(counts.get(region, 0))
            p_binom = stats.binomtest(observed, n_type, share).pvalue
            prop_lo, prop_hi = wilson_ci(observed, n_type)
            rows.append(
                {
                    "region": region,
                    "exception_type": exc_type,
                    "observed": observed,
                    "expected": expected,
                    "n_type_total": n_type,
                    "store_share": float(share),
                    "lift": observed / expected if expected else 0.0,
                    "lift_ci_lo": prop_lo / share,
                    "lift_ci_hi": prop_hi / share,
                    "p_raw": float(p_binom),
                }
            )
    df = pd.DataFrame(rows)
    reject, p_fdr, _, _ = multipletests(df["p_raw"], alpha=ALPHA, method="fdr_bh")
    df["p_fdr"] = p_fdr
    df["significant_fdr"] = reject

    flagged = tables["insights"].query("category == 'regional_hotspot'")
    engine_cells = set()
    for _, r in flagged.iterrows():
        # metric_name is structured: '<exception_type>_share_in_region'
        exc_type = r["metric_name"].removesuffix("_share_in_region")
        region = r["headline"].split(" region")[0]
        engine_cells.add((region, exc_type))
    df["engine_flagged"] = [
        (r, t) in engine_cells
        for r, t in zip(df["region"], df["exception_type"])
    ]
    return df.sort_values("p_fdr").reset_index(drop=True)


# ---------------------------------------------------------------------------
# 3.2 Field-rep compliance over-indexing
# ---------------------------------------------------------------------------

def analyze_field_reps(tables: dict[str, pd.DataFrame]) -> dict:
    exc, stores = tables["exceptions"], tables["stores"]
    covered = stores.dropna(subset=["field_rep"]).copy()
    cp = exc[exc["exception_type"].isin(COMPLIANCE_TYPES)]
    n_uncovered = int((~cp["store_id"].isin(covered["store_id"])).sum())

    per_store = (
        cp.groupby("store_id").size().reindex(covered["store_id"], fill_value=0)
    ).to_numpy(dtype=float)
    reps = covered["field_rep"].to_numpy()
    fleet_rate = per_store.sum() / len(per_store)
    overdispersion = float(per_store.var(ddof=1) / per_store.mean())

    rng = np.random.default_rng(RNG_SEED)
    rows = []
    for rep in sorted(covered["field_rep"].unique()):
        mask = reps == rep
        n_rep_stores = int(mask.sum())
        observed_total = float(per_store[mask].sum())
        rep_rate = observed_total / n_rep_stores
        lift = rep_rate / fleet_rate

        # Store-level permutation test (one-sided: over-indexing).
        perm_totals = np.array(
            [
                rng.choice(per_store, size=n_rep_stores, replace=False).sum()
                for _ in range(N_PERMUTATIONS)
            ]
        )
        p_perm = float((np.sum(perm_totals >= observed_total) + 1) / (N_PERMUTATIONS + 1))

        # Store-level bootstrap CI on the lift.
        rep_counts = per_store[mask]
        boots = np.empty(N_BOOT)
        for i in range(N_BOOT):
            rep_bs = rng.choice(rep_counts, size=n_rep_stores, replace=True).mean()
            fleet_bs = rng.choice(per_store, size=len(per_store), replace=True).mean()
            boots[i] = rep_bs / fleet_bs if fleet_bs > 0 else np.nan
        lift_lo, lift_hi = np.nanpercentile(boots, [2.5, 97.5])

        rows.append(
            {
                "field_rep": rep,
                "stores": n_rep_stores,
                "compliance_exceptions": int(observed_total),
                "rate_per_store": rep_rate,
                "lift": lift,
                "lift_ci_lo": float(lift_lo),
                "lift_ci_hi": float(lift_hi),
                "p_raw": p_perm,
            }
        )

    df = pd.DataFrame(rows)
    reject, p_fdr, _, _ = multipletests(df["p_raw"], alpha=ALPHA, method="fdr_bh")
    df["p_fdr"] = p_fdr
    df["significant_fdr"] = reject
    df = df.sort_values("lift", ascending=False).reset_index(drop=True)
    return {
        "table": df,
        "fleet_rate_per_store": float(fleet_rate),
        "overdispersion_var_over_mean": overdispersion,
        "stores_without_rep": int(stores["field_rep"].isna().sum()),
        "compliance_exceptions_excluded_no_rep": n_uncovered,
        "compliance_exceptions_total": int(len(cp)),
        "n_permutations": N_PERMUTATIONS,
    }


# ---------------------------------------------------------------------------
# 3.3 Upstream attribution (DC / carrier)
# ---------------------------------------------------------------------------

def analyze_upstream(tables: dict[str, pd.DataFrame]) -> dict:
    exc, disp = tables["exceptions"], tables["dispatch"]
    qm = exc[exc["exception_type"] == "quantity_mismatch"].merge(
        disp[["allocation_id", "dc_id", "carrier"]], on="allocation_id", how="left"
    )
    out = {"n_mismatches": int(len(qm))}
    for dim in ("dc_id", "carrier"):
        observed = qm[dim].value_counts().sort_index()
        shipments = disp.groupby(dim)["allocation_id"].nunique().reindex(observed.index)
        expected = observed.sum() * shipments / shipments.sum()
        chi2, p = stats.chisquare(observed, f_exp=expected)
        k = len(observed)
        n = observed.sum()
        cramers_v = float(np.sqrt(chi2 / (n * (k - 1)))) if k > 1 else 0.0
        out[dim] = {
            "observed": observed.to_dict(),
            "expected": {k_: float(v) for k_, v in expected.items()},
            "chi2": float(chi2),
            "df": k - 1,
            "p": float(p),
            "cramers_v": cramers_v,
            "min_expected": float(expected.min()),
            "expected_ge_5": bool(expected.min() >= MIN_EXPECTED),
        }
    return out


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def make_charts(analysis: dict) -> list[str]:
    import matplotlib.pyplot as plt

    from scripts.insight_engine.charts import PALETTE, save_chart

    paths = []

    # Hotspot lift chart (engine-flagged cells + any FDR-significant cell)
    hs = analysis["hotspots"]
    show = hs[hs["engine_flagged"] | hs["significant_fdr"]].copy()
    show = show.sort_values("lift", ascending=True)
    labels = [
        f"{r} — {t.replace('_', ' ')}"
        for r, t in zip(show["region"], show["exception_type"])
    ]
    fig, ax = plt.subplots(figsize=(9, 0.5 * len(show) + 2.2))
    colors = [
        PALETTE["red"] if sig else PALETTE["gray"]
        for sig in show["significant_fdr"]
    ]
    err_lo = (show["lift"] - show["lift_ci_lo"]).clip(lower=0)
    err_hi = (show["lift_ci_hi"] - show["lift"]).clip(lower=0)
    ax.barh(labels, show["lift"], color=colors, alpha=0.85)
    ax.errorbar(
        show["lift"], labels, xerr=[err_lo, err_hi],
        fmt="none", ecolor=PALETTE["dark"], capsize=3, lw=1,
    )
    ax.axvline(1.0, ls="--", color="gray", lw=1)
    ax.set_title(
        "Lift hotspot regional — merah = signifikan setelah koreksi BH-FDR "
        f"(keluarga uji: {len(hs)} sel wilayah×tipe)"
    )
    ax.set_xlabel("Lift (× pangsa toko wilayah); galat = CI 95% Wilson")
    paths.append(str(save_chart(fig, "layer3_hotspot_lift")))

    # Field-rep lift chart
    fr = analysis["field_reps"]["table"]
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = [
        PALETTE["red"] if sig and lift > 1 else PALETTE["blue"] if lift > 1 else PALETTE["gray"]
        for sig, lift in zip(fr["significant_fdr"], fr["lift"])
    ]
    x = np.arange(len(fr))
    ax.bar(x, fr["lift"], color=colors, alpha=0.85)
    ax.errorbar(
        x, fr["lift"],
        yerr=[
            (fr["lift"] - fr["lift_ci_lo"]).clip(lower=0),
            (fr["lift_ci_hi"] - fr["lift"]).clip(lower=0),
        ],
        fmt="none", ecolor=PALETTE["dark"], capsize=3, lw=1,
    )
    ax.axhline(1.0, ls="--", color="gray", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(fr["field_rep"], rotation=45, ha="right")
    ax.set_title(
        "Lift eksepsi kepatuhan per field rep — uji permutasi tingkat toko, "
        "merah = signifikan setelah BH-FDR"
    )
    ax.set_ylabel("Lift (× laju armada per toko); galat = CI 95% bootstrap")
    paths.append(str(save_chart(fig, "layer3_fieldrep_lift")))

    # Upstream observed vs expected
    up = analysis["upstream"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, dim, judul in zip(axes, ("dc_id", "carrier"), ("Gudang (DC)", "Kurir")):
        d = up[dim]
        cats = list(d["observed"].keys())
        xs = np.arange(len(cats))
        ax.bar(xs - 0.2, list(d["observed"].values()), width=0.4,
               color=PALETTE["red"], alpha=0.8, label="Observasi")
        ax.bar(xs + 0.2, list(d["expected"].values()), width=0.4,
               color=PALETTE["gray"], alpha=0.8, label="Ekspektasi")
        ax.set_xticks(xs)
        ax.set_xticklabels(cats, rotation=20, ha="right")
        ax.set_title(
            f"{judul} — \u03c7\u00b2={d['chi2']:.2f} (df={d['df']}), "
            f"p={d['p']:.3f}, V={d['cramers_v']:.3f}"
        )
        ax.set_ylabel("Jumlah quantity mismatch")
        ax.legend(fontsize=9)
    fig.suptitle(
        "Atribusi quantity mismatch — observasi vs ekspektasi (berdasarkan volume kiriman)",
        fontweight="bold",
    )
    paths.append(str(save_chart(fig, "layer3_upstream_mismatch")))
    return paths


def analyze(tables: dict[str, pd.DataFrame] | None = None) -> dict:
    tables = tables or load_tables()
    return {
        "hotspots": analyze_hotspots(tables),
        "field_reps": analyze_field_reps(tables),
        "upstream": analyze_upstream(tables),
    }


def run(export: bool = True) -> dict:
    analysis = analyze()
    charts = make_charts(analysis)
    if export:
        export_csv("layer3_hotspots", analysis["hotspots"])
        export_csv("layer3_field_reps", analysis["field_reps"]["table"])
        export_json(
            "layer3_attribution",
            {
                "field_reps_meta": {
                    k: v
                    for k, v in analysis["field_reps"].items()
                    if k != "table"
                },
                "upstream": analysis["upstream"],
                "hotspot_family_size": int(len(analysis["hotspots"])),
                "hotspots_significant_fdr": int(
                    analysis["hotspots"]["significant_fdr"].sum()
                ),
            },
        )
    analysis["charts"] = charts
    return analysis


if __name__ == "__main__":
    result = run()
    hs = result["hotspots"]
    print(f"Hotspot: {len(hs)} sel diuji, {hs['significant_fdr'].sum()} signifikan FDR")
    print(hs[hs["engine_flagged"] | hs["significant_fdr"]].to_string(index=False))
    fr = result["field_reps"]
    print(f"\nOverdispersi per toko (var/mean): {fr['overdispersion_var_over_mean']:.2f}")
    print(fr["table"].to_string(index=False))
    up = result["upstream"]
    for dim in ("dc_id", "carrier"):
        d = up[dim]
        print(f"\n{dim}: chi2={d['chi2']:.2f} df={d['df']} p={d['p']:.3f} V={d['cramers_v']:.3f}")
    print(f"Grafik: {result['charts']}")
