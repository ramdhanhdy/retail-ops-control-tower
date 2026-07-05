"""Layer 2 — Segmentation analysis (store format & region).

Which store attributes predict per-store exception volume?

Method (fixes vs the V2 notebook):
- Groups are built over the full 100-store fleet, including zero-exception
  stores. The V2 notebook dropped them, producing group sizes that do not
  exist in the store master (e.g. 22 drive-thru stores when only 16 exist).
- Assumption checks (Shapiro-Wilk per group, Levene) run BEFORE the ANOVA.
  Because normality fails, Kruskal-Wallis is the authoritative omnibus test,
  reported with its own effect size (epsilon-squared) — the V2 notebook
  wrongly attached the ANOVA eta-squared to the Kruskal-Wallis result.
- Post-hoc pairwise comparisons use Mann-Whitney U with Holm correction and
  rank-biserial effect sizes, consistent with the non-parametric route
  (the V2 notebook used pooled-variance t-tests despite a failed Levene).
  Welch t-tests and Cohen's d are reported as a parametric sensitivity check.
- For the non-significant region result, an a-priori power estimate for a
  conventional medium effect (f=0.25) is reported instead of circular
  post-hoc power computed from the observed (near-zero) effect.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

from scripts.insight_engine.common import (
    export_csv,
    export_json,
    load_tables,
    store_exception_frame,
)

ALPHA = 0.05


def _epsilon_squared(h: float, k: int, n: int) -> float:
    """Effect size for Kruskal-Wallis: eps^2 = (H - k + 1) / (n - k)."""
    return float((h - k + 1) / (n - k))


def _rank_biserial(a: np.ndarray, b: np.ndarray) -> float:
    """Rank-biserial correlation from Mann-Whitney U (positive = a > b)."""
    u, _ = stats.mannwhitneyu(a, b, alternative="two-sided")
    return float(2 * u / (len(a) * len(b)) - 1)


def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = len(a), len(b)
    pooled = np.sqrt(
        ((na - 1) * a.std(ddof=1) ** 2 + (nb - 1) * b.std(ddof=1) ** 2)
        / (na + nb - 2)
    )
    return float((a.mean() - b.mean()) / pooled) if pooled > 0 else 0.0


def _effect_label_d(d: float) -> str:
    a = abs(d)
    return "besar" if a >= 0.8 else "sedang" if a >= 0.5 else "kecil" if a >= 0.2 else "dapat diabaikan"


def _holm(pvals: list[float], alpha: float = ALPHA) -> list[bool]:
    """Holm step-down rejection decisions."""
    order = np.argsort(pvals)
    m = len(pvals)
    reject = [False] * m
    for rank, idx in enumerate(order):
        if pvals[idx] <= alpha / (m - rank):
            reject[idx] = True
        else:
            break
    return reject


def _analyze_factor(frame: pd.DataFrame, factor: str) -> dict:
    grouped = {
        name: g["exceptions"].to_numpy(dtype=float)
        for name, g in frame.groupby(factor)
    }
    names = sorted(grouped, key=lambda n: -grouped[n].mean())
    groups = [grouped[n] for n in names]
    n_total = sum(len(g) for g in groups)
    k = len(groups)

    # -- assumption checks ---------------------------------------------------
    shapiro = []
    normality_ok = True
    for name, g in zip(names, groups):
        w, p = stats.shapiro(g)
        ok = p > ALPHA
        normality_ok &= ok
        shapiro.append({"group": name, "n": len(g), "W": float(w), "p": float(p), "pass": ok})
    lev_w, lev_p = stats.levene(*groups)
    variance_ok = lev_p > ALPHA
    assumptions_ok = normality_ok and variance_ok

    # -- omnibus tests --------------------------------------------------------
    f_stat, p_anova = stats.f_oneway(*groups)
    # Unequal-variance omnibus alternative (Alexander-Govern).
    ag = stats.alexandergovern(*groups)
    h_stat, p_kw = stats.kruskal(*groups)

    grand_mean = np.concatenate(groups).mean()
    ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
    ss_total = ((np.concatenate(groups) - grand_mean) ** 2).sum()
    eta_sq = float(ss_between / ss_total)
    eps_sq = _epsilon_squared(h_stat, k, n_total)

    # -- post-hoc pairwise (non-parametric primary) ---------------------------
    rows = []
    for a, b in combinations(names, 2):
        va, vb = grouped[a], grouped[b]
        u, p_mw = stats.mannwhitneyu(va, vb, alternative="two-sided")
        t_w, p_w = stats.ttest_ind(va, vb, equal_var=False)
        d = _cohens_d(va, vb)
        rows.append(
            {
                "pair": f"{a} vs {b}",
                "n_a": len(va),
                "n_b": len(vb),
                "mean_diff": float(va.mean() - vb.mean()),
                "mannwhitney_p_raw": float(p_mw),
                "rank_biserial": _rank_biserial(va, vb),
                "welch_p_raw": float(p_w),
                "cohens_d": d,
                "effect_label": _effect_label_d(d),
            }
        )
    posthoc = pd.DataFrame(rows)
    posthoc["significant_holm"] = _holm(posthoc["mannwhitney_p_raw"].tolist())

    descr = (
        frame.groupby(factor)["exceptions"]
        .agg(["count", "mean", "median", "std"])
        .round(2)
        .reindex(names)
        .reset_index()
    )

    return {
        "factor": factor,
        "groups": names,
        "descriptives": descr,
        "assumptions": {
            "shapiro": shapiro,
            "levene": {"W": float(lev_w), "p": float(lev_p), "pass": variance_ok},
            "anova_assumptions_met": assumptions_ok,
            "authoritative_test": "anova" if assumptions_ok else "kruskal-wallis",
        },
        "anova": {"F": float(f_stat), "p": float(p_anova), "eta_squared": eta_sq},
        "alexander_govern": {"A": float(ag.statistic), "p": float(ag.pvalue)},
        "kruskal_wallis": {"H": float(h_stat), "p": float(p_kw), "epsilon_squared": eps_sq},
        "posthoc": posthoc,
    }


def _power_for_medium_effect(n: int, k: int) -> float:
    """A-priori power of a one-way ANOVA for Cohen's f = 0.25 at this n."""
    from statsmodels.stats.power import FTestAnovaPower

    return float(
        FTestAnovaPower().solve_power(
            effect_size=0.25, nobs=n, alpha=ALPHA, k_groups=k
        )
    )


