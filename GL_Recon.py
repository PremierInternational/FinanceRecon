"""Finance reconciliation utility with a Streamlit web UI.

This module lets users upload Excel files, configure comparison options,
and download reconciliation results. The resulting comparison is written
to an Excel file and displayed on screen.
"""

import base64
import json
import os
from dataclasses import dataclass
from io import BytesIO

import anthropic
import pandas as pd
import streamlit as st
from openpyxl import load_workbook

PROFILES_FILE = "config_profiles.json"


@dataclass
class ComparisonResult:
    """Simple container for comparison output."""

    merged: pd.DataFrame
    summary_text: str


def load_profiles() -> dict:
    """Return all saved configuration profiles from disk."""
    if not os.path.exists(PROFILES_FILE):
        return {}
    with open(PROFILES_FILE) as f:
        return json.load(f)


def save_profile(name: str, config: dict) -> None:
    """Persist a named configuration profile to disk."""
    profiles = load_profiles()
    profiles[name] = config
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)


def delete_profile(name: str) -> None:
    """Remove a named configuration profile from disk."""
    profiles = load_profiles()
    profiles.pop(name, None)
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)


def compare_data(
    legacy: pd.DataFrame,
    converted: pd.DataFrame,
    pk_legacy: list[str],
    pk_converted: list[str],
    match_col_legacy: str,
    match_col_converted: str,
    output_file: str | None = None,
    tolerance_type: str | None = None,
    tolerance_value: float | None = None,
    distinct_list: bool = True,
) -> ComparisonResult:
    """Compare two dataframes and return a summary."""

    def _unique_key_name() -> str:
        base = "_comparison_key"
        key_name = base
        counter = 1
        while key_name in legacy.columns or key_name in converted.columns:
            key_name = f"{base}_{counter}"
            counter += 1
        return key_name

    def _build_comparison_key(data: pd.DataFrame, columns: list[str]) -> pd.Series:
        parts = data[columns].fillna("").astype(str)
        return parts.apply(lambda row: " | ".join(value.strip() for value in row), axis=1)

    comparison_key = _unique_key_name()
    legacy = legacy.copy()
    converted = converted.copy()
    legacy_columns = set(legacy.columns)
    converted_columns = set(converted.columns)
    legacy[comparison_key] = _build_comparison_key(legacy, pk_legacy)
    converted[comparison_key] = _build_comparison_key(converted, pk_converted)

    if distinct_list:
        legacy = (
            legacy.groupby(comparison_key, dropna=False)
            .agg({match_col_legacy: "sum", **{col: "first" for col in pk_legacy}})
            .reset_index()
        )
        converted = (
            converted.groupby(comparison_key, dropna=False)
            .agg({match_col_converted: "sum", **{col: "first" for col in pk_converted}})
            .reset_index()
        )

    merged_df = pd.merge(
        legacy,
        converted,
        on=comparison_key,
        suffixes=("_legacy", "_converted"),
        how="outer",
    )
    merged_df.rename(columns={comparison_key: "Comparison Key"}, inplace=True)

    legacy_value_column = (
        f"{match_col_legacy}_legacy" if f"{match_col_legacy}_legacy" in merged_df.columns else match_col_legacy
    )
    converted_value_column = (
        f"{match_col_converted}_converted"
        if f"{match_col_converted}_converted" in merged_df.columns
        else match_col_converted
    )

    def _difference(row: pd.Series) -> bool:
        legacy_val = row.get(legacy_value_column)
        conv_val = row.get(converted_value_column)
        if pd.isna(legacy_val) or pd.isna(conv_val):
            return True
        if tolerance_type == "Dollar ($)":
            if tolerance_value is None:
                return legacy_val != conv_val
            return abs(legacy_val - conv_val) > tolerance_value
        if tolerance_type == "Percentage (%)":
            if tolerance_value is None or legacy_val == 0:
                return legacy_val != conv_val
            return abs((legacy_val - conv_val) / legacy_val) > tolerance_value
        return legacy_val != conv_val

    merged_df["Difference"] = merged_df.apply(_difference, axis=1)
    merged_df["Dollar Difference"] = merged_df.apply(
        lambda row: (
            (0 if pd.isna(row.get(legacy_value_column)) else row.get(legacy_value_column))
            - (0 if pd.isna(row.get(converted_value_column)) else row.get(converted_value_column))
        ),
        axis=1,
    )
    merged_df["Percentage Difference"] = merged_df.apply(
        lambda row: (
            float("nan")
            if pd.isna(row.get(legacy_value_column)) or pd.isna(row.get(converted_value_column))
            else (
                abs(row.get(legacy_value_column) - row.get(converted_value_column))
                / abs(row.get(legacy_value_column))
                if row.get(legacy_value_column) != 0
                else float("nan")
            )
        ),
        axis=1,
    )

    def _should_drop_match_column(column_name: str) -> bool:
        if column_name in pk_legacy or column_name in pk_converted:
            return True
        if column_name.endswith("_legacy") and column_name[: -len("_legacy")] in pk_legacy:
            return True
        if column_name.endswith("_converted") and column_name[: -len("_converted")] in pk_converted:
            return True
        return False

    drop_columns = [col for col in merged_df.columns if _should_drop_match_column(col)]
    if drop_columns:
        merged_df.drop(columns=drop_columns, inplace=True)

    rename_columns: dict[str, str] = {}
    for column in merged_df.columns:
        if column in {"Comparison Key", "Difference", "Dollar Difference", "Percentage Difference"}:
            continue
        if column.endswith("_legacy"):
            base = column[: -len("_legacy")]
            rename_columns[column] = f"{base} (First)"
        elif column.endswith("_converted"):
            base = column[: -len("_converted")]
            rename_columns[column] = f"{base} (Second)"
        elif column in legacy_columns and column not in converted_columns:
            rename_columns[column] = f"{column} (First)"
        elif column in converted_columns and column not in legacy_columns:
            rename_columns[column] = f"{column} (Second)"

    if rename_columns:
        merged_df.rename(columns=rename_columns, inplace=True)

    total_records = len(merged_df)
    matched_records = len(merged_df[~merged_df["Difference"]])
    matched_percentage = (matched_records / total_records) * 100 if total_records else 0

    summary_lines = [
        f"Total records: {total_records}",
        f"Matched records: {matched_records}",
        f"Match percentage: {matched_percentage:.2f}%",
    ]

    if output_file:
        merged_df.to_excel(output_file, index=False)
        _format_output(output_file, merged_df)

    return ComparisonResult(merged_df, "\n".join(summary_lines))


