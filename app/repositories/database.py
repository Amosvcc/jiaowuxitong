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
