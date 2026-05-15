import pytest

from app.models import Project
from app.services.column_service import ColumnService


def test_column_service_updates_column_name_and_type() -> None:
    project = Project.create_empty(row_count=1, column_count=2)

    column = ColumnService().update_column(
        project,
        0,
        name="状态",
        field_type="dropdown",
        dropdown_options=["进行中", "已完成"],
        allow_custom_value=False,
    )

    assert column.name == "状态"
    assert column.field_type == "dropdown"
    assert column.dropdown_options == ["进行中", "已完成"]
    assert column.allow_custom_value is False
    assert project.dirty is True


def test_column_service_rejects_empty_column_name() -> None:
    project = Project.create_empty(row_count=1, column_count=1)

    with pytest.raises(ValueError, match="列名不能为空"):
        ColumnService().update_column(
            project,
            0,
            name="  ",
            field_type="text",
            dropdown_options=[],
            allow_custom_value=True,
        )


def test_column_service_rejects_duplicate_column_name() -> None:
    project = Project.create_empty(row_count=1, column_count=2)
    project.columns[1].name = "状态"

    with pytest.raises(ValueError, match="列名不能重复"):
        ColumnService().update_column(
            project,
            0,
            name="状态",
            field_type="text",
            dropdown_options=[],
            allow_custom_value=True,
        )


def test_column_service_trims_dropdown_options() -> None:
    project = Project.create_empty(row_count=1, column_count=1)

    column = ColumnService().update_column(
        project,
        0,
        name="状态",
        field_type="dropdown",
        dropdown_options=[" 进行中 ", " 已完成 "],
        allow_custom_value=True,
    )

    assert column.dropdown_options == ["进行中", "已完成"]


def test_column_service_rejects_empty_dropdown_option() -> None:
    project = Project.create_empty(row_count=1, column_count=1)

    with pytest.raises(ValueError, match="下拉选项不能为空"):
        ColumnService().update_column(
            project,
            0,
            name="状态",
            field_type="dropdown",
            dropdown_options=["进行中", " "],
            allow_custom_value=True,
        )


def test_column_service_rejects_duplicate_dropdown_options() -> None:
    project = Project.create_empty(row_count=1, column_count=1)

    with pytest.raises(ValueError, match="同一列下拉选项不能重复"):
        ColumnService().update_column(
            project,
            0,
            name="状态",
            field_type="dropdown",
            dropdown_options=["进行中", "进行中"],
            allow_custom_value=True,
        )


def test_column_service_deletes_columns_and_cells() -> None:
    project = Project.create_empty(row_count=2, column_count=3)
    deleted_column_id = project.columns[1].id

    affected_columns = ColumnService().delete_columns(project, [1])

    assert affected_columns == 1
    assert len(project.columns) == 2
    assert all(column.id != deleted_column_id for column in project.columns)
    assert all(column_id != deleted_column_id for _row_id, column_id in project.cells)
    assert [column.order_index for column in project.columns] == [0, 1]
    assert project.dirty is True


def test_column_service_delete_ignores_invalid_indexes() -> None:
    project = Project.create_empty(row_count=1, column_count=1)

    affected_columns = ColumnService().delete_columns(project, [-1, 2])

    assert affected_columns == 0
    assert len(project.columns) == 1
    assert project.dirty is False
