"""Trendline controls."""

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
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from plotbook.models.enums import (
    LineStyle,
    TrendlineType,
    TRENDLINE_TYPE_NAMES,
)
from plotbook.models.style import Trendline


class TrendlinePage(QWidget):
    """Controls for adding a trendline to XY graphs."""

    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._trendline: Trendline | None = None
        self._updating = False

        layout = QVBoxLayout(self)

        # Fit type
        form = QFormLayout()
        self._type_combo = QComboBox()
        for tt, label in TRENDLINE_TYPE_NAMES.items():
            self._type_combo.addItem(label, tt)
        self._type_combo.currentIndexChanged.connect(self._on_changed)
        form.addRow("Fit Type:", self._type_combo)
        layout.addLayout(form)

        # Line style group
        line_group = QGroupBox("Line")
        line_form = QFormLayout(line_group)

        self._color_btn = QPushButton("  ")
        self._color_btn.setFixedSize(40, 25)
        self._color_btn.clicked.connect(self._pick_color)
        color_row = QHBoxLayout()
        color_row.addWidget(self._color_btn)
        color_row.addStretch()
        line_form.addRow("Color:", color_row)

        self._line_style = QComboBox()
        for ls in LineStyle:
            self._line_style.addItem(ls.name.replace("_", " ").title(), ls)
        self._line_style.currentIndexChanged.connect(self._on_changed)
        line_form.addRow("Style:", self._line_style)

        self._line_width = QDoubleSpinBox()
        self._line_width.setRange(0.5, 8)
        self._line_width.setValue(1.5)
        self._line_width.setSingleStep(0.5)
        self._line_width.valueChanged.connect(self._on_changed)
        line_form.addRow("Width:", self._line_width)

        self._extrapolate = QDoubleSpinBox()
        self._extrapolate.setRange(0, 50)
        self._extrapolate.setValue(0)
        self._extrapolate.setSingleStep(5)
        self._extrapolate.setSuffix(" %")
        self._extrapolate.setToolTip("Extend the trendline beyond the data range")
        self._extrapolate.valueChanged.connect(self._on_changed)
        line_form.addRow("Extrapolate:", self._extrapolate)

        layout.addWidget(line_group)

        # Equation / R² group
        eq_group = QGroupBox("Equation / R\u00b2")
        eq_form = QFormLayout(eq_group)

        self._show_equation = QCheckBox("Show Equation")
        self._show_equation.setChecked(True)
        self._show_equation.toggled.connect(self._on_changed)
        eq_form.addRow("", self._show_equation)

        self._show_r2 = QCheckBox("Show R\u00b2")
        self._show_r2.setChecked(True)
        self._show_r2.toggled.connect(self._on_changed)
        eq_form.addRow("", self._show_r2)

        self._eq_font_size = QDoubleSpinBox()
        self._eq_font_size.setRange(6, 24)
        self._eq_font_size.setValue(9)
        self._eq_font_size.setSuffix(" pt")
        self._eq_font_size.valueChanged.connect(self._on_changed)
        eq_form.addRow("Font Size:", self._eq_font_size)

        self._eq_position = QComboBox()
        self._eq_position.addItem("Top Left", "top_left")
        self._eq_position.addItem("Top Right", "top_right")
        self._eq_position.addItem("Bottom Left", "bottom_left")
        self._eq_position.addItem("Bottom Right", "bottom_right")
        self._eq_position.currentIndexChanged.connect(self._on_changed)
        eq_form.addRow("Position:", self._eq_position)

        layout.addWidget(eq_group)
        layout.addStretch()

    def load(self, trendline: Trendline) -> None:
        self._updating = True
        self._trendline = trendline

        idx = self._type_combo.findData(trendline.fit_type)
        if idx >= 0:
            self._type_combo.setCurrentIndex(idx)

        self._set_color(trendline.color)

        idx = self._line_style.findData(trendline.line_style)
        if idx >= 0:
            self._line_style.setCurrentIndex(idx)
        self._line_width.setValue(trendline.line_width)
        self._extrapolate.setValue(trendline.extrapolate_pct)

        self._show_equation.setChecked(trendline.show_equation)
        self._show_r2.setChecked(trendline.show_r_squared)
        self._eq_font_size.setValue(trendline.equation_font.size)

        idx = self._eq_position.findData(trendline.equation_position)
        if idx >= 0:
            self._eq_position.setCurrentIndex(idx)

        self._updating = False

    def _on_changed(self, *_) -> None:
        if self._updating or self._trendline is None:
            return

        self._trendline.fit_type = self._type_combo.currentData() or TrendlineType.NONE
        self._trendline.color = self._color_btn.property("color") or self._trendline.color
        self._trendline.line_style = self._line_style.currentData() or self._trendline.line_style
        self._trendline.line_width = self._line_width.value()
        self._trendline.extrapolate_pct = self._extrapolate.value()
        self._trendline.show_equation = self._show_equation.isChecked()
        self._trendline.show_r_squared = self._show_r2.isChecked()
        self._trendline.equation_font.size = self._eq_font_size.value()
        self._trendline.equation_position = self._eq_position.currentData() or "top_left"

        self.changed.emit()

    def _set_color(self, color: str) -> None:
        self._color_btn.setStyleSheet(f"background-color: {color}; border: 1px solid #888;")
        self._color_btn.setProperty("color", color)

    def _pick_color(self) -> None:
        cur = self._color_btn.property("color") or "#FF0000"
        c = QColorDialog.getColor(QColor(cur), self)
        if c.isValid():
            self._set_color(c.name())
            self._on_changed()
