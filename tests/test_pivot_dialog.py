from pathlib import Path

from PySide6.QtWidgets import QApplication, QFileDialog

from app.models import PivotResult, Project
from app.ui.dialogs import PivotDialog


def get_qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def build_project() -> Project:
    project = Project.create_empty(row_count=2, column_count=3)
    project.columns[0].name = "姓名"
    project.columns[1].name = "班级"
    project.columns[2].name = "性别"
    project.set_cell_value(1, 1, "张三")
    project.set_cell_value(1, 2, "一班")
    project.set_cell_value(1, 3, "男")
    project.set_cell_value(2, 1, "李四")
    project.set_cell_value(2, 2, "一班")
    project.set_cell_value(2, 3, "女")
    project.dirty = False
    return project


def build_result() -> PivotResult:
    return PivotResult(
        row_field="班级",
        column_field="性别",
        row_headers=["一班"],
        column_headers=["男", "女"],
        matrix={"一班": {"男": 1, "女": 1}},
        row_totals={"一班": 2},
        column_totals={"男": 1, "女": 1},
        grand_total=2,
        show_row_totals=True,
        show_column_totals=True,
    )


def test_pivot_dialog_can_be_created() -> None:
    app = get_qapp()
    dialog = PivotDialog(build_project())

    try:
        assert dialog.windowTitle() == "数据透视 / 交叉统计"
        assert dialog.result_table.model() is dialog.result_model
    finally:
        dialog.close()
        app.processEvents()


def test_pivot_dialog_loads_project_fields() -> None:
    app = get_qapp()
    dialog = PivotDialog(build_project())

    try:
        assert [dialog.row_field_combo.itemText(index) for index in range(dialog.row_field_combo.count())] == [
            "",
            "姓名",
            "班级",
            "性别",
        ]
        assert [dialog.column_field_combo.itemText(index) for index in range(dialog.column_field_combo.count())] == [
            "",
            "姓名",
            "班级",
            "性别",
        ]
    finally:
        dialog.close()
        app.processEvents()


def test_pivot_dialog_has_correct_default_options() -> None:
    app = get_qapp()
    dialog = PivotDialog(build_project())

    try:
        assert dialog.expand_tags_checkbox.isChecked() is False
        assert dialog.tag_separators_input.isEnabled() is False
        assert dialog.ignore_empty_row_checkbox.isChecked() is True
        assert dialog.ignore_empty_column_checkbox.isChecked() is True
        assert dialog.include_terminated_rows_checkbox.isChecked() is True
        assert dialog.show_row_totals_checkbox.isChecked() is True
        assert dialog.show_column_totals_checkbox.isChecked() is True
        assert dialog.generate_button.isEnabled() is False
        assert dialog.export_button.isEnabled() is False
    finally:
        dialog.close()
        app.processEvents()


def test_pivot_dialog_cannot_generate_without_selected_fields() -> None:
    app = get_qapp()
    dialog = PivotDialog(build_project())

    try:
        assert dialog.can_generate() is False
        assert dialog.generate_button.isEnabled() is False
    finally:
        dialog.close()
        app.processEvents()


def test_pivot_dialog_generate_calls_pivot_service() -> None:
    app = get_qapp()
    project = build_project()
    called = {}

    class FakePivotService:
        def build_pivot(self, *args, **kwargs):
            called["args"] = args
            called["kwargs"] = kwargs
            return build_result()

    dialog = PivotDialog(project, pivot_service=FakePivotService())
    dialog.row_field_combo.setCurrentText("班级")
    dialog.column_field_combo.setCurrentText("性别")

    try:
        dialog.generate_pivot()
        app.processEvents()

        assert called["args"][0] is project
        assert called["kwargs"]["row_field"] == "班级"
        assert called["kwargs"]["column_field"] == "性别"
    finally:
        dialog.close()
        app.processEvents()


def test_pivot_dialog_passes_expand_tag_options_to_pivot_service() -> None:
    app = get_qapp()
    called = {}

    class FakePivotService:
        def build_pivot(self, *args, **kwargs):
            called["kwargs"] = kwargs
            return build_result()

    dialog = PivotDialog(build_project(), pivot_service=FakePivotService())
    dialog.row_field_combo.setCurrentText("班级")
    dialog.column_field_combo.setCurrentText("性别")
    dialog.expand_tags_checkbox.setChecked(True)
    dialog.tag_separators_input.setText(";|\\n")

    try:
        dialog.generate_pivot()
        app.processEvents()

        assert dialog.tag_separators_input.isEnabled() is True
        assert called["kwargs"]["expand_column_tags"] is True
        assert called["kwargs"]["tag_separators"] == [";", "|", "\n"]
    finally:
        dialog.close()
        app.processEvents()


def test_pivot_dialog_shows_result_in_table_view() -> None:
    app = get_qapp()
    dialog = PivotDialog(build_project())
    dialog.row_field_combo.setCurrentText("班级")
    dialog.column_field_combo.setCurrentText("性别")

    try:
        dialog.generate_pivot()
        app.processEvents()

        assert dialog.result_model.rowCount() == 2
        assert dialog.result_model.columnCount() == 4
        assert dialog.result_model.data(dialog.result_model.index(0, 0)) == "一班"
    finally:
        dialog.close()
        app.processEvents()


def test_pivot_dialog_export_is_disabled_before_generate() -> None:
    app = get_qapp()
    dialog = PivotDialog(build_project())

    try:
        assert dialog.export_button.isEnabled() is False
    finally:
        dialog.close()
        app.processEvents()


def test_pivot_dialog_export_is_enabled_after_generate() -> None:
    app = get_qapp()
    dialog = PivotDialog(build_project())
    dialog.row_field_combo.setCurrentText("班级")
    dialog.column_field_combo.setCurrentText("性别")

    try:
        dialog.generate_pivot()
        app.processEvents()

        assert dialog.export_button.isEnabled() is True
    finally:
        dialog.close()
        app.processEvents()


def test_pivot_dialog_close_does_not_change_dirty_state() -> None:
    app = get_qapp()
    project = build_project()
    dialog = PivotDialog(project)

    try:
        dialog.close()
        app.processEvents()

        assert project.dirty is False
    finally:
        app.processEvents()


def test_pivot_dialog_can_export_after_generate(monkeypatch, workspace_tmp_path) -> None:
    app = get_qapp()
    exported = {}

    class FakeImportExportService:
        def export_pivot_result(self, result, path: str) -> None:
            exported["result"] = result
            exported["path"] = path

    dialog = PivotDialog(
        build_project(),
        import_export_service=FakeImportExportService(),
    )
    dialog.row_field_combo.setCurrentText("班级")
    dialog.column_field_combo.setCurrentText("性别")
    export_path = workspace_tmp_path / "pivot.csv"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(export_path), ""))

    try:
        dialog.generate_pivot()
        dialog.export_pivot()
        app.processEvents()

        assert exported["result"] is dialog.current_result
        assert exported["path"] == str(export_path)
        assert dialog.status_label.text() == f"已导出数据透视结果：{Path(export_path).name}"
    finally:
        dialog.close()
        app.processEvents()
