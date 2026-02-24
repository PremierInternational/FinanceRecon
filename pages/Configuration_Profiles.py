"""Configuration Profiles management page.

Lists all saved reconciliation configuration profiles and allows deletion.
Profiles are saved from the main Reconciliation page.
"""

import json
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import apply_global_styles, render_header

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

apply_global_styles()
render_header("Configuration Profiles")

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
