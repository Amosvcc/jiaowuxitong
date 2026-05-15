from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DataUpdateAction(StrEnum):
    ADD_COLUMN = "ADD_COLUMN"
    UPDATE_CELL = "UPDATE_CELL"
    SKIP_EMPTY = "SKIP_EMPTY"
    SKIP_EXISTING = "SKIP_EXISTING"
    SKIP_TERMINATED = "SKIP_TERMINATED"
    APPEND_ROW = "APPEND_ROW"
    UNMATCHED_ROW = "UNMATCHED_ROW"
    NO_CHANGE = "NO_CHANGE"


@dataclass(slots=True)
class DataUpdateDetail:
    action: DataUpdateAction
    key_value: str = ""
    source_row_index: int | None = None
    target_row_index: int | None = None
    column_name: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    message: str | None = None
