"""Title styling controls."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from plotbook.models.style import TitleStyle
from plotbook.ui.symbol_picker import SymbolButton


class TitlePage(QWidget):
    """Controls for graph title."""

    titleChanged = pyqtSignal(str, object)  # (attr_path, value)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating = False

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._text = QPlainTextEdit()
        self._text.setPlaceholderText("Graph Title (Enter for new line)")
        self._text.setMaximumHeight(50)
        self._text.textChanged.connect(
            lambda: self._emit("text", self._text.toPlainText())
        )
        title_row = QHBoxLayout()
        title_row.addWidget(self._text, 1)
        title_row.addWidget(SymbolButton(self._text))
        form.addRow("Title:", title_row)

        self._font_family = QComboBox()
        for font in ["Arial", "Times New Roman", "Helvetica", "Courier New",
                      "Georgia", "Verdana", "Calibri"]:
            self._font_family.addItem(font)
        self._font_family.currentTextChanged.connect(
            lambda t: self._emit("font.family", t)
        )
        form.addRow("Font:", self._font_family)

        self._font_size = QDoubleSpinBox()
        self._font_size.setRange(8, 48)
        self._font_size.setValue(14)
        self._font_size.valueChanged.connect(lambda v: self._emit("font.size", v))
        form.addRow("Size:", self._font_size)

        self._bold = QCheckBox("Bold")
        self._bold.setChecked(True)
        self._bold.toggled.connect(lambda v: self._emit("font.bold", v))
        form.addRow("", self._bold)

        self._italic = QCheckBox("Italic")
        self._italic.toggled.connect(lambda v: self._emit("font.italic", v))
        form.addRow("", self._italic)

        layout.addLayout(form)
        layout.addStretch()

    def load(self, style: TitleStyle) -> None:
        self._updating = True
        self._text.setPlainText(style.text)
        idx = self._font_family.findText(style.font.family)
        if idx >= 0:
            self._font_family.setCurrentIndex(idx)
        self._font_size.setValue(style.font.size)
        self._bold.setChecked(style.font.bold)
        self._italic.setChecked(style.font.italic)
        self._updating = False

    def _emit(self, attr: str, value) -> None:
        if not self._updating:
            self.titleChanged.emit(attr, value)
