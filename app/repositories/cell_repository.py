from __future__ import annotations

import sqlite3
from datetime import datetime

from app.models import Cell


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class CellRepository:
    def save_all(self, connection: sqlite3.Connection, cells: dict[tuple[int, int], Cell]) -> None:
        connection.execute("DELETE FROM cells")
        timestamp = _now_iso()
        ordered_cells = sorted(cells.values(), key=lambda cell: (cell.row_id, cell.column_id))
        connection.executemany(
            """
            INSERT INTO cells (row_id, column_id, value, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    cell.row_id,
                    cell.column_id,
                    cell.value,
                    timestamp,
                )
                for cell in ordered_cells
            ],
        )

    def load_all(self, connection: sqlite3.Connection) -> dict[tuple[int, int], Cell]:
        rows = connection.execute(
            """
            SELECT row_id, column_id, value
            FROM cells
            ORDER BY row_id, column_id
            """
        ).fetchall()
        return {
            (row["row_id"], row["column_id"]): Cell(
                row_id=row["row_id"],
                column_id=row["column_id"],
                value=row["value"],
            )
            for row in rows
        }
