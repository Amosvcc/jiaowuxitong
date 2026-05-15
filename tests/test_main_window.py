from pathlib import Path

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from app.models import ColumnFilterCriteria, Project
from app.ui.main_window import MainWindow
from app.ui.table_view import DataTableView
from app.ui.widgets import SearchBar


def get_qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_initial_state() -> None:
    app = get_qapp()
    window = MainWindow()

    try:
        assert window.windowTitle() == "数据分析软件 V1.0 - 未命名项目"
        assert window.size().width() == 1200
        assert window.size().height() == 800
        assert isinstance(window.table_view, DataTableView)
        assert window.table_view.model() is window.table_model
        assert window.row_count_label.text() == "行数：10"
        assert window.column_count_label.text() == "列数：5"
        assert window.action_new.isEnabled()
        assert window.action_open.isEnabled()
        assert window.action_import.isEnabled()
        assert window.action_save.isEnabled()
        assert window.action_save_as.isEnabled()
        assert window.action_export.isEnabled()
        assert window.action_data_update.isEnabled()
        assert window.action_undo.text() == "撤销"
        assert not window.action_undo.isEnabled()
        assert window.action_add_row.isEnabled()
        assert window.action_add_column.isEnabled()
        assert window.action_column_settings.isEnabled()
        assert window.action_terminate_row.isEnabled()
        assert window.action_restore_row.isEnabled()
        assert window.action_statistics.isEnabled()
        assert window.action_pivot.isEnabled()
        assert isinstance(window.search_bar, SearchBar)
        assert window.search_bar.search_input.placeholderText() == "搜索..."
        assert not window.search_bar.previous_button.isEnabled()
        assert not window.search_bar.next_button.isEnabled()
        assert window.action_delete.isEnabled()
    finally:
        window.close()
        app.processEvents()


def test_main_window_actions_update_model_and_status() -> None:
    app = get_qapp()
    window = MainWindow()

    try:
        window.action_add_row.trigger()
        window.action_add_column.trigger()
        app.processEvents()

        assert window.table_model.rowCount() == 11
        assert window.table_model.columnCount() == 6
        assert window.row_count_label.text() == "行数：11"
        assert window.column_count_label.text() == "列数：6"
        assert window.windowTitle().endswith("*")
    finally:
        window.table_model.mark_clean()
        window.close()
        app.processEvents()


def test_main_window_adds_row_after_current_selection() -> None:
    app = get_qapp()
    window = MainWindow()
    original_row_ids = [row.id for row in window.table_model.rows]
    window.table_view.setCurrentIndex(window.table_model.index(1, 0))

    try:
        window.action_add_row.trigger()
        app.processEvents()

        assert window.table_model.rowCount() == 11
        assert [row.id for row in window.table_model.rows[:4]] == [
            original_row_ids[0],
            original_row_ids[1],
            11,
            original_row_ids[2],
        ]
        assert window.table_model.project.dirty is True
    finally:
        window.table_model.mark_clean()
        window.close()
        app.processEvents()


def test_main_window_adds_column_after_current_selection() -> None:
    app = get_qapp()
    window = MainWindow()
    original_column_ids = [column.id for column in window.table_model.columns]
    window.table_view.setCurrentIndex(window.table_model.index(0, 1))

    try:
        window.action_add_column.trigger()
        app.processEvents()

        assert window.table_model.columnCount() == 6
        assert [column.id for column in window.table_model.columns[:4]] == [
            original_column_ids[0],
            original_column_ids[1],
            6,
            original_column_ids[2],
        ]
        assert window.table_model.project.dirty is True
    finally:
        window.table_model.mark_clean()
        window.close()
        app.processEvents()


def test_main_window_can_terminate_selected_rows() -> None:
    app = get_qapp()
    window = MainWindow()
    window.table_view.selectRow(1)

    try:
        window._terminate_selected_rows()
        app.processEvents()

        assert window.table_model.rows[1].is_terminated is True
        assert window.table_model.project.dirty is True
    finally:
        window.table_model.mark_clean()
        window.close()
        app.processEvents()


