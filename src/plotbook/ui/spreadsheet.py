"""Spreadsheet-style data entry widget."""

from __future__ import annotations

from PyQt6.QtCore import QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QMouseEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from plotbook.ui.symbol_picker import SymbolButton
from plotbook.viewmodels.table_model import DataTableModel


class EditableHeaderView(QHeaderView):
    """Horizontal header that supports double-click to rename columns (series)."""

    headerRenamed = pyqtSignal(int, str)  # (logical_index, new_name)

    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setSectionsClickable(True)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        logical_index = self.logicalIndexAt(event.pos())
        if logical_index >= 0:
            model = self.model()
            if model is not None:
                current_name = model.headerData(
                    logical_index, Qt.Orientation.Horizontal,
                    Qt.ItemDataRole.DisplayRole
                )
                new_name, ok = _rename_dialog(self, current_name or "")
                if ok and new_name.strip():
                    self.headerRenamed.emit(logical_index, new_name.strip())
        super().mouseDoubleClickEvent(event)


class SpreadsheetWidget(QWidget):
    """Spreadsheet-like data entry backed by a DataTableModel."""

    seriesAdded = pyqtSignal()
    seriesRemoved = pyqtSignal(str)  # series_id
    seriesRenamed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._table_view = QTableView(self)
        self._model: DataTableModel | None = None

        # Editable header
        self._header = EditableHeaderView(self._table_view)
        self._header.headerRenamed.connect(self._on_header_renamed)
        self._table_view.setHorizontalHeader(self._header)

        # Configure table view
        self._table_view.setAlternatingRowColors(False)
        self._table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self._header.setMinimumSectionSize(60)
        self._header.setDefaultSectionSize(80)
        self._header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table_view.verticalHeader().setDefaultSectionSize(24)
        self._table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table_view.customContextMenuRequested.connect(self._show_context_menu)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._table_view)

        # Keyboard shortcuts
        self._setup_shortcuts()

    def set_model(self, model: DataTableModel) -> None:
        self._model = model
        self._table_view.setModel(model)

    def _on_header_renamed(self, logical_index: int, new_name: str) -> None:
        """Rename the series that owns this column."""
        if self._model is None:
            return

        col_defs = self._model.column_defs()
        if logical_index >= len(col_defs):
            return

        cd = col_defs[logical_index]

        # Don't allow renaming the row-label column
        if cd.group_id == "__rowlabel__":
            return

        # X column: rename the column header on the table
        if cd.group_id == "__x__":
            from plotbook.models.table_formats import XYTable
            table = self._model.data_table
            if isinstance(table, XYTable):
                table.x_column_name = new_name
                self._model.refresh_structure()
                self.seriesRenamed.emit()
            return

        # Find the series and rename it
        for series in self._model.data_table.series:
            if series.id == cd.group_id:
                series.name = new_name
                break

        # Refresh the model to update all headers for this group
        self._model.refresh_structure()
        self.seriesRenamed.emit()

    def _setup_shortcuts(self) -> None:
        # Ctrl+V: paste from clipboard
        paste_action = QAction("Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self._paste_clipboard)
        self.addAction(paste_action)

        # Ctrl+C: copy selection
        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self._copy_selection)
        self.addAction(copy_action)

        # Delete: clear selection
        delete_action = QAction("Delete", self)
        delete_action.setShortcut(QKeySequence(Qt.Key.Key_Delete))
        delete_action.triggered.connect(self._delete_selection)
        self.addAction(delete_action)

    def _show_context_menu(self, pos) -> None:
        if self._model is None:
            return

        menu = QMenu(self)
        menu.addAction("Add Series/Group", self._add_series)

        # If clicking on a data column, offer rename and remove
        index = self._table_view.indexAt(pos)
        if index.isValid():
            col_defs = self._model.column_defs()
            if index.column() < len(col_defs):
                cd = col_defs[index.column()]
                if cd.group_id not in ("__x__", "__rowlabel__"):
                    series_name = cd.name
                    menu.addSeparator()
                    menu.addAction(
                        f"Rename '{series_name}'",
                        lambda col=index.column(): self._rename_via_dialog(col),
                    )
                    menu.addAction(
                        f"Remove '{series_name}'",
                        lambda sid=cd.group_id: self._remove_series(sid),
                    )

        menu.addSeparator()
        menu.addAction("Paste", self._paste_clipboard)
        menu.addAction("Paste Transposed", self._paste_clipboard_transposed)
        menu.addAction("Copy", self._copy_selection)
        menu.addAction("Clear Selection", self._delete_selection)

        menu.exec(self._table_view.viewport().mapToGlobal(pos))

    def _rename_via_dialog(self, col: int) -> None:
        """Show rename dialog for the column at given index."""
        if self._model is None:
            return
        col_defs = self._model.column_defs()
        if col >= len(col_defs):
            return
        cd = col_defs[col]
        current_name = cd.name
        new_name, ok = _rename_dialog(self, current_name)
        if ok and new_name.strip():
            self._on_header_renamed(col, new_name.strip())

    def _add_series(self) -> None:
        if self._model is None:
            return
        n = len(self._model.data_table.series) + 1
        self._model.add_series(f"Dataset {chr(64 + n)}")
        self.seriesAdded.emit()

    def _remove_series(self, series_id: str) -> None:
        if self._model is None:
            return
        self._model.remove_series(series_id)
        self.seriesRemoved.emit(series_id)

    def _paste_clipboard(self) -> None:
        """Paste tab-separated data from clipboard."""
        self._do_paste(transpose=False)

    def _paste_clipboard_transposed(self) -> None:
        """Paste tab-separated data from clipboard, swapping rows and columns."""
        self._do_paste(transpose=True)

    def _do_paste(self, transpose: bool = False) -> None:
        if self._model is None:
            return

        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            return

        # Get paste start position
        indexes = self._table_view.selectedIndexes()
        if indexes:
            start_row = min(idx.row() for idx in indexes)
            start_col = min(idx.column() for idx in indexes)
        else:
            start_row, start_col = 0, 0

        # Parse clipboard into 2D grid
        grid = []
        for line in text.strip().split("\n"):
            grid.append([c.strip() for c in line.split("\t")])

        if transpose:
            # Transpose: swap rows and columns
            max_cols = max(len(r) for r in grid)
            # Pad short rows so zip works
            padded = [r + [""] * (max_cols - len(r)) for r in grid]
            grid = [list(col) for col in zip(*padded)]

        for r_offset, row_cells in enumerate(grid):
            for c_offset, cell in enumerate(row_cells):
                row = start_row + r_offset
                col = start_col + c_offset
                idx = self._model.index(row, col)
                self._model.setData(idx, cell, Qt.ItemDataRole.EditRole)

    def _copy_selection(self) -> None:
        """Copy selected cells as tab-separated text."""
        if self._model is None:
            return

        indexes = self._table_view.selectedIndexes()
        if not indexes:
            return

        rows = sorted(set(idx.row() for idx in indexes))
        cols = sorted(set(idx.column() for idx in indexes))

        lines = []
        for row in rows:
            cells = []
            for col in cols:
                idx = self._model.index(row, col)
                val = self._model.data(idx, Qt.ItemDataRole.DisplayRole)
                cells.append(str(val) if val else "")
            lines.append("\t".join(cells))

        QApplication.clipboard().setText("\n".join(lines))

    def _delete_selection(self) -> None:
        """Clear selected cells."""
        if self._model is None:
            return

        for idx in self._table_view.selectedIndexes():
            self._model.setData(idx, "", Qt.ItemDataRole.EditRole)


def _rename_dialog(parent: QWidget, current_name: str) -> tuple[str, bool]:
    """Show a rename dialog with a symbol picker button. Returns (name, accepted)."""
    dlg = QDialog(parent)
    dlg.setWindowTitle("Rename")
    dlg.setMinimumWidth(320)

    layout = QVBoxLayout(dlg)
    layout.addWidget(QLabel("New name:"))

    row = QHBoxLayout()
    line_edit = QLineEdit(current_name)
    line_edit.selectAll()
    row.addWidget(line_edit, 1)
    row.addWidget(SymbolButton(line_edit))
    layout.addLayout(row)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    layout.addWidget(buttons)

    if dlg.exec() == QDialog.DialogCode.Accepted:
        return line_edit.text(), True
    return "", False
