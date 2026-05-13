from app.models import Project
from app.services.search_service import SearchService


def test_search_service_finds_exact_match() -> None:
    project = Project.create_empty(row_count=2, column_count=2)
    project.set_cell_value(1, 1, "张三")
    project.set_cell_value(2, 2, "已完成")

    matches = SearchService().search(project, "张三")

    assert matches == [(0, 0)]


def test_search_service_finds_partial_match() -> None:
    project = Project.create_empty(row_count=1, column_count=2)
    project.set_cell_value(1, 2, "进行中")

    matches = SearchService().search(project, "进行")

    assert matches == [(0, 1)]


def test_search_service_is_case_insensitive() -> None:
    project = Project.create_empty(row_count=1, column_count=1)
    project.set_cell_value(1, 1, "Hello World")

    matches = SearchService().search(project, "hello")

    assert matches == [(0, 0)]


def test_search_service_returns_empty_for_blank_keyword() -> None:
    project = Project.create_empty(row_count=1, column_count=1)
    project.set_cell_value(1, 1, "张三")

    assert SearchService().search(project, "") == []
    assert SearchService().search(project, "   ") == []


def test_search_service_includes_terminated_rows() -> None:
    project = Project.create_empty(row_count=2, column_count=1)
    project.rows[1].is_terminated = True
    project.set_cell_value(2, 1, "归档")

    matches = SearchService().search(project, "归")

    assert matches == [(1, 0)]


def test_search_service_respects_row_and_column_order() -> None:
    project = Project.create_empty(row_count=2, column_count=2)
    project.set_cell_value(1, 2, "状态")
    project.set_cell_value(2, 1, "状态")
    project.set_cell_value(2, 2, "状态")

    matches = SearchService().search(project, "状态")

    assert matches == [(0, 1), (1, 0), (1, 1)]


def test_search_service_does_not_modify_dirty_state() -> None:
    project = Project.create_empty(row_count=1, column_count=1)
    project.dirty = True
    project.set_cell_value(1, 1, "张三")
    project.dirty = False

    SearchService().search(project, "张")

    assert project.dirty is False
