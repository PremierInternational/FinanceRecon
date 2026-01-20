"""Finance reconciliation utility with a simple Tkinter UI.

This module lets users pick the input files first and then configure
comparison options via dropdowns and list selectors. The resulting
comparison is written to ``Output.xlsx`` in the working directory.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd


class ReconApp:
    """GUI application for reconciling up to two Excel files."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("GL Reconciliation")
        self.root.geometry("700x650")

        self.file_paths = {"legacy": None, "converted": None, "third": None}
        self.dataframes: dict[str, pd.DataFrame | None] = {"legacy": None, "converted": None, "third": None}

        self._build_file_picker()
        self._build_column_selectors()
        self._build_options()
        self._build_run_section()

    # ----------------------------- UI building ----------------------------- #
    def _build_file_picker(self) -> None:
        file_frame = ttk.LabelFrame(self.root, text="1) Pick files", padding=10)
        file_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(file_frame, text="Select first file", command=lambda: self._select_file("legacy")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.legacy_label = ttk.Label(file_frame, text="No file selected", width=70)
        self.legacy_label.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(file_frame, text="Select second file", command=lambda: self._select_file("converted")).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.converted_label = ttk.Label(file_frame, text="No file selected", width=70)
        self.converted_label.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(file_frame, text="Select optional third file", command=lambda: self._select_file("third")).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.third_label = ttk.Label(file_frame, text="No file selected (optional)", width=70)
        self.third_label.grid(row=2, column=1, padx=5, pady=5)

    def _build_column_selectors(self) -> None:
        columns_frame = ttk.LabelFrame(self.root, text="2) Choose columns", padding=10)
        columns_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(columns_frame, text="Primary keys (first file)").grid(row=0, column=0, sticky="w")
        self.pk_list_legacy = tk.Listbox(columns_frame, selectmode="multiple", height=6, exportselection=False)
        self.pk_list_legacy.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        ttk.Label(columns_frame, text="Primary keys (second file)").grid(row=0, column=1, sticky="w")
        self.pk_list_converted = tk.Listbox(columns_frame, selectmode="multiple", height=6, exportselection=False)
        self.pk_list_converted.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        ttk.Label(columns_frame, text="Match column (first file)").grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.match_legacy = ttk.Combobox(columns_frame, state="readonly")
        self.match_legacy.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

        ttk.Label(columns_frame, text="Match column (second file)").grid(row=2, column=1, sticky="w", pady=(10, 0))
        self.match_converted = ttk.Combobox(columns_frame, state="readonly")
        self.match_converted.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        columns_frame.columnconfigure(0, weight=1)
        columns_frame.columnconfigure(1, weight=1)

    def _build_options(self) -> None:
        options_frame = ttk.LabelFrame(self.root, text="3) Options", padding=10)
        options_frame.pack(fill="x", padx=10, pady=10)

        self.distinct_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Aggregate by primary keys before comparing", variable=self.distinct_var).grid(row=0, column=0, columnspan=2, sticky="w", pady=5)

        ttk.Label(options_frame, text="Tolerance type").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.tolerance_type = ttk.Combobox(options_frame, state="readonly", values=["None", "Dollar ($)", "Percentage (%)"])
        self.tolerance_type.current(0)
        self.tolerance_type.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.tolerance_type.bind("<<ComboboxSelected>>", self._on_tolerance_change)

        ttk.Label(options_frame, text="Tolerance value").grid(row=1, column=1, sticky="w", pady=(10, 0))
        self.tolerance_value = ttk.Entry(options_frame)
        self.tolerance_value.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.tolerance_value.configure(state="disabled")

        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)

    def _build_run_section(self) -> None:
        run_frame = ttk.LabelFrame(self.root, text="4) Run", padding=10)
        run_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Button(run_frame, text="Run comparison", command=self._run_comparison).pack(anchor="w", pady=5)
        self.summary_text = tk.Text(run_frame, height=12, state="disabled", wrap="word")
        self.summary_text.pack(fill="both", expand=True)

    # ----------------------------- Event handlers ----------------------------- #
    def _select_file(self, key: str) -> None:
        filetypes = [("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Select file", filetypes=filetypes)
        if not path:
            return

        try:
            data = pd.read_excel(path)
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("Unable to open file", f"Could not read {os.path.basename(path)}.\n{exc}")
            return

        self.file_paths[key] = path
        self.dataframes[key] = data
        label_map = {"legacy": self.legacy_label, "converted": self.converted_label, "third": self.third_label}
        label_map[key].configure(text=path)
        self._refresh_columns()

    def _refresh_columns(self) -> None:
        if self.dataframes["legacy"] is None or self.dataframes["converted"] is None:
            return

        legacy_cols = list(self.dataframes["legacy"].columns)
        converted_cols = list(self.dataframes["converted"].columns)

        self._populate_listbox(self.pk_list_legacy, legacy_cols)
        self._populate_listbox(self.pk_list_converted, converted_cols)
        self.match_legacy.configure(values=legacy_cols)
        self.match_converted.configure(values=converted_cols)
        if legacy_cols:
            self.match_legacy.current(0)
        if converted_cols:
            self.match_converted.current(0)

    @staticmethod
    def _populate_listbox(listbox: tk.Listbox, items: list[str]) -> None:
        listbox.delete(0, tk.END)
        for item in items:
            listbox.insert(tk.END, item)

    def _on_tolerance_change(self, _: tk.Event) -> None:  # type: ignore[override]
        selected = self.tolerance_type.get()
        if selected == "None":
            self.tolerance_value.delete(0, tk.END)
            self.tolerance_value.configure(state="disabled")
        else:
            self.tolerance_value.configure(state="normal")

    def _run_comparison(self) -> None:
        if self.dataframes["legacy"] is None or self.dataframes["converted"] is None:
            messagebox.showwarning("Missing files", "Please select the first two files before running the comparison.")
            return

        pk_legacy = self._selected_items(self.pk_list_legacy)
        pk_converted = self._selected_items(self.pk_list_converted)
        if not pk_legacy or not pk_converted:
            messagebox.showwarning("Missing primary keys", "Select one or more primary key columns for each file.")
            return

        match_col_legacy = self.match_legacy.get()
        match_col_converted = self.match_converted.get()
        if not match_col_legacy or not match_col_converted:
            messagebox.showwarning("Missing match columns", "Select match columns for both files.")
            return

        tolerance_type = self.tolerance_type.get()
        tolerance_value = None
        if tolerance_type != "None":
            try:
                tolerance_value = float(self.tolerance_value.get())
            except ValueError:
                messagebox.showerror("Invalid tolerance", "Enter a numeric tolerance value.")
                return

        result = compare_data(
            self.dataframes["legacy"],
            self.dataframes["converted"],
            pk_legacy,
            pk_converted,
            match_col_legacy,
            match_col_converted,
            tolerance_type=None if tolerance_type == "None" else tolerance_type,
            tolerance_value=tolerance_value,
            distinct_list=self.distinct_var.get(),
        )
        self._display_summary(result)

    @staticmethod
    def _selected_items(listbox: tk.Listbox) -> list[str]:
        return [listbox.get(idx) for idx in listbox.curselection()]

    def _display_summary(self, result: "ComparisonResult") -> None:
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, result.summary_text)
        self.summary_text.configure(state="disabled")


