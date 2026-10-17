import streamlit as st


def initialize_session():

    defaults = {

        "dataset": None,

        "dataset_name": None,

        "dimensions": [],

        "results": None,

        "project_name": "Untitled Project"

    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value