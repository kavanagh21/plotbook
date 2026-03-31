"""QAbstractTableModel bridging DataTable to QTableView."""

from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt6.QtGui import QColor

from plotbook.models.datatable import ColumnDef, DataTable
from plotbook.models.table_formats import GroupedTable


class DataTableModel(QAbstractTableModel):
    """Qt table model backed by a DataTable."""

    def __init__(self, data_table: DataTable, parent=None):
        super().__init__(parent)
        self._table = data_table
        self._col_defs: list[ColumnDef] = data_table.column_defs()
        # Alternating group colors for visual clarity
        self._group_colors = self._build_group_colors()

    @property
    def data_table(self) -> DataTable:
        return self._table

    def column_defs(self) -> list[ColumnDef]:
        return self._col_defs

    def _build_group_colors(self) -> list[QColor | None]:
        """Assign alternating subtle background colors to column groups."""
        colors = []
        seen_groups: dict[str, int] = {}
        group_idx = 0
        bg_light = [QColor(255, 255, 255, 0), QColor(240, 245, 255, 80)]

        for cd in self._col_defs:
            if cd.group_id not in seen_groups:
                seen_groups[cd.group_id] = group_idx
                group_idx += 1
            idx = seen_groups[cd.group_id]
            colors.append(bg_light[idx % 2])
        return colors

    def rowCount(self, parent=QModelIndex()) -> int:
        return self._table.row_count()

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._col_defs)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row, col = index.row(), index.column()

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            val = self._table.get_value(row, col)
            if isinstance(val, str):
                return val
            if val is None or (isinstance(val, float) and (math.isnan(val) or np.isnan(val))):
                return ""
            return f"{val:g}"

        if role == Qt.ItemDataRole.BackgroundRole:
            if col < len(self._group_colors):
                return self._group_colors[col]

        return None

    def setData(self, index: QModelIndex, value, role=Qt.ItemDataRole.EditRole) -> bool:
        if role != Qt.ItemDataRole.EditRole:
            return False

        row, col = index.row(), index.column()
        cd = self._col_defs[col] if col < len(self._col_defs) else None

        # Row label column (GroupedTable)
        if cd and cd.role == "row_label":
            if isinstance(self._table, GroupedTable):
                self._table.set_row_label(row, str(value))
                self.dataChanged.emit(index, index, [role])
                return True
            return False

        # Numeric columns
        text = str(value).strip()
        if text == "":
            self._table.set_value(row, col, None)
        else:
            try:
                numeric = float(text)
            except ValueError:
                return False
            self._table.set_value(row, col, numeric)

        self.dataChanged.emit(index, index, [role])

        # Auto-expand: if user types in last row, add more rows
        if row >= self._table.row_count() - 2:
            self.beginInsertRows(QModelIndex(), self._table.row_count(),
                                 self._table.row_count() + 9)
            self._table.ensure_rows(self._table.row_count() + 10)
            self.endInsertRows()

        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        base = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        return base | Qt.ItemFlag.ItemIsEditable

    def headerData(self, section: int, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section < len(self._col_defs):
                    cd = self._col_defs[section]
                    if cd.role == "replicate":
                        return f"{cd.name}"
                    return cd.name
            elif orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        return None

    def refresh_structure(self) -> None:
        """Call after adding/removing series."""
        self.beginResetModel()
        self._col_defs = self._table.column_defs()
        self._group_colors = self._build_group_colors()
        self.endResetModel()

    def add_series(self, name: str) -> None:
        self._table.add_series(name)
        self.refresh_structure()

    def remove_series(self, series_id: str) -> None:
        self._table.remove_series(series_id)
        self.refresh_structure()
