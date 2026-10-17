"""Professional two-period MPI comparison."""

from __future__ import annotations

from copy import deepcopy

import pandas as pd
import plotly.express as px
import streamlit as st

from core.change_over_time import ChangeOverTimeEngine
from core.mpi_config import MPIConfig
from core.theme import page_header

BLUE = "#155EEF"
ORANGE = "#C2410C"
NAVY = "#102A43"

MPIConfig.initialize()
page_header(
    "⏳",
    "Change Over Time",
    "Compare two survey periods using the same MPI definition and the survey-weight setting stored in MPI Analysis.",
)

current_dataset = st.session_state.get("dataset")
current_config = deepcopy(MPIConfig.get())


def configured_weight(config: dict) -> str | None:
    """Resolve the active survey weight without asking for it again."""
    return (
        config.get("survey_weight_variable")
        or st.session_state.get("analysis_weight_variable")
    )


def current_period(year: str) -> dict:
    config = deepcopy(current_config)
    return {
        "year": year,
        "config": config,
        "dataset": current_dataset,
        "metadata": {},
        "weight_variable": configured_weight(config),
        "missing_method": config.get("missing_method", "strict"),
        "source": "Current MPI Configuration",
    }


def uploaded_period(year: str, uploaded_file) -> dict:
    loaded = ChangeOverTimeEngine.load_period(uploaded_file.getvalue())
    config = loaded["config"]
    metadata = loaded.get("metadata", {})
    weight = (
        config.get("survey_weight_variable")
        or metadata.get("weight_variable")
    )
    return {
        "year": year,
        "config": config,
        "dataset": loaded.get("dataset"),
        "metadata": metadata,
        "weight_variable": weight,
        "missing_method": config.get("missing_method") or metadata.get("missing_method") or "strict",
        "source": uploaded_file.name,
    }


def period_card(title: str, key: str) -> dict | None:
    with st.container(border=True):
        st.markdown(f"#### {title}")
        source = st.radio(
            "Source",
            ["Current MPI Configuration", "Upload .nmpi Project"],
            key=f"cot_source_{key}",
            horizontal=True,
            label_visibility="collapsed",
        )
        year = st.text_input(
            "Survey year",
            placeholder="e.g. 2015",
            key=f"cot_year_{key}",
        ).strip()

        if not year:
            st.caption("Enter the survey year. This exact label will be used throughout the comparison.")
            return None

        if source == "Current MPI Configuration":
            if current_dataset is None or current_dataset.empty:
                st.warning("Load the current dataset before using the current configuration.")
                return None
            weight = configured_weight(current_config)
            st.caption(f"Dataset: current active dataset · Weight: `{weight or 'None'}`")
            return current_period(year)

        uploaded = st.file_uploader(
            "MPI project",
            type=["nmpi"],
            key=f"cot_upload_{key}",
            label_visibility="collapsed",
        )
        if uploaded is None:
            st.caption("Upload the saved .nmpi project for this survey period.")
            return None
        try:
            period = uploaded_period(year, uploaded)
        except Exception as exc:
            st.error(f"Could not read the project: {exc}")
            return None
        if period["dataset"] is None:
            st.error("This .nmpi project does not contain its working dataset.")
            return None
        st.caption(f"Project: `{uploaded.name}` · Weight: `{period['weight_variable'] or 'None'}`")
        return period


left, right = st.columns(2, gap="large")
with left:
    period_a = period_card("Period A", "a")
with right:
    period_b = period_card("Period B", "b")

if not period_a or not period_b:
    st.info("Complete both period cards to continue.")
    st.stop()

if period_a["year"] == period_b["year"]:
    st.error("The two survey years must be different.")
    st.stop()

# Never silently fall back to unweighted sample results when a weight was configured.
for label, period in ((period_a["year"], period_a), (period_b["year"], period_b)):
    weight = period.get("weight_variable")
    if weight and weight not in period["dataset"].columns:
        st.error(f"Survey weight `{weight}` configured for {label} is not present in that period's dataset.")
        st.stop()

if not period_a.get("weight_variable") or not period_b.get("weight_variable"):
    st.warning(
        "One or both periods have no survey weight stored in MPI Configuration/.nmpi. "
        "The affected period would otherwise be calculated on the analytical sample. "
        "Return to Analysis and select the survey expansion weight before comparing."
    )

try:
    comparison = ChangeOverTimeEngine.compare(period_a, period_b)
except Exception as exc:
    st.error(f"Comparison could not be completed: {exc}")
    st.stop()

year_a, year_b = comparison["years"]

st.success(f"MPI definition validated for **{year_a}** and **{year_b}**.")

# ------------------------------------------------------------
# Overall MPI — INDEX VALUES, NOT PERCENTAGES
# ------------------------------------------------------------
st.subheader("Overall MPI Comparison")
st.caption("H, A and M0 are shown as index/proportion values. They are not converted to percentages here.")
overall = comparison["overall"].copy()
metric_long = overall.melt(
    id_vars="Year",
    value_vars=["H", "A", "M0"],
    var_name="Metric",
    value_name="Index Value",
)
fig = px.bar(
    metric_long,
    x="Metric",
    y="Index Value",
    color="Year",
    barmode="group",
    text=metric_long["Index Value"].map(lambda x: f"{x:.4f}"),
    color_discrete_map={year_a: BLUE, year_b: ORANGE},
)
fig.update_traces(textposition="outside", cliponaxis=False)
fig.update_layout(
    xaxis_title="",
    yaxis_title="Index Value",
    legend_title="Survey Year",
    margin=dict(t=30, b=20, l=20, r=20),
)
st.plotly_chart(fig, use_container_width=True)

