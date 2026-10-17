import pandas as pd
import plotly.express as px
import streamlit as st

from core.analysis_engine import AnalysisEngine
from core.mpi_config import MPIConfig

MPIConfig.initialize()

st.title("📊 MPI Analysis")
st.caption(
    "Validate the MPI definition, select the survey weight once, "
    "and run the Alkire–Foster analysis."
)

df = st.session_state.get("dataset")
if df is None:
    st.warning("📂 Please load a dataset before running the analysis.")
    st.stop()
if not isinstance(df, pd.DataFrame) or df.empty:
    st.error("The loaded dataset is empty or invalid.")
    st.stop()

config = MPIConfig.get()
indicators = AnalysisEngine.get_indicator_map()

# Always read the active weight from the MPI configuration first.
# The session-state value is retained only as a backward-compatible fallback.
weight_variable = config.get("survey_weight_variable") or st.session_state.get("analysis_weight_variable")
missing_method = config.get("missing_method") or st.session_state.get("analysis_missing_method", "strict")
cutoff = float(config.get("poverty_cutoff", 0.333))

st.subheader("📂 Analysis Readiness")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Observations", f"{len(df):,}")
c2.metric("Variables", f"{len(df.columns):,}")
c3.metric("Dimensions", f"{len(config.get('dimensions', [])):,}")
c4.metric("Indicators", f"{len(indicators):,}")

st.divider()
st.subheader("⚙️ Analysis Settings")
st.caption(
    "These settings become part of the active MPI configuration and are reused automatically by Change Over Time."
)

sc1, sc2, sc3 = st.columns([1.4, 1.2, 1.0], gap="large")

with sc1:
    weight_options = ["None"] + [str(c) for c in df.columns]
    current_weight = weight_variable if weight_variable in weight_options else "None"
    selected_weight = st.selectbox(
        "Survey Weight Variable",
        weight_options,
        index=weight_options.index(current_weight),
        help="Select the survey expansion weight used for population estimates and weighted MPI results.",
    )
    weight_variable = None if selected_weight == "None" else selected_weight

with sc2:
    methods = ["strict", "normalize", "zero"]
    missing_method = st.selectbox(
        "Missing Value Treatment",
        methods,
        index=methods.index(missing_method) if missing_method in methods else 0,
        format_func=lambda x: {
            "strict": "Strict — require observed indicators",
            "normalize": "Normalize observed weight",
            "zero": "Treat missing as 0",
        }[x],
    )

with sc3:
    cutoff = st.number_input(
        "Poverty Cut-off (k)",
        min_value=0.0,
        max_value=1.0,
        value=cutoff,
        step=0.001,
        format="%.3f",
    )

# Persist the settings centrally. COT reads this same configuration.
config["survey_weight_variable"] = weight_variable
config["missing_method"] = missing_method
config["poverty_cutoff"] = cutoff
MPIConfig.save(config)
st.session_state.analysis_weight_variable = weight_variable
st.session_state.analysis_missing_method = missing_method

if weight_variable:
    st.success(f"Survey weight active: **{weight_variable}** — population estimates will use the expansion weight.")
else:
    st.warning("No survey weight is selected. Results will use the analytical sample rather than projected population totals.")

validation_errors = []
try:
    AnalysisEngine.validate_dataset(df)
    AnalysisEngine.validate_indicator_variables(df)
    AnalysisEngine.validate_deprivation_values(df)
    AnalysisEngine.validate_indicator_weights()
    if weight_variable:
        AnalysisEngine.get_survey_weights(df, weight_variable)
except Exception as exc:
    validation_errors.append(str(exc))

if validation_errors:
    st.error("Data or MPI configuration needs attention.")
    for msg in validation_errors:
        st.error(msg)
    st.stop()

st.success("Dataset, deprivation coding and MPI weights are valid. ✅")

if st.button("▶️ Run MPI Analysis", type="primary", use_container_width=True):
    try:
        with st.spinner("Calculating Alkire–Foster MPI..."):
            result = AnalysisEngine.run(
                df=df,
                missing_method=missing_method,
                cutoff=cutoff,
                weight_variable=weight_variable,
            )
        st.session_state.mpi_analysis_result = result
        st.session_state.mpi_analysis_settings = {
            "cutoff": cutoff,
            "missing_method": missing_method,
            "weight_variable": weight_variable,
        }
        st.success("MPI analysis completed successfully. Open 📈 Results for the full reporting tables.")
    except Exception as exc:
        st.error(f"MPI analysis failed: {exc}")
        st.stop()

result = st.session_state.get("mpi_analysis_result")
if result is None:
    st.info("Run the analysis to display the contribution visualizations.")
    st.stop()

st.divider()
st.subheader("🏛️ Dimension Contribution")
dim = result.get("dimension_contribution", pd.DataFrame()).copy()
if dim.empty or "Contribution (%)" not in dim.columns:
    st.info("Dimension contribution is not available.")
else:
    dim = dim[["Dimension", "Contribution (%)"]].dropna()
    fig = px.pie(
        dim,
        names="Dimension",
        values="Contribution (%)",
        hole=0.55,
        title="Contribution of Dimensions to Overall MPI",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_traces(
        texttemplate="%{label}<br>%{percent:.1%}",
        hovertemplate="%{label}: %{value:.2f}%<extra></extra>",
    )
    fig.update_layout(legend_title_text="", margin=dict(t=70, b=20, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("🧩 Indicator Contribution")
ind = result.get("indicator_contribution", pd.DataFrame()).copy()
if ind.empty or "Contribution (%)" not in ind.columns:
    st.info("Indicator contribution is not available.")
else:
    ind = ind[["Indicator", "Contribution (%)"]].dropna()
    fig = px.pie(
        ind,
        names="Indicator",
        values="Contribution (%)",
        hole=0.55,
        title="Contribution of Indicators to Overall MPI",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_traces(
        texttemplate="%{label}<br>%{percent:.1%}",
        hovertemplate="%{label}: %{value:.2f}%<extra></extra>",
    )
    fig.update_layout(legend_title_text="", margin=dict(t=70, b=20, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)

st.caption("Detailed H, A, M0, population estimates and contribution tables are available under 📈 Results.")
