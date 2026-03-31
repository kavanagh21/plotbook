"""Error bar styling controls."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QVBoxLayout,
    QWidget,
)

from plotbook.models.enums import ErrorBarDirection, ErrorBarType
from plotbook.models.style import ErrorBarConfig


class ErrorBarsPage(QWidget):
    """Controls for error bar configuration."""

    errorBarsChanged = pyqtSignal(str, object)  # (attr, value)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating = False

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._type = QComboBox()
        type_items = [
            ("None", ErrorBarType.NONE),
            ("Standard Deviation (SD)", ErrorBarType.SD),
            ("Standard Error (SEM)", ErrorBarType.SEM),
            ("95% Confidence Interval", ErrorBarType.CI95),
            ("99% Confidence Interval", ErrorBarType.CI99),
            ("Range", ErrorBarType.RANGE),
        ]
        for label, val in type_items:
            self._type.addItem(label, val)
        self._type.currentIndexChanged.connect(
            lambda: self._emit("error_type", self._type.currentData())
        )
        form.addRow("Type:", self._type)

        self._direction = QComboBox()
        dir_items = [
            ("Both", ErrorBarDirection.BOTH),
            ("Above Only", ErrorBarDirection.ABOVE),
            ("Below Only", ErrorBarDirection.BELOW),
        ]
        for label, val in dir_items:
            self._direction.addItem(label, val)
        self._direction.currentIndexChanged.connect(
            lambda: self._emit("direction", self._direction.currentData())
        )
        form.addRow("Direction:", self._direction)

        self._cap_width = QDoubleSpinBox()
        self._cap_width.setRange(0, 20)
        self._cap_width.setValue(4)
        self._cap_width.setSingleStep(1)
        self._cap_width.valueChanged.connect(lambda v: self._emit("cap_width", v))
        form.addRow("Cap Width:", self._cap_width)

        self._line_width = QDoubleSpinBox()
        self._line_width.setRange(0.5, 5)
        self._line_width.setValue(1.0)
        self._line_width.setSingleStep(0.5)
        self._line_width.valueChanged.connect(lambda v: self._emit("line_width", v))
        form.addRow("Line Width:", self._line_width)

        layout.addLayout(form)
        layout.addStretch()

    def load(self, config: ErrorBarConfig) -> None:
        self._updating = True
        idx = self._type.findData(config.error_type)
        if idx >= 0:
            self._type.setCurrentIndex(idx)
        idx = self._direction.findData(config.direction)
        if idx >= 0:
            self._direction.setCurrentIndex(idx)
        self._cap_width.setValue(config.cap_width)
        self._line_width.setValue(config.line_width)
        self._updating = False

    def _emit(self, attr: str, value) -> None:
        if not self._updating:
            self.errorBarsChanged.emit(attr, value)
