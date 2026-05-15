from __future__ import annotations

from datetime import datetime

from app.models import Project


class RowService:
    def delete_rows(self, project: Project, row_indexes: list[int]) -> int:
        valid_indexes = sorted(
            {index for index in row_indexes if 0 <= index < len(project.rows)},
            reverse=True,
        )
        if not valid_indexes:
            return 0

        deleted_row_ids: set[int] = set()
        for row_index in valid_indexes:
            row = project.rows.pop(row_index)
            deleted_row_ids.add(row.id)

        project.cells = {
            key: cell
            for key, cell in project.cells.items()
            if key[0] not in deleted_row_ids
        }
        for order_index, row in enumerate(project.rows):
            row.order_index = order_index

        project.updated_at = datetime.now().isoformat(timespec="seconds")
        project.dirty = True
        return len(valid_indexes)

    def terminate_rows(self, project: Project, row_indexes: list[int]) -> int:
        return self._set_rows_terminated_state(project, row_indexes, is_terminated=True)

    def restore_rows(self, project: Project, row_indexes: list[int]) -> int:
        return self._set_rows_terminated_state(project, row_indexes, is_terminated=False)

    def _set_rows_terminated_state(
        self,
        project: Project,
        row_indexes: list[int],
        *,
        is_terminated: bool,
    ) -> int:
        affected_rows = 0
        timestamp = datetime.now().isoformat(timespec="seconds")
        valid_indexes = sorted({index for index in row_indexes if 0 <= index < len(project.rows)})
        if not valid_indexes:
            return 0

        for row_index in valid_indexes:
            row = project.rows[row_index]
            row.is_terminated = is_terminated
            row.terminated_at = timestamp if is_terminated else None
            affected_rows += 1

        project.updated_at = timestamp
        project.dirty = True
        return affected_rows
