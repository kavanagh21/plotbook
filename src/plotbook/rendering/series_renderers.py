"""Renderer functions for each graph type."""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes
from scipy.interpolate import make_interp_spline

from plotbook.models.datatable import DataTable
from plotbook.models.enums import EntryMode, ErrorBarType, GraphType
from plotbook.models.graph_spec import GraphSpec
from plotbook.models.table_formats import ColumnTable, GroupedTable, XYTable
from plotbook.rendering.engine import register
from plotbook.rendering.error_bars import draw_error_bars
from plotbook.stats.descriptive import column_stats


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _xy_series_data(table: XYTable, series, spec: GraphSpec):
    """Extract x, y_mean, y_error for an XY series."""
    x = table.x_values()
    y_mean = series.computed_mean()
    eb_config = spec.error_bars
    y_err = series.computed_error(eb_config.error_type)
    return x, y_mean, y_err


def _valid_mask(*arrays: np.ndarray) -> np.ndarray:
    mask = np.ones(len(arrays[0]), dtype=bool)
    for a in arrays:
        mask &= ~np.isnan(a)
    return mask


def _store_xy_points(ax, table: "XYTable", spec) -> None:
    """Store sorted (x, y_top) pairs for the first series, for annotations."""
    if not table.series:
        return
    x = table.x_values()
    s = table.series[0]
    y_mean = s.computed_mean()
    y_err = s.computed_error(spec.error_bars.error_type)
    mask = _valid_mask(x, y_mean)
    if not np.any(mask):
        return
    xm, ym = x[mask], y_mean[mask]
    em = y_err[mask]
    em = np.where(np.isnan(em), 0, em)
    order = np.argsort(xm)
    ax._plotbook_bar_x = [float(xm[i]) for i in order]
    ax._plotbook_bar_tops = [float(ym[i] + em[i]) for i in order]


# ---------------------------------------------------------------------------
# XY Format Renderers
# ---------------------------------------------------------------------------

@register(GraphType.SCATTER)
def render_scatter(ax: Axes, data_table: DataTable, spec: GraphSpec) -> None:
    assert isinstance(data_table, XYTable)

    for series in data_table.series:
        style = spec.series_styles[series.id]
        x, y_mean, y_err = _xy_series_data(data_table, series, spec)

        if series.entry_mode == EntryMode.RAW:
            # Plot individual replicates
            xv = data_table.x_values()
            for col_idx in range(series.n_subcols):
                yv = series.data[:, col_idx]
                mask = _valid_mask(xv, yv)
                if np.any(mask):
                    ax.scatter(
                        xv[mask], yv[mask],
                        color=style.color,
                        marker=style.marker_shape.value or "o",
                        s=style.marker_size ** 2,
                        alpha=0.6 if series.n_subcols > 1 else 1.0,
                        edgecolors=style.marker_edge_color or style.color,
                        linewidths=style.marker_edge_width,
                        zorder=3,
                    )
            # Error bars on means
            if spec.error_bars.error_type != ErrorBarType.NONE:
                mask = _valid_mask(x, y_mean)
                if np.any(mask):
                    draw_error_bars(ax, x, y_mean, y_err, spec.error_bars, style)
        else:
            mask = _valid_mask(x, y_mean)
            if np.any(mask):
                facecolor = style.color if style.marker_fill else "none"
                ax.scatter(
                    x[mask], y_mean[mask],
                    color=style.color,
                    marker=style.marker_shape.value or "o",
                    s=style.marker_size ** 2,
                    facecolors=facecolor,
                    edgecolors=style.marker_edge_color or style.color,
                    linewidths=style.marker_edge_width,
                    label=series.name,
                    zorder=3,
                )
                if spec.error_bars.error_type != ErrorBarType.NONE:
                    draw_error_bars(ax, x[mask], y_mean[mask], y_err[mask],
                                    spec.error_bars, style)

        # Add label for RAW mode (only once)
        if series.entry_mode == EntryMode.RAW:
            ax.scatter([], [], color=style.color,
                       marker=style.marker_shape.value or "o",
                       label=series.name)

    _store_xy_points(ax, data_table, spec)


