"""Legend styling controls."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QVBoxLayout,
    QWidget,
)

from plotbook.models.enums import LegendPosition
from plotbook.models.style import LegendStyle


class LegendPage(QWidget):
    """Controls for legend configuration."""

    legendChanged = pyqtSignal(str, object)  # (attr, value)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating = False

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._show = QCheckBox("Show Legend")
        self._show.setChecked(True)
        self._show.toggled.connect(lambda v: self._emit("show", v))
        form.addRow("", self._show)

        self._position = QComboBox()
        pos_items = [
            ("Best", LegendPosition.BEST),
            ("Upper Right", LegendPosition.TOP_RIGHT),
            ("Upper Left", LegendPosition.TOP_LEFT),
            ("Lower Right", LegendPosition.BOTTOM_RIGHT),
            ("Lower Left", LegendPosition.BOTTOM_LEFT),
            ("Center Right", LegendPosition.CENTER_RIGHT),
            ("Center Left", LegendPosition.CENTER_LEFT),
            ("Upper Center", LegendPosition.UPPER_CENTER),
            ("Lower Center", LegendPosition.LOWER_CENTER),
        ]
        for label, val in pos_items:
            self._position.addItem(label, val)
        self._position.currentIndexChanged.connect(
            lambda: self._emit("position", self._position.currentData())
        )
        form.addRow("Position:", self._position)

        self._font_size = QDoubleSpinBox()
        self._font_size.setRange(6, 24)
        self._font_size.setValue(10)
        self._font_size.valueChanged.connect(lambda v: self._emit("font.size", v))
        form.addRow("Font Size:", self._font_size)

        self._frame = QCheckBox("Show Frame")
        self._frame.setChecked(True)
        self._frame.toggled.connect(lambda v: self._emit("frame", v))
        form.addRow("", self._frame)

        layout.addLayout(form)
        layout.addStretch()

    def load(self, style: LegendStyle) -> None:
        self._updating = True
        self._show.setChecked(style.show)
        idx = self._position.findData(style.position)
        if idx >= 0:
            self._position.setCurrentIndex(idx)
        self._font_size.setValue(style.font.size)
        self._frame.setChecked(style.frame)
        self._updating = False

    def _emit(self, attr: str, value) -> None:
        if not self._updating:
            self.legendChanged.emit(attr, value)
