"""Automated tests for core MPI calculations."""

import numpy as np
import pandas as pd
import pytest

from core.analysis_engine import AnalysisEngine


def test_weight_validation_passes(mpi_config):
    assert AnalysisEngine.validate_indicator_weights() is True


def test_weight_validation_rejects_dimension_total_below_one(mpi_config):
    mpi_config["dimensions"][1]["weight"] = 0.49
    with pytest.raises(ValueError, match="Dimension weights must sum"):
        AnalysisEngine.validate_indicator_weights()


def test_weight_validation_requires_indicator_total_to_match_dimension(mpi_config):
    mpi_config["dimensions"][0]["indicators"][0]["weight"] = 0.4
    with pytest.raises(ValueError, match="must sum to the Dimension Weight"):
        AnalysisEngine.validate_indicator_weights()


def test_deprivation_score_strict(mpi_config, sample_df):
    score = AnalysisEngine.calculate_deprivation_score(sample_df, "strict")
    expected = pd.Series([1.0, 0.5, 0.5, 0.0])
    pd.testing.assert_series_equal(score.reset_index(drop=True), expected, check_names=False)


def test_weighted_h_a_m0(mpi_config, sample_df):
    result = AnalysisEngine.run(
        sample_df,
        missing_method="strict",
        cutoff=0.5,
        weight_variable="hhweight",
    )
    assert np.isclose(result["H"], 4 / 6)
    assert np.isclose(result["A"], 0.625)
    assert np.isclose(result["M0"], 0.4166666666666667)
    assert result["metadata"]["run_id"]
    assert result["metadata"]["dataset_hash"]
    assert result["metadata"]["configuration_hash"]


def test_contributions_sum_to_100_percent(mpi_config, sample_df):
    result = AnalysisEngine.run(
        sample_df,
        cutoff=0.5,
        weight_variable="hhweight",
    )
    dim = result["dimension_contribution"]
    ind = result["indicator_contribution"]
    assert np.isclose(dim["Contribution (%)"].sum(), 100.0)
    assert np.isclose(ind["Contribution (%)"].sum(), 100.0)


def test_disaggregation_returns_groups(mpi_config, sample_df):
    result = AnalysisEngine.disaggregate(
        sample_df,
        group_variable="sex",
        cutoff=0.5,
        weight_variable="hhweight",
    )
    assert set(result["Group"]) == {"Male", "Female"}
    assert {"H", "A", "M0", "Weighted Population"}.issubset(result.columns)


def test_invalid_deprivation_value_is_rejected(mpi_config, sample_df):
    bad = sample_df.copy()
    bad.loc[0, "nutrition"] = 2
    with pytest.raises(ValueError, match="Invalid deprivation values"):
        AnalysisEngine.validate_deprivation_values(bad)


def test_negative_survey_weight_is_rejected(mpi_config, sample_df):
    bad = sample_df.copy()
    bad.loc[0, "hhweight"] = -1
    with pytest.raises(ValueError, match="negative values"):
        AnalysisEngine.get_survey_weights(bad, "hhweight")