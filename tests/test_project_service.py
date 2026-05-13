import pytest

from app.models import Project
from app.services.project_service import ProjectService


def test_project_service_save_project_auto_appends_suffix(workspace_tmp_path) -> None:
    service = ProjectService()
    path_without_suffix = workspace_tmp_path / "demo"
    project = Project.create_empty(row_count=1, column_count=1)
    project.dirty = True

    saved_path = service.save_project(project, str(path_without_suffix))

    assert saved_path.endswith(".dasproj")
    assert project.file_path == saved_path
    assert project.dirty is False


def test_project_service_open_project_restores_saved_project(workspace_tmp_path) -> None:
    service = ProjectService()
    path = workspace_tmp_path / "demo.dasproj"
    project = Project.create_empty(row_count=1, column_count=1)
    project.name = "demo"
    project.set_cell_value(1, 1, "中文内容")
    service.save_project(project, str(path))

    loaded = service.open_project(str(path))

    assert loaded.file_path == str(path)
    assert loaded.name == "demo"
    assert loaded.get_cell_value(1, 1) == "中文内容"
    assert loaded.dirty is False


def test_project_service_open_invalid_file_raises(workspace_tmp_path) -> None:
    service = ProjectService()
    path = workspace_tmp_path / "broken.dasproj"
    path.write_text("not sqlite", encoding="utf-8")

    with pytest.raises(Exception):
        service.open_project(str(path))
