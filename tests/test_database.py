import sqlite3

from app.repositories.database import DatabaseManager


def test_database_initializes_expected_tables(workspace_tmp_path) -> None:
    path = workspace_tmp_path / "schema.dasproj"
    manager = DatabaseManager()
    connection = manager.connect(str(path))

    try:
        manager.initialize_schema(connection)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        connection.close()

    assert {"project_info", "columns", "rows", "cells", "app_settings"} <= tables
