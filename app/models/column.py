from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Column:
    id: int
    name: str
    field_type: str = "text"
    order_index: int = 0
    dropdown_options: list[str] = field(default_factory=list)
    allow_custom_value: bool = True
