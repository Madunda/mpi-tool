import hashlib
import json

import pandas as pd
import streamlit as st


# ==========================================================
# NMPI PERFORMANCE ENGINE
# ==========================================================

class PerformanceManager:
    """
    Central performance and caching manager for NMPI.

    Main goals:

        1. Avoid unnecessary recalculation.
        2. Avoid unnecessary dataframe copying.
        3. Provide stable dataset fingerprints.
        4. Provide stable MPI configuration fingerprints.
        5. Track when analysis inputs change.
        6. Clear only the results that actually depend
           on changed inputs.
    """

    # ======================================================
    # SESSION STATE INITIALIZATION
    # ======================================================

    @staticmethod
    def initialize():

        defaults = {

            "dataset": None,

            "dataset_name": None,

            "dataset_fingerprint": None,

            "mpi_analysis_result": None,

            "mpi_analysis_fingerprint": None,

            "mpi_disaggregation_result": None,

            "mpi_disaggregation_fingerprint": None,

            "mpi_dimension_contribution": None,

            "mpi_indicator_contribution": None,

        }

        for key, value in defaults.items():

            if key not in st.session_state:

                st.session_state[key] = value

    # ======================================================
    # DATASET FINGERPRINT
    # ======================================================

    @staticmethod
    def dataset_fingerprint(df):

        if df is None:

            return None

        if not isinstance(
            df,
            pd.DataFrame
        ):

            raise TypeError(
                "Dataset must be a pandas DataFrame."
            )

        if df.empty:

            return "EMPTY_DATASET"

        hasher = hashlib.sha256()

        # --------------------------------------------------
        # Shape
        # --------------------------------------------------

        hasher.update(
            str(df.shape).encode("utf-8")
        )

        # --------------------------------------------------
        # Column names
        # --------------------------------------------------

        hasher.update(
            json.dumps(
                [
                    str(column)
                    for column in df.columns
                ],
                ensure_ascii=False,
            ).encode("utf-8")
        )

        # --------------------------------------------------
        # Column dtypes
        # --------------------------------------------------

        hasher.update(
            json.dumps(
                [
                    str(dtype)
                    for dtype in df.dtypes
                ]
            ).encode("utf-8")
        )

        # --------------------------------------------------
        # Data hash
        # --------------------------------------------------

        try:

            data_hash = pd.util.hash_pandas_object(
                df,
                index=True,
            ).values.tobytes()

            hasher.update(
                data_hash
            )

        except Exception:

            hasher.update(
                df.to_csv(
                    index=True
                ).encode("utf-8")
            )

        return hasher.hexdigest()

    # ======================================================
    # CONFIGURATION FINGERPRINT
    # ======================================================

    @staticmethod
    def configuration_fingerprint(
        config
    ):

        if config is None:

            return None

        payload = json.dumps(
            config,
            sort_keys=True,
            default=str,
            ensure_ascii=False,
        )

        return hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()

    # ======================================================
    # ANALYSIS FINGERPRINT
    # ======================================================

    @staticmethod
    def analysis_fingerprint(
        dataset_fingerprint,
        configuration_fingerprint,
        cutoff,
        missing_method,
        weight_variable,
    ):

        payload = {

            "dataset":
                dataset_fingerprint,

            "configuration":
                configuration_fingerprint,

            "cutoff":
                float(cutoff),

            "missing_method":
                missing_method,

            "weight_variable":
                weight_variable,

        }

        serialized = json.dumps(
            payload,
            sort_keys=True,
            default=str,
        )

        return hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()

    # ======================================================
    # DISAGGREGATION FINGERPRINT
    # ======================================================

    @staticmethod
    def disaggregation_fingerprint(
        analysis_fingerprint,
        group_variable,
    ):

        payload = {

            "analysis":
                analysis_fingerprint,

            "group":
                group_variable,

        }

        serialized = json.dumps(
            payload,
            sort_keys=True,
            default=str,
        )

        return hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()

    # ======================================================
    # CHECK ANALYSIS CACHE
    # ======================================================

    @staticmethod
    def has_current_analysis(
        fingerprint
    ):

        stored = (
            st.session_state.get(
                "mpi_analysis_fingerprint"
            )
        )

        result = (
            st.session_state.get(
                "mpi_analysis_result"
            )
        )

        return (
            result is not None
            and stored == fingerprint
        )

    # ======================================================
    # SAVE ANALYSIS RESULT
    # ======================================================

    @staticmethod
    def save_analysis(
        result,
        fingerprint,
    ):

        st.session_state[
            "mpi_analysis_result"
        ] = result

        st.session_state[
            "mpi_analysis_fingerprint"
        ] = fingerprint

        st.session_state[
            "mpi_dimension_contribution"
        ] = result.get(
            "dimension_contribution"
        )

        st.session_state[
            "mpi_indicator_contribution"
        ] = result.get(
            "indicator_contribution"
        )

        # Disaggregation belongs to
        # a specific analysis.
        PerformanceManager.clear_disaggregation()

    # ======================================================
    # CLEAR ANALYSIS
    # ======================================================

    @staticmethod
    def clear_analysis():

        st.session_state[
            "mpi_analysis_result"
        ] = None

        st.session_state[
            "mpi_analysis_fingerprint"
        ] = None

        st.session_state[
            "mpi_dimension_contribution"
        ] = None

        st.session_state[
            "mpi_indicator_contribution"
        ] = None

        PerformanceManager.clear_disaggregation()

    # ======================================================
    # CLEAR DISAGGREGATION
    # ======================================================

    @staticmethod
    def clear_disaggregation():

        st.session_state[
            "mpi_disaggregation_result"
        ] = None

        st.session_state[
            "mpi_disaggregation_fingerprint"
        ] = None

    # ======================================================
    # SET DATASET
    # ======================================================

    @staticmethod
    def set_dataset(
        df,
        dataset_name=None,
    ):

        fingerprint = (
            PerformanceManager.dataset_fingerprint(
                df
            )
        )

        old_fingerprint = (
            st.session_state.get(
                "dataset_fingerprint"
            )
        )

        st.session_state[
            "dataset"
        ] = df

        st.session_state[
            "dataset_name"
        ] = dataset_name

        st.session_state[
            "dataset_fingerprint"
        ] = fingerprint

        # --------------------------------------------------
        # Only invalidate analysis if dataset changed.
        # --------------------------------------------------

        if (
            old_fingerprint
            != fingerprint
        ):

            PerformanceManager.clear_analysis()

        return fingerprint

    # ======================================================
    # DATASET STATUS
    # ======================================================

    @staticmethod
    def dataset_changed(
        df
    ):

        current = (
            PerformanceManager.dataset_fingerprint(
                df
            )
        )

        stored = (
            st.session_state.get(
                "dataset_fingerprint"
            )
        )

        return current != stored


# ==========================================================
# CACHE HELPERS
# ==========================================================

@st.cache_data(
    show_spinner=False,
    max_entries=10,
)
def cached_numeric_series(
    series,
):

    return pd.to_numeric(
        series,
        errors="coerce",
    )


@st.cache_data(
    show_spinner=False,
    max_entries=10,
)
def cached_dataframe_head(
    df,
    rows=100,
):

    return df.head(
        rows
    ).copy()


__all__ = [
    "PerformanceManager",
    "cached_numeric_series",
    "cached_dataframe_head",
]