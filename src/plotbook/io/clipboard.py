"""Clipboard utilities for paste from Excel/Google Sheets."""

from __future__ import annotations


def parse_tsv(text: str) -> list[list[str]]:
    """Parse tab-separated text (from Excel/Sheets clipboard) into 2D list."""
    rows = []
    for line in text.strip().split("\n"):
        cells = line.split("\t")
        rows.append([c.strip() for c in cells])
    return rows
