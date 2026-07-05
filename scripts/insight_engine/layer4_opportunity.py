"""Layer 4 — Opportunity analysis.

Four blocks:
1. Inventory rebalancing — SKUs simultaneously at stockout and overstock risk
   within the same campaign (zero-procurement transfer candidates).
2. SLA risk profile — breach rates with Wilson CIs, plus the exception AGING
   profile. The V2 notebook fitted a daily-trend regression on
   ``created_date``, but 1,423 of 1,603 values in that column are dated AFTER
   the aging snapshot and contradict ``age_days`` — there is no valid daily
   time series in this data. The honest replacement is an aging profile
   built from ``age_days`` (the reliable field).
3. Financial impact (illustrative) — corrected drivers: the V2 notebook
   counted "stockout-class" exceptions with types that do not exist in the
   taxonomy (``out_of_stock``, ``damaged_shipment``); the actual type is
   ``stockout_risk``. Rebalancing ROI is based on the 15 SKU-campaign
   transfer actions actually recommended, not the 3 insight rows.
4. Sensitivity of the impact-score ranking — critical counts are recomputed
   directly from the exception table per insight (the V2 notebook
   reverse-engineered them from the score formula, which loses information
   to integer truncation).
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from scripts.insight_engine.common import (
    COMPLIANCE_TYPES,
    export_csv,
    export_json,
    load_tables,
    wilson_ci,
)

# Aging buckets per retail_ops_control_tower.constants.AgingBucket
AGING_BUCKETS = [
    ("0-5 hari (fresh)", 0, 5),
    ("6-15 hari (aging)", 6, 15),
    ("16-30 hari (overdue)", 16, 30),
    ("30+ hari (chronic)", 31, 10_000),
]

# ── Illustrative financial parameters (placeholders for finance-supplied
#    figures; the structure of the calculation is the deliverable). ──
STOCKOUT_REVENUE_PER_STORE_DAY = 4_200
SLA_PENALTY_PER_BREACH = 1_500
CRITICAL_EXPEDITING_COST = 800
TRANSFER_COST_PER_ACTION = 250
REBALANCING_SAVINGS_PER_ACTION = 3_100


# ---------------------------------------------------------------------------
# 4.1 Rebalancing
# ---------------------------------------------------------------------------

def analyze_rebalancing(tables: dict[str, pd.DataFrame]) -> dict:
    exc = tables["exceptions"]
    stockout = exc.loc[
        exc["exception_type"] == "stockout_risk",
        ["campaign_id", "store_id", "sku"],
    ].drop_duplicates()
    overstock = exc.loc[
        exc["exception_type"] == "overstock_risk",
        ["campaign_id", "store_id", "sku"],
    ].drop_duplicates()
    matched = stockout.merge(
        overstock, on=["campaign_id", "sku"], suffixes=("_stockout", "_overstock")
    )
    summary = (
        matched.groupby("campaign_id")
        .agg(
            transferable_skus=("sku", "nunique"),
            stockout_stores=("store_id_stockout", "nunique"),
            overstock_stores=("store_id_overstock", "nunique"),
        )
        .reset_index()
    )
    # store-campaign touchpoints, consistent with the insight engine
    touchpoints = int(
        summary["stockout_stores"].sum() + summary["overstock_stores"].sum()
    )
    return {
        "summary": summary,
        "total_transferable_skus": int(summary["transferable_skus"].sum()),
        "total_touchpoints": touchpoints,
    }


# ---------------------------------------------------------------------------
# 4.2 SLA & aging profile
# ---------------------------------------------------------------------------

def analyze_sla(tables: dict[str, pd.DataFrame]) -> dict:
    exc = tables["exceptions"]
    n = len(exc)
    n_breach = int((exc["sla_status"] == "breached").sum())
    n_approaching = int((exc["sla_status"] == "approaching").sum())
    n_critical = int((exc["severity"] == "critical").sum())

    by_type = (
        exc.groupby("exception_type")
        .agg(
            total=("exception_id", "count"),
            breached=("sla_status", lambda x: int((x == "breached").sum())),
        )
        .reset_index()
    )
    by_type["breach_rate"] = by_type["breached"] / by_type["total"]
    ci = by_type.apply(
        lambda r: wilson_ci(int(r["breached"]), int(r["total"])), axis=1
    )
    by_type["breach_ci_lo"] = [c[0] for c in ci]
    by_type["breach_ci_hi"] = [c[1] for c in ci]
    by_type = by_type.sort_values("breach_rate", ascending=False)

    buckets = []
    for label, lo, hi in AGING_BUCKETS:
        mask = exc["age_days"].between(lo, hi)
        buckets.append(
            {
                "bucket": label,
                "count": int(mask.sum()),
                "breached": int((exc.loc[mask, "sla_status"] == "breached").sum()),
            }
        )

    breach_ci = wilson_ci(n_breach, n)
    crit_ci = wilson_ci(n_critical, n)
    return {
        "n_exceptions": n,
        "breached": n_breach,
        "breach_rate": n_breach / n,
        "breach_rate_wilson_ci": list(breach_ci),
        "approaching": n_approaching,
        "critical": n_critical,
        "critical_share": n_critical / n,
        "critical_share_wilson_ci": list(crit_ci),
        "by_type": by_type,
        "aging_buckets": pd.DataFrame(buckets),
        "detected_at_snapshot": int((exc["age_days"] == 0).sum()),
        "created_date_inconsistent_rows": _count_bad_created_dates(exc),
    }


def _count_bad_created_dates(exc: pd.DataFrame) -> int:
    """Rows whose created_date contradicts age_days (documented data flaw)."""
    from scripts.insight_engine.common import AGING_DATE

    cd = pd.to_datetime(exc["created_date"].astype(str).str[:10])
    implied = (AGING_DATE - cd).dt.days
    return int((exc["age_days"] != implied).sum())


# ---------------------------------------------------------------------------
# 4.3 Financial impact (illustrative)
# ---------------------------------------------------------------------------

def analyze_financial(tables: dict[str, pd.DataFrame], rebal: dict) -> dict:
    exc = tables["exceptions"]
    stockout_mask = exc["exception_type"] == "stockout_risk"
    n_stockout_exc = int(stockout_mask.sum())
    n_stockout_stores = int(exc.loc[stockout_mask, "store_id"].nunique())
    n_breach = int((exc["sla_status"] == "breached").sum())
    n_critical = int((exc["severity"] == "critical").sum())

    stockout_revenue = n_stockout_stores * STOCKOUT_REVENUE_PER_STORE_DAY
    sla_penalty = n_breach * SLA_PENALTY_PER_BREACH
    expediting = n_critical * CRITICAL_EXPEDITING_COST

    n_actions = rebal["total_transferable_skus"]  # 1 transfer action per SKU-campaign
    transfer_cost = n_actions * TRANSFER_COST_PER_ACTION
    savings = n_actions * REBALANCING_SAVINGS_PER_ACTION

    return {
        "illustrative": True,
        "parameters": {
            "stockout_revenue_per_store_day": STOCKOUT_REVENUE_PER_STORE_DAY,
            "sla_penalty_per_breach": SLA_PENALTY_PER_BREACH,
            "critical_expediting_cost": CRITICAL_EXPEDITING_COST,
            "transfer_cost_per_action": TRANSFER_COST_PER_ACTION,
            "rebalancing_savings_per_action": REBALANCING_SAVINGS_PER_ACTION,
        },
        "drivers": {
            "stockout_risk_exceptions": n_stockout_exc,
            "stockout_risk_stores": n_stockout_stores,
            "sla_breaches": n_breach,
            "critical_exceptions": n_critical,
            "rebalancing_actions": n_actions,
        },
        "stockout_revenue_at_risk": stockout_revenue,
        "sla_breach_penalties": sla_penalty,
        "critical_expediting": expediting,
        "total_exposure": stockout_revenue + sla_penalty + expediting,
        "transfer_cost": transfer_cost,
        "rebalancing_savings": savings,
        "net_rebalancing_value": savings - transfer_cost,
        "roi_ratio": savings / transfer_cost if transfer_cost else float("nan"),
    }


# ---------------------------------------------------------------------------
# 4.4 Impact-score ranking sensitivity
# ---------------------------------------------------------------------------

def _critical_counts_per_insight(tables: dict[str, pd.DataFrame]) -> pd.Series:
    """Recompute each insight's critical-exception count from raw data."""
    exc, stores, ins = tables["exceptions"], tables["stores"], tables["insights"]
    crit = exc[exc["severity"] == "critical"]
    counts = {}
    for _, row in ins.iterrows():
        cat, iid = row["category"], row["insight_id"]
        if cat == "pareto_concentration":
            per_store = exc.groupby("store_id").size()
            ranked = per_store.sort_index().sort_values(ascending=False, kind="stable")
            cum, vital = 0, []
            for sid, c in ranked.items():
                cum += c
                vital.append(sid)
                if cum / len(exc) >= 0.80:
                    break
            counts[iid] = int(crit["store_id"].isin(vital).sum())
        elif cat == "regional_hotspot":
            exc_type = row["metric_name"].removesuffix("_share_in_region")
            region = row["headline"].split(" region")[0]
            counts[iid] = int(
                ((crit["region"] == region) & (crit["exception_type"] == exc_type)).sum()
            )
        elif cat == "field_rep_workload":
            m = re.match(r"Field rep (.+) over-indexes", row["headline"])
            rep_stores = stores.loc[stores["field_rep"] == m.group(1), "store_id"]
            counts[iid] = int(
                (
                    crit["store_id"].isin(rep_stores)
                    & crit["exception_type"].isin(COMPLIANCE_TYPES)
                ).sum()
            )
        elif cat == "rebalancing_opportunity":
            campaign = re.search(r"in (C-[\w-]+) have", row["headline"]).group(1)
            sub = exc[
                (exc["campaign_id"] == campaign)
                & exc["exception_type"].isin(["stockout_risk", "overstock_risk"])
            ]
            st = sub[sub["exception_type"] == "stockout_risk"]["sku"].unique()
            ov = sub[sub["exception_type"] == "overstock_risk"]["sku"].unique()
            matched_skus = set(st) & set(ov)
            counts[iid] = int(
                (
                    (sub["sku"].isin(matched_skus))
                    & (sub["severity"] == "critical")
                ).sum()
            )
        else:
            counts[iid] = 0
    return pd.Series(counts)


