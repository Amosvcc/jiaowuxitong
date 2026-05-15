from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PivotResult:
    row_field: str
    column_field: str
    row_headers: list[str] = field(default_factory=list)
    column_headers: list[str] = field(default_factory=list)
    matrix: dict[str, dict[str, int]] = field(default_factory=dict)
    row_totals: dict[str, int] = field(default_factory=dict)
    column_totals: dict[str, int] = field(default_factory=dict)
    grand_total: int = 0
    include_terminated_rows: bool = False
    ignore_empty_row_values: bool = True
    ignore_empty_column_values: bool = True
    expand_column_tags: bool = False
    show_row_totals: bool = True
    show_column_totals: bool = True
    skipped_empty_row_values: int = 0
    skipped_empty_column_values: int = 0
    skipped_terminated_rows: int = 0
