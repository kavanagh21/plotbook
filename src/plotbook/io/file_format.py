"""Save/load .plotbook project files (JSON)."""

from __future__ import annotations

import json

from plotbook.models.project import Project

PLOTBOOK_VERSION = 1


def save_project(project: Project, path: str) -> None:
    data = {
        "version": PLOTBOOK_VERSION,
        "project": project.to_dict(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=_json_default)


def load_project(path: str) -> Project:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    version = data.get("version", 1)
    if version != PLOTBOOK_VERSION:
        pass  # Future: migration logic

    return Project.from_dict(data["project"])


def _json_default(obj):
    """Handle NaN/Inf in JSON serialization."""
    import math
    if isinstance(obj, float):
        if math.isnan(obj):
            return None
        if math.isinf(obj):
            return None
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
