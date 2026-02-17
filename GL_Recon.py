"""Finance reconciliation utility with a Streamlit web UI.

This module lets users upload Excel files, configure comparison options,
and download reconciliation results. The resulting comparison is written
to an Excel file and displayed on screen.
"""

import base64
import os
from dataclasses import dataclass
from io import BytesIO

import pandas as pd
import streamlit as st
from openpyxl import load_workbook


@dataclass
class ComparisonResult:
    """Simple container for comparison output."""

    merged: pd.DataFrame
    summary_text: str


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


# ----------------------------- Streamlit UI ----------------------------- #
def main():
    """Main Streamlit application."""

    # Page config
    st.set_page_config(page_title="Reconciliation", layout="wide")

    # Brand colors
    brand_colors = {
        "primary_blue": "#0D2C71",
        "primary_green": "#00AB63",
        "midnight": "#02072D",
        "cool_gray": "#D8D7EE",
        "white": "#FFFFFF",
    }

    # Logo SVG with white text (converted from the provided logo)
    logo_svg = """
    <svg width="200" height="40" xmlns="http://www.w3.org/2000/svg">
        <text x="0" y="30" font-family="Arial, sans-serif" font-size="32" font-weight="bold" fill="#FFFFFF">definian</text>
        <rect x="160" y="5" width="15" height="15" fill="#00AB63" rx="3"/>
        <rect x="180" y="5" width="15" height="15" fill="#00AB63" rx="3"/>
    </svg>
    """

    # Custom CSS for brand colors, layout, and background
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(to right, {brand_colors['midnight']} 0%, {brand_colors['midnight']} 70%, rgba(2, 7, 45, 0.9) 100%),
                        url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 600"><defs><linearGradient id="g1" x1="0%25" y1="0%25" x2="100%25" y2="100%25"><stop offset="0%25" style="stop-color:%2300AB63;stop-opacity:0.3" /><stop offset="100%25" style="stop-color:%2300AB63;stop-opacity:0.1" /></linearGradient></defs><path d="M 300 50 L 380 50 Q 390 50 390 60 L 390 150 Q 390 160 380 160 L 300 160 Q 290 160 290 150 L 290 60 Q 290 50 300 50 Z" fill="url(%23g1)" transform="rotate(15 340 105)"/><path d="M 320 200 L 400 200 Q 410 200 410 210 L 410 300 Q 410 310 400 310 L 320 310 Q 310 310 310 300 L 310 210 Q 310 200 320 200 Z" fill="url(%23g1)" transform="rotate(-10 355 255)"/><path d="M 300 350 L 380 350 Q 390 350 390 360 L 390 450 Q 390 460 380 460 L 300 460 Q 290 460 290 450 L 290 360 Q 290 350 300 350 Z" fill="url(%23g1)" transform="rotate(20 340 405)"/></svg>') right center / contain no-repeat;
            background-attachment: fixed;
        }}
        .main {{
            background-color: transparent;
        }}
        div[data-testid="stHeader"] {{
            background-color: {brand_colors['midnight']};
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {brand_colors['white']} !important;
        }}
        h1 {{
            background-color: {brand_colors['midnight']};
            padding: 1rem;
            margin: -1rem -1rem 1rem -1rem;
        }}
        p, div, span, label {{
            color: {brand_colors['white']} !important;
        }}
        /* Text on white/gray backgrounds should be black */
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
        /* Make sure text in dropdown options is black */
        div[role="listbox"] div {{
            color: #000000 !important;
        }}
        /* Results text should be white on midnight background */
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
        /* Make dataframe larger */
        div[data-testid="stDataFrame"] {{
            height: 600px !important;
        }}
        /* Success/info messages */
        .stSuccess, .stInfo {{
            color: {brand_colors['white']} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header with logo
    st.markdown(
        f"""
        <div style="background-color: {brand_colors['midnight']}; padding: 1.5rem; margin: -1rem -1rem 2rem -1rem; display: flex; align-items: center; gap: 2rem;">
            <div style="flex-shrink: 0;">
                {logo_svg}
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

    # Create two columns for Upload Files and Configure sections
    col1, col2 = st.columns(2)

    # Upload Files section (left column)
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

    # Configure section (right column)
    with col2:
        st.markdown("### Configure")

        if st.session_state.first_df is not None and st.session_state.second_df is not None:
            first_cols = list(st.session_state.first_df.columns)
            second_cols = list(st.session_state.second_df.columns)

            # Match keys
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

            # Compare columns
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

            # Tolerance options
            tolerance_type = st.selectbox("Tolerance type", ["None", "Dollar ($)", "Percentage (%)"], index=0)

            tolerance_value = None
            if tolerance_type != "None":
                tolerance_value = st.number_input(
                    "Tolerance value",
                    min_value=0.0,
                    value=0.0,
                    step=0.01,
                    format="%.2f",
                )

            # Run comparison button
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
                            st.success("Comparison complete!")
                    except Exception as e:
                        st.error(f"Error during comparison: {e}")
                        st.session_state.result = None
        else:
            st.info("Upload both files to configure the comparison")

    # Display results automatically
    if st.session_state.result:
        st.markdown("### Results")

        # Display summary in white text on midnight background
        st.markdown(
            f"""
            <div style="background-color: {brand_colors['midnight']}; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">
                <pre style="color: {brand_colors['white']}; margin: 0; font-family: monospace;">{st.session_state.result.summary_text}</pre>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Filter options for preview
        st.markdown("**Filter Results**")
        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            show_differences_only = st.checkbox("Show differences only", value=False)

        with filter_col2:
            show_matches_only = st.checkbox("Show matches only", value=False)

        # Apply filters
        filtered_df = st.session_state.result.merged.copy()
        if show_differences_only and not show_matches_only:
            filtered_df = filtered_df[filtered_df["Difference"]]
        elif show_matches_only and not show_differences_only:
            filtered_df = filtered_df[~filtered_df["Difference"]]

        # Show preview with larger size
        st.markdown(f"**Preview Results ({len(filtered_df)} rows)**")
        st.dataframe(filtered_df, use_container_width=True, height=600)

        # Generate Excel file for download with custom filename support
        st.markdown("**Download Options**")
        download_filename = st.text_input(
            "File name for download",
            value="reconciliation_results.xlsx",
            help="Enter the desired filename (must end with .xlsx)",
        )

        # Ensure filename ends with .xlsx
        if not download_filename.endswith(".xlsx"):
            download_filename += ".xlsx"

        # Create Excel file in memory
        output_buffer = BytesIO()
        filtered_df.to_excel(output_buffer, index=False)
        output_buffer.seek(0)

        # Load and format the Excel file
        temp_filename = "temp_reconciliation_results.xlsx"
        with open(temp_filename, "wb") as f:
            f.write(output_buffer.getvalue())
        _format_output(temp_filename, filtered_df)

        # Read the formatted file for download
        with open(temp_filename, "rb") as f:
            excel_data = f.read()

        # Provide download button
        st.download_button(
            label="Download Results",
            data=excel_data,
            file_name=download_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=False,
        )


if __name__ == "__main__":
    main()
