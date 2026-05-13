from app.models import Project
from app.repositories.project_repository import ProjectRepository


def test_project_repository_saves_and_loads_empty_project(workspace_tmp_path) -> None:
    path = workspace_tmp_path / "empty.dasproj"
    repository = ProjectRepository()
    project = Project.create_empty(row_count=1, column_count=1)

    repository.save(str(path), project)
    loaded = repository.load(str(path))

    assert loaded.name == "未命名项目"
    assert len(loaded.columns) == 1
    assert len(loaded.rows) == 1
    assert loaded.get_cell_value(1, 1) == ""


def test_project_repository_saves_and_loads_full_project_data(workspace_tmp_path) -> None:
    path = workspace_tmp_path / "full.dasproj"
    repository = ProjectRepository()
    project = Project.create_empty(row_count=2, column_count=2)
    project.name = "中文项目"
    project.columns[0].name = "姓名"
    project.columns[0].field_type = "dropdown"
    project.columns[0].dropdown_options = ["张三", "李四"]
    project.columns[0].allow_custom_value = False
    project.columns[1].name = "状态"
    project.rows[1].is_terminated = True
    project.rows[1].terminated_at = "2026-05-13T10:00:00"
    project.set_cell_value(1, 1, "张三")
    project.set_cell_value(1, 2, "进行中")
    project.set_cell_value(2, 1, "李四")
    project.set_cell_value(2, 2, "已完成")

    repository.save(str(path), project)
    loaded = repository.load(str(path))

    assert loaded.name == "中文项目"
    assert [column.name for column in loaded.columns] == ["姓名", "状态"]
    assert loaded.columns[0].field_type == "dropdown"
    assert loaded.columns[0].dropdown_options == ["张三", "李四"]
    assert loaded.columns[0].allow_custom_value is False
    assert loaded.rows[1].is_terminated is True
    assert loaded.rows[1].terminated_at == "2026-05-13T10:00:00"
    assert loaded.get_cell_value(1, 1) == "张三"
    assert loaded.get_cell_value(2, 2) == "已完成"
