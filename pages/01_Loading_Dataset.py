import streamlit as st
import pandas as pd

from core.data_loader import DataLoader
from core.data_summary import DataSummary
from core.variable_explorer import VariableExplorer
from core.data_validator import DataValidator

# =========================================================
# PAGE TITLE
# =========================================================

st.title("📂 Load Dataset")

st.write("Upload a CSV or Excel or Stata dataset for Multidimensional Poverty Index (MPI) analysis.")

# =========================================================
# FILE UPLOADER
# =========================================================

uploaded_file = st.file_uploader(
    "Choose Dataset",
    type=["csv", "xlsx", "dta"],
)

summary = None

# =========================================================
# LOAD DATASET
# =========================================================

if uploaded_file:

    try:

        dataset = DataLoader.load_dataset(uploaded_file)

        st.session_state.dataset = dataset
        st.session_state.dataset_name = uploaded_file.name

        st.success("✅ Dataset loaded successfully.")

        summary = DataSummary.get_summary(dataset, uploaded_file)

    except Exception as e:

        st.error(f"Error loading dataset : {e}")

# =========================================================
# DISPLAY DATASET
# =========================================================

if st.session_state.get("dataset") is not None:

    dataset = st.session_state.dataset

    if summary is None:

        summary = DataSummary.get_summary(dataset)

    # =====================================================
    # DATASET INFORMATION
    # =====================================================

    st.divider()

    st.subheader("📁 Dataset Information")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Dataset Name",
            st.session_state.dataset_name
        )

    with c2:
        st.metric(
            "Observations",
            dataset.shape[0]
        )

    with c3:
        st.metric(
            "Variables",
            dataset.shape[1]
        )

    # =====================================================
    # DATASET SUMMARY
    # =====================================================

    st.divider()

    st.subheader("📊 Dataset Summary")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "File Size (MB)",
            summary["file_size"]
        )

    with c2:
        st.metric(
            "Memory Usage (MB)",
            summary["memory"]
        )

    with c3:
        st.metric(
            "Numeric Variables",
            summary["numeric"]
        )

    with c4:
        st.metric(
            "Categorical Variables",
            summary["categorical"]
        )

    # =====================================================
    # DATA PREVIEW
    # =====================================================

    st.divider()

    st.subheader("👀 Dataset Preview")

    st.dataframe(
        dataset.head(10),
        use_container_width=True
    )

    # =====================================================
    # VARIABLE SUMMARY
    # =====================================================

    st.divider()

    st.subheader("📑 Variable Summary")

    variable_table = DataSummary.variable_summary(dataset)

    st.dataframe(
        variable_table,
        use_container_width=True,
        hide_index=True
    )

    # =====================================================
    # VARIABLE EXPLORER
    # =====================================================

    st.divider()

    st.subheader("🔍 Variable Explorer")

    left, right = st.columns([2, 1])

    with left:

        search = st.text_input(
            "Search Variable",
            placeholder="Example : age"
        )

    with right:

        dtype = st.selectbox(
            "Filter by Data Type",
            [
                "All",
                "Numeric",
                "Categorical",
                "Boolean",
                "Date"
            ]
        )

    variables = VariableExplorer.filter_variables(
        dataset,
        dtype,
        search
    )

    st.dataframe(
        variables,
        use_container_width=True,
        hide_index=True
    )

    # =====================================================
    # VARIABLE DETAILS
    # =====================================================

    st.divider()

    st.subheader("📌 Variable Details")

    selected = st.selectbox(
        "Select Variable",
        dataset.columns
    )

    series = dataset[selected]

    st.write("### First 15 Values")

    st.dataframe(
        series.head(15),
        use_container_width=True
    )

    if pd.api.types.is_numeric_dtype(series):

        stats = VariableExplorer.numeric_summary(series)

        a, b, c, d, e = st.columns(5)

        a.metric("Mean", stats["Mean"])
        b.metric("Median", stats["Median"])
        c.metric("Minimum", stats["Minimum"])
        d.metric("Maximum", stats["Maximum"])
        e.metric("Std Dev", stats["Std"])

    else:

        st.write("### Frequency Distribution")

        freq = VariableExplorer.categorical_summary(series)

        st.dataframe(
            freq,
            use_container_width=True,
            hide_index=True
        )

    # =====================================================
    # DATA VALIDATION
    # =====================================================

    st.divider()

    st.subheader("✅ Data Validation")

    validation = DataValidator.validate(dataset)

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Duplicate Rows",
            validation["duplicate_rows"]
        )

    with c2:

        st.metric(
            "Missing Cells",
            validation["missing_cells"]
        )

    with c3:

        st.metric(
            "Constant Variables",
            validation["constant_variables"]
        )

    c1, c2 = st.columns(2)

    with c1:

        st.metric(
            "Variables >50% Missing",
            validation["high_missing_variables"]
        )

    with c2:

        score = 100

        score -= validation["duplicate_rows"] * 0.5

        score -= validation["constant_variables"] * 2

        score -= validation["high_missing_variables"] * 5

        score = max(0, round(score))

        st.metric(
            "Validation Score",
            f"{score}%"
        )

    st.subheader("📉 Missing Values Report")

    missing = DataValidator.missing_table(dataset)

    st.dataframe(
        missing,
        use_container_width=True,
        hide_index=True
    )

    constant = DataValidator.constant_variables(dataset)

    if constant:

        st.warning("Constant Variables Found")

        st.write(constant)

    else:

        st.success("No Constant Variables Found.")

else:

    st.info("👆 Please upload a dataset to continue.")