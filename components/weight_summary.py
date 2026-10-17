import streamlit as st

from core.mpi_config import MPIConfig


def show_weight_summary():
    st.subheader("Weight Summary")

    total = MPIConfig.total_weight()
    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric("Total Weight", f"{total:.3f}")

    with col2:
        if MPIConfig.weights_are_valid():
            st.success("Dimension weights are valid.")
        else:
            st.warning("The total dimension weight must equal 1.000.")


__all__ = ["show_weight_summary"]