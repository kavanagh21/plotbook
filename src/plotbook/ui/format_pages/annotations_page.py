"""Bar annotation and comparison bracket controls."""

from __future__ import annotations

import math
import uuid


def _log10(x: float) -> float:
    """Safe log10 for adaptive step calculation."""
    if x <= 0:
        return 0
    return math.log10(x)

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
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from plotbook.models.style import BarAnnotation, ComparisonBracket, FontSpec
from plotbook.ui.symbol_picker import SymbolButton


class AnnotationsPage(QWidget):
    """Manage bar annotations (text above bars) and comparison brackets."""

    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._annotations: list[BarAnnotation] = []
        self._brackets: list[ComparisonBracket] = []
        self._updating = False

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        self._ann_tab = _BarAnnotationsTab()
        self._ann_tab.changed.connect(self._emit_changed)
        self._brk_tab = _BracketsTab()
        self._brk_tab.changed.connect(self._emit_changed)

        tabs.addTab(self._ann_tab, "Labels")
        tabs.addTab(self._brk_tab, "Brackets")
        layout.addWidget(tabs)

    def load(self, annotations: list[BarAnnotation],
             brackets: list[ComparisonBracket],
             bar_names: list[str],
             y_range: float = 10.0) -> None:
        self._annotations = annotations
        self._brackets = brackets
        self._ann_tab.load(annotations, bar_names, y_range)
        self._brk_tab.load(brackets, bar_names, y_range)

    def _emit_changed(self) -> None:
        self.changed.emit()


class _BarAnnotationsTab(QWidget):
    """Tab for text labels above individual bars."""

    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[BarAnnotation] = []
        self._bar_names: list[str] = []
        self._updating = False

        layout = QVBoxLayout(self)

        # List + buttons
        list_row = QHBoxLayout()
        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_selection)
        list_row.addWidget(self._list, 1)

        btn_col = QVBoxLayout()
        btn_col.addWidget(self._make_btn("Add", self._on_add))
        btn_col.addWidget(self._make_btn("Remove", self._on_remove))
        btn_col.addStretch()
        list_row.addLayout(btn_col)
        layout.addLayout(list_row)

        # Properties
        self._props = QGroupBox("Label Properties")
        form = QFormLayout(self._props)

        self._bar_combo = QComboBox()
        self._bar_combo.currentIndexChanged.connect(self._on_prop)
        form.addRow("Bar:", self._bar_combo)

        self._text = QLineEdit()
        self._text.setPlaceholderText("e.g. *, **, ns, p<0.05")
        self._text.textChanged.connect(self._on_prop)
        text_row = QHBoxLayout()
        text_row.addWidget(self._text, 1)
        text_row.addWidget(SymbolButton(self._text))
        form.addRow("Text:", text_row)

        self._font_size = QDoubleSpinBox()
        self._font_size.setRange(6, 36)
        self._font_size.setValue(12)
        self._font_size.setSuffix(" pt")
        self._font_size.valueChanged.connect(self._on_prop)
        form.addRow("Font Size:", self._font_size)

        self._bold = QCheckBox("Bold")
        self._bold.setChecked(True)
        self._bold.toggled.connect(self._on_prop)
        form.addRow("", self._bold)

        self._color_btn = QPushButton("  ")
        self._color_btn.setFixedSize(40, 25)
        self._color_btn.clicked.connect(self._pick_color)
        color_row = QHBoxLayout()
        color_row.addWidget(self._color_btn)
        color_row.addStretch()
        form.addRow("Color:", color_row)

        self._y_offset = QDoubleSpinBox()
        self._y_offset.setRange(-1e6, 1e6)
        self._y_offset.setValue(0)
        self._y_offset.setDecimals(4)
        self._y_offset.setSingleStep(0.001)
        self._y_offset.setToolTip(
            "Extra vertical offset above the bar (data units).\n"
            "Use the scroll wheel or type a value directly."
        )
        self._y_offset.valueChanged.connect(self._on_prop)
        form.addRow("Y Offset:", self._y_offset)

        self._props.setEnabled(False)
        layout.addWidget(self._props)

    def load(self, items: list[BarAnnotation], bar_names: list[str],
             y_range: float = 10.0) -> None:
        self._updating = True
        self._items = items
        self._bar_names = bar_names
        self._bar_combo.clear()
        for i, name in enumerate(bar_names):
            self._bar_combo.addItem(f"{i}: {name}", i)
        # Adaptive step: ~1% of the data range
        step = max(abs(y_range) * 0.01, 1e-6)
        self._y_offset.setSingleStep(step)
        self._y_offset.setDecimals(max(0, 4 - int(max(0, _log10(abs(y_range))))))
        self._refresh_list()
        self._updating = False

    def _refresh_list(self) -> None:
        self._list.blockSignals(True)
        cur = self._list.currentRow()
        self._list.clear()
        for ann in self._items:
            bar_label = self._bar_names[ann.bar_index] if ann.bar_index < len(self._bar_names) else f"#{ann.bar_index}"
            self._list.addItem(f'"{ann.text}" on {bar_label}')
        if 0 <= cur < self._list.count():
            self._list.setCurrentRow(cur)
        self._list.blockSignals(False)

    def _selected(self) -> BarAnnotation | None:
        r = self._list.currentRow()
        return self._items[r] if 0 <= r < len(self._items) else None

    def _on_selection(self, row: int) -> None:
        ann = self._selected()
        self._props.setEnabled(ann is not None)
        if ann:
            self._updating = True
            idx = self._bar_combo.findData(ann.bar_index)
            if idx >= 0:
                self._bar_combo.setCurrentIndex(idx)
            self._text.setText(ann.text)
            self._font_size.setValue(ann.font.size)
            self._bold.setChecked(ann.font.bold)
            self._set_color(ann.color)
            self._y_offset.setValue(ann.y_offset)
            self._updating = False

    def _on_prop(self, *_) -> None:
        if self._updating:
            return
        ann = self._selected()
        if not ann:
            return
        ann.bar_index = self._bar_combo.currentData() or 0
        ann.text = self._text.text()
        ann.font.size = self._font_size.value()
        ann.font.bold = self._bold.isChecked()
        ann.color = self._color_btn.property("color") or ann.color
        ann.y_offset = self._y_offset.value()
        self._refresh_list()
        self.changed.emit()

    def _on_add(self) -> None:
        ann = BarAnnotation(bar_index=0, text="*")
        self._items.append(ann)
        self._refresh_list()
        self._list.setCurrentRow(len(self._items) - 1)
        self.changed.emit()

    def _on_remove(self) -> None:
        r = self._list.currentRow()
        if 0 <= r < len(self._items):
            self._items.pop(r)
            self._refresh_list()
            if not self._items:
                self._props.setEnabled(False)
            self.changed.emit()

    def _set_color(self, color: str) -> None:
        self._color_btn.setStyleSheet(f"background-color: {color}; border: 1px solid #888;")
        self._color_btn.setProperty("color", color)

    def _pick_color(self) -> None:
        cur = self._color_btn.property("color") or "#000000"
        c = QColorDialog.getColor(QColor(cur), self)
        if c.isValid():
            self._set_color(c.name())
            self._on_prop()

    @staticmethod
    def _make_btn(text, slot):
        b = QPushButton(text)
        b.clicked.connect(slot)
        return b


