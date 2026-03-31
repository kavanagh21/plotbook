"""Format panel dock widget with tabbed styling pages."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QDockWidget, QTabWidget, QWidget

from plotbook.models.datatable import DataTable
from plotbook.models.graph_spec import GraphSpec
from plotbook.models.style import FontSpec
from plotbook.ui.format_pages.annotations_page import AnnotationsPage
from plotbook.ui.format_pages.axis_page import AxisPage
from plotbook.ui.format_pages.errorbars_page import ErrorBarsPage
from plotbook.ui.format_pages.legend_page import LegendPage
from plotbook.ui.format_pages.reflines_page import ReferenceLinesPage
from plotbook.ui.format_pages.series_page import SeriesPage
from plotbook.ui.format_pages.title_page import TitlePage
from plotbook.ui.format_pages.trendline_page import TrendlinePage
from plotbook.viewmodels.graph_viewmodel import GraphViewModel


class FormatPanel(QDockWidget):
    """Right-side formatting panel with tabbed pages."""

    def __init__(self, parent=None):
        super().__init__("Format", parent)
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)

        self._tabs = QTabWidget()
        self._series_page = SeriesPage()
        self._errorbars_page = ErrorBarsPage()
        self._xaxis_page = AxisPage("X Axis")
        self._yaxis_page = AxisPage("Y Axis")
        self._title_page = TitlePage()
        self._legend_page = LegendPage()
        self._reflines_page = ReferenceLinesPage()
        self._annotations_page = AnnotationsPage()
        self._trendline_page = TrendlinePage()

        self._tabs.addTab(self._series_page, "Series")
        self._tabs.addTab(self._errorbars_page, "Error Bars")
        self._tabs.addTab(self._xaxis_page, "X Axis")
        self._tabs.addTab(self._yaxis_page, "Y Axis")
        self._tabs.addTab(self._title_page, "Title")
        self._tabs.addTab(self._legend_page, "Legend")
        self._tabs.addTab(self._reflines_page, "Ref Lines")
        self._tabs.addTab(self._annotations_page, "Annotate")
        self._tabs.addTab(self._trendline_page, "Trendline")

        self.setWidget(self._tabs)

        self._vm: GraphViewModel | None = None

    def load_from_spec(self, spec: GraphSpec, data_table: DataTable) -> None:
        """Populate all pages from current spec."""
        series_names = {s.id: s.name for s in data_table.series}
        self._series_page.load(spec.series_styles, series_names)
        self._errorbars_page.load(spec.error_bars)
        self._xaxis_page.load(spec.x_axis)
        self._yaxis_page.load(spec.y_axis)
        self._title_page.load(spec.title)
        self._legend_page.load(spec.legend)
        self._reflines_page.load(spec.reference_lines)

        # Annotations: build point/bar name list
        from plotbook.models.table_formats import XYTable
        if isinstance(data_table, XYTable):
            # For XY charts, label by X value at each data point
            import numpy as np
            x_vals = data_table.x_values()
            if data_table.series:
                y_vals = data_table.series[0].computed_mean()
                mask = ~np.isnan(x_vals) & ~np.isnan(y_vals)
                valid_x = x_vals[mask]
                order = np.argsort(valid_x)
                point_names = [f"X={valid_x[i]:g}" for i in order]
            else:
                point_names = []
        else:
            point_names = [s.name for s in data_table.series]

        # Compute Y range for adaptive offset step
        import numpy as np
        y_range = 10.0  # fallback
        for s in data_table.series:
            vals = s.computed_mean()
            clean = vals[~np.isnan(vals)]
            if len(clean) > 0:
                r = float(np.max(clean) - np.min(clean))
                if r > 0:
                    y_range = r
                    break

        self._annotations_page.load(
            spec.bar_annotations, spec.comparison_brackets, point_names, y_range
        )
        self._trendline_page.load(spec.trendline)

    def connect_to_viewmodel(self, vm: GraphViewModel) -> None:
        """Wire all page signals to the viewmodel."""
        if self._vm is not None:
            self._disconnect_old()

        self._vm = vm

        self._series_page.styleChanged.connect(self._on_series_style_changed)
        self._errorbars_page.errorBarsChanged.connect(self._on_errorbars_changed)
        self._xaxis_page.axisChanged.connect(self._on_xaxis_changed)
        self._yaxis_page.axisChanged.connect(self._on_yaxis_changed)
        self._title_page.titleChanged.connect(self._on_title_changed)
        self._legend_page.legendChanged.connect(self._on_legend_changed)
        self._reflines_page.changed.connect(self._on_reflines_changed)
        self._annotations_page.changed.connect(self._on_annotations_changed)
        self._trendline_page.changed.connect(self._on_trendline_changed)

    def _disconnect_old(self) -> None:
        try:
            self._series_page.styleChanged.disconnect(self._on_series_style_changed)
            self._errorbars_page.errorBarsChanged.disconnect(self._on_errorbars_changed)
            self._xaxis_page.axisChanged.disconnect(self._on_xaxis_changed)
            self._yaxis_page.axisChanged.disconnect(self._on_yaxis_changed)
            self._title_page.titleChanged.disconnect(self._on_title_changed)
            self._legend_page.legendChanged.disconnect(self._on_legend_changed)
            self._reflines_page.changed.disconnect(self._on_reflines_changed)
            self._annotations_page.changed.disconnect(self._on_annotations_changed)
            self._trendline_page.changed.disconnect(self._on_trendline_changed)
        except (TypeError, RuntimeError):
            pass

    def _on_series_style_changed(self, series_id: str, attr: str, value) -> None:
        if self._vm:
            self._vm.update_series_style(series_id, **{attr: value})

    def _on_errorbars_changed(self, attr: str, value) -> None:
        if self._vm:
            self._vm.update_error_bars(**{attr: value})

    def _on_xaxis_changed(self, attr: str, value) -> None:
        if self._vm:
            self._set_nested_attr(self._vm.sheet.graph_spec.x_axis, attr, value)
            self._vm.request_render()

    def _on_yaxis_changed(self, attr: str, value) -> None:
        if self._vm:
            self._set_nested_attr(self._vm.sheet.graph_spec.y_axis, attr, value)
            self._vm.request_render()

    def _on_title_changed(self, attr: str, value) -> None:
        if self._vm:
            self._set_nested_attr(self._vm.sheet.graph_spec.title, attr, value)
            self._vm.request_render()

    def _on_legend_changed(self, attr: str, value) -> None:
        if self._vm:
            self._set_nested_attr(self._vm.sheet.graph_spec.legend, attr, value)
            self._vm.request_render()

    def _on_reflines_changed(self) -> None:
        if self._vm:
            self._vm.request_render()

    def _on_annotations_changed(self) -> None:
        if self._vm:
            self._vm.request_render()

    def _on_trendline_changed(self) -> None:
        if self._vm:
            self._vm.request_render()

    @staticmethod
    def _set_nested_attr(obj, attr_path: str, value) -> None:
        """Set a potentially nested attribute like 'font.size'."""
        parts = attr_path.split(".")
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)
