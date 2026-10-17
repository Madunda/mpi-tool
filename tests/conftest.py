"""Pytest fixtures for NMPI Automation Tool."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

try:
    from core.mpi_config import MPIConfig
except ModuleNotFoundError:
    import types

    class MPIConfig:
        pass

    fallback = types.ModuleType("core.mpi_config")
    fallback.MPIConfig = MPIConfig
    sys.modules["core.mpi_config"] = fallback


@pytest.fixture
def mpi_config(monkeypatch):

    config = {
        "project_name": "Test MPI Project",
        "analysis_unit": "Household",
        "poverty_cutoff": 0.333,
        "weight_method": "Equal",
        "dimensions": [
            {
                "id": "d1",
                "name": "Education",
                "weight": 0.5,
                "indicators": [
                    {
                        "id": "i1",
                        "name": "School Attendance",
                        "variable": "school_attendance",
                        "weight": 0.5,
                    }
                ],
            },
            {
                "id": "d2",
                "name": "Health",
                "weight": 0.5,
                "indicators": [
                    {
                        "id": "i2",
                        "name": "Nutrition",
                        "variable": "nutrition",
                        "weight": 0.5,
                    }
                ],
            },
        ],
    }

    monkeypatch.setattr(MPIConfig, "get_all_dimensions", staticmethod(lambda: config["dimensions"]), raising=False)
    monkeypatch.setattr(MPIConfig, "get", staticmethod(lambda: config), raising=False)
    return config


@pytest.fixture
def sample_df():
    import pandas as pd

    return pd.DataFrame(
        {
            "school_attendance": [1, 0, 1, 0],
            "nutrition": [1, 1, 0, 0],
            "hhweight": [1.0, 2.0, 1.0, 2.0],
            "sex": ["Male", "Female", "Male", "Female"],
        }
    )