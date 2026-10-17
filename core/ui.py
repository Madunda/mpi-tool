from __future__ import annotations

import base64
import io
from pathlib import Path

import streamlit as st
from PIL import Image, UnidentifiedImageError


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --nmpi-navy: #102a43;
            --nmpi-blue: #1f4e79;
            --nmpi-gold: #c89b3c;
            --nmpi-red: #b42318;
            --nmpi-ink: #172b4d;
            --nmpi-muted: #667085;
            --nmpi-bg: #f5f7fa;
            --nmpi-card: #ffffff;
            --nmpi-border: #d9e2ec;
        }

        .stApp {
            background: var(--nmpi-bg);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #102a43 0%, #163b5c 100%);
            border-right: 1px solid rgba(255,255,255,.10);
        }

        [data-testid="stSidebar"] * {
            color: #f8fafc;
        }

        [data-testid="stSidebarNav"] a {
            border-radius: 10px;
            margin: 3px 8px;
            transition: all .15s ease;
        }

        [data-testid="stSidebarNav"] a:hover {
            background: rgba(255,255,255,.10);
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: rgba(200,155,60,.18);
            border-left: 3px solid var(--nmpi-gold);
        }

        .nmpi-brand {
            display: grid;
            grid-template-columns: 92px 1fr 92px;
            align-items: center;
            gap: 22px;
            padding: 20px 28px;
            margin-bottom: 10px;
            background: var(--nmpi-card);
            border: 1px solid var(--nmpi-border);
            border-radius: 16px;
            box-shadow: 0 4px 18px rgba(16,42,67,.06);
        }

        .nmpi-brand-logo {
            width: 92px;
            height: 92px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .nmpi-brand-logo img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }

        .nmpi-brand-logo--empty {
            width: 92px;
            height: 92px;
            border: 1px dashed var(--nmpi-border);
            border-radius: 8px;
            color: #98A2B3;
            font-size: .62rem;
            text-align: center;
            line-height: 92px;
            margin: 0 auto;
        }

        .nmpi-brand-center {
            text-align: center;
            padding: 0 6px;
        }

        .nmpi-brand h1 {
            margin: 0;
            color: var(--nmpi-navy);
            font-size: 1.55rem;
            font-weight: 750;
            line-height: 1.25;
            letter-spacing: -.01em;
        }

        .nmpi-brand p {
            margin: 5px 0 0;
            color: var(--nmpi-muted);
            font-size: .9rem;
        }

        @media (max-width: 700px) {
            .nmpi-brand {
                grid-template-columns: 52px 1fr 52px;
                padding: 14px 16px;
                gap: 12px;
            }
            .nmpi-brand-logo,
            .nmpi-brand-logo--empty {
                width: 52px;
                height: 52px;
                line-height: 52px;
            }
            .nmpi-brand h1 { font-size: 1.1rem; }
            .nmpi-brand p { font-size: .78rem; }
        }

        .nmpi-hero {
            padding: 34px 38px;
            border-radius: 20px;
            color: white;
            background: linear-gradient(135deg, #102a43 0%, #1f4e79 68%, #284f70 100%);
            box-shadow: 0 12px 35px rgba(16,42,67,.16);
            margin: 10px 0 24px;
        }

        .nmpi-hero h1 {
            margin: 0 0 8px;
            font-size: 2.2rem;
            letter-spacing: -.02em;
        }

        .nmpi-hero p {
            margin: 0;
            max-width: 850px;
            color: #e7eef5;
            line-height: 1.65;
        }

        .nmpi-section {
            color: var(--nmpi-navy);
            font-size: 1.18rem;
            font-weight: 750;
            margin: 26px 0 10px;
        }

        .nmpi-card {
            background: var(--nmpi-card);
            border: 1px solid var(--nmpi-border);
            border-radius: 14px;
            padding: 20px;
            box-shadow: 0 3px 12px rgba(16,42,67,.05);
            height: 100%;
        }

        .nmpi-card h3 {
            color: var(--nmpi-navy);
            margin-top: 0;
            font-size: 1.05rem;
        }

        .nmpi-card p {
            color: #475467;
            line-height: 1.6;
            margin-bottom: 0;
        }

        .nmpi-step {
            display: flex;
            gap: 14px;
            padding: 14px 0;
            border-bottom: 1px solid #e8edf2;
        }

        .nmpi-step:last-child { border-bottom: 0; }

        .nmpi-number {
            min-width: 32px;
            height: 32px;
            display: grid;
            place-items: center;
            border-radius: 50%;
            background: #eaf0f6;
            color: var(--nmpi-blue);
            font-weight: 800;
        }

        .nmpi-step-title {
            font-weight: 750;
            color: var(--nmpi-ink);
            margin-bottom: 3px;
        }

        .nmpi-step-body {
            color: #475467;
            line-height: 1.55;
            font-size: .94rem;
        }

        .nmpi-note {
            border-left: 4px solid var(--nmpi-gold);
            background: #fffaf0;
            padding: 13px 16px;
            border-radius: 8px;
            color: #594214;
        }

        .nmpi-footer {
            text-align: center;
            color: #7b8794;
            font-size: .82rem;
            padding: 28px 0 8px;
        }

        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid var(--nmpi-border);
            padding: 12px 15px;
            border-radius: 12px;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 9px;
            font-weight: 650;
            border: 1px solid #b9c7d6;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: var(--nmpi-blue);
            color: var(--nmpi-blue);
        }

        .nmpi-divider {
            height: 1px;
            background: #dfe6ed;
            margin: 22px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def asset_path(*filenames: str) -> Path | None:
    """Return the first candidate filename that exists on disk (any size).

    Validity (readable as an image) is checked separately in
    ``_safe_image_data_uri`` — a file that exists but is corrupt or
    empty is still "found" here, then gracefully falls back to a
    placeholder instead of a broken image icon.
    """
    for filename in filenames:
        path = ASSETS / filename
        if path.is_file():
            return path
    return None


@st.cache_data(show_spinner=False)
def _safe_image_data_uri(path_str: str) -> str | None:
    """Return a base64 data URI for a valid image, or None if the file
    is missing, empty, or corrupted (e.g. PIL.UnidentifiedImageError)."""
    path = Path(path_str)
    if not path.is_file() or path.stat().st_size == 0:
        return None
    try:
        data = path.read_bytes()
        img = Image.open(io.BytesIO(data))
        img.verify()
        fmt = (Image.open(io.BytesIO(data)).format or "PNG").lower()
    except (UnidentifiedImageError, OSError, ValueError):
        return None
    mime = "jpeg" if fmt in ("jpg", "jpeg") else fmt
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:image/{mime};base64,{encoded}"


def _brand_logo_html(filenames: tuple[str, ...], alt_label: str) -> str:
    """Render one logo cell — a real image if valid, otherwise a neat
    placeholder box so the header stays balanced either way."""
    path = asset_path(*filenames)
    data_uri = _safe_image_data_uri(str(path)) if path else None
    if data_uri:
        return f'<div class="nmpi-brand-logo"><img src="{data_uri}" alt="{alt_label}"></div>'
    return f'<div class="nmpi-brand-logo nmpi-brand-logo--empty">{alt_label}</div>'


def render_brand() -> None:
    inject_global_css()

    left_html = _brand_logo_html(("ngao.png", "logo.png"), "Ngao")
    right_html = _brand_logo_html(("nbs.png", "nbs_logo.png", "logo_right.png"), "NBS")

    st.markdown(
        f"""
        <div class="nmpi-brand">
            {left_html}
            <div class="nmpi-brand-center">
                <h1>NMPI Automation Tool</h1>
                <p>National Multidimensional Poverty Index analysis platform</p>
            </div>
            {right_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        '<div class="nmpi-footer">NMPI Automation Tool · Alkire-Foster methodology · National Bureau of Statistics</div>',
        unsafe_allow_html=True,
    )