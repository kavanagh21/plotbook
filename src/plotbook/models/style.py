"""Style dataclasses for graph formatting."""

from __future__ import annotations

from dataclasses import dataclass, field

import uuid

from plotbook.models.enums import (
    ErrorBarDirection,
    ErrorBarType,
    LegendPosition,
    LineStyle,
    MarkerShape,
    TrendlineType,
)


@dataclass
class FontSpec:
    family: str = "Arial"
    size: float = 12.0
    bold: bool = False
    italic: bool = False

    def to_dict(self) -> dict:
        return {
            "family": self.family,
            "size": self.size,
            "bold": self.bold,
            "italic": self.italic,
        }

    @classmethod
    def from_dict(cls, d: dict) -> FontSpec:
        return cls(**d)

    # Fallback font for Unicode symbols (subscripts, Greek, math) that
    # many standard fonts lack.  DejaVu Sans ships with matplotlib.
    _FALLBACK = "DejaVu Sans"

    def to_mpl(self) -> dict:
        """Convert to matplotlib fontdict."""
        weight = "bold" if self.bold else "normal"
        style = "italic" if self.italic else "normal"
        family = [self.family, self._FALLBACK] if self.family != self._FALLBACK else self.family
        return {
            "fontfamily": family,
            "fontsize": self.size,
            "fontweight": weight,
            "fontstyle": style,
        }

    def mpl_family_list(self) -> list[str]:
        """Return font family as a list with DejaVu Sans fallback."""
        if self.family == self._FALLBACK:
            return [self.family]
        return [self.family, self._FALLBACK]


