"""Shared UI utilities for all pages."""

import os
import sys

import streamlit as st


def _asset_path(relative: str) -> str:
    """Resolve a path relative to the bundle/script root.

    Works in two contexts:
    - Normal development:  relative to this file's directory
    - cx_Freeze bundle:    relative to the directory containing the .exe
    """
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)

BRAND_COLORS = {
    "primary_blue": "#0D2C71",
    "primary_green": "#00AB63",
    "midnight": "#02072D",
    "cool_gray": "#D8D7EE",
    "white": "#FFFFFF",
}


def load_svg(path: str) -> str:
    with open(_asset_path(path), "r") as f:
        return f.read()


def apply_global_styles() -> None:
    """Inject the shared CSS that applies to every page."""
    c = BRAND_COLORS
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {c['midnight']};
            background-attachment: fixed;
        }}
        .block-container {{
            padding-top: 0rem !important;
        }}
        /* Hide / recolour the native Streamlit top bar */
        header[data-testid="stHeader"],
        div[data-testid="stHeader"] {{
            background-color: {c['midnight']} !important;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {c['white']} !important;
        }}
        p, div, span, label {{
            color: {c['white']} !important;
        }}
        /* Sidebar navigation background */
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div {{
            background-color: #3C405B !important;
        }}
        /* Dropdowns and selects - force black text on white backgrounds */
        div[data-baseweb="select"] *,
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div,
        div[data-baseweb="select"] input {{
            color: #000000 !important;
        }}
        div[data-baseweb="select"] > div {{
            background-color: #ffffff !important;
        }}
        /* Multiselect tags */
        span[data-baseweb="tag"],
        span[data-baseweb="tag"] *,
        span[data-baseweb="tag"] span {{
            color: #000000 !important;
        }}
        /* Dropdown option list */
        div[role="listbox"] *,
        div[role="listbox"] div,
        div[role="option"] div,
        div[role="option"] span {{
            color: #000000 !important;
        }}
        input {{
            color: #000000 !important;
            background-color: {c['white']};
        }}
        .uploadedFile {{
            background-color: {c['white']};
            color: #000000 !important;
        }}
        .stMarkdown {{
            color: {c['white']} !important;
        }}
        pre {{
            color: {c['white']} !important;
            background-color: rgba(255, 255, 255, 0.1) !important;
        }}
        [data-testid="stWidgetLabel"] button svg path {{
            fill: {c['white']} !important;
        }}
        button[data-testid="stBaseButton-minimal"] svg path {{
            fill: {c['white']} !important;
        }}
        [data-testid="stTooltipContent"],
        [data-testid="stTooltipContent"] p,
        [data-testid="stTooltipContent"] div,
        [data-testid="stTooltipContent"] span {{
            color: #000000 !important;
            background-color: {c['white']} !important;
        }}
        .stButton>button {{
            background-color: {c['primary_blue']};
            color: {c['white']};
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: bold;
        }}
        .stButton>button:hover {{
            background-color: {c['primary_green']};
        }}
        .stDownloadButton>button {{
            background-color: {c['primary_blue']};
            color: {c['white']};
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: bold;
        }}
        .stDownloadButton>button:hover {{
            background-color: {c['primary_green']};
        }}
        .stSelectbox label, .stMultiSelect label, .stNumberInput label, .stCheckbox label {{
            color: {c['white']} !important;
        }}
        .stSuccess, .stInfo {{
            color: {c['white']} !important;
        }}
        /* File uploader — keep its internal text readable (dark on light bg) */
        .main {{
            background-color: transparent;
        }}
        div[data-testid="stFileUploader"],
        div[data-testid="stFileUploaderDropzone"],
        div[data-testid="stFileUploaderFile"] {{
            background-color: {c['white']} !important;
            border-radius: 4px;
        }}
        div[data-testid="stFileUploader"] *,
        div[data-testid="stFileUploaderDropzone"] *,
        div[data-testid="stFileUploaderFile"] * {{
            color: #000000 !important;
        }}
        /* Dropdown open list / popover — white background, black text */
        div[data-baseweb="popover"],
        div[data-baseweb="popover"] *,
        div[data-baseweb="menu"],
        div[data-baseweb="menu"] *,
        ul[role="listbox"],
        ul[role="listbox"] * {{
            background-color: #ffffff !important;
            color: #000000 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: str) -> None:
    """Render the branded page header with logo, background graphic, and page title."""
    logo_svg = load_svg("assets/modernization.svg")
    background_svg = load_svg("assets/Trapz.svg")
    c = BRAND_COLORS
    st.markdown(
        f"""
        <style>
        .right-bg {{
            position: fixed;
            top: -30vh;
            right: -5vw;
            height: 100vh;
            width: auto;
            z-index: 0;
            opacity: 0.45;
            pointer-events: none;
            transform: scale(2);
            transform-origin: top right;
            filter: saturate(3) brightness(1.1);
        }}
        </style>
        <div style="background-color: {c['midnight']}; padding: 1.5rem;
                    margin: -1rem -1rem 2rem -1rem;
                    display: flex; align-items: center; gap: 2rem;">
            <div style="text-align: center; width: 75px;">
                {logo_svg}
            </div>
            <div class="right-bg">
                {background_svg}
            </div>
            <h1 style="margin: 0; color: {c['white']}; flex-grow: 1;">{title}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