def analyze_sensitivity(tables: dict[str, pd.DataFrame]) -> dict:
    ins = tables["insights"].copy()
    ins["critical_count"] = ins["insight_id"].map(
        _critical_counts_per_insight(tables)
    )
    # The published `lift` column is rounded to 2 decimals; the engine scores
    # with the unrounded ratio, which metric_value/baseline_value preserves.
    ins["lift_exact"] = np.where(
        ins["baseline_value"] > 0,
        ins["metric_value"] / ins["baseline_value"],
        ins["lift"],
    )

    # Verify the reconstruction reproduces the engine's published scores.
    capped = ins["lift_exact"].clip(lower=1.0, upper=3.0)
    recomputed = (
        (ins["affected_count"] * capped + ins["critical_count"] * 2)
        .astype(int)
        .clip(lower=1)
    )
    verified = bool((recomputed == ins["impact_score"]).all())

    scenarios = {
        "original": {"lift_cap": 3.0, "crit_w": 2},
        "conservative": {"lift_cap": 2.0, "crit_w": 3},
        "aggressive": {"lift_cap": 4.0, "crit_w": 1},
    }
    for name, p in scenarios.items():
        c = ins["lift_exact"].clip(lower=1.0, upper=p["lift_cap"])
        ins[f"score_{name}"] = (
            ins["affected_count"] * c + ins["critical_count"] * p["crit_w"]
        )
        ins[f"rank_{name}"] = ins[f"score_{name}"].rank(ascending=False).astype(int)

    rho_cons, p_cons = spearmanr(ins["score_original"], ins["score_conservative"])
    rho_aggr, p_aggr = spearmanr(ins["score_original"], ins["score_aggressive"])
    min_rho = min(rho_cons, rho_aggr)
    top5 = {
        name: ins.nlargest(5, f"score_{name}")["insight_id"].tolist()
        for name in scenarios
    }
    common_top5 = sorted(set.intersection(*(set(v) for v in top5.values())))
    return {
        "table": ins,
        "score_reconstruction_verified": verified,
        "spearman": {
            "original_vs_conservative": {"rho": float(rho_cons), "p": float(p_cons)},
            "original_vs_aggressive": {"rho": float(rho_aggr), "p": float(p_aggr)},
        },
        "min_rho": float(min_rho),
        "verdict": "ROBUST" if min_rho >= 0.8 else "SENSITIVE" if min_rho < 0.6 else "MIXED",
        "top5_by_scenario": top5,
        "common_top5": common_top5,
    }


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def make_charts(analysis: dict) -> list[str]:
    import matplotlib.pyplot as plt

    from scripts.insight_engine.charts import PALETTE, save_chart

    paths = []

    # Rebalancing
    reb = analysis["rebalancing"]["summary"]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = np.arange(len(reb))
    for off, col, color, label in (
        (-0.25, "transferable_skus", PALETTE["green"], "SKU dapat ditransfer"),
        (0.0, "stockout_stores", PALETTE["red"], "Toko risiko stockout"),
        (0.25, "overstock_stores", PALETTE["orange"], "Toko overstock"),
    ):
        ax.bar(x + off, reb[col], width=0.25, color=color, alpha=0.85, label=label)
    ax.set_xticks(x)
    ax.set_xticklabels(reb["campaign_id"])
    ax.set_title(
        "Peluang rebalancing — SKU dengan stockout & overstock simultan per kampanye"
    )
    ax.set_ylabel("Jumlah")
    ax.set_xlabel("Kampanye")
    ax.legend(fontsize=9)
    paths.append(str(save_chart(fig, "layer4_rebalancing")))

    # SLA breach by type
    sla = analysis["sla"]
    bt = sla["by_type"].sort_values("breach_rate")
    fig, ax = plt.subplots(figsize=(9, 4.8))
    labels = [t.replace("_", " ") for t in bt["exception_type"]]
    err_lo = ((bt["breach_rate"] - bt["breach_ci_lo"]) * 100).clip(lower=0)
    err_hi = ((bt["breach_ci_hi"] - bt["breach_rate"]) * 100).clip(lower=0)
    ax.barh(labels, bt["breach_rate"] * 100, color=PALETTE["orange"], alpha=0.85)
    ax.errorbar(
        bt["breach_rate"] * 100, labels, xerr=[err_lo, err_hi],
        fmt="none", ecolor=PALETTE["dark"], capsize=3, lw=1,
    )
    for y, (ci_hi, brc, tot) in enumerate(
        zip(bt["breach_ci_hi"], bt["breached"], bt["total"])
    ):
        ax.annotate(
            f" {brc}/{tot}", (ci_hi * 100, y), va="center", fontsize=8,
            xytext=(6, 0), textcoords="offset points",
        )
    ax.set_xlim(0, 118)
    ax.set_title(
        f"Tingkat pelanggaran SLA per tipe eksepsi — keseluruhan "
        f"{sla['breach_rate']:.1%} (CI 95% Wilson: "
        f"[{sla['breach_rate_wilson_ci'][0]:.1%}, {sla['breach_rate_wilson_ci'][1]:.1%}])"
    )
    ax.set_xlabel("Tingkat pelanggaran SLA (%); galat = CI 95% Wilson")
    paths.append(str(save_chart(fig, "layer4_sla_breach")))

    # Aging profile
    buckets = sla["aging_buckets"]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    bars = ax.bar(
        buckets["bucket"], buckets["count"], color=PALETTE["blue"], alpha=0.8,
        label="Total eksepsi",
    )
    ax.bar(
        buckets["bucket"], buckets["breached"], color=PALETTE["red"], alpha=0.9,
        label="Melanggar SLA",
    )
    for bar, cnt in zip(bars, buckets["count"]):
        ax.annotate(
            f"{cnt}", (bar.get_x() + bar.get_width() / 2, cnt),
            ha="center", va="bottom", fontsize=9,
        )
    ax.set_title(
        f"Profil umur eksepsi (bucket SLA) — {sla['detected_at_snapshot']} eksepsi "
        f"terdeteksi pada tanggal snapshot"
    )
    ax.set_ylabel("Jumlah eksepsi")
    ax.set_xlabel("Bucket umur (age_days, bidang temporal yang andal)")
    ax.legend(fontsize=9)
    paths.append(str(save_chart(fig, "layer4_aging_profile")))

    # Financial
    fin = analysis["financial"]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    labels = [
        "Pendapatan berisiko\n(stockout)", "Penalti\npelanggaran SLA",
        "Biaya ekspedisi\n(kritis)", "Penghematan\nrebalancing", "Biaya\ntransfer",
    ]
    values = [
        fin["stockout_revenue_at_risk"], fin["sla_breach_penalties"],
        fin["critical_expediting"], fin["rebalancing_savings"], fin["transfer_cost"],
    ]
    colors = [PALETTE["red"], PALETTE["orange"], "#8e44ad", PALETTE["green"], PALETTE["gray"]]
    bars = ax.bar(labels, values, color=colors, alpha=0.85)
    for bar, v in zip(bars, values):
        ax.annotate(
            f"${v:,.0f}", (bar.get_x() + bar.get_width() / 2, v),
            ha="center", va="bottom", fontsize=9,
        )
    ax.set_title(
        f"Estimasi dampak finansial (ILUSTRATIF) — total eksposur "
        f"${fin['total_exposure']:,.0f} | ROI rebalancing {fin['roi_ratio']:.1f}×"
    )
    ax.set_ylabel("USD ($, parameter ilustratif)")
    paths.append(str(save_chart(fig, "layer4_financial")))

    # Sensitivity: rank stability
    sens = analysis["sensitivity"]["table"].sort_values("rank_original")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    scen_labels = {
        "original": "Original (cap=3.0, w=2)",
        "conservative": "Konservatif (cap=2.0, w=3)",
        "aggressive": "Agresif (cap=4.0, w=1)",
    }
    for name, color in zip(scen_labels, (PALETTE["dark"], PALETTE["blue"], PALETTE["orange"])):
        ax.plot(
            sens["insight_id"], sens[f"rank_{name}"], marker="o", color=color,
            label=scen_labels[name], alpha=0.85,
        )
    ax.invert_yaxis()
    ax.set_title(
        f"Stabilitas peringkat impact score antar skenario bobot — "
        f"min \u03c1 Spearman = {analysis['sensitivity']['min_rho']:.3f} "
        f"({analysis['sensitivity']['verdict']})"
    )
    ax.set_ylabel("Peringkat (1 = prioritas tertinggi)")
    ax.set_xlabel("Insight")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(fontsize=9)
    paths.append(str(save_chart(fig, "layer4_sensitivity")))
    return paths


