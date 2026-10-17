import streamlit as st

from core.mpi_config import MPIConfig


def show_dimension_form():
    """Render compact MPI weighting controls and the add-dimension form."""
    config = MPIConfig.get()
    current_method = config.get("weight_method", "Equal")

    st.subheader("Weighting & Add Dimension")

    c1, c2 = st.columns([1.1, 2.2])
    with c1:
        selected_method = st.radio(
            "Weighting Method",
            ["Equal", "Custom"],
            index=0 if current_method == "Equal" else 1,
            horizontal=True,
            help="Equal distributes weights automatically. Custom lets you enter them manually.",
        )
    with c2:
        if selected_method == "Equal":
            st.caption("Equal weighting automatically rebalances dimensions and their indicators while preserving the exact total of 1.000.")
        else:
            st.caption("Custom weighting: dimension weights must sum to 1.000 and each dimension's indicator weights must equal its dimension weight.")

    if selected_method != current_method:
        MPIConfig.update_project_settings(weight_method=selected_method)
        if selected_method == "Equal":
            MPIConfig.equalize_dimension_weights()
        st.rerun()

    with st.form("add_dimension_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([2.5, 1, 1])
        with c1:
            dimension_name = st.text_input("Dimension Name", placeholder="e.g. Education")
        with c2:
            if selected_method == "Custom":
                dimension_weight = st.number_input("Weight", 0.0, 1.0, 0.333, 0.001, format="%.3f")
            else:
                dimension_weight = 0.0
                st.text_input("Weight", value="Automatic", disabled=True)
        with c3:
            st.write("")
            st.write("")
            submitted = st.form_submit_button("Add Dimension", type="primary", use_container_width=True)

        if submitted:
            name = dimension_name.strip()
            if not name:
                st.error("Enter a dimension name.")
            elif MPIConfig.add_dimension(name, dimension_weight):
                st.success("Dimension added.")
                st.rerun()
            else:
                st.error("A dimension with this name already exists.")


__all__ = ["show_dimension_form"]
