from __future__ import annotations

from dataclasses import dataclass, field

from app.models.update_detail import DataUpdateDetail


@dataclass(slots=True)
class DataUpdateResult:
    matched_rows: int = 0
    unmatched_source_rows: int = 0
    appended_rows: int = 0
    added_columns: list[str] = field(default_factory=list)
    updated_cells: int = 0
    skipped_empty_values: int = 0
    skipped_existing_values: int = 0
    skipped_terminated_rows: int = 0
    duplicate_target_keys: list[str] = field(default_factory=list)
    duplicate_source_keys: list[str] = field(default_factory=list)
    details: list[DataUpdateDetail] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added_columns or self.updated_cells or self.appended_rows)
