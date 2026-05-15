from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from app.models.cell import Cell
from app.models.column import Column
from app.models.row import Row


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass(slots=True)
class Project:
    name: str = "未命名项目"
    file_path: str | None = None
    dirty: bool = False
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    app_version: str = "1.0"
    columns: list[Column] = field(default_factory=list)
    rows: list[Row] = field(default_factory=list)
    cells: dict[tuple[int, int], Cell] = field(default_factory=dict)

    @classmethod
    def create_empty(
        cls,
        row_count: int = 10,
        column_count: int = 5,
        *,
        name: str = "未命名项目",
    ) -> "Project":
        columns = [
            Column(id=index, name=f"字段{index}", order_index=index - 1)
            for index in range(1, column_count + 1)
        ]
        rows = [Row(id=index, order_index=index - 1) for index in range(1, row_count + 1)]
        cells = {
            (row.id, column.id): Cell(row_id=row.id, column_id=column.id, value="")
            for row in rows
            for column in columns
        }
        return cls(name=name, columns=columns, rows=rows, cells=cells)

    @classmethod
    def from_dataframe(cls, dataframe: pd.DataFrame) -> "Project":
        normalized_names = cls._normalize_column_names(list(dataframe.columns))
        columns = [
            Column(
                id=index,
                name=name,
                field_type="text",
                order_index=index - 1,
                dropdown_options=[],
                allow_custom_value=True,
            )
            for index, name in enumerate(normalized_names, start=1)
        ]
        rows = [
            Row(id=index, order_index=index - 1, is_terminated=False)
            for index in range(1, len(dataframe.index) + 1)
        ]
        cells: dict[tuple[int, int], Cell] = {}

        for row_position, row in enumerate(rows):
            for column_position, column in enumerate(columns):
                value = dataframe.iat[row_position, column_position]
                cells[(row.id, column.id)] = Cell(
                    row_id=row.id,
                    column_id=column.id,
                    value="" if pd.isna(value) else str(value),
                )

        return cls(columns=columns, rows=rows, cells=cells)

    def to_dataframe(self) -> pd.DataFrame:
        ordered_columns = self.get_ordered_columns()
        ordered_rows = self.get_ordered_rows()
        return pd.DataFrame(
            [
                [self.get_cell_value(row.id, column.id) for column in ordered_columns]
                for row in ordered_rows
            ],
            columns=[column.name for column in ordered_columns],
        )

    @staticmethod
    def _normalize_column_names(names: list[object]) -> list[str]:
        normalized_names: list[str] = []
        name_counts: dict[str, int] = {}

        for index, raw_name in enumerate(names, start=1):
            candidate = "" if pd.isna(raw_name) else str(raw_name).strip()
            base_name = candidate or f"字段{index}"
            name_counts[base_name] = name_counts.get(base_name, 0) + 1
            normalized_names.append(
                base_name if name_counts[base_name] == 1 else f"{base_name}_{name_counts[base_name]}"
            )

        return normalized_names

    def get_ordered_columns(self) -> list[Column]:
        return sorted(self.columns, key=lambda column: column.order_index)

    def get_ordered_rows(self) -> list[Row]:
        return sorted(self.rows, key=lambda row: row.order_index)

    def get_cell_value(self, row_id: int, column_id: int) -> str:
        cell = self.cells.get((row_id, column_id))
        return "" if cell is None else cell.value

    def set_cell_value(self, row_id: int, column_id: int, value: str) -> None:
        self.cells[(row_id, column_id)] = Cell(row_id=row_id, column_id=column_id, value=value)
        self.updated_at = _now_iso()

    def append_row(self) -> Row:
        return self.insert_row(len(self.rows))

    def insert_row(self, row_index: int) -> Row:
        next_row_id = 1 if not self.rows else max(row.id for row in self.rows) + 1
        insert_index = min(max(row_index, 0), len(self.rows))
        row = Row(id=next_row_id, order_index=insert_index)
        self.rows.insert(insert_index, row)
        for order_index, existing_row in enumerate(self.rows):
            existing_row.order_index = order_index
        for column in self.get_ordered_columns():
            self.cells[(row.id, column.id)] = Cell(row_id=row.id, column_id=column.id, value="")
        self.updated_at = _now_iso()
        return row

    def append_column(self) -> Column:
        return self.insert_column(len(self.columns))

    def insert_column(self, column_index: int) -> Column:
        next_column_id = 1 if not self.columns else max(column.id for column in self.columns) + 1
        insert_index = min(max(column_index, 0), len(self.columns))
        column = Column(id=next_column_id, name=f"字段{next_column_id}", order_index=insert_index)
        self.columns.insert(insert_index, column)
        for order_index, existing_column in enumerate(self.columns):
            existing_column.order_index = order_index
        for row in self.get_ordered_rows():
            if row.is_terminated:
                continue
            self.cells[(row.id, column.id)] = Cell(row_id=row.id, column_id=column.id, value="")
        self.updated_at = _now_iso()
        return column
