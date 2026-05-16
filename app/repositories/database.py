from __future__ import annotations

import sqlite3
from pathlib import Path

from app.repositories.schema import SCHEMA_SQL


class DatabaseManager:
    def connect(self, path: str) -> sqlite3.Connection:
        connection = sqlite3.connect(Path(path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize_schema(self, connection: sqlite3.Connection) -> None:
        connection.executescript(SCHEMA_SQL)
        self._apply_lightweight_migrations(connection)

    def _apply_lightweight_migrations(self, connection: sqlite3.Connection) -> None:
        row_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(rows)").fetchall()
        }
        if "terminated_column_id" not in row_columns:
            connection.execute("ALTER TABLE rows ADD COLUMN terminated_column_id INTEGER")
