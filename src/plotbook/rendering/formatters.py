"""Apply style objects to matplotlib axes."""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes

from plotbook.models.enums import TrendlineType
from plotbook.models.style import (
    AxisStyle,
    BarAnnotation,
    ComparisonBracket,
    LegendStyle,
    ReferenceLine,
    TitleStyle,
    Trendline,
)


def apply_axis_style(ax: Axes, style: AxisStyle, axis: str) -> None:
    """Apply AxisStyle to x or y axis."""
    # Label
    setter = ax.set_xlabel if axis == "x" else ax.set_ylabel
    setter(style.label, labelpad=style.label_pad, **style.label_font.to_mpl())

    # Tick font
    target = ax.xaxis if axis == "x" else ax.yaxis

    # Newline separator: replace a chosen character with \n in tick labels
    if style.tick_newline_sep:
        current_labels = [t.get_text() for t in target.get_ticklabels()]
        if any(current_labels):
            new_labels = [
                lbl.replace(style.tick_newline_sep, "\n") for lbl in current_labels
            ]
            if axis == "x":
                ax.set_xticklabels(new_labels)
            else:
                ax.set_yticklabels(new_labels)

    for label in target.get_ticklabels():
        label.set_fontsize(style.tick_font.size)
        label.set_fontfamily(style.tick_font.mpl_family_list())
        if style.tick_font.bold:
            label.set_fontweight("bold")
        if style.tick_font.italic:
            label.set_fontstyle("italic")

    # Tick rotation
    if style.tick_angle != 0:
        ha = "right" if (axis == "x" and style.tick_angle > 0) else "center"
        if axis == "x":
            ax.tick_params(axis="x", rotation=style.tick_angle)
            for label in ax.xaxis.get_ticklabels():
                label.set_ha(ha)
        else:
            ax.tick_params(axis="y", rotation=style.tick_angle)

    # Range
    set_lim = ax.set_xlim if axis == "x" else ax.set_ylim
    current = (ax.get_xlim if axis == "x" else ax.get_ylim)()
    lo = style.min_val if style.min_val is not None else current[0]
    hi = style.max_val if style.max_val is not None else current[1]
    if style.min_val is not None or style.max_val is not None:
        set_lim(lo, hi)

    # Log scale
    if style.log_scale:
        (ax.set_xscale if axis == "x" else ax.set_yscale)("log")

    # Grid
    if style.show_grid:
        ax.grid(
            True,
            axis=axis,
            color=style.grid_color,
            alpha=style.grid_alpha,
            linestyle=style.grid_line_style.value,
        )

    # Invert
    if style.invert:
        if axis == "x":
            ax.invert_xaxis()
        else:
            ax.invert_yaxis()

    # Move scientific notation exponent into axis label
    if style.exponent_in_label:
        _move_exponent_to_label(ax, style, axis)


def _move_exponent_to_label(ax: Axes, style, axis: str) -> None:
    """
    If data values are very small or very large, compute a power-of-10
    scale factor, rescale the tick labels to clean numbers, and append
    the exponent to the axis label as Unicode (e.g. 'Papp (cm/s)  [×10⁻⁷]').
    """
    import math
    import matplotlib.ticker as mticker

    # Get the data range on this axis
    lim = ax.get_xlim() if axis == "x" else ax.get_ylim()
    max_abs = max(abs(lim[0]), abs(lim[1]))

    if max_abs == 0 or not np.isfinite(max_abs):
        return

    # Compute the order of magnitude
    order = math.floor(math.log10(max_abs))

    # Only apply if the exponent is significant (|order| >= 3)
    if abs(order) < 3:
        return

    exponent = order
    scale = 10.0 ** (-exponent)

    # Build Unicode superscript string for the exponent
    sup_map = {'0': '\u2070', '1': '\u00b9', '2': '\u00b2', '3': '\u00b3',
               '4': '\u2074', '5': '\u2075', '6': '\u2076', '7': '\u2077',
               '8': '\u2078', '9': '\u2079'}
    sup_digits = str(abs(exponent))
    sup_str = ''.join(sup_map.get(c, c) for c in sup_digits)
    if exponent < 0:
        sup_str = '\u207b' + sup_str

    scale_text = f"  [\u00d710{sup_str}]"  # e.g. " [×10⁻⁷]"

    # Append to axis label
    setter = ax.set_xlabel if axis == "x" else ax.set_ylabel
    current_label = ax.get_xlabel() if axis == "x" else ax.get_ylabel()
    setter(current_label + scale_text, labelpad=style.label_pad,
           **style.label_font.to_mpl())

    # Replace the formatter with scaled values and hide the offset
    target = ax.xaxis if axis == "x" else ax.yaxis
    target.set_major_formatter(
        mticker.FuncFormatter(lambda val, pos: f"{val * scale:g}")
    )
    target.get_offset_text().set_visible(False)


def apply_title(ax: Axes, style: TitleStyle) -> None:
    if style.text:
        ax.set_title(style.text, **style.font.to_mpl())


