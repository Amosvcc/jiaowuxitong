import pandas as pd

from app.models import Cell, Column, Project, Row


def test_column_row_and_cell_defaults() -> None:
    column = Column(id=1, name="字段1")
    row = Row(id=2, order_index=1)
    cell = Cell(row_id=2, column_id=1, value="内容")

    assert column.field_type == "text"
    assert column.order_index == 0
    assert column.dropdown_options == []
    assert column.allow_custom_value is True
    assert row.is_terminated is False
    assert row.terminated_at is None
    assert cell.value == "内容"


def test_project_create_empty_builds_expected_structure() -> None:
    project = Project.create_empty(row_count=2, column_count=3)

    assert project.name == "未命名项目"
    assert project.dirty is False
    assert len(project.columns) == 3
    assert len(project.rows) == 2
    assert len(project.cells) == 6
    assert project.get_cell_value(1, 1) == ""
    assert project.columns[0].name == "字段1"
    assert project.columns[0].order_index == 0
    assert project.rows[1].order_index == 1


def test_project_set_cell_and_append_entities() -> None:
    project = Project.create_empty(row_count=1, column_count=1)

    project.set_cell_value(1, 1, "更新后")
    new_row = project.append_row()
    new_column = project.append_column()

    assert project.get_cell_value(1, 1) == "更新后"
    assert new_row.id == 2
    assert new_row.order_index == 1
    assert new_column.id == 2
    assert new_column.name == "字段2"
    assert new_column.order_index == 1
    assert project.get_cell_value(new_row.id, 1) == ""
    assert project.get_cell_value(1, new_column.id) == ""


def test_project_from_dataframe_normalizes_headers_and_cells() -> None:
    dataframe = pd.DataFrame([["张三", None, "进行中"]], columns=["姓名", "", "姓名"])

    project = Project.from_dataframe(dataframe)

    assert [column.name for column in project.columns] == ["姓名", "字段2", "姓名_2"]
    assert project.columns[0].field_type == "text"
    assert project.rows[0].is_terminated is False
    assert project.get_cell_value(1, 2) == ""


def test_project_to_dataframe_keeps_column_and_row_order() -> None:
    project = Project.create_empty(row_count=2, column_count=2)
    project.columns[0].name = "姓名"
    project.columns[1].name = "状态"
    project.set_cell_value(1, 1, "张三")
    project.set_cell_value(1, 2, "进行中")
    project.set_cell_value(2, 1, "李四")
    project.set_cell_value(2, 2, "已完成")

    dataframe = project.to_dataframe()

    assert dataframe.columns.tolist() == ["姓名", "状态"]
    assert dataframe.values.tolist() == [["张三", "进行中"], ["李四", "已完成"]]