@register(GraphType.LINE)
def render_line(ax: Axes, data_table: DataTable, spec: GraphSpec) -> None:
    assert isinstance(data_table, XYTable)

    for series in data_table.series:
        style = spec.series_styles[series.id]
        x, y_mean, y_err = _xy_series_data(data_table, series, spec)
        mask = _valid_mask(x, y_mean)
        if not np.any(mask):
            continue

        xm, ym = x[mask], y_mean[mask]
        order = np.argsort(xm)
        xm, ym = xm[order], ym[order]

        if style.show_line:
            ax.plot(
                xm, ym,
                color=style.color,
                linewidth=style.line_width,
                linestyle=style.line_style.value,
                label=series.name,
                zorder=2,
            )

        if style.show_markers and style.marker_shape.value:
            facecolor = style.color if style.marker_fill else "none"
            ax.scatter(
                xm, ym,
                color=style.color,
                marker=style.marker_shape.value,
                s=style.marker_size ** 2,
                facecolors=facecolor,
                edgecolors=style.marker_edge_color or style.color,
                zorder=3,
            )

        if spec.error_bars.error_type != ErrorBarType.NONE:
            y_err_m = y_err[_valid_mask(x, y_mean)]
            y_err_m = y_err_m[order]
            draw_error_bars(ax, xm, ym, y_err_m, spec.error_bars, style)

    _store_xy_points(ax, data_table, spec)


@register(GraphType.LINE_SCATTER)
def render_line_scatter(ax: Axes, data_table: DataTable, spec: GraphSpec) -> None:
    """Line + scatter: always show both line and markers."""
    assert isinstance(data_table, XYTable)

    for series in data_table.series:
        style = spec.series_styles[series.id]
        x, y_mean, y_err = _xy_series_data(data_table, series, spec)
        mask = _valid_mask(x, y_mean)
        if not np.any(mask):
            continue

        xm, ym = x[mask], y_mean[mask]
        order = np.argsort(xm)
        xm, ym = xm[order], ym[order]

        marker = style.marker_shape.value or "o"
        facecolor = style.color if style.marker_fill else "none"

        ax.plot(
            xm, ym,
            color=style.color,
            linewidth=style.line_width,
            linestyle=style.line_style.value,
            marker=marker,
            markersize=style.marker_size,
            markerfacecolor=facecolor,
            markeredgecolor=style.marker_edge_color or style.color,
            label=series.name,
            zorder=3,
        )

        if spec.error_bars.error_type != ErrorBarType.NONE:
            y_err_m = y_err[_valid_mask(x, y_mean)][order]
            draw_error_bars(ax, xm, ym, y_err_m, spec.error_bars, style)

    _store_xy_points(ax, data_table, spec)


@register(GraphType.SPLINE)
def render_spline(ax: Axes, data_table: DataTable, spec: GraphSpec) -> None:
    assert isinstance(data_table, XYTable)

    for series in data_table.series:
        style = spec.series_styles[series.id]
        x, y_mean, y_err = _xy_series_data(data_table, series, spec)
        mask = _valid_mask(x, y_mean)
        if np.sum(mask) < 3:
            # Fall back to line if not enough points for spline
            render_line(ax, data_table, spec)
            return

        xm, ym = x[mask], y_mean[mask]
        order = np.argsort(xm)
        xm, ym = xm[order], ym[order]

        try:
            spl = make_interp_spline(xm, ym, k=min(3, len(xm) - 1))
            x_smooth = np.linspace(xm.min(), xm.max(), 300)
            y_smooth = spl(x_smooth)

            ax.plot(
                x_smooth, y_smooth,
                color=style.color,
                linewidth=style.line_width,
                linestyle=style.line_style.value,
                label=series.name,
                zorder=2,
            )
        except Exception:
            ax.plot(xm, ym, color=style.color, linewidth=style.line_width,
                    label=series.name, zorder=2)

        if style.show_markers and style.marker_shape.value:
            ax.scatter(xm, ym, color=style.color,
                       marker=style.marker_shape.value,
                       s=style.marker_size ** 2, zorder=3)

        if spec.error_bars.error_type != ErrorBarType.NONE:
            y_err_m = y_err[_valid_mask(x, y_mean)][order]
            draw_error_bars(ax, xm, ym, y_err_m, spec.error_bars, style)

    _store_xy_points(ax, data_table, spec)