def test_main_window_can_restore_selected_rows() -> None:
    app = get_qapp()
    window = MainWindow()
    window.table_model.rows[1].is_terminated = True
    window.table_model.rows[1].terminated_at = "2026-05-14T10:00:00"
    window.table_view.selectRow(1)

    try:
        window._restore_selected_rows()
        app.processEvents()

        assert window.table_model.rows[1].is_terminated is False
        assert window.table_model.rows[1].terminated_at is None
        assert window.table_model.project.dirty is True
    finally:
        window.table_model.mark_clean()
        window.close()
        app.processEvents()


def test_main_window_can_delete_selected_rows() -> None:
    app = get_qapp()
    window = MainWindow()
    deleted_row_id = window.table_model.rows[1].id
    window.table_view.selectRow(1)

    try:
        window._delete_selected_rows()
        app.processEvents()

        assert window.table_model.rowCount() == 9
        assert all(row.id != deleted_row_id for row in window.table_model.rows)
        assert all(row_id != deleted_row_id for row_id, _column_id in window.table_model.cells)
        assert window.table_model.project.dirty is True
    finally:
        window.table_model.mark_clean()
        window.close()
        app.processEvents()


def test_main_window_undo_restores_deleted_row() -> None:
    app = get_qapp()
    window = MainWindow()
    deleted_row_id = window.table_model.rows[1].id
    window.table_view.selectRow(1)

    try:
        window._delete_selected_rows()
        window._undo_last_operation()
        app.processEvents()

        assert window.table_model.rowCount() == 10
        assert any(row.id == deleted_row_id for row in window.table_model.rows)
        assert window.table_model.project.dirty is False
        assert not window.action_undo.isEnabled()
    finally:
        window.close()
        app.processEvents()


def test_main_window_can_delete_columns_and_clear_filter() -> None:
    app = get_qapp()
    window = MainWindow()
    deleted_column_id = window.source_table_model.column_id_at(0)
    window.table_model.set_column_filter(
        ColumnFilterCriteria(
            column_id=deleted_column_id,
            selected_values={"x"},
        )
    )

    try:
        window._delete_columns([0])
        app.processEvents()

        assert window.table_model.columnCount() == 4
        assert deleted_column_id not in window.table_model.filter_state.filters
        assert all(str(column.id) != deleted_column_id for column in window.table_model.columns)
        assert window.table_model.project.dirty is True
    finally:
        window.table_model.mark_clean()
        window.close()
        app.processEvents()


def test_main_window_undo_restores_deleted_column() -> None:
    app = get_qapp()
    window = MainWindow()
    deleted_column_id = window.source_table_model.column_id_at(0)

    try:
        window._delete_columns([0])
        window._undo_last_operation()
        app.processEvents()

        assert window.table_model.columnCount() == 5
        assert any(str(column.id) == deleted_column_id for column in window.table_model.columns)
        assert window.table_model.project.dirty is False
    finally:
        window.close()
        app.processEvents()


def test_main_window_undo_restores_cell_edit() -> None:
    app = get_qapp()
    window = MainWindow()

    try:
        window.table_model.setData(window.table_model.index(0, 0), "新值")
        window._undo_last_operation()
        app.processEvents()

        assert window.table_model.data(window.table_model.index(0, 0)) == ""
        assert window.table_model.project.dirty is False
    finally:
        window.close()
        app.processEvents()


def test_main_window_undo_restores_added_row() -> None:
    app = get_qapp()
    window = MainWindow()

    try:
        window.action_add_row.trigger()
        window._undo_last_operation()
        app.processEvents()

        assert window.table_model.rowCount() == 10
        assert window.table_model.project.dirty is False
    finally:
        window.close()
        app.processEvents()


def test_main_window_column_settings_uses_first_column_when_no_selection(monkeypatch) -> None:
    app = get_qapp()
    window = MainWindow()
    opened_indices: list[int] = []
    monkeypatch.setattr(window, "_open_column_settings_for_index", lambda index: opened_indices.append(index))

    try:
        window.action_column_settings.trigger()
        app.processEvents()

        assert opened_indices == [0]
    finally:
        window.close()
        app.processEvents()


