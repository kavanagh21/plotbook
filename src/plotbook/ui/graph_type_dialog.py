"""Dialog for changing graph type."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QVBoxLayout,
)

from plotbook.models.enums import (
    GRAPH_TYPES_FOR_FORMAT,
    GRAPH_TYPE_NAMES,
    GraphType,
    TableFormat,
)


class GraphTypeDialog(QDialog):
    """Dialog to select a graph type compatible with the current table format."""

    def __init__(
        self,
        table_format: TableFormat,
        current_type: GraphType,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Change Graph Type")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._graph_type = QComboBox()
        for gt in GRAPH_TYPES_FOR_FORMAT.get(table_format, []):
            self._graph_type.addItem(GRAPH_TYPE_NAMES.get(gt, gt.name), gt)

        # Select current
        idx = self._graph_type.findData(current_type)
        if idx >= 0:
            self._graph_type.setCurrentIndex(idx)

        form.addRow("Graph Type:", self._graph_type)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_type(self) -> GraphType:
        return self._graph_type.currentData()
