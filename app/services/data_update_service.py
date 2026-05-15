from __future__ import annotations

from datetime import datetime

from app.core import DuplicateMatchKeyError
from app.models import (
    Cell,
    Column,
    DataUpdateAction,
    DataUpdateDetail,
    DataUpdateResult,
    Project,
    Row,
)


class DataUpdateService:
    def update_project_from_table(
        self,
        project: Project,
        source_columns: list[str],
        source_rows: list[list[str]],
        target_key_column: str,
        source_key_column: str,
        overwrite_existing: bool = False,
        ignore_empty_values: bool = True,
        add_missing_columns: bool = True,
        append_unmatched_rows: bool = False,
        update_terminated_rows: bool = False,
    ) -> DataUpdateResult:
        target_column_map = {column.name: column for column in project.get_ordered_columns()}
        if target_key_column not in target_column_map:
            raise ValueError("主表匹配字段不存在")
        if source_key_column not in source_columns:
            raise ValueError("更新表匹配字段不存在")

        result = DataUpdateResult()
        source_key_index = source_columns.index(source_key_column)

        target_rows_by_key, duplicate_target_keys = self._build_target_row_map(
            project,
            target_column_map[target_key_column].id,
        )
        if duplicate_target_keys:
            result.duplicate_target_keys = duplicate_target_keys
            raise DuplicateMatchKeyError(
                "主表匹配字段存在重复值，无法执行数据更新",
                duplicate_target_keys=duplicate_target_keys,
            )

        source_rows_by_key, duplicate_source_keys = self._build_source_row_map(
            source_rows,
            source_key_index,
        )
        if duplicate_source_keys:
            result.duplicate_source_keys = duplicate_source_keys
            raise DuplicateMatchKeyError(
                "更新表匹配字段存在重复值，无法执行数据更新",
                duplicate_source_keys=duplicate_source_keys,
            )

        copied_source_columns = [
            name for name in source_columns if name and name != source_key_column
        ]
        if add_missing_columns:
            for column_name in copied_source_columns:
                if column_name in target_column_map:
                    continue
                column = self._append_column(project, column_name)
                target_column_map[column.name] = column
                result.added_columns.append(column.name)
                result.details.append(
                    DataUpdateDetail(
                        action=DataUpdateAction.ADD_COLUMN,
                        column_name=column.name,
                        new_value=column.name,
                        message=f"新增主表字段：{column.name}",
                    )
                )

        for source_key, source_row_info in source_rows_by_key.items():
            source_row_index, source_row = source_row_info
            target_row = target_rows_by_key.get(source_key)
            if target_row is None:
                result.unmatched_source_rows += 1
                if append_unmatched_rows:
                    row = project.append_row()
                    result.appended_rows += 1
                    result.details.append(
                        DataUpdateDetail(
                            action=DataUpdateAction.APPEND_ROW,
                            key_value=source_key,
                            source_row_index=source_row_index,
                            target_row_index=row.order_index + 1,
                            message="主表无匹配行，已追加新行",
                        )
                    )
                    self._set_cell_value(
                        project=project,
                        row_id=row.id,
                        column_id=target_column_map[target_key_column].id,
                        value=source_key,
                        result=result,
                        key_value=source_key,
                        source_row_index=source_row_index,
                        target_row_index=row.order_index + 1,
                        column_name=target_key_column,
                    )
                    self._update_row(
                        project=project,
                        target_row=row,
                        source_columns=source_columns,
                        source_row=source_row,
                        source_row_index=source_row_index,
                        source_key_column=source_key_column,
                        key_value=source_key,
                        target_column_map=target_column_map,
                        overwrite_existing=True,
                        ignore_empty_values=False,
                        update_terminated_rows=True,
                        result=result,
                    )
                else:
                    result.details.append(
                        DataUpdateDetail(
                            action=DataUpdateAction.UNMATCHED_ROW,
                            key_value=source_key,
                            source_row_index=source_row_index,
                            message="主表无匹配行，未追加",
                        )
                    )
                continue

            result.matched_rows += 1
            self._update_row(
                project=project,
                target_row=target_row,
                source_columns=source_columns,
                source_row=source_row,
                source_row_index=source_row_index,
                source_key_column=source_key_column,
                key_value=source_key,
                target_column_map=target_column_map,
                overwrite_existing=overwrite_existing,
                ignore_empty_values=ignore_empty_values,
                update_terminated_rows=update_terminated_rows,
                result=result,
            )

        return result

    def _build_target_row_map(
        self,
        project: Project,
        target_key_column_id: int,
    ) -> tuple[dict[str, Row], list[str]]:
        row_map: dict[str, Row] = {}
        duplicates: set[str] = set()

        for row in project.get_ordered_rows():
            key = self._normalize_key(project.get_cell_value(row.id, target_key_column_id))
            if not key:
                continue
            if key in row_map:
                duplicates.add(key)
                continue
            row_map[key] = row

        return row_map, sorted(duplicates)

    def _build_source_row_map(
        self,
        source_rows: list[list[str]],
        source_key_index: int,
    ) -> tuple[dict[str, tuple[int, list[str]]], list[str]]:
        row_map: dict[str, tuple[int, list[str]]] = {}
        duplicates: set[str] = set()

        for row_offset, source_row in enumerate(source_rows, start=1):
            key = self._normalize_key(self._get_source_value(source_row, source_key_index))
            if not key:
                continue
            if key in row_map:
                duplicates.add(key)
                continue
            row_map[key] = (row_offset, source_row)

        return row_map, sorted(duplicates)

    def _append_column(self, project: Project, column_name: str) -> Column:
        next_column_id = 1 if not project.columns else max(column.id for column in project.columns) + 1
        column = Column(id=next_column_id, name=column_name, order_index=len(project.columns))
        project.columns.append(column)
        for row in project.get_ordered_rows():
            if row.is_terminated:
                continue
            project.cells[(row.id, column.id)] = Cell(row_id=row.id, column_id=column.id, value="")
        project.updated_at = datetime.now().isoformat(timespec="seconds")
        return column

    def _update_row(
        self,
        *,
        project: Project,
        target_row: Row,
        source_columns: list[str],
        source_row: list[str],
        source_row_index: int,
        source_key_column: str,
        key_value: str,
        target_column_map: dict[str, Column],
        overwrite_existing: bool,
        ignore_empty_values: bool,
        update_terminated_rows: bool,
        result: DataUpdateResult,
    ) -> None:
        candidate_columns = [
            source_column_name
            for source_column_name in source_columns
            if source_column_name in target_column_map and source_column_name != source_key_column
        ]
        if target_row.is_terminated and not update_terminated_rows:
            result.skipped_terminated_rows += len(candidate_columns)
            for source_column_name in candidate_columns:
                result.details.append(
                    DataUpdateDetail(
                        action=DataUpdateAction.SKIP_TERMINATED,
                        key_value=key_value,
                        source_row_index=source_row_index,
                        target_row_index=target_row.order_index + 1,
                        column_name=source_column_name,
                        message="目标行为已终止，已跳过更新",
                    )
                )
            return

        for column_index, source_column_name in enumerate(source_columns):
            if source_column_name == source_key_column:
                continue
            if source_column_name not in target_column_map:
                continue

            source_value = self._get_source_value(source_row, column_index)
            target_column = target_column_map[source_column_name]
            current_value = project.get_cell_value(target_row.id, target_column.id)

            if ignore_empty_values and source_value == "":
                result.skipped_empty_values += 1
                result.details.append(
                    DataUpdateDetail(
                        action=DataUpdateAction.SKIP_EMPTY,
                        key_value=key_value,
                        source_row_index=source_row_index,
                        target_row_index=target_row.order_index + 1,
                        column_name=source_column_name,
                        old_value=current_value,
                        new_value=source_value,
                        message="更新表值为空，已跳过",
                    )
                )
                continue

            if not overwrite_existing and current_value != "":
                result.skipped_existing_values += 1
                result.details.append(
                    DataUpdateDetail(
                        action=DataUpdateAction.SKIP_EXISTING,
                        key_value=key_value,
                        source_row_index=source_row_index,
                        target_row_index=target_row.order_index + 1,
                        column_name=source_column_name,
                        old_value=current_value,
                        new_value=source_value,
                        message="主表已有值且未启用覆盖，已跳过",
                    )
                )
                continue

            if current_value == source_value:
                continue

            self._set_cell_value(
                project=project,
                row_id=target_row.id,
                column_id=target_column.id,
                value=source_value,
                result=result,
                key_value=key_value,
                source_row_index=source_row_index,
                target_row_index=target_row.order_index + 1,
                column_name=source_column_name,
                old_value=current_value,
            )

    def _set_cell_value(
        self,
        *,
        project: Project,
        row_id: int,
        column_id: int,
        value: str,
        result: DataUpdateResult,
        key_value: str,
        source_row_index: int,
        target_row_index: int,
        column_name: str,
        old_value: str = "",
    ) -> None:
        project.set_cell_value(row_id, column_id, value)
        result.updated_cells += 1
        result.details.append(
            DataUpdateDetail(
                action=DataUpdateAction.UPDATE_CELL,
                key_value=key_value,
                source_row_index=source_row_index,
                target_row_index=target_row_index,
                column_name=column_name,
                old_value=old_value,
                new_value=value,
                message="已更新单元格",
            )
        )

    @staticmethod
    def _get_source_value(source_row: list[str], column_index: int) -> str:
        if column_index >= len(source_row):
            return ""
        value = source_row[column_index]
        return "" if value is None else str(value)

    @staticmethod
    def _normalize_key(value: str) -> str:
        return value.strip()
