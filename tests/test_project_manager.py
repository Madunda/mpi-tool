"""Automated tests for .nmpi project persistence."""

import pytest

from core.project_manager import NMPProjectManager


def test_nmpi_round_trip(mpi_config, sample_df):
    payload = NMPProjectManager.build_project_bytes(
        config=mpi_config,
        dataset=sample_df,
        dataset_name="test_dataset.csv",
    )
    loaded = NMPProjectManager.load_project_bytes(payload)
    assert loaded["config"]["project_name"] == "Test MPI Project"
    assert loaded["dataset"] is not None
    assert loaded["dataset"].shape == sample_df.shape
    assert loaded["metadata"]["configuration_hash"]
    assert loaded["metadata"]["dataset_hash"]


def test_inspect_nmpi_without_loading_dataset(mpi_config, sample_df):
    payload = NMPProjectManager.build_project_bytes(mpi_config, sample_df)
    inspected = NMPProjectManager.inspect_project_bytes(payload)
    assert inspected["dataset_included"] is True
    assert "project.json" in inspected["files"]
    assert "metadata.json" in inspected["files"]


def test_invalid_project_is_rejected():
    with pytest.raises(ValueError, match="valid .nmpi"):
        NMPProjectManager.load_project_bytes(b"not-a-project")


def test_invalid_config_is_rejected():
    with pytest.raises(ValueError, match="missing"):
        NMPProjectManager.validate_config({})