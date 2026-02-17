# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit web application
streamlit run GL_Recon.py
```

There are no automated tests or linting configs in this project.

## Architecture

This is a single-file Streamlit web application (`GL_Recon.py`) for reconciling financial data between Excel files.

### Core Classes and Functions

**`ComparisonResult`** (line 17) — A simple dataclass holding the merged DataFrame and a text summary after reconciliation.

**`compare_data()`** (line 24) — The reconciliation engine. Steps:
1. Loads two Excel files from uploaded data into pandas DataFrames
2. Creates a composite match key from the user-selected columns
3. Optionally aggregates (groupby + sum) before comparing
4. Performs an outer merge on match keys
5. Computes dollar difference and percentage difference for the selected compare column
6. Applies configurable tolerance (dollar threshold or percentage threshold) to flag rows as matching or differing
7. Writes the result to an Excel output file and returns a summary

**`_format_output()`** (line 172) — Post-processes the Excel output using openpyxl to apply currency/percentage number formats.

**`main()`** (line 191) — The main Streamlit application function. Manages the full UI lifecycle: file upload, column configuration, reconciliation options, and results display. Uses a wide layout with brand colors (blue/green/gray palette).

### UI Flow

The app has a 4-step workflow presented in a compact single-screen layout:
1. **Pick Files** — Upload first and second Excel files (third file option removed)
2. **Choose Columns** — Multi-select match key columns; single-select the column to compare
3. **Options** — Toggle aggregation; set tolerance type (dollar or percent) and value
4. **Run** — Executes reconciliation and displays the text summary with download button

### Output

Results are written to an Excel file in the same directory as the input files, with columns renamed using `(First)` and `(Second)` suffixes plus computed `Difference`, `Dollar Difference`, and `Percentage Difference` columns.
