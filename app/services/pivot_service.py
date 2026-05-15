from __future__ import annotations

import re
from collections import OrderedDict

import pandas as pd

from app.models import PivotResult, Project


class PivotService:
    DEFAULT_TAG_SEPARATORS = [";", "；", ",", "，", "、", "/", "|", "\n"]

    def build_pivot(
        self,
        project: Project,
        row_field: str,
        column_field: str,
        expand_column_tags: bool = False,
        tag_separators: list[str] | None = None,
        ignore_empty_row_values: bool = True,
        ignore_empty_column_values: bool = True,
        include_terminated_rows: bool = False,
        show_row_totals: bool = True,
        show_column_totals: bool = True,
    ) -> PivotResult:
        original_dirty = project.dirty
        row_column = self._resolve_column(project, row_field)
        column_column = self._resolve_column(project, column_field)

        row_headers: list[str] = []
        column_headers: list[str] = []
        row_seen: set[str] = set()
        column_seen: set[str] = set()
        matrix: dict[str, dict[str, int]] = {}
        row_totals: dict[str, int] = {}
        column_totals: dict[str, int] = {}
        grand_total = 0
        skipped_empty_row_values = 0
        skipped_empty_column_values = 0
        skipped_terminated_rows = 0

        separators = tag_separators or self.DEFAULT_TAG_SEPARATORS

        for row in project.get_ordered_rows():
            if row.is_terminated and not include_terminated_rows:
                skipped_terminated_rows += 1
                continue

            row_value = project.get_cell_value(row.id, row_column.id).strip()
            if not row_value and ignore_empty_row_values:
                skipped_empty_row_values += 1
                continue

            column_value = project.get_cell_value(row.id, column_column.id)
            column_keys = self._parse_column_keys(
                column_value,
                expand_column_tags=expand_column_tags,
                tag_separators=separators,
            )
            if not column_keys and ignore_empty_column_values:
                skipped_empty_column_values += 1
                continue
            if not column_keys:
                column_keys = [""]

            if row_value not in row_seen:
                row_seen.add(row_value)
                row_headers.append(row_value)
            if row_value not in matrix:
                matrix[row_value] = {}
            row_totals.setdefault(row_value, 0)

            for column_key in column_keys:
                if column_key not in column_seen:
                    column_seen.add(column_key)
                    column_headers.append(column_key)
                matrix[row_value][column_key] = matrix[row_value].get(column_key, 0) + 1
                row_totals[row_value] += 1
                column_totals[column_key] = column_totals.get(column_key, 0) + 1
                grand_total += 1

        result = PivotResult(
            row_field=row_field,
            column_field=column_field,
            row_headers=row_headers,
            column_headers=column_headers,
            matrix=matrix,
            row_totals=row_totals,
            column_totals=column_totals,
            grand_total=grand_total,
            include_terminated_rows=include_terminated_rows,
            ignore_empty_row_values=ignore_empty_row_values,
            ignore_empty_column_values=ignore_empty_column_values,
            expand_column_tags=expand_column_tags,
            show_row_totals=show_row_totals,
            show_column_totals=show_column_totals,
            skipped_empty_row_values=skipped_empty_row_values,
            skipped_empty_column_values=skipped_empty_column_values,
            skipped_terminated_rows=skipped_terminated_rows,
        )
        project.dirty = original_dirty
        return result

    def build_pivot_dataframe(self, result: PivotResult) -> pd.DataFrame:
        rows: list[OrderedDict[str, object]] = []
        for row_header in result.row_headers:
            row = OrderedDict()
            row[result.row_field] = row_header
            for column_header in result.column_headers:
                row[column_header] = result.matrix.get(row_header, {}).get(column_header, 0)
            if result.show_row_totals:
                row["合计"] = result.row_totals.get(row_header, 0)
            rows.append(row)

        if result.show_column_totals:
            total_row = OrderedDict()
            total_row[result.row_field] = "合计"
            for column_header in result.column_headers:
                total_row[column_header] = result.column_totals.get(column_header, 0)
            if result.show_row_totals:
                total_row["合计"] = result.grand_total
            rows.append(total_row)

        columns = [result.row_field, *result.column_headers]
        if result.show_row_totals:
            columns.append("合计")
        return pd.DataFrame(rows, columns=columns)

    def _resolve_column(self, project: Project, field_name: str):
        normalized_field_name = field_name.strip()
        for column in project.get_ordered_columns():
            if column.name == normalized_field_name:
                return column
        raise ValueError(f"字段不存在: {field_name}")

    def _parse_column_keys(
        self,
        value: str,
        *,
        expand_column_tags: bool,
        tag_separators: list[str],
    ) -> list[str]:
        raw_value = value.strip()
        if not expand_column_tags:
            return [raw_value] if raw_value else []

        if not raw_value:
            return []

        pattern = "|".join(re.escape(separator) for separator in tag_separators if separator)
        if not pattern:
            return [raw_value]

        parts = re.split(pattern, raw_value)
        keys: list[str] = []
        seen: set[str] = set()
        for part in parts:
            token = part.strip()
            if not token or token in seen:
                continue
            seen.add(token)
            keys.append(token)
        return keys
