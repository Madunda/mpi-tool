import streamlit as st

from core.mpi_config import MPIConfig


def show_project_settings():
    config = MPIConfig.get()

    st.subheader("Project Settings")

    config["project_name"] = st.text_input(
        "Project Name",
        value=config["project_name"],
    )

    config["analysis_unit"] = st.selectbox(
        "Analysis Unit",
        ["Household", "Individual"],
        index=0 if config["analysis_unit"] == "Household" else 1,
    )

    config["poverty_cutoff"] = st.number_input(
        "Poverty Cut-off (k)",
        min_value=0.00,
        max_value=1.00,
        value=float(config["poverty_cutoff"]),
        step=0.01,
        format="%.3f",
    )

    config["weight_method"] = st.selectbox(
        "Weighting Method",
        ["Equal", "Custom"],
        index=0 if config["weight_method"] == "Equal" else 1,
    )

    MPIConfig.save(config)
    st.success("Project settings saved successfully.")


__all__ = ["show_project_settings"]
