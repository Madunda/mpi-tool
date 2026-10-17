import streamlit as st
import pandas as pd

from core.mpi_config import MPIConfig


def _get_valid_indicator_variables(df):
    """
    Return dataset variables that are valid MPI
    deprivation indicators.

    A valid deprivation variable must contain only:

        0
        1
        Missing values

    The variable name itself is converted to string
    so mixed-type dataframe column names do not cause
    sorting errors.
    """

    valid = []

    for column in df.columns:

        series = df[column]

        # Remove missing values
        non_missing = series.dropna()

        # Empty/all-missing variables are not valid
        if len(non_missing) == 0:
            continue

        # Convert values to numeric where possible
        numeric_values = pd.to_numeric(
            non_missing,
            errors="coerce"
        )

        # If any value cannot be converted to numeric,
        # this is not a valid 0/1 deprivation indicator.
        if numeric_values.isna().any():
            continue

        unique_values = set(
            numeric_values.unique()
        )

        # Valid deprivation indicator:
        # only 0 and/or 1
        if unique_values.issubset({0, 1}):

            valid.append(str(column))

    return sorted(valid)


def show_indicator_form(dimension):

    st.subheader("Add Indicator")
    st.caption("Define the indicator first, then link it to the deprivation variable and weight it.")

    # ==========================================================
    # CHECK DATASET
    # ==========================================================

    if st.session_state.get("dataset") is None:

        st.warning(
            "Please load a dataset before adding indicators."
        )

        return

    df = st.session_state.dataset

    # ==========================================================
    # FIND VALID DEPRIVATION VARIABLES
    # ==========================================================

    indicator_variables = _get_valid_indicator_variables(df)

    if len(indicator_variables) == 0:

        st.warning(
            "No valid deprivation indicator variables were found. "
            "Variables must contain only 0, 1, and missing values."
        )

        return

    # ==========================================================
    # INDICATOR FORM
    # ==========================================================

    with st.form(
        f"indicator_form_{dimension['id']}",
        clear_on_submit=True
    ):

        c1, c2 = st.columns([1.25, 1])
        with c1:
            indicator_name = st.text_input(
                "Indicator Name",
                placeholder="e.g. Years of Schooling",
                help="A short, clear name used in tables and charts.",
            )
        with c2:
            variable = st.selectbox(
                "Dataset Variable",
                options=indicator_variables,
            )

        indicator_definition = st.text_area(
            "Indicator Definition",
            placeholder="State what the indicator measures and the deprivation rule.",
            height=75,
            help="Keep the methodological definition concise and reproducible.",
        )

        is_equal = MPIConfig.is_equal_weighting()

        if is_equal:
            st.caption(
                "Weight will be split equally across this "
                "dimension's indicators once this is added."
            )
            indicator_weight = 0.0
        else:
            indicator_weight = st.number_input(
                "Indicator Weight",
                min_value=0.0,
                max_value=1.0,
                value=0.167,
                step=0.001,
                format="%.3f"
            )

        submitted = st.form_submit_button(
            "Add Indicator", type="primary", use_container_width=True
        )

        # ======================================================
        # SUBMIT
        # ======================================================

        if submitted:

            name = indicator_name.strip()

            if not name:

                st.error(
                    "Please enter an indicator name."
                )

                return

            # --------------------------------------------------
            # Add indicator to MPI configuration
            # --------------------------------------------------

            success = MPIConfig.add_indicator(

                dimension_id=dimension["id"],

                name=name,
                definition=indicator_definition.strip(),
                variable=variable,

                weight=indicator_weight

            )

            if success:

                st.success(
                    "Indicator added successfully."
                )

                st.rerun()

            else:

                st.error(
                    "Indicator name or dataset variable "
                    "already exists in this dimension."
                )


__all__ = [
    "show_indicator_form"
]