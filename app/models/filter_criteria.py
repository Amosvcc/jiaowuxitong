from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ColumnFilterCriteria:
    column_id: str
    selected_values: set[str] = field(default_factory=set)
    include_blank: bool = False

    @property
    def is_active(self) -> bool:
        return bool(self.selected_values) or self.include_blank


@dataclass
class TableFilterState:
    filters: dict[str, ColumnFilterCriteria] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        return any(criteria.is_active for criteria in self.filters.values())
