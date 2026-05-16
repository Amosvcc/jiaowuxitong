from PySide6.QtWidgets import QApplication, QMessageBox

from app.models import DataUpdateAction, DataUpdateDetail, DataUpdateResult, Project
from app.ui.dialogs import DataUpdateDialog


def get_qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def build_project() -> Project:
    project = Project.create_empty(row_count=2, column_count=2)
    project.columns[0].name = "学号"
    project.columns[1].name = "姓名"
    project.set_cell_value(1, 1, "1001")
    project.set_cell_value(1, 2, "张三")
    project.dirty = False
    return project


class FakeImportExportService:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def read_table(self, path: str) -> tuple[list[str], list[list[str]]]:
        self.calls.append(path)
        return ["学号", "班级"], [["1001", "一班"]]


class FakeDataUpdateService:
    def __init__(self) -> None:
        self.called = False
        self.last_kwargs = None

    def update_project_from_table(self, **kwargs) -> DataUpdateResult:
        self.called = True
        self.last_kwargs = kwargs
        return DataUpdateResult(
            matched_rows=1,
            updated_cells=1,
            details=[
                DataUpdateDetail(
                    action=DataUpdateAction.UPDATE_CELL,
                    key_value="1001",
                    source_row_index=1,
                    target_row_index=1,
                    column_name="班级",
                    old_value="",
                    new_value="一班",
                    message="已更新单元格",
                )
            ],
        )


def test_dialog_can_be_created() -> None:
    app = get_qapp()
    dialog = DataUpdateDialog(build_project())

    try:
        assert dialog.windowTitle() == "数据更新"
        assert dialog.result is None
    finally:
        dialog.close()
        app.processEvents()


def test_dialog_loads_target_columns() -> None:
    app = get_qapp()
    dialog = DataUpdateDialog(build_project())

    try:
        assert dialog.target_key_combo.count() == 2
        assert [dialog.target_key_combo.itemText(i) for i in range(dialog.target_key_combo.count())] == [
            "学号",
            "姓名",
        ]
    finally:
        dialog.close()
        app.processEvents()


def test_dialog_shows_default_options() -> None:
    app = get_qapp()
    dialog = DataUpdateDialog(build_project())

    try:
        assert dialog.overwrite_existing_checkbox.isChecked() is False
        assert dialog.ignore_empty_values_checkbox.isChecked() is True
        assert dialog.add_missing_columns_checkbox.isChecked() is True
        assert dialog.append_unmatched_rows_checkbox.isChecked() is True
        assert dialog.update_terminated_rows_checkbox.isChecked() is False
    finally:
        dialog.close()
        app.processEvents()


def test_dialog_cannot_execute_without_match_fields(monkeypatch) -> None:
    app = get_qapp()
    fake_service = FakeDataUpdateService()
    warnings: list[tuple[str, str]] = []
    dialog = DataUpdateDialog(
        build_project(),
        import_export_service=FakeImportExportService(),
        data_update_service=fake_service,
    )
    dialog.source_columns = []
    dialog.source_rows = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda parent, title, message: warnings.append((title, message)) or QMessageBox.StandardButton.Ok,
    )

    try:
        dialog.execute_update()
        app.processEvents()

        assert fake_service.called is False
        assert warnings == [("数据更新", "请选择主表和更新表匹配字段。")]
    finally:
        dialog.close()
        app.processEvents()


def test_dialog_can_load_file_and_call_service(monkeypatch, workspace_tmp_path) -> None:
    app = get_qapp()
    fake_import = FakeImportExportService()
    fake_service = FakeDataUpdateService()
    infos: list[tuple[str, str]] = []
    dialog = DataUpdateDialog(
        build_project(),
        import_export_service=fake_import,
        data_update_service=fake_service,
    )

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda parent, title, message: infos.append((title, message)) or QMessageBox.StandardButton.Ok,
    )

    try:
        dialog.load_source_file(str(workspace_tmp_path / "update.csv"))
        dialog.target_key_combo.setCurrentText("学号")
        dialog.source_key_combo.setCurrentText("学号")
        dialog.execute_update()
        app.processEvents()

        assert fake_import.calls
        assert fake_service.called is True
        assert fake_service.last_kwargs["target_key_column"] == "学号"
        assert fake_service.last_kwargs["source_key_column"] == "学号"
        assert dialog.result is not None
        assert dialog.view_details_button.isEnabled() is True
        assert infos and infos[0][0] == "数据更新完成"
    finally:
        dialog.close()
        app.processEvents()


def test_dialog_cancel_does_not_change_project_dirty() -> None:
    app = get_qapp()
    project = build_project()
    dialog = DataUpdateDialog(project)

    try:
        dialog.reject()
        app.processEvents()

        assert project.dirty is False
        assert dialog.result is None
    finally:
        dialog.close()
        app.processEvents()
