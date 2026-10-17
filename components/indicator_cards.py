import streamlit as st

from core.mpi_config import MPIConfig


def show_indicator_cards(dimension):
    """Show compact indicator summaries with on-demand editing."""
    indicators = dimension.get("indicators", [])
    st.subheader(f"Indicators ({len(indicators)})")

    if not indicators:
        st.info("No indicators have been added to this dimension yet.")
        return

    dataset = st.session_state.get("dataset")
    variables = list(dataset.columns) if dataset is not None else []

    for number, indicator in enumerate(indicators, start=1):
        definition = str(indicator.get("definition", "")).strip()
        title = f"{number}. {indicator['name']}  ·  {indicator['weight']:.3f}"

        with st.expander(title, expanded=False):
            summary_left, summary_right = st.columns([4, 2])
            with summary_left:
                st.caption("Definition")
                st.write(definition or "Not provided")
                st.caption("Dataset variable")
                st.code(indicator["variable"], language=None)
            with summary_right:
                st.metric("Weight", f"{float(indicator['weight']):.3f}")
                st.caption("Edit the indicator only when changes are required.")

            with st.form(f"edit_indicator_{indicator['id']}"):
                c1, c2 = st.columns([1.3, 1])
                with c1:
                    new_name = st.text_input("Indicator Name", value=indicator["name"])
                with c2:
                    current_variable = indicator.get("variable", "")
                    variable_index = variables.index(current_variable) if current_variable in variables else 0
                    new_variable = st.selectbox(
                        "Dataset Variable",
                        options=variables,
                        index=variable_index,
                    )

                new_definition = st.text_area(
                    "Indicator Definition",
                    value=definition,
                    height=80,
                )

                if MPIConfig.is_equal_weighting():
                    new_weight = float(indicator["weight"])
                    st.info(f"Equal weighting is active. Weight is managed automatically: **{new_weight:.3f}**")
                else:
                    new_weight = st.number_input(
                        "Indicator Weight",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(indicator["weight"]),
                        step=0.001,
                        format="%.3f",
                    )

                save_col, delete_col = st.columns([1, 1])
                with save_col:
                    save = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                with delete_col:
                    delete = st.form_submit_button("Delete Indicator", use_container_width=True)

                if save:
                    ok = MPIConfig.update_indicator(
                        dimension["id"],
                        indicator["id"],
                        new_name.strip(),
                        new_variable,
                        new_weight,
                        new_definition.strip(),
                    )
                    if ok:
                        st.success("Indicator updated.")
                        st.rerun()
                    st.error("Could not update the indicator. Check for duplicate names or variables.")

                if delete:
                    MPIConfig.delete_indicator(dimension["id"], indicator["id"])
                    st.rerun()


__all__ = ["show_indicator_cards"]