def test_main_window_column_settings_can_update_column(monkeypatch) -> None:
    app = get_qapp()
    window = MainWindow()

    class FakeDialog:
        DialogCode = type("DialogCode", (), {"Accepted": 1})

        def __init__(self, column, parent=None):
            self.column = column

        def exec(self):
            return self.DialogCode.Accepted

        def get_settings(self):
            return {
                "name": "状态",
                "field_type": "dropdown",
                "dropdown_options": ["进行中", "已完成"],
                "allow_custom_value": False,
            }

        def show_validation_error(self, message: str) -> None:
            raise AssertionError(message)

    monkeypatch.setattr("app.ui.main_window.ColumnSettingsDialog", FakeDialog)

    try:
        window._open_column_settings_for_index(0)
        app.processEvents()

        assert window.table_model.columns[0].name == "状态"
        assert window.table_model.columns[0].field_type == "dropdown"
        assert window.table_model.columns[0].dropdown_options == ["进行中", "已完成"]
        assert window.table_model.columns[0].allow_custom_value is False
        assert window.table_model.project.dirty is True
    finally:
        window.table_model.mark_clean()
        window.close()
        app.processEvents()


def test_main_window_search_updates_matches_and_navigation() -> None:
    app = get_qapp()
    window = MainWindow()
    window.table_model.setData(window.table_model.index(0, 0), "张三")
    window.table_model.setData(window.table_model.index(1, 1), "张三-重复")
    window.table_model.mark_clean()

    try:
        window.search_bar.search_input.setText("张三")
        window._perform_search()
        app.processEvents()

        assert window.table_model.search_matches == [(0, 0), (1, 1)]
        assert window.table_model.current_search_index == 0
        assert window.search_bar.previous_button.isEnabled()
        assert window.search_bar.next_button.isEnabled()
        assert window.search_status_label.text() == "找到 2 个匹配项，当前第 1 个"

        window._go_to_next_match()
        app.processEvents()
        assert window.table_model.current_search_index == 1
        assert window.table_view.currentIndex().row() == 1
        assert window.table_view.currentIndex().column() == 1

        window._go_to_previous_match()
        app.processEvents()
        assert window.table_model.current_search_index == 0
        assert window.table_view.currentIndex().row() == 0
        assert window.table_model.project.dirty is False
    finally:
        window.close()
        app.processEvents()


def test_main_window_clear_search_clears_matches() -> None:
    app = get_qapp()
    window = MainWindow()
    window.table_model.setData(window.table_model.index(0, 0), "搜索词")
    window.table_model.mark_clean()

    try:
        window.search_bar.search_input.setText("搜索")
        window._perform_search()
        app.processEvents()

        window._clear_search()
        app.processEvents()

        assert window.search_bar.keyword() == ""
        assert window.table_model.search_matches == []
        assert not window.search_bar.previous_button.isEnabled()
        assert not window.search_bar.next_button.isEnabled()
        assert window.search_status_label.text() == ""
        assert window.table_model.project.dirty is False
    finally:
        window.close()
        app.processEvents()


def test_main_window_import_failure_keeps_existing_model(monkeypatch, workspace_tmp_path) -> None:
    app = get_qapp()
    window = MainWindow()
    original_project = window.table_model.project
    original_dimensions = (window.table_model.rowCount(), window.table_model.columnCount())
    errors: list[tuple[str, str]] = []

    def fake_open_file_name(*args, **kwargs):
        return str(workspace_tmp_path / "bad.unsupported"), ""

    def fake_critical(parent, title: str, message: str):
        errors.append((title, message))
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QFileDialog, "getOpenFileName", fake_open_file_name)
    monkeypatch.setattr(
        window.import_export_service,
        "import_file",
        lambda path: (_ for _ in ()).throw(ValueError("导入失败测试")),
    )
    monkeypatch.setattr(QMessageBox, "critical", fake_critical)

    try:
        window._import_file()
        app.processEvents()

        assert window.table_model.project is original_project
        assert (window.table_model.rowCount(), window.table_model.columnCount()) == original_dimensions
        assert errors == [("导入失败", "导入失败测试")]
    finally:
        window.close()
        app.processEvents()


