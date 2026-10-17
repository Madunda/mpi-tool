"""
NMPI Automation Tool
Project Manager

Handles saving and opening portable .nmpi project files.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Any

import pandas as pd


class NMPProjectManager:
    """
    Manage portable NMPI .nmpi project files.

    A .nmpi file is a ZIP archive containing:

        project.json
        metadata.json
        dataset.csv              optional
        README.txt

    Analysis results are intentionally not stored because they
    should be regenerated from the configuration and dataset.
    """

    FORMAT_NAME = "NMPI Automation Project"
    FORMAT_VERSION = "1.0"

    # ------------------------------------------------------
    # BASIC HELPERS
    # ------------------------------------------------------

    @staticmethod
    def _json_safe(value: Any) -> Any:

        if isinstance(value, dict):
            return {
                str(key): NMPProjectManager._json_safe(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                NMPProjectManager._json_safe(item)
                for item in value
            ]

        if isinstance(value, pd.Timestamp):
            return value.isoformat()

        try:
            if pd.isna(value):
                return None
        except Exception:
            pass

        if hasattr(value, "item"):
            try:
                return value.item()
            except Exception:
                pass

        return value

    @classmethod
    def _canonical_json(cls, value: Any) -> str:

        safe_value = cls._json_safe(value)

        return json.dumps(
            safe_value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )

    @classmethod
    def _hash_text(cls, text: str) -> str:

        return hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()

    @classmethod
    def hash_config(cls, config: dict) -> str:

        return cls._hash_text(
            cls._canonical_json(config)
        )

    @classmethod
    def hash_dataframe(
        cls,
        df: pd.DataFrame,
    ) -> str:

        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                "Dataset must be a pandas DataFrame."
            )

        hasher = hashlib.sha256()

        hasher.update(
            str(df.shape).encode("utf-8")
        )

        hasher.update(
            cls._canonical_json(
                [str(column) for column in df.columns]
            ).encode("utf-8")
        )

        hasher.update(
            cls._canonical_json(
                [str(dtype) for dtype in df.dtypes]
            ).encode("utf-8")
        )

        try:

            row_hash = pd.util.hash_pandas_object(
                df,
                index=True,
                categorize=True,
            )

            hasher.update(
                row_hash.to_numpy(
                    dtype="uint64",
                    copy=False,
                ).tobytes()
            )

        except Exception:

            hasher.update(
                df.to_csv(
                    index=True
                ).encode("utf-8")
            )

        return hasher.hexdigest()

    # ------------------------------------------------------
    # CONFIGURATION VALIDATION
    # ------------------------------------------------------

    @classmethod
    def validate_config(
        cls,
        config: dict,
    ) -> bool:

        if not isinstance(config, dict):
            raise TypeError(
                "Project configuration must be a dictionary."
            )

        required = [
            "project_name",
            "analysis_unit",
            "poverty_cutoff",
            "dimensions",
        ]

        missing = [
            key
            for key in required
            if key not in config
        ]

        if missing:

            raise ValueError(
                "The project configuration is missing: "
                + ", ".join(missing)
            )

        try:

            cutoff = float(
                config["poverty_cutoff"]
            )

        except Exception as error:

            raise ValueError(
                "Poverty cut-off must be numeric."
            ) from error

        if not 0 <= cutoff <= 1:

            raise ValueError(
                "Poverty cut-off must be between 0 and 1."
            )

        dimensions = config["dimensions"]

        if not isinstance(dimensions, list):

            raise ValueError(
                "Project dimensions must be stored as a list."
            )

        # --------------------------------------------------
        # Dimension weights
        # --------------------------------------------------

        dimension_weight_total = 0.0

        for dimension in dimensions:

            if not isinstance(dimension, dict):

                raise ValueError(
                    "Each dimension must be a dictionary."
                )

            if "name" not in dimension:
                raise ValueError(
                    "Every dimension must have a name."
                )

            if "weight" not in dimension:
                raise ValueError(
                    f"Dimension '{dimension['name']}' "
                    "is missing its weight."
                )

            try:

                dimension_weight = float(
                    dimension["weight"]
                )

            except Exception as error:

                raise ValueError(
                    f"Invalid weight for dimension "
                    f"'{dimension['name']}'."
                ) from error

            if dimension_weight < 0:

                raise ValueError(
                    f"Dimension '{dimension['name']}' "
                    "cannot have a negative weight."
                )

            dimension_weight_total += (
                dimension_weight
            )

            indicators = dimension.get(
                "indicators",
                [],
            )

            if not isinstance(indicators, list):

                raise ValueError(
                    f"Indicators for dimension "
                    f"'{dimension['name']}' must be a list."
                )

            # ----------------------------------------------
            # Indicator weights
            # ----------------------------------------------

            indicator_total = 0.0

            for indicator in indicators:

                if not isinstance(
                    indicator,
                    dict,
                ):

                    raise ValueError(
                        f"Invalid indicator configuration "
                        f"in dimension '{dimension['name']}'."
                    )

                if "name" not in indicator:
                    raise ValueError(
                        f"An indicator in dimension "
                        f"'{dimension['name']}' is missing a name."
                    )

                if "weight" not in indicator:
                    raise ValueError(
                        f"Indicator '{indicator['name']}' "
                        "is missing its weight."
                    )

                try:

                    indicator_weight = float(
                        indicator["weight"]
                    )

                except Exception as error:

                    raise ValueError(
                        f"Invalid weight for indicator "
                        f"'{indicator['name']}'."
                    ) from error

                if indicator_weight < 0:

                    raise ValueError(
                        f"Indicator '{indicator['name']}' "
                        "cannot have a negative weight."
                    )

                indicator_total += (
                    indicator_weight
                )

            # ----------------------------------------------
            # Indicator total must equal dimension weight
            # ----------------------------------------------

            if indicators:

                if abs(
                    indicator_total
                    - dimension_weight
                ) > 1e-9:

                    raise ValueError(
                        f"Indicator weights for dimension "
                        f"'{dimension['name']}' must sum to "
                        f"the dimension weight "
                        f"{dimension_weight:.3f}. "
                        f"Current total is "
                        f"{indicator_total:.3f}."
                    )

        # --------------------------------------------------
        # Dimension total must be exactly 1
        # --------------------------------------------------

        if abs(
            dimension_weight_total - 1.0
        ) > 1e-9:

            raise ValueError(
                "Dimension weights must sum to exactly "
                f"1.000. Current total is "
                f"{dimension_weight_total:.3f}."
            )

        return True

    # ------------------------------------------------------
    # BUILD PROJECT
    # ------------------------------------------------------

    @classmethod
    def build_project_bytes(
        cls,
        config: dict,
        dataset: pd.DataFrame | None = None,
        dataset_name: str | None = None,
    ) -> bytes:

        if config is None:

            raise ValueError(
                "MPI configuration is required."
            )

        if not isinstance(config, dict):

            raise TypeError(
                "MPI configuration must be a dictionary."
            )

        cls.validate_config(config)

        if dataset is not None:

            if not isinstance(
                dataset,
                pd.DataFrame,
            ):

                raise TypeError(
                    "Dataset must be a pandas DataFrame."
                )

        created_at = datetime.now(
            timezone.utc
        ).isoformat()

        dataset_hash = (
            cls.hash_dataframe(dataset)
            if dataset is not None
            else None
        )

        configuration_hash = (
            cls.hash_config(config)
        )

        metadata = {

            "format": cls.FORMAT_NAME,

            "format_version":
                cls.FORMAT_VERSION,

            "created_at":
                created_at,

            "project_name":
                config.get(
                    "project_name",
                    "New MPI Project",
                ),

            "analysis_unit":
                config.get(
                    "analysis_unit",
                    "Household",
                ),

            "weight_variable":
                config.get("survey_weight_variable"),

            "missing_method":
                config.get("missing_method", "strict"),

            "dataset_name":
                dataset_name
                or "dataset.csv",

            "dataset_included":
                dataset is not None,

            "dataset_hash":
                dataset_hash,

            "configuration_hash":
                configuration_hash,

            "dataset_rows":
                int(len(dataset))
                if dataset is not None
                else 0,

            "dataset_columns":
                int(len(dataset.columns))
                if dataset is not None
                else 0,

            # Preserve Stata variable/value labels so disaggregation
            # can display names such as Arusha instead of code 1.
            "variable_labels": (
                cls._json_safe(dataset.attrs.get("variable_labels", {}))
                if dataset is not None else {}
            ),
            "value_labels": (
                cls._json_safe(dataset.attrs.get("value_labels", {}))
                if dataset is not None else {}
            ),
        }

        project_json = {

            "metadata":
                metadata,

            "config":
                cls._json_safe(config),
        }

        output = io.BytesIO()

        with zipfile.ZipFile(
            output,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:

            archive.writestr(
                "project.json",
                json.dumps(
                    project_json,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                ),
            )

            archive.writestr(
                "metadata.json",
                json.dumps(
                    metadata,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                ),
            )

            if dataset is not None:

                archive.writestr(
                    "dataset.csv",
                    dataset.to_csv(
                        index=False
                    ),
                )

            readme = (
                "NMPI Automation Project\n"
                "========================\n\n"
                f"Format version: {cls.FORMAT_VERSION}\n"
                f"Project name: "
                f"{metadata['project_name']}\n"
                f"Created at: "
                f"{created_at}\n\n"
                "This project contains the MPI configuration "
                "and, when selected, the working dataset.\n\n"
                "Analysis results are intentionally not stored. "
                "They should be regenerated from the configuration "
                "and dataset after opening the project.\n"
            )

            archive.writestr(
                "README.txt",
                readme,
            )

        output.seek(0)

        return output.getvalue()

    # ------------------------------------------------------
    # INSPECT PROJECT
    # ------------------------------------------------------

    @classmethod
    def inspect_project_bytes(
        cls,
        file_bytes: bytes,
    ) -> dict:

        if not file_bytes:

            raise ValueError(
                "The .nmpi file is empty."
            )

        try:

            with zipfile.ZipFile(
                io.BytesIO(file_bytes),
                mode="r",
            ) as archive:

                names = archive.namelist()

                if "project.json" not in names:

                    raise ValueError(
                        "Invalid .nmpi project: "
                        "project.json is missing."
                    )

                project = json.loads(
                    archive.read(
                        "project.json"
                    ).decode("utf-8")
                )

                metadata = project.get(
                    "metadata",
                    {},
                )

                config = project.get(
                    "config"
                )

                if not isinstance(
                    config,
                    dict,
                ):

                    raise ValueError(
                        "Invalid .nmpi project: "
                        "configuration is missing."
                    )

                cls.validate_config(
                    config
                )

                return {

                    "metadata":
                        metadata,

                    "config":
                        config,

                    "dataset_included":
                        "dataset.csv" in names,

                    "files":
                        names,
                }

        except zipfile.BadZipFile as error:

            raise ValueError(
                "The selected file is not a valid .nmpi project."
            ) from error

        except json.JSONDecodeError as error:

            raise ValueError(
                "The .nmpi project contains "
                "invalid project metadata."
            ) from error

    # ------------------------------------------------------
    # LOAD PROJECT
    # ------------------------------------------------------

    @classmethod
    def load_project_bytes(
        cls,
        file_bytes: bytes,
    ) -> dict:

        if not file_bytes:

            raise ValueError(
                "The .nmpi file is empty."
            )

        try:

            with zipfile.ZipFile(
                io.BytesIO(file_bytes),
                mode="r",
            ) as archive:

                names = archive.namelist()

                if "project.json" not in names:

                    raise ValueError(
                        "Invalid .nmpi project: "
                        "project.json is missing."
                    )

                project = json.loads(
                    archive.read(
                        "project.json"
                    ).decode("utf-8")
                )

                config = project.get(
                    "config"
                )

                if not isinstance(
                    config,
                    dict,
                ):

                    raise ValueError(
                        "Invalid .nmpi project configuration."
                    )

                cls.validate_config(
                    config
                )

                dataset = None

                if "dataset.csv" in names:

                    dataset = pd.read_csv(
                        io.BytesIO(
                            archive.read(
                                "dataset.csv"
                            )
                        )
                    )

                metadata = project.get(
                    "metadata",
                    {},
                )

                if dataset is not None:
                    dataset.attrs["variable_labels"] = metadata.get(
                        "variable_labels", {}
                    )
                    dataset.attrs["value_labels"] = metadata.get(
                        "value_labels", {}
                    )

                # Backward-compatible fallback for projects created after
                # analysis settings were persisted in the configuration.
                if config.get("survey_weight_variable") is None:
                    config["survey_weight_variable"] = metadata.get(
                        "weight_variable"
                    )

                return {

                    "config":
                        config,

                    "dataset":
                        dataset,

                    "metadata":
                        metadata,

                    "files":
                        names,
                }

        except zipfile.BadZipFile as error:

            raise ValueError(
                "The selected file is not a valid .nmpi project."
            ) from error

        except json.JSONDecodeError as error:

            raise ValueError(
                "The .nmpi project contains "
                "invalid project metadata."
            ) from error


__all__ = [
    "NMPProjectManager",
]