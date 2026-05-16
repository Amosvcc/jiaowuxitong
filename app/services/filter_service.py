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

        rows_by_id = {str(row.id): row for row in project.get_ordered_rows()}
        row = rows_by_id.get(str(row_id))
        if row is None:
            raise ValueError(f"行不存在：{row_id}")
        return self._row_matches_compiled_filters(
            project,
            row,
            filter_state.row_status,
            self._compile_column_filters(project, filter_state),
        )

    def get_matching_row_ids(
        self,
        project: Project,
        filter_state: TableFilterState,
    ) -> set[str]:
        if not filter_state.is_active:
            return {str(row.id) for row in project.get_ordered_rows()}

        compiled_filters = self._compile_column_filters(project, filter_state)
        row_status = filter_state.row_status
        return {
            str(row.id)
            for row in project.get_ordered_rows()
            if self._row_matches_compiled_filters(project, row, row_status, compiled_filters)
        }

    def _compile_column_filters(
        self,
        project: Project,
        filter_state: TableFilterState,
    ) -> list[tuple[int, set[str], bool]]:
        column_ids_by_string = {
            str(column.id): column.id for column in project.get_ordered_columns()
        }
        compiled_filters: list[tuple[int, set[str], bool]] = []
        for criteria in filter_state.filters.values():
            if not criteria.is_active:
                continue
            column_id = column_ids_by_string.get(str(criteria.column_id))
            if column_id is None:
                raise ValueError(f"字段不存在：{criteria.column_id}")
            compiled_filters.append(
                (column_id, set(criteria.selected_values), criteria.include_blank)
            )
        return compiled_filters

    @staticmethod
    def _row_matches_compiled_filters(
        project: Project,
        row,
        row_status: str,
        compiled_filters: list[tuple[int, set[str], bool]],
    ) -> bool:
        if row_status == "terminated" and not row.is_terminated:
            return False
        if row_status == "active" and row.is_terminated:
            return False

        for column_id, selected_values, include_blank in compiled_filters:
            value = project.get_cell_value(row.id, column_id)
            if value == "":
                if not include_blank:
                    return False
                continue
            if value not in selected_values:
                return False
        return True

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
