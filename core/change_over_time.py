"""Change-over-time analysis for two MPI survey periods."""

from __future__ import annotations

from contextlib import contextmanager
import numpy as np
import pandas as pd
import streamlit as st

from core.analysis_engine import AnalysisEngine
from core.project_manager import NMPProjectManager


class ChangeOverTimeEngine:
    """Run comparable AF-MPI analysis for two periods."""

    @staticmethod
    def config_signature(config: dict) -> tuple:
        """Create an order-independent MPI definition signature.

        Internal UUIDs are deliberately ignored. Dimension and indicator order
        is also ignored so projects with the same substantive definition do
        not fail comparison merely because they were created in a different
        order.
        """
        dimensions = []
        for dimension in config.get("dimensions", []):
            indicators = []
            for indicator in dimension.get("indicators", []):
                indicators.append(
                    (
                        str(indicator.get("name", "")).strip().casefold(),
                        str(indicator.get("definition", "")).strip().casefold(),
                        str(indicator.get("variable", "")).strip().casefold(),
                        round(float(indicator.get("weight", 0)), 6),
                    )
                )
            indicators.sort()
            dimensions.append(
                (
                    str(dimension.get("name", "")).strip().casefold(),
                    round(float(dimension.get("weight", 0)), 6),
                    tuple(indicators),
                )
            )
        return tuple(sorted(dimensions))

    @classmethod
    def validate_same_definition(cls, config_a: dict, config_b: dict) -> None:
        cutoff_a = float(config_a.get("poverty_cutoff", np.nan))
        cutoff_b = float(config_b.get("poverty_cutoff", np.nan))
        if not np.isclose(cutoff_a, cutoff_b, atol=1e-9, rtol=0):
            raise ValueError(
                f"The MPI poverty cut-offs differ ({cutoff_a:.3f} vs {cutoff_b:.3f})."
            )

        if cls.config_signature(config_a) != cls.config_signature(config_b):
            raise ValueError(
                "The two periods do not have the same MPI definition "
                "(dimensions, indicators, variables, definitions or weights)."
            )

    @staticmethod
    def load_period(file_bytes: bytes) -> dict:
        return NMPProjectManager.load_project_bytes(file_bytes)

    @staticmethod
    def _weight_variable(period: dict) -> str | None:
        """Resolve the survey weight without asking the COT user again.

        Priority is explicit period metadata, then persisted MPI
        configuration, then project metadata.
        """
        value = (
            period.get("weight_variable")
            or period.get("config", {}).get("survey_weight_variable")
            or period.get("metadata", {}).get("weight_variable")
        )
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    @classmethod
    def _validated_weight_variable(cls, period: dict) -> str | None:
        dataset = period.get("dataset")
        weight_variable = cls._weight_variable(period)

        if weight_variable is None:
            return None

        if not isinstance(dataset, pd.DataFrame):
            raise ValueError("A dataset is required before a survey weight can be used.")

        if weight_variable not in dataset.columns:
            raise ValueError(
                f"Survey-weight variable '{weight_variable}' is configured for "
                f"{period.get('year', 'this period')} but is not present in the dataset."
            )

        weights = pd.to_numeric(dataset[weight_variable], errors="coerce")
        if weights.notna().sum() == 0:
            raise ValueError(
                f"Survey-weight variable '{weight_variable}' contains no numeric values."
            )
        if (weights.dropna() < 0).any():
            raise ValueError(
                f"Survey-weight variable '{weight_variable}' contains negative values."
            )

        return weight_variable

    @staticmethod
    def _missing_method(period: dict) -> str:
        return (
            period.get("missing_method")
            or period.get("config", {}).get("missing_method")
            or "strict"
        )

    @staticmethod
    @contextmanager
    def _config_context(config: dict):
        """Temporarily expose a period configuration to AnalysisEngine."""
        old = st.session_state.get("mpi_config")
        st.session_state["mpi_config"] = config
        try:
            yield
        finally:
            if old is None:
                st.session_state.pop("mpi_config", None)
            else:
                st.session_state["mpi_config"] = old

    @classmethod
    def run_period(cls, period: dict) -> dict:
        dataset = period.get("dataset")
        config = period.get("config") or {}
        if not isinstance(dataset, pd.DataFrame) or dataset.empty:
            raise ValueError("Each period must contain a non-empty dataset.")

        weight_variable = cls._validated_weight_variable(period)
        missing_method = cls._missing_method(period)
        cutoff = float(config.get("poverty_cutoff", 0.333))

        with cls._config_context(config):
            result = AnalysisEngine.run(
                dataset,
                missing_method=missing_method,
                cutoff=cutoff,
                weight_variable=weight_variable,
            )
        return result

    @classmethod
    def compare(cls, first_period: dict, second_period: dict) -> dict:
        if not first_period or not second_period:
            raise ValueError("Both periods are required.")

        cls.validate_same_definition(
            first_period["config"],
            second_period["config"],
        )

        year_a = str(first_period.get("year", "")).strip()
        year_b = str(second_period.get("year", "")).strip()
        if not year_a or not year_b:
            raise ValueError("Both survey years must be provided.")
        if year_a == year_b:
            raise ValueError("The two survey years must be different.")

        first_result = cls.run_period(first_period)
        second_result = cls.run_period(second_period)

        overall = pd.DataFrame(
            {
                "Year": [year_a, year_b],
                "H": [first_result["H"], second_result["H"]],
                "A": [first_result["A"], second_result["A"]],
                "M0": [first_result["M0"], second_result["M0"]],
                "Projected Population": [
                    first_result["weighted_population"],
                    second_result["weighted_population"],
                ],
                "Projected Poor Population": [
                    first_result["weighted_poor_population"],
                    second_result["weighted_poor_population"],
                ],
            }
        )

        dim_a = first_result["dimension_contribution"][["Dimension", "Contribution (%)"]].rename(
            columns={"Contribution (%)": year_a}
        )
        dim_b = second_result["dimension_contribution"][["Dimension", "Contribution (%)"]].rename(
            columns={"Contribution (%)": year_b}
        )
        dimensions = dim_a.merge(dim_b, on="Dimension", how="outer").fillna(0)
        dimensions["Change (pp)"] = dimensions[year_b] - dimensions[year_a]

        ind_a = first_result["indicator_contribution"][
            ["Indicator", "Uncensored Headcount", "Censored Headcount", "Contribution (%)"]
        ].rename(
            columns={
                "Uncensored Headcount": f"Uncensored {year_a}",
                "Censored Headcount": f"Censored {year_a}",
                "Contribution (%)": f"Contribution {year_a}",
            }
        )
        ind_b = second_result["indicator_contribution"][
            ["Indicator", "Uncensored Headcount", "Censored Headcount", "Contribution (%)"]
        ].rename(
            columns={
                "Uncensored Headcount": f"Uncensored {year_b}",
                "Censored Headcount": f"Censored {year_b}",
                "Contribution (%)": f"Contribution {year_b}",
            }
        )
        indicators = ind_a.merge(ind_b, on="Indicator", how="outer")
        for column in indicators.columns:
            if column != "Indicator":
                indicators[column] = pd.to_numeric(
                    indicators[column], errors="coerce"
                ).fillna(0)

        indicators[f"Deprivation Change (pp)"] = (
            indicators[f"Uncensored {year_b}"]
            - indicators[f"Uncensored {year_a}"]
        ) * 100
        indicators[f"Contribution Change (pp)"] = (
            indicators[f"Contribution {year_b}"]
            - indicators[f"Contribution {year_a}"]
        )

        return {
            "years": (year_a, year_b),
            "first": first_result,
            "second": second_result,
            "overall": overall,
            "dimensions": dimensions,
            "indicators": indicators,
        }

    @classmethod
    def disaggregate(
        cls,
        first_period: dict,
        second_period: dict,
        group_variable: str,
    ) -> pd.DataFrame:
        cls.validate_same_definition(
            first_period["config"],
            second_period["config"],
        )

        output = []
        for period in (first_period, second_period):
            config = period["config"]
            weight_variable = cls._validated_weight_variable(period)
            missing_method = cls._missing_method(period)
            with cls._config_context(config):
                result = AnalysisEngine.disaggregate(
                    period["dataset"],
                    group_variable,
                    missing_method=missing_method,
                    cutoff=float(config.get("poverty_cutoff", 0.333)),
                    weight_variable=weight_variable,
                )
            result.insert(0, "Year", str(period["year"]))
            output.append(result)

        return pd.concat(output, ignore_index=True)


__all__ = ["ChangeOverTimeEngine"]