@dataclass
class ErrorBarConfig:
    error_type: ErrorBarType = ErrorBarType.SD
    direction: ErrorBarDirection = ErrorBarDirection.BOTH
    cap_width: float = 4.0
    line_width: float = 1.0
    color: str | None = None  # None = match series color

    def to_dict(self) -> dict:
        return {
            "error_type": self.error_type.name,
            "direction": self.direction.name,
            "cap_width": self.cap_width,
            "line_width": self.line_width,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ErrorBarConfig:
        return cls(
            error_type=ErrorBarType[d["error_type"]],
            direction=ErrorBarDirection[d["direction"]],
            cap_width=d["cap_width"],
            line_width=d["line_width"],
            color=d.get("color"),
        )


@dataclass
class SeriesStyle:
    color: str = "#1f77b4"
    # Line properties
    line_width: float = 1.5
    line_style: LineStyle = LineStyle.SOLID
    show_line: bool = True
    # Marker properties
    marker_shape: MarkerShape = MarkerShape.CIRCLE
    marker_size: float = 6.0
    marker_fill: bool = True
    marker_edge_color: str | None = None
    marker_edge_width: float = 1.0
    show_markers: bool = True
    # Bar properties
    bar_width: float = 0.8
    bar_edge_color: str | None = None
    bar_edge_width: float = 1.0
    bar_alpha: float = 1.0

    def to_dict(self) -> dict:
        return {
            "color": self.color,
            "line_width": self.line_width,
            "line_style": self.line_style.name,
            "show_line": self.show_line,
            "marker_shape": self.marker_shape.name,
            "marker_size": self.marker_size,
            "marker_fill": self.marker_fill,
            "marker_edge_color": self.marker_edge_color,
            "marker_edge_width": self.marker_edge_width,
            "show_markers": self.show_markers,
            "bar_width": self.bar_width,
            "bar_edge_color": self.bar_edge_color,
            "bar_edge_width": self.bar_edge_width,
            "bar_alpha": self.bar_alpha,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SeriesStyle:
        return cls(
            color=d["color"],
            line_width=d["line_width"],
            line_style=LineStyle[d["line_style"]],
            show_line=d.get("show_line", True),
            marker_shape=MarkerShape[d["marker_shape"]],
            marker_size=d["marker_size"],
            marker_fill=d["marker_fill"],
            marker_edge_color=d.get("marker_edge_color"),
            marker_edge_width=d.get("marker_edge_width", 1.0),
            show_markers=d.get("show_markers", True),
            bar_width=d["bar_width"],
            bar_edge_color=d.get("bar_edge_color"),
            bar_edge_width=d.get("bar_edge_width", 1.0),
            bar_alpha=d.get("bar_alpha", 1.0),
        )


@dataclass
class AxisStyle:
    label: str = ""
    label_font: FontSpec = field(default_factory=FontSpec)
    tick_font: FontSpec = field(default_factory=lambda: FontSpec(size=10))
    tick_angle: float = 0.0  # Rotation in degrees (0 = horizontal, 90 = vertical)
    tick_newline_sep: str = ""  # Character to replace with newline in tick labels (e.g. " " or "/")
    label_pad: float = 4.0  # Spacing (pts) between axis label and tick labels
    exponent_in_label: bool = True  # Move the ×10^n exponent into the axis label
    min_val: float | None = None
    max_val: float | None = None
    log_scale: bool = False
    show_grid: bool = False
    grid_color: str = "#cccccc"
    grid_alpha: float = 0.5
    grid_line_style: LineStyle = LineStyle.SOLID
    invert: bool = False

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "label_font": self.label_font.to_dict(),
            "tick_font": self.tick_font.to_dict(),
            "tick_angle": self.tick_angle,
            "tick_newline_sep": self.tick_newline_sep,
            "label_pad": self.label_pad,
            "exponent_in_label": self.exponent_in_label,
            "min_val": self.min_val,
            "max_val": self.max_val,
            "log_scale": self.log_scale,
            "show_grid": self.show_grid,
            "grid_color": self.grid_color,
            "grid_alpha": self.grid_alpha,
            "grid_line_style": self.grid_line_style.name,
            "invert": self.invert,
        }

    @classmethod
    def from_dict(cls, d: dict) -> AxisStyle:
        return cls(
            label=d["label"],
            label_font=FontSpec.from_dict(d["label_font"]),
            tick_font=FontSpec.from_dict(d["tick_font"]),
            tick_angle=d.get("tick_angle", 0.0),
            tick_newline_sep=d.get("tick_newline_sep", ""),
            label_pad=d.get("label_pad", 4.0),
            exponent_in_label=d.get("exponent_in_label", True),
            min_val=d.get("min_val"),
            max_val=d.get("max_val"),
            log_scale=d.get("log_scale", False),
            show_grid=d.get("show_grid", False),
            grid_color=d.get("grid_color", "#cccccc"),
            grid_alpha=d.get("grid_alpha", 0.5),
            grid_line_style=LineStyle[d.get("grid_line_style", "SOLID")],
            invert=d.get("invert", False),
        )


@dataclass
class TitleStyle:
    text: str = ""
    font: FontSpec = field(default_factory=lambda: FontSpec(size=14, bold=True))

    def to_dict(self) -> dict:
        return {"text": self.text, "font": self.font.to_dict()}

    @classmethod
    def from_dict(cls, d: dict) -> TitleStyle:
        return cls(text=d["text"], font=FontSpec.from_dict(d["font"]))


@dataclass
class LegendStyle:
    show: bool = True
    position: LegendPosition = LegendPosition.BEST
    font: FontSpec = field(default_factory=lambda: FontSpec(size=10))
    frame: bool = True

    def to_dict(self) -> dict:
        return {
            "show": self.show,
            "position": self.position.name,
            "font": self.font.to_dict(),
            "frame": self.frame,
        }

    @classmethod
    def from_dict(cls, d: dict) -> LegendStyle:
        return cls(
            show=d["show"],
            position=LegendPosition[d["position"]],
            font=FontSpec.from_dict(d["font"]),
            frame=d.get("frame", True),
        )


@dataclass
class ReferenceLine:
    """A horizontal or vertical reference/normalisation line."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    axis: str = "y"              # "x" for vertical, "y" for horizontal
    value: float = 1.0           # Position on the axis
    color: str = "#333333"
    line_width: float = 1.5
    line_style: LineStyle = LineStyle.DASHED
    label: str = ""              # Text annotation next to the line
    label_font: FontSpec = field(default_factory=lambda: FontSpec(size=9))
    label_position: str = "right"  # "left", "right", "center" (horizontal); "top", "bottom", "center" (vertical)
    show_label: bool = True
    alpha: float = 1.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "axis": self.axis,
            "value": self.value,
            "color": self.color,
            "line_width": self.line_width,
            "line_style": self.line_style.name,
            "label": self.label,
            "label_font": self.label_font.to_dict(),
            "label_position": self.label_position,
            "show_label": self.show_label,
            "alpha": self.alpha,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ReferenceLine:
        return cls(
            id=d.get("id", uuid.uuid4().hex[:8]),
            axis=d.get("axis", "y"),
            value=d["value"],
            color=d.get("color", "#333333"),
            line_width=d.get("line_width", 1.5),
            line_style=LineStyle[d.get("line_style", "DASHED")],
            label=d.get("label", ""),
            label_font=FontSpec.from_dict(d["label_font"]) if "label_font" in d
                else FontSpec(size=9),
            label_position=d.get("label_position", "right"),
            show_label=d.get("show_label", True),
            alpha=d.get("alpha", 1.0),
        )


@dataclass
class BarAnnotation:
    """Text label above a single bar (e.g. *, ns, p<0.05)."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    bar_index: int = 0           # Which bar (0-based position on the x-axis)
    text: str = "*"
    font: FontSpec = field(default_factory=lambda: FontSpec(size=12, bold=True))
    color: str = "#000000"
    y_offset: float = 0.0       # Extra offset above the bar top (in data units)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "bar_index": self.bar_index,
            "text": self.text,
            "font": self.font.to_dict(),
            "color": self.color,
            "y_offset": self.y_offset,
        }

    @classmethod
    def from_dict(cls, d: dict) -> BarAnnotation:
        return cls(
            id=d.get("id", uuid.uuid4().hex[:8]),
            bar_index=d["bar_index"],
            text=d.get("text", "*"),
            font=FontSpec.from_dict(d["font"]) if "font" in d
                else FontSpec(size=12, bold=True),
            color=d.get("color", "#000000"),
            y_offset=d.get("y_offset", 0.0),
        )


