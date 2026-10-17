"""
NMPI Automation Tool — Home page
National Bureau of Statistics, Tanzania
"""

from pathlib import Path

import streamlit as st

from core.ui import render_brand


# ============================================================
# HELPERS
# ============================================================

def find_page(pattern: str):
    """
    Return the path ("pages/<file>") of the first page in this folder
    that matches `pattern`, or None if it does not exist.

    Works whether the page files have emoji in their names or not.
    """
    match = next(Path(__file__).parent.glob(pattern), None)
    return f"pages/{match.name}" if match else None


# ============================================================
# HEADER (logo, title, logo)
# ============================================================

render_brand()


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 1120px;
        padding-top: 1.4rem;
        padding-bottom: 2.5rem;
    }

    .nmpi-card {
        background: #FFFFFF;
        border: 1px solid #D9E2EC;
        border-radius: 12px;
        padding: 1.1rem 1.25rem;
        margin-bottom: 0.85rem;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
    }

    .nmpi-card-title {
        color: #17365D;
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.45rem;
    }

    .nmpi-card-text {
        color: #344054;
        font-size: 0.92rem;
        line-height: 1.6;
        margin: 0;
    }

    .nmpi-manual {
        background: #F8FAFC;
        border: 1px solid #D9E2EC;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-top: 0.6rem;
        margin-bottom: 0.75rem;
    }

    .nmpi-manual-title {
        color: #17365D;
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }

    .nmpi-manual-text {
        color: #475467;
        font-size: 0.9rem;
        line-height: 1.5;
        margin: 0;
    }

    .nmpi-footer {
        text-align: center;
        color: #98A2B3;
        font-size: 0.75rem;
        margin-top: 2rem;
    }

    @media (max-width: 700px) {
        .nmpi-card { padding: 0.9rem; }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# ABOUT
# ============================================================

st.markdown(
    """
    <div class="nmpi-card">
        <div class="nmpi-card-title">About the National MPI</div>
        <p class="nmpi-card-text">
            The National Multidimensional Poverty Index looks beyond income
            to measure how many people are deprived across education,
            health and living standards at the same time. Using the
            Alkire-Foster methodology, the tool combines weighted
            indicators against a chosen poverty cut-off to identify who is
            multidimensionally poor, producing H (headcount), A (intensity)
            and M0 (the overall index) to show both how widespread and how
            severe that poverty is.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# USER MANUAL
# ============================================================

st.markdown(
    """
    <div class="nmpi-manual">
        <div class="nmpi-manual-title">
            User Manual
        </div>
        <p class="nmpi-manual-text">
            Get the complete guide for preparing data, configuring the MPI,
            running analysis, interpreting results and exporting outputs.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

manual_page = find_page("06_*Manual*.py")

if manual_page:
    try:
        st.page_link(manual_page, label="📖 Open User Manual")
    except Exception:
        # The manual page is not registered for this account/role —
        # skip the link instead of crashing the Home page.
        pass


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="nmpi-footer">
        National Bureau of Statistics · Tanzania
    </div>
    """,
    unsafe_allow_html=True,
)