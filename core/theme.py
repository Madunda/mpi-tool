"""Shared visual design system for the NMPI Automation Tool.

Presentation only — nothing in this module touches calculations or data.

Usage
-----
    from core.theme import inject_theme, page_header, card_header, kpi_grid, pill

* ``inject_theme()``  — call once from ``app.py`` (runs on every page).
* ``login_css()``     — stylesheet used only by the sign-in screen.
* HTML helpers        — small, escaped building blocks used by the pages.
"""

from __future__ import annotations

from html import escape

import streamlit as st

# ----------------------------------------------------------------------
# Global stylesheet (all signed-in pages)
# ----------------------------------------------------------------------

_THEME_CSS = """
<style>
:root {
    --nx-navy: #102a43;
    --nx-navy-2: #163b5c;
    --nx-blue: #1f4e79;
    --nx-gold: #c89b3c;
    --nx-ink: #172b4d;
    --nx-muted: #667085;
    --nx-bg: #f4f6fa;
    --nx-card: #ffffff;
    --nx-border: #dde5ee;
    --nx-ok: #067647;
    --nx-ok-bg: #e7f6ee;
    --nx-warn: #b54708;
    --nx-warn-bg: #fff4e5;
    --nx-bad: #b42318;
    --nx-bad-bg: #fdecea;
}

.stApp { background: var(--nx-bg); }

/* --- chrome ------------------------------------------------------- */
[data-testid="stAppDeployButton"], .stDeployButton { display: none !important; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"], .block-container {
    max-width: 1180px;
    padding-top: 2.2rem;
    padding-bottom: 3rem;
}

/* --- sidebar ------------------------------------------------------ */
[data-testid="stSidebar"] {
    background: linear-gradient(190deg, #0d2238 0%, #133453 55%, #1a4468 100%);
    border-right: 1px solid rgba(255,255,255,.08);
}
[data-testid="stSidebar"] * { color: #eaf1f8; }
[data-testid="stSidebarNav"] a {
    border-radius: 10px;
    margin: 2px 8px;
    transition: background .15s ease;
}
[data-testid="stSidebarNav"] a:hover { background: rgba(255,255,255,.09); }
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: linear-gradient(90deg, rgba(200,155,60,.28), rgba(200,155,60,.08));
    border-left: 3px solid var(--nx-gold);
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.12); }
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.28);
    color: #ffffff;
    border-radius: 10px;
    font-weight: 600;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,.16);
    border-color: rgba(255,255,255,.55);
    color: #ffffff;
}

.nx-userchip {
    display: flex; align-items: center; gap: 12px;
    margin: 6px 4px 14px;
    padding: 12px 14px;
    background: rgba(255,255,255,.07);
    border: 1px solid rgba(255,255,255,.12);
    border-radius: 14px;
}
.nx-userchip .nx-avatar { width: 40px; height: 40px; font-size: .9rem; }
.nx-userchip-name { font-weight: 650; font-size: .92rem; line-height: 1.2; color: #fff; }
.nx-userchip-role { font-size: .74rem; letter-spacing: .06em; text-transform: uppercase; color: #f0cf8a; margin-top: 2px; }

/* --- typography --------------------------------------------------- */
h1, h2, h3 { color: var(--nx-navy); letter-spacing: -.015em; }
h1 { font-weight: 750; }

/* --- page header -------------------------------------------------- */
.nx-pagehead { display: flex; align-items: center; gap: 16px; margin: 0 0 1.4rem; }
.nx-pagehead-icon {
    width: 52px; height: 52px; border-radius: 15px; flex: 0 0 52px;
    display: grid; place-items: center; font-size: 1.5rem;
    background: linear-gradient(145deg, #143a5e, #1f4e79);
    box-shadow: 0 8px 20px rgba(16,42,67,.22);
}
.nx-pagehead h1 { margin: 0; padding: 0; font-size: 1.7rem; line-height: 1.2; color: var(--nx-navy); }
.nx-pagehead p { margin: 3px 0 0; color: var(--nx-muted); font-size: .95rem; }

/* --- cards -------------------------------------------------------- */
[class*="st-key-nxcard_"] {
    background: var(--nx-card);
    border: 1px solid var(--nx-border);
    border-radius: 18px;
    padding: 1.35rem 1.6rem 1.5rem;
    box-shadow: 0 1px 2px rgba(16,42,67,.04), 0 10px 28px rgba(16,42,67,.05);
}
.nx-card-head { display: flex; align-items: center; gap: 14px; margin-bottom: .55rem; }
.nx-card-icon {
    width: 42px; height: 42px; border-radius: 12px; flex: 0 0 42px;
    display: grid; place-items: center; font-size: 1.2rem;
    background: #e9f0f7; border: 1px solid #d5e2ef;
}
.nx-card-title { font-size: 1.08rem; font-weight: 700; color: var(--nx-navy); line-height: 1.25; }
.nx-card-sub { font-size: .86rem; color: var(--nx-muted); margin-top: 2px; }
.nx-card-right { margin-left: auto; }

/* forms placed inside a card lose their own frame */
[class*="st-key-nxcard_"] [data-testid="stForm"] { border: 0; padding: 0; }

/* --- pills -------------------------------------------------------- */
.nx-pill {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 3px 11px; border-radius: 999px;
    font-size: .76rem; font-weight: 650; white-space: nowrap;
    background: #eef2f6; color: #475467; border: 1px solid #e0e6ed;
}
.nx-pill::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; opacity: .85; }
.nx-pill.ok    { background: var(--nx-ok-bg);   color: var(--nx-ok);   border-color: #c6e8d5; }
.nx-pill.warn  { background: var(--nx-warn-bg); color: var(--nx-warn); border-color: #fbdcae; }
.nx-pill.bad   { background: var(--nx-bad-bg);  color: var(--nx-bad);  border-color: #f6cdc8; }
.nx-pill.admin   { background: #f3e8f7; color: #7a2a8f; border-color: #e6cff0; }
.nx-pill.analyst { background: #e6f0fb; color: #1f4e79; border-color: #cfe0f5; }
.nx-pill.viewer  { background: #eef2f6; color: #475467; border-color: #e0e6ed; }
.nx-pill.you     { background: #fff6e0; color: #8a6414; border-color: #f3dfaa; }

/* --- KPI tiles ---------------------------------------------------- */
.nx-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; margin: .4rem 0 1rem; }
.nx-kpi {
    background: var(--nx-card); border: 1px solid var(--nx-border); border-radius: 16px;
    padding: 16px 18px; display: flex; gap: 14px; align-items: center;
    box-shadow: 0 1px 2px rgba(16,42,67,.04), 0 8px 22px rgba(16,42,67,.045);
}
.nx-kpi-icon {
    width: 44px; height: 44px; border-radius: 13px; flex: 0 0 44px;
    display: grid; place-items: center; font-size: 1.25rem; background: #e9f0f7;
}
.nx-kpi.ok   .nx-kpi-icon { background: var(--nx-ok-bg); }
.nx-kpi.warn .nx-kpi-icon { background: var(--nx-warn-bg); }
.nx-kpi-label { font-size: .74rem; font-weight: 650; letter-spacing: .07em; text-transform: uppercase; color: var(--nx-muted); }
.nx-kpi-value { font-size: 1.55rem; font-weight: 750; color: var(--nx-navy); line-height: 1.15; }
.nx-kpi.ok   .nx-kpi-value { color: var(--nx-ok); }
.nx-kpi.warn .nx-kpi-value { color: var(--nx-warn); }
.nx-kpi-foot { font-size: .78rem; color: var(--nx-muted); margin-top: 1px; }
@media (max-width: 900px) { .nx-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } }

/* --- avatar ------------------------------------------------------- */
.nx-avatar {
    width: 40px; height: 40px; border-radius: 50%; flex: 0 0 40px;
    display: grid; place-items: center; font-weight: 700; font-size: .85rem; letter-spacing: .02em;
    color: #fff; background: linear-gradient(145deg, #1f4e79, #2e6da4);
}
.nx-avatar.admin   { background: linear-gradient(145deg, #6b2a86, #9b4bb8); }
.nx-avatar.analyst { background: linear-gradient(145deg, #1f4e79, #2e6da4); }
.nx-avatar.viewer  { background: linear-gradient(145deg, #55657a, #7a8aa0); }
.nx-avatar.off     { background: #c5ccd6; }

/* --- users table -------------------------------------------------- */
.nx-table-wrap {
    overflow-x: auto; margin-top: .8rem;
    border: 1px solid var(--nx-border); border-radius: 14px;
}
.nx-table { width: 100%; border-collapse: collapse; font-size: .92rem; margin: 0; }
.nx-table th, .nx-table td { border: 0; }
.nx-table th {
    text-align: left; font-size: .72rem; font-weight: 650; letter-spacing: .07em; text-transform: uppercase;
    color: var(--nx-muted); padding: 11px 16px; background: #f6f8fb;
    border-bottom: 1px solid var(--nx-border);
}
.nx-table td { padding: 13px 16px; border-bottom: 1px solid #edf1f5; vertical-align: middle; color: var(--nx-ink); }
.nx-table tbody tr:last-child td { border-bottom: 0; }
.nx-table tbody tr:hover td { background: #fafbfd; }
.nx-usercell { display: flex; align-items: center; gap: 12px; }
.nx-username { font-weight: 650; color: var(--nx-navy); line-height: 1.2; }
.nx-handle { font-size: .8rem; color: var(--nx-muted); font-family: ui-monospace, 'Cascadia Mono', Consolas, monospace; }
.nx-access { color: #475467; font-size: .86rem; }

/* --- native widgets polish --------------------------------------- */
div[data-testid="stMetric"] {
    background: #fff; border: 1px solid var(--nx-border); border-radius: 14px; padding: 12px 16px;
}
[data-testid="stExpander"] {
    background: #fff; border: 1px solid var(--nx-border); border-radius: 14px; overflow: hidden;
}
[data-testid="stAlert"] { border-radius: 12px; }
[data-testid="stTextInputRootElement"], [data-baseweb="select"] > div { border-radius: 10px; }
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
    border-radius: 10px; font-weight: 650;
}
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] {
    background: linear-gradient(135deg, #123a5e, #1f4e79);
    border: 0; color: #fff;
    box-shadow: 0 6px 16px rgba(31,78,121,.28);
}
.stButton > button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"]:hover {
    filter: brightness(1.08); color: #fff;
}
button[data-baseweb="tab"] { font-weight: 600; padding: 10px 6px; }
div[data-baseweb="tab-list"] { gap: 18px; }

/* danger button (delete) */
[class*="st-key-nxdanger_"] button {
    background: linear-gradient(135deg, #a3200f, #c8321f) !important;
    border: 0 !important; color: #fff !important;
    box-shadow: 0 6px 16px rgba(180,35,24,.28);
}

[class*="st-key-nxdanger_"] button:disabled { opacity: .4; box-shadow: none; cursor: not-allowed; }

/* sliders */
[data-testid="stSlider"] [role="slider"] { box-shadow: 0 0 0 4px rgba(31,78,121,.16); }
</style>
"""


