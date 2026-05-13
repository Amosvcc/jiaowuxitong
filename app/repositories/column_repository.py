from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from app.models import Column


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class ColumnRepository:
    def save_all(self, connection: sqlite3.Connection, columns: list[Column]) -> None:
        connection.execute("DELETE FROM columns")
        timestamp = _now_iso()
        connection.executemany(
            """
            INSERT INTO columns (
                id, name, field_type, order_index, dropdown_options,
                allow_custom_value, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    column.id,
                    column.name,
                    column.field_type,
                    column.order_index,
                    json.dumps(column.dropdown_options, ensure_ascii=False),
                    1 if column.allow_custom_value else 0,
                    timestamp,
                    timestamp,
                )
                for column in columns
            ],
        )

    def load_all(self, connection: sqlite3.Connection) -> list[Column]:
        rows = connection.execute(
            """
            SELECT id, name, field_type, order_index, dropdown_options, allow_custom_value
            FROM columns
            ORDER BY order_index
            """
        ).fetchall()
        return [
            Column(
                id=row["id"],
                name=row["name"],
                field_type=row["field_type"],
                order_index=row["order_index"],
                dropdown_options=json.loads(row["dropdown_options"]),
                allow_custom_value=bool(row["allow_custom_value"]),
            )
            for row in rows
        ]