def test_main_window_import_success_loads_project_and_marks_dirty(
    monkeypatch, workspace_tmp_path
) -> None:
    app = get_qapp()
    window = MainWindow()
    project = Project.create_empty(row_count=1, column_count=2)
    project.columns[0].name = "姓名"
    project.columns[1].name = "状态"
    project.set_cell_value(1, 1, "张三")
    project.set_cell_value(1, 2, "进行中")
    project.dirty = False

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(workspace_tmp_path / "data.csv"), ""),
    )
    monkeypatch.setattr(window.import_export_service, "import_file", lambda path: project)

    try:
        window._import_file()
        app.processEvents()

        assert window.table_model.project is project
        assert window.table_model.project.dirty is True
        assert window.table_model.rowCount() == 1
        assert window.table_model.columnCount() == 2
        assert window.row_count_label.text() == "行数：1"
        assert window.column_count_label.text() == "列数：2"
    finally:
        window.table_model.mark_clean()
        window.close()
        app.processEvents()


def test_main_window_open_failure_keeps_existing_model(monkeypatch, workspace_tmp_path) -> None:
    app = get_qapp()
    window = MainWindow()
    original_project = window.table_model.project
    errors: list[tuple[str, str]] = []

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(workspace_tmp_path / "broken.dasproj"), ""),
    )
    monkeypatch.setattr(
        window.project_service,
        "open_project",
        lambda path: (_ for _ in ()).throw(ValueError("打开失败测试")),
    )
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda parent, title, message: errors.append((title, message)) or QMessageBox.StandardButton.Ok,
    )

    try:
        window._open_project()
        app.processEvents()

        assert window.table_model.project is original_project
        assert errors == [("打开失败", "打开失败测试")]
    finally:
        window.close()
        app.processEvents()


def test_main_window_statistics_action_opens_dialog(monkeypatch) -> None:
    app = get_qapp()
    window = MainWindow()
    opened = {"count": 0, "project": None}

    class FakeDialog:
        def __init__(self, project, parent=None):
            opened["count"] += 1
            opened["project"] = project

        def exec(self):
            return 0

    monkeypatch.setattr("app.ui.main_window.StatisticsDialog", FakeDialog)

    try:
        window.action_statistics.trigger()
        app.processEvents()

        assert opened["count"] == 1
        assert opened["project"] is window.table_model.project
    finally:
        window.close()
        app.processEvents()


def test_main_window_statistics_does_not_change_dirty(monkeypatch) -> None:
    app = get_qapp()
    window = MainWindow()
    window.table_model.mark_clean()

    class FakeDialog:
        def __init__(self, project, parent=None):
            self.project = project

        def exec(self):
            return 0

    monkeypatch.setattr("app.ui.main_window.StatisticsDialog", FakeDialog)

    try:
        window._open_statistics_dialog()
        app.processEvents()

        assert window.table_model.project.dirty is False
        assert not window.windowTitle().endswith("*")
    finally:
        window.close()
        app.processEvents()


def test_main_window_pivot_action_opens_dialog(monkeypatch) -> None:
    app = get_qapp()
    window = MainWindow()
    opened = {"count": 0, "project": None}

    class FakeDialog:
        def __init__(self, project, parent=None, **kwargs):
            opened["count"] += 1
            opened["project"] = project

        def exec(self):
            return 0

    monkeypatch.setattr("app.ui.main_window.PivotDialog", FakeDialog)

    try:
        window.action_pivot.trigger()
        app.processEvents()

        assert opened["count"] == 1
        assert opened["project"] is window.table_model.project
    finally:
        window.close()
        app.processEvents()


def test_main_window_pivot_does_not_change_dirty(monkeypatch) -> None:
    app = get_qapp()
    window = MainWindow()
    window.table_model.mark_clean()

    class FakeDialog:
        def __init__(self, project, parent=None, **kwargs):
            self.project = project

        def exec(self):
            return 0

    monkeypatch.setattr("app.ui.main_window.PivotDialog", FakeDialog)

    try:
        window._open_pivot_dialog()
        app.processEvents()

        assert window.table_model.project.dirty is False
        assert not window.windowTitle().endswith("*")
    finally:
        window.close()
        app.processEvents()
