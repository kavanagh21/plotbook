"""Stateless rendering engine."""

from __future__ import annotations

from typing import Callable

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from plotbook.models.datatable import DataTable
from plotbook.models.enums import GraphType
from plotbook.models.graph_spec import GraphSpec
from plotbook.rendering.formatters import (
    apply_axis_style,
    apply_bar_annotations,
    apply_comparison_brackets,
    apply_legend,
    apply_reference_lines,
    apply_title,
    apply_trendline,
)

# Registry of renderer functions
_renderers: dict[GraphType, Callable] = {}


def register(graph_type: GraphType):
    """Decorator to register a series renderer function."""
    def decorator(func: Callable) -> Callable:
        _renderers[graph_type] = func
        return func
    return decorator


def render(data_table: DataTable, graph_spec: GraphSpec) -> Figure:
    """
    Main entry point: create a matplotlib Figure from data + spec.

    1. Create Figure + Axes
    2. Ensure series styles with palette colors
    3. Dispatch to type-specific renderer
    4. Apply formatting + annotations
    5. Return Figure
    """
    fig = Figure(figsize=(7, 5), dpi=100)
    ax = fig.add_subplot(111)

    # Ensure every series has a style
    for i, series in enumerate(data_table.series):
        graph_spec.ensure_series_style(series.id, i)

    # Import renderers to trigger registration
    import plotbook.rendering.series_renderers  # noqa: F401

    # Show placeholder if no data yet
    if not data_table.has_data():
        from plotbook.models.enums import GRAPH_TYPE_NAMES
        type_name = GRAPH_TYPE_NAMES.get(graph_spec.graph_type, "graph")
        ax.text(0.5, 0.5, f"Enter data to see {type_name}",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=14, color="#999999")
        ax.set_xticks([])
        ax.set_yticks([])
        fig.tight_layout()
        return fig

    # Dispatch to type-specific renderer
    # Renderers may set ax._plotbook_bar_x and ax._plotbook_bar_tops
    renderer_fn = _renderers.get(graph_spec.graph_type)
    if renderer_fn is not None:
        renderer_fn(ax, data_table, graph_spec)

    # Apply formatting
    apply_axis_style(ax, graph_spec.x_axis, "x")
    apply_axis_style(ax, graph_spec.y_axis, "y")
    apply_title(ax, graph_spec.title)
    apply_legend(ax, graph_spec.legend)

    # Reference / normalisation lines
    apply_reference_lines(ax, graph_spec.reference_lines)

    # Trendline (XY format graphs only)
    from plotbook.models.enums import TrendlineType
    from plotbook.models.table_formats import XYTable
    if (graph_spec.trendline.fit_type != TrendlineType.NONE
            and isinstance(data_table, XYTable)):
        import numpy as np
        x_data = data_table.x_values()
        # Use means from first series (trendline fits the primary dataset)
        if data_table.series:
            y_data = data_table.series[0].computed_mean()
            apply_trendline(ax, graph_spec.trendline, x_data, y_data)

    # Bar annotations and comparison brackets
    bar_x = getattr(ax, "_plotbook_bar_x", [])
    bar_tops = getattr(ax, "_plotbook_bar_tops", [])
    if bar_x and bar_tops:
        apply_bar_annotations(ax, graph_spec.bar_annotations, bar_tops, bar_x)
        apply_comparison_brackets(ax, graph_spec.comparison_brackets, bar_tops, bar_x)

    # Clean look
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return fig
