from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Cell:
    row_id: int
    column_id: int
    value: str = ""
