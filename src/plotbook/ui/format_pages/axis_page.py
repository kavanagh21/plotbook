"""Axis styling controls."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from plotbook.models.enums import LineStyle
from plotbook.models.style import AxisStyle
from plotbook.ui.symbol_picker import SymbolButton

_FONT_FAMILIES = [
    "Arial", "Times New Roman", "Helvetica", "Courier New",
    "Georgia", "Verdana", "Calibri", "Tahoma", "Palatino",
]


class AxisPage(QWidget):
    """Controls for one axis (X or Y)."""

    axisChanged = pyqtSignal(str, object)  # (attr_path, value)

    def __init__(self, axis_name: str = "X Axis", parent=None):
        super().__init__(parent)
        self._axis_name = axis_name
        self._updating = False

        layout = QVBoxLayout(self)

        # --- Axis Label ---
        label_group = QGroupBox("Axis Label")
        label_form = QFormLayout(label_group)

        self._label_text = QPlainTextEdit()
        self._label_text.setPlaceholderText("Enter axis label (Enter for new line)")
        self._label_text.setMaximumHeight(50)
        self._label_text.textChanged.connect(
            lambda: self._emit("label", self._label_text.toPlainText())
        )
        label_row = QHBoxLayout()
        label_row.addWidget(self._label_text, 1)
        label_row.addWidget(SymbolButton(self._label_text))
        label_form.addRow("Text:", label_row)

        self._label_font_family = QComboBox()
        for font in _FONT_FAMILIES:
            self._label_font_family.addItem(font)
        self._label_font_family.currentTextChanged.connect(
            lambda t: self._emit("label_font.family", t)
        )
        label_form.addRow("Font:", self._label_font_family)

        self._label_font_size = QDoubleSpinBox()
        self._label_font_size.setRange(6, 48)
        self._label_font_size.setValue(12)
        self._label_font_size.setSingleStep(1)
        self._label_font_size.setSuffix(" pt")
        self._label_font_size.valueChanged.connect(
            lambda v: self._emit("label_font.size", v)
        )
        label_form.addRow("Font Size:", self._label_font_size)

        self._label_bold = QCheckBox("Bold")
        self._label_bold.toggled.connect(lambda v: self._emit("label_font.bold", v))
        label_form.addRow("", self._label_bold)

        self._label_italic = QCheckBox("Italic")
        self._label_italic.toggled.connect(lambda v: self._emit("label_font.italic", v))
        label_form.addRow("", self._label_italic)

        self._label_pad = QDoubleSpinBox()
        self._label_pad.setRange(0, 40)
        self._label_pad.setValue(4)
        self._label_pad.setSingleStep(2)
        self._label_pad.setSuffix(" pt")
        self._label_pad.setToolTip("Spacing between the axis label and the tick labels")
        self._label_pad.valueChanged.connect(lambda v: self._emit("label_pad", v))
        label_form.addRow("Spacing:", self._label_pad)

        layout.addWidget(label_group)

        # --- Tick Labels ---
        tick_group = QGroupBox("Tick Labels (numbers on axis)")
        tick_form = QFormLayout(tick_group)

        self._tick_font_family = QComboBox()
        for font in _FONT_FAMILIES:
            self._tick_font_family.addItem(font)
        self._tick_font_family.currentTextChanged.connect(
            lambda t: self._emit("tick_font.family", t)
        )
        tick_form.addRow("Font:", self._tick_font_family)

        self._tick_font_size = QDoubleSpinBox()
        self._tick_font_size.setRange(6, 36)
        self._tick_font_size.setValue(10)
        self._tick_font_size.setSingleStep(1)
        self._tick_font_size.setSuffix(" pt")
        self._tick_font_size.valueChanged.connect(
            lambda v: self._emit("tick_font.size", v)
        )
        tick_form.addRow("Font Size:", self._tick_font_size)

        self._tick_bold = QCheckBox("Bold")
        self._tick_bold.toggled.connect(lambda v: self._emit("tick_font.bold", v))
        tick_form.addRow("", self._tick_bold)

        self._tick_angle = QSpinBox()
        self._tick_angle.setRange(-90, 90)
        self._tick_angle.setValue(0)
        self._tick_angle.setSingleStep(15)
        self._tick_angle.setSuffix("\u00b0")
        self._tick_angle.setToolTip(
            "Rotate tick labels to prevent overlap.\n"
            "Common values: 45\u00b0 for diagonal, 90\u00b0 for vertical."
        )
        self._tick_angle.valueChanged.connect(
            lambda v: self._emit("tick_angle", float(v))
        )
        tick_form.addRow("Angle:", self._tick_angle)

        self._tick_newline_sep = QComboBox()
        self._tick_newline_sep.setEditable(True)
        self._tick_newline_sep.addItem("(none)", "")
        self._tick_newline_sep.addItem("Space", " ")
        self._tick_newline_sep.addItem("/ (slash)", "/")
        self._tick_newline_sep.addItem("- (dash)", "-")
        self._tick_newline_sep.addItem("_ (underscore)", "_")
        self._tick_newline_sep.addItem(", (comma)", ",")
        self._tick_newline_sep.setToolTip(
            "Split tick labels into multiple lines at this character.\n"
            "E.g. choose Space to turn 'Group A' into 'Group\\nA'.\n"
            "You can also type a custom separator."
        )
        self._tick_newline_sep.currentIndexChanged.connect(self._on_newline_sep_changed)
        self._tick_newline_sep.lineEdit().editingFinished.connect(
            self._on_newline_sep_edited
        )
        tick_form.addRow("Wrap at:", self._tick_newline_sep)

        layout.addWidget(tick_group)

        # --- Range ---
        range_group = QGroupBox("Range")
        range_form = QFormLayout(range_group)

        self._min_val = QDoubleSpinBox()
        self._min_val.setRange(-1e9, 1e9)
        self._min_val.setSpecialValueText("Auto")
        self._min_val.setValue(self._min_val.minimum())
        self._min_val.valueChanged.connect(self._on_min_changed)
        min_row = QHBoxLayout()
        min_row.addWidget(self._min_val, 1)
        self._min_auto_btn = QPushButton("Auto")
        self._min_auto_btn.setFixedWidth(40)
        self._min_auto_btn.clicked.connect(
            lambda: self._min_val.setValue(self._min_val.minimum())
        )
        min_row.addWidget(self._min_auto_btn)
        range_form.addRow("Min:", min_row)

        self._max_val = QDoubleSpinBox()
        self._max_val.setRange(-1e9, 1e9)
        self._max_val.setSpecialValueText("Auto")
        self._max_val.setValue(self._max_val.minimum())
        self._max_val.valueChanged.connect(self._on_max_changed)
        max_row = QHBoxLayout()
        max_row.addWidget(self._max_val, 1)
        self._max_auto_btn = QPushButton("Auto")
        self._max_auto_btn.setFixedWidth(40)
        self._max_auto_btn.clicked.connect(
            lambda: self._max_val.setValue(self._max_val.minimum())
        )
        max_row.addWidget(self._max_auto_btn)
        range_form.addRow("Max:", max_row)

        self._log_scale = QCheckBox("Log Scale")
        self._log_scale.toggled.connect(lambda v: self._emit("log_scale", v))
        range_form.addRow("", self._log_scale)

        self._exponent_in_label = QCheckBox("Exponent in label")
        self._exponent_in_label.setChecked(True)
        self._exponent_in_label.setToolTip(
            "When ticks use scientific notation (e.g. 1e-7),\n"
            "move the exponent into the axis label as [\u00d710\u207b\u2077]\n"
            "instead of showing it floating at the axis edge."
        )
        self._exponent_in_label.toggled.connect(
            lambda v: self._emit("exponent_in_label", v)
        )
        range_form.addRow("", self._exponent_in_label)

        self._invert = QCheckBox("Invert")
        self._invert.toggled.connect(lambda v: self._emit("invert", v))
        range_form.addRow("", self._invert)

        layout.addWidget(range_group)

        # --- Grid ---
        grid_group = QGroupBox("Grid Lines")
        grid_form = QFormLayout(grid_group)

        self._show_grid = QCheckBox("Show Grid")
        self._show_grid.toggled.connect(lambda v: self._emit("show_grid", v))
        grid_form.addRow("", self._show_grid)

        self._grid_style = QComboBox()
        for ls in LineStyle:
            self._grid_style.addItem(ls.name.replace("_", " ").title(), ls)
        self._grid_style.currentIndexChanged.connect(
            lambda: self._emit("grid_line_style", self._grid_style.currentData())
        )
        grid_form.addRow("Style:", self._grid_style)

        layout.addWidget(grid_group)
        layout.addStretch()

    def load(self, style: AxisStyle) -> None:
        self._updating = True
        self._label_text.setPlainText(style.label)

        idx = self._label_font_family.findText(style.label_font.family)
        if idx >= 0:
            self._label_font_family.setCurrentIndex(idx)
        self._label_font_size.setValue(style.label_font.size)
        self._label_bold.setChecked(style.label_font.bold)
        self._label_italic.setChecked(style.label_font.italic)
        self._label_pad.setValue(style.label_pad)

        idx = self._tick_font_family.findText(style.tick_font.family)
        if idx >= 0:
            self._tick_font_family.setCurrentIndex(idx)
        self._tick_font_size.setValue(style.tick_font.size)
        self._tick_bold.setChecked(style.tick_font.bold)

        self._tick_angle.setValue(int(style.tick_angle))

        # Load newline separator
        sep = style.tick_newline_sep
        matched = False
        for i in range(self._tick_newline_sep.count()):
            if self._tick_newline_sep.itemData(i) == sep:
                self._tick_newline_sep.setCurrentIndex(i)
                matched = True
                break
        if not matched and sep:
            self._tick_newline_sep.setEditText(sep)

        if style.min_val is not None:
            self._min_val.setValue(style.min_val)
        else:
            self._min_val.setValue(self._min_val.minimum())

        if style.max_val is not None:
            self._max_val.setValue(style.max_val)
        else:
            self._max_val.setValue(self._max_val.minimum())

        self._log_scale.setChecked(style.log_scale)
        self._exponent_in_label.setChecked(style.exponent_in_label)
        self._invert.setChecked(style.invert)
        self._show_grid.setChecked(style.show_grid)

        idx = self._grid_style.findData(style.grid_line_style)
        if idx >= 0:
            self._grid_style.setCurrentIndex(idx)

        self._updating = False

    def _on_newline_sep_changed(self, index: int) -> None:
        if self._updating:
            return
        data = self._tick_newline_sep.itemData(index)
        if data is not None:
            self._emit("tick_newline_sep", data)

    def _on_newline_sep_edited(self) -> None:
        if self._updating:
            return
        text = self._tick_newline_sep.currentText()
        # If the text matches a known item's display text, use the item data
        for i in range(self._tick_newline_sep.count()):
            if self._tick_newline_sep.itemText(i) == text:
                data = self._tick_newline_sep.itemData(i)
                if data is not None:
                    self._emit("tick_newline_sep", data)
                    return
        # Otherwise treat the typed text as the literal separator
        self._emit("tick_newline_sep", text)

    def _on_min_changed(self, value: float) -> None:
        if value == self._min_val.minimum():
            self._emit("min_val", None)
        else:
            self._emit("min_val", value)

    def _on_max_changed(self, value: float) -> None:
        if value == self._max_val.minimum():
            self._emit("max_val", None)
        else:
            self._emit("max_val", value)

    def _emit(self, attr: str, value) -> None:
        if not self._updating:
            self.axisChanged.emit(attr, value)
