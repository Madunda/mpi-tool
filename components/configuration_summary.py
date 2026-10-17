import streamlit as st

from core.mpi_config import MPIConfig
from core.theme import card_header, kpi_grid, pill


# ==========================================================
# PROJECT SETTINGS (interactive first section)
# ==========================================================

UNIT_OPTIONS = ["Household", "Individual"]
UNIT_LABELS = {"Household": "🏠 Household", "Individual": "👤 Individual"}

NAME_KEY = "cfg_project_name"
UNIT_KEY = "cfg_analysis_unit"
CUTOFF_KEY = "cfg_deprivation_cutoff_pct"

CUTOFF_MIN = 1.0
CUTOFF_MAX = 100.0
CUTOFF_PRESETS = (20.0, 33.3, 50.0)


def _cutoff_to_percent(cutoff) -> float:
    """Stored cut-off (0-1 proportion) -> slider percentage."""
    try:
        pct = float(cutoff) * 100.0
    except (TypeError, ValueError):
        pct = 33.3
    return round(min(max(pct, CUTOFF_MIN), CUTOFF_MAX), 1)


def _on_name_change():
    new_name = str(st.session_state.get(NAME_KEY, "")).strip()

    if new_name:
        MPIConfig.update_project_settings(project_name=new_name)
    else:
        # A project must keep a name — restore the previous one.
        st.session_state[NAME_KEY] = MPIConfig.get()["project_name"]
        st.session_state["cfg_name_blank"] = True


def _on_unit_change():
    unit = st.session_state.get(UNIT_KEY)

    if unit in UNIT_OPTIONS:
        MPIConfig.update_project_settings(analysis_unit=unit)
    else:
        # Clicking the selected option again clears it — keep the current unit.
        st.session_state[UNIT_KEY] = MPIConfig.get()["analysis_unit"]


def _on_cutoff_change():
    pct = float(st.session_state.get(CUTOFF_KEY, 33.3))
    # The engine keeps reading the same stored value (a 0-1 proportion).
    MPIConfig.update_project_settings(poverty_cutoff=round(pct / 100.0, 4))


def _apply_cutoff_preset(pct: float):
    st.session_state[CUTOFF_KEY] = pct
    _on_cutoff_change()


def _show_project_settings(config):
    """Editable project card: name, unit of identification , deprivation cut-off."""

    # Seed widget state once (later edits are handled by the callbacks).
    if NAME_KEY not in st.session_state:
        st.session_state[NAME_KEY] = config["project_name"]

    if UNIT_KEY not in st.session_state:
        unit = config.get("unit_of_identification", "Household")
        st.session_state[UNIT_KEY] = unit if unit in UNIT_OPTIONS else "Household"

    if CUTOFF_KEY not in st.session_state:
        st.session_state[CUTOFF_KEY] = _cutoff_to_percent(config["poverty_cutoff"])

    is_valid = MPIConfig.is_configuration_valid()
    status_pill = (
        pill("Ready for analysis", "ok") if is_valid else pill("Incomplete", "warn")
    )

    with st.container(key="nxcard_project"):

        card_header(
            "⚙️",
            "Project Settings",
            "Name your project and choose the unit and cut-off used to identify "
            "poverty. Changes apply immediately.",
            right_html=status_pill,
        )

        col_name, col_unit, col_cutoff = st.columns([1.15, 1.25, 1.35], gap="large")

        with col_name:
            st.text_input(
                "Project name",
                key=NAME_KEY,
                on_change=_on_name_change,
                placeholder="e.g. National MPI 2022",
                max_chars=120,
            )

            if st.session_state.pop("cfg_name_blank", False):
                st.caption("⚠️ The project name cannot be empty — previous name restored.")

        with col_unit:
            st.segmented_control(
                "Unit of Identification ",
                options=UNIT_OPTIONS,
                format_func=lambda option: UNIT_LABELS[option],
                key=UNIT_KEY,
                on_change=_on_unit_change,
            )

        with col_cutoff:
            st.slider(
                "Deprivation cut-off (k)",
                min_value=CUTOFF_MIN,
                max_value=CUTOFF_MAX,
                step=0.1,
                format="%.1f%%",
                key=CUTOFF_KEY,
                on_change=_on_cutoff_change,
            )

        # Plain-language reading of the chosen values + quick presets
        col_note, col_presets = st.columns([2.4, 1.35], gap="large")

        unit_name = str(config.get("analysis_unit", "Household")).lower()
        unit_phrase = ("an " if unit_name.startswith(("a", "e", "i", "o", "u")) else "a ") + unit_name
        cutoff_pct = float(config["poverty_cutoff"]) * 100.0

        with col_note:
            st.caption(
                f"{unit_phrase.capitalize()} is identified as multidimensionally poor when its "
                f"weighted deprivation score is **{cutoff_pct:.1f}%** or higher "
                f"(k = {float(config['poverty_cutoff']):.3f})."
            )

        with col_presets:
            preset_cols = st.columns(len(CUTOFF_PRESETS), gap="small")
            for column, pct in zip(preset_cols, CUTOFF_PRESETS):
                column.button(
                    f"{pct:g}%",
                    key=f"cfg_cutoff_preset_{pct:g}",
                    on_click=_apply_cutoff_preset,
                    args=(pct,),
                    use_container_width=True,
                )


