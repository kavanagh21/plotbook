"""Format-specific DataTable subclasses."""

from __future__ import annotations

import numpy as np

from plotbook.models.datatable import ColumnDef, DataTable
from plotbook.models.enums import EntryMode, TableFormat


class XYTable(DataTable):
    """
    XY format: shared X column + Y series with subcolumns.

    Spreadsheet layout (RAW, 2 series, 3 reps each):
        X  | Y1  | Y1  | Y1  | Y2  | Y2  | Y2
        1  | 2.3 | 2.5 | 2.1 | 5.0 | 5.2 | 4.8

    Spreadsheet layout (MEAN_SD, 2 series):
        X  | Y1 Mean | Y1 ±SD | Y2 Mean | Y2 ±SD
        1  | 2.3     | 0.2    | 5.1     | 0.1
    """

    def __init__(self, name: str, entry_mode: EntryMode):
        super().__init__(name, TableFormat.XY, entry_mode)
        self._x_data: np.ndarray = np.full(self._row_count, np.nan, dtype=np.float64)
        self.x_column_name: str = "X"

    def x_values(self) -> np.ndarray:
        return self._x_data.copy()

    def ensure_rows(self, n: int) -> None:
        if n > self._row_count:
            extra = np.full(n - self._row_count, np.nan, dtype=np.float64)
            self._x_data = np.concatenate([self._x_data, extra])
        super().ensure_rows(n)

    def column_defs(self) -> list[ColumnDef]:
        cols = [ColumnDef(name=self.x_column_name, group_id="__x__", role="x")]
        for series in self._series:
            if self.entry_mode == EntryMode.RAW:
                for i in range(series.n_subcols):
                    cols.append(ColumnDef(
                        name=series.name,
                        group_id=series.id,
                        role="replicate",
                        replicate_index=i,
                    ))
            elif self.entry_mode == EntryMode.MEAN_SD:
                cols.append(ColumnDef(name=f"{series.name} Mean", group_id=series.id, role="mean"))
                cols.append(ColumnDef(name="±SD", group_id=series.id, role="sd"))
            elif self.entry_mode == EntryMode.MEAN_SEM:
                cols.append(ColumnDef(name=f"{series.name} Mean", group_id=series.id, role="mean"))
                cols.append(ColumnDef(name="±SEM", group_id=series.id, role="sem"))
            else:  # SINGLE
                cols.append(ColumnDef(name=series.name, group_id=series.id, role="y"))
        return cols

    def get_value(self, row: int, col: int) -> float:
        if row >= self._row_count:
            return float("nan")
        if col == 0:
            return float(self._x_data[row])
        # Map col index to series + subcol
        col_idx = 1
        for series in self._series:
            n = series.n_subcols
            if col < col_idx + n:
                subcol = col - col_idx
                return float(series.data[row, subcol])
            col_idx += n
        return float("nan")

    def set_value(self, row: int, col: int, value: float | None) -> None:
        val = float("nan") if value is None else value
        # Auto-expand
        if row >= self._row_count:
            self.ensure_rows(row + 10)

        if col == 0:
            self._x_data[row] = val
            return

        col_idx = 1
        for series in self._series:
            n = series.n_subcols
            if col < col_idx + n:
                subcol = col - col_idx
                series.data[row, subcol] = val
                return
            col_idx += n

    def swap_x_and_mean(self) -> None:
        """Swap the X column with the Mean column of the first series.
        Useful when data was pasted with columns in the wrong order."""
        if not self._series:
            return
        s = self._series[0]
        old_x = self._x_data.copy()
        old_mean = s.data[:, 0].copy()
        # Swap
        n = min(len(old_x), s.n_rows)
        self._x_data[:n] = old_mean[:n]
        s.data[:n, 0] = old_x[:n]

    def to_dict(self) -> dict:
        d = self._base_dict()
        d["x_data"] = self._x_data.tolist()
        d["x_column_name"] = self.x_column_name
        return d

    @classmethod
    def from_dict(cls, d: dict) -> XYTable:
        t = cls(name=d["name"], entry_mode=EntryMode[d["entry_mode"]])
        t._load_base(d)
        t._x_data = np.array(d["x_data"], dtype=np.float64)
        t.x_column_name = d.get("x_column_name", "X")
        return t


