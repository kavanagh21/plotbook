"""Declarative graph specification."""

from __future__ import annotations

from dataclasses import dataclass, field

from plotbook.models.enums import GRAPH_TYPES_FOR_FORMAT, GraphType, TableFormat
from plotbook.models.palette import get_palette
from plotbook.models.style import (
    AxisStyle,
    BarAnnotation,
    ComparisonBracket,
    ErrorBarConfig,
    LegendStyle,
    ReferenceLine,
    SeriesStyle,
    TitleStyle,
    Trendline,
)


@dataclass
class GraphSpec:
    """Complete declarative specification of a graph."""

    graph_type: GraphType = GraphType.SCATTER

    # Per-series styling keyed by DataSeries.id
    series_styles: dict[str, SeriesStyle] = field(default_factory=dict)

    # Global formatting
    title: TitleStyle = field(default_factory=TitleStyle)
    x_axis: AxisStyle = field(default_factory=lambda: AxisStyle(label="X"))
    y_axis: AxisStyle = field(default_factory=lambda: AxisStyle(label="Y"))
    legend: LegendStyle = field(default_factory=LegendStyle)
    error_bars: ErrorBarConfig = field(default_factory=ErrorBarConfig)
    reference_lines: list[ReferenceLine] = field(default_factory=list)
    bar_annotations: list[BarAnnotation] = field(default_factory=list)
    comparison_brackets: list[ComparisonBracket] = field(default_factory=list)
    trendline: Trendline = field(default_factory=Trendline)

    palette_name: str = "default"

    def ensure_series_style(self, series_id: str, index: int) -> SeriesStyle:
        """Get or create a SeriesStyle, assigning a palette color."""
        if series_id not in self.series_styles:
            palette = get_palette(self.palette_name)
            self.series_styles[series_id] = SeriesStyle(
                color=palette.color_at(index)
            )
        return self.series_styles[series_id]

    @staticmethod
    def compatible_graph_types(table_format: TableFormat) -> list[GraphType]:
        return GRAPH_TYPES_FOR_FORMAT.get(table_format, [])

    def to_dict(self) -> dict:
        return {
            "graph_type": self.graph_type.name,
            "series_styles": {
                k: v.to_dict() for k, v in self.series_styles.items()
            },
            "title": self.title.to_dict(),
            "x_axis": self.x_axis.to_dict(),
            "y_axis": self.y_axis.to_dict(),
            "legend": self.legend.to_dict(),
            "error_bars": self.error_bars.to_dict(),
            "reference_lines": [rl.to_dict() for rl in self.reference_lines],
            "bar_annotations": [a.to_dict() for a in self.bar_annotations],
            "comparison_brackets": [b.to_dict() for b in self.comparison_brackets],
            "trendline": self.trendline.to_dict(),
            "palette_name": self.palette_name,
        }

    @classmethod
    def from_dict(cls, d: dict) -> GraphSpec:
        return cls(
            graph_type=GraphType[d["graph_type"]],
            series_styles={
                k: SeriesStyle.from_dict(v)
                for k, v in d.get("series_styles", {}).items()
            },
            title=TitleStyle.from_dict(d["title"]),
            x_axis=AxisStyle.from_dict(d["x_axis"]),
            y_axis=AxisStyle.from_dict(d["y_axis"]),
            legend=LegendStyle.from_dict(d["legend"]),
            error_bars=ErrorBarConfig.from_dict(d["error_bars"]),
            reference_lines=[
                ReferenceLine.from_dict(rl)
                for rl in d.get("reference_lines", [])
            ],
            bar_annotations=[
                BarAnnotation.from_dict(a)
                for a in d.get("bar_annotations", [])
            ],
            comparison_brackets=[
                ComparisonBracket.from_dict(b)
                for b in d.get("comparison_brackets", [])
            ],
            trendline=Trendline.from_dict(d["trendline"])
                if "trendline" in d else Trendline(),
            palette_name=d.get("palette_name", "default"),
        )
