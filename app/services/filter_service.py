from __future__ import annotations

from collections import Counter

from app.models import Project
from app.models.filter_criteria import TableFilterState


class FilterService:
    def get_unique_values(
        self,
        project: Project,
        column_id: str,
        include_terminated_rows: bool = True,
    ) -> dict[str, int]:
        column = self._find_column(project, column_id)
        counter: Counter[str] = Counter()

        for row in project.get_ordered_rows():
            if row.is_terminated and not include_terminated_rows:
                continue
            counter[project.get_cell_value(row.id, column.id)] += 1

        return dict(sorted(counter.items(), key=lambda item: (item[0] != "", item[0])))

    def row_matches_filters(
        self,
        project: Project,
        row_id: str,
        filter_state: TableFilterState,
    ) -> bool:
        if not filter_state.is_active:
            return True

        row = self._find_row(project, row_id)
        if filter_state.row_status == "terminated" and not row.is_terminated:
            return False
        if filter_state.row_status == "active" and row.is_terminated:
            return False

        for criteria in filter_state.filters.values():
            if not criteria.is_active:
                continue
            column = self._find_column(project, criteria.column_id)
            value = project.get_cell_value(row.id, column.id)
            if value == "":
                if not criteria.include_blank:
                    return False
                continue
            if value not in criteria.selected_values:
                return False

        return True

    def get_matching_row_ids(
        self,
        project: Project,
        filter_state: TableFilterState,
    ) -> set[str]:
        return {
            str(row.id)
            for row in project.get_ordered_rows()
            if self.row_matches_filters(project, str(row.id), filter_state)
        }

    @staticmethod
    def _find_column(project: Project, column_id: str):
        for column in project.get_ordered_columns():
            if str(column.id) == str(column_id):
                return column
        raise ValueError(f"字段不存在：{column_id}")

    @staticmethod
    def _find_row(project: Project, row_id: str):
        for row in project.get_ordered_rows():
            if str(row.id) == str(row_id):
                return row
        raise ValueError(f"行不存在：{row_id}")
