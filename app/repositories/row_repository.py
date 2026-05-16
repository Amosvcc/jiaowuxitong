from __future__ import annotations

import sqlite3
from datetime import datetime

from app.models import Row


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class RowRepository:
    def save_all(self, connection: sqlite3.Connection, rows: list[Row]) -> None:
        connection.execute("DELETE FROM rows")
        timestamp = _now_iso()
        connection.executemany(
            """
            INSERT INTO rows (
                id, order_index, is_terminated, terminated_at, terminated_column_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row.id,
                    row.order_index,
                    1 if row.is_terminated else 0,
                    row.terminated_at,
                    row.terminated_column_id,
                    timestamp,
                    timestamp,
                )
                for row in rows
            ],
        )

    def load_all(self, connection: sqlite3.Connection) -> list[Row]:
        rows = connection.execute(
            """
            SELECT id, order_index, is_terminated, terminated_at, terminated_column_id
            FROM rows
            ORDER BY order_index
            """
        ).fetchall()
        return [
            Row(
                id=row["id"],
                order_index=row["order_index"],
                is_terminated=bool(row["is_terminated"]),
                terminated_at=row["terminated_at"],
                terminated_column_id=row["terminated_column_id"],
            )
            for row in rows
        ]
