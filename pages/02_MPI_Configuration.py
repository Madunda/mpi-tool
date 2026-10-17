"""Compact, professional MPI configuration workspace."""

from __future__ import annotations

import streamlit as st

from core.mpi_config import MPIConfig
from core.theme import page_header

MPIConfig.initialize()
config = MPIConfig.get()
dataset = st.session_state.get("dataset")

page_header(
    "⚙️",
    "MPI Configuration",
    "Build the MPI definition in a compact workspace. Edit only what you need; weights and indicators remain synchronized automatically.",
)

# ------------------------------------------------------------------
# Project settings
# ------------------------------------------------------------------
with st.container(border=True):
    st.markdown("### Project settings")
    c1, c2, c3, c4 = st.columns([2.2, 1.2, 1.0, 1.3], gap="medium")
    with c1:
        project_name = st.text_input("Project Name", value=config.get("project_name", "New MPI Project"))
    with c2:
        analysis_unit = st.selectbox(
            "Analysis Unit",
            ["Household", "Individual", "Person"],
            index=["Household", "Individual", "Person"].index(config.get("analysis_unit", "Household"))
            if config.get("analysis_unit", "Household") in ["Household", "Individual", "Person"] else 0,
        )
    with c3:
        cutoff = st.number_input(
            "Poverty Cut-off (k)",
            min_value=0.0,
            max_value=1.0,
            value=float(config.get("poverty_cutoff", 0.333)),
            step=0.001,
            format="%.3f",
        )
    with c4:
        weight_method = st.selectbox(
            "Weight Method",
            ["Equal", "Custom"],
            index=0 if config.get("weight_method", "Equal") == "Equal" else 1,
        )

    if st.button("Save Project Settings", type="primary", key="save_project_settings"):
        MPIConfig.update_project_settings(
            project_name=project_name,
            analysis_unit=analysis_unit,
            poverty_cutoff=cutoff,
            weight_method=weight_method,
        )
        st.success("Project settings saved.")
        st.rerun()

# ------------------------------------------------------------------
# Weight status — always visible, very compact
# ------------------------------------------------------------------
config = MPIConfig.get()
total_weight = MPIConfig.total_weight()
weight_ok = MPIConfig.weights_are_valid()

m1, m2, m3 = st.columns(3)
m1.metric("Dimensions", len(config.get("dimensions", [])))
m2.metric("Total Dimension Weight", f"{total_weight:.3f}")
m3.metric("Weight Status", "Valid" if weight_ok else "Needs attention")

if not weight_ok:
    st.warning("Dimension weights must sum exactly to 1.000. Equal weighting can rebalance them automatically.")