def apply_reference_lines(ax: Axes, lines: list[ReferenceLine]) -> None:
    """Draw horizontal/vertical reference lines with optional labels."""
    for rl in lines:
        line_kw = dict(
            color=rl.color,
            linewidth=rl.line_width,
            linestyle=rl.line_style.value,
            alpha=rl.alpha,
            zorder=1,
        )

        if rl.axis == "y":
            # Horizontal line
            ax.axhline(y=rl.value, **line_kw)
        else:
            # Vertical line
            ax.axvline(x=rl.value, **line_kw)

        # Label
        if rl.show_label and rl.label:
            font_kw = rl.label_font.to_mpl()
            font_kw["color"] = rl.color

            if rl.axis == "y":
                # Horizontal line label
                xlim = ax.get_xlim()
                if rl.label_position == "left":
                    x_pos = xlim[0]
                    ha = "left"
                elif rl.label_position == "center":
                    x_pos = (xlim[0] + xlim[1]) / 2
                    ha = "center"
                else:  # right
                    x_pos = xlim[1]
                    ha = "right"
                ax.text(
                    x_pos, rl.value, f"  {rl.label}  ",
                    ha=ha, va="bottom",
                    fontdict=font_kw,
                    zorder=5,
                )
            else:
                # Vertical line label
                ylim = ax.get_ylim()
                if rl.label_position == "bottom":
                    y_pos = ylim[0]
                    va = "bottom"
                elif rl.label_position == "center":
                    y_pos = (ylim[0] + ylim[1]) / 2
                    va = "center"
                else:  # top
                    y_pos = ylim[1]
                    va = "top"
                ax.text(
                    rl.value, y_pos, f"  {rl.label}  ",
                    ha="left", va=va,
                    fontdict=font_kw,
                    rotation=90,
                    zorder=5,
                )


def apply_legend(ax: Axes, style: LegendStyle) -> None:
    if style.show:
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            leg = ax.legend(
                loc=style.position.value,
                frameon=style.frame,
                prop={
                    "family": style.font.mpl_family_list(),
                    "size": style.font.size,
                },
            )


def apply_bar_annotations(
    ax: Axes,
    annotations: list[BarAnnotation],
    bar_tops: list[float],
    bar_x_positions: list[float],
) -> None:
    """Draw text labels above individual bars."""
    if not annotations or not bar_tops:
        return
    y_range = ax.get_ylim()
    auto_offset = (y_range[1] - y_range[0]) * 0.03

    for ann in annotations:
        idx = ann.bar_index
        if idx < 0 or idx >= len(bar_tops):
            continue
        x = bar_x_positions[idx]
        y = bar_tops[idx] + auto_offset + ann.y_offset

        font_kw = ann.font.to_mpl()
        font_kw["color"] = ann.color
        ax.text(
            x, y, ann.text,
            ha="center", va="bottom",
            fontdict=font_kw,
            zorder=6,
        )


def apply_comparison_brackets(
    ax: Axes,
    brackets: list[ComparisonBracket],
    bar_tops: list[float],
    bar_x_positions: list[float],
) -> None:
    """Draw comparison bracket lines between bars with text above."""
    if not brackets or not bar_tops:
        return
    y_range = ax.get_ylim()
    range_height = y_range[1] - y_range[0]
    auto_base = max(bar_tops) + range_height * 0.05

    # Sort brackets by span width so narrower ones sit lower
    sorted_brackets = sorted(brackets, key=lambda b: abs(b.bar_right - b.bar_left))

    # Track the highest y used so far to stack brackets
    used_y = auto_base

    for brk in sorted_brackets:
        left = min(brk.bar_left, brk.bar_right)
        right = max(brk.bar_left, brk.bar_right)
        if left < 0 or right >= len(bar_x_positions):
            continue

        x_left = bar_x_positions[left]
        x_right = bar_x_positions[right]

        # Determine y position
        if brk.y_position is not None:
            y = brk.y_position + brk.y_offset
        else:
            # Auto: above tallest bar in the span, stacked above previous brackets
            span_max = max(bar_tops[left:right + 1])
            y = max(used_y, span_max + range_height * 0.05) + brk.y_offset

        tip = range_height * brk.tip_length

        # Draw the bracket: two vertical tips + one horizontal bar
        ax.plot(
            [x_left, x_left, x_right, x_right],
            [y - tip, y, y, y - tip],
            color=brk.color,
            linewidth=brk.line_width,
            solid_capstyle="butt",
            zorder=6,
        )

        # Text above the horizontal bar
        x_mid = (x_left + x_right) / 2
        font_kw = brk.font.to_mpl()
        font_kw["color"] = brk.color
        ax.text(
            x_mid, y, brk.text,
            ha="center", va="bottom",
            fontdict=font_kw,
            zorder=6,
        )

        # Update stacking tracker
        text_height = range_height * 0.06  # Approximate text height
        used_y = y + text_height


