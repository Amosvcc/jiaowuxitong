from PySide6.QtCore import Qt

from app.models import DataUpdateAction, DataUpdateDetail
from app.ui.models import DataUpdateDetailTableModel


def build_details() -> list[DataUpdateDetail]:
    return [
        DataUpdateDetail(
            action=DataUpdateAction.UPDATE_CELL,
            key_value="1001",
            source_row_index=1,
            target_row_index=2,
            column_name="班级",
            old_value="一班",
            new_value="二班",
            message="已更新单元格",
        ),
        DataUpdateDetail(
            action=DataUpdateAction.SKIP_EMPTY,
            key_value="1002",
            source_row_index=None,
            target_row_index=None,
            column_name=None,
            old_value=None,
            new_value=None,
            message=None,
        ),
    ]


def test_detail_table_model_row_count() -> None:
    model = DataUpdateDetailTableModel(build_details())

    assert model.rowCount() == 2


def test_detail_table_model_column_count() -> None:
    model = DataUpdateDetailTableModel(build_details())

    assert model.columnCount() == 8


def test_detail_table_model_displays_fields() -> None:
    model = DataUpdateDetailTableModel(build_details())

    assert model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole) == "更新单元格"
    assert model.data(model.index(0, 1), Qt.ItemDataRole.DisplayRole) == "1001"
    assert model.data(model.index(0, 2), Qt.ItemDataRole.DisplayRole) == "1"
    assert model.data(model.index(0, 3), Qt.ItemDataRole.DisplayRole) == "2"
    assert model.data(model.index(0, 4), Qt.ItemDataRole.DisplayRole) == "班级"
    assert model.data(model.index(0, 5), Qt.ItemDataRole.DisplayRole) == "一班"
    assert model.data(model.index(0, 6), Qt.ItemDataRole.DisplayRole) == "二班"
    assert model.data(model.index(0, 7), Qt.ItemDataRole.DisplayRole) == "已更新单元格"


def test_detail_table_model_none_values_show_empty_string() -> None:
    model = DataUpdateDetailTableModel(build_details())

    assert model.data(model.index(1, 2), Qt.ItemDataRole.DisplayRole) == ""
    assert model.data(model.index(1, 3), Qt.ItemDataRole.DisplayRole) == ""
    assert model.data(model.index(1, 4), Qt.ItemDataRole.DisplayRole) == ""
    assert model.data(model.index(1, 5), Qt.ItemDataRole.DisplayRole) == ""
    assert model.data(model.index(1, 6), Qt.ItemDataRole.DisplayRole) == ""
    assert model.data(model.index(1, 7), Qt.ItemDataRole.DisplayRole) == ""


def test_detail_table_model_headers_are_correct() -> None:
    model = DataUpdateDetailTableModel(build_details())

    assert [
        model.headerData(index, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        for index in range(model.columnCount())
    ] == ["类型", "匹配值", "源表行号", "主表行号", "字段名", "原值", "新值", "说明"]
