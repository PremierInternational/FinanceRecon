"""Finance reconciliation utility with a Streamlit web UI.

This module lets users upload Excel files, configure comparison options,
and download reconciliation results. The resulting comparison is written
to an Excel file and displayed on screen.
"""

import os
from dataclasses import dataclass

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
    output_file: str,
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
        f"Output written to {output_file} ({total_records} rows)",
        f"Matched records: {matched_records} ({matched_percentage:.2f}%)",
    ]

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

    # Brand colors
    brand_colors = {
        "primary_blue": "#2F2891",  # PANTONE 2748
        "primary_green": "#00A68C",  # PANTONE 3405
        "midnight": "#1C2340",  # PANTONE 533
        "cool_gray": "#D9D9D6",  # PANTONE Cool Gray 1
        "white": "#FFFFFF",
    }

    # Custom CSS for brand colors and compact layout
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {brand_colors['cool_gray']};
        }}
        .main {{
            background-color: {brand_colors['cool_gray']};
        }}
        div[data-testid="stHeader"] {{
            background-color: {brand_colors['primary_blue']};
        }}
        h1 {{
            color: {brand_colors['white']};
            background-color: {brand_colors['primary_blue']};
            padding: 1rem;
            margin: -1rem -1rem 1rem -1rem;
        }}
        h2 {{
            color: {brand_colors['primary_blue']};
            font-size: 1.2rem;
        }}
        h3 {{
            color: {brand_colors['primary_blue']};
            font-size: 1rem;
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
        .uploadedFile {{
            background-color: {brand_colors['white']};
        }}
        div[data-baseweb="select"] {{
            background-color: {brand_colors['white']};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Page config
    st.set_page_config(page_title="Reconciliation", layout="wide")

    # Header
    st.markdown(
        f"""
        <div style="background-color: {brand_colors['primary_blue']}; padding: 1.5rem; margin: -1rem -1rem 2rem -1rem;">
            <h1 style="margin: 0; color: {brand_colors['white']};">Reconciliation</h1>
            <p style="margin: 0.5rem 0 0 0; color: {brand_colors['white']};">Compare files with branded tolerance controls</p>
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

    # Use columns for compact layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 1) Pick Files")
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

        output_filename = st.text_input("Output filename", value="Output.xlsx", help="Name of the output Excel file")

    with col2:
        st.markdown("### 2) Choose Columns")

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
        else:
            st.info("Upload both files to select columns")

    # Options section
    st.markdown("### 3) Options")
    opt_col1, opt_col2, opt_col3 = st.columns([1, 1, 1])

    with opt_col1:
        aggregate = st.checkbox("Aggregate by match keys before comparing", value=True)

    with opt_col2:
        tolerance_type = st.selectbox("Tolerance type", ["None", "Dollar ($)", "Percentage (%)"], index=0)

    with opt_col3:
        tolerance_value = None
        if tolerance_type != "None":
            tolerance_value = st.number_input(
                "Tolerance value",
                min_value=0.0,
                value=0.0,
                step=0.01,
                format="%.2f",
            )

    # Run section
    st.markdown("### 4) Run")

    if st.button("Run Comparison", use_container_width=True):
        if st.session_state.first_df is None or st.session_state.second_df is None:
            st.error("Please upload both files before running the comparison.")
        elif not match_keys_first or not match_keys_second:
            st.error("Please select match key columns for both files.")
        elif not compare_col_first or not compare_col_second:
            st.error("Please select compare columns for both files.")
        elif not output_filename.strip():
            st.error("Please enter an output filename.")
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
                        output_file=output_filename,
                        tolerance_type=None if tolerance_type == "None" else tolerance_type,
                        tolerance_value=tolerance_value if tolerance_type != "None" else None,
                        distinct_list=aggregate,
                    )
                    st.session_state.result = result
                    st.success("Comparison complete!")
            except Exception as e:
                st.error(f"Error during comparison: {e}")
                st.session_state.result = None

    # Display results
    if st.session_state.result:
        st.markdown("### Results")
        st.text(st.session_state.result.summary_text)

        # Provide download button
        if os.path.exists(output_filename):
            with open(output_filename, "rb") as f:
                st.download_button(
                    label="Download Results",
                    data=f,
                    file_name=output_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

        # Show preview of results
        with st.expander("Preview Results (first 100 rows)"):
            st.dataframe(st.session_state.result.merged.head(100), use_container_width=True)


if __name__ == "__main__":
    main()