def apply_trendline(
    ax: Axes,
    trendline: Trendline,
    x: np.ndarray,
    y: np.ndarray,
) -> None:
    """Fit and draw a trendline on XY data."""
    if trendline.fit_type == TrendlineType.NONE:
        return

    # Clean NaN
    mask = ~np.isnan(x) & ~np.isnan(y)
    if np.sum(mask) < 2:
        return
    xc, yc = x[mask], y[mask]
    order = np.argsort(xc)
    xc, yc = xc[order], yc[order]

    # Generate smooth x for the trendline curve
    ext = (xc[-1] - xc[0]) * trendline.extrapolate_pct / 100
    x_line = np.linspace(xc[0] - ext, xc[-1] + ext, 300)

    equation_str = ""
    r_squared = np.nan

    try:
        fit_type = trendline.fit_type

        if fit_type == TrendlineType.LINEAR:
            coeffs = np.polyfit(xc, yc, 1)
            y_line = np.polyval(coeffs, x_line)
            y_pred = np.polyval(coeffs, xc)
            m, b = coeffs
            equation_str = f"y = {m:.4g}x + {b:.4g}"

        elif fit_type == TrendlineType.POLYNOMIAL_2:
            coeffs = np.polyfit(xc, yc, 2)
            y_line = np.polyval(coeffs, x_line)
            y_pred = np.polyval(coeffs, xc)
            a, b, c = coeffs
            equation_str = f"y = {a:.4g}x\u00b2 + {b:.4g}x + {c:.4g}"

        elif fit_type == TrendlineType.POLYNOMIAL_3:
            coeffs = np.polyfit(xc, yc, 3)
            y_line = np.polyval(coeffs, x_line)
            y_pred = np.polyval(coeffs, xc)
            equation_str = "y = poly3"

        elif fit_type == TrendlineType.EXPONENTIAL:
            # y = a * e^(bx) → ln(y) = ln(a) + bx
            pos = yc > 0
            if np.sum(pos) < 2:
                return
            coeffs = np.polyfit(xc[pos], np.log(yc[pos]), 1)
            b, ln_a = coeffs
            a = np.exp(ln_a)
            y_line = a * np.exp(b * x_line)
            y_pred = a * np.exp(b * xc)
            equation_str = f"y = {a:.4g}e^({b:.4g}x)"

        elif fit_type == TrendlineType.LOGARITHMIC:
            # y = a * ln(x) + b
            pos = xc > 0
            if np.sum(pos) < 2:
                return
            coeffs = np.polyfit(np.log(xc[pos]), yc[pos], 1)
            a, b = coeffs
            x_line_pos = x_line[x_line > 0]
            y_line = a * np.log(x_line_pos) + b
            x_line = x_line_pos
            y_pred = a * np.log(xc[pos]) + b
            yc = yc[pos]
            equation_str = f"y = {a:.4g}ln(x) + {b:.4g}"

        elif fit_type == TrendlineType.POWER:
            # y = a * x^b → ln(y) = ln(a) + b*ln(x)
            pos = (xc > 0) & (yc > 0)
            if np.sum(pos) < 2:
                return
            coeffs = np.polyfit(np.log(xc[pos]), np.log(yc[pos]), 1)
            b, ln_a = coeffs
            a = np.exp(ln_a)
            x_line_pos = x_line[x_line > 0]
            y_line = a * x_line_pos ** b
            x_line = x_line_pos
            y_pred = a * xc[pos] ** b
            yc = yc[pos]
            equation_str = f"y = {a:.4g}x^{b:.4g}"

        else:
            return

        # R-squared
        ss_res = np.sum((yc - y_pred) ** 2)
        ss_tot = np.sum((yc - np.mean(yc)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else np.nan

        # Draw the trendline
        ax.plot(
            x_line, y_line,
            color=trendline.color,
            linewidth=trendline.line_width,
            linestyle=trendline.line_style.value,
            zorder=1.5,
        )

        # Equation / R² annotation
        parts = []
        if trendline.show_equation and equation_str:
            parts.append(equation_str)
        if trendline.show_r_squared and not np.isnan(r_squared):
            parts.append(f"R\u00b2 = {r_squared:.4f}")

        if parts:
            text = "\n".join(parts)
            pos_map = {
                "top_left": (0.03, 0.97, "left", "top"),
                "top_right": (0.97, 0.97, "right", "top"),
                "bottom_left": (0.03, 0.03, "left", "bottom"),
                "bottom_right": (0.97, 0.03, "right", "bottom"),
            }
            px, py, ha, va = pos_map.get(
                trendline.equation_position, (0.03, 0.97, "left", "top")
            )
            font_kw = trendline.equation_font.to_mpl()
            font_kw["color"] = trendline.color
            ax.text(
                px, py, text,
                transform=ax.transAxes,
                ha=ha, va=va,
                fontdict=font_kw,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor=trendline.color, alpha=0.8),
                zorder=7,
            )

    except Exception:
        pass  # Silently skip if fit fails