def show_configuration_summary():
    """
    Display a complete summary of the current MPI configuration.

    Validates:
        1. Project settings
        2. Dimension existence
        3. Dimension weights
        4. Indicator existence
        5. Indicator weights
        6. Indicator dataset variables
    """

    config = MPIConfig.get()
    dimensions = MPIConfig.get_all_dimensions()

    # ==========================================================
    # PROJECT SETTINGS  (interactive)
    # ==========================================================

    _show_project_settings(config)

    # ==========================================================
    # OVERALL COUNTS
    # ==========================================================

    total_weight = MPIConfig.total_weight()
    is_valid = MPIConfig.is_configuration_valid()

    if not dimensions:
        weight_tone = ""
    elif MPIConfig.weights_are_valid():
        weight_tone = "ok"
    else:
        weight_tone = "warn"

    kpi_grid(
        [
            ("📁", "Dimensions", MPIConfig.total_dimension_count(), "", ""),
            ("🧩", "Indicators", MPIConfig.total_indicator_count(), "", ""),
            ("⚖️", "Dimension weight", f"{total_weight:.3f}", "Must total 1.000", weight_tone),
            (
                "✅" if is_valid else "⚠️",
                "Status",
                "Valid" if is_valid else "Incomplete",
                "Ready for analysis" if is_valid else "Review the checks below",
                "ok" if is_valid else "warn",
            ),
        ]
    )

    # ==========================================================
    # NO DIMENSIONS
    # ==========================================================

    if len(dimensions) == 0:

        st.info(
            "No dimensions have been configured yet."
        )

        return

    # ==========================================================
    # DIMENSION WEIGHT
    # ==========================================================

    st.divider()

    st.markdown("### Dimension Weights")

    total_dimension_weight = MPIConfig.total_weight()

    if MPIConfig.weights_are_valid():

        st.success(
            f"Total dimension weight = "
            f"{total_dimension_weight:.3f} ✅"
        )

    else:

        st.warning(
            f"Total dimension weight = "
            f"{total_dimension_weight:.3f}. "
            f"Dimension weights must sum to 1.000."
        )

    # ==========================================================
    # DIMENSION DETAILS
    # ==========================================================

    st.divider()

    st.markdown("### Dimensions & Indicators")

    for dimension in dimensions:

        indicators = dimension["indicators"]

        indicator_total = MPIConfig.indicator_total_weight(
            dimension["id"]
        )

        indicator_weights_valid = (
            MPIConfig.indicator_weights_are_valid(
                dimension["id"]
            )
        )

        if indicator_weights_valid:
            status_icon = "✅"
        else:
            status_icon = "⚠️"

        with st.expander(
            f"📁 {dimension['name']} "
            f"| Weight: {dimension['weight']:.3f} "
            f"| Indicators: {len(indicators)} "
            f"| {status_icon}"
        ):

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    f"**Dimension Weight:** "
                    f"{dimension['weight']:.3f}"
                )

            with col2:

                st.write(
                    f"**Indicator Weight Total:** "
                    f"{indicator_total:.3f}"
                )

            if len(indicators) == 0:

                st.warning(
                    "This dimension has no indicators."
                )

                continue

            if indicator_weights_valid:

                st.success(
                    "Indicator weights are valid."
                )

            else:

                st.warning(
                    "Indicator weights must sum to 1.000."
                )

            st.divider()

            # ==================================================
            # INDICATOR TABLE
            # ==================================================

            for indicator in indicators:

                col1, col2, col3 = st.columns(
                    [4, 4, 2]
                )

                with col1:

                    st.write(
                        f"**{indicator['name']}**"
                    )

                with col2:

                    st.code(
                        indicator["variable"]
                    )

                with col3:

                    st.write(
                        f"{indicator['weight']:.3f}"
                    )

    # ==========================================================
    # FINAL VALIDATION
    # ==========================================================

    st.divider()

    st.markdown("### 🔎 Final Validation")

    validation_errors = []

    # ----------------------------------------------------------
    # Dimension validation
    # ----------------------------------------------------------

    if len(dimensions) == 0:

        validation_errors.append(
            "At least one dimension is required."
        )

    # ----------------------------------------------------------
    # Dimension weight validation
    # ----------------------------------------------------------

    if not MPIConfig.weights_are_valid():

        validation_errors.append(
            "Dimension weights must sum to 1.000."
        )

    # ----------------------------------------------------------
    # Indicator validation
    # ----------------------------------------------------------

    for dimension in dimensions:

        if len(dimension["indicators"]) == 0:

            validation_errors.append(
                f"Dimension '{dimension['name']}' "
                f"has no indicators."
            )

            continue

        if not MPIConfig.indicator_weights_are_valid(
            dimension["id"]
        ):

            validation_errors.append(
                f"Indicators in dimension "
                f"'{dimension['name']}' "
                f"must have weights summing to 1.000."
            )

    # ==========================================================
    # VALID / INVALID RESULT
    # ==========================================================

    if len(validation_errors) == 0:

        st.success(
            "✅ MPI configuration is valid and ready "
            "for Analysis."
        )

        return True

    else:

        st.error(
            "❌ MPI configuration is not yet valid."
        )

        for error in validation_errors:

            st.write(
                f"- {error}"
            )

        return False


__all__ = [
    "show_configuration_summary"
]