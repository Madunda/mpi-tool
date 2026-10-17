"""Metadata and reproducibility utilities for NMPI Automation Tool."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import numpy as np
import pandas as pd


class MetadataManager:
    """Create deterministic metadata and reproducibility records."""

    TOOL_NAME = "NMPI Automation Tool"
    TOOL_VERSION = "1.0.0"
    METADATA_VERSION = "1.0"

    @staticmethod
    def utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def new_run_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def json_safe(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): MetadataManager.json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [MetadataManager.json_safe(v) for v in value]
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            return float(value)
        if isinstance(value, (np.bool_,)):
            return bool(value)
        if isinstance(value, (pd.Timestamp,)):
            return value.isoformat()
        if isinstance(value, (datetime,)):
            return value.isoformat()
        if pd.isna(value) if not isinstance(value, (dict, list, tuple, set)) else False:
            return None
        return value

    @classmethod
    def canonical_json(cls, value: Any) -> str:
        safe = cls.json_safe(value)
        return json.dumps(safe, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)

    @classmethod
    def sha256_text(cls, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    def hash_config(cls, config: Dict[str, Any]) -> str:
        if not isinstance(config, dict):
            raise TypeError("Configuration must be a dictionary.")
        return cls.sha256_text(cls.canonical_json(config))

    @classmethod
    def hash_dataframe(cls, df: pd.DataFrame) -> str:
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Dataset must be a pandas DataFrame.")

        hasher = hashlib.sha256()
        hasher.update(str(df.shape).encode("utf-8"))
        hasher.update(cls.canonical_json([str(c) for c in df.columns]).encode("utf-8"))
        hasher.update(cls.canonical_json([str(dtype) for dtype in df.dtypes]).encode("utf-8"))

        try:
            row_hash = pd.util.hash_pandas_object(df, index=True, categorize=True)
            hasher.update(row_hash.to_numpy(dtype=np.uint64, copy=False).tobytes())
        except Exception:
            # Fallback is deliberately deterministic for unusual object columns.
            csv_bytes = df.to_csv(index=True).encode("utf-8")
            hasher.update(csv_bytes)

        return hasher.hexdigest()

    @classmethod
    def dataset_metadata(cls, df: Optional[pd.DataFrame]) -> Dict[str, Any]:
        if df is None:
            return {
                "dataset_present": False,
                "dataset_hash": None,
                "rows": 0,
                "columns": 0,
                "missing_cells": 0,
                "column_names": [],
                "dtypes": {},
            }

        if not isinstance(df, pd.DataFrame):
            raise TypeError("Dataset must be a pandas DataFrame.")

        return {
            "dataset_present": True,
            "dataset_hash": cls.hash_dataframe(df),
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "missing_cells": int(df.isna().sum().sum()),
            "column_names": [str(c) for c in df.columns],
            "dtypes": {str(c): str(dtype) for c, dtype in df.dtypes.items()},
        }

    @classmethod
    def package_versions(cls, packages: Optional[Iterable[str]] = None) -> Dict[str, str]:
        names = list(packages or ["numpy", "pandas", "streamlit", "openpyxl"])
        versions: Dict[str, str] = {}
        for package in names:
            try:
                versions[package] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                versions[package] = "not-installed"
        return versions

    @classmethod
    def file_hash(cls, path: Path) -> Optional[str]:
        path = Path(path)
        if not path.exists() or not path.is_file():
            return None
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def source_hashes(cls, paths: Optional[Iterable[str | Path]] = None) -> Dict[str, Optional[str]]:
        if paths is None:
            return {}
        return {str(Path(path)): cls.file_hash(Path(path)) for path in paths}

    @classmethod
    def build_analysis_metadata(
        cls,
        config: Dict[str, Any],
        df: Optional[pd.DataFrame],
        *,
        cutoff: float,
        missing_method: str,
        weight_variable: Optional[str],
        run_id: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        source_files: Optional[Iterable[str | Path]] = None,
    ) -> Dict[str, Any]:
        dataset_info = cls.dataset_metadata(df)
        now = cls.utc_now()
        return {
            "metadata_version": cls.METADATA_VERSION,
            "tool_name": cls.TOOL_NAME,
            "tool_version": cls.TOOL_VERSION,
            "run_id": run_id or cls.new_run_id(),
            "analysis_started_at": started_at or now,
            "analysis_completed_at": completed_at or now,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "system": platform.system(),
            "machine": platform.machine(),
            "package_versions": cls.package_versions(),
            "project_name": config.get("project_name", "New MPI Project"),
            "analysis_unit": config.get("analysis_unit", "Household"),
            "poverty_cutoff": float(cutoff),
            "missing_method": missing_method,
            "weight_variable": weight_variable,
            "configuration_hash": cls.hash_config(config),
            **dataset_info,
            "source_file_hashes": cls.source_hashes(source_files),
            "methodology": {
                "framework": "Alkire-Foster",
                "identification_rule": "c_i >= k",
                "mpi_formula": "M0 = H * A",
                "indicator_contribution": "weighted censored deprivation / total weighted censored deprivation",
                "dimension_contribution": "sum of indicator contributions within dimension",
            },
        }

    @classmethod
    def to_dataframe(cls, metadata: Dict[str, Any]) -> pd.DataFrame:
        rows = []

        def flatten(prefix: str, value: Any) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    flatten(f"{prefix}.{key}" if prefix else str(key), item)
            elif isinstance(value, list):
                rows.append({"Property": prefix, "Value": json.dumps(cls.json_safe(value), ensure_ascii=False)})
            else:
                rows.append({"Property": prefix, "Value": cls.json_safe(value)})

        flatten("", metadata)
        return pd.DataFrame(rows)


__all__ = ["MetadataManager"]