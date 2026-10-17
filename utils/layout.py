import streamlit as st

from utils.constants import APP_NAME, VERSION


def page_header():

    st.title(APP_NAME)

    st.caption(VERSION)

    st.divider()


def footer():

    st.divider()

    st.caption("MPI Analysis Tool | Alkire-Foster Methodology")