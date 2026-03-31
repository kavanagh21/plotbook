"""Series styling controls."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
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
    QSlider,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt

from plotbook.models.enums import LineStyle, MarkerShape
from plotbook.models.style import SeriesStyle


class SeriesPage(QWidget):
    """Controls for styling the currently selected series."""

    styleChanged = pyqtSignal(str, str, object)  # (series_id, attr, value)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._series_map: dict[str, SeriesStyle] = {}  # id -> style
        self._series_names: dict[str, str] = {}  # id -> name
        self._updating = False

        layout = QVBoxLayout(self)

        # Series selector
        self._series_combo = QComboBox()
        self._series_combo.currentIndexChanged.connect(self._on_series_changed)
        layout.addWidget(self._series_combo)

        # Color
        color_layout = QHBoxLayout()
        self._color_button = QPushButton("  ")
        self._color_button.setFixedSize(40, 25)
        self._color_button.clicked.connect(self._pick_color)
        color_layout.addWidget(self._color_button)
        color_layout.addStretch()
        form = QFormLayout()
        form.addRow("Color:", color_layout)
        layout.addLayout(form)

        # Markers group
        marker_group = QGroupBox("Markers")
        marker_form = QFormLayout(marker_group)

        self._marker_shape = QComboBox()
        for ms in MarkerShape:
            self._marker_shape.addItem(ms.name.replace("_", " ").title(), ms)
        self._marker_shape.currentIndexChanged.connect(
            lambda: self._emit("marker_shape", self._marker_shape.currentData())
        )
        marker_form.addRow("Shape:", self._marker_shape)

        self._marker_size = QDoubleSpinBox()
        self._marker_size.setRange(1, 30)
        self._marker_size.setValue(6)
        self._marker_size.valueChanged.connect(lambda v: self._emit("marker_size", v))
        marker_form.addRow("Size:", self._marker_size)

        self._marker_fill = QCheckBox("Filled")
        self._marker_fill.setChecked(True)
        self._marker_fill.toggled.connect(lambda v: self._emit("marker_fill", v))
        marker_form.addRow("", self._marker_fill)

        layout.addWidget(marker_group)

        # Lines group
        line_group = QGroupBox("Lines")
        line_form = QFormLayout(line_group)

        self._show_line = QCheckBox("Show Line")
        self._show_line.setChecked(True)
        self._show_line.toggled.connect(lambda v: self._emit("show_line", v))
        line_form.addRow("", self._show_line)

        self._line_style = QComboBox()
        for ls in LineStyle:
            self._line_style.addItem(ls.name.replace("_", " ").title(), ls)
        self._line_style.currentIndexChanged.connect(
            lambda: self._emit("line_style", self._line_style.currentData())
        )
        line_form.addRow("Style:", self._line_style)

        self._line_width = QDoubleSpinBox()
        self._line_width.setRange(0.5, 10)
        self._line_width.setValue(1.5)
        self._line_width.setSingleStep(0.5)
        self._line_width.valueChanged.connect(lambda v: self._emit("line_width", v))
        line_form.addRow("Width:", self._line_width)

        layout.addWidget(line_group)

        # Bars group
        bar_group = QGroupBox("Bars")
        bar_form = QFormLayout(bar_group)

        self._bar_width = QDoubleSpinBox()
        self._bar_width.setRange(0.1, 1.0)
        self._bar_width.setValue(0.8)
        self._bar_width.setSingleStep(0.1)
        self._bar_width.valueChanged.connect(lambda v: self._emit("bar_width", v))
        bar_form.addRow("Width:", self._bar_width)

        self._bar_alpha = QSlider(Qt.Orientation.Horizontal)
        self._bar_alpha.setRange(10, 100)
        self._bar_alpha.setValue(100)
        self._bar_alpha.valueChanged.connect(lambda v: self._emit("bar_alpha", v / 100.0))
        bar_form.addRow("Opacity:", self._bar_alpha)

        self._bar_edge_width = QDoubleSpinBox()
        self._bar_edge_width.setRange(0, 5)
        self._bar_edge_width.setValue(1.0)
        self._bar_edge_width.setSingleStep(0.5)
        self._bar_edge_width.valueChanged.connect(lambda v: self._emit("bar_edge_width", v))
        bar_form.addRow("Edge Width:", self._bar_edge_width)

        layout.addWidget(bar_group)
        layout.addStretch()

    def load(self, series_styles: dict[str, SeriesStyle],
             series_names: dict[str, str]) -> None:
        """Populate from current graph spec."""
        self._updating = True
        self._series_map = series_styles
        self._series_names = series_names

        self._series_combo.clear()
        for sid, name in series_names.items():
            self._series_combo.addItem(name, sid)

        if series_names:
            self._series_combo.setCurrentIndex(0)
            self._load_style(list(series_styles.values())[0] if series_styles else None)

        self._updating = False

    def _on_series_changed(self, index: int) -> None:
        if self._updating or index < 0:
            return
        sid = self._series_combo.currentData()
        if sid and sid in self._series_map:
            self._updating = True
            self._load_style(self._series_map[sid])
            self._updating = False

    def _load_style(self, style: SeriesStyle | None) -> None:
        if style is None:
            return
        self._set_color_button(style.color)

        idx = self._marker_shape.findData(style.marker_shape)
        if idx >= 0:
            self._marker_shape.setCurrentIndex(idx)
        self._marker_size.setValue(style.marker_size)
        self._marker_fill.setChecked(style.marker_fill)

        self._show_line.setChecked(style.show_line)
        idx = self._line_style.findData(style.line_style)
        if idx >= 0:
            self._line_style.setCurrentIndex(idx)
        self._line_width.setValue(style.line_width)

        self._bar_width.setValue(style.bar_width)
        self._bar_alpha.setValue(int(style.bar_alpha * 100))
        self._bar_edge_width.setValue(style.bar_edge_width)

    def _set_color_button(self, color: str) -> None:
        self._color_button.setStyleSheet(
            f"background-color: {color}; border: 1px solid #888;"
        )
        self._color_button.setProperty("color", color)

    def _pick_color(self) -> None:
        current = self._color_button.property("color") or "#1f77b4"
        color = QColorDialog.getColor(QColor(current), self, "Series Color")
        if color.isValid():
            hex_color = color.name()
            self._set_color_button(hex_color)
            self._emit("color", hex_color)

    def _emit(self, attr: str, value) -> None:
        if self._updating:
            return
        sid = self._series_combo.currentData()
        if sid:
            self.styleChanged.emit(sid, attr, value)
