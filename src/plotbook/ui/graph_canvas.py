"""Matplotlib canvas widget for displaying graphs."""

from __future__ import annotations

import io

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PyQt6.QtCore import QBuffer, QByteArray, Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class GraphCanvas(QWidget):
    """Hosts a matplotlib FigureCanvasQTAgg, replacing the figure on each render."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._figure: Figure | None = None
        self._canvas: FigureCanvasQTAgg | None = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        # Start with a blank figure
        self._set_figure(self._blank_figure())

    def update_figure(self, fig: Figure) -> None:
        """Replace the displayed figure with a new one."""
        self._set_figure(fig)

    def get_figure(self) -> Figure | None:
        return self._figure

    def _set_figure(self, fig: Figure) -> None:
        if self._canvas is not None:
            self._layout.removeWidget(self._canvas)
            self._canvas.deleteLater()
            self._canvas = None

        self._figure = fig
        self._canvas = FigureCanvasQTAgg(fig)
        self._layout.addWidget(self._canvas)
        self._canvas.draw()

    @staticmethod
    def _blank_figure() -> Figure:
        fig = Figure(figsize=(7, 5), dpi=100)
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, "Enter data to see graph",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=14, color="#999999")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        return fig


def _figure_to_clipboard(fig: Figure | None, dpi: int = 150) -> None:
    """Copy a matplotlib figure to the system clipboard as an image."""
    if fig is None:
        return
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    image = QImage.fromData(buf.read())
    QApplication.clipboard().setImage(image)


class _MinimalToolbar(NavigationToolbar2QT):
    """Toolbar with only Home, Pan, and Save."""

    toolitems = [
        ("Home", "Reset original view", "home", "home"),
        (None, None, None, None),
        ("Pan", "Pan with left mouse, zoom with right", "move", "pan"),
        (None, None, None, None),
        ("Save", "Save the figure", "filesave", "save_figure"),
    ]


# Predefined window sizes: (label, width, height)
_PRESET_SIZES = [
    ("Custom", 0, 0),
    ("Small (640x480)", 640, 480),
    ("Medium (800x600)", 800, 600),
    ("Large (1024x768)", 1024, 768),
    ("Wide (1200x600)", 1200, 600),
    ("Presentation (1280x720)", 1280, 720),
    ("A4 Landscape (1123x794)", 1123, 794),
    ("Square (700x700)", 700, 700),
]


class PopOutGraphWindow(QWidget):
    """
    Separate window that mirrors the graph from the main canvas.
    Stays synced: receives the same figureReady signal.
    Includes a minimal toolbar, copy-to-clipboard, and preset sizes.
    """

    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("PlotBook - Graph")
        self.resize(900, 650)

        self._figure: Figure | None = None
        self._canvas: FigureCanvasQTAgg | None = None
        self._toolbar: _MinimalToolbar | None = None
        self._updating_size = False  # Guard against signal loops

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)

        # Top bar: copy button + size controls
        top_bar = QHBoxLayout()

        self._copy_btn = QPushButton("Copy to Clipboard")
        self._copy_btn.setToolTip("Copy graph as image to clipboard")
        self._copy_btn.clicked.connect(self._copy_to_clipboard)
        top_bar.addWidget(self._copy_btn)

        top_bar.addStretch()

        # Size preset dropdown
        top_bar.addWidget(QLabel("Size:"))
        self._size_combo = QComboBox()
        self._size_combo.setMinimumWidth(160)
        for label, w, h in _PRESET_SIZES:
            self._size_combo.addItem(label, (w, h))
        self._size_combo.currentIndexChanged.connect(self._on_preset_selected)
        top_bar.addWidget(self._size_combo)

        # Width x Height spin boxes
        self._w_spin = QSpinBox()
        self._w_spin.setRange(200, 4000)
        self._w_spin.setValue(900)
        self._w_spin.setSuffix(" px")
        self._w_spin.setToolTip("Window width")
        self._w_spin.editingFinished.connect(self._on_spin_changed)
        top_bar.addWidget(self._w_spin)

        top_bar.addWidget(QLabel("\u00d7"))  # multiplication sign

        self._h_spin = QSpinBox()
        self._h_spin.setRange(200, 4000)
        self._h_spin.setValue(650)
        self._h_spin.setSuffix(" px")
        self._h_spin.setToolTip("Window height")
        self._h_spin.editingFinished.connect(self._on_spin_changed)
        top_bar.addWidget(self._h_spin)

        self._layout.addLayout(top_bar)

        # Toolbar + canvas placeholder area
        self._canvas_area = QVBoxLayout()
        self._layout.addLayout(self._canvas_area, 1)

        # Placeholder
        self._set_figure(GraphCanvas._blank_figure())

    def update_figure(self, fig: Figure) -> None:
        """Replace the displayed figure."""
        self._set_figure(fig)

    def get_figure(self) -> Figure | None:
        return self._figure

    def _set_figure(self, fig: Figure) -> None:
        if self._toolbar is not None:
            self._canvas_area.removeWidget(self._toolbar)
            self._toolbar.deleteLater()
            self._toolbar = None
        if self._canvas is not None:
            self._canvas_area.removeWidget(self._canvas)
            self._canvas.deleteLater()
            self._canvas = None

        self._figure = fig
        self._canvas = FigureCanvasQTAgg(fig)
        self._toolbar = _MinimalToolbar(self._canvas, self)

        self._canvas_area.addWidget(self._toolbar)
        self._canvas_area.addWidget(self._canvas)
        self._canvas.draw()

    def _copy_to_clipboard(self) -> None:
        _figure_to_clipboard(self._figure)

    def _on_preset_selected(self, index: int) -> None:
        """User picked a preset from the dropdown."""
        if self._updating_size:
            return
        data = self._size_combo.itemData(index)
        if data and data[0] > 0 and data[1] > 0:
            self._updating_size = True
            self.resize(data[0], data[1])
            self._w_spin.setValue(data[0])
            self._h_spin.setValue(data[1])
            self._updating_size = False

    def _on_spin_changed(self) -> None:
        """User typed a custom size in the spin boxes."""
        if self._updating_size:
            return
        w, h = self._w_spin.value(), self._h_spin.value()
        self._updating_size = True
        self.resize(w, h)
        self._sync_combo_to_custom()
        self._updating_size = False

    def resizeEvent(self, event) -> None:
        """Track manual drag-resizes and update the controls."""
        super().resizeEvent(event)
        if self._updating_size:
            return
        self._updating_size = True
        w, h = self.width(), self.height()
        self._w_spin.setValue(w)
        self._h_spin.setValue(h)
        self._sync_combo_to_custom()
        self._updating_size = False

    def _sync_combo_to_custom(self) -> None:
        """Set the dropdown to 'Custom (WxH)', or match a preset if exact."""
        w, h = self.width(), self.height()

        # Check if it matches a preset
        for i in range(1, self._size_combo.count()):  # skip index 0 (Custom)
            data = self._size_combo.itemData(i)
            if data and abs(data[0] - w) <= 2 and abs(data[1] - h) <= 2:
                self._size_combo.blockSignals(True)
                self._size_combo.setCurrentIndex(i)
                self._size_combo.blockSignals(False)
                # Reset the Custom entry text
                self._size_combo.setItemText(0, "Custom")
                return

        # No preset matched - update the Custom entry
        self._size_combo.setItemText(0, f"Custom ({w}\u00d7{h})")
        self._size_combo.blockSignals(True)
        self._size_combo.setCurrentIndex(0)
        self._size_combo.setItemData(0, (w, h))
        self._size_combo.blockSignals(False)

    def closeEvent(self, event) -> None:
        self.closed.emit()
        super().closeEvent(event)
