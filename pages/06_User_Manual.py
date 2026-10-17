import streamlit as st

from core.ui import render_brand


render_brand()


# ============================================================
# CUSTOM CSS — mtindo unaofanana na Home, lakini wenye taswira
# ya "guide" ya kitaalamu (professional documentation feel)
# ============================================================

st.markdown(
    """
    <style>

    .manual-hero {
        text-align: center;
        padding: 1.4rem 1rem 1.6rem 1rem;
        margin-bottom: 1.2rem;
    }

    .manual-hero h1 {
        color: #17365D;
        font-size: 1.9rem;
        font-weight: 750;
        margin-bottom: 0.4rem;
        letter-spacing: -0.01em;
    }

    .manual-hero p {
        color: #667085;
        font-size: 0.98rem;
        max-width: 620px;
        margin: 0 auto;
        line-height: 1.55;
    }

    .manual-divider {
        border: none;
        border-top: 1px solid #E4E7EC;
        margin: 0.5rem 0 1.6rem 0;
    }

    .manual-section-label {
        color: #17365D;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin: 1.6rem 0 0.7rem 2px;
    }

    /* Muhtasari wa yaliyomo — grid ya vitufe vidogo */
    .manual-toc {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.55rem;
        margin-bottom: 0.6rem;
    }

    .manual-toc-item {
        background: #F8FAFC;
        border: 1px solid #E4E7EC;
        border-radius: 10px;
        padding: 0.6rem 0.8rem;
        color: #344054;
        font-size: 0.85rem;
        font-weight: 550;
    }

    @media (max-width: 700px) {
        .manual-toc { grid-template-columns: 1fr; }
    }

    /* Streamlit expander kama "documentation entry" ya kitaalamu */
    div[data-testid="stExpander"] {
        border: 1px solid #E4E7EC !important;
        border-radius: 12px !important;
        margin-bottom: 0.6rem;
        overflow: hidden;
    }

    div[data-testid="stExpander"] summary {
        padding: 0.85rem 1.1rem !important;
        font-weight: 650 !important;
        color: #17365D !important;
        font-size: 0.98rem !important;
    }

    div[data-testid="stExpander"] summary:hover {
        background: #F8FAFC;
    }

    .manual-body {
        color: #475467;
        font-size: 0.92rem;
        line-height: 1.65;
        padding: 0.2rem 0.2rem 0.6rem 0.2rem;
    }

    .manual-note {
        background: #FFF9EC;
        border: 1px solid #F4D9A0;
        border-left: 4px solid #C98A1C;
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        color: #7A5416;
        font-size: 0.9rem;
        line-height: 1.6;
        margin-top: 0.4rem;
    }

    .manual-note b {
        color: #5C3F10;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="manual-hero">
        <h1>User Manual</h1>
        <p>
            A complete reference for preparing data, configuring the MPI,
            running the Alkire–Foster analysis, interpreting results,
            saving projects and exporting outputs.
        </p>
    </div>
    <hr class="manual-divider">
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TABLE OF CONTENTS — muhtasari wa haraka
# ============================================================

toc_items = [
    "Load your dataset",
    "Configure dimensions",
    "Configure indicators",
    "Set the poverty cut-off",
    "Select survey weights",
    "Run the analysis",
    "Read the results",
    "Read contribution results",
    "Disaggregate results",
    "Save your project",
    "Export results",
]

st.markdown('<div class="manual-section-label" style="text-align:center;">Contents</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="manual-toc">'
    + "".join(f'<div class="manual-toc-item">{item}</div>' for item in toc_items)
    + "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# SECTIONS — expanders badala ya kadi tuli; hakuna namba,
# hakuna emoji zisizo za lazima
# ============================================================

sections = [
    ("Load your dataset",
     "Start from Load Dataset. Select the file containing your analysis variables. "
     "The tool checks that the dataset exists, is readable and contains the configured "
     "deprivation indicators."),
    ("Configure dimensions",
     "A dimension is a broad area of poverty such as Education, Health or Living Standards. "
     "Give every dimension a weight. All dimension weights must add up to exactly 1.000."),
    ("Configure indicators",
     "Add the indicators belonging to each dimension and connect each indicator to its "
     "deprivation variable. Indicator weights within a dimension must add up to that "
     "dimension's weight."),
    ("Set the poverty cut-off",
     "The poverty cut-off k determines the minimum weighted deprivation score required for "
     "an observation to be classified as multidimensionally poor."),
    ("Select survey weights",
     "If your survey uses expansion weights, select the appropriate weight variable. The "
     "tool then calculates weighted H, A, M0 and subgroup results."),
    ("Run the analysis",
     "Run the analysis after validation succeeds. The tool calculates the deprivation "
     "score, identifies the multidimensionally poor and produces the main MPI measures."),
    ("Read the results",
     "H is the weighted proportion of people who are multidimensionally poor. A is the "
     "average weighted deprivation intensity among the poor. M0 is H multiplied by A."),
    ("Read contribution results",
     "Dimension contribution shows how much each dimension contributes to the overall MPI. "
     "Indicator contribution provides the more detailed contribution of individual indicators."),
    ("Disaggregate results",
     "Select a population characteristic such as sex, residence, region or another valid "
     "grouping variable to compare MPI results across subgroups."),
    ("Save your project",
     "Use the .nmpi project option to preserve the configuration, dataset and reproducibility "
     "metadata so the work can be reopened later."),
    ("Export results",
     "Export analysis tables, contribution tables, audit information and metadata for "
     "reporting, review and further processing."),
]

st.markdown('<div class="manual-section-label">Guide</div>', unsafe_allow_html=True)

for title, body in sections:
    with st.expander(title, expanded=False):
        st.markdown(f'<div class="manual-body">{body}</div>', unsafe_allow_html=True)


# ============================================================
# WEIGHT RULE — muhimu, hivyo inaonyeshwa kama callout
# ============================================================

st.markdown('<div class="manual-section-label">Important weight rule</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="manual-note">
        Dimension weights must sum to <b>1.000</b>. Within every dimension, indicator
        weights must sum to that dimension's weight. For example, if a dimension has
        weight 0.334, its indicators must total 0.334.
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()
st.header("⏳ Change Over Time")
st.write(
    "Use Change Over Time when two survey periods use the same MPI definition. "
    "Load the first-year and second-year .nmpi projects, enter or confirm the survey "
    "weight variable for each period, and compare H, A and M0."
)
st.markdown(
    """
1. **Period A** — select the earlier `.nmpi` project and year.
2. **Period B** — select the later `.nmpi` project and year.
3. The tool checks dimensions, indicators, variables, weights and the poverty cut-off.
4. Different internal UUIDs do not matter; the substantive MPI definition is compared.
5. Review the comparison bar charts for overall MPI, dimension contribution and indicator contribution.
6. Use subgroup analysis for a common sex, residence or other grouping variable.
"""
)
st.info(
    "If the two periods use different dimensions, indicators, variables, weights or cut-offs, "
    "the comparison is not a pure time comparison."
)
