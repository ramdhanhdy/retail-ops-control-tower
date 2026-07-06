"""Streamlit dashboard for the Retail Ops Control Tower.

5 question-named views + 1 action queue view, organized around what
an Ops Lead asks throughout the day.
"""
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
    "campaigns", "stores", "allocation_plan", "dispatch",
    "store_confirmations", "photo_proofs", "sales_daily",
]
PROCESSED_TABLES = ["kpi_summary", "am_scorecard", "exceptions", "daily_action_list"]
OPTIONAL_TABLES = ["insights"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Filter helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# KPI helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Table builders
# ---------------------------------------------------------------------------

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
        rows.append({
            "campaign_id": campaign_id, "campaign": campaign_name,
            "allocation_lines": len(group), "confirmed_lines": confirmed,
            "photo_ready_lines": with_photo, "readiness_rate": readiness,
        })
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
        lambda row: row["units_sold"] / row["received_units"] if row["received_units"] else 0, axis=1)
    return stores.sort_values(["critical_exceptions", "open_exceptions"], ascending=False)


def normalize_scorecard(am_scorecard: pd.DataFrame) -> pd.DataFrame:
    if am_scorecard.empty:
        return am_scorecard
    renamed = {}
    for column in am_scorecard.columns:
        if "backlog" in column.lower():
            renamed[column] = "<<redacted:am_backlog>>"
    return am_scorecard.rename(columns=renamed)


def pareto_curve(exceptions: pd.DataFrame) -> pd.DataFrame:
    if exceptions.empty or "store_id" not in exceptions.columns:
        return pd.DataFrame()
    counts = (
        exceptions.dropna(subset=["store_id"])
        .groupby("store_id").size().sort_values(ascending=False)
        .reset_index(name="exceptions")
    )
    if counts.empty:
        return pd.DataFrame()
    counts["store_rank"] = range(1, len(counts) + 1)
    counts["cumulative_share"] = counts["exceptions"].cumsum() / counts["exceptions"].sum()
    return counts


# ---------------------------------------------------------------------------
# View 1: What needs attention today?
# ---------------------------------------------------------------------------

