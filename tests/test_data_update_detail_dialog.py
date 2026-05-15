from PySide6.QtWidgets import QApplication

from app.models import DataUpdateAction, DataUpdateDetail, Project
from app.ui.dialogs import DataUpdateDetailDialog


def get_qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def build_details() -> list[DataUpdateDetail]:
    return [
        DataUpdateDetail(
            action=DataUpdateAction.UPDATE_CELL,
            key_value="1001",
            source_row_index=1,
            target_row_index=1,
            column_name="班级",
            old_value="一班",
            new_value="二班",
            message="已更新单元格",
        ),
        DataUpdateDetail(
            action=DataUpdateAction.SKIP_EMPTY,
            key_value="1002",
            source_row_index=2,
            target_row_index=2,
            column_name="班级",
            old_value="一班",
            new_value="",
            message="更新表值为空，已跳过",
        ),
    ]


def test_detail_dialog_can_be_created() -> None:
    app = get_qapp()
    dialog = DataUpdateDetailDialog(build_details())

    try:
        assert dialog.windowTitle() == "更新详情"
    finally:
        dialog.close()
        app.processEvents()


def test_detail_dialog_loads_details() -> None:
    app = get_qapp()
    dialog = DataUpdateDetailDialog(build_details())

    try:
        assert dialog.table_model.rowCount() == 2
        assert dialog.count_label.text() == "详情数量：2"
    finally:
        dialog.close()
        app.processEvents()


def test_detail_dialog_filter_updates_count() -> None:
    app = get_qapp()
    dialog = DataUpdateDetailDialog(build_details())

    try:
        dialog.action_filter_combo.setCurrentText("跳过空值")
        app.processEvents()

        assert dialog.table_model.rowCount() == 1
        assert dialog.count_label.text() == "详情数量：1"
    finally:
        dialog.close()
        app.processEvents()


def test_detail_dialog_close_does_not_change_project_dirty() -> None:
    app = get_qapp()
    project = Project.create_empty(row_count=1, column_count=1)
    project.dirty = False
    dialog = DataUpdateDetailDialog(build_details())

    try:
        dialog.reject()
        app.processEvents()

        assert project.dirty is False
    finally:
        dialog.close()
        app.processEvents()
