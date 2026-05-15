from __future__ import annotations

from copy import deepcopy

from app.models import Project


class UndoService:
    def __init__(self, max_snapshots: int = 50) -> None:
        self.max_snapshots = max_snapshots
        self._snapshots: list[Project] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._snapshots)

    def push_snapshot(self, project: Project) -> None:
        self._snapshots.append(deepcopy(project))
        if len(self._snapshots) > self.max_snapshots:
            self._snapshots.pop(0)

    def pop_snapshot(self) -> Project | None:
        if not self._snapshots:
            return None
        return deepcopy(self._snapshots.pop())

    def discard_latest(self) -> None:
        if self._snapshots:
            self._snapshots.pop()

    def clear(self) -> None:
        self._snapshots.clear()
