from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.models import Project
from app.repositories import ProjectRepository


class ProjectService:
    def __init__(self, project_repository: ProjectRepository | None = None) -> None:
        self.project_repository = project_repository or ProjectRepository()

    def create_project(self) -> Project:
        return Project.create_empty()

    def save_project(self, project: Project, path: str | None = None) -> str:
        target_path = self._normalize_project_path(path or project.file_path)
        if target_path is None:
            raise ValueError("保存项目时必须提供路径")

        original_name = project.name
        original_file_path = project.file_path
        original_dirty = project.dirty
        original_updated_at = project.updated_at
        project_name = project.name if project.name and project.name != "未命名项目" else Path(target_path).stem
        updated_at = datetime.now().isoformat(timespec="seconds")

        project.name = project_name
        project.file_path = target_path
        project.updated_at = updated_at
        try:
            self.project_repository.save(target_path, project)
        except Exception:
            project.name = original_name
            project.file_path = original_file_path
            project.updated_at = original_updated_at
            project.dirty = original_dirty
            raise

        project.dirty = False
        return target_path

    def open_project(self, path: str) -> Project:
        target_path = self._normalize_project_path(path)
        if target_path is None:
            raise ValueError("打开项目时必须提供路径")

        project = self.project_repository.load(target_path)
        project.file_path = target_path
        project.dirty = False
        return project

    @staticmethod
    def _normalize_project_path(path: str | None) -> str | None:
        if not path:
            return None
        return path if path.lower().endswith(".dasproj") else f"{path}.dasproj"
