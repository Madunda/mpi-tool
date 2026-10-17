import numpy as np
import pandas as pd

from core.mpi_config import MPIConfig
from core.metadata_manager import MetadataManager


class AnalysisEngine:
    """
    Alkire-Foster MPI Analysis Engine.

    Supports:
        - MPI indicator configuration
        - Indicator and dimension weight validation
        - Deprivation score
        - Poverty identification
        - Survey-weighted H, A and M0
        - Dimension contribution
        - Indicator contribution
        - Disaggregation
        - AF audit
    """

    # ==========================================================
    # DATASET VALIDATION
    # ==========================================================

    @staticmethod
    def validate_dataset(df):
        if df is None:
            raise ValueError("No dataset has been loaded.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("Dataset must be a pandas DataFrame.")

        if df.empty:
            raise ValueError("The loaded dataset is empty.")

        return True

    # ==========================================================
    # INDICATOR MAP
    # ==========================================================

    @staticmethod
    def get_indicator_map():
        indicator_map = []

        for dimension in MPIConfig.get_all_dimensions():
            dimension_weight = float(dimension["weight"])

            for indicator in dimension.get("indicators", []):
                indicator_map.append(
                    {
                        "dimension_id": dimension["id"],
                        "dimension": dimension["name"],
                        "dimension_weight": dimension_weight,
                        "indicator_id": indicator["id"],
                        "indicator": indicator["name"],
                        "variable": indicator["variable"],
                        "weight": float(indicator["weight"]),
                    }
                )

        return indicator_map

    # ==========================================================
    # WEIGHT VALIDATION
    # ==========================================================

    @staticmethod
    def validate_indicator_weights(tolerance=1e-9):
        indicator_map = AnalysisEngine.get_indicator_map()

        if not indicator_map:
            raise ValueError("No MPI indicators have been configured.")

        dimensions = MPIConfig.get_all_dimensions()

        if not dimensions:
            raise ValueError("No MPI dimensions have been configured.")

        dimension_weight_total = sum(
            float(d.get("weight", 0.0)) for d in dimensions
        )

        if not np.isclose(
            dimension_weight_total, 1.0, atol=tolerance
        ):
            raise ValueError(
                "Dimension weights must sum exactly to 1.000 "
                f"within tolerance. Current total = "
                f"{dimension_weight_total:.6f}."
            )

        for dimension in dimensions:
            dimension_name = dimension["name"]
            dimension_weight = float(dimension["weight"])
            indicators = dimension.get("indicators", [])

            if not indicators:
                raise ValueError(
                    f"Dimension '{dimension_name}' has no indicators."
                )

            indicator_total = sum(
                float(i.get("weight", 0.0)) for i in indicators
            )

            if any(float(i.get("weight", 0.0)) < 0 for i in indicators):
                raise ValueError(
                    f"Negative indicator weight found in "
                    f"dimension '{dimension_name}'."
                )

            if not np.isclose(
                indicator_total,
                dimension_weight,
                atol=tolerance
            ):
                raise ValueError(
                    f"Indicators in dimension '{dimension_name}' "
                    f"must sum to the Dimension Weight "
                    f"{dimension_weight:.3f}. "
                    f"Current indicator total = "
                    f"{indicator_total:.6f}."
                )

        total_indicator_weight = sum(
            float(i["weight"]) for i in indicator_map
        )

        if not np.isclose(
            total_indicator_weight, 1.0, atol=tolerance
        ):
            raise ValueError(
                "Total indicator weights must equal 1.000. "
                f"Current total = {total_indicator_weight:.6f}."
            )

        return True

    # ==========================================================
    # VALIDATE VARIABLES
    # ==========================================================

    @staticmethod
    def validate_indicator_variables(df):
        AnalysisEngine.validate_dataset(df)

        missing = [
            item["variable"]
            for item in AnalysisEngine.get_indicator_map()
            if item["variable"] not in df.columns
        ]

        if missing:
            missing = list(dict.fromkeys(missing))
            raise ValueError(
                "The following deprivation variables are missing "
                "from the dataset: " + ", ".join(missing)
            )

        return True

    # ==========================================================
    # VALIDATE DEPRIVATION VALUES
    # ==========================================================

    @staticmethod
    def validate_deprivation_values(df):
        AnalysisEngine.validate_dataset(df)
        AnalysisEngine.validate_indicator_variables(df)

        invalid = {}

        for item in AnalysisEngine.get_indicator_map():
            variable = item["variable"]

            values = pd.to_numeric(
                df[variable],
                errors="coerce"
            )

            conversion_failed = (
                values.isna() & df[variable].notna()
            )

            invalid_values = values[
                values.notna() & ~values.isin([0, 1])
            ]

            if conversion_failed.any() or len(invalid_values) > 0:
                invalid[variable] = True

        if invalid:
            raise ValueError(
                "Invalid deprivation values found in: "
                + ", ".join(invalid.keys())
                + ". Expected only 0, 1 or missing."
            )

        return True

    # ==========================================================
    # DEPRIVATION MATRIX
    # ==========================================================

    @staticmethod
    def build_deprivation_matrix(df):
        AnalysisEngine.validate_deprivation_values(df)

        matrix = pd.DataFrame(index=df.index)

        for item in AnalysisEngine.get_indicator_map():
            matrix[item["variable"]] = pd.to_numeric(
                df[item["variable"]],
                errors="coerce"
            )

        return matrix

    # ==========================================================
    # WEIGHT VECTOR
    # ==========================================================

    @staticmethod
    def build_weight_vector():
        weights = {}

        for item in AnalysisEngine.get_indicator_map():
            weights[item["variable"]] = item["weight"]

        return pd.Series(weights, dtype=float)

    # ==========================================================
    # DEPRIVATION SCORE
    # ==========================================================

    @staticmethod
    def calculate_deprivation_score(df, missing_method="strict"):
        if missing_method not in {"strict", "normalize", "zero"}:
            raise ValueError(
                "missing_method must be 'strict', 'normalize' or 'zero'."
            )

        deprivation = AnalysisEngine.build_deprivation_matrix(df)
        weights = AnalysisEngine.build_weight_vector()

        weighted = deprivation.multiply(weights, axis="columns")

        if missing_method == "strict":
            return weighted.sum(axis=1, skipna=False)

        if missing_method == "zero":
            return weighted.fillna(0).sum(axis=1)

        observed_weight = (
            deprivation.notna()
            .multiply(weights, axis="columns")
            .sum(axis=1)
        )

        weighted_sum = weighted.sum(axis=1, skipna=True)

        score = pd.Series(np.nan, index=df.index, dtype=float)
        valid = observed_weight > 0
        score.loc[valid] = (
            weighted_sum.loc[valid] / observed_weight.loc[valid]
        )

        return score

    # ==========================================================
    # POVERTY IDENTIFICATION
    # ==========================================================

    @staticmethod
    def identify_poor(score, cutoff=None):
        if cutoff is None:
            cutoff = float(MPIConfig.get()["poverty_cutoff"])

        cutoff = float(cutoff)

        if not 0 <= cutoff <= 1:
            raise ValueError(
                "Poverty cutoff must be between 0 and 1."
            )

        poor = pd.Series(np.nan, index=score.index, dtype=float)
        valid = score.notna()
        poor.loc[valid] = (score.loc[valid] >= cutoff).astype(float)

        return poor

    # ==========================================================
    # SURVEY WEIGHTS
    # ==========================================================

    @staticmethod
    def get_survey_weights(df, weight_variable=None):
        AnalysisEngine.validate_dataset(df)

        if weight_variable is None:
            return pd.Series(1.0, index=df.index, dtype=float)

        if weight_variable not in df.columns:
            raise ValueError(
                f"Weight variable '{weight_variable}' "
                "was not found in the dataset."
            )

        weights = pd.to_numeric(
            df[weight_variable],
            errors="coerce"
        )

        if (weights < 0).any():
            raise ValueError(
                f"Survey weight '{weight_variable}' "
                "contains negative values."
            )

        return weights

    # ==========================================================
    # H, A, M0
    # ==========================================================

    @staticmethod
    def calculate_headcount(poor, survey_weights=None):
        if survey_weights is None:
            survey_weights = pd.Series(
                1.0, index=poor.index, dtype=float
            )

        valid = (
            poor.notna()
            & survey_weights.notna()
            & (survey_weights >= 0)
        )

        if not valid.any():
            return np.nan

        weights = survey_weights.loc[valid]
        poor_valid = poor.loc[valid]

        denominator = weights.sum()

        if denominator <= 0:
            return np.nan

        numerator = (weights * (poor_valid == 1)).sum()

        return float(numerator / denominator)

    @staticmethod
    def calculate_intensity(score, poor, survey_weights=None):
        if survey_weights is None:
            survey_weights = pd.Series(
                1.0, index=score.index, dtype=float
            )

        poor_mask = (
            (poor == 1)
            & score.notna()
            & survey_weights.notna()
            & (survey_weights >= 0)
        )

        if not poor_mask.any():
            return np.nan

        weights = survey_weights.loc[poor_mask]
        scores = score.loc[poor_mask]

        denominator = weights.sum()

        if denominator <= 0:
            return np.nan

        return float((weights * scores).sum() / denominator)

    @staticmethod
    def calculate_mpi(headcount, intensity):
        if pd.isna(headcount) or pd.isna(intensity):
            return np.nan

        return float(headcount * intensity)

    @staticmethod
    def calculate_weighted_population(survey_weights):
        if survey_weights is None:
            return np.nan

        valid = survey_weights.notna() & (survey_weights >= 0)

        if not valid.any():
            return np.nan

        return float(survey_weights.loc[valid].sum())

    @staticmethod
    def calculate_weighted_poor_population(poor, survey_weights):
        valid = (
            poor.notna()
            & survey_weights.notna()
            & (survey_weights >= 0)
        )

        if not valid.any():
            return np.nan

        return float(
            (
                survey_weights.loc[valid]
                * (poor.loc[valid] == 1)
            ).sum()
        )

    # ==========================================================
    # CONTRIBUTION BY INDICATOR
    # ==========================================================

    @staticmethod
    def calculate_indicator_contribution(
        df,
        poor,
        survey_weights=None
    ):
        """
        Indicator contribution to overall MPI.

        For each indicator:

            C_j = weighted poor deprivation of indicator j
                  / weighted total deprivation score

        Contribution percentage is C_j * 100.

        Only multidimensionally poor observations are included,
        following the censored deprivation matrix used by AF.
        """

        AnalysisEngine.validate_dataset(df)

        if survey_weights is None:
            survey_weights = pd.Series(
                1.0, index=df.index, dtype=float
            )

        deprivation = AnalysisEngine.build_deprivation_matrix(df)
        indicator_map = AnalysisEngine.get_indicator_map()

        valid_weight = (
            survey_weights.notna()
            & (survey_weights >= 0)
        )

        poor_mask = (
            poor.eq(1)
            & valid_weight
        )

        if not poor_mask.any():
            return pd.DataFrame(
                columns=[
                    "Dimension",
                    "Indicator",
                    "Variable",
                    "Weight",
                    "Uncensored Headcount",
                    "Censored Headcount",
                    "Weighted Deprivation",
                    "Contribution",
                    "Contribution (%)",
                ]
            )

        total_censored_deprivation = 0.0
        rows = []

        for item in indicator_map:
            variable = item["variable"]
            values = deprivation[variable].copy()

            censored = values.where(poor.eq(1), 0.0)

            valid_indicator = values.notna() & valid_weight
            denominator = survey_weights.where(valid_indicator, 0.0).sum()
            uncensored_headcount = (
                survey_weights.where(valid_indicator & values.eq(1), 0.0).sum()
                / denominator
                if denominator > 0 else np.nan
            )

            censored_valid = valid_indicator & poor.eq(1)
            censored_denominator = survey_weights.where(
                poor_mask & values.notna(), 0.0
            ).sum()
            censored_headcount = (
                survey_weights.where(censored_valid & values.eq(1), 0.0).sum()
                / censored_denominator
                if censored_denominator > 0 else np.nan
            )

            contribution_value = (
                survey_weights
                .where(poor_mask, 0.0)
                .mul(censored.fillna(0.0))
                .sum()
                * item["weight"]
            )

            total_censored_deprivation += contribution_value

            rows.append(
                {
                    "Dimension": item["dimension"],
                    "Indicator": item["indicator"],
                    "Variable": variable,
                    "Weight": item["weight"],
                    "Uncensored Headcount": float(uncensored_headcount)
                    if not pd.isna(uncensored_headcount) else np.nan,
                    "Censored Headcount": float(censored_headcount)
                    if not pd.isna(censored_headcount) else np.nan,
                    "Weighted Deprivation": float(contribution_value),
                }
            )

        result = pd.DataFrame(rows)

        if total_censored_deprivation > 0:
            result["Contribution"] = (
                result["Weighted Deprivation"]
                / total_censored_deprivation
            )
            result["Contribution (%)"] = (
                result["Contribution"] * 100
            )
        else:
            result["Contribution"] = np.nan
            result["Contribution (%)"] = np.nan

        return result

    # ==========================================================
    # CONTRIBUTION BY DIMENSION
    # ==========================================================

    @staticmethod
    def calculate_dimension_contribution(
        df,
        poor,
        survey_weights=None
    ):
        """
        Calculate each dimension's contribution to overall MPI.

        Indicator contributions are first calculated, then summed
        within each dimension. This guarantees that dimension
        contribution is consistent with indicator contribution.
        """

        indicator_result = (
            AnalysisEngine.calculate_indicator_contribution(
                df=df,
                poor=poor,
                survey_weights=survey_weights,
            )
        )

        if indicator_result.empty:
            return pd.DataFrame(
                columns=[
                    "Dimension",
                    "Dimension Weight",
                    "Weighted Deprivation",
                    "Contribution",
                    "Contribution (%)",
                ]
            )

        dimensions = (
            indicator_result.groupby(
                "Dimension",
                dropna=False,
                as_index=False
            )
            .agg(
                {
                    "Weighted Deprivation": "sum"
                }
            )
        )

        dimension_lookup = {
            d["name"]: float(d["weight"])
            for d in MPIConfig.get_all_dimensions()
        }

        dimensions["Dimension Weight"] = (
            dimensions["Dimension"]
            .map(dimension_lookup)
        )

        total = dimensions["Weighted Deprivation"].sum()

        if total > 0:
            dimensions["Contribution"] = (
                dimensions["Weighted Deprivation"] / total
            )
            dimensions["Contribution (%)"] = (
                dimensions["Contribution"] * 100
            )
        else:
            dimensions["Contribution"] = np.nan
            dimensions["Contribution (%)"] = np.nan

        return dimensions[
            [
                "Dimension",
                "Dimension Weight",
                "Weighted Deprivation",
                "Contribution",
                "Contribution (%)",
            ]
        ]

    # ==========================================================
    # COMPLETE ANALYSIS
    # ==========================================================

    @staticmethod
    def run(
        df,
        missing_method="strict",
        cutoff=None,
        weight_variable=None
    ):
        AnalysisEngine.validate_dataset(df)
        AnalysisEngine.validate_indicator_variables(df)
        AnalysisEngine.validate_deprivation_values(df)
        AnalysisEngine.validate_indicator_weights()

        if cutoff is None:
            cutoff = float(MPIConfig.get()["poverty_cutoff"])

        cutoff = float(cutoff)

        score = AnalysisEngine.calculate_deprivation_score(
            df,
            missing_method=missing_method
        )

        poor = AnalysisEngine.identify_poor(
            score,
            cutoff
        )

        survey_weights = AnalysisEngine.get_survey_weights(
            df,
            weight_variable
        )

        weighted_population = (
            AnalysisEngine.calculate_weighted_population(
                survey_weights
            )
        )

        weighted_poor_population = (
            AnalysisEngine.calculate_weighted_poor_population(
                poor,
                survey_weights
            )
        )

        H = AnalysisEngine.calculate_headcount(
            poor,
            survey_weights
        )

        A = AnalysisEngine.calculate_intensity(
            score,
            poor,
            survey_weights
        )

        M0 = AnalysisEngine.calculate_mpi(H, A)

        dimension_contribution = (
            AnalysisEngine.calculate_dimension_contribution(
                df=df,
                poor=poor,
                survey_weights=survey_weights,
            )
        )

        indicator_contribution = (
            AnalysisEngine.calculate_indicator_contribution(
                df=df,
                poor=poor,
                survey_weights=survey_weights,
            )
        )

        results = df.copy()
        results["mpi_deprivation_score"] = score
        results["mpi_poor"] = poor
        results["mpi_weight"] = survey_weights

        metadata = MetadataManager.build_analysis_metadata(
            MPIConfig.get(),
            df,
            cutoff=cutoff,
            missing_method=missing_method,
            weight_variable=weight_variable,
        )

        return {
            "data": results,
            "deprivation_score": score,
            "poor": poor,
            "H": H,
            "A": A,
            "M0": M0,
            "metadata": metadata,
            "cutoff": cutoff,
            "weight_variable": weight_variable,
            "missing_method": missing_method,
            "weighted_population": weighted_population,
            "weighted_poor_population": weighted_poor_population,
            "dimension_contribution": dimension_contribution,
            "indicator_contribution": indicator_contribution,
        }

    # ==========================================================
    # AF AUDIT
    # ==========================================================

    @staticmethod
    def audit(df, result, weight_variable=None):
        AnalysisEngine.validate_dataset(df)

        audit_df = pd.DataFrame(index=df.index)
        audit_df["deprivation_score"] = result["deprivation_score"]
        audit_df["poor"] = result["poor"]

        if weight_variable is None:
            weight_variable = result.get("weight_variable")

        survey_weights = AnalysisEngine.get_survey_weights(
            df,
            weight_variable
        )

        audit_df["survey_weight"] = survey_weights
        audit_df["weighted_poor"] = (
            audit_df["survey_weight"] * audit_df["poor"]
        )
        audit_df["weighted_deprivation"] = (
            audit_df["survey_weight"]
            * audit_df["deprivation_score"]
        )

        return audit_df

    # ==========================================================
    # DISAGGREGATION
    # ==========================================================

    @staticmethod
    def _normalise_value_label_map(value_labels):
        """Return a robust string-keyed value-label mapping."""
        if not isinstance(value_labels, dict):
            return {}
        return {str(key).strip(): str(value).strip() for key, value in value_labels.items()}

    @staticmethod
    def _display_group_value(group_value, group_variable, df=None):
        """Prefer dataset metadata labels, then use safe common fallbacks."""
        if pd.isna(group_value):
            return "Missing"

        text = str(group_value).strip()

        # Stata value labels are preserved by DataLoader in DataFrame.attrs.
        # This is the authoritative source for coded geography/sex/residence
        # values and prevents gaps such as 20 -> 50 from becoming blanks.
        if isinstance(df, pd.DataFrame):
            metadata = df.attrs.get("value_labels", {})
            variable_labels = metadata.get(str(group_variable), {})
            label_map = AnalysisEngine._normalise_value_label_map(variable_labels)
            if text in label_map and label_map[text]:
                return label_map[text]

        variable = str(group_variable).strip().lower()
        mappings = {
            "sex": {"1": "Male", "2": "Female"},
            "gender": {"1": "Male", "2": "Female"},
            "urban_rural": {"1": "Urban", "2": "Rural"},
            "urbanrural": {"1": "Urban", "2": "Rural"},
            "residence": {"1": "Urban", "2": "Rural"},
            "residence_type": {"1": "Urban", "2": "Rural"},
            "location": {"1": "Urban", "2": "Rural"},
        }

        if variable in mappings and text in mappings[variable]:
            return mappings[variable][text]

        if ("sex" in variable or "gender" in variable) and text in {"1", "2"}:
            return {"1": "Male", "2": "Female"}[text]

        if any(term in variable for term in ("urban", "rural", "residence")) and text in {"1", "2"}:
            return {"1": "Urban", "2": "Rural"}[text]

        return text

    @staticmethod
    def disaggregate(
        df,
        group_variable,
        missing_method="strict",
        cutoff=None,
        weight_variable=None
    ):
        AnalysisEngine.validate_dataset(df)

        if group_variable not in df.columns:
            raise ValueError(
                f"Grouping variable '{group_variable}' "
                "was not found in the dataset."
            )

        score = AnalysisEngine.calculate_deprivation_score(
            df,
            missing_method=missing_method
        )

        poor = AnalysisEngine.identify_poor(
            score,
            cutoff
        )

        survey_weights = AnalysisEngine.get_survey_weights(
            df,
            weight_variable
        )

        temp = pd.DataFrame(
            {
                "group": df[group_variable],
                "score": score,
                "poor": poor,
                "weight": survey_weights,
            },
            index=df.index
        )

        rows = []

        for group_value, group_df in temp.groupby(
            "group",
            dropna=False
        ):
            valid = (
                group_df["score"].notna()
                & group_df["poor"].notna()
                & group_df["weight"].notna()
                & (group_df["weight"] >= 0)
            )

            group_valid = group_df.loc[valid]

            if group_valid.empty:
                continue

            weights = group_valid["weight"]
            scores = group_valid["score"]
            poor_values = group_valid["poor"]

            weighted_population = weights.sum()
            weighted_poor = (
                weights * (poor_values == 1)
            ).sum()

            H = (
                weighted_poor / weighted_population
                if weighted_population > 0
                else np.nan
            )

            poor_mask = poor_values == 1
            poor_weights = weights.loc[poor_mask]
            poor_scores = scores.loc[poor_mask]

            A = (
                (poor_weights * poor_scores).sum()
                / poor_weights.sum()
                if len(poor_weights) > 0
                and poor_weights.sum() > 0
                else np.nan
            )

            M0 = (
                H * A
                if not pd.isna(H) and not pd.isna(A)
                else np.nan
            )

            rows.append(
                {
                    "Group": AnalysisEngine._display_group_value(
                        group_value, group_variable, df
                    ),
                    "Observations": len(group_df),
                    "Projected Population": int(round(weighted_population)),
                    "Projected Poor Population": int(round(weighted_poor)),
                    "Weighted Population": float(weighted_population),
                    "H": H,
                    "A": A,
                    "M0": M0,
                }
            )

        return pd.DataFrame(rows)

    # ==========================================================
    # SUMMARY
    # ==========================================================

    @staticmethod
    def summary(result):
        return {
            "Headcount (H)": result.get("H"),
            "Intensity (A)": result.get("A"),
            "MPI (M0)": result.get("M0"),
            "Poverty Cutoff": result.get("cutoff"),
            "Weight Variable": (
                result.get("weight_variable")
                if result.get("weight_variable") is not None
                else "None"
            ),
            "Weighted Population": result.get(
                "weighted_population"
            ),
            "Weighted Poor Population": result.get(
                "weighted_poor_population"
            ),
            "Missing Method": result.get(
                "missing_method"
            ),
        }


__all__ = ["AnalysisEngine"]