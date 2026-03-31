"""Error bar computation and drawing."""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes

from plotbook.models.enums import ErrorBarDirection, ErrorBarType
from plotbook.models.style import ErrorBarConfig, SeriesStyle


def draw_error_bars(
    ax: Axes,
    x: np.ndarray,
    y: np.ndarray,
    errors: np.ndarray,
    config: ErrorBarConfig,
    series_style: SeriesStyle,
    horizontal: bool = False,
) -> None:
    """Render error bars onto the axes."""
    if config.error_type == ErrorBarType.NONE:
        return

    mask = ~np.isnan(x) & ~np.isnan(y) & ~np.isnan(errors)
    if not np.any(mask):
        return

    xm, ym, em = x[mask], y[mask], errors[mask]

    # Split by direction
    if config.direction == ErrorBarDirection.ABOVE:
        err_low = np.zeros_like(em)
        err_high = em
    elif config.direction == ErrorBarDirection.BELOW:
        err_low = em
        err_high = np.zeros_like(em)
    else:
        err_low = em
        err_high = em

    color = config.color or series_style.color

    kwargs = dict(
        fmt="none",
        ecolor=color,
        elinewidth=config.line_width,
        capsize=config.cap_width,
        capthick=config.line_width,
        zorder=2,
    )

    if horizontal:
        ax.errorbar(xm, ym, xerr=[err_low, err_high], **kwargs)
    else:
        ax.errorbar(xm, ym, yerr=[err_low, err_high], **kwargs)
