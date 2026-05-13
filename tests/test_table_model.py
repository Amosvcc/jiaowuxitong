from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush

from app.models import Project
from app.ui.table_model import DataTableModel


def test_table_model_has_default_grid() -> None:
    model = DataTableModel()

    assert model.rowCount() == 10
    assert model.columnCount() == 5
    assert model.project.dirty is False
    assert [model.headerData(index, Qt.Orientation.Horizontal) for index in range(5)] == [
        "字段1",
        "字段2",
        "字段3",
        "字段4",
        "字段5",
    ]


def test_table_model_returns_empty_string_for_default_cells() -> None:
    model = DataTableModel()
    index = model.index(0, 0)

    assert model.data(index, Qt.ItemDataRole.DisplayRole) == ""


def test_table_model_overwrites_existing_cell_value_and_marks_dirty() -> None:
    model = DataTableModel()
    index = model.index(2, 3)

    assert model.setData(index, "测试值")
    assert model.data(index, Qt.ItemDataRole.DisplayRole) == "测试值"
    assert model.project.dirty is True

    row_id = model.rows[2].id
    column_id = model.columns[3].id
    assert model.cells[(row_id, column_id)].value == "测试值"


def test_table_model_adds_empty_row_and_marks_dirty() -> None:
    model = DataTableModel()

    model.add_empty_row()

    assert model.rowCount() == 11
    assert model.project.dirty is True
    new_row = model.rows[-1]
    assert new_row.order_index == 10
    assert new_row.is_terminated is False
    assert [model.cells[(new_row.id, column.id)].value for column in model.columns] == [
        "",
        "",
        "",
        "",
        "",
    ]


def test_table_model_adds_empty_column_and_marks_dirty() -> None:
    model = DataTableModel()

    model.add_empty_column()

    assert model.columnCount() == 6
    assert model.project.dirty is True
    new_column = model.columns[-1]
    assert new_column.name == "字段6"
    assert new_column.field_type == "text"
    assert all(model.cells[(row.id, new_column.id)].value == "" for row in model.rows)


def test_table_model_does_not_create_cell_for_terminated_row_when_adding_column() -> None:
    project = Project.create_empty(row_count=2, column_count=1)
    project.rows[1].is_terminated = True
    model = DataTableModel(project)

    model.add_empty_column()

    new_column = model.columns[-1]
    assert (project.rows[0].id, new_column.id) in model.cells
    assert (project.rows[1].id, new_column.id) not in model.cells
    assert model.data(model.index(1, 1), Qt.ItemDataRole.DisplayRole) == ""


def test_table_model_can_load_project() -> None:
    project = Project.create_empty(row_count=1, column_count=2)
    project.columns[0].name = "姓名"
    project.set_cell_value(1, 1, "张三")
    model = DataTableModel()

    model.load_project(project)

    assert model.rowCount() == 1
    assert model.columnCount() == 2
    assert model.headerData(0, Qt.Orientation.Horizontal) == "姓名"
    assert model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole) == "张三"


def test_table_model_mark_clean_clears_dirty() -> None:
    model = DataTableModel()
    model.add_empty_row()

    model.mark_clean()

    assert model.project.dirty is False


def test_table_model_can_store_search_matches_and_highlight() -> None:
    model = DataTableModel()
    model.set_search_matches([(0, 0), (1, 1)], 0)

    assert model.search_matches == [(0, 0), (1, 1)]
    assert model.current_search_index == 0
    assert isinstance(model.data(model.index(0, 0), Qt.ItemDataRole.BackgroundRole), QBrush)
    assert isinstance(model.data(model.index(1, 1), Qt.ItemDataRole.BackgroundRole), QBrush)


def test_table_model_clear_search_removes_matches() -> None:
    model = DataTableModel()
    model.set_search_matches([(0, 0)], 0)

    model.clear_search()

    assert model.search_matches == []
    assert model.current_search_index == -1
    assert model.data(model.index(0, 0), Qt.ItemDataRole.BackgroundRole) is None


def test_table_model_refresh_column_updates_header() -> None:
    project = Project.create_empty(row_count=1, column_count=1)
    model = DataTableModel(project)
    project.columns[0].name = "新列名"

    model.refresh_column(0)

    assert model.headerData(0, Qt.Orientation.Horizontal) == "新列名"


def test_table_model_terminated_row_is_not_editable() -> None:
    project = Project.create_empty(row_count=1, column_count=1)
    project.rows[0].is_terminated = True
    model = DataTableModel(project)

    flags = model.flags(model.index(0, 0))

    assert not bool(flags & Qt.ItemFlag.ItemIsEditable)


def test_table_model_terminated_row_rejects_set_data() -> None:
    project = Project.create_empty(row_count=1, column_count=1)
    project.rows[0].is_terminated = True
    model = DataTableModel(project)

    assert model.setData(model.index(0, 0), "新值") is False
    assert model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole) == ""


def test_table_model_terminated_row_has_background() -> None:
    project = Project.create_empty(row_count=1, column_count=1)
    project.rows[0].is_terminated = True
    model = DataTableModel(project)

    assert isinstance(model.data(model.index(0, 0), Qt.ItemDataRole.BackgroundRole), QBrush)


def test_table_model_search_highlight_has_priority_over_terminated_background() -> None:
    project = Project.create_empty(row_count=1, column_count=1)
    project.rows[0].is_terminated = True
    model = DataTableModel(project)
    model.set_search_matches([(0, 0)], 0)

    brush = model.data(model.index(0, 0), Qt.ItemDataRole.BackgroundRole)

    assert isinstance(brush, QBrush)
    assert brush.color().name().lower() == "#ffcc80"


def test_table_model_vertical_header_marks_terminated_row() -> None:
    project = Project.create_empty(row_count=2, column_count=1)
    project.rows[1].is_terminated = True
    model = DataTableModel(project)

    assert model.headerData(0, Qt.Orientation.Vertical) == "1"
    assert model.headerData(1, Qt.Orientation.Vertical) == "[终止] 2"
