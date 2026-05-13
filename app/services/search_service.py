from __future__ import annotations

from app.models import Project


class SearchService:
    def search(self, project: Project, keyword: str) -> list[tuple[int, int]]:
        normalized_keyword = keyword.strip().lower()
        if not normalized_keyword:
            return []

        matches: list[tuple[int, int]] = []
        ordered_rows = project.get_ordered_rows()
        ordered_columns = project.get_ordered_columns()

        for row_index, row in enumerate(ordered_rows):
            for column_index, column in enumerate(ordered_columns):
                value = project.get_cell_value(row.id, column.id)
                if normalized_keyword in value.lower():
                    matches.append((row_index, column_index))

        return matches
