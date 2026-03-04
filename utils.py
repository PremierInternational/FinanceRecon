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


# Official Definian brand colors (from Brand Style Guide, August 2025)
BRAND_COLORS = {
    "primary_blue": "#0D2C71",    # Definian Blue (Pantone 2748)
    "primary_green": "#00AB63",   # Definian Green (Pantone 3405)
    "midnight": "#02072D",        # Midnight (Pantone 533) — primary dark bg
    "cool_gray": "#D8D7EE",       # Cool Gray (Pantone Cool Gray 1) — primary text on dark
    "dark_gray": "#3C405B",       # Dark Gray — borders/dividers on dark bg
    "white": "#FFFFFF",
    # Tertiary chart colors
    "chart_teal": "#038FBA",
    "chart_sky": "#69D9FA",
    "chart_sage": "#338261",
    "chart_mint": "#99DEC2",
}


def load_svg(path: str) -> str:
    with open(_asset_path(path), "r") as f:
        return f.read()


def apply_global_styles() -> None:
    """Inject the shared CSS that applies to every page."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@300;400;600;700&family=Roboto:wght@300;400;500&family=Roboto+Mono:wght@400;500&display=swap');

        /* ── Official Definian Brand Palette ── */
        :root {
            /* Backgrounds — layered over Midnight */
            --midnight:        #02072D;  /* primary app background */
            --bg-panel:        #06103d;  /* card / panel surface */
            --bg-input:        #091540;  /* input & select fields */
            --bg-hover:        #0f1f55;  /* hover / focus highlight */
            --bg-header:       #0D2C71;  /* topbar (Definian Blue) */

            /* Brand colors */
            --definian-blue:   #0D2C71;
            --definian-green:  #00AB63;

            /* Text */
            --text-primary:    #D8D7EE;  /* Cool Gray — brand specified for dark bg */
            --text-secondary:  #8a8eb8;  /* muted cool gray */
            --text-muted:      #5c6090;

            /* Borders — brand guide specifies Dark Gray #3C405B for dark bg */
            --border:          #3C405B;
            --border-light:    #4a4e6a;

            /* Status */
            --green:           #00AB63;
            --amber:           #f59e0b;
            --red:             #e05252;
        }

        /* ── Base ── */
        .stApp {
            background-color: var(--midnight) !important;
            font-family: 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        .block-container {
            padding-top: 0rem !important;
        }
        .main { background-color: transparent; }

        /* ── Streamlit native header ── */
        header[data-testid="stHeader"],
        div[data-testid="stHeader"] {
            background-color: var(--bg-header) !important;
            border-bottom: 1px solid var(--border) !important;
        }

        /* ── Typography ── */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Titillium Web', sans-serif !important;
            color: var(--text-primary) !important;
        }
        p, div, span, label {
            color: var(--text-primary) !important;
        }

        /* ── Sidebar ── */
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div {
            background-color: var(--bg-panel) !important;
            border-right: 1px solid var(--border) !important;
        }

        /* ── Tabs ── */
        div[data-baseweb="tab-list"] {
            background-color: transparent !important;
            border-bottom: 1px solid var(--border) !important;
            gap: 0 !important;
        }
        button[data-baseweb="tab"] {
            font-family: 'Titillium Web', sans-serif !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            color: var(--text-secondary) !important;
            background-color: transparent !important;
            border: none !important;
            padding: 0.65rem 1.25rem !important;
        }
        button[data-baseweb="tab"]:hover {
            color: var(--text-primary) !important;
            background-color: rgba(60, 64, 91, 0.3) !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--definian-green) !important;
            background-color: transparent !important;
        }
        div[data-baseweb="tab-border"] {
            background-color: var(--definian-green) !important;
            height: 2px !important;
        }
        div[data-baseweb="tab-panel"] {
            padding-top: 1.25rem !important;
            background-color: transparent !important;
        }

        /* ── Inputs (standalone only — not inside select/dropdowns) ── */
        input:not([data-baseweb]) {
            background-color: var(--bg-input) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 5px !important;
        }
        input:not([data-baseweb]):focus {
            border-color: var(--definian-green) !important;
            outline: none !important;
        }
        input::placeholder { color: var(--text-muted) !important; }
        /* Number input specifically */
        div[data-testid="stNumberInput"] input {
            background-color: var(--bg-input) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 5px !important;
        }
        /* Text input specifically */
        div[data-testid="stTextInput"] input {
            background-color: var(--bg-input) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 5px !important;
        }

        /* ── Select / Dropdown ── */
        div[data-baseweb="select"] > div {
            background-color: var(--bg-input) !important;
            border-color: var(--border) !important;
        }
        /* Text and non-interactive children */
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div:not([role="button"]) {
            color: var(--text-primary) !important;
            background-color: transparent !important;
        }
        /* The hidden search input inside select — no border */
        div[data-baseweb="select"] input {
            color: var(--text-primary) !important;
            background-color: transparent !important;
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            outline: none !important;
        }
        /* Chevron / clear button inside select — transparent, no outline oval */
        div[data-baseweb="select"] button,
        div[data-baseweb="select"] [role="button"] {
            background-color: transparent !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }
        /* SVG icons inside select (chevron arrow) */
        div[data-baseweb="select"] svg {
            fill: var(--text-secondary) !important;
            overflow: visible !important;
        }

        /* ── Multiselect tags ── */
        span[data-baseweb="tag"] {
            background-color: rgba(0, 171, 99, 0.15) !important;
            border: 1px solid rgba(0, 171, 99, 0.45) !important;
        }
        span[data-baseweb="tag"] span {
            color: var(--definian-green) !important;
        }
        /* Tag remove (×) button */
        span[data-baseweb="tag"] button {
            background-color: transparent !important;
            border: none !important;
            outline: none !important;
        }
        span[data-baseweb="tag"] svg {
            fill: var(--definian-green) !important;
        }

        /* ── Dropdown list / popover ── */
        div[data-baseweb="popover"],
        div[data-baseweb="menu"],
        ul[role="listbox"],
        div[role="listbox"] {
            background-color: var(--bg-panel) !important;
            border: 1px solid var(--border) !important;
            border-radius: 6px !important;
        }
        div[data-baseweb="popover"] *,
        div[data-baseweb="menu"] *,
        ul[role="listbox"] *,
        div[role="listbox"] *,
        div[role="option"] div,
        div[role="option"] span {
            color: var(--text-primary) !important;
            background-color: transparent !important;
        }
        li[role="option"]:hover,
        div[role="option"]:hover {
            background-color: var(--bg-hover) !important;
        }

        /* ── File uploader ── */
        div[data-testid="stFileUploader"],
        div[data-testid="stFileUploaderDropzone"],
        div[data-testid="stFileUploaderFile"] {
            background-color: var(--bg-input) !important;
            border: 1px solid var(--border) !important;
            border-radius: 6px !important;
        }
        div[data-testid="stFileUploader"] *,
        div[data-testid="stFileUploaderDropzone"] *,
        div[data-testid="stFileUploaderFile"] * {
            color: var(--text-secondary) !important;
        }
        /* File remove button — transparent so the × icon is visible, not a green block */
        div[data-testid="stFileUploaderFile"] button {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 2px !important;
        }
        div[data-testid="stFileUploaderFile"] button svg,
        div[data-testid="stFileUploaderFile"] button svg path {
            fill: var(--text-secondary) !important;
        }

        /* ── Tooltip ── */
        [data-testid="stTooltipContent"],
        [data-testid="stTooltipContent"] p,
        [data-testid="stTooltipContent"] div,
        [data-testid="stTooltipContent"] span {
            background-color: var(--bg-panel) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border) !important;
        }

        /* ── Buttons — Definian Green as primary action ── */
        /* Target only labelled action buttons, not icon/minimal buttons */
        .stButton > button[kind="primary"],
        .stButton > button[kind="secondary"],
        .stButton > button:not([data-testid="stBaseButton-minimal"]) {
            background-color: var(--definian-green) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 5px !important;
            padding: 0.5rem 1.5rem !important;
            font-family: 'Titillium Web', sans-serif !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            letter-spacing: 0.5px !important;
            text-transform: uppercase !important;
            transition: background-color 0.15s ease !important;
        }
        .stButton > button:not([data-testid="stBaseButton-minimal"]):hover {
            background-color: #00c870 !important;
        }
        /* Minimal / icon buttons — keep transparent */
        button[data-testid="stBaseButton-minimal"] {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        .stDownloadButton > button {
            background-color: var(--bg-panel) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 5px !important;
            font-family: 'Titillium Web', sans-serif !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px !important;
        }
        .stDownloadButton > button:hover {
            background-color: var(--bg-hover) !important;
            border-color: var(--border-light) !important;
        }

        /* ── Widget labels ── */
        .stSelectbox label,
        .stMultiSelect label,
        .stNumberInput label,
        .stCheckbox label,
        .stTextInput label {
            color: var(--text-secondary) !important;
            font-family: 'Titillium Web', sans-serif !important;
            font-size: 10px !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.8px !important;
        }
        [data-testid="stWidgetLabel"] button svg path {
            fill: var(--text-secondary) !important;
        }
        button[data-testid="stBaseButton-minimal"] svg path {
            fill: var(--text-secondary) !important;
        }

        /* ── Alerts ── */
        .stSuccess {
            background-color: rgba(0, 171, 99, 0.10) !important;
            border: 1px solid rgba(0, 171, 99, 0.40) !important;
        }
        .stSuccess * { color: #00AB63 !important; }
        .stInfo {
            background-color: rgba(13, 44, 113, 0.30) !important;
            border: 1px solid rgba(13, 44, 113, 0.60) !important;
        }
        .stInfo * { color: var(--text-secondary) !important; }
        .stError {
            background-color: rgba(224, 82, 82, 0.10) !important;
            border: 1px solid rgba(224, 82, 82, 0.40) !important;
        }
        .stError * { color: var(--red) !important; }
        .stWarning {
            background-color: rgba(245, 158, 11, 0.10) !important;
            border: 1px solid rgba(245, 158, 11, 0.40) !important;
        }
        .stWarning * { color: var(--amber) !important; }

        /* ── Misc ── */
        .stMarkdown { color: var(--text-primary) !important; }
        pre {
            background-color: var(--bg-panel) !important;
            border: 1px solid var(--border) !important;
            color: var(--text-primary) !important;
        }
        hr { border-color: var(--border) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: str) -> None:
    """Render the branded page header with logo and page title."""
    logo_svg = load_svg("assets/modernization.svg")
    background_svg = load_svg("assets/Trapz.svg")
    st.markdown(
        f"""
        <style>
        .definian-header-bg {{
            position: fixed;
            top: 0;
            right: -5vw;
            height: 60px;
            width: auto;
            z-index: 0;
            opacity: 0.18;
            pointer-events: none;
            transform-origin: top right;
            filter: saturate(1.5) brightness(1.5);
        }}
        </style>
        <div style="background-color: #0D2C71;
                    padding: 0 1.5rem;
                    height: 56px;
                    margin: -1rem -1rem 1.5rem -1rem;
                    display: flex; align-items: center; gap: 1.25rem;
                    border-bottom: 2px solid #00AB63;
                    position: relative; overflow: hidden;">
            <div class="definian-header-bg">
                {background_svg}
            </div>
            <div style="display: flex; align-items: center; gap: 10px;
                        padding-right: 1.25rem;
                        border-right: 1px solid rgba(216,215,238,0.25);
                        height: 100%; z-index: 1;">
                <div style="width: 30px; display: flex; align-items: center;">
                    {logo_svg}
                </div>
            </div>
            <h1 style="margin: 0; z-index: 1;
                       font-family: 'Titillium Web', sans-serif;
                       font-size: 16px; font-weight: 700;
                       color: #D8D7EE; letter-spacing: 1px;
                       text-transform: uppercase; flex-grow: 1;">
                {title}
            </h1>
            <span style="z-index: 1;
                         font-family: 'Titillium Web', sans-serif;
                         font-size: 10px; font-weight: 600;
                         color: rgba(216,215,238,0.45);
                         letter-spacing: 1.5px; text-transform: uppercase;">
                Definian
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
