"""ViewModel bridging data/spec changes to graph rendering."""

from __future__ import annotations

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from matplotlib.figure import Figure

from plotbook.models.enums import GraphType
from plotbook.models.project import Sheet
from plotbook.rendering.engine import render


class GraphViewModel(QObject):
    """
    Bridges Sheet (DataTable + GraphSpec) to the rendering engine.
    Debounces rapid updates (100ms) and emits figureReady with a new Figure.
    """

    figureReady = pyqtSignal(object)  # Emits Figure

    def __init__(self, sheet: Sheet, parent=None):
        super().__init__(parent)
        self._sheet = sheet
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(100)
        self._debounce.timeout.connect(self._do_render)

    @property
    def sheet(self) -> Sheet:
        return self._sheet

    def request_render(self) -> None:
        """Schedule a debounced render."""
        self._debounce.start()

    def force_render(self) -> None:
        """Render immediately without debounce."""
        self._do_render()

    def _do_render(self) -> None:
        try:
            fig = render(self._sheet.data_table, self._sheet.graph_spec)
            self.figureReady.emit(fig)
        except Exception as e:
            # Don't crash on render errors - emit empty figure
            fig = Figure(figsize=(7, 5), dpi=100)
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, f"Render error:\n{e}",
                    transform=ax.transAxes, ha="center", va="center",
                    fontsize=10, color="red")
            self.figureReady.emit(fig)

    def set_graph_type(self, graph_type: GraphType) -> None:
        self._sheet.graph_spec.graph_type = graph_type
        self.request_render()

    def update_series_style(self, series_id: str, **kwargs) -> None:
        style = self._sheet.graph_spec.series_styles.get(series_id)
        if style:
            for k, v in kwargs.items():
                setattr(style, k, v)
            self.request_render()

    def update_x_axis(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self._sheet.graph_spec.x_axis, k, v)
        self.request_render()

    def update_y_axis(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self._sheet.graph_spec.y_axis, k, v)
        self.request_render()

    def update_title(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self._sheet.graph_spec.title, k, v)
        self.request_render()

    def update_legend(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self._sheet.graph_spec.legend, k, v)
        self.request_render()

    def update_error_bars(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self._sheet.graph_spec.error_bars, k, v)
        self.request_render()
