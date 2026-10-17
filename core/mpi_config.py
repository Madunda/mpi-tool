import uuid
import streamlit as st


class MPIConfig:
    """
    Central configuration manager for the MPI project.

    Configuration structure:

    Project
        ├── project_name
        ├── analysis_unit
        ├── poverty_cutoff
        └── weight_method

    Dimensions
        └── Dimension
              ├── id
              ├── name
              ├── weight
              └── indicators
                    ├── id
                    ├── name
                    ├── variable
                    └── weight

    IMPORTANT MPI WEIGHT RULE
    -------------------------
    1. All dimension weights must sum to 1.000.
    2. Indicator weights within each dimension must
       sum to the weight of that dimension.

    Example:

        Education = 0.333

            Schooling      = 0.1665
            Attendance     = 0.1665
            -------------------------
            Total          = 0.3330

    The indicator variable is already a deprivation variable
    prepared before loading the dataset.

    Expected indicator variable:

        0 = Not deprived
        1 = Deprived
        NaN = Missing
    """

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    @staticmethod
    def initialize():
        """
        Initialize MPI configuration in Streamlit session state.
        """

        if "mpi_config" not in st.session_state:

            st.session_state.mpi_config = {
                "project_name": "New MPI Project",
                "analysis_unit": "Household",
                "poverty_cutoff": 0.333,
                "weight_method": "Equal",
                "survey_weight_variable": None,
                "missing_method": "strict",
                "dimensions": [],
            }

        else:
            MPIConfig._ensure_structure()

    # ==========================================================
    # INTERNAL STRUCTURE VALIDATION
    # ==========================================================

    @staticmethod
    def _ensure_structure():
        """
        Ensure older session configurations contain
        all required fields.

        This helps prevent errors when the application
        is updated while Streamlit session state still
        contains an older configuration.
        """

        config = st.session_state.mpi_config

        config.setdefault(
            "survey_weight_variable",
            None,
        )

        for _dimension in config.get("dimensions", []):
            for _indicator in _dimension.get("indicators", []):
                _indicator.setdefault("definition", "")

        config.setdefault(
            "project_name",
            "New MPI Project"
        )

        config.setdefault(
            "analysis_unit",
            "Household"
        )

        config.setdefault(
            "poverty_cutoff",
            0.333
        )

        config.setdefault(
            "weight_method",
            "Equal"
        )

        config.setdefault(
            "dimensions",
            []
        )

        for dimension in config["dimensions"]:

            dimension.setdefault(
                "id",
                str(uuid.uuid4())
            )

            dimension.setdefault(
                "name",
                "Unnamed Dimension"
            )

            dimension.setdefault(
                "weight",
                0.0
            )

            dimension.setdefault(
                "indicators",
                []
            )

            for indicator in dimension["indicators"]:

                indicator.setdefault(
                    "id",
                    str(uuid.uuid4())
                )

                indicator.setdefault(
                    "name",
                    "Unnamed Indicator"
                )

                # New architecture uses one variable
                if "variable" not in indicator:

                    variables = indicator.get(
                        "variables",
                        []
                    )

                    if variables:
                        indicator["variable"] = (
                            variables[0]
                        )
                    else:
                        indicator["variable"] = ""

                # Keep backward compatibility
                indicator["variables"] = [
                    indicator["variable"]
                ] if indicator["variable"] else []

                indicator.setdefault(
                    "weight",
                    0.0
                )

        st.session_state.mpi_config = config

    # ==========================================================
    # GET CONFIGURATION
    # ==========================================================

    @staticmethod
    def get():
        """
        Return the complete MPI configuration.
        """

        MPIConfig.initialize()

        return st.session_state.mpi_config

    # ==========================================================
    # SAVE CONFIGURATION
    # ==========================================================

    @staticmethod
    def save(config):
        """
        Save MPI configuration to Streamlit session state.
        """

        st.session_state.mpi_config = config

        MPIConfig._ensure_structure()

    # ==========================================================
    # PROJECT SETTINGS
    # ==========================================================

    @staticmethod
    def update_project_settings(
        project_name=None,
        analysis_unit=None,
        poverty_cutoff=None,
        weight_method=None,
    ):
        """
        Update project-level MPI settings.
        """

        config = MPIConfig.get()

        if project_name is not None:

            config["project_name"] = (
                str(project_name).strip()
            )

        if analysis_unit is not None:

            config["analysis_unit"] = (
                str(analysis_unit).strip()
            )

        if poverty_cutoff is not None:

            config["poverty_cutoff"] = float(
                poverty_cutoff
            )

        if weight_method is not None:

            config["weight_method"] = (
                str(weight_method).strip()
            )

        MPIConfig.save(config)

    # ==========================================================
    # AUTO-BALANCE (EQUAL WEIGHTING)
    # ==========================================================

    @staticmethod
    def is_equal_weighting():
        """
        Return True when the project is using the "Equal"
        weighting method (weights are split automatically),
        and False when using "Custom" (manual weights).
        """

        config = MPIConfig.get()

        return str(
            config.get("weight_method", "Equal")
        ).strip() == "Equal"

    @staticmethod
    def _split_weight(total: float, count: int, decimals: int = 3) -> list[float]:
        """Split a total into count rounded weights whose displayed values
        still sum exactly to the requested total.

        The final component receives the rounding remainder. This avoids
        the common 0.333 x 3 = 0.999 problem and also handles odd counts
        such as five indicators cleanly.
        """
        if count <= 0:
            return []

        scale = 10 ** decimals
        total_units = int(round(float(total) * scale))
        base_units = total_units // count
        remainder = total_units - (base_units * count)

        values = [base_units / scale] * count
        for index in range(remainder):
            values[index] += 1 / scale

        return values

    @staticmethod
    def equalize_dimension_weights():
        """Automatically create exact three-decimal equal weights.

        Example with 3 dimensions:
            0.333, 0.333, 0.334 = 1.000

        Indicator weights are independently split within each dimension,
        and their rounded values sum exactly to that dimension's weight.
        """
        config = MPIConfig.get()
        dimensions = config.get("dimensions", [])
        n_dimensions = len(dimensions)

        if n_dimensions == 0:
            MPIConfig.save(config)
            return

        dimension_weights = MPIConfig._split_weight(1.0, n_dimensions, 3)

        for dimension, dimension_weight in zip(dimensions, dimension_weights):
            dimension["weight"] = float(dimension_weight)

            indicators = dimension.get("indicators", [])
            n_indicators = len(indicators)

            if n_indicators:
                indicator_weights = MPIConfig._split_weight(
                    dimension_weight, n_indicators, 3
                )
                for indicator, indicator_weight in zip(
                    indicators, indicator_weights
                ):
                    indicator["weight"] = float(indicator_weight)

        MPIConfig.save(config)

    @staticmethod
    def _auto_balance():
        """
        Called after every dimension/indicator add, edit, or
        delete. If the project is using "Equal" weighting, this
        silently re-splits all weights to stay balanced. Under
        "Custom" weighting, this does nothing — manual weights
        are left exactly as entered.
        """

        if MPIConfig.is_equal_weighting():
            MPIConfig.equalize_dimension_weights()

    # ==========================================================
    # ADD DIMENSION
    # ==========================================================

    @staticmethod
    def add_dimension(
        name,
        weight
    ):
        """
        Add a new MPI dimension.
        """

        config = MPIConfig.get()

        name = str(name).strip()
        weight = float(weight)

        if not name:
            return False

        if weight < 0 or weight > 1:
            return False

        # Prevent duplicate dimension names
        for dimension in config["dimensions"]:

            existing_name = str(
                dimension.get(
                    "name",
                    ""
                )
            ).strip().lower()

            if existing_name == name.lower():
                return False

        dimension = {
            "id": str(uuid.uuid4()),
            "name": name,
            "weight": weight,
            "indicators": [],
        }

        config["dimensions"].append(
            dimension
        )

        MPIConfig.save(config)
        MPIConfig._auto_balance()

        return True

    # ==========================================================
    # GET ALL DIMENSIONS
    # ==========================================================

    @staticmethod
    def get_all_dimensions():
        """
        Return all configured dimensions.
        """

        config = MPIConfig.get()

        return config.get(
            "dimensions",
            []
        )

    # ==========================================================
    # GET DIMENSION
    # ==========================================================

    @staticmethod
    def get_dimension(
        dimension_id
    ):
        """
        Return one dimension by ID.
        """

        for dimension in (
            MPIConfig.get_all_dimensions()
        ):

            if dimension.get("id") == dimension_id:

                return dimension

        return None

    # ==========================================================
    # DIMENSION COUNT
    # ==========================================================

    @staticmethod
    def total_dimension_count():

        return len(
            MPIConfig.get_all_dimensions()
        )

    # ==========================================================
    # UPDATE DIMENSION
    # ==========================================================

    @staticmethod
    def update_dimension(
        dimension_id,
        new_name,
        new_weight
    ):
        """
        Update an existing dimension.
        """

        config = MPIConfig.get()

        new_name = str(
            new_name
        ).strip()

        new_weight = float(
            new_weight
        )

        if not new_name:
            return False

        if new_weight < 0 or new_weight > 1:
            return False

        # Prevent duplicate names
        for dimension in config["dimensions"]:

            if dimension["id"] == dimension_id:
                continue

            if (
                dimension["name"]
                .strip()
                .lower()
                == new_name.lower()
            ):
                return False

        for dimension in config["dimensions"]:

            if dimension["id"] == dimension_id:

                dimension["name"] = new_name

                dimension["weight"] = (
                    new_weight
                )

                MPIConfig.save(config)
                MPIConfig._auto_balance()

                return True

        return False

    # ==========================================================
    # DELETE DIMENSION
    # ==========================================================

    @staticmethod
    def delete_dimension(
        dimension_id
    ):
        """
        Delete a dimension and all indicators
        belonging to that dimension.
        """

        config = MPIConfig.get()

        original_count = len(
            config["dimensions"]
        )

        config["dimensions"] = [
            dimension

            for dimension
            in config["dimensions"]

            if dimension.get("id")
            != dimension_id
        ]

        MPIConfig.save(config)
        MPIConfig._auto_balance()

        return (
            len(config["dimensions"])
            < original_count
        )

    # ==========================================================
    # CLEAR DIMENSIONS
    # ==========================================================

    @staticmethod
    def clear_dimensions():
        """
        Remove all dimensions and indicators.
        """

        config = MPIConfig.get()

        config["dimensions"] = []

        MPIConfig.save(config)

    # ==========================================================
    # ADD INDICATOR
    # ==========================================================

    @staticmethod
    def add_indicator(
        dimension_id,
        name,
        variable,
        weight,
        definition="",
    ):
        """
        Add one deprivation indicator to a dimension.

        The variable must already exist in the loaded dataset.

        Example:

            name:
                Improved Sanitation

            variable:
                hh_dep_toilet_sdg

            values:
                0 = Not deprived
                1 = Deprived
                NaN = Missing
        """

        config = MPIConfig.get()

        name = str(name).strip()
        definition = str(definition or "").strip()
        variable = str(variable).strip()
        weight = float(weight)

        if not name:
            return False

        if not variable:
            return False

        if weight < 0 or weight > 1:
            return False

        for dimension in config["dimensions"]:

            if dimension.get("id") != dimension_id:
                continue

            # Prevent duplicate indicator names
            for indicator in dimension["indicators"]:

                if (
                    indicator.get("name", "")
                    .strip()
                    .lower()
                    == name.lower()
                ):
                    return False

                # Prevent same deprivation variable
                # from being accidentally added twice
                if (
                    indicator.get("variable", "")
                    .strip()
                    .lower()
                    == variable.lower()
                ):
                    return False

            indicator = {
                "id": str(uuid.uuid4()),
                "name": name,
                "definition": definition,
                "variable": variable,
                "variables": [variable],
                "weight": weight,
            }

            dimension["indicators"].append(
                indicator
            )

            MPIConfig.save(config)
            MPIConfig._auto_balance()

            return True

        return False

    # ==========================================================
    # GET INDICATORS
    # ==========================================================

    @staticmethod
    def get_indicators(
        dimension_id
    ):
        """
        Return indicators belonging to one dimension.
        """

        dimension = MPIConfig.get_dimension(
            dimension_id
        )

        if dimension is None:
            return []

        return dimension.get(
            "indicators",
            []
        )

    # ==========================================================
    # GET ALL INDICATORS
    # ==========================================================

    @staticmethod
    def get_all_indicators():
        """
        Return all indicators across all dimensions.
        """

        indicators = []

        for dimension in (
            MPIConfig.get_all_dimensions()
        ):

            for indicator in dimension.get(
                "indicators",
                []
            ):

                item = dict(indicator)

                item["dimension_id"] = (
                    dimension["id"]
                )

                item["dimension"] = (
                    dimension["name"]
                )

                indicators.append(
                    item
                )

        return indicators

    # ==========================================================
    # INDICATOR COUNT
    # ==========================================================

    @staticmethod
    def total_indicator_count():

        return len(
            MPIConfig.get_all_indicators()
        )

    # ==========================================================
    # UPDATE INDICATOR
    # ==========================================================

    @staticmethod
    def update_indicator(
        dimension_id,
        indicator_id,
        new_name,
        new_variable,
        new_weight,
        new_definition="",
    ):
        """
        Update an existing indicator.
        """

        config = MPIConfig.get()

        new_name = str(
            new_name
        ).strip()

        new_definition = str(
            new_definition or ""
        ).strip()

        new_variable = str(
            new_variable
        ).strip()

        new_weight = float(
            new_weight
        )

        if not new_name:
            return False

        if not new_variable:
            return False

        if new_weight < 0 or new_weight > 1:
            return False

        dimension = MPIConfig.get_dimension(
            dimension_id
        )

        if dimension is None:
            return False

        # Prevent duplicate indicator name/variable
        for indicator in dimension["indicators"]:

            if indicator["id"] == indicator_id:
                continue

            if (
                indicator["name"]
                .strip()
                .lower()
                == new_name.lower()
            ):
                return False

            if (
                indicator.get("variable", "")
                .strip()
                .lower()
                == new_variable.lower()
            ):
                return False

        for indicator in dimension["indicators"]:

            if indicator["id"] != indicator_id:
                continue

            indicator["name"] = new_name
            indicator["definition"] = new_definition

            indicator["variable"] = (
                new_variable
            )

            indicator["variables"] = [
                new_variable
            ]

            indicator["weight"] = (
                new_weight
            )

            MPIConfig.save(config)
            MPIConfig._auto_balance()

            return True

        return False

    # ==========================================================
    # DELETE INDICATOR
    # ==========================================================

    @staticmethod
    def delete_indicator(
        dimension_id,
        indicator_id
    ):
        """
        Delete one indicator.
        """

        config = MPIConfig.get()

        dimension = MPIConfig.get_dimension(
            dimension_id
        )

        if dimension is None:
            return False

        original_count = len(
            dimension["indicators"]
        )

        dimension["indicators"] = [

            indicator

            for indicator
            in dimension["indicators"]

            if indicator.get("id")
            != indicator_id
        ]

        MPIConfig.save(config)
        MPIConfig._auto_balance()

        return (
            len(dimension["indicators"])
            < original_count
        )

    # ==========================================================
    # DIMENSION WEIGHTS
    # ==========================================================

    @staticmethod
    def total_weight():
        """
        Return total weight of all dimensions.
        """

        return sum(

            float(
                dimension.get(
                    "weight",
                    0.0
                )
            )

            for dimension
            in MPIConfig.get_all_dimensions()
        )

    # ==========================================================
    # VALIDATE DIMENSION WEIGHTS
    # ==========================================================

    @staticmethod
    def weights_are_valid(
        tolerance=1e-9
    ):
        """
        Dimension weights must sum to 1.000.
        """

        total = MPIConfig.total_weight()

        return abs(
            total - 1.0
        ) <= tolerance

    # ==========================================================
    # INDICATOR TOTAL WEIGHT
    # ==========================================================

    @staticmethod
    def indicator_total_weight(
        dimension_id
    ):
        """
        Return total indicator weight within
        one dimension.
        """

        indicators = MPIConfig.get_indicators(
            dimension_id
        )

        return sum(

            float(
                indicator.get(
                    "weight",
                    0.0
                )
            )

            for indicator
            in indicators
        )

    # ==========================================================
    # VALIDATE INDICATOR WEIGHTS
    # ==========================================================

    @staticmethod
    def indicator_weights_are_valid(
        dimension_id,
        tolerance=0.001
    ):
        """
        Indicator weights must sum to the
        parent dimension's weight.

        Example:

            Education = 0.333

            Indicator A = 0.1665
            Indicator B = 0.1665

            Total = 0.333
        """

        dimension = MPIConfig.get_dimension(
            dimension_id
        )

        if dimension is None:
            return False

        dimension_weight = float(
            dimension.get(
                "weight",
                0.0
            )
        )

        indicator_total = (
            MPIConfig.indicator_total_weight(
                dimension_id
            )
        )

        return abs(
            indicator_total
            - dimension_weight
        ) <= tolerance

    # ==========================================================
    # INDICATOR WEIGHT SUMMARY
    # ==========================================================

    @staticmethod
    def indicator_weight_summary():
        """
        Return validation summary for every dimension.
        """

        summary = []

        for dimension in (
            MPIConfig.get_all_dimensions()
        ):

            dimension_weight = float(
                dimension.get(
                    "weight",
                    0.0
                )
            )

            indicator_weight = (
                MPIConfig.indicator_total_weight(
                    dimension["id"]
                )
            )

            difference = (
                indicator_weight
                - dimension_weight
            )

            summary.append(
                {
                    "dimension":
                        dimension["name"],

                    "dimension_weight":
                        dimension_weight,

                    "indicator_weight":
                        indicator_weight,

                    "difference":
                        difference,

                    "valid":
                        abs(
                            difference
                        ) <= 0.001,
                }
            )

        return summary

    # ==========================================================
    # TOTAL CONFIGURATION VALIDATION
    # ==========================================================

    @staticmethod
    def is_configuration_valid():
        """
        Validate the complete MPI configuration.

        Rules:

        1. At least one dimension exists.
        2. Dimension weights sum to 1.000.
        3. Every dimension contains at least one indicator.
        4. Indicator weights within each dimension
           sum to the dimension weight.
        """

        dimensions = (
            MPIConfig.get_all_dimensions()
        )

        # No dimensions
        if not dimensions:
            return False

        # Dimension weights
        if not MPIConfig.weights_are_valid():
            return False

        # Validate every dimension
        for dimension in dimensions:

            indicators = dimension.get(
                "indicators",
                []
            )

            # Dimension without indicators
            if not indicators:
                return False

            # Indicator weights must equal
            # parent dimension weight
            if not MPIConfig.indicator_weights_are_valid(
                dimension["id"]
            ):
                return False

            # Every indicator needs a name
            # and a dataset variable
            for indicator in indicators:

                if not str(
                    indicator.get(
                        "name",
                        ""
                    )
                ).strip():
                    return False

                if not str(
                    indicator.get(
                        "variable",
                        ""
                    )
                ).strip():
                    return False

        return True


# ==============================================================
# PUBLIC API
# ==============================================================

__all__ = [
    "MPIConfig"
]