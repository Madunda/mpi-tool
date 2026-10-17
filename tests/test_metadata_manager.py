"""Tests for metadata and reproducibility utilities."""

import pandas as pd

from core.metadata_manager import MetadataManager


def test_dataframe_hash_is_deterministic(sample_df):
    assert MetadataManager.hash_dataframe(sample_df) == MetadataManager.hash_dataframe(sample_df.copy())


def test_dataframe_hash_changes_when_data_changes(sample_df):
    original = MetadataManager.hash_dataframe(sample_df)
    changed = sample_df.copy()
    changed.loc[0, "nutrition"] = 0
    assert original != MetadataManager.hash_dataframe(changed)


def test_config_hash_is_deterministic(mpi_config):
    assert MetadataManager.hash_config(mpi_config) == MetadataManager.hash_config(mpi_config.copy())


def test_analysis_metadata_contains_reproducibility_fields(mpi_config, sample_df):
    metadata = MetadataManager.build_analysis_metadata(
        mpi_config,
        sample_df,
        cutoff=0.333,
        missing_method="strict",
        weight_variable="hhweight",
    )
    required = {
        "run_id",
        "configuration_hash",
        "dataset_hash",
        "python_version",
        "package_versions",
        "methodology",
        "analysis_started_at",
        "analysis_completed_at",
    }
    assert required.issubset(metadata.keys())
    assert metadata["rows"] == 4
    assert metadata["columns"] == 4


def test_metadata_to_dataframe(sample_df, mpi_config):
    metadata = MetadataManager.build_analysis_metadata(
        mpi_config,
        sample_df,
        cutoff=0.333,
        missing_method="strict",
        weight_variable="hhweight",
    )
    table = MetadataManager.to_dataframe(metadata)
    assert isinstance(table, pd.DataFrame)
    assert {"Property", "Value"}.issubset(table.columns)
    assert not table.empty