def inject_theme() -> None:
    """Inject the shared stylesheet. Call from ``app.py`` (every page)."""
    st.markdown(_THEME_CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Small HTML helpers (all user-supplied text is escaped)
# ----------------------------------------------------------------------

def initials(name: str) -> str:
    parts = [p for p in str(name).replace("_", " ").replace(".", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def pill(text: str, kind: str = "") -> str:
    return f'<span class="nx-pill {escape(kind)}">{escape(str(text))}</span>'


def page_header(icon: str, title: str, subtitle: str = "") -> None:
    sub = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="nx-pagehead">
            <div class="nx-pagehead-icon">{icon}</div>
            <div><h1>{escape(title)}</h1>{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_header(icon: str, title: str, subtitle: str = "", right_html: str = "") -> None:
    """Header row used inside a card. ``right_html`` must already be safe HTML."""
    sub = f'<div class="nx-card-sub">{escape(subtitle)}</div>' if subtitle else ""
    right = f'<div class="nx-card-right">{right_html}</div>' if right_html else ""
    st.markdown(
        f"""
        <div class="nx-card-head">
            <div class="nx-card-icon">{icon}</div>
            <div><div class="nx-card-title">{escape(title)}</div>{sub}</div>
            {right}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_grid(items: list[tuple]) -> None:
    """items: (icon, label, value, foot, tone) where tone is '', 'ok' or 'warn'."""
    cells = []
    for icon, label, value, foot, tone in items:
        foot_html = f'<div class="nx-kpi-foot">{escape(str(foot))}</div>' if foot else ""
        cells.append(
            f'<div class="nx-kpi {escape(tone)}">'
            f'<div class="nx-kpi-icon">{icon}</div>'
            f'<div><div class="nx-kpi-label">{escape(str(label))}</div>'
            f'<div class="nx-kpi-value">{escape(str(value))}</div>{foot_html}</div>'
            f"</div>"
        )
    st.markdown(f'<div class="nx-kpis">{"".join(cells)}</div>', unsafe_allow_html=True)


def user_chip(name: str, role_name: str) -> str:
    """Sidebar profile card (safe HTML string)."""
    return (
        '<div class="nx-userchip">'
        f'<div class="nx-avatar {escape(role_name.lower())}">{escape(initials(name))}</div>'
        f'<div><div class="nx-userchip-name">{escape(name)}</div>'
        f'<div class="nx-userchip-role">{escape(role_name)}</div></div>'
        "</div>"
    )


# ----------------------------------------------------------------------
# Sign-in screen stylesheet
# ----------------------------------------------------------------------

_ICON_USER = (
    "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'>"
    "<path d='M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm0 2c-4.4 0-8 2.2-8 5v1h16v-1c0-2.8-3.6-5-8-5z'/></svg>\")"
)
_ICON_LOCK = (
    "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'>"
    "<path d='M17 9h-1V7a4 4 0 0 0-8 0v2H7a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2zM9.5 7a2.5 2.5 0 0 1 5 0v2h-5V7zm3.5 9.2V18h-2v-1.8a2 2 0 1 1 2 0z'/></svg>\")"
)


def login_css() -> str:
    return (
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&display=swap');

html, body, .stApp, .stApp p, .stApp label, .stApp div, .stApp input, .stApp button, .stApp summary {
    font-family: 'Montserrat', 'Segoe UI', system-ui, sans-serif;
}

/* hide app chrome on the sign-in screen */
[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stToolbar"], [data-testid="stAppDeployButton"], footer { display: none !important; }

.stApp {
    background:
        radial-gradient(55% 42% at 50% -4%, rgba(168,34,58,.62) 0%, rgba(168,34,58,0) 72%),
        radial-gradient(75% 55% at 100% 104%, rgba(158,178,255,.95) 0%, rgba(118,124,222,.42) 46%, rgba(118,124,222,0) 78%),
        radial-gradient(50% 55% at -6% 100%, rgba(150,132,166,.65) 0%, rgba(150,132,166,0) 72%),
        radial-gradient(45% 55% at 104% 46%, rgba(44,28,118,.95) 0%, rgba(44,28,118,0) 74%),
        linear-gradient(165deg, #2a1136 0%, #2b1238 42%, #221238 100%);
    background-attachment: fixed;
}
[data-testid="stMainBlockContainer"], .block-container {
    max-width: 500px; padding: 5vh 1rem 2rem;
}

/* --- the glass card (the form itself) ---- */
[data-testid="stForm"] {
    position: relative;
    border: 1px solid rgba(255,255,255,.24);
    border-radius: 38px;
    padding: 2.3rem 2.6rem 2.5rem;
    background:
        radial-gradient(90% 55% at 50% 0%, rgba(176,38,62,.72) 0%, rgba(176,38,62,0) 100%),
        radial-gradient(85% 75% at 100% 100%, rgba(176,198,255,.98) 0%, rgba(124,136,236,.62) 44%, rgba(124,136,236,0) 100%),
        linear-gradient(150deg, #3f2158 0%, #4a2452 48%, #5b4d9c 100%);
    backdrop-filter: blur(24px) saturate(1.25);
    -webkit-backdrop-filter: blur(24px) saturate(1.25);
    box-shadow: 0 34px 90px rgba(12,4,30,.6), inset 0 1px 0 rgba(255,255,255,.28);
}
[data-testid="stForm"] p, [data-testid="stForm"] label, [data-testid="stForm"] span { color: #fff; }

/* --- header: logos + title ---- */
.lg-head { text-align: center; margin-bottom: 1.5rem; }
.lg-badges { display: flex; justify-content: center; align-items: center; gap: 18px; margin-bottom: 1.1rem; }
.lg-badge {
    width: 92px; height: 92px; border-radius: 50%;
    background: rgba(255,255,255,.95);
    display: grid; place-items: center;
    box-shadow: 0 10px 28px rgba(20,6,40,.38), 0 0 0 5px rgba(255,255,255,.16);
}
.lg-badge img { max-width: 76%; max-height: 76%; object-fit: contain; }
.lg-title { color: #fff; font-weight: 700; font-size: 1.42rem; letter-spacing: .03em; line-height: 1.25; }
.lg-sub { color: rgba(255,255,255,.78); font-weight: 300; font-size: .82rem; letter-spacing: .06em; margin-top: 6px; }
.lg-rule { width: 46px; height: 3px; border-radius: 3px; margin: 14px auto 0; background: linear-gradient(90deg, #ffd88a, #ffffff); opacity: .85; }

/* --- underline inputs with leading icon ---- */
[data-testid="stForm"] [data-testid="stTextInput"] { margin-bottom: .55rem; }
[data-testid="stForm"] [data-testid="stTextInputRootElement"] {
    position: relative;
    background: transparent !important;
    border: 0 !important;
    border-bottom: 1.5px solid rgba(255,255,255,.88) !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding-left: 0;
    min-height: 3.1rem;
}
[data-testid="stForm"] [data-testid="stTextInputRootElement"]::before {
    content: ""; position: absolute; left: 4px; top: 50%; width: 20px; height: 20px; margin-top: -10px;
    background-repeat: no-repeat; background-position: center; background-size: contain; opacity: .95;
    pointer-events: none;
}
.st-key-login_user [data-testid="stTextInputRootElement"]::before { background-image: __ICON_USER__; }
.st-key-login_pass [data-testid="stTextInputRootElement"]::before { background-image: __ICON_LOCK__; }

[data-testid="stForm"] [data-testid="stTextInputField"] {
    background: transparent !important;
    color: #fff !important;
    -webkit-text-fill-color: #fff !important;
    font-size: 1.02rem; font-weight: 400; letter-spacing: .05em;
    padding-left: 3rem !important;
    caret-color: #fff;
}
[data-testid="stForm"] [data-testid="stTextInputField"]::placeholder {
    color: rgba(255,255,255,.82) !important; -webkit-text-fill-color: rgba(255,255,255,.82) !important;
    font-weight: 300; letter-spacing: .06em;
}
[data-testid="stForm"] [data-testid="stTextInputRootElement"]:focus-within {
    border-bottom-color: #ffe3a3 !important;
    box-shadow: 0 6px 14px -8px rgba(255,227,163,.9) !important;
}
[data-testid="stForm"] [data-testid="stTextInputRootElement"] button,
[data-testid="stForm"] [data-testid="stTextInputRootElement"] button * {
    color: rgba(255,255,255,.9) !important; background: transparent !important;
}
/* browsers' autofill paints a light box — keep it transparent */
[data-testid="stForm"] input:-webkit-autofill {
    -webkit-box-shadow: 0 0 0 40px rgba(72,40,100,.92) inset !important;
    -webkit-text-fill-color: #fff !important;
}

/* --- remember me / forgot password row ---- */
[data-testid="stForm"] [data-testid="stCheckbox"] label { color: rgba(255,255,255,.88) !important; font-weight: 300; font-size: .9rem; }
[data-testid="stForm"] [data-testid="stCheckbox"] label p { color: rgba(255,255,255,.88) !important; font-weight: 300; font-size: .88rem; }
[data-testid="stForm"] [data-testid="stCheckbox"] label:not([data-baseweb="checkbox"]) > div:first-of-type,
[data-testid="stForm"] [data-testid="stCheckbox"] [data-baseweb="checkbox"] > span:first-of-type {
    background: rgba(30,8,50,.55) !important;
    border: 1.5px solid rgba(255,255,255,.78) !important;
    border-radius: 5px !important;
}
[data-testid="stForm"] [data-testid="stCheckbox"] label:has(input:checked):not([data-baseweb="checkbox"]) > div:first-of-type {
    background: rgba(30,8,50,.9) !important;
}
.lg-forgot { text-align: right; padding-top: .4rem; }
.lg-forgot summary {
    cursor: pointer; list-style: none; font-style: italic; font-weight: 300; font-size: .88rem;
    color: rgba(255,255,255,.85); display: inline-block;
}
.lg-forgot summary::-webkit-details-marker { display: none; }
.lg-forgot summary:hover { color: #fff; text-decoration: underline; }
.lg-forgot details { position: relative; }
.lg-forgot details > div {
    position: absolute; right: 0; top: 28px; z-index: 20; width: 270px;
    padding: 10px 14px; border-radius: 14px; text-align: left;
    background: rgba(38,14,66,.96); border: 1px solid rgba(255,255,255,.25);
    box-shadow: 0 12px 28px rgba(10,2,30,.5);
    color: #fff; font-size: .78rem; font-weight: 400; line-height: 1.5;
}
/* Streamlit's "Press Enter to submit form" hint overlaps the underline inputs */
[data-testid="stForm"] [data-testid="InputInstructions"] { display: none !important; }

/* --- sign-in button ---- */
[data-testid="stForm"] [data-testid="stFormSubmitButton"] > button {
    width: 100%; height: 3.35rem; margin-top: .7rem;
    border: 0 !important; border-radius: 18px;
    background: linear-gradient(105deg, #4f0a30 0%, #3d3a9a 55%, #7a92ee 100%) !important;
    box-shadow: 0 14px 30px rgba(28,10,70,.5), inset 0 1px 0 rgba(255,255,255,.22);
    transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] > button p {
    color: #fff !important; font-weight: 700; letter-spacing: .28em; text-transform: uppercase; font-size: .92rem;
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-1px); filter: brightness(1.12);
    box-shadow: 0 18px 36px rgba(28,10,70,.55), inset 0 1px 0 rgba(255,255,255,.3);
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] > button:active { transform: translateY(0); }

/* --- error message ---- */
[data-testid="stAlert"] {
    background: rgba(255,255,255,.14) !important; border: 1px solid rgba(255,255,255,.35);
    border-radius: 14px; backdrop-filter: blur(10px);
}
[data-testid="stAlert"] * { color: #fff !important; }

.lg-foot { text-align: center; margin-top: 1.4rem; color: rgba(255,255,255,.72); font-size: .76rem; font-weight: 300; letter-spacing: .05em; }
.lg-foot b { font-weight: 600; color: rgba(255,255,255,.9); }
@media (max-width: 520px) {
    [data-testid="stForm"] { padding: 1.8rem 1.4rem 2rem; border-radius: 28px; }
    .lg-badge { width: 78px; height: 78px; }
}
</style>
""".replace("__ICON_USER__", _ICON_USER).replace("__ICON_LOCK__", _ICON_LOCK)
    )


__all__ = [
    "inject_theme",
    "login_css",
    "page_header",
    "card_header",
    "kpi_grid",
    "pill",
    "initials",
    "user_chip",
]
