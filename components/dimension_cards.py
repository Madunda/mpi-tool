import streamlit as st

from core.mpi_config import MPIConfig
from components.indicator_form import show_indicator_form
from components.indicator_cards import show_indicator_cards


def show_dimension_cards():
    """Render compact dimension cards and on-demand edit sections."""
    dimensions = MPIConfig.get_all_dimensions()
    st.subheader(f"Configured Dimensions ({len(dimensions)})")

    total_weight = MPIConfig.total_weight()
    if MPIConfig.weights_are_valid(tolerance=1e-9):
        st.success(f"Dimension weights: {total_weight:.3f} / 1.000 ✓")
    else:
        st.warning(f"Dimension weights: {total_weight:.3f} / 1.000 — adjustment required")

    if not dimensions:
        st.info("No dimensions have been added yet.")
        return

    for number, dimension in enumerate(dimensions, start=1):
        indicators = dimension.get("indicators", [])
        title = f"{number}. {dimension['name']}  ·  {float(dimension['weight']):.3f}  ·  {len(indicators)} indicators"

        with st.expander(title, expanded=False):
            top_left, top_right = st.columns([4, 2])
            with top_left:
                st.caption("Dimension weight")
                st.write(f"**{float(dimension['weight']):.3f}**")
            with top_right:
                if st.button("Delete Dimension", key=f"delete_dimension_{dimension['id']}", use_container_width=True):
                    MPIConfig.delete_dimension(dimension["id"])
                    st.rerun()

            with st.expander("Edit Dimension", expanded=False):
                with st.form(f"edit_dimension_{dimension['id']}"):
                    c1, c2 = st.columns([2.5, 1])
                    with c1:
                        new_name = st.text_input("Dimension Name", value=dimension["name"])
                    with c2:
                        new_weight = st.number_input(
                            "Weight",
                            min_value=0.0,
                            max_value=1.0,
                            value=float(dimension["weight"]),
                            step=0.001,
                            format="%.3f",
                        )
                    save = st.form_submit_button("Save Dimension", type="primary", use_container_width=True)
                    if save:
                        ok = MPIConfig.update_dimension(dimension["id"], new_name.strip(), new_weight)
                        if ok:
                            st.success("Dimension updated.")
                            st.rerun()
                        st.error("Could not update the dimension. Check the name and weight.")

            st.divider()
            show_indicator_cards(dimension)
            st.divider()
            show_indicator_form(dimension)


__all__ = ["show_dimension_cards"]
