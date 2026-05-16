from __future__ import annotations

import sqlite3
import json
from pathlib import Path

from app.models import Project
from app.repositories.cell_repository import CellRepository
from app.repositories.column_repository import ColumnRepository
from app.repositories.database import DatabaseManager
from app.repositories.row_repository import RowRepository


class ProjectRepository:
    def __init__(self, database_manager: DatabaseManager | None = None) -> None:
        self.database_manager = database_manager or DatabaseManager()
        self.column_repository = ColumnRepository()
        self.row_repository = RowRepository()
        self.cell_repository = CellRepository()

    def save(self, path: str, project: Project) -> None:
        connection = self.database_manager.connect(path)
        try:
            self.database_manager.initialize_schema(connection)
            with connection:
                connection.execute("DELETE FROM app_settings")
                connection.execute("DELETE FROM project_info")
                connection.execute("DELETE FROM cells")
                connection.execute("DELETE FROM rows")
                connection.execute("DELETE FROM columns")
                self.column_repository.save_all(connection, project.get_ordered_columns())
                self.row_repository.save_all(connection, project.get_ordered_rows())
                self.cell_repository.save_all(connection, project.cells)
                connection.execute(
                    """
                    INSERT INTO project_info (id, name, created_at, updated_at, app_version)
                    VALUES (1, ?, ?, ?, ?)
                    """,
                    (project.name, project.created_at, project.updated_at, project.app_version),
                )
                self._save_app_settings(connection, project.view_settings)
        finally:
            connection.close()

    def load(self, path: str) -> Project:
        connection = self.database_manager.connect(path)
        try:
            self.database_manager.initialize_schema(connection)
            project_info = connection.execute(
                "SELECT name, created_at, updated_at, app_version FROM project_info WHERE id = 1"
            ).fetchone()
            if project_info is None:
                raise ValueError("项目文件无有效项目数据")

            project = Project(
                name=project_info["name"],
                file_path=str(Path(path)),
                dirty=False,
                created_at=project_info["created_at"],
                updated_at=project_info["updated_at"],
                app_version=project_info["app_version"],
                columns=self.column_repository.load_all(connection),
                rows=self.row_repository.load_all(connection),
                cells=self.cell_repository.load_all(connection),
                view_settings=self._load_app_settings(connection),
            )
            return project
        finally:
            connection.close()

    @staticmethod
    def _save_app_settings(connection: sqlite3.Connection, settings: dict[str, object]) -> None:
        for key, value in settings.items():
            connection.execute(
                "INSERT INTO app_settings (key, value) VALUES (?, ?)",
                (key, json.dumps(value, ensure_ascii=False)),
            )

    @staticmethod
    def _load_app_settings(connection: sqlite3.Connection) -> dict[str, object]:
        rows = connection.execute("SELECT key, value FROM app_settings").fetchall()
        settings: dict[str, object] = {}
        for row in rows:
            try:
                settings[row["key"]] = json.loads(row["value"])
            except json.JSONDecodeError:
                settings[row["key"]] = row["value"]
        return settings
