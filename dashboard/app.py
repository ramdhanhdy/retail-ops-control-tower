"""Streamlit dashboard for the simulated Retail Ops Control Tower."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "data" / "sample"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_PATH = ROOT / "reports" / "weekly_ops_report.md"

SAMPLE_TABLES = [
    "campaigns",
    "stores",
    "allocation_plan",
    "dispatch",
    "store_confirmations",
    "photo_proofs",
    "sales_daily",
]
PROCESSED_TABLES = ["kpi_summary", "am_scorecard", "exceptions", "daily_action_list"]
OPTIONAL_TABLES = ["insights"]


@st.cache_data(show_spinner=False)
def read_csv(path: str) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        return pd.DataFrame()
    return pd.read_csv(csv_path)


@st.cache_data(show_spinner=False)
def load_tables() -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}
    for name in SAMPLE_TABLES:
        tables[name] = read_csv(str(SAMPLE_DIR / f"{name}.csv"))
    for name in PROCESSED_TABLES + OPTIONAL_TABLES:
        tables[name] = read_csv(str(PROCESSED_DIR / f"{name}.csv"))
    return tables


@st.cache_data(show_spinner=False)
def read_report(path: str) -> str:
    report_path = Path(path)
    if not report_path.exists():
        return ""
    return report_path.read_text(encoding="utf-8")


def missing_required_files() -> list[Path]:
    required = [SAMPLE_DIR / f"{name}.csv" for name in SAMPLE_TABLES]
    required.extend(PROCESSED_DIR / f"{name}.csv" for name in PROCESSED_TABLES)
    return [path for path in required if not path.exists()]


def show_missing_data_message(missing: Iterable[Path]) -> None:
    st.warning("Generated sample or processed data is missing.")
    st.markdown(
        "This dashboard uses simulated CSV outputs from the project pipeline. "
        "Generate the local data first, then rerun the dashboard:"
    )
    st.code(
        "python scripts/generate_sample_data.py\n"
        "python scripts/build_exception_table.py\n"
        "python scripts/build_kpi_summary.py\n"
        "python scripts/generate_weekly_report.py",
        language="bash",
    )
    st.caption("Missing files:")
    for path in missing:
        st.write(f"- {path.relative_to(ROOT)}")


def fmt_int(value: float | int | str | None) -> str:
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return "0"


def fmt_percent(value: float | int | str | None) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def title_case_metric(name: str) -> str:
    return name.replace("_", " ").title()


def kpi_lookup(kpi_summary: pd.DataFrame) -> dict[str, dict[str, object]]:
    if kpi_summary.empty:
        return {}
    return kpi_summary.set_index("kpi_name").to_dict("index")


def metric_value(kpis: dict[str, dict[str, object]], name: str) -> float:
    row = kpis.get(name, {})
    try:
        return float(row.get("value", 0))
    except (TypeError, ValueError):
        return 0.0


def display_metric(label: str, value: float, unit: str = "count") -> None:
    if unit == "ratio":
        st.metric(label, fmt_percent(value))
    else:
        st.metric(label, fmt_int(value))


def options_from(df: pd.DataFrame, column: str) -> list[str]:
    if df.empty or column not in df.columns:
        return []
    return sorted(str(value) for value in df[column].dropna().unique())


def campaign_label_map(campaigns: pd.DataFrame) -> dict[str, str]:
    if campaigns.empty:
        return {}
    return {
        str(row["campaign_id"]): f"{row['campaign_name']} ({row['campaign_id']})"
        for _, row in campaigns.iterrows()
    }


def filter_by_values(df: pd.DataFrame, column: str, selected: list[str]) -> pd.DataFrame:
    if df.empty or column not in df.columns or not selected:
        return df
    return df[df[column].astype(str).isin(selected)]


def filtered_tables(tables: dict[str, pd.DataFrame], campaign_ids: list[str], regions: list[str], ams: list[str]) -> dict[str, pd.DataFrame]:
    stores = tables["stores"].copy()
    stores = filter_by_values(stores, "region", regions)
    stores = filter_by_values(stores, "area_manager", ams)
    store_ids = set(stores["store_id"].astype(str)) if not stores.empty and "store_id" in stores else set()

    result: dict[str, pd.DataFrame] = {}
    for name, df in tables.items():
        view = df.copy()
        view = filter_by_values(view, "campaign_id", campaign_ids)
        if store_ids and "store_id" in view.columns:
            view = view[view["store_id"].astype(str).isin(store_ids)]
        if "region" in view.columns:
            view = filter_by_values(view, "region", regions)
        if "area_manager" in view.columns:
            view = filter_by_values(view, "area_manager", ams)
        result[name] = view
    result["stores"] = stores
    return result


def campaign_readiness_table(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    allocations = tables["allocation_plan"]
    confirmations = tables["store_confirmations"]
    photos = tables["photo_proofs"]
    campaigns = tables["campaigns"]
    if allocations.empty:
        return pd.DataFrame()

    rows = []
    for campaign_id, group in allocations.groupby("campaign_id"):
        alloc_ids = set(group["allocation_id"].astype(str))
        conf = confirmations[confirmations["allocation_id"].astype(str).isin(alloc_ids)] if not confirmations.empty else pd.DataFrame()
        confirmed_ids = set(conf["allocation_id"].astype(str)) if not conf.empty else set()
        confirmed = len(confirmed_ids)
        photo_conf_ids = set(photos["confirmation_id"].astype(str)) if not photos.empty else set()
        with_photo = len(set(conf["confirmation_id"].astype(str)).intersection(photo_conf_ids)) if not conf.empty else 0
        campaign = campaigns[campaigns["campaign_id"].astype(str) == str(campaign_id)] if not campaigns.empty else pd.DataFrame()
        campaign_name = campaign.iloc[0]["campaign_name"] if not campaign.empty else campaign_id
        readiness = with_photo / len(group) if len(group) else 0
        rows.append(
            {
                "campaign_id": campaign_id,
                "campaign": campaign_name,
                "allocation_lines": len(group),
                "confirmed_lines": confirmed,
                "photo_ready_lines": with_photo,
                "readiness_rate": readiness,
            }
        )
    return pd.DataFrame(rows).sort_values("readiness_rate", ascending=False)


def reconciliation_table(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    allocations = tables["allocation_plan"]
    dispatch = tables["dispatch"]
    confirmations = tables["store_confirmations"]
    if allocations.empty:
        return pd.DataFrame()
    plan = allocations.groupby("campaign_id", dropna=False)["planned_quantity"].sum().rename("planned_quantity")
    shipped = dispatch.groupby("campaign_id", dropna=False)["shipped_quantity"].sum().rename("shipped_quantity") if not dispatch.empty else pd.Series(dtype="float64")
    received = confirmations.groupby("campaign_id", dropna=False)["received_quantity"].sum().rename("received_quantity") if not confirmations.empty else pd.Series(dtype="float64")
    out = pd.concat([plan, shipped, received], axis=1).fillna(0).reset_index()
    out["ship_vs_plan"] = out["shipped_quantity"] - out["planned_quantity"]
    out["receipt_vs_ship"] = out["received_quantity"] - out["shipped_quantity"]
    return out


def store_detail_table(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    stores = tables["stores"].copy()
    if stores.empty:
        return stores
    exceptions = tables["exceptions"]
    confirmations = tables["store_confirmations"]
    sales = tables["sales_daily"]

    if not exceptions.empty:
        exc_counts = exceptions.groupby("store_id").agg(
            open_exceptions=("exception_id", "count"),
            critical_exceptions=("severity", lambda values: (values == "critical").sum()),
            sla_breaches=("sla_status", lambda values: (values == "breached").sum()),
        )
        stores = stores.merge(exc_counts, on="store_id", how="left")
    if not confirmations.empty:
        received = confirmations.groupby("store_id")["received_quantity"].sum().rename("received_units")
        stores = stores.merge(received, on="store_id", how="left")
    if not sales.empty:
        sold = sales.groupby("store_id")["units_sold"].sum().rename("units_sold")
        stores = stores.merge(sold, on="store_id", how="left")

    for col in ["open_exceptions", "critical_exceptions", "sla_breaches", "received_units", "units_sold"]:
        if col not in stores.columns:
            stores[col] = 0
        stores[col] = stores[col].fillna(0)
    stores["sell_through_rate"] = stores.apply(
        lambda row: row["units_sold"] / row["received_units"] if row["received_units"] else 0,
        axis=1,
    )
    return stores.sort_values(["critical_exceptions", "open_exceptions"], ascending=False)


def normalize_scorecard(am_scorecard: pd.DataFrame) -> pd.DataFrame:
    if am_scorecard.empty:
        return am_scorecard
    renamed = {}
    for column in am_scorecard.columns:
        if "backlog" in column.lower():
            renamed[column] = "am_followup_backlog"
    return am_scorecard.rename(columns=renamed)


def render_executive_overview(tables: dict[str, pd.DataFrame]) -> None:
    st.header("1. Executive overview")
    st.info("Portfolio demo using simulated sample data only. Figures do not represent Tomoro or any real retailer.")
    kpis = kpi_lookup(tables["kpi_summary"])
    cols = st.columns(4)
    with cols[0]:
        display_metric("Campaign readiness", metric_value(kpis, "campaign_readiness_rate"), "ratio")
    with cols[1]:
        display_metric("Open exceptions", metric_value(kpis, "open_exception_count"))
    with cols[2]:
        display_metric("SLA breaches", metric_value(kpis, "sla_breach_count"))
    with cols[3]:
        display_metric("Sell-through", metric_value(kpis, "sell_through_rate"), "ratio")

    kpi_rows = tables["kpi_summary"].copy()
    if not kpi_rows.empty:
        kpi_rows["metric"] = kpi_rows["kpi_name"].map(title_case_metric)
        kpi_rows["display_value"] = kpi_rows.apply(
            lambda row: fmt_percent(row["value"]) if row["unit"] == "ratio" else fmt_int(row["value"]),
            axis=1,
        )
        st.dataframe(kpi_rows[["metric", "category", "display_value", "description"]], use_container_width=True, hide_index=True)


def render_campaign_readiness(tables: dict[str, pd.DataFrame]) -> None:
    st.header("2. Campaign readiness")
    readiness = campaign_readiness_table(tables)
    if readiness.empty:
        st.warning("No allocation data available for the current filters.")
        return
    chart = readiness.copy()
    chart["readiness_pct"] = chart["readiness_rate"] * 100
    st.plotly_chart(
        px.bar(chart, x="campaign", y="readiness_pct", text="readiness_pct", title="Photo-ready campaign allocation lines", labels={"readiness_pct": "Ready lines (%)", "campaign": "Campaign"}),
        use_container_width=True,
    )
    table = readiness.copy()
    table["readiness_rate"] = table["readiness_rate"].map(fmt_percent)
    st.dataframe(table, use_container_width=True, hide_index=True)


def render_allocation_reconciliation(tables: dict[str, pd.DataFrame]) -> None:
    st.header("3. Allocation reconciliation")
    recon = reconciliation_table(tables)
    if recon.empty:
        st.warning("No allocation data available for the current filters.")
        return
    st.plotly_chart(
        px.bar(recon, x="campaign_id", y=["planned_quantity", "shipped_quantity", "received_quantity"], barmode="group", title="Planned vs shipped vs received units"),
        use_container_width=True,
    )
    st.dataframe(recon, use_container_width=True, hide_index=True)


def render_exception_board(tables: dict[str, pd.DataFrame]) -> None:
    st.header("4. Exception board")
    exceptions = tables["exceptions"]
    actions = tables["daily_action_list"]
    if exceptions.empty:
        st.warning("No exceptions available for the current filters.")
        return
    cols = st.columns(3)
    with cols[0]:
        st.metric("Filtered exceptions", fmt_int(len(exceptions)))
    with cols[1]:
        st.metric("Critical", fmt_int((exceptions["severity"] == "critical").sum()))
    with cols[2]:
        st.metric("SLA breached", fmt_int((exceptions["sla_status"] == "breached").sum()))

    left, right = st.columns(2)
    with left:
        by_type = exceptions.groupby("exception_type").size().reset_index(name="count").sort_values("count", ascending=False)
        st.plotly_chart(px.bar(by_type, x="count", y="exception_type", orientation="h", title="Exceptions by type"), use_container_width=True)
    with right:
        by_severity = exceptions.groupby("severity").size().reset_index(name="count")
        st.plotly_chart(px.pie(by_severity, names="severity", values="count", title="Severity mix"), use_container_width=True)

    st.subheader("Priority action list")
    action_source = actions if not actions.empty else exceptions
    cols_to_show = [col for col in ["rank", "exception_id", "exception_type", "severity", "priority_score", "owner", "region", "area_manager", "store_id", "campaign_id", "age_days", "sla_status", "recommended_action"] if col in action_source.columns]
    st.dataframe(action_source[cols_to_show].head(25), use_container_width=True, hide_index=True)


def pareto_curve(exceptions: pd.DataFrame) -> pd.DataFrame:
    if exceptions.empty or "store_id" not in exceptions.columns:
        return pd.DataFrame()
    counts = (
        exceptions.dropna(subset=["store_id"])
        .groupby("store_id")
        .size()
        .sort_values(ascending=False)
        .reset_index(name="exceptions")
    )
    if counts.empty:
        return pd.DataFrame()
    counts["store_rank"] = range(1, len(counts) + 1)
    counts["cumulative_share"] = counts["exceptions"].cumsum() / counts["exceptions"].sum()
    return counts


def render_insights(tables: dict[str, pd.DataFrame]) -> None:
    st.header("5. Diagnostic insights")
    st.caption(
        "Root-cause findings mined from the exception table: concentration, "
        "hotspot lift, upstream attribution, and rebalancing opportunities. "
        "Ranked by impact score. Findings are computed on the full dataset; "
        "the Pareto chart respects the sidebar filters."
    )
    insights = tables.get("insights", pd.DataFrame())
    if insights.empty:
        st.warning(
            "data/processed/insights.csv is missing. Run "
            "python scripts/build_insights.py to generate it."
        )
    else:
        cols = st.columns(3)
        with cols[0]:
            st.metric("Ranked findings", fmt_int(len(insights)))
        with cols[1]:
            st.metric("Categories", fmt_int(insights["category"].nunique()))
        with cols[2]:
            top_impact = insights["impact_score"].max() if "impact_score" in insights.columns else 0
            st.metric("Top impact score", fmt_int(top_impact))

        for _, row in insights.iterrows():
            label = f"{row['insight_id']} | {row['headline']} (impact {fmt_int(row.get('impact_score', 0))})"
            with st.expander(label):
                st.write(row.get("detail", ""))
                meta_cols = st.columns(3)
                with meta_cols[0]:
                    st.metric("Affected", fmt_int(row.get("affected_count", 0)))
                with meta_cols[1]:
                    lift = row.get("lift", 0)
                    st.metric("Lift", f"{float(lift):.2f}x" if float(lift or 0) else "n/a")
                with meta_cols[2]:
                    st.metric("Category", str(row.get("category", "")).replace("_", " "))
                st.markdown(f"**Evidence:** {row.get('evidence', '')}")
                st.markdown(f"**Recommended action:** {row.get('recommended_action', '')}")

    st.subheader("Exception concentration (Pareto)")
    curve = pareto_curve(tables["exceptions"])
    if curve.empty:
        st.warning("No exception data available for the current filters.")
        return
    fig = go.Figure()
    fig.add_bar(
        x=curve["store_rank"], y=curve["exceptions"], name="Exceptions per store"
    )
    fig.add_scatter(
        x=curve["store_rank"],
        y=curve["cumulative_share"] * 100,
        name="Cumulative share (%)",
        yaxis="y2",
        mode="lines",
    )
    fig.add_hline(y=80, line_dash="dash", line_color="gray", yref="y2")
    fig.update_layout(
        title="Stores ranked by exception count (80% line dashed)",
        xaxis_title="Store rank",
        yaxis=dict(title="Exceptions"),
        yaxis2=dict(title="Cumulative share (%)", overlaying="y", side="right", range=[0, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_am_scorecard(tables: dict[str, pd.DataFrame]) -> None:
    st.header("6. AM scorecard")
    scorecard = normalize_scorecard(tables["am_scorecard"])
    if scorecard.empty:
        st.warning("No AM scorecard data available for the current filters.")
        return
    chart = scorecard.sort_values("open_exception_count", ascending=False)
    st.plotly_chart(px.bar(chart, x="area_manager", y="open_exception_count", color="region", title="Open exceptions by area manager"), use_container_width=True)
    display = scorecard.copy()
    for col in ["sell_through_rate", "exception_rate"]:
        if col in display.columns:
            display[col] = display[col].map(lambda value: f"{float(value):.3f}")
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_store_detail(tables: dict[str, pd.DataFrame]) -> None:
    st.header("7. Store detail table")
    detail = store_detail_table(tables)
    if detail.empty:
        st.warning("No store data available for the current filters.")
        return
    display = detail[[col for col in ["store_id", "store_name", "region", "area_manager", "store_format", "open_exceptions", "critical_exceptions", "sla_breaches", "received_units", "units_sold", "sell_through_rate"] if col in detail.columns]].copy()
    if "sell_through_rate" in display.columns:
        display["sell_through_rate"] = display["sell_through_rate"].map(fmt_percent)
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_weekly_report_preview() -> None:
    st.header("8. Weekly report preview")
    report = read_report(str(REPORT_PATH))
    if not report:
        st.warning("reports/weekly_ops_report.md is missing. Run python scripts/generate_weekly_report.py to create it.")
        return
    st.markdown(report)


def main() -> None:
    st.set_page_config(page_title="Retail Ops Control Tower", layout="wide")
    st.title("Retail Ops Control Tower")
    st.caption("Interactive control tower for simulated campaign execution, allocation reconciliation, exceptions, AM workload, and weekly reporting.")

    missing = missing_required_files()
    if missing:
        show_missing_data_message(missing)
        return

    tables = load_tables()
    campaign_labels = campaign_label_map(tables["campaigns"])
    campaign_options = list(campaign_labels.keys())

    st.sidebar.header("Filters")
    selected_campaign_labels = st.sidebar.multiselect(
        "Campaign",
        options=[campaign_labels[cid] for cid in campaign_options],
        default=[campaign_labels[cid] for cid in campaign_options],
    )
    label_to_id = {label: cid for cid, label in campaign_labels.items()}
    selected_campaigns = [label_to_id[label] for label in selected_campaign_labels]

    region_options = options_from(tables["stores"], "region")
    selected_regions = st.sidebar.multiselect("Region", options=region_options, default=region_options)
    am_options = options_from(tables["stores"], "area_manager")
    selected_ams = st.sidebar.multiselect("AM", options=am_options, default=am_options)

    filtered = filtered_tables(tables, selected_campaigns, selected_regions, selected_ams)

    sections = [
        "Executive overview",
        "Campaign readiness",
        "Allocation reconciliation",
        "Exception board",
        "Insights",
        "AM scorecard",
        "Store detail table",
        "Weekly report preview",
    ]
    tabs = st.tabs(sections)
    with tabs[0]:
        render_executive_overview(filtered)
    with tabs[1]:
        render_campaign_readiness(filtered)
    with tabs[2]:
        render_allocation_reconciliation(filtered)
    with tabs[3]:
        render_exception_board(filtered)
    with tabs[4]:
        render_insights(filtered)
    with tabs[5]:
        render_am_scorecard(filtered)
    with tabs[6]:
        render_store_detail(filtered)
    with tabs[7]:
        render_weekly_report_preview()


if __name__ == "__main__":
    main()