class ColumnTable(DataTable):
    """
    Column format: each series is a group, rows are replicates.

    Spreadsheet layout (RAW, 3 groups):
        Control | Drug A | Drug B
        5.1     | 7.2    | 6.8
        5.3     | 7.0    | 7.1
        4.9     | 7.5    | 6.5

    For MEAN_SD: each group has [Mean, ±SD] subcolumns.
    """

    def __init__(self, name: str, entry_mode: EntryMode):
        super().__init__(name, TableFormat.COLUMN, entry_mode)

    def column_defs(self) -> list[ColumnDef]:
        cols = []
        for series in self._series:
            if self.entry_mode == EntryMode.RAW:
                # In Column format with RAW, the series itself is one column
                # (rows are replicates within the group)
                cols.append(ColumnDef(
                    name=series.name, group_id=series.id, role="replicate",
                    replicate_index=0,
                ))
            elif self.entry_mode == EntryMode.MEAN_SD:
                cols.append(ColumnDef(name=f"{series.name} Mean", group_id=series.id, role="mean"))
                cols.append(ColumnDef(name="±SD", group_id=series.id, role="sd"))
            elif self.entry_mode == EntryMode.MEAN_SEM:
                cols.append(ColumnDef(name=f"{series.name} Mean", group_id=series.id, role="mean"))
                cols.append(ColumnDef(name="±SEM", group_id=series.id, role="sem"))
            else:  # SINGLE
                cols.append(ColumnDef(name=series.name, group_id=series.id, role="y"))
        return cols

    def get_value(self, row: int, col: int) -> float:
        if row >= self._row_count:
            return float("nan")
        col_idx = 0
        for series in self._series:
            n = series.n_subcols
            if col < col_idx + n:
                subcol = col - col_idx
                return float(series.data[row, subcol])
            col_idx += n
        return float("nan")

    def set_value(self, row: int, col: int, value: float | None) -> None:
        val = float("nan") if value is None else value
        if row >= self._row_count:
            self.ensure_rows(row + 10)

        col_idx = 0
        for series in self._series:
            n = series.n_subcols
            if col < col_idx + n:
                subcol = col - col_idx
                series.data[row, subcol] = val
                return
            col_idx += n

    def add_series(self, name: str, n_replicates: int = 1) -> "DataSeries":
        """Column format: RAW mode uses 1 subcol (rows are replicates)."""
        from plotbook.models.datatable import DataSeries
        if self.entry_mode == EntryMode.RAW:
            s = DataSeries(
                name=name,
                entry_mode=self.entry_mode,
                n_rows=self._row_count,
                n_replicates=1,
            )
        else:
            s = DataSeries(
                name=name,
                entry_mode=self.entry_mode,
                n_rows=self._row_count,
            )
        self._series.append(s)
        return s

    def to_dict(self) -> dict:
        return self._base_dict()

    @classmethod
    def from_dict(cls, d: dict) -> ColumnTable:
        t = cls(name=d["name"], entry_mode=EntryMode[d["entry_mode"]])
        t._load_base(d)
        return t