def _format_output(output_file: str, merged_df: pd.DataFrame) -> None:
    workbook = load_workbook(output_file)
    worksheet = workbook.active
    header_map = {header: idx + 1 for idx, header in enumerate(merged_df.columns)}
    dollar_column = header_map.get("Dollar Difference")
    percent_column = header_map.get("Percentage Difference")

    if dollar_column:
        for row_idx in range(2, worksheet.max_row + 1):
            worksheet.cell(row=row_idx, column=dollar_column).number_format = "$#,##0.00"

    if percent_column:
        for row_idx in range(2, worksheet.max_row + 1):
            worksheet.cell(row=row_idx, column=percent_column).number_format = "0.00%"

    workbook.save(output_file)


def load_svg(path):
    with open(path, "r") as f:
        return f.read()


def query_results_with_nlq(df: pd.DataFrame, question: str) -> tuple[pd.DataFrame | None, str]:
    """Use Claude to interpret a natural language question and filter or summarise the dataframe."""
    schema = "\n".join(f"- {col} (dtype: {df[col].dtype})" for col in df.columns)
    sample = df.head(5).to_string(index=False)

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=(
            "You are a data analyst assistant helping users query a pandas DataFrame of "
            "financial reconciliation results. When given a question, respond in one of two ways:\n\n"
            "1. If the question can be answered by filtering rows, respond with ONLY a valid "
            "Python boolean expression using the variable `df` "
            "(e.g. `df['Difference'] == True` or `df['Percentage Difference'].abs() > 0.05`). "
            "Do not include any explanation \u2014 just the expression.\n\n"
            "2. If the question asks for a count, summary, or cannot be answered by a simple "
            "row filter, respond with a plain-English answer prefixed with exactly 'ANSWER: '.\n\n"
            "Column names must match the schema exactly, including spaces and capitalisation."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"DataFrame schema:\n{schema}\n\n"
                    f"Sample data (first 5 rows):\n{sample}\n\n"
                    f"Question: {question}"
                ),
            }
        ],
    )

    response = message.content[0].text.strip()

    if response.startswith("ANSWER:"):
        return None, response[7:].strip()

    try:
        mask = eval(response, {"__builtins__": {}}, {"df": df, "pd": pd})  # noqa: S307
        filtered = df[mask].reset_index(drop=True)
        return filtered, f"Found {len(filtered)} record(s) matching your query."
    except Exception as exc:
        return None, f"I couldn't apply that filter: {exc}"


