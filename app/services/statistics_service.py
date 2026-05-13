from __future__ import annotations

from collections import Counter

import pandas as pd

from app.io.export_adapter import ExportAdapter
from app.models import Project, StatisticsItem


class StatisticsService:
    EMPTY_VALUE_LABEL = "<空值>"

    def __init__(self) -> None:
        self.export_adapter = ExportAdapter()

    def generate_statistics(
        self,
        project: Project,
        *,
        column_index: int | None = None,
        column_id: int | None = None,
        include_terminated: bool,
        ignore_empty: bool,
    ) -> list[StatisticsItem]:
        if not project.get_ordered_columns():
            return []

        column = self._resolve_column(project, column_index=column_index, column_id=column_id)
        counter: Counter[str] = Counter()
        total_count = 0

        for row in project.get_ordered_rows():
            if not include_terminated and row.is_terminated:
                continue

            value = project.get_cell_value(row.id, column.id)
            if value == "":
                if ignore_empty:
                    continue
                normalized_value = self.EMPTY_VALUE_LABEL
            else:
                normalized_value = value

            counter[normalized_value] += 1
            total_count += 1

        if total_count == 0:
            return []

        items = [
            StatisticsItem(value=value, count=count, ratio=count / total_count)
            for value, count in counter.items()
        ]
        items.sort(key=lambda item: (-item.count, item.value))
        return items

    def build_statistics_dataframe(
        self,
        column_name: str,
        items: list[StatisticsItem],
        *,
        include_terminated: bool,
        ignore_empty: bool,
    ) -> pd.DataFrame:
        rows = [
            {
                "统计字段": column_name,
                "字段值": item.value,
                "数量": item.count,
                "占比": self.format_ratio(item.ratio),
                "包含已终止行": "是" if include_terminated else "否",
                "忽略空值": "是" if ignore_empty else "否",
            }
            for item in items
        ]
        return pd.DataFrame(
            rows,
            columns=["统计字段", "字段值", "数量", "占比", "包含已终止行", "忽略空值"],
        )

    def export_statistics(
        self,
        path: str,
        column_name: str,
        items: list[StatisticsItem],
        *,
        include_terminated: bool,
        ignore_empty: bool,
    ) -> None:
        dataframe = self.build_statistics_dataframe(
            column_name,
            items,
            include_terminated=include_terminated,
            ignore_empty=ignore_empty,
        )
        self.export_adapter.write(dataframe, path)

    @staticmethod
    def format_ratio(ratio: float) -> str:
        return f"{ratio * 100:.2f}%"

    def _resolve_column(
        self,
        project: Project,
        *,
        column_index: int | None,
        column_id: int | None,
    ):
        ordered_columns = project.get_ordered_columns()
        if column_id is not None:
            for column in ordered_columns:
                if column.id == column_id:
                    return column
            raise ValueError("列 ID 不存在")

        if column_index is None:
            raise ValueError("必须提供列索引或列 ID")

        if column_index < 0 or column_index >= len(ordered_columns):
            raise ValueError("列索引超出范围")
        return ordered_columns[column_index]
