"""Dialog for creating a new sheet."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from plotbook.models.enums import (
    GRAPH_TYPES_FOR_FORMAT,
    GRAPH_TYPE_NAMES,
    EntryMode,
    GraphType,
    TableFormat,
)


class NewSheetDialog(QDialog):
    """Dialog to configure a new sheet (format, entry mode, graph type, name)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Sheet")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Name
        self._name = QLineEdit()
        self._name.setPlaceholderText("Sheet name")
        form.addRow("Name:", self._name)

        # Table format
        self._format = QComboBox()
        self._format.addItem("XY (Scatter, Line, Area)", TableFormat.XY)
        self._format.addItem("Column (Bar, Box, Violin)", TableFormat.COLUMN)
        self._format.addItem("Grouped (Grouped Bar, Stacked)", TableFormat.GROUPED)
        self._format.currentIndexChanged.connect(self._on_format_changed)
        form.addRow("Table Format:", self._format)

        # Entry mode
        self._entry_mode = QComboBox()
        self._entry_mode.addItem("Enter Replicate Values", EntryMode.RAW)
        self._entry_mode.addItem("Enter Mean \u00b1 SD", EntryMode.MEAN_SD)
        self._entry_mode.addItem("Enter Mean \u00b1 SEM", EntryMode.MEAN_SEM)
        self._entry_mode.addItem("Single Values (no error)", EntryMode.SINGLE)
        form.addRow("Data Entry:", self._entry_mode)

        # Graph type
        self._graph_type = QComboBox()
        form.addRow("Graph Type:", self._graph_type)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Initialize graph types
        self._on_format_changed()

    def _on_format_changed(self) -> None:
        fmt = self._format.currentData()
        self._graph_type.clear()
        if fmt:
            for gt in GRAPH_TYPES_FOR_FORMAT.get(fmt, []):
                self._graph_type.addItem(GRAPH_TYPE_NAMES.get(gt, gt.name), gt)

    def result_values(self) -> tuple[str, TableFormat, EntryMode, GraphType]:
        return (
            self._name.text().strip() or "",
            self._format.currentData(),
            self._entry_mode.currentData(),
            self._graph_type.currentData(),
        )
