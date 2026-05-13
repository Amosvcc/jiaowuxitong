from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StatisticsItem:
    value: str
    count: int
    ratio: float