def render_attention_today(tables: dict[str, pd.DataFrame]) -> None:
    st.header("What needs attention today?")
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

    exceptions = tables["exceptions"]
    if not exceptions.empty:
        critical = exceptions[exceptions["severity"] == "critical"]
        breached = exceptions[exceptions["sla_status"] == "breached"]
        st.markdown(f"**{len(critical)} critical** exceptions, **{len(breached)} SLA breached**")

    actions = tables["daily_action_list"]
    action_source = actions if not actions.empty else exceptions
    if not action_source.empty:
        cols_to_show = [col for col in [
            "rank", "exception_id", "exception_type", "severity",
            "priority_score", "owner", "area_manager", "store_id",
            "sla_status", "recommended_action",
        ] if col in action_source.columns]
        st.dataframe(action_source[cols_to_show].head(15), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# View 2: What do I fix first?
# ---------------------------------------------------------------------------

def render_fix_first(tables: dict[str, pd.DataFrame]) -> None:
    st.header("What do I fix first?")
    exceptions = tables["exceptions"]
    actions = tables["daily_action_list"]
    if exceptions.empty:
        st.warning("No exceptions data available.")
        return

    cols = st.columns(3)
    with cols[0]:
        st.metric("Total exceptions", fmt_int(len(exceptions)))
    with cols[1]:
        st.metric("Critical", fmt_int((exceptions["severity"] == "critical").sum()))
    with cols[2]:
        st.metric("SLA breached", fmt_int((exceptions["sla_status"] == "breached").sum()))

    left, right = st.columns(2)
    with left:
        by_type = exceptions.groupby("exception_type").size().reset_index(name="count").sort_values("count", ascending=True)
        st.plotly_chart(px.bar(by_type, x="count", y="exception_type", orientation="h", title="Exceptions by type"), use_container_width=True)
    with right:
        by_severity = exceptions.groupby("severity").size().reset_index(name="count")
        st.plotly_chart(px.pie(by_severity, names="severity", values="count", title="Severity mix"), use_container_width=True)

    st.subheader("Priority action list")
    action_source = actions if not actions.empty else exceptions
    cols_to_show = [col for col in [
        "rank", "exception_id", "exception_type", "severity", "priority_score",
        "owner", "region", "area_manager", "store_id", "campaign_id",
        "age_days", "sla_status", "recommended_action",
    ] if col in action_source.columns]
    st.dataframe(action_source[cols_to_show].head(25), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# View 3: What's about to breach?
# ---------------------------------------------------------------------------

def render_about_to_breach(tables: dict[str, pd.DataFrame]) -> None:
    st.header("What's about to breach?")
    exceptions = tables["exceptions"]
    if exceptions.empty:
        st.warning("No exceptions data available.")
        return

    approaching = exceptions[exceptions["sla_status"] == "approaching"]
    breached = exceptions[exceptions["sla_status"] == "breached"]
    cols = st.columns(2)
    with cols[0]:
        st.metric("Approaching SLA", fmt_int(len(approaching)))
    with cols[1]:
        st.metric("Already breached", fmt_int(len(breached)))

    at_risk = pd.concat([breached, approaching]) if not approaching.empty else breached
    if at_risk.empty:
        st.info("No exceptions at SLA risk.")
        return
    cols_to_show = [col for col in [
        "exception_id", "exception_type", "severity", "priority_score",
        "store_id", "area_manager", "age_days", "sla_status",
    ] if col in at_risk.columns]
    st.dataframe(at_risk[cols_to_show], use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# View 4: Which AM needs a call?
# ---------------------------------------------------------------------------

def render_am_call(tables: dict[str, pd.DataFrame]) -> None:
    st.header("Which AM needs a call?")
    scorecard = normalize_scorecard(tables["am_scorecard"])
    if scorecard.empty:
        st.warning("No AM scorecard data available.")
        return
    chart = scorecard.sort_values("open_exception_count", ascending=False)
    st.plotly_chart(px.bar(chart, x="area_manager", y="open_exception_count", color="region", title="Open exceptions by area manager"), use_container_width=True)
    display = scorecard.copy()
    for col in ["sell_through_rate", "exception_rate"]:
        if col in display.columns:
            display[col] = display[col].map(lambda value: f"{float(value):.3f}")
    st.dataframe(display, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# View 5: Are campaigns on track?
# ---------------------------------------------------------------------------

def render_campaigns_on_track(tables: dict[str, pd.DataFrame]) -> None:
    st.header("Are campaigns on track?")
    readiness = campaign_readiness_table(tables)
    if readiness.empty:
        st.warning("No allocation data available.")
        return
    chart = readiness.copy()
    chart["readiness_pct"] = chart["readiness_rate"] * 100
    st.plotly_chart(
        px.bar(chart, x="campaign", y="readiness_pct", text="readiness_pct", title="Photo-ready allocation lines (%)"),
        use_container_width=True)

    recon = reconciliation_table(tables)
    if not recon.empty:
        st.subheader("Planned vs shipped vs received")
        st.plotly_chart(px.bar(recon, x="campaign_id", y=["planned_quantity", "shipped_quantity", "received_quantity"], barmode="group"), use_container_width=True)
        st.dataframe(recon, use_container_width=True, hide_index=True)

    detail = store_detail_table(tables)
    if not detail.empty:
        display = detail[[col for col in [
            "store_id", "store_name", "region", "area_manager",
            "open_exceptions", "critical_exceptions", "sla_breaches",
            "received_units", "units_sold", "sell_through_rate",
        ] if col in detail.columns]].copy()
        if "sell_through_rate" in display.columns:
            display["sell_through_rate"] = display["sell_through_rate"].map(fmt_percent)
        st.dataframe(display, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# View 6: Did interventions work? (verification)
# ---------------------------------------------------------------------------

def render_verification(tables: dict[str, pd.DataFrame]) -> None:
    st.header("Did interventions work?")
    outcomes_path = SAMPLE_DIR / "intervention_outcomes.csv"
    if not outcomes_path.exists():
        st.warning("Run `python scripts/generate_sample_data.py` and `python scripts/build_verification.py` first.")
        return
    outcomes = pd.read_csv(outcomes_path)
    if outcomes.empty:
        st.warning("No intervention outcomes data.")
        return

    int_rate = outcomes["resolved"].mean()
    ctrl_rate = outcomes["control_resolved"].mean()
    effect = int_rate - ctrl_rate

    cols = st.columns(3)
    with cols[0]:
        st.metric("Intervention resolved", fmt_percent(int_rate))
    with cols[1]:
        st.metric("Control resolved", fmt_percent(ctrl_rate))
    with cols[2]:
        st.metric("Observed effect", f"{effect:+.1%}")

    st.info(
        "Results are from simulated data. The deliverable is the measurement "
        "methodology, not the finding."
    )

    by_type = outcomes.groupby("exception_type")[["resolved", "control_resolved"]].mean()
    by_type["effect"] = by_type["resolved"] - by_type["control_resolved"]
    by_type = by_type.sort_values("effect", ascending=True)
    st.plotly_chart(px.bar(by_type.reset_index(), x="effect", y="exception_type", orientation="h", title="Effect by exception type"), use_container_width=True)


# ---------------------------------------------------------------------------
# View 7: Action queue (assign/resolve)
# ---------------------------------------------------------------------------

def render_action_queue(tables: dict[str, pd.DataFrame]) -> None:
    st.header("Action queue")
    import sqlite3
    from retail_ops_control_tower.dashboard.action_queue import (
        init_db, assign_exception, resolve_exception, get_queue,
    )

    DB_PATH = ROOT / "data" / "processed" / "action_queue.db"
    conn = sqlite3.connect(str(DB_PATH))
    init_db(conn)

    st.subheader("Assign new action")
    exceptions = tables["exceptions"]
    if not exceptions.empty:
        exc_ids = sorted(exceptions["exception_id"].unique().tolist())
        am_options = options_from(tables["stores"], "area_manager")
        col1, col2, col3 = st.columns(3)
        with col1:
            sel_exc = st.selectbox("Exception ID", exc_ids, key="aq_exc")
        with col2:
            sel_am = st.selectbox("Assign to", am_options, key="aq_am")
        with col3:
            sel_action = st.selectbox("Action type", ["phone_call", "site_visit", "dc_count_verification", "sku_transfer", "escalation"], key="aq_type")
        if st.button("Assign", key="aq_assign"):
            assign_exception(conn, sel_exc, sel_am, sel_action)
            st.success(f"Assigned {sel_exc} to {sel_am}")
            st.rerun()

    st.subheader("Queue")
    queue = get_queue(conn)
    if queue:
        queue_df = pd.DataFrame(queue)
        st.dataframe(queue_df, use_container_width=True, hide_index=True)

        st.subheader("Resolve action")
        queue_exc_ids = [q["exception_id"] for q in queue]
        sel_resolve = st.selectbox("Exception to resolve", queue_exc_ids, key="aq_resolve")
        resolve_status = st.selectbox("Outcome", ["resolved", "unresolved", "failed"], key="aq_status")
        resolve_notes = st.text_input("Notes", key="aq_notes")
        if st.button("Resolve", key="aq_resolve_btn"):
            resolve_exception(conn, sel_resolve, resolve_status, resolve_notes)
            st.success(f"Resolved {sel_resolve}: {resolve_status}")
            st.rerun()
    else:
        st.info("No actions in queue. Assign one above.")

    conn.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="Retail Ops Control Tower", layout="wide")
    st.title("Retail Ops Control Tower")
    st.caption("Kopi Senja -- 100-store coffee chain, 3 seasonal LTO campaigns, 1,603 operational exceptions.")

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

    views = [
        "What needs attention today?",
        "What do I fix first?",
        "What's about to breach?",
        "Which AM needs a call?",
        "Are campaigns on track?",
        "Did interventions work?",
        "Action queue",
    ]
    tabs = st.tabs(views)
    with tabs[0]:
        render_attention_today(filtered)
    with tabs[1]:
        render_fix_first(filtered)
    with tabs[2]:
        render_about_to_breach(filtered)
    with tabs[3]:
        render_am_call(filtered)
    with tabs[4]:
        render_campaigns_on_track(filtered)
    with tabs[5]:
        render_verification(filtered)
    with tabs[6]:
        render_action_queue(filtered)


if __name__ == "__main__":
    main()
