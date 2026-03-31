"""All enumerations for PlotBook."""

from enum import Enum, auto


class TableFormat(Enum):
    XY = auto()
    COLUMN = auto()
    GROUPED = auto()


class EntryMode(Enum):
    RAW = auto()        # Raw replicate values, stats computed automatically
    MEAN_SD = auto()    # User enters mean and SD
    MEAN_SEM = auto()   # User enters mean and SEM
    SINGLE = auto()     # Single values, no error information


class GraphType(Enum):
    # XY format types
    SCATTER = auto()
    LINE = auto()
    SPLINE = auto()
    AREA = auto()
    LINE_SCATTER = auto()
    # Column format types
    BAR = auto()
    BOX_WHISKER = auto()
    VIOLIN = auto()
    DOT_PLOT = auto()
    # Grouped format types
    GROUPED_BAR = auto()
    STACKED_BAR = auto()


# Which graph types are available for each table format
GRAPH_TYPES_FOR_FORMAT: dict[TableFormat, list[GraphType]] = {
    TableFormat.XY: [
        GraphType.SCATTER,
        GraphType.LINE,
        GraphType.LINE_SCATTER,
        GraphType.SPLINE,
        GraphType.AREA,
    ],
    TableFormat.COLUMN: [
        GraphType.BAR,
        GraphType.BOX_WHISKER,
        GraphType.VIOLIN,
        GraphType.DOT_PLOT,
    ],
    TableFormat.GROUPED: [
        GraphType.GROUPED_BAR,
        GraphType.STACKED_BAR,
    ],
}

# Human-readable names
GRAPH_TYPE_NAMES: dict[GraphType, str] = {
    GraphType.SCATTER: "Scatter",
    GraphType.LINE: "Line",
    GraphType.LINE_SCATTER: "Line + Scatter",
    GraphType.SPLINE: "Spline",
    GraphType.AREA: "Area",
    GraphType.BAR: "Bar",
    GraphType.BOX_WHISKER: "Box & Whisker",
    GraphType.VIOLIN: "Violin",
    GraphType.DOT_PLOT: "Dot Plot",
    GraphType.GROUPED_BAR: "Grouped Bar",
    GraphType.STACKED_BAR: "Stacked Bar",
}


class ErrorBarType(Enum):
    NONE = auto()
    SD = auto()
    SEM = auto()
    CI95 = auto()
    CI99 = auto()
    RANGE = auto()


class ErrorBarDirection(Enum):
    BOTH = auto()
    ABOVE = auto()
    BELOW = auto()


class TrendlineType(Enum):
    NONE = auto()
    LINEAR = auto()
    POLYNOMIAL_2 = auto()  # Quadratic
    POLYNOMIAL_3 = auto()  # Cubic
    EXPONENTIAL = auto()
    LOGARITHMIC = auto()
    POWER = auto()


TRENDLINE_TYPE_NAMES: dict["TrendlineType", str] = {
    TrendlineType.NONE: "None",
    TrendlineType.LINEAR: "Linear",
    TrendlineType.POLYNOMIAL_2: "Polynomial (2nd order)",
    TrendlineType.POLYNOMIAL_3: "Polynomial (3rd order)",
    TrendlineType.EXPONENTIAL: "Exponential",
    TrendlineType.LOGARITHMIC: "Logarithmic",
    TrendlineType.POWER: "Power",
}


class MarkerShape(Enum):
    CIRCLE = "o"
    SQUARE = "s"
    TRIANGLE_UP = "^"
    TRIANGLE_DOWN = "v"
    DIAMOND = "D"
    PLUS = "+"
    CROSS = "x"
    STAR = "*"
    NONE = ""


class LineStyle(Enum):
    SOLID = "-"
    DASHED = "--"
    DOTTED = ":"
    DASH_DOT = "-."


class LegendPosition(Enum):
    BEST = "best"
    TOP_RIGHT = "upper right"
    TOP_LEFT = "upper left"
    BOTTOM_RIGHT = "lower right"
    BOTTOM_LEFT = "lower left"
    CENTER_RIGHT = "center right"
    CENTER_LEFT = "center left"
    UPPER_CENTER = "upper center"
    LOWER_CENTER = "lower center"
