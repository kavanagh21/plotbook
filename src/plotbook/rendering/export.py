"""Export figures to various formats."""

from __future__ import annotations

from matplotlib.figure import Figure


def export_figure(
    fig: Figure,
    path: str,
    dpi: int = 300,
    transparent: bool = False,
) -> None:
    """Export to PNG, SVG, PDF, or TIFF based on file extension."""
    fig.savefig(path, dpi=dpi, transparent=transparent, bbox_inches="tight")
