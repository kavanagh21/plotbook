"""Project and Sheet models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from plotbook.models.datatable import DataTable
from plotbook.models.enums import (
    GRAPH_TYPES_FOR_FORMAT,
    EntryMode,
    GraphType,
    TableFormat,
)
from plotbook.models.graph_spec import GraphSpec
from plotbook.models.table_formats import create_table, table_from_dict


@dataclass
class Sheet:
    """One sheet = one data table + one graph spec."""

    id: str
    name: str
    data_table: DataTable
    graph_spec: GraphSpec

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "data_table": self.data_table.to_dict(),
            "graph_spec": self.graph_spec.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> Sheet:
        return cls(
            id=d["id"],
            name=d["name"],
            data_table=table_from_dict(d["data_table"]),
            graph_spec=GraphSpec.from_dict(d["graph_spec"]),
        )


@dataclass
class Project:
    """Top-level document. Collection of sheets."""

    name: str
    file_path: str | None = None
    sheets: list[Sheet] = field(default_factory=list)
    dirty: bool = False

    def add_sheet(
        self,
        table_format: TableFormat,
        entry_mode: EntryMode,
        graph_type: GraphType | None = None,
        name: str = "",
    ) -> Sheet:
        if not name:
            name = f"Sheet {len(self.sheets) + 1}"

        if graph_type is None:
            graph_type = GRAPH_TYPES_FOR_FORMAT[table_format][0]

        table = create_table(name, table_format, entry_mode)

        # Create default series
        if table_format == TableFormat.XY:
            table.add_series("Dataset A")
        elif table_format == TableFormat.COLUMN:
            for label in ["Group A", "Group B", "Group C"]:
                table.add_series(label)
        elif table_format == TableFormat.GROUPED:
            table.add_series("Treatment A")
            table.add_series("Treatment B")

        spec = GraphSpec(graph_type=graph_type)

        # Assign palette colors to default series
        for i, series in enumerate(table.series):
            spec.ensure_series_style(series.id, i)

        sheet = Sheet(
            id=uuid.uuid4().hex[:8],
            name=name,
            data_table=table,
            graph_spec=spec,
        )
        self.sheets.append(sheet)
        self.dirty = True
        return sheet

    def remove_sheet(self, sheet_id: str) -> None:
        self.sheets = [s for s in self.sheets if s.id != sheet_id]
        self.dirty = True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "sheets": [s.to_dict() for s in self.sheets],
        }

    @classmethod
    def from_dict(cls, d: dict) -> Project:
        p = cls(name=d["name"])
        p.sheets = [Sheet.from_dict(sd) for sd in d.get("sheets", [])]
        return p