def analyze(tables: dict[str, pd.DataFrame] | None = None) -> dict:
    tables = tables or load_tables()
    frame = store_exception_frame(tables)
    fmt = _analyze_factor(frame, "store_format")
    reg = _analyze_factor(frame, "region")
    reg["power_medium_effect_f025"] = _power_for_medium_effect(
        len(frame), frame["region"].nunique()
    )
    return {"frame": frame, "format": fmt, "region": reg}


def make_charts(analysis: dict) -> list[str]:
    import matplotlib.pyplot as plt

    from scripts.insight_engine.charts import PALETTE, save_chart

    frame = analysis["frame"]
    paths = []
    for key, factor, xlabel in (
        ("format", "store_format", "Format toko"),
        ("region", "region", "Wilayah"),
    ):
        res = analysis[key]
        names = res["groups"]
        data = [
            frame.loc[frame[factor] == n, "exceptions"].to_numpy() for n in names
        ]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        bp = ax.boxplot(
            data, tick_labels=[f"{n}\n(n={len(d)})" for n, d in zip(names, data)],
            patch_artist=True, showmeans=True,
        )
        for patch in bp["boxes"]:
            patch.set_facecolor(PALETTE["blue"])
            patch.set_alpha(0.5)
        kw = res["kruskal_wallis"]
        ax.set_title(
            f"Sebaran eksepsi per toko menurut {xlabel.lower()} — "
            f"Kruskal-Wallis H={kw['H']:.2f}, p={kw['p']:.2e}, "
            f"\u03b5\u00b2={kw['epsilon_squared']:.3f}"
        )
        ax.set_xlabel(f"{xlabel} (armada penuh 100 toko)")
        ax.set_ylabel("Eksepsi per toko")
        paths.append(str(save_chart(fig, f"layer2_{key}_boxplot")))
    return paths


def run(export: bool = True) -> dict:
    analysis = analyze()
    charts = make_charts(analysis)
    if export:
        for key in ("format", "region"):
            res = analysis[key]
            payload = {
                k: v
                for k, v in res.items()
                if k not in ("posthoc", "descriptives")
            }
            payload["descriptives"] = res["descriptives"].to_dict("records")
            export_json(f"layer2_{key}", payload)
            export_csv(f"layer2_{key}_posthoc", res["posthoc"])
    analysis["charts"] = charts
    return analysis


if __name__ == "__main__":
    result = run()
    for key in ("format", "region"):
        res = result[key]
        kw = res["kruskal_wallis"]
        print(
            f"[{key}] KW H={kw['H']:.2f} p={kw['p']:.2e} "
            f"eps2={kw['epsilon_squared']:.3f} | "
            f"ANOVA F={res['anova']['F']:.2f} p={res['anova']['p']:.2e} "
            f"eta2={res['anova']['eta_squared']:.3f} | "
            f"uji otoritatif: {res['assumptions']['authoritative_test']}"
        )
        print(res["posthoc"].to_string(index=False))
    print(f"Power wilayah (f=0.25): {result['region']['power_medium_effect_f025']:.2f}")
    print(f"Grafik: {result['charts']}")