class _BracketsTab(QWidget):
    """Tab for comparison brackets between bars."""

    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[ComparisonBracket] = []
        self._bar_names: list[str] = []
        self._updating = False

        layout = QVBoxLayout(self)

        # List + buttons
        list_row = QHBoxLayout()
        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_selection)
        list_row.addWidget(self._list, 1)

        btn_col = QVBoxLayout()
        btn_col.addWidget(self._make_btn("Add", self._on_add))
        btn_col.addWidget(self._make_btn("Remove", self._on_remove))
        btn_col.addStretch()
        list_row.addLayout(btn_col)
        layout.addLayout(list_row)

        # Properties
        self._props = QGroupBox("Bracket Properties")
        form = QFormLayout(self._props)

        self._left_combo = QComboBox()
        self._left_combo.currentIndexChanged.connect(self._on_prop)
        form.addRow("From Bar:", self._left_combo)

        self._right_combo = QComboBox()
        self._right_combo.currentIndexChanged.connect(self._on_prop)
        form.addRow("To Bar:", self._right_combo)

        self._text = QLineEdit()
        self._text.setPlaceholderText("e.g. *, ***, ns, p=0.03")
        self._text.textChanged.connect(self._on_prop)
        text_row = QHBoxLayout()
        text_row.addWidget(self._text, 1)
        text_row.addWidget(SymbolButton(self._text))
        form.addRow("Text:", text_row)

        self._font_size = QDoubleSpinBox()
        self._font_size.setRange(6, 36)
        self._font_size.setValue(12)
        self._font_size.setSuffix(" pt")
        self._font_size.valueChanged.connect(self._on_prop)
        form.addRow("Font Size:", self._font_size)

        self._bold = QCheckBox("Bold")
        self._bold.setChecked(True)
        self._bold.toggled.connect(self._on_prop)
        form.addRow("", self._bold)

        self._color_btn = QPushButton("  ")
        self._color_btn.setFixedSize(40, 25)
        self._color_btn.clicked.connect(self._pick_color)
        color_row = QHBoxLayout()
        color_row.addWidget(self._color_btn)
        color_row.addStretch()
        form.addRow("Color:", color_row)

        self._line_width = QDoubleSpinBox()
        self._line_width.setRange(0.5, 5)
        self._line_width.setValue(1.2)
        self._line_width.setSingleStep(0.5)
        self._line_width.valueChanged.connect(self._on_prop)
        form.addRow("Line Width:", self._line_width)

        self._y_offset = QDoubleSpinBox()
        self._y_offset.setRange(-1e6, 1e6)
        self._y_offset.setValue(0)
        self._y_offset.setDecimals(4)
        self._y_offset.setSingleStep(0.001)
        self._y_offset.setToolTip(
            "Extra vertical offset (data units).\n"
            "Use the scroll wheel or type a value directly."
        )
        self._y_offset.valueChanged.connect(self._on_prop)
        form.addRow("Y Offset:", self._y_offset)

        self._tip_length = QDoubleSpinBox()
        self._tip_length.setRange(0.0, 0.1)
        self._tip_length.setValue(0.02)
        self._tip_length.setSingleStep(0.005)
        self._tip_length.setDecimals(3)
        self._tip_length.setToolTip("Length of vertical bracket tips (fraction of y range)")
        self._tip_length.valueChanged.connect(self._on_prop)
        form.addRow("Tip Length:", self._tip_length)

        self._props.setEnabled(False)
        layout.addWidget(self._props)

    def load(self, items: list[ComparisonBracket], bar_names: list[str],
             y_range: float = 10.0) -> None:
        self._updating = True
        self._items = items
        self._bar_names = bar_names
        for combo in (self._left_combo, self._right_combo):
            combo.clear()
            for i, name in enumerate(bar_names):
                combo.addItem(f"{i}: {name}", i)
        step = max(abs(y_range) * 0.01, 1e-6)
        self._y_offset.setSingleStep(step)
        self._y_offset.setDecimals(max(0, 4 - int(max(0, _log10(abs(y_range))))))
        self._refresh_list()
        self._updating = False

    def _refresh_list(self) -> None:
        self._list.blockSignals(True)
        cur = self._list.currentRow()
        self._list.clear()
        for brk in self._items:
            ln = self._bar_names[brk.bar_left] if brk.bar_left < len(self._bar_names) else f"#{brk.bar_left}"
            rn = self._bar_names[brk.bar_right] if brk.bar_right < len(self._bar_names) else f"#{brk.bar_right}"
            self._list.addItem(f'"{brk.text}"  {ln} \u2194 {rn}')
        if 0 <= cur < self._list.count():
            self._list.setCurrentRow(cur)
        self._list.blockSignals(False)

    def _selected(self) -> ComparisonBracket | None:
        r = self._list.currentRow()
        return self._items[r] if 0 <= r < len(self._items) else None

    def _on_selection(self, row: int) -> None:
        brk = self._selected()
        self._props.setEnabled(brk is not None)
        if brk:
            self._updating = True
            idx = self._left_combo.findData(brk.bar_left)
            if idx >= 0:
                self._left_combo.setCurrentIndex(idx)
            idx = self._right_combo.findData(brk.bar_right)
            if idx >= 0:
                self._right_combo.setCurrentIndex(idx)
            self._text.setText(brk.text)
            self._font_size.setValue(brk.font.size)
            self._bold.setChecked(brk.font.bold)
            self._set_color(brk.color)
            self._line_width.setValue(brk.line_width)
            self._y_offset.setValue(brk.y_offset)
            self._tip_length.setValue(brk.tip_length)
            self._updating = False

    def _on_prop(self, *_) -> None:
        if self._updating:
            return
        brk = self._selected()
        if not brk:
            return
        brk.bar_left = self._left_combo.currentData() or 0
        brk.bar_right = self._right_combo.currentData() or 1
        brk.text = self._text.text()
        brk.font.size = self._font_size.value()
        brk.font.bold = self._bold.isChecked()
        brk.color = self._color_btn.property("color") or brk.color
        brk.line_width = self._line_width.value()
        brk.y_offset = self._y_offset.value()
        brk.tip_length = self._tip_length.value()
        self._refresh_list()
        self.changed.emit()

    def _on_add(self) -> None:
        n = len(self._bar_names)
        brk = ComparisonBracket(bar_left=0, bar_right=min(1, n - 1), text="*")
        self._items.append(brk)
        self._refresh_list()
        self._list.setCurrentRow(len(self._items) - 1)
        self.changed.emit()

    def _on_remove(self) -> None:
        r = self._list.currentRow()
        if 0 <= r < len(self._items):
            self._items.pop(r)
            self._refresh_list()
            if not self._items:
                self._props.setEnabled(False)
            self.changed.emit()

    def _set_color(self, color: str) -> None:
        self._color_btn.setStyleSheet(f"background-color: {color}; border: 1px solid #888;")
        self._color_btn.setProperty("color", color)

    def _pick_color(self) -> None:
        cur = self._color_btn.property("color") or "#000000"
        c = QColorDialog.getColor(QColor(cur), self)
        if c.isValid():
            self._set_color(c.name())
            self._on_prop()

    @staticmethod
    def _make_btn(text, slot):
        b = QPushButton(text)
        b.clicked.connect(slot)
        return b