@register(GraphType.AREA)
def render_area(ax: Axes, data_table: DataTable, spec: GraphSpec) -> None:
    assert isinstance(data_table, XYTable)

    for series in data_table.series:
        style = spec.series_styles[series.id]
        x, y_mean, _ = _xy_series_data(data_table, series, spec)
        mask = _valid_mask(x, y_mean)
        if not np.any(mask):
            continue

        xm, ym = x[mask], y_mean[mask]
        order = np.argsort(xm)
        xm, ym = xm[order], ym[order]

        ax.fill_between(xm, ym, alpha=0.3, color=style.color, zorder=1)
        ax.plot(xm, ym, color=style.color, linewidth=style.line_width,
                linestyle=style.line_style.value, label=series.name, zorder=2)

    _store_xy_points(ax, data_table, spec)


# ---------------------------------------------------------------------------
# Column Format Renderers
# ---------------------------------------------------------------------------

@register(GraphType.BAR)
def render_bar(ax: Axes, data_table: DataTable, spec: GraphSpec) -> None:
    assert isinstance(data_table, ColumnTable)
    series_list = data_table.series

    x_pos = np.arange(len(series_list))
    has_any_data = False
    bar_tops = []
    bar_x_list = []

    for i, series in enumerate(series_list):
        style = spec.series_styles[series.id]
        stats = column_stats(series.data.ravel())

        mean_val = stats["mean"] if stats["n"] > 0 and not np.isnan(stats["mean"]) else 0
        err_val = 0.0

        if stats["n"] > 0 and not np.isnan(stats["mean"]):
            has_any_data = True
            ax.bar(
                x_pos[i],
                stats["mean"],
                width=style.bar_width,
                color=style.color,
                edgecolor=style.bar_edge_color or "black",
                linewidth=style.bar_edge_width,
                alpha=style.bar_alpha,
                label=series.name,
                zorder=3,
            )

            if spec.error_bars.error_type != ErrorBarType.NONE:
                err_val = _column_error(stats, spec.error_bars.error_type)
                if not np.isnan(err_val):
                    draw_error_bars(
                        ax,
                        np.array([x_pos[i]]),
                        np.array([stats["mean"]]),
                        np.array([err_val]),
                        spec.error_bars,
                        style,
                    )
                else:
                    err_val = 0.0

        bar_x_list.append(float(x_pos[i]))
        bar_tops.append(mean_val + err_val)

    # Store bar positions for annotations
    ax._plotbook_bar_x = bar_x_list
    ax._plotbook_bar_tops = bar_tops

    ax.set_xticks(x_pos)
    ax.set_xticklabels([s.name for s in series_list])

    if not has_any_data:
        ax.text(0.5, 0.5, "Enter data in each column\n(rows are replicates)",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=11, color="#999999")


