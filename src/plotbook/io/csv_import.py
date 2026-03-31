"""Import CSV files into PlotBook sheets."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from plotbook.models.enums import EntryMode, GraphType, TableFormat
from plotbook.models.project import Project, Sheet


def import_csv_to_sheet(
    path: str,
    project: Project,
    delimiter: str | None = None,
) -> Sheet:
    """
    Import a CSV/TSV file as a new XY sheet.

    Auto-detects delimiter if not specified.
    First row is treated as headers.
    First column becomes X values, remaining columns become Y series.
    """
    filepath = Path(path)

    # Auto-detect delimiter
    if delimiter is None:
        if filepath.suffix.lower() == ".tsv":
            delimiter = "\t"
        else:
            with open(path, "r", encoding="utf-8") as f:
                sample = f.read(4096)
                sniffer = csv.Sniffer()
                try:
                    dialect = sniffer.sniff(sample)
                    delimiter = dialect.delimiter
                except csv.Error:
                    delimiter = ","

    # Read CSV
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        rows = list(reader)

    if not rows:
        raise ValueError("CSV file is empty")

    headers = rows[0]
    data_rows = rows[1:]

    # Create XY sheet
    name = filepath.stem
    sheet = project.add_sheet(
        TableFormat.XY,
        EntryMode.SINGLE,
        GraphType.SCATTER,
        name,
    )

    table = sheet.data_table
    # Remove default series
    for s in list(table.series):
        table.remove_series(s.id)

    # Add series for each Y column
    for header in headers[1:]:
        table.add_series(header or f"Column {headers.index(header)}")

    # Ensure enough rows
    table.ensure_rows(len(data_rows))

    # Populate data
    for row_idx, row in enumerate(data_rows):
        for col_idx, cell in enumerate(row):
            cell = cell.strip()
            if not cell:
                continue
            try:
                val = float(cell)
                table.set_value(row_idx, col_idx, val)
            except ValueError:
                pass  # Skip non-numeric cells

    # Ensure series styles
    spec = sheet.graph_spec
    for i, s in enumerate(table.series):
        spec.ensure_series_style(s.id, i)

    return sheet