# ------------------------------------------------------------------
# Add dimension
# ------------------------------------------------------------------
with st.popover("＋ Add Dimension", use_container_width=True):
    st.markdown("#### New dimension")
    with st.form("add_dimension_form", clear_on_submit=True):
        name = st.text_input("Dimension Name", placeholder="e.g. Education")
        if MPIConfig.is_equal_weighting():
            st.caption("Equal weighting is active. The dimension weight will be recalculated automatically.")
            weight = 0.0
        else:
            weight = st.number_input("Dimension Weight", min_value=0.0, max_value=1.0, value=0.333, step=0.001, format="%.3f")
        submitted = st.form_submit_button("Add Dimension", type="primary", use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("Enter a dimension name.")
            elif MPIConfig.add_dimension(name, weight):
                st.success("Dimension added.")
                st.rerun()
            else:
                st.error("Dimension name already exists or the weight is invalid.")

# ------------------------------------------------------------------
# Dimension workspace
# ------------------------------------------------------------------
dimensions = MPIConfig.get_all_dimensions()
if not dimensions:
    st.info("No dimensions configured yet. Use ＋ Add Dimension to begin.")
    st.stop()

labels = [f"{i + 1}. {d['name']}  ·  {float(d['weight']):.3f}" for i, d in enumerate(dimensions)]
tabs = st.tabs(labels)

for tab, dimension in zip(tabs, dimensions):
    with tab:
        indicators = dimension.get("indicators", [])
        indicator_total = sum(float(i.get("weight", 0)) for i in indicators)
        dim_weight = float(dimension.get("weight", 0))

        # Header row
        h1, h2, h3, h4 = st.columns([3.4, 1.2, 1.4, 1.0])
        h1.markdown(f"### {dimension['name']}")
        h2.metric("Weight", f"{dim_weight:.3f}")
        h3.metric("Indicators", len(indicators))
        h4.metric("Ind. total", f"{indicator_total:.3f}")

        # Edit/delete controls are hidden in compact popovers.
        edit_col, delete_col, add_col = st.columns([1, 1, 1])
        with edit_col:
            with st.popover("Edit Dimension", use_container_width=True):
                with st.form(f"edit_dimension_{dimension['id']}"):
                    new_name = st.text_input("Dimension Name", value=dimension["name"])
                    if MPIConfig.is_equal_weighting():
                        st.caption("Weight is controlled automatically by Equal weighting.")
                        new_weight = dim_weight
                    else:
                        new_weight = st.number_input("Dimension Weight", 0.0, 1.0, dim_weight, 0.001, format="%.3f")
                    save = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                    if save:
                        if MPIConfig.update_dimension(dimension["id"], new_name, new_weight):
                            st.success("Dimension updated.")
                            st.rerun()
                        else:
                            st.error("Could not update the dimension. Check the name and weight.")
        with delete_col:
            if st.button("Delete", key=f"delete_dimension_{dimension['id']}", use_container_width=True):
                MPIConfig.delete_dimension(dimension["id"])
                st.rerun()
        with add_col:
            with st.popover("＋ Indicator", use_container_width=True):
                if dataset is None:
                    st.warning("Load a dataset before adding indicators.")
                else:
                    valid_variables = []
                    for column in dataset.columns:
                        values = dataset[column].dropna()
                        numeric = values.apply(lambda x: float(x) if str(x).strip() in {"0", "1", "0.0", "1.0"} else x)
                        try:
                            unique = set(numeric.astype(float).unique())
                        except Exception:
                            continue
                        if unique and unique.issubset({0.0, 1.0}):
                            valid_variables.append(str(column))
                    with st.form(f"add_indicator_{dimension['id']}", clear_on_submit=True):
                        indicator_name = st.text_input("Indicator Name", placeholder="e.g. School Attendance")
                        definition = st.text_area("Indicator Definition", placeholder="Define the indicator and deprivation condition.", height=90)
                        variable = st.selectbox("Dataset Variable", valid_variables) if valid_variables else None
                        if MPIConfig.is_equal_weighting():
                            st.caption("Weight will be balanced automatically within this dimension.")
                            indicator_weight = 0.0
                        else:
                            indicator_weight = st.number_input("Indicator Weight", 0.0, 1.0, 0.167, 0.001, format="%.3f")
                        add = st.form_submit_button("Add Indicator", type="primary", use_container_width=True)
                        if add:
                            if not valid_variables:
                                st.error("No valid 0/1 deprivation variable was found in the dataset.")
                            elif not indicator_name.strip():
                                st.error("Enter an indicator name.")
                            else:
                                ok = MPIConfig.add_indicator(
                                    dimension["id"],
                                    indicator_name,
                                    variable,
                                    indicator_weight,
                                    definition,
                                )
                                if ok:
                                    st.success("Indicator added.")
                                    st.rerun()
                                else:
                                    st.error("Indicator name or variable already exists in this dimension.")

        st.divider()

        if not indicators:
            st.caption("No indicators configured in this dimension.")
            continue

        # Compact indicator list. Editing is inside popovers so the page does not become a long form.
        for indicator in indicators:
            row1, row2, row3, row4 = st.columns([2.6, 3.2, 1.0, 1.0], gap="small")
            with row1:
                st.markdown(f"**{indicator['name']}**")
                st.caption(indicator.get("definition") or "No definition provided")
            with row2:
                st.caption(f"Variable: `{indicator.get('variable', '')}`")
            with row3:
                st.metric("Weight", f"{float(indicator.get('weight', 0)):.3f}")
            with row4:
                with st.popover("Edit", use_container_width=True):
                    with st.form(f"edit_indicator_{indicator['id']}"):
                        new_name = st.text_input("Indicator Name", value=indicator["name"])
                        new_definition = st.text_area("Indicator Definition", value=indicator.get("definition", ""), height=90)
                        columns = [str(c) for c in dataset.columns] if dataset is not None else [indicator.get("variable", "")]
                        current_var = indicator.get("variable", "")
                        if current_var not in columns:
                            columns.append(current_var)
                        new_variable = st.selectbox("Dataset Variable", columns, index=columns.index(current_var))
                        if MPIConfig.is_equal_weighting():
                            st.caption("Weight is automatically balanced.")
                            new_weight = float(indicator.get("weight", 0))
                        else:
                            new_weight = st.number_input("Indicator Weight", 0.0, 1.0, float(indicator.get("weight", 0)), 0.001, format="%.3f")
                        save = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                        if save:
                            ok = MPIConfig.update_indicator(
                                dimension["id"], indicator["id"], new_name, new_variable, new_weight, new_definition
                            )
                            if ok:
                                st.success("Indicator updated.")
                                st.rerun()
                            else:
                                st.error("Could not update the indicator. Check its name, variable and weight.")
            st.divider()

st.caption("Tip: use the dimension tabs and Edit popovers to keep the configuration page compact. Changes are saved immediately after each form submission.")