@register(GraphType.DOT_PLOT)
def render_dot_plot(ax: Axes, data_table: DataTable, spec: GraphSpec) -> None:
    assert isinstance(data_table, ColumnTable)
    series_list = data_table.series

    x_pos = np.arange(len(series_list))

    for i, series in enumerate(series_list):
        style = spec.series_styles[series.id]
        values = series.data.ravel()
        clean = values[~np.isnan(values)]

        if len(clean) > 0:
            # Jitter x positions slightly
            jitter = np.random.default_rng(42).uniform(-0.15, 0.15, len(clean))
            ax.scatter(
                x_pos[i] + jitter, clean,
                color=style.color,
                marker=style.marker_shape.value or "o",
                s=style.marker_size ** 2,
                edgecolors=style.marker_edge_color or style.color,
                zorder=3,
                label=series.name,
            )

            # Mean line
            mean_val = np.nanmean(clean)
            ax.hlines(mean_val, x_pos[i] - 0.3, x_pos[i] + 0.3,
                      colors=style.color, linewidths=2, zorder=4)

            # Error bars
            if spec.error_bars.error_type != ErrorBarType.NONE:
                stats = column_stats(values)
                err_val = _column_error(stats, spec.error_bars.error_type)
                if not np.isnan(err_val):
                    draw_error_bars(
                        ax, np.array([x_pos[i]]), np.array([mean_val]),
                        np.array([err_val]), spec.error_bars, style,
                    )

    # Store bar positions for annotations
    bar_tops = []
    for i, series in enumerate(series_list):
        values = series.data.ravel()
        clean = values[~np.isnan(values)]
        if len(clean) > 0:
            stats = column_stats(values)
            err = _column_error(stats, spec.error_bars.error_type) if spec.error_bars.error_type != ErrorBarType.NONE else 0
            bar_tops.append(stats["mean"] + (err if not np.isnan(err) else 0))
        else:
            bar_tops.append(0)
    ax._plotbook_bar_x = [float(p) for p in x_pos]
    ax._plotbook_bar_tops = bar_tops

    ax.set_xticks(x_pos)
    ax.set_xticklabels([s.name for s in series_list])


@register(GraphType.BOX_WHISKER)
def render_box(ax: Axes, data_table: DataTable, spec: GraphSpec) -> None:
    assert isinstance(data_table, ColumnTable)
    series_list = data_table.series

    box_data = []
    labels = []
    colors = []

    for series in series_list:
        style = spec.series_styles[series.id]
        values = series.data.ravel()
        clean = values[~np.isnan(values)]
        if len(clean) > 0:
            box_data.append(clean)
        else:
            box_data.append([0])
        labels.append(series.name)
        colors.append(style.color)

    if box_data:
        bp = ax.boxplot(
            box_data,
            labels=labels,
            patch_artist=True,
            widths=0.6,
            zorder=2,
        )
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        for element in ["whiskers", "caps", "medians"]:
            for line in bp[element]:
                line.set_color("black")
                line.set_linewidth(1.2)


@register(GraphType.VIOLIN)
def render_violin(ax: Axes, data_table: DataTable, spec: GraphSpec) -> None:
    assert isinstance(data_table, ColumnTable)
    series_list = data_table.series

    plot_data = []
    positions = []
    labels = []
    colors = []

    for i, series in enumerate(series_list):
        style = spec.series_styles[series.id]
        values = series.data.ravel()
        clean = values[~np.isnan(values)]
        if len(clean) >= 2:
            plot_data.append(clean)
            positions.append(i)
            labels.append(series.name)
            colors.append(style.color)

    if plot_data:
        parts = ax.violinplot(plot_data, positions=positions, showmeans=True,
                              showmedians=True, widths=0.7)
        for i, pc in enumerate(parts["bodies"]):
            pc.set_facecolor(colors[i])
            pc.set_alpha(0.7)
        for partname in ["cbars", "cmins", "cmaxes", "cmeans", "cmedians"]:
            if partname in parts:
                parts[partname].set_color("black")

        ax.set_xticks(positions)
        ax.set_xticklabels(labels)


# ---------------------------------------------------------------------------
# Grouped Format Renderers
# ---------------------------------------------------------------------------

