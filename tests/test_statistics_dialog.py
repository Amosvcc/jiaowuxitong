import pandas as pd
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from app.models import Project
from app.ui.dialogs import StatisticsDialog


def get_qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def build_project() -> Project:
    project = Project.create_empty(row_count=4, column_count=2)
    project.columns[0].name = "状态"
    project.columns[1].name = "负责人"
    project.set_cell_value(1, 1, "已完成")
    project.set_cell_value(2, 1, "进行中")
    project.set_cell_value(3, 1, "已完成")
    project.set_cell_value(4, 1, "")
    project.dirty = False
    return project


def test_statistics_dialog_column_combo_contains_all_columns() -> None:
    app = get_qapp()
    dialog = StatisticsDialog(build_project())

    try:
        assert dialog.column_combo.count() == 2
        assert [dialog.column_combo.itemText(index) for index in range(dialog.column_combo.count())] == [
            "状态",
            "负责人",
        ]
        assert dialog.include_terminated_checkbox.isChecked() is True
        assert dialog.ignore_empty_checkbox.isChecked() is True
    finally:
        dialog.close()
        app.processEvents()


def test_statistics_dialog_generate_populates_result_table() -> None:
    app = get_qapp()
    dialog = StatisticsDialog(build_project())

    try:
        dialog.generate_statistics()
        app.processEvents()

        assert dialog.result_table.rowCount() == 2
        assert dialog.result_table.item(0, 0).text() == "已完成"
        assert dialog.result_table.item(0, 1).text() == "2"
        assert dialog.result_table.item(0, 2).text() == "66.67%"
        assert dialog.status_label.text() == "共 2 条统计结果"
    finally:
        dialog.close()
        app.processEvents()


def test_statistics_dialog_empty_result_shows_message() -> None:
    app = get_qapp()
    project = Project.create_empty(row_count=2, column_count=1)
    dialog = StatisticsDialog(project)

    try:
        dialog.generate_statistics()
        app.processEvents()

        assert dialog.result_table.rowCount() == 0
        assert dialog.status_label.text() == "无统计结果"
    finally:
        dialog.close()
        app.processEvents()


def test_statistics_dialog_export_without_generate_warns(monkeypatch) -> None:
    app = get_qapp()
    dialog = StatisticsDialog(build_project())
    warnings: list[tuple[str, str]] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda parent, title, message: warnings.append((title, message)) or QMessageBox.StandardButton.Ok,
    )

    try:
        dialog.export_statistics()
        app.processEvents()

        assert warnings == [("导出统计结果", "请先生成统计结果")]
    finally:
        dialog.close()
        app.processEvents()


def test_statistics_dialog_can_export_csv(monkeypatch, workspace_tmp_path) -> None:
    app = get_qapp()
    dialog = StatisticsDialog(build_project())
    export_path = workspace_tmp_path / "统计导出.csv"

    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(export_path), ""))

    try:
        dialog.generate_statistics()
        dialog.export_statistics()
        app.processEvents()

        exported = pd.read_csv(export_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        assert exported["字段值"].tolist() == ["已完成", "进行中"]
        assert exported["占比"].tolist() == ["66.67%", "33.33%"]
        assert dialog.status_label.text() == f"已导出统计结果：{export_path.name}"
    finally:
        dialog.close()
        app.processEvents()


def test_statistics_dialog_can_export_excel(monkeypatch, workspace_tmp_path) -> None:
    app = get_qapp()
    dialog = StatisticsDialog(build_project())
    export_path = workspace_tmp_path / "统计导出.xlsx"

    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(export_path), ""))

    try:
        dialog.generate_statistics()
        dialog.export_statistics()
        app.processEvents()

        exported = pd.read_excel(export_path, dtype=str, keep_default_na=False)
        assert exported["字段值"].tolist() == ["已完成", "进行中"]
        assert exported["占比"].tolist() == ["66.67%", "33.33%"]
    finally:
        dialog.close()
        app.processEvents()
