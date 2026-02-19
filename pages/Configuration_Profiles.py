"""Configuration Profiles management page.

Lists all saved reconciliation configuration profiles and allows deletion.
Profiles are saved from the main Reconciliation page.
"""

import json
import os

import streamlit as st

PROFILES_FILE = "config_profiles.json"


def load_profiles() -> dict:
    if not os.path.exists(PROFILES_FILE):
        return {}
    with open(PROFILES_FILE) as f:
        return json.load(f)


def delete_profile(name: str) -> None:
    profiles = load_profiles()
    profiles.pop(name, None)
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)


st.set_page_config(page_title="Configuration Profiles", layout="wide")

brand_colors = {
    "primary_blue": "#0D2C71",
    "primary_green": "#00AB63",
    "midnight": "#02072D",
    "white": "#FFFFFF",
}

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {brand_colors['midnight']};
    }}
    div[data-testid="stHeader"] {{
        background-color: {brand_colors['midnight']};
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {brand_colors['white']} !important;
    }}
    p, div, span, label {{
        color: {brand_colors['white']} !important;
    }}
    .stMarkdown {{
        color: {brand_colors['white']} !important;
    }}
    .stButton>button {{
        background-color: {brand_colors['primary_blue']};
        color: {brand_colors['white']};
        border: 1px solid {brand_colors['white']};
        border-radius: 4px;
        padding: 0.25rem 0.75rem;
        font-weight: bold;
    }}
    .stButton>button:hover {{
        background-color: #c0392b;
        border-color: #c0392b;
    }}
    .stInfo {{
        color: {brand_colors['white']} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("## Configuration Profiles")
st.markdown("Saved profiles can be loaded from the **Reconciliation** page via the Load Profile dropdown.")

profiles = load_profiles()

if not profiles:
    st.info("No configuration profiles saved yet. Go to the Reconciliation page, configure a comparison, and click Save.")
else:
    st.markdown(f"**{len(profiles)} profile(s) saved**")
    st.markdown("---")

    for name, cfg in profiles.items():
        col_info, col_delete = st.columns([5, 1])

        with col_info:
            with st.expander(f"**{name}**"):
                st.markdown(
                    f"**Match keys (first file):** "
                    f"{', '.join(cfg.get('match_keys_first', [])) or '—'}"
                )
                st.markdown(
                    f"**Match keys (second file):** "
                    f"{', '.join(cfg.get('match_keys_second', [])) or '—'}"
                )
                st.markdown(f"**Compare column (first file):** {cfg.get('compare_col_first', '—')}")
                st.markdown(f"**Compare column (second file):** {cfg.get('compare_col_second', '—')}")
                tol_type = cfg.get('tolerance_type', 'None')
                tol_val = cfg.get('tolerance_value')
                tol_display = tol_type if tol_type == 'None' else f"{tol_type} {tol_val}"
                st.markdown(f"**Tolerance:** {tol_display}")

        with col_delete:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            if st.button("Delete", key=f"delete_{name}"):
                delete_profile(name)
                st.rerun()
