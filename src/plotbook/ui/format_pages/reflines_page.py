"""Reference / normalisation line controls."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from plotbook.models.enums import LineStyle
from plotbook.models.style import FontSpec, ReferenceLine
from plotbook.ui.symbol_picker import SymbolButton


class ReferenceLinesPage(QWidget):
    """Manage reference/normalisation lines on the graph."""

    changed = pyqtSignal()  # Generic "something changed" signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lines: list[ReferenceLine] = []
        self._updating = False

        layout = QVBoxLayout(self)

        # --- List + add/remove buttons ---
        list_layout = QHBoxLayout()
        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self._list, 1)

        btn_layout = QVBoxLayout()
        self._add_btn = QPushButton("Add")
        self._add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self._add_btn)

        self._remove_btn = QPushButton("Remove")
        self._remove_btn.clicked.connect(self._on_remove)
        btn_layout.addWidget(self._remove_btn)

        self._dup_btn = QPushButton("Duplicate")
        self._dup_btn.clicked.connect(self._on_duplicate)
        btn_layout.addWidget(self._dup_btn)
        btn_layout.addStretch()

        list_layout.addLayout(btn_layout)
        layout.addLayout(list_layout)

        # --- Properties for the selected line ---
        self._props_group = QGroupBox("Line Properties")
        props = QFormLayout(self._props_group)

        self._axis_combo = QComboBox()
        self._axis_combo.addItem("Horizontal (Y value)", "y")
        self._axis_combo.addItem("Vertical (X value)", "x")
        self._axis_combo.currentIndexChanged.connect(self._on_prop_changed)
        props.addRow("Direction:", self._axis_combo)

        self._value_spin = QDoubleSpinBox()
        self._value_spin.setRange(-1e9, 1e9)
        self._value_spin.setDecimals(4)
        self._value_spin.setValue(1.0)
        self._value_spin.valueChanged.connect(self._on_prop_changed)
        props.addRow("Value:", self._value_spin)

        # Color
        color_row = QHBoxLayout()
        self._color_btn = QPushButton("  ")
        self._color_btn.setFixedSize(40, 25)
        self._color_btn.clicked.connect(self._pick_color)
        color_row.addWidget(self._color_btn)
        color_row.addStretch()
        props.addRow("Color:", color_row)

        self._line_style = QComboBox()
        for ls in LineStyle:
            self._line_style.addItem(ls.name.replace("_", " ").title(), ls)
        self._line_style.currentIndexChanged.connect(self._on_prop_changed)
        props.addRow("Style:", self._line_style)

        self._line_width = QDoubleSpinBox()
        self._line_width.setRange(0.5, 8)
        self._line_width.setValue(1.5)
        self._line_width.setSingleStep(0.5)
        self._line_width.valueChanged.connect(self._on_prop_changed)
        props.addRow("Width:", self._line_width)

        self._alpha = QSlider(Qt.Orientation.Horizontal)
        self._alpha.setRange(10, 100)
        self._alpha.setValue(100)
        self._alpha.valueChanged.connect(self._on_prop_changed)
        props.addRow("Opacity:", self._alpha)

        layout.addWidget(self._props_group)

        # --- Label ---
        label_group = QGroupBox("Label")
        label_form = QFormLayout(label_group)

        self._show_label = QCheckBox("Show Label")
        self._show_label.setChecked(True)
        self._show_label.toggled.connect(self._on_prop_changed)
        label_form.addRow("", self._show_label)

        self._label_text = QLineEdit()
        self._label_text.setPlaceholderText("e.g. Normalised = 1")
        self._label_text.textChanged.connect(self._on_prop_changed)
        label_text_row = QHBoxLayout()
        label_text_row.addWidget(self._label_text, 1)
        label_text_row.addWidget(SymbolButton(self._label_text))
        label_form.addRow("Text:", label_text_row)

        self._label_size = QDoubleSpinBox()
        self._label_size.setRange(6, 24)
        self._label_size.setValue(9)
        self._label_size.setSuffix(" pt")
        self._label_size.valueChanged.connect(self._on_prop_changed)
        label_form.addRow("Font Size:", self._label_size)

        self._label_pos = QComboBox()
        # Items change depending on axis, populated in _update_label_pos_items
        self._label_pos.currentIndexChanged.connect(self._on_prop_changed)
        label_form.addRow("Position:", self._label_pos)

        layout.addWidget(label_group)
        layout.addStretch()

        # Disable props until a line is selected
        self._props_group.setEnabled(False)
        label_group.setEnabled(False)
        self._label_group = label_group

    def load(self, lines: list[ReferenceLine]) -> None:
        """Populate from current graph spec."""
        self._updating = True
        self._lines = lines
        self._refresh_list()
        if lines:
            self._list.setCurrentRow(0)
        else:
            self._props_group.setEnabled(False)
            self._label_group.setEnabled(False)
        self._updating = False

    def _refresh_list(self) -> None:
        self._list.blockSignals(True)
        current = self._list.currentRow()
        self._list.clear()
        for rl in self._lines:
            direction = "H" if rl.axis == "y" else "V"
            text = f"{direction} @ {rl.value:g}"
            if rl.label:
                text += f'  "{rl.label}"'
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, rl.id)
            self._list.addItem(item)
        if 0 <= current < self._list.count():
            self._list.setCurrentRow(current)
        self._list.blockSignals(False)

    def _selected_line(self) -> ReferenceLine | None:
        row = self._list.currentRow()
        if 0 <= row < len(self._lines):
            return self._lines[row]
        return None

    def _on_selection_changed(self, row: int) -> None:
        rl = self._selected_line()
        enabled = rl is not None
        self._props_group.setEnabled(enabled)
        self._label_group.setEnabled(enabled)
        if rl:
            self._load_props(rl)

    def _load_props(self, rl: ReferenceLine) -> None:
        self._updating = True

        idx = self._axis_combo.findData(rl.axis)
        if idx >= 0:
            self._axis_combo.setCurrentIndex(idx)

        self._value_spin.setValue(rl.value)
        self._set_color_btn(rl.color)

        idx = self._line_style.findData(rl.line_style)
        if idx >= 0:
            self._line_style.setCurrentIndex(idx)
        self._line_width.setValue(rl.line_width)
        self._alpha.setValue(int(rl.alpha * 100))

        self._show_label.setChecked(rl.show_label)
        self._label_text.setText(rl.label)
        self._label_size.setValue(rl.label_font.size)

        self._update_label_pos_items(rl.axis)
        idx = self._label_pos.findData(rl.label_position)
        if idx >= 0:
            self._label_pos.setCurrentIndex(idx)

        self._updating = False

    def _update_label_pos_items(self, axis: str) -> None:
        self._label_pos.blockSignals(True)
        self._label_pos.clear()
        if axis == "y":
            self._label_pos.addItem("Right", "right")
            self._label_pos.addItem("Left", "left")
            self._label_pos.addItem("Center", "center")
        else:
            self._label_pos.addItem("Top", "top")
            self._label_pos.addItem("Bottom", "bottom")
            self._label_pos.addItem("Center", "center")
        self._label_pos.blockSignals(False)

    def _on_prop_changed(self, *_args) -> None:
        if self._updating:
            return
        rl = self._selected_line()
        if rl is None:
            return

        new_axis = self._axis_combo.currentData()
        if new_axis != rl.axis:
            rl.axis = new_axis
            self._update_label_pos_items(new_axis)

        rl.value = self._value_spin.value()
        rl.color = self._color_btn.property("color") or rl.color
        rl.line_style = self._line_style.currentData() or rl.line_style
        rl.line_width = self._line_width.value()
        rl.alpha = self._alpha.value() / 100.0

        rl.show_label = self._show_label.isChecked()
        rl.label = self._label_text.text()
        rl.label_font.size = self._label_size.value()
        pos = self._label_pos.currentData()
        if pos:
            rl.label_position = pos

        self._refresh_list()
        self.changed.emit()

    def _on_add(self) -> None:
        rl = ReferenceLine(value=1.0, label="Normalised")
        self._lines.append(rl)
        self._refresh_list()
        self._list.setCurrentRow(len(self._lines) - 1)
        self.changed.emit()

    def _on_remove(self) -> None:
        row = self._list.currentRow()
        if 0 <= row < len(self._lines):
            self._lines.pop(row)
            self._refresh_list()
            if self._lines:
                self._list.setCurrentRow(min(row, len(self._lines) - 1))
            else:
                self._props_group.setEnabled(False)
                self._label_group.setEnabled(False)
            self.changed.emit()

    def _on_duplicate(self) -> None:
        rl = self._selected_line()
        if rl is None:
            return
        new_rl = ReferenceLine.from_dict(rl.to_dict())
        import uuid
        new_rl.id = uuid.uuid4().hex[:8]
        new_rl.value += 0.5
        self._lines.append(new_rl)
        self._refresh_list()
        self._list.setCurrentRow(len(self._lines) - 1)
        self.changed.emit()

    def _set_color_btn(self, color: str) -> None:
        self._color_btn.setStyleSheet(
            f"background-color: {color}; border: 1px solid #888;"
        )
        self._color_btn.setProperty("color", color)

    def _pick_color(self) -> None:
        current = self._color_btn.property("color") or "#333333"
        color = QColorDialog.getColor(QColor(current), self, "Line Color")
        if color.isValid():
            self._set_color_btn(color.name())
            self._on_prop_changed()