with st.expander("Projected population estimates", expanded=False):
    display = overall[["Year", "Projected Population", "Projected Poor Population"]].copy()
    display["Projected Population"] = display["Projected Population"].round().astype("Int64")
    display["Projected Poor Population"] = display["Projected Poor Population"].round().astype("Int64")
    st.dataframe(display, use_container_width=True, hide_index=True)

# ------------------------------------------------------------
# Dimension contribution
# ------------------------------------------------------------
st.subheader("Dimension Contribution")
dimensions = comparison["dimensions"].copy()
dim_long = dimensions.melt(
    id_vars=["Dimension", "Change (pp)"],
    value_vars=[year_a, year_b],
    var_name="Year",
    value_name="Contribution (%)",
)
fig = px.bar(
    dim_long,
    x="Dimension",
    y="Contribution (%)",
    color="Year",
    barmode="group",
    text=dim_long["Contribution (%)"].map(lambda x: f"{x:.1f}%"),
    color_discrete_map={year_a: BLUE, year_b: ORANGE},
)
fig.update_traces(textposition="outside", cliponaxis=False)
fig.update_layout(xaxis_title="", yaxis_title="Contribution (%)", legend_title="Survey Year", margin=dict(t=30, b=20, l=20, r=20))
st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# Indicator deprivation — retain the strong horizontal view
# ------------------------------------------------------------
st.subheader("Indicator Deprivation Change")
st.caption("Uncensored headcount for every indicator; change is shown in percentage points in the table below.")
indicators = comparison["indicators"].copy()
indicator_plot = indicators[["Indicator", f"Uncensored {year_a}", f"Uncensored {year_b}"]].melt(
    id_vars="Indicator",
    var_name="Period",
    value_name="Headcount",
)
indicator_plot["Year"] = indicator_plot["Period"].str.replace("Uncensored ", "", regex=False)
indicator_plot["Headcount"] = indicator_plot["Headcount"] * 100
fig = px.bar(
    indicator_plot,
    x="Headcount",
    y="Indicator",
    color="Year",
    barmode="group",
    orientation="h",
    text=indicator_plot["Headcount"].map(lambda x: f"{x:.1f}%"),
    color_discrete_map={year_a: BLUE, year_b: ORANGE},
)
fig.update_traces(textposition="outside", cliponaxis=False)
fig.update_layout(xaxis_title="Uncensored Headcount (%)", yaxis_title="", legend_title="Survey Year", margin=dict(t=30, b=20, l=20, r=50))
st.plotly_chart(fig, use_container_width=True)

change_table = indicators[["Indicator", "Deprivation Change (pp)", "Contribution Change (pp)"]].rename(
    columns={
        "Deprivation Change (pp)": f"Change {year_a} → {year_b} (pp)",
        "Contribution Change (pp)": f"Contribution Change {year_a} → {year_b} (pp)",
    }
)
st.dataframe(
    change_table.style.format({
        f"Change {year_a} → {year_b} (pp)": "{:.2f}",
        f"Contribution Change {year_a} → {year_b} (pp)": "{:.2f}",
    }),
    use_container_width=True,
    hide_index=True,
)

# ------------------------------------------------------------
# Disaggregation
# ------------------------------------------------------------
st.subheader("Disaggregated MPI Comparison")
common_groups = [c for c in period_a["dataset"].columns if c in period_b["dataset"].columns]
if not common_groups:
    st.info("No common grouping variables are available between the two datasets.")
else:
    group_variable = st.selectbox("Grouping Variable", common_groups, key="cot_group_variable")
    try:
        disagg = ChangeOverTimeEngine.disaggregate(period_a, period_b, group_variable)
    except Exception as exc:
        st.error(f"Disaggregation could not be calculated: {exc}")
    else:
        disagg["H (%)"] = disagg["H"] * 100
        fig = px.bar(
            disagg,
            x="H (%)",
            y="Group",
            color="Year",
            barmode="group",
            orientation="h",
            text=disagg["H (%)"].map(lambda x: f"{x:.1f}%"),
            color_discrete_map={year_a: BLUE, year_b: ORANGE},
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(xaxis_title="Headcount (H, %)", yaxis_title=group_variable, legend_title="Survey Year", margin=dict(t=30, b=20, l=20, r=50))
        st.plotly_chart(fig, use_container_width=True)

        show_cols = ["Year", "Group", "Projected Population", "Projected Poor Population", "H", "A", "M0"]
        table = disagg[show_cols].copy()
        table["H"] = table["H"] * 100
        table["A"] = table["A"] * 100
        table["M0"] = table["M0"] * 100
        st.dataframe(
            table.style.format({
                "Projected Population": "{:,.0f}",
                "Projected Poor Population": "{:,.0f}",
                "H": "{:.2f}%",
                "A": "{:.2f}%",
                "M0": "{:.4f}%",
            }),
            use_container_width=True,
            hide_index=True,
        )

st.caption("Survey weights are inherited from MPI Analysis/configuration. No survey-weight input is required on this page.")