class GroupedTable(DataTable):
    """
    Grouped format: rows are categories, columns are groups with subcolumns.

    Spreadsheet layout (RAW, 2 groups, 3 reps each):
        Row Label | Drug A | Drug A | Drug A | Drug B | Drug B | Drug B
        Week 1    | 5.1    | 5.3    | 4.9    | 7.2    | 7.0    | 7.5
        Week 2    | 6.0    | 5.8    | 6.2    | 8.1    | 7.9    | 8.3

    For MEAN_SD: each group has [Mean, ±SD] subcolumns.
    """

    def __init__(self, name: str, entry_mode: EntryMode):
        super().__init__(name, TableFormat.GROUPED, entry_mode)
        self._row_labels: list[str] = [""] * self._row_count

    @property
    def row_labels(self) -> list[str]:
        return self._row_labels

    def ensure_rows(self, n: int) -> None:
        if n > self._row_count:
            self._row_labels.extend([""] * (n - self._row_count))
        super().ensure_rows(n)

    def set_row_label(self, row: int, label: str) -> None:
        if row >= self._row_count:
            self.ensure_rows(row + 10)
        self._row_labels[row] = label

    def column_defs(self) -> list[ColumnDef]:
        cols = [ColumnDef(name="", group_id="__rowlabel__", role="row_label")]
        for series in self._series:
            if self.entry_mode == EntryMode.RAW:
                for i in range(series.n_subcols):
                    cols.append(ColumnDef(
                        name=series.name,
                        group_id=series.id,
                        role="replicate",
                        replicate_index=i,
                    ))
            elif self.entry_mode == EntryMode.MEAN_SD:
                cols.append(ColumnDef(name=f"{series.name} Mean", group_id=series.id, role="mean"))
                cols.append(ColumnDef(name="±SD", group_id=series.id, role="sd"))
            elif self.entry_mode == EntryMode.MEAN_SEM:
                cols.append(ColumnDef(name=f"{series.name} Mean", group_id=series.id, role="mean"))
                cols.append(ColumnDef(name="±SEM", group_id=series.id, role="sem"))
            else:  # SINGLE
                cols.append(ColumnDef(name=series.name, group_id=series.id, role="y"))
        return cols

    def get_value(self, row: int, col: int) -> float | str:
        if row >= self._row_count:
            return float("nan")
        if col == 0:
            return self._row_labels[row]

        col_idx = 1
        for series in self._series:
            n = series.n_subcols
            if col < col_idx + n:
                subcol = col - col_idx
                return float(series.data[row, subcol])
            col_idx += n
        return float("nan")

    def set_value(self, row: int, col: int, value) -> None:
        if row >= self._row_count:
            self.ensure_rows(row + 10)

        if col == 0:
            self._row_labels[row] = str(value) if value else ""
            return

        val = float("nan") if value is None else float(value)
        col_idx = 1
        for series in self._series:
            n = series.n_subcols
            if col < col_idx + n:
                subcol = col - col_idx
                series.data[row, subcol] = val
                return
            col_idx += n

    def to_dict(self) -> dict:
        d = self._base_dict()
        d["row_labels"] = self._row_labels
        return d

    @classmethod
    def from_dict(cls, d: dict) -> GroupedTable:
        t = cls(name=d["name"], entry_mode=EntryMode[d["entry_mode"]])
        t._load_base(d)
        t._row_labels = d.get("row_labels", [""] * t._row_count)
        return t


def create_table(
    name: str, table_format: TableFormat, entry_mode: EntryMode
) -> DataTable:
    """Factory function to create the appropriate table type."""
    if table_format == TableFormat.XY:
        return XYTable(name, entry_mode)
    elif table_format == TableFormat.COLUMN:
        return ColumnTable(name, entry_mode)
    elif table_format == TableFormat.GROUPED:
        return GroupedTable(name, entry_mode)
    raise ValueError(f"Unknown table format: {table_format}")


def table_from_dict(d: dict) -> DataTable:
    """Deserialize any table type from dict."""
    fmt = TableFormat[d["table_format"]]
    if fmt == TableFormat.XY:
        return XYTable.from_dict(d)
    elif fmt == TableFormat.COLUMN:
        return ColumnTable.from_dict(d)
    elif fmt == TableFormat.GROUPED:
        return GroupedTable.from_dict(d)
    raise ValueError(f"Unknown table format: {fmt}")