class ComparisonResult:
    """Simple container for comparison output."""

    def __init__(self, merged: pd.DataFrame, summary_text: str) -> None:
        self.merged = merged
        self.summary_text = summary_text


# ----------------------------- Core comparison ----------------------------- #
def compare_data(
    legacy: pd.DataFrame,
    converted: pd.DataFrame,
    pk_legacy: list[str],
    pk_converted: list[str],
    match_col_legacy: str,
    match_col_converted: str,
    tolerance_type: str | None = None,
    tolerance_value: float | None = None,
    distinct_list: bool = True,
) -> ComparisonResult:
    """Compare two dataframes and return a summary."""

    if distinct_list:
        legacy = legacy.groupby(pk_legacy)[match_col_legacy].sum().reset_index()
        converted = converted.groupby(pk_converted)[match_col_converted].sum().reset_index()

    merged_df = pd.merge(
        legacy,
        converted,
        left_on=pk_legacy,
        right_on=pk_converted,
        suffixes=("_legacy", "_converted"),
        how="outer",
    )

    def _difference(row: pd.Series) -> bool:
        legacy_val = row.get(f"{match_col_legacy}_legacy")
        conv_val = row.get(f"{match_col_converted}_converted")
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
        lambda row: row.get(f"{match_col_legacy}_legacy") - row.get(f"{match_col_converted}_converted"), axis=1
    )
    merged_df["Percentage Difference"] = merged_df.apply(
        lambda row: (
            abs(row.get(f"{match_col_legacy}_legacy") - row.get(f"{match_col_converted}_converted"))
            / abs(row.get(f"{match_col_legacy}_legacy")) * 100
            if row.get(f"{match_col_legacy}_legacy") not in [None, 0] else None
        ),
        axis=1,
    )

    total_records = len(merged_df)
    matched_records = len(merged_df[~merged_df["Difference"]])
    matched_percentage = (matched_records / total_records) * 100 if total_records else 0

    summary_lines = [
        f"Output written to Output.xlsx ({total_records} rows)",
        f"Matched records: {matched_records} ({matched_percentage:.2f}%)",
    ]

    output_file = "Output.xlsx"
    merged_df.to_excel(output_file, index=False)

    return ComparisonResult(merged_df, "\n".join(summary_lines))


# ----------------------------- Entry point ----------------------------- #
if __name__ == "__main__":
    root = tk.Tk()
    app = ReconApp(root)
    root.mainloop()
