from __future__ import annotations

from datetime import datetime

from app.models import Column, Project


class ColumnService:
    VALID_FIELD_TYPES = {"text", "number", "date", "dropdown"}

    def update_column(
        self,
        project: Project,
        column_index: int,
        *,
        name: str,
        field_type: str,
        dropdown_options: list[str],
        allow_custom_value: bool,
    ) -> Column:
        if column_index < 0 or column_index >= len(project.columns):
            raise ValueError("列索引超出范围")

        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("列名不能为空")

        duplicate_names = {
            column.name.strip()
            for index, column in enumerate(project.columns)
            if index != column_index
        }
        if normalized_name in duplicate_names:
            raise ValueError("列名不能重复")

        normalized_field_type = field_type.strip().lower()
        if normalized_field_type not in self.VALID_FIELD_TYPES:
            raise ValueError("不支持的字段类型")

        normalized_options = self._normalize_dropdown_options(dropdown_options)
        if normalized_field_type == "dropdown" and not normalized_options:
            raise ValueError("下拉选项不能为空")

        column = project.columns[column_index]
        column.name = normalized_name
        column.field_type = normalized_field_type
        column.dropdown_options = normalized_options
        column.allow_custom_value = allow_custom_value
        project.updated_at = datetime.now().isoformat(timespec="seconds")
        project.dirty = True
        return column

    def _normalize_dropdown_options(self, dropdown_options: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()

        for option in dropdown_options:
            trimmed = option.strip()
            if not trimmed:
                raise ValueError("下拉选项不能为空")
            if trimmed in seen:
                raise ValueError("同一列下拉选项不能重复")
            seen.add(trimmed)
            normalized.append(trimmed)

        return normalized
