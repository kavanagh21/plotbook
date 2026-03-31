"""Color palettes for graph series."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ColorPalette:
    name: str
    colors: list[str]

    def color_at(self, index: int) -> str:
        return self.colors[index % len(self.colors)]


BUILTIN_PALETTES: dict[str, ColorPalette] = {}


def load_palettes() -> dict[str, ColorPalette]:
    """Load built-in palettes from resources/palettes.json."""
    global BUILTIN_PALETTES

    # Look relative to this file's package, then fall back to project root
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "resources" / "palettes.json",
        Path(__file__).resolve().parent.parent.parent / "resources" / "palettes.json",
    ]

    for path in candidates:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            BUILTIN_PALETTES = {
                name: ColorPalette(name=name, colors=colors)
                for name, colors in raw.items()
            }
            return BUILTIN_PALETTES

    # Fallback: default palette hardcoded
    BUILTIN_PALETTES = {
        "default": ColorPalette(
            name="default",
            colors=[
                "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
                "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
            ],
        )
    }
    return BUILTIN_PALETTES


def get_palette(name: str = "default") -> ColorPalette:
    if not BUILTIN_PALETTES:
        load_palettes()
    return BUILTIN_PALETTES.get(name, BUILTIN_PALETTES["default"])
