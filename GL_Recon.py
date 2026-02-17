"""Finance reconciliation utility with a simple Tkinter UI.

This module lets users pick the input files first and then configure
comparison options via dropdowns and list selectors. The resulting
comparison is written to the selected output file.
"""

import os
import tkinter as tk
from tkinter import filedialog, font, messagebox, ttk

from openpyxl import load_workbook
import pandas as pd


class ReconApp:
    """GUI application for reconciling up to two Excel files."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Reconciliation")
        self.root.geometry("700x650")
        self.root.configure(bg="#D8D7EE")

        self.file_paths = {"legacy": None, "converted": None, "third": None}
        self.dataframes: dict[str, pd.DataFrame | None] = {"legacy": None, "converted": None, "third": None}
        self.output_path = tk.StringVar(value="Output.xlsx")

        self.brand_colors = {
            "primary_blue": "#2F2891",  # PANTONE 2748
            "primary_green": "#00A68C",  # PANTONE 3405
            "midnight": "#1C2340",  # PANTONE 533
            "cool_gray": "#D9D9D6",  # PANTONE Cool Gray 1
            "white": "#FFFFFF",
        }
        self.base_font = self._resolve_font_family()
        self._configure_styles()

        self._build_scroll_container()
        self._build_header()
        self._build_file_picker()
        self._build_column_selectors()
        self._build_options()
        self._build_run_section()

    # ----------------------------- UI building ----------------------------- #
    def _build_scroll_container(self) -> None:
        container = tk.Frame(self.root, background=self.brand_colors["cool_gray"])
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            container,
            background=self.brand_colors["cool_gray"],
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scroll_frame = tk.Frame(self.canvas, background=self.brand_colors["cool_gray"])
        self.scroll_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        self.scroll_frame.bind("<Configure>", self._on_scroll_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_scroll_frame_configure(self, _: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.scroll_window, width=event.width)

    def _build_header(self) -> None:
        header_frame = tk.Frame(
            self.scroll_frame,
            background=self.brand_colors["primary_blue"],
            padx=18,
            pady=14,
        )
        header_frame.pack(fill="x")

        title = tk.Label(
            header_frame,
            text="Reconciliation",
            background=self.brand_colors["primary_blue"],
            foreground=self.brand_colors["white"],
            font=(self.base_font, 18, "bold"),
        )
        title.pack(anchor="w")
        subtitle = tk.Label(
            header_frame,
            text="Compare files with branded tolerance controls",
            background=self.brand_colors["primary_blue"],
            foreground=self.brand_colors["white"],
            font=(self.base_font, 11),
        )
        subtitle.pack(anchor="w", pady=(2, 0))

    def _build_file_picker(self) -> None:
        file_frame = ttk.LabelFrame(self.scroll_frame, text="1) Pick files", padding=10, style="Card.TLabelframe")
        file_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(file_frame, text="Select first file", command=lambda: self._select_file("legacy"), style="Primary.TButton").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.legacy_label = ttk.Label(file_frame, text="No file selected", width=70, style="Card.TLabel")
        self.legacy_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Button(file_frame, text="Select second file", command=lambda: self._select_file("converted"), style="Primary.TButton").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        self.converted_label = ttk.Label(file_frame, text="No file selected", width=70, style="Card.TLabel")
        self.converted_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Button(file_frame, text="Select optional third file", command=lambda: self._select_file("third"), style="Primary.TButton").grid(
            row=2, column=0, padx=5, pady=5, sticky="w"
        )
        self.third_label = ttk.Label(file_frame, text="No file selected (optional)", width=70, style="Card.TLabel")
        self.third_label.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(file_frame, text="Output file", style="Card.TLabel").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        output_frame = ttk.Frame(file_frame)
        output_frame.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_path)
        self.output_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(output_frame, text="Browse", command=self._select_output_file, style="Primary.TButton").pack(side="left", padx=(8, 0))

        file_frame.columnconfigure(1, weight=1)

    def _build_column_selectors(self) -> None:
        columns_frame = ttk.LabelFrame(self.scroll_frame, text="2) Choose columns", padding=10, style="Card.TLabelframe")
        columns_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(columns_frame, text="Match keys (first file)", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        self.pk_list_legacy = tk.Listbox(columns_frame, selectmode="multiple", height=6, exportselection=False)
        self.pk_list_legacy.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        ttk.Label(columns_frame, text="Match keys (second file)", style="Card.TLabel").grid(row=0, column=1, sticky="w")
        self.pk_list_converted = tk.Listbox(columns_frame, selectmode="multiple", height=6, exportselection=False)
        self.pk_list_converted.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        ttk.Label(columns_frame, text="Compare column (first file)", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.match_legacy = ttk.Combobox(columns_frame, state="readonly")
        self.match_legacy.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

        ttk.Label(columns_frame, text="Compare column (second file)", style="Card.TLabel").grid(row=2, column=1, sticky="w", pady=(10, 0))
        self.match_converted = ttk.Combobox(columns_frame, state="readonly")
        self.match_converted.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        columns_frame.columnconfigure(0, weight=1)
        columns_frame.columnconfigure(1, weight=1)
        self._style_listboxes()

    def _build_options(self) -> None:
        options_frame = ttk.LabelFrame(self.scroll_frame, text="3) Options", padding=10, style="Card.TLabelframe")
        options_frame.pack(fill="x", padx=10, pady=10)

        self.distinct_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Aggregate by match keys before comparing",
            variable=self.distinct_var,
            style="Card.TCheckbutton",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=5)

        ttk.Label(options_frame, text="Tolerance type", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.tolerance_type = ttk.Combobox(options_frame, state="readonly", values=["None", "Dollar ($)", "Percentage (%)"])
        self.tolerance_type.current(0)
        self.tolerance_type.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.tolerance_type.bind("<<ComboboxSelected>>", self._on_tolerance_change)

        ttk.Label(options_frame, text="Tolerance value", style="Card.TLabel").grid(row=1, column=1, sticky="w", pady=(10, 0))
        self.tolerance_value = ttk.Entry(options_frame)
        self.tolerance_value.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.tolerance_value.configure(state="disabled")

        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)

    def _build_run_section(self) -> None:
        run_frame = ttk.LabelFrame(self.scroll_frame, text="4) Run", padding=10, style="Card.TLabelframe")
        run_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.run_button = ttk.Button(run_frame, text="Run comparison", command=self._run_comparison, style="Primary.TButton")
        self.run_button.pack(fill="x", pady=(4, 10))
        self.summary_text = tk.Text(run_frame, height=12, state="disabled", wrap="word")
        self.summary_text.pack(fill="both", expand=True)
        self._style_summary_text()

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

    def _select_output_file(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Select output file",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if not path:
            return
        self.output_path.set(path)

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
            messagebox.showwarning("Missing match keys", "Select one or more match key columns for each file.")
            return

        match_col_legacy = self.match_legacy.get()
        match_col_converted = self.match_converted.get()
        if not match_col_legacy or not match_col_converted:
            messagebox.showwarning("Missing compare columns", "Select compare columns for both files.")
            return

        output_file = self.output_path.get().strip()
        if not output_file:
            messagebox.showwarning("Missing output file", "Select an output file before running the comparison.")
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
            output_file=output_file,
            tolerance_type=None if tolerance_type == "None" else tolerance_type,
            tolerance_value=tolerance_value,
            distinct_list=self.distinct_var.get(),
        )
        self._display_summary(result)

    def _configure_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.root.option_add("*Font", (self.base_font, 10))
        self.root.option_add("*Background", self.brand_colors["cool_gray"])

        style.configure(
            ".",
            background=self.brand_colors["cool_gray"],
            foreground=self.brand_colors["midnight"],
            font=(self.base_font, 10),
        )
        style.configure(
            "TLabel",
            background=self.brand_colors["cool_gray"],
            foreground=self.brand_colors["midnight"],
        )
        style.configure(
            "Card.TLabelframe",
            background=self.brand_colors["white"],
            foreground=self.brand_colors["primary_blue"],
            font=(self.base_font, 11, "bold"),
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=self.brand_colors["white"],
            foreground=self.brand_colors["primary_blue"],
            font=(self.base_font, 11, "bold"),
        )
        style.configure("Card.TLabel", background=self.brand_colors["white"], foreground=self.brand_colors["midnight"])
        style.configure("TFrame", background=self.brand_colors["white"])
        style.configure(
            "TEntry",
            fieldbackground=self.brand_colors["white"],
            foreground=self.brand_colors["midnight"],
        )
        style.configure(
            "TCombobox",
            fieldbackground=self.brand_colors["white"],
            foreground=self.brand_colors["midnight"],
        )
        style.configure(
            "Primary.TButton",
            background=self.brand_colors["primary_blue"],
            foreground=self.brand_colors["white"],
            font=(self.base_font, 11, "bold"),
            padding=(12, 6),
        )
        style.map(
            "Primary.TButton",
            background=[("active", self.brand_colors["primary_green"]), ("disabled", self.brand_colors["cool_gray"])],
            foreground=[("disabled", "#7A7A8A")],
        )
        style.configure(
            "Card.TCheckbutton",
            background=self.brand_colors["white"],
            foreground=self.brand_colors["midnight"],
        )

    def _style_listboxes(self) -> None:
        listbox_style = {
            "background": self.brand_colors["white"],
            "foreground": self.brand_colors["midnight"],
            "highlightbackground": self.brand_colors["primary_blue"],
            "selectbackground": self.brand_colors["primary_green"],
            "selectforeground": self.brand_colors["white"],
            "font": (self.base_font, 10),
        }
        self.pk_list_legacy.configure(**listbox_style)
        self.pk_list_converted.configure(**listbox_style)

    def _style_summary_text(self) -> None:
        self.summary_text.configure(
            background=self.brand_colors["white"],
            foreground=self.brand_colors["midnight"],
            padx=10,
            pady=8,
            borderwidth=0,
            font=(self.base_font, 10),
        )

    @staticmethod
    def _resolve_font_family() -> str:
        try:
            available = set(font.families())
        except tk.TclError:
            return "TkDefaultFont"
        for family in ("Titillium Web", "Titillium", "Roboto", "Segoe UI", "Arial"):
            if family in available:
                return family
        return "TkDefaultFont"

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
                if row.get(legacy_value_column) != 0 else float("nan")
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


# ----------------------------- Entry point ----------------------------- #
if __name__ == "__main__":
    root = tk.Tk()
    app = ReconApp(root)
    root.mainloop()