def analyze(tables: dict[str, pd.DataFrame] | None = None) -> dict:
    tables = tables or load_tables()
    rebal = analyze_rebalancing(tables)
    return {
        "rebalancing": rebal,
        "sla": analyze_sla(tables),
        "financial": analyze_financial(tables, rebal),
        "sensitivity": analyze_sensitivity(tables),
    }


def run(export: bool = True) -> dict:
    analysis = analyze()
    charts = make_charts(analysis)
    if export:
        export_csv("layer4_rebalancing", analysis["rebalancing"]["summary"])
        export_csv("layer4_sla_by_type", analysis["sla"]["by_type"])
        export_csv(
            "layer4_sensitivity",
            analysis["sensitivity"]["table"][
                [
                    "insight_id", "category", "affected_count", "lift",
                    "critical_count", "impact_score",
                    "score_original", "score_conservative", "score_aggressive",
                    "rank_original", "rank_conservative", "rank_aggressive",
                ]
            ],
        )
        sla = analysis["sla"]
        export_json(
            "layer4_opportunity",
            {
                "rebalancing": {
                    k: v for k, v in analysis["rebalancing"].items() if k != "summary"
                },
                "sla": {
                    k: v
                    for k, v in sla.items()
                    if k not in ("by_type", "aging_buckets")
                },
                "aging_buckets": sla["aging_buckets"].to_dict("records"),
                "financial": analysis["financial"],
                "sensitivity": {
                    k: v
                    for k, v in analysis["sensitivity"].items()
                    if k != "table"
                },
            },
        )
    analysis["charts"] = charts
    return analysis


if __name__ == "__main__":
    result = run()
    reb = result["rebalancing"]
    print(f"SKU transfer: {reb['total_transferable_skus']} | touchpoint: {reb['total_touchpoints']}")
    print(reb["summary"].to_string(index=False))
    sla = result["sla"]
    print(
        f"Pelanggaran SLA: {sla['breached']}/{sla['n_exceptions']} = {sla['breach_rate']:.1%} "
        f"CI {sla['breach_rate_wilson_ci']}"
    )
    fin = result["financial"]
    print(f"Total eksposur (ilustratif): ${fin['total_exposure']:,} | ROI {fin['roi_ratio']:.1f}x")
    sens = result["sensitivity"]
    print(
        f"Rekonstruksi skor terverifikasi: {sens['score_reconstruction_verified']} | "
        f"min rho={sens['min_rho']:.3f} ({sens['verdict']}) | top-5 stabil: {sens['common_top5']}"
    )
    print(f"Grafik: {result['charts']}")
