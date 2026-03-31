"""Save/load reusable style presets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from plotbook.models.graph_spec import GraphSpec
from plotbook.models.style import (
    AxisStyle,
    ErrorBarConfig,
    LegendStyle,
    SeriesStyle,
    TitleStyle,
)

PRESET_VERSION = 1


@dataclass
class StylePreset:
    """
    A saved style template. Captures all formatting from a GraphSpec
    but not the data-specific parts (graph_type, series IDs).

    When applied to a new sheet, series styles are mapped by position
    (first series gets first style, etc.) rather than by ID.
    """
    name: str
    description: str = ""

    # Ordered list of series styles (applied positionally)
    series_styles: list[SeriesStyle] | None = None

    # Global formatting
    title: TitleStyle | None = None
    x_axis: AxisStyle | None = None
    y_axis: AxisStyle | None = None
    legend: LegendStyle | None = None
    error_bars: ErrorBarConfig | None = None
    palette_name: str | None = None

    @classmethod
    def from_graph_spec(cls, spec: GraphSpec, name: str,
                        description: str = "") -> StylePreset:
        """Capture current formatting from a GraphSpec."""
        # Collect series styles in order (strip the ID keys)
        ordered_styles = list(spec.series_styles.values())

        return cls(
            name=name,
            description=description,
            series_styles=[_clone_series_style(s) for s in ordered_styles],
            title=TitleStyle.from_dict(spec.title.to_dict()),
            x_axis=AxisStyle.from_dict(spec.x_axis.to_dict()),
            y_axis=AxisStyle.from_dict(spec.y_axis.to_dict()),
            legend=LegendStyle.from_dict(spec.legend.to_dict()),
            error_bars=ErrorBarConfig.from_dict(spec.error_bars.to_dict()),
            palette_name=spec.palette_name,
        )

    def apply_to(self, spec: GraphSpec) -> None:
        """Apply this preset to a GraphSpec, mapping series styles by position."""
        if self.title is not None:
            spec.title = TitleStyle.from_dict(self.title.to_dict())
        if self.x_axis is not None:
            spec.x_axis = AxisStyle.from_dict(self.x_axis.to_dict())
        if self.y_axis is not None:
            spec.y_axis = AxisStyle.from_dict(self.y_axis.to_dict())
        if self.legend is not None:
            spec.legend = LegendStyle.from_dict(self.legend.to_dict())
        if self.error_bars is not None:
            spec.error_bars = ErrorBarConfig.from_dict(self.error_bars.to_dict())
        if self.palette_name is not None:
            spec.palette_name = self.palette_name

        # Map series styles by position
        if self.series_styles:
            series_ids = list(spec.series_styles.keys())
            for i, sid in enumerate(series_ids):
                if i < len(self.series_styles):
                    spec.series_styles[sid] = SeriesStyle.from_dict(
                        self.series_styles[i].to_dict()
                    )

    def to_dict(self) -> dict:
        d: dict = {
            "version": PRESET_VERSION,
            "name": self.name,
            "description": self.description,
        }
        if self.series_styles is not None:
            d["series_styles"] = [s.to_dict() for s in self.series_styles]
        if self.title is not None:
            d["title"] = self.title.to_dict()
        if self.x_axis is not None:
            d["x_axis"] = self.x_axis.to_dict()
        if self.y_axis is not None:
            d["y_axis"] = self.y_axis.to_dict()
        if self.legend is not None:
            d["legend"] = self.legend.to_dict()
        if self.error_bars is not None:
            d["error_bars"] = self.error_bars.to_dict()
        if self.palette_name is not None:
            d["palette_name"] = self.palette_name
        return d

    @classmethod
    def from_dict(cls, d: dict) -> StylePreset:
        return cls(
            name=d["name"],
            description=d.get("description", ""),
            series_styles=[SeriesStyle.from_dict(s) for s in d["series_styles"]]
                if "series_styles" in d else None,
            title=TitleStyle.from_dict(d["title"]) if "title" in d else None,
            x_axis=AxisStyle.from_dict(d["x_axis"]) if "x_axis" in d else None,
            y_axis=AxisStyle.from_dict(d["y_axis"]) if "y_axis" in d else None,
            legend=LegendStyle.from_dict(d["legend"]) if "legend" in d else None,
            error_bars=ErrorBarConfig.from_dict(d["error_bars"])
                if "error_bars" in d else None,
            palette_name=d.get("palette_name"),
        )


def _clone_series_style(s: SeriesStyle) -> SeriesStyle:
    return SeriesStyle.from_dict(s.to_dict())


# ---------------------------------------------------------------------------
# Preset storage: saved to ~/.plotbook/styles/ as individual JSON files
# ---------------------------------------------------------------------------

def _presets_dir() -> Path:
    d = Path.home() / ".plotbook" / "styles"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_preset(preset: StylePreset) -> Path:
    """Save a preset to disk. Returns the file path."""
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in preset.name)
    path = _presets_dir() / f"{safe_name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(preset.to_dict(), f, indent=2)
    return path


def load_preset(path: Path | str) -> StylePreset:
    """Load a single preset from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return StylePreset.from_dict(json.load(f))


def list_presets() -> list[StylePreset]:
    """List all saved presets."""
    presets = []
    for path in sorted(_presets_dir().glob("*.json")):
        try:
            presets.append(load_preset(path))
        except Exception:
            continue
    return presets


def delete_preset(name: str) -> bool:
    """Delete a preset by name. Returns True if deleted."""
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in name)
    path = _presets_dir() / f"{safe_name}.json"
    if path.exists():
        path.unlink()
        return True
    return False