#def get_base64_svg(path):
#    with open(path, "rb") as f:
#        return base64.b64encode(f.read()).decode()
# ----------------------------- Streamlit UI ----------------------------- #
def main():
    """Main Streamlit application."""

    st.set_page_config(page_title="Reconciliation", layout="wide")

    brand_colors = {
        "primary_blue": "#0D2C71",
        "primary_green": "#00AB63",
        "midnight": "#02072D",
        "cool_gray": "#D8D7EE",
        "white": "#FFFFFF",
    }

    logo_svg = load_svg("assets/modernization.svg")

    if "ANTHROPIC_API_KEY" in st.secrets:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {brand_colors['primary_blue']};
            background-attachment: fixed;
        }}
        .right-bg {{
            position: fixed;
            top: 0;
            right: 0;
            height: 100vh;
            width: 50vw;
            display: flex;
            justify-content: flex-end;
            align-items: center;
            pointer-events: none;
            z-index: -1;
            opacity: 0.25;
        }}
        .right-bg svg {{
            height: 80vh;
            width: auto;
        }}
        .main {{
            background-color: transparent;
        }}
        div[data-testid="stFileUploader"] label {{
            color: black !important;
        }}
        div[data-testid="stFileUploader"] span {{
            color: black !important;
        }}
        div[data-testid="stFileUploader"] button {{
            color: black !important;
        }}
        div[data-testid="stHeader"] {{
            background-color: {brand_colors['primary_blue']};
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {brand_colors['white']} !important;
        }}
        h1 {{
            background-color: {brand_colors['primary_blue']};
            padding: 1rem;
            margin: -1rem -1rem 1rem -1rem;
        }}
        p, div, span, label {{
            color: {brand_colors['white']} !important;
        }}
        div[data-baseweb="select"] > div {{
            color: #000000 !important;
        }}
        input {{
            color: #000000 !important;
            background-color: {brand_colors['white']};
        }}
        .uploadedFile {{
            background-color: {brand_colors['white']};
            color: #000000 !important;
        }}
        div[role="listbox"] div {{
            color: #000000 !important;
        }}
        .stMarkdown {{
            color: {brand_colors['white']} !important;
        }}
        pre {{
            color: {brand_colors['white']} !important;
            background-color: rgba(255, 255, 255, 0.1) !important;
        }}
        .stButton>button {{
            background-color: {brand_colors['primary_blue']};
            color: {brand_colors['white']};
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: bold;
        }}
        .stButton>button:hover {{
            background-color: {brand_colors['primary_green']};
        }}
        .stDownloadButton>button {{
            background-color: {brand_colors['primary_blue']};
            color: {brand_colors['white']};
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: bold;
        }}
        .stDownloadButton>button:hover {{
            background-color: {brand_colors['primary_green']};
        }}
        .stSelectbox label, .stMultiSelect label, .stNumberInput label, .stCheckbox label {{
            color: {brand_colors['white']} !important;
        }}
        div[data-testid="stDataFrame"] {{
            height: 600px !important;
        }}
        .stSuccess, .stInfo {{
            color: {brand_colors['white']} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    with open("assets/Trapz.svg", "r") as f:
        background_svg = f.read()

    st.markdown(
        f"""
        <div style="background-color: {brand_colors['primary_blue']}; padding: 1.5rem; margin: -1rem -1rem 2rem -1rem; display: flex; align-items: center; gap: 2rem;">
            <div style="text-align: center; width: 75px;">
                {logo_svg}
            </div>
            <div class="right-bg">
                {background_svg}
            </div>
            <h1 style="margin: 0; color: {brand_colors['white']}; flex-grow: 1;">Reconciliation</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Initialize session state
    if "first_df" not in st.session_state:
        st.session_state.first_df = None
    if "second_df" not in st.session_state:
        st.session_state.second_df = None
    if "result" not in st.session_state:
        st.session_state.result = None
    if "nlq_result" not in st.session_state:
        st.session_state.nlq_result = None
    if "pending_profile" not in st.session_state:
        st.session_state.pending_profile = None  # profile config waiting to be applied

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Upload Files")
        first_file = st.file_uploader(
            "Select first file",
            type=["xlsx", "xls"],
            key="first_file",
            help="Upload the first Excel file to compare",
        )
        if first_file:
            try:
                st.session_state.first_df = pd.read_excel(first_file)
                st.success(f"✓ Loaded: {first_file.name}")
            except Exception as e:
                st.error(f"Error reading first file: {e}")
                st.session_state.first_df = None

        second_file = st.file_uploader(
            "Select second file",
            type=["xlsx", "xls"],
            key="second_file",
            help="Upload the second Excel file to compare",
        )
        if second_file:
            try:
                st.session_state.second_df = pd.read_excel(second_file)
                st.success(f"✓ Loaded: {second_file.name}")
            except Exception as e:
                st.error(f"Error reading second file: {e}")
                st.session_state.second_df = None

    with col2:
        st.markdown("### Configure")

        if st.session_state.first_df is not None and st.session_state.second_df is not None:
            first_cols = list(st.session_state.first_df.columns)
            second_cols = list(st.session_state.second_df.columns)

            # ---- Load Profile ---- #
            profiles = load_profiles()
            if profiles:
                st.markdown("**Load Profile**")
                lp_col1, lp_col2 = st.columns([4, 1])
                with lp_col1:
                    profile_to_load = st.selectbox(
                        "Select a saved profile",
                        [""] + list(profiles.keys()),
                        key="profile_selector",
                        label_visibility="collapsed",
                    )
                with lp_col2:
                    if st.button("Load", key="load_profile_btn") and profile_to_load:
                        st.session_state.pending_profile = profiles[profile_to_load]
                        st.rerun()

            # Apply a pending profile now that columns are known
            if st.session_state.pending_profile:
                cfg = st.session_state.pending_profile
                st.session_state["match_keys_first"] = [
                    k for k in cfg.get("match_keys_first", []) if k in first_cols
                ]
                st.session_state["match_keys_second"] = [
                    k for k in cfg.get("match_keys_second", []) if k in second_cols
                ]
                if cfg.get("compare_col_first") in first_cols:
                    st.session_state["compare_col_first"] = cfg["compare_col_first"]
                if cfg.get("compare_col_second") in second_cols:
                    st.session_state["compare_col_second"] = cfg["compare_col_second"]
                tolerance_options = ["None", "Dollar ($)", "Percentage (%)"]
                saved_tol = cfg.get("tolerance_type", "None")
                if saved_tol in tolerance_options:
                    st.session_state["tolerance_type_select"] = saved_tol
                st.session_state.pending_profile = None

            # ---- Widget definitions ---- #
            st.markdown("**Match keys (first file)**")
            match_keys_first = st.multiselect(
                "Select one or more columns",
                first_cols,
                key="match_keys_first",
                label_visibility="collapsed",
            )

            st.markdown("**Match keys (second file)**")
            match_keys_second = st.multiselect(
                "Select one or more columns",
                second_cols,
                key="match_keys_second",
                label_visibility="collapsed",
            )

            st.markdown("**Compare column (first file)**")
            compare_col_first = st.selectbox(
                "Select compare column",
                first_cols,
                key="compare_col_first",
                label_visibility="collapsed",
            )

            st.markdown("**Compare column (second file)**")
            compare_col_second = st.selectbox(
                "Select compare column",
                second_cols,
                key="compare_col_second",
                label_visibility="collapsed",
            )

            tolerance_type = st.selectbox(
                "Tolerance type",
                ["None", "Dollar ($)", "Percentage (%)"],
                index=0,
                key="tolerance_type_select",
            )

            tolerance_value = None
            if tolerance_type != "None":
                tolerance_value = st.number_input(
                    "Tolerance value",
                    min_value=0.0,
                    value=0.0,
                    step=0.01,
                    format="%.2f",
                )

            if st.button("Run Comparison", use_container_width=False):
                if not match_keys_first or not match_keys_second:
                    st.error("Please select match key columns for both files.")
                elif not compare_col_first or not compare_col_second:
                    st.error("Please select compare columns for both files.")
                else:
                    try:
                        with st.spinner("Running comparison..."):
                            result = compare_data(
                                st.session_state.first_df,
                                st.session_state.second_df,
                                match_keys_first,
                                match_keys_second,
                                compare_col_first,
                                compare_col_second,
                                output_file=None,
                                tolerance_type=None if tolerance_type == "None" else tolerance_type,
                                tolerance_value=tolerance_value if tolerance_type != "None" else None,
                                distinct_list=True,
                            )
                            st.session_state.result = result
                            st.session_state.nlq_result = None
                            st.success("Comparison complete!")
                    except Exception as e:
                        st.error(f"Error during comparison: {e}")
                        st.session_state.result = None

            # ---- Save Profile ---- #
            st.markdown("---")
            st.markdown("**Save Configuration Profile**")
            sp_col1, sp_col2 = st.columns([4, 1])
            with sp_col1:
                profile_name = st.text_input(
                    "Profile name",
                    key="profile_name_input",
                    placeholder="e.g. Monthly Vendor Reconciliation",
                    label_visibility="collapsed",
                )
            with sp_col2:
                if st.button("Save", key="save_profile_btn"):
                    if not profile_name:
                        st.error("Enter a profile name before saving.")
                    else:
                        save_profile(
                            profile_name,
                            {
                                "match_keys_first": match_keys_first,
                                "match_keys_second": match_keys_second,
                                "compare_col_first": compare_col_first,
                                "compare_col_second": compare_col_second,
                                "tolerance_type": tolerance_type,
                                "tolerance_value": tolerance_value,
                            },
                        )
                        st.success(f"Profile \u2018{profile_name}\u2019 saved!")
        else:
            st.info("Upload both files to configure the comparison")

    if st.session_state.result:
        st.markdown("### Results")

        st.markdown(
            f"""
            <div style="background-color: {brand_colors['primary_blue']}; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">
                <pre style="color: {brand_colors['white']}; margin: 0; font-family: monospace;">{st.session_state.result.summary_text}</pre>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("**Filter Results**")
        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            show_differences_only = st.checkbox("Show differences only", value=False)

        with filter_col2:
            show_matches_only = st.checkbox("Show matches only", value=False)

        filtered_df = st.session_state.result.merged.copy()
        if show_differences_only and not show_matches_only:
            filtered_df = filtered_df[filtered_df["Difference"]]
        elif show_matches_only and not show_differences_only:
            filtered_df = filtered_df[~filtered_df["Difference"]]

        st.markdown(f"**Preview Results ({len(filtered_df)} rows)**")
        st.dataframe(filtered_df, use_container_width=True, height=600)

        st.markdown("**Download Options**")
        download_filename = st.text_input(
            "File name for download",
            value="reconciliation_results.xlsx",
            help="Enter the desired filename (must end with .xlsx)",
        )

        if not download_filename.endswith(".xlsx"):
            download_filename += ".xlsx"

        output_buffer = BytesIO()
        filtered_df.to_excel(output_buffer, index=False)
        output_buffer.seek(0)

        temp_filename = "temp_reconciliation_results.xlsx"
        with open(temp_filename, "wb") as f:
            f.write(output_buffer.getvalue())
        _format_output(temp_filename, filtered_df)

        with open(temp_filename, "rb") as f:
            excel_data = f.read()

        st.download_button(
            label="Download Results",
            data=excel_data,
            file_name=download_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=False,
        )

        # ------------------------------------------------------------------ #
        # Natural Language Query section
        # ------------------------------------------------------------------ #
        st.markdown("---")
        st.markdown("### Ask a Question About the Results")
        st.markdown(
            "Query the reconciliation data in plain English. "
            "*Examples: \"Show me any differences over 5%\" &nbsp;\u00b7&nbsp; "
            "\"Can you show me any records for Supplier ACME Widgets\"*"
        )

        nlq_col1, nlq_col2 = st.columns([5, 1])
        with nlq_col1:
            nlq_question = st.text_input(
                "Your question",
                placeholder="e.g. Show me any differences over 5%",
                key="nlq_question",
                label_visibility="collapsed",
            )
        with nlq_col2:
            nlq_submit = st.button("Ask", use_container_width=True, key="nlq_submit")

        if nlq_submit and nlq_question:
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                st.error(
                    "ANTHROPIC_API_KEY is not configured. "
                    "Add it to .streamlit/secrets.toml or set it as an environment variable."
                )
            else:
                with st.spinner("Analysing your question..."):
                    nlq_df, nlq_answer = query_results_with_nlq(
                        st.session_state.result.merged, nlq_question
                    )
                st.session_state.nlq_result = (nlq_df, nlq_answer)

        if st.session_state.nlq_result is not None:
            nlq_df, nlq_answer = st.session_state.nlq_result
            st.markdown(
                f"""
                <div style="background-color: {brand_colors['primary_blue']}; padding: 1rem;
                            border-radius: 4px; margin-bottom: 1rem;
                            border-left: 4px solid {brand_colors['primary_green']};">
                    <p style="color: {brand_colors['white']}; margin: 0;">{nlq_answer}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if nlq_df is not None:
                st.dataframe(nlq_df, use_container_width=True, height=400)


if __name__ == "__main__":
    main()
