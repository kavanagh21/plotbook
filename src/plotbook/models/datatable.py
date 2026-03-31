"""Core data table model."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

import numpy as np

from plotbook.models.enums import EntryMode, ErrorBarType, TableFormat


@dataclass
class ColumnDef:
    """Metadata for a single visual column in the spreadsheet."""
    name: str
    group_id: str       # Which DataSeries this belongs to
    role: str           # "x", "y", "mean", "sd", "sem", "replicate", "row_label"
    replicate_index: int = 0


class DataSeries:
    """One logical data series (a Y dataset, group, or treatment)."""

    def __init__(
        self,
        name: str,
        entry_mode: EntryMode,
        n_rows: int = 20,
        n_replicates: int = 3,
        series_id: str | None = None,
    ):
        self.id = series_id or uuid.uuid4().hex[:8]
        self.name = name
        self.entry_mode = entry_mode

        # Determine number of subcolumns based on entry mode
        if entry_mode == EntryMode.RAW:
            n_subcols = n_replicates
        elif entry_mode in (EntryMode.MEAN_SD, EntryMode.MEAN_SEM):
            n_subcols = 2  # [mean, error]
        else:  # SINGLE
            n_subcols = 1

        self.data: np.ndarray = np.full((n_rows, n_subcols), np.nan, dtype=np.float64)

    @property
    def n_rows(self) -> int:
        return self.data.shape[0]

    @property
    def n_subcols(self) -> int:
        return self.data.shape[1]

    @property
    def n_replicates(self) -> int:
        if self.entry_mode == EntryMode.RAW:
            return self.data.shape[1]
        return 0

    def ensure_rows(self, n: int) -> None:
        """Expand row count if needed."""
        if n > self.n_rows:
            extra = np.full((n - self.n_rows, self.n_subcols), np.nan, dtype=np.float64)
            self.data = np.vstack([self.data, extra])

    def add_replicate_column(self) -> None:
        """Add a replicate column (RAW mode only)."""
        if self.entry_mode != EntryMode.RAW:
            return
        col = np.full((self.n_rows, 1), np.nan, dtype=np.float64)
        self.data = np.hstack([self.data, col])

    def computed_mean(self) -> np.ndarray:
        """Per-row means."""
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            if self.entry_mode == EntryMode.RAW:
                return np.nanmean(self.data, axis=1)
            else:
                return self.data[:, 0].copy()

    def computed_error(self, error_type: ErrorBarType) -> np.ndarray:
        """Per-row error values for the given error bar type."""
        if error_type == ErrorBarType.NONE:
            return np.zeros(self.n_rows)

        if self.entry_mode == EntryMode.MEAN_SD:
            if error_type == ErrorBarType.SD:
                return self.data[:, 1].copy()
            # Convert SD to SEM: SEM = SD / sqrt(n), but n is unknown in MEAN_SD mode
            return self.data[:, 1].copy()

        if self.entry_mode == EntryMode.MEAN_SEM:
            if error_type == ErrorBarType.SEM:
                return self.data[:, 1].copy()
            return self.data[:, 1].copy()

        if self.entry_mode == EntryMode.SINGLE:
            return np.zeros(self.n_rows)

        # RAW mode: compute from replicates
        from plotbook.stats.descriptive import (
            row_ci95,
            row_ci99,
            row_range_half,
            row_sd,
            row_sem,
        )

        if error_type == ErrorBarType.SD:
            return row_sd(self.data)
        elif error_type == ErrorBarType.SEM:
            return row_sem(self.data)
        elif error_type == ErrorBarType.CI95:
            return row_ci95(self.data)
        elif error_type == ErrorBarType.CI99:
            return row_ci99(self.data)
        elif error_type == ErrorBarType.RANGE:
            return row_range_half(self.data)
        return np.zeros(self.n_rows)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "entry_mode": self.entry_mode.name,
            "data": self.data.tolist(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> DataSeries:
        entry_mode = EntryMode[d["entry_mode"]]
        data = np.array(d["data"], dtype=np.float64)
        series = cls(
            name=d["name"],
            entry_mode=entry_mode,
            n_rows=data.shape[0],
            n_replicates=data.shape[1] if entry_mode == EntryMode.RAW else 3,
            series_id=d["id"],
        )
        series.data = data
        return series


class DataTable:
    """Base class for all table formats."""

    def __init__(self, name: str, table_format: TableFormat, entry_mode: EntryMode):
        self.name = name
        self.table_format = table_format
        self.entry_mode = entry_mode
        self._series: list[DataSeries] = []
        self._row_count: int = 20

    @property
    def series(self) -> list[DataSeries]:
        return self._series

    def add_series(self, name: str, n_replicates: int = 3) -> DataSeries:
        s = DataSeries(
            name=name,
            entry_mode=self.entry_mode,
            n_rows=self._row_count,
            n_replicates=n_replicates,
        )
        self._series.append(s)
        return s

    def remove_series(self, series_id: str) -> None:
        self._series = [s for s in self._series if s.id != series_id]

    def row_count(self) -> int:
        return self._row_count

    def ensure_rows(self, n: int) -> None:
        if n > self._row_count:
            self._row_count = n
            for s in self._series:
                s.ensure_rows(n)

    def column_defs(self) -> list[ColumnDef]:
        raise NotImplementedError

    def get_value(self, row: int, col: int) -> float:
        raise NotImplementedError

    def set_value(self, row: int, col: int, value: float | None) -> None:
        raise NotImplementedError

    def has_data(self) -> bool:
        """Check if any non-NaN data exists."""
        for s in self._series:
            if not np.all(np.isnan(s.data)):
                return True
        return False

    def _base_dict(self) -> dict:
        return {
            "name": self.name,
            "table_format": self.table_format.name,
            "entry_mode": self.entry_mode.name,
            "row_count": self._row_count,
            "series": [s.to_dict() for s in self._series],
        }

    def _load_base(self, d: dict) -> None:
        self._row_count = d["row_count"]
        self._series = [DataSeries.from_dict(sd) for sd in d["series"]]
