import numpy as np
import pandas as pd

from core.mpi_config import MPIConfig


class AnalysisEngine:
    """
    Core engine for Alkire-Foster MPI analysis.

    Input:
        Dataset containing already-created deprivation variables.

    Expected deprivation values:
        1     = deprived
        0     = non-deprived
        NaN   = missing

    The engine does NOT create deprivation rules.
    Those variables are assumed to have been prepared before
    the dataset is loaded into the MPI Tool.
    """

    # ==========================================================
    # LOAD CONFIGURATION
    # ==========================================================

    @staticmethod
    def get_indicators():

        return MPIConfig.get_all_indicators()

    # ==========================================================
    # VALIDATE DATASET
    # ==========================================================

    @staticmethod
    def validate_dataset(df):

        if df is None:

            raise ValueError(
                "No dataset has been loaded."
            )

        if not isinstance(df, pd.DataFrame):

            raise TypeError(
                "Dataset must be a pandas DataFrame."
            )

        if df.empty:

            raise ValueError(
                "The loaded dataset is empty."
            )

        return True

    # ==========================================================
    # VALIDATE INDICATOR VARIABLES
    # ==========================================================

    @staticmethod
    def validate_indicator_variables(df):

        AnalysisEngine.validate_dataset(df)

        indicators = MPIConfig.get_all_indicators()

        if len(indicators) == 0:

            raise ValueError(
                "No MPI indicators have been configured."
            )

        missing_variables = []

        invalid_variables = []

        for indicator in indicators:

            variable = indicator["variable"]

            if variable not in df.columns:

                missing_variables.append(
                    variable
                )

                continue

            series = pd.to_numeric(
                df[variable],
                errors="coerce"
            )

            non_missing = series.dropna()

            if len(non_missing) == 0:

                invalid_variables.append(
                    f"{variable}: all observations are missing"
                )

                continue

            values = set(
                non_missing.unique()
            )

            if not values.issubset({0, 1}):

                invalid_variables.append(
                    f"{variable}: contains values "
                    f"other than 0 and 1"
                )

        if missing_variables:

            raise ValueError(
                "The following indicator variables "
                "are missing from the dataset: "
                + ", ".join(missing_variables)
            )

        if invalid_variables:

            raise ValueError(
                "Invalid deprivation variables:\n"
                + "\n".join(invalid_variables)
            )

        return True

    # ==========================================================
    # BUILD DEPRIVATION MATRIX
    # ==========================================================

    @staticmethod
    def build_deprivation_matrix(df):

        AnalysisEngine.validate_indicator_variables(
            df
        )

        indicators = MPIConfig.get_all_indicators()

        deprivation = pd.DataFrame(
            index=df.index
        )

        for indicator in indicators:

            variable = indicator["variable"]

            deprivation[
                indicator["indicator_id"]
            ] = pd.to_numeric(
                df[variable],
                errors="coerce"
            )

        return deprivation

    # ==========================================================
    # BUILD NAMED DEPRIVATION MATRIX
    # ==========================================================

    @staticmethod
    def build_named_deprivation_matrix(df):

        AnalysisEngine.validate_indicator_variables(
            df
        )

        indicators = MPIConfig.get_all_indicators()

        deprivation = pd.DataFrame(
            index=df.index
        )

        for indicator in indicators:

            deprivation[
                indicator["indicator_name"]
            ] = pd.to_numeric(
                df[indicator["variable"]],
                errors="coerce"
            )

        return deprivation

    # ==========================================================
    # MISSING OBSERVATIONS
    # ==========================================================

    @staticmethod
    def missing_summary(deprivation):

        summary = []

        for column in deprivation.columns:

            missing = int(
                deprivation[column].isna().sum()
            )

            total = len(
                deprivation[column]
            )

            percentage = (
                missing / total * 100
                if total > 0
                else 0
            )

            summary.append({

                "indicator": column,

                "missing": missing,

                "total": total,

                "missing_percent": percentage

            })

        return pd.DataFrame(summary)

    # ==========================================================
    # VALID OBSERVATION MASK
    # ==========================================================

    @staticmethod
    def valid_observation_mask(
        deprivation
    ):

        """
        An observation is valid when all configured
        deprivation indicators are observed.

        Missing observations are NOT silently converted
        to 0 or 1.
        """

        return ~deprivation.isna().any(
            axis=1
        )

    # ==========================================================
    # COMPLETE CASE MATRIX
    # ==========================================================

    @staticmethod
    def complete_deprivation_matrix(
        deprivation
    ):

        mask = AnalysisEngine.valid_observation_mask(
            deprivation
        )

        return deprivation.loc[
            mask
        ].copy()

    # ==========================================================
    # BASIC AF INPUT
    # ==========================================================

    @staticmethod
    def prepare_af_input(df):

        """
        Prepare the dataset required for the
        Alkire-Foster computation.

        Returns:
            {
                "deprivation": DataFrame,
                "valid_mask": Series,
                "missing_summary": DataFrame
            }
        """

        deprivation = (
            AnalysisEngine
            .build_named_deprivation_matrix(df)
        )

        valid_mask = (
            AnalysisEngine
            .valid_observation_mask(
                deprivation
            )
        )

        missing_summary = (
            AnalysisEngine
            .missing_summary(
                deprivation
            )
        )

        return {

            "deprivation": deprivation,

            "valid_mask": valid_mask,

            "missing_summary": missing_summary

        }

    # ==========================================================
    # ANALYSIS SUMMARY
    # ==========================================================

    @staticmethod
    def analysis_summary(df):

        AnalysisEngine.validate_dataset(
            df
        )

        indicators = MPIConfig.get_all_indicators()

        dimensions = MPIConfig.get_all_dimensions()

        deprivation = (
            AnalysisEngine
            .build_named_deprivation_matrix(df)
        )

        valid_mask = (
            AnalysisEngine
            .valid_observation_mask(
                deprivation
            )
        )

        return {

            "observations": len(df),

            "dimensions": len(dimensions),

            "indicators": len(indicators),

            "complete_observations": int(
                valid_mask.sum()
            ),

            "incomplete_observations": int(
                (~valid_mask).sum()
            ),

            "complete_percent": (
                valid_mask.mean() * 100
            ),

            "incomplete_percent": (
                (~valid_mask).mean() * 100
            )

        }