from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Row:
    id: int
    order_index: int
    is_terminated: bool = False
    terminated_at: str | None = None
    terminated_column_id: int | None = None
