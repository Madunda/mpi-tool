import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from core.mpi_config import MPIConfig
from core.analysis_engine import AnalysisEngine

MPIConfig.initialize()
st.title("📈 MPI Results")
st.caption("Population-representative MPI results and contribution reporting.")

result = st.session_state.get("mpi_analysis_result")
if result is None:
    st.warning("No MPI analysis results are available yet.")
    st.info("Go to 📊 Analysis and run the MPI analysis first.")
    st.stop()

H, A, M0 = result.get("H", np.nan), result.get("A", np.nan), result.get("M0", np.nan)
cutoff = result.get("cutoff", np.nan)
weight_variable = result.get("weight_variable")
missing_method = result.get("missing_method")
projected_population = result.get("weighted_population", np.nan)
projected_poor = result.get("weighted_poor_population", np.nan)
projected_nonpoor = (
    projected_population - projected_poor
    if pd.notna(projected_population) and pd.notna(projected_poor) else np.nan
)

st.success("MPI analysis results are available. ✅")
if weight_variable:
    st.caption(f"Survey weight: `{weight_variable}`")

st.subheader("📊 Key MPI Results")
c1,c2,c3 = st.columns(3)
c1.metric("Headcount Ratio (H)", "N/A" if pd.isna(H) else f"{H:.4f}")
c2.metric("Intensity (A)", "N/A" if pd.isna(A) else f"{A:.4f}")
c3.metric("MPI (M0)", "N/A" if pd.isna(M0) else f"{M0:.4f}")

st.subheader("👥 Population Estimates")
p1,p2,p3 = st.columns(3)
p1.metric("Projected Population", "N/A" if pd.isna(projected_population) else f"{int(round(projected_population)):,}")
p2.metric("Projected Poor Population", "N/A" if pd.isna(projected_poor) else f"{int(round(projected_poor)):,}")
p3.metric("Projected Non-Poor Population", "N/A" if pd.isna(projected_nonpoor) else f"{int(round(projected_nonpoor)):,}")

st.caption("Projected Population is the population represented by the selected survey weights; it is not the raw sample count.")

st.divider()
st.subheader("🏛️ Dimension Contribution (%)")
dim = result.get("dimension_contribution", pd.DataFrame()).copy()
if not dim.empty:
    display = dim[["Dimension","Contribution (%)"]].copy()
    display["Contribution (%)"] = display["Contribution (%)"].round(4)
    st.dataframe(display, use_container_width=True, hide_index=True)
else:
    st.info("Dimension contribution is not available.")

st.divider()
st.subheader("🧩 Indicator Contribution (%)")
ind = result.get("indicator_contribution", pd.DataFrame()).copy()
if not ind.empty:
    cols = [c for c in ["Indicator","Uncensored Headcount","Censored Headcount","Contribution (%)"] if c in ind.columns]
    display = ind[cols].copy()
    for c in ["Uncensored Headcount","Censored Headcount","Contribution (%)"]:
        if c in display.columns:
            display[c] = display[c].round(4)
            if "Headcount" in c:
                display[c] = display[c] * 100
    rename = {"Uncensored Headcount":"Uncensored Headcount (%)","Censored Headcount":"Censored Headcount (%)"}
    display.rename(columns=rename, inplace=True)
    st.dataframe(display, use_container_width=True, hide_index=True)
else:
    st.info("Indicator contribution is not available.")

st.divider()
st.subheader("👥 Disaggregated MPI")
df = st.session_state.get("dataset")
if isinstance(df, pd.DataFrame) and not df.empty:
    group_options = [str(c) for c in df.columns]
    group_var = st.selectbox("Group by", ["None"] + group_options, key="results_disagg_group")
    if group_var != "None":
        try:
            dis = AnalysisEngine.disaggregate(df, group_var, missing_method=missing_method, cutoff=cutoff, weight_variable=weight_variable)
            if not dis.empty:
                for c in ["Projected Population","Projected Poor Population"]:
                    if c in dis.columns:
                        dis[c] = pd.to_numeric(dis[c], errors="coerce").round().astype("Int64")
                for c in ["H","A","M0"]:
                    if c in dis.columns:
                        dis[c] = dis[c].round(4)
                st.dataframe(dis, use_container_width=True, hide_index=True)
                fig = px.bar(
                    dis, x="H", y="Group", orientation="h",
                    text=dis["H"].map(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A"),
                    title=f"Headcount Ratio by {group_var}",
                )
                fig.update_layout(xaxis_title="Headcount Ratio", yaxis_title="")
                st.plotly_chart(fig, use_container_width=True)
        except Exception as exc:
            st.error(f"Disaggregation failed: {exc}")

st.divider()
st.subheader("⚙️ Analysis Information")
info = pd.DataFrame({
    "Parameter":["Poverty Cut-off","Missing Value Treatment","Survey Weight","Analysis Unit"],
    "Value":[f"{cutoff:.3f}", missing_method or "N/A", weight_variable or "Equal weights", MPIConfig.get().get("analysis_unit","N/A")]
})
st.dataframe(info, use_container_width=True, hide_index=True)