@register(GraphType.GROUPED_BAR)
def render_grouped_bar(ax: Axes, data_table: DataTable, spec: GraphSpec) -> None:
    assert isinstance(data_table, GroupedTable)
    series_list = data_table.series

    # Find rows that have labels
    row_labels = data_table.row_labels
    n_categories = _count_used_rows(data_table)
    if n_categories == 0:
        return

    n_groups = len(series_list)
    x = np.arange(n_categories)
    total_width = 0.8
    bar_width = total_width / max(n_groups, 1)

    # Collect all bar x-positions and tops for annotations (flattened left-to-right)
    all_bar_x = []
    all_bar_tops = []

    for g_idx, series in enumerate(series_list):
        style = spec.series_styles[series.id]
        offset = (g_idx - (n_groups - 1) / 2) * bar_width
        means = series.computed_mean()[:n_categories]
        errors = series.computed_error(spec.error_bars.error_type)[:n_categories]

        ax.bar(
            x + offset,
            np.where(np.isnan(means), 0, means),
            width=bar_width * 0.9,
            color=style.color,
            edgecolor=style.bar_edge_color or "black",
            linewidth=style.bar_edge_width,
            alpha=style.bar_alpha,
            label=series.name,
            zorder=3,
        )

        if spec.error_bars.error_type != ErrorBarType.NONE:
            valid = ~np.isnan(means) & ~np.isnan(errors)
            if np.any(valid):
                draw_error_bars(
                    ax,
                    (x + offset)[valid],
                    means[valid],
                    errors[valid],
                    spec.error_bars,
                    style,
                )

        # Store bar positions for each bar in this group
        for cat_idx in range(n_categories):
            all_bar_x.append(float(x[cat_idx] + offset))
            m = means[cat_idx] if not np.isnan(means[cat_idx]) else 0
            e = errors[cat_idx] if not np.isnan(errors[cat_idx]) else 0
            all_bar_tops.append(m + e)

    # Store for annotations (ordered: group0_cat0, group0_cat1, ..., group1_cat0, ...)
    # Re-order to left-to-right visual order (by x position)
    if all_bar_x:
        paired = sorted(zip(all_bar_x, all_bar_tops))
        ax._plotbook_bar_x = [p[0] for p in paired]
        ax._plotbook_bar_tops = [p[1] for p in paired]

    ax.set_xticks(x)
    ax.set_xticklabels(row_labels[:n_categories])


@register(GraphType.STACKED_BAR)
def render_stacked_bar(ax: Axes, data_table: DataTable, spec: GraphSpec) -> None:
    assert isinstance(data_table, GroupedTable)
    series_list = data_table.series

    n_categories = _count_used_rows(data_table)
    if n_categories == 0:
        return

    x = np.arange(n_categories)
    bottom = np.zeros(n_categories)

    for series in series_list:
        style = spec.series_styles[series.id]
        means = series.computed_mean()[:n_categories]
        values = np.where(np.isnan(means), 0, means)

        ax.bar(
            x, values,
            width=0.6,
            bottom=bottom,
            color=style.color,
            edgecolor=style.bar_edge_color or "black",
            linewidth=style.bar_edge_width,
            alpha=style.bar_alpha,
            label=series.name,
            zorder=3,
        )
        bottom += values

    row_labels = data_table.row_labels
    ax.set_xticks(x)
    ax.set_xticklabels(row_labels[:n_categories])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _column_error(stats: dict, error_type: ErrorBarType) -> float:
    """Get the appropriate error value from column stats."""
    if error_type == ErrorBarType.SD:
        return stats["sd"]
    elif error_type == ErrorBarType.SEM:
        return stats["sem"]
    elif error_type == ErrorBarType.RANGE:
        return (stats["max"] - stats["min"]) / 2
    elif error_type in (ErrorBarType.CI95, ErrorBarType.CI99):
        # Approximate using SEM * t-value
        n = stats["n"]
        if n < 2:
            return np.nan
        try:
            from scipy.stats import t
            confidence = 0.95 if error_type == ErrorBarType.CI95 else 0.99
            t_crit = t.ppf((1 + confidence) / 2, df=n - 1)
            return stats["sem"] * t_crit
        except ImportError:
            z = 1.96 if error_type == ErrorBarType.CI95 else 2.576
            return stats["sem"] * z
    return np.nan


def _count_used_rows(table: GroupedTable) -> int:
    """Count rows that have either a label or any data."""
    n = 0
    for i in range(table.row_count()):
        has_label = bool(table.row_labels[i].strip()) if i < len(table.row_labels) else False
        has_data = False
        for s in table.series:
            if i < s.n_rows and not np.all(np.isnan(s.data[i])):
                has_data = True
                break
        if has_label or has_data:
            n = i + 1  # Track highest used row
        else:
            break
    return n