@dataclass
class ComparisonBracket:
    """
    A bracket line between two bars with text above,
    used to show statistical significance (e.g. bar 0 vs bar 2, text='***').
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    bar_left: int = 0            # Left bar index
    bar_right: int = 1           # Right bar index
    text: str = "*"
    font: FontSpec = field(default_factory=lambda: FontSpec(size=12, bold=True))
    color: str = "#000000"
    line_width: float = 1.2
    y_position: float | None = None  # None = auto (above the tallest bar + offset)
    y_offset: float = 0.0       # Extra offset above auto position
    tip_length: float = 0.02    # Length of the vertical tips (fraction of y-axis range)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "bar_left": self.bar_left,
            "bar_right": self.bar_right,
            "text": self.text,
            "font": self.font.to_dict(),
            "color": self.color,
            "line_width": self.line_width,
            "y_position": self.y_position,
            "y_offset": self.y_offset,
            "tip_length": self.tip_length,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ComparisonBracket:
        return cls(
            id=d.get("id", uuid.uuid4().hex[:8]),
            bar_left=d["bar_left"],
            bar_right=d["bar_right"],
            text=d.get("text", "*"),
            font=FontSpec.from_dict(d["font"]) if "font" in d
                else FontSpec(size=12, bold=True),
            color=d.get("color", "#000000"),
            line_width=d.get("line_width", 1.2),
            y_position=d.get("y_position"),
            y_offset=d.get("y_offset", 0.0),
            tip_length=d.get("tip_length", 0.02),
        )


@dataclass
class Trendline:
    """A fitted trendline overlaid on XY data."""

    fit_type: TrendlineType = TrendlineType.NONE
    color: str = "#FF0000"
    line_width: float = 1.5
    line_style: LineStyle = LineStyle.DASHED
    show_equation: bool = True
    show_r_squared: bool = True
    equation_font: FontSpec = field(default_factory=lambda: FontSpec(size=9))
    equation_position: str = "top_left"  # top_left, top_right, bottom_left, bottom_right
    extrapolate_pct: float = 0.0  # Extend line beyond data range by this %

    def to_dict(self) -> dict:
        return {
            "fit_type": self.fit_type.name,
            "color": self.color,
            "line_width": self.line_width,
            "line_style": self.line_style.name,
            "show_equation": self.show_equation,
            "show_r_squared": self.show_r_squared,
            "equation_font": self.equation_font.to_dict(),
            "equation_position": self.equation_position,
            "extrapolate_pct": self.extrapolate_pct,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Trendline:
        return cls(
            fit_type=TrendlineType[d.get("fit_type", "NONE")],
            color=d.get("color", "#FF0000"),
            line_width=d.get("line_width", 1.5),
            line_style=LineStyle[d.get("line_style", "DASHED")],
            show_equation=d.get("show_equation", True),
            show_r_squared=d.get("show_r_squared", True),
            equation_font=FontSpec.from_dict(d["equation_font"])
                if "equation_font" in d else FontSpec(size=9),
            equation_position=d.get("equation_position", "top_left"),
            extrapolate_pct=d.get("extrapolate_pct", 0.0),
        )
