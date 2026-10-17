from pathlib import Path

import streamlit as st

from core.auth import allowed, login_form, logout, require_login, role
from core.theme import inject_theme, user_chip

st.set_page_config(
    page_title="NMPI Automation Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not require_login():
    login_form()
    st.stop()

inject_theme()

_display_name = st.session_state.get("user_name", st.session_state.get("username", ""))
st.sidebar.markdown(user_chip(_display_name, role().title()), unsafe_allow_html=True)
if st.sidebar.button("🚪 Sign out", use_container_width=True):
    logout()


# ============================================================
# PAGES
# ============================================================

PAGES_DIR = Path(__file__).parent / "pages"

pages = []


def add_page(number, title, icon, key):
    """
    Register the page whose file name starts with `number` (e.g. "00_").

    The file is found by its number, so it does not matter whether the
    file name contains an emoji or not (00_Home.py or 00_🏠_Home.py).
    """
    if not allowed(role(), key):
        return

    match = next(iter(sorted(PAGES_DIR.glob(f"{number}_*.py"))), None)
    if match is None:
        return  # page file is missing — skip it instead of crashing

    pages.append(st.Page(f"pages/{match.name}", title=title, icon=icon))


add_page("00", "Home", ":material/home:", "home")
add_page("01", "Load Dataset", ":material/folder_open:", "load")
add_page("02", "MPI Configuration", ":material/settings:", "config")
add_page("03", "Analysis", ":material/analytics:", "analysis")
add_page("04", "Results", ":material/insert_chart:", "results")
add_page("05", "Export", ":material/download:", "export")
add_page("07", "Change Over Time", ":material/timeline:", "change")
add_page("06", "User Guide", ":material/menu_book:", "guide")
add_page("08", "User Manager", ":material/group:", "users")

if not pages:
    st.error("No pages are available for this account.")
    st.stop()

navigation = st.navigation(pages, position="sidebar")
navigation.run()