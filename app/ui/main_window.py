from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QComboBox,
    QSizePolicy,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.services import (
    ColumnService,
    DataUpdateService,
    FilterService,
    ImportExportService,
    PivotService,
    ProjectService,
    RowService,
    SearchService,
    UndoService,
)
from app.ui.delegates import DataColumnDelegate
from app.ui.dialogs import (
    ColumnFilterDialog,
    ColumnSettingsDialog,
    DataUpdateDialog,
    PivotDialog,
    StatisticsDialog,
)
from app.ui.models import TableFilterProxyModel
from app.ui.table_model import DataTableModel
from app.ui.table_view import DataTableView
from app.ui.widgets import SearchBar


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.import_export_service = ImportExportService()
        self.data_update_service = DataUpdateService()
        self.project_service = ProjectService()
        self.search_service = SearchService()
        self.column_service = ColumnService()
        self.row_service = RowService()
        self.pivot_service = PivotService()
        self.filter_service = FilterService()
        self.undo_service = UndoService()
        self.source_table_model = DataTableModel()
        self.source_table_model.before_project_change = self._push_undo_snapshot
        self.table_model = TableFilterProxyModel(filter_service=self.filter_service)
        self.table_model.setSourceModel(self.source_table_model)
        self.table_view = DataTableView(self)
        self.table_view.setModel(self.table_model)
        self.column_delegate = DataColumnDelegate(self.table_view)
        self.table_view.setItemDelegate(self.column_delegate)

        self.row_count_label = QLabel()
        self.column_count_label = QLabel()
        self.current_cell_label = QLabel()
        self.filter_status_label = QLabel()
        self.search_status_label = QLabel()

        self.resize(1200, 800)
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_status_bar()
        self._connect_signals()
        self._update_status_labels()
        self._update_window_title()

    def _setup_ui(self) -> None:
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table_view)
        self.setCentralWidget(central_widget)

    def _setup_menu_bar(self) -> None:
        self.file_menu = self.menuBar().addMenu("文件")
        self.edit_menu = self.menuBar().addMenu("编辑")
        self.menuBar().addMenu("帮助")

        self.action_new = self._create_action("新建")
        self.action_open = self._create_action("打开")
        self.action_import = self._create_action("导入")
        self.action_save = self._create_action("保存")
        self.action_save_as = self._create_action("另存为")
        self.action_export = self._create_action("导出")
        self.action_data_update = self._create_action("数据更新")
        self.action_undo = self._create_action("撤销", enabled=False)
        self.action_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.action_column_settings = self._create_action("列设置")
        self.action_terminate_row = self._create_action("终止行")
        self.action_restore_row = self._create_action("恢复行")
        self.action_statistics = self._create_action("统计")
        self.action_pivot = self._create_action("数据透视")
        self.action_clear_all_filters = self._create_action("清除全部筛选")

        for action in (
            self.action_new,
            self.action_open,
            self.action_import,
            self.action_save,
            self.action_save_as,
            self.action_export,
            self.action_data_update,
        ):
            self.file_menu.addAction(action)

        self.edit_menu.addAction(self.action_column_settings)
        self.edit_menu.addAction(self.action_undo)
        self.edit_menu.addAction(self.action_terminate_row)
        self.edit_menu.addAction(self.action_restore_row)
        self.edit_menu.addAction(self.action_clear_all_filters)
        self.edit_menu.addAction(self.action_statistics)
        self.edit_menu.addAction(self.action_pivot)

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("主工具栏", self)
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        self.action_add_row = self._create_action("新增行")
        self.action_add_column = self._create_action("新增列")
        self.action_delete = self._create_action("删除")
        self.search_bar = SearchBar(self)
        self.row_status_filter_combo = QComboBox(self)
        self.row_status_filter_combo.addItem("全部行", "all")
        self.row_status_filter_combo.addItem("已终止", "terminated")
        self.row_status_filter_combo.addItem("未终止", "active")
        self.row_status_filter_combo.setToolTip("按行终止状态筛选")
        self.row_status_filter_combo.setMinimumWidth(110)

        toolbar.addWidget(QLabel("行状态", self))
        toolbar.addWidget(self.row_status_filter_combo)
        toolbar.addSeparator()

        for action in (
            self.action_new,
            self.action_open,
            self.action_import,
            self.action_save,
            self.action_export,
            self.action_data_update,
        ):
            toolbar.addAction(action)

        toolbar.addSeparator()
        toolbar.addAction(self.action_add_row)
        toolbar.addAction(self.action_add_column)
        toolbar.addAction(self.action_delete)
        toolbar.addAction(self.action_undo)

        toolbar.addSeparator()
        toolbar.addAction(self.action_terminate_row)
        toolbar.addAction(self.action_restore_row)

        toolbar.addSeparator()
        toolbar.addAction(self.action_column_settings)
        toolbar.addAction(self.action_clear_all_filters)
        toolbar.addAction(self.action_statistics)
        toolbar.addAction(self.action_pivot)

        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        toolbar.addWidget(self.search_bar)

    def _setup_status_bar(self) -> None:
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        status_bar.addPermanentWidget(self.row_count_label)
        status_bar.addPermanentWidget(self.column_count_label)
        status_bar.addPermanentWidget(self.current_cell_label, 1)
        status_bar.addPermanentWidget(self.filter_status_label)
        status_bar.addPermanentWidget(self.search_status_label)

    def _connect_signals(self) -> None:
        self.action_new.triggered.connect(self._new_project)
        self.action_open.triggered.connect(self._open_project)
        self.action_import.triggered.connect(self._import_file)
        self.action_save.triggered.connect(self._save_project)
        self.action_save_as.triggered.connect(self._save_project_as)
        self.action_export.triggered.connect(self._export_file)
        self.action_data_update.triggered.connect(self._open_data_update_dialog)
        self.action_undo.triggered.connect(self._undo_last_operation)
        self.action_add_row.triggered.connect(self._add_row_after_selection)
        self.action_add_column.triggered.connect(self._add_column_after_selection)
        self.action_add_row.triggered.connect(self._update_status_labels)
        self.action_add_column.triggered.connect(self._update_status_labels)
        self.action_delete.triggered.connect(self._delete_selected_items)
        self.action_column_settings.triggered.connect(self._open_selected_column_settings)
        self.action_terminate_row.triggered.connect(self._terminate_selected_rows)
        self.action_restore_row.triggered.connect(self._restore_selected_rows)
        self.action_clear_all_filters.triggered.connect(self._clear_all_filters)
        self.action_statistics.triggered.connect(self._open_statistics_dialog)
        self.action_pivot.triggered.connect(self._open_pivot_dialog)
        self.source_table_model.dirty_changed.connect(self._on_dirty_changed)
        self.table_view.selectionModel().currentChanged.connect(self._on_current_changed)
        self.table_view.horizontalHeader().customContextMenuRequested.connect(
            self._show_column_header_menu
        )
        self.table_view.verticalHeader().customContextMenuRequested.connect(
            self._show_row_header_menu
        )
        self.search_bar.search_requested.connect(self._perform_search)
        self.search_bar.previous_requested.connect(self._go_to_previous_match)
        self.search_bar.next_requested.connect(self._go_to_next_match)
        self.search_bar.clear_requested.connect(self._clear_search)
        self.row_status_filter_combo.currentIndexChanged.connect(self._set_row_status_filter)

    def _create_action(self, text: str, *, enabled: bool = True, checkable: bool = False) -> QAction:
        action = QAction(text, self)
        action.setEnabled(enabled)
        action.setCheckable(checkable)
        return action

    def _new_project(self) -> None:
        if not self._confirm_save_if_needed():
            return

        project = self.project_service.create_project()
        self.table_model.load_project(project)
        self.row_status_filter_combo.setCurrentIndex(0)
        self._clear_undo_history()
        self.search_bar.clear()
        self.search_bar.set_navigation_enabled(False)
        self._update_status_labels()
        self._clear_search_status()
        self._update_window_title()
        self.statusBar().showMessage("已新建项目", 5000)

    def _open_project(self) -> None:
        if not self._confirm_save_if_needed():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开项目",
            "",
            "Data Analysis Project (*.dasproj)",
        )
        if not file_path:
            return

        current_project = self.table_model.project
        try:
            project = self.project_service.open_project(file_path)
        except Exception as exc:
            self.table_model.load_project(current_project)
            QMessageBox.critical(self, "打开失败", str(exc))
            return

        self.table_model.load_project(project)
        self.row_status_filter_combo.setCurrentIndex(0)
        self._apply_table_view_settings(project)
        self._clear_undo_history()
        self.search_bar.clear()
        self.search_bar.set_navigation_enabled(False)
        self._update_status_labels()
        self._clear_search_status()
        self._update_window_title()
        self.statusBar().showMessage(f"打开成功：{Path(project.file_path or file_path).name}", 5000)

    def _save_project(self) -> bool:
        if self.table_model.project.file_path:
            return self._save_project_to_path(self.table_model.project.file_path)
        return self._save_project_as()

    def _save_project_as(self) -> bool:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "另存为项目",
            self.table_model.project.file_path or "",
            "Data Analysis Project (*.dasproj)",
        )
        if not file_path:
            return False
        return self._save_project_to_path(file_path)

    def _save_project_to_path(self, file_path: str) -> bool:
        self.table_model.project.view_settings = self._collect_table_view_settings()
        try:
            saved_path = self.project_service.save_project(self.table_model.project, file_path)
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", str(exc))
            return False

        self.table_model.mark_clean()
        self._update_window_title()
        self.statusBar().showMessage(f"保存成功：{Path(saved_path).name}", 5000)
        return True

    def _import_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择导入文件",
            "",
            "数据文件 (*.csv *.xlsx);;CSV 文件 (*.csv);;Excel 文件 (*.xlsx)",
        )
        if not file_path:
            return

        try:
            project = self.import_export_service.import_file(file_path)
        except Exception as exc:
            QMessageBox.critical(self, "导入失败", str(exc))
            return

        project.dirty = True
        self.table_model.load_project(project)
        self.row_status_filter_combo.setCurrentIndex(0)
        self._clear_undo_history()
        self.search_bar.clear()
        self.search_bar.set_navigation_enabled(False)
        self._update_status_labels()
        self._clear_search_status()
        self._update_window_title()
        self.statusBar().showMessage(
            f"导入成功：{self.table_model.rowCount()} 行，{self.table_model.columnCount()} 列",
            5000,
        )

    def _export_file(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出表格",
            "",
            "CSV 文件 (*.csv);;Excel 文件 (*.xlsx)",
        )
        if not file_path:
            return

        if not Path(file_path).suffix:
            file_path = f"{file_path}.csv"

        try:
            self.import_export_service.export_file(self.table_model.project, file_path)
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", str(exc))
            return

        self.statusBar().showMessage(f"导出成功：{Path(file_path).name}", 5000)

    def _open_statistics_dialog(self) -> None:
        dialog = StatisticsDialog(self.table_model.project, self)
        dialog.exec()

    def _open_pivot_dialog(self) -> None:
        dialog = PivotDialog(
            self.table_model.project,
            self,
            pivot_service=self.pivot_service,
            import_export_service=self.import_export_service,
        )
        dialog.exec()

    def _open_data_update_dialog(self) -> None:
        dialog = DataUpdateDialog(
            self.table_model.project,
            self,
            import_export_service=self.import_export_service,
            data_update_service=self.data_update_service,
            before_project_change=self._push_undo_snapshot,
        )
        dialog.exec()
        if dialog.result is None:
            return

        if dialog.result.has_changes:
            self.table_model.load_project(self.table_model.project)
            self.table_model.mark_dirty()
            self.search_bar.clear()
            self.search_bar.set_navigation_enabled(False)
            self._clear_search_status()
            self._update_status_labels()
            self._update_window_title()
        elif dialog.undo_snapshot_pushed:
            self._discard_latest_undo_snapshot()

        self.statusBar().showMessage(
            f"数据更新完成：更新 {dialog.result.updated_cells} 个单元格，新增 {dialog.result.appended_rows} 行",
            5000,
        )

    def _open_selected_column_settings(self) -> None:
        self._open_column_settings_for_index(self._selected_column_index())

    def _show_column_header_menu(self, position) -> None:
        column_index = self.table_view.horizontalHeader().logicalIndexAt(position)
        if column_index < 0:
            return
        global_position = self.table_view.horizontalHeader().mapToGlobal(position)
        self.table_view.show_header_menu(
            global_position,
            lambda: self._open_column_settings_for_index(column_index),
            lambda: self._open_column_filter_dialog(column_index),
            lambda: self._clear_column_filter(column_index),
            lambda: self._delete_columns([column_index]),
        )

    def _show_row_header_menu(self, position) -> None:
        row_index = self.table_view.verticalHeader().logicalIndexAt(position)
        if row_index < 0:
            return
        global_position = self.table_view.verticalHeader().mapToGlobal(position)
        self.table_view.selectRow(row_index)
        self.table_view.show_row_header_menu(
            global_position,
            self._terminate_selected_rows,
            self._restore_selected_rows,
            self._delete_selected_rows,
        )

    def _selected_column_index(self) -> int:
        current_index = self.table_view.currentIndex()
        if current_index.isValid():
            return current_index.column()
        return 0

    def _selected_row_indexes(self) -> list[int]:
        selected_rows = {
            self.table_model.mapToSource(index).row()
            for index in self.table_view.selectionModel().selectedIndexes()
            if index.isValid() and self.table_model.mapToSource(index).isValid()
        }
        return sorted(selected_rows)

    def _selected_column_indexes(self) -> list[int]:
        selected_columns = {
            index.column()
            for index in self.table_view.selectionModel().selectedColumns()
            if index.isValid()
        }
        return sorted(selected_columns)

    def _selected_source_row_index_for_insert(self) -> int | None:
        selected_rows = self._selected_row_indexes()
        if selected_rows:
            return selected_rows[-1]

        current_index = self.table_view.currentIndex()
        if not current_index.isValid():
            return None
        source_index = self.table_model.mapToSource(current_index)
        return source_index.row() if source_index.isValid() else None

    def _selected_source_column_index_for_insert(self) -> int | None:
        selected_columns = self._selected_column_indexes()
        if selected_columns:
            return selected_columns[-1]

        current_index = self.table_view.currentIndex()
        if not current_index.isValid():
            return None
        return current_index.column()

    def _current_source_row_index(self) -> int | None:
        current_index = self.table_view.currentIndex()
        if not current_index.isValid():
            return None
        source_index = self.table_model.mapToSource(current_index)
        return source_index.row() if source_index.isValid() else None

    def _current_source_column_index(self) -> int | None:
        current_index = self.table_view.currentIndex()
        if not current_index.isValid():
            return None
        source_index = self.table_model.mapToSource(current_index)
        return source_index.column() if source_index.isValid() else None

    def _add_row_after_selection(self) -> None:
        self.table_model.add_empty_row(self._selected_source_row_index_for_insert())
        self._perform_search(self.search_bar.keyword())
        self._update_status_labels()

    def _add_column_after_selection(self) -> None:
        self.table_model.add_empty_column(self._selected_source_column_index_for_insert())
        self._perform_search(self.search_bar.keyword())
        self._update_status_labels()

    def _delete_selected_items(self) -> None:
        column_indexes = self._selected_column_indexes()
        if column_indexes:
            self._delete_columns(column_indexes)
            return
        self._delete_selected_rows()

    def _delete_selected_rows(self) -> None:
        row_indexes = self._selected_row_indexes()
        if not row_indexes:
            current_index = self.table_view.currentIndex()
            if current_index.isValid():
                source_index = self.table_model.mapToSource(current_index)
                if source_index.isValid():
                    row_indexes = [source_index.row()]
        if not row_indexes:
            QMessageBox.information(self, "删除", "请先选择要删除的行或列。")
            return

        self._push_undo_snapshot()
        affected_rows = self.row_service.delete_rows(self.table_model.project, row_indexes)
        if affected_rows == 0:
            return
        self.source_table_model.load_project(self.table_model.project)
        self.table_model.refresh_filter()
        self._perform_search(self.search_bar.keyword())
        self._update_window_title()
        self._update_status_labels()
        self.statusBar().showMessage(f"已删除 {affected_rows} 行", 5000)

    def _delete_columns(self, column_indexes: list[int]) -> None:
        valid_column_ids = [
            self.source_table_model.column_id_at(column_index)
            for column_index in column_indexes
            if 0 <= column_index < self.source_table_model.columnCount()
        ]
        if not valid_column_ids:
            QMessageBox.information(self, "删除", "请先选择要删除的列。")
            return

        self._push_undo_snapshot()
        affected_columns = self.column_service.delete_columns(self.table_model.project, column_indexes)
        if affected_columns == 0:
            return
        for column_id in valid_column_ids:
            self.table_model.filter_state.filters.pop(str(column_id), None)
        self.source_table_model.load_project(self.table_model.project)
        self.table_model.refresh_filter()
        self._perform_search(self.search_bar.keyword())
        self._update_window_title()
        self._update_status_labels()
        self.statusBar().showMessage(f"已删除 {affected_columns} 列", 5000)

    def _terminate_selected_rows(self) -> None:
        row_indexes = self._selected_row_indexes()
        if not row_indexes:
            current_row_index = self._current_source_row_index()
            if current_row_index is not None:
                row_indexes = [current_row_index]
        if not row_indexes:
            QMessageBox.information(self, "终止行", "请先选择行。")
            return
        self._push_undo_snapshot()
        affected_rows = self.row_service.terminate_rows(
            self.table_model.project,
            row_indexes,
            terminated_column_index=self._current_source_column_index(),
        )
        if affected_rows == 0:
            return
        self.table_model.refresh_rows(row_indexes)
        self._perform_search(self.search_bar.keyword())
        self.table_model.mark_dirty()
        self._update_window_title()
        self._update_status_labels()
        self.statusBar().showMessage(f"已终止 {affected_rows} 行", 5000)

    def _restore_selected_rows(self) -> None:
        row_indexes = self._selected_row_indexes()
        if not row_indexes:
            QMessageBox.information(self, "恢复行", "请先选择行。")
            return
        self._push_undo_snapshot()
        affected_rows = self.row_service.restore_rows(self.table_model.project, row_indexes)
        if affected_rows == 0:
            return
        self.table_model.refresh_rows(row_indexes)
        self._perform_search(self.search_bar.keyword())
        self.table_model.mark_dirty()
        self._update_window_title()
        self._update_status_labels()
        self.statusBar().showMessage(f"已恢复 {affected_rows} 行", 5000)

    def _open_column_filter_dialog(self, column_index: int) -> None:
        if column_index < 0 or column_index >= self.table_model.columnCount():
            return

        column = self.source_table_model.columns[column_index]
        column_id = str(column.id)
        unique_values = self.filter_service.get_unique_values(
            self.source_table_model.project,
            column_id,
            include_terminated_rows=True,
        )
        current_criteria = self.table_model.filter_state.filters.get(column_id)
        dialog = ColumnFilterDialog(
            column_id=column_id,
            column_name=column.name,
            unique_values=unique_values,
            current_criteria=current_criteria,
            parent=self,
        )
        if dialog.exec() != ColumnFilterDialog.DialogCode.Accepted:
            return

        if dialog.is_cleared:
            self.table_model.clear_column_filter(column_id)
        else:
            self.table_model.set_column_filter(dialog.get_criteria())
        self._after_filter_changed()

    def _clear_column_filter(self, column_index: int) -> None:
        if column_index < 0 or column_index >= self.table_model.columnCount():
            return
        self.table_model.clear_column_filter(self.source_table_model.column_id_at(column_index))
        self._after_filter_changed()

    def _clear_all_filters(self) -> None:
        self.table_model.clear_filters()
        self.row_status_filter_combo.setCurrentIndex(0)
        self._after_filter_changed()
        self.statusBar().showMessage("已清除全部筛选", 5000)

    def _set_row_status_filter(self) -> None:
        row_status = self.row_status_filter_combo.currentData()
        self.table_model.set_row_status_filter(str(row_status or "all"))
        self._after_filter_changed()

    def _after_filter_changed(self) -> None:
        self._perform_search(self.search_bar.keyword())
        self._update_status_labels()

    def _open_column_settings_for_index(self, column_index: int) -> None:
        if column_index < 0 or column_index >= self.table_model.columnCount():
            return

        while True:
            column = self.table_model.columns[column_index]
            dialog = ColumnSettingsDialog(column, self)
            if dialog.exec() != ColumnSettingsDialog.DialogCode.Accepted:
                return

            try:
                self._push_undo_snapshot()
                self.column_service.update_column(
                    self.table_model.project,
                    column_index,
                    **dialog.get_settings(),
                )
            except ValueError as exc:
                self._discard_latest_undo_snapshot()
                dialog.show_validation_error(str(exc))
                continue

            self.table_model.refresh_column(column_index)
            self.table_model.mark_dirty()
            self._update_window_title()
            break

    def _push_undo_snapshot(self) -> None:
        self.undo_service.push_snapshot(self.table_model.project)
        self._update_undo_action()

    def _clear_undo_history(self) -> None:
        self.undo_service.clear()
        self._update_undo_action()

    def _discard_latest_undo_snapshot(self) -> None:
        self.undo_service.discard_latest()
        self._update_undo_action()

    def _undo_last_operation(self) -> None:
        project = self.undo_service.pop_snapshot()
        if project is None:
            return
        self.table_model.load_project(project)
        self.row_status_filter_combo.setCurrentIndex(0)
        self.table_model.refresh_filter()
        self._perform_search(self.search_bar.keyword())
        self._update_status_labels()
        self._update_window_title()
        self._update_undo_action()
        self.statusBar().showMessage("已撤销上一步操作", 5000)

    def _update_undo_action(self) -> None:
        self.action_undo.setEnabled(self.undo_service.can_undo)

    def _perform_search(self, keyword: str | None = None) -> None:
        search_keyword = self.search_bar.keyword() if keyword is None else keyword
        matches = self.search_service.search(self.table_model.project, search_keyword)
        matches = self._visible_search_matches(matches)
        if not matches:
            self.table_model.clear_search()
            self.search_bar.set_navigation_enabled(False)
            if search_keyword.strip():
                self.search_status_label.setText("未找到匹配项")
            else:
                self._clear_search_status()
            return

        self.table_model.set_search_matches(matches, 0)
        self.search_bar.set_navigation_enabled(True)
        self._focus_search_match(0)

    def _go_to_previous_match(self) -> None:
        if not self.table_model.search_matches:
            return
        next_index = (self.table_model.current_search_index - 1) % len(self.table_model.search_matches)
        self._focus_search_match(next_index)

    def _go_to_next_match(self) -> None:
        if not self.table_model.search_matches:
            return
        next_index = (self.table_model.current_search_index + 1) % len(self.table_model.search_matches)
        self._focus_search_match(next_index)

    def _focus_search_match(self, match_index: int) -> None:
        self.table_model.set_current_search_index(match_index)
        row_index, column_index = self.table_model.search_matches[match_index]
        source_index = self.source_table_model.index(row_index, column_index)
        model_index = self.table_model.mapFromSource(source_index)
        if not model_index.isValid():
            return
        self.table_view.setCurrentIndex(model_index)
        self.table_view.scrollTo(model_index, DataTableView.ScrollHint.PositionAtCenter)
        self._update_search_status()

    def _visible_search_matches(self, matches: list[tuple[int, int]]) -> list[tuple[int, int]]:
        visible_matches: list[tuple[int, int]] = []
        for row_index, column_index in matches:
            source_index = self.source_table_model.index(row_index, column_index)
            if self.table_model.mapFromSource(source_index).isValid():
                visible_matches.append((row_index, column_index))
        return visible_matches

    def _clear_search(self) -> None:
        self.table_model.clear_search()
        self.search_bar.clear()
        self.search_bar.set_navigation_enabled(False)
        self._clear_search_status()
        self.statusBar().showMessage("已清除搜索", 5000)

    def _clear_search_status(self) -> None:
        self.search_status_label.clear()

    def _update_search_status(self) -> None:
        if not self.table_model.search_matches:
            self.search_status_label.setText("未找到匹配项")
            return
        self.search_status_label.setText(
            f"找到 {len(self.table_model.search_matches)} 个匹配项，当前第 {self.table_model.current_search_index + 1} 个"
        )

    def _confirm_save_if_needed(self) -> bool:
        if not self.table_model.project.dirty:
            return True

        result = QMessageBox.question(
            self,
            "未保存更改",
            "当前项目有未保存更改，是否先保存？",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if result == QMessageBox.StandardButton.Save:
            return self._save_project()
        if result == QMessageBox.StandardButton.Discard:
            return True
        return False

    def _on_dirty_changed(self, _dirty: bool) -> None:
        self._update_window_title()

    def _on_current_changed(self) -> None:
        self._update_status_labels()

    def _update_status_labels(self) -> None:
        row_count = self.table_model.rowCount()
        total_row_count = self.source_table_model.rowCount()
        column_count = self.table_model.columnCount()
        self.row_count_label.setText(f"行数：{row_count}")
        self.column_count_label.setText(f"列数：{column_count}")
        if self.table_model.filter_state.is_active:
            self.filter_status_label.setText(f"已筛选：显示 {row_count} / {total_row_count} 行")
        else:
            self.filter_status_label.clear()

        index = self.table_view.currentIndex()
        if index.isValid():
            self.current_cell_label.setText(
                f"当前单元格：第 {index.row() + 1} 行，第 {index.column() + 1} 列"
            )
        else:
            self.current_cell_label.setText("当前单元格：未选中")

    def _update_window_title(self) -> None:
        project = self.table_model.project
        project_label = Path(project.file_path).name if project.file_path else project.name
        dirty_suffix = " *" if project.dirty else ""
        self.setWindowTitle(f"ZY专用 V1.0 - {project_label}{dirty_suffix}")

    def _collect_table_view_settings(self) -> dict[str, object]:
        column_widths: dict[str, int] = {}
        for column_index, column in enumerate(self.source_table_model.columns):
            column_widths[str(column.id)] = self.table_view.columnWidth(column_index)
        return {"column_widths": column_widths}

    def _apply_table_view_settings(self, project) -> None:
        settings = project.view_settings if isinstance(project.view_settings, dict) else {}
        raw_widths = settings.get("column_widths", {})
        if not isinstance(raw_widths, dict):
            return
        width_by_column_id = {
            str(column_id): width
            for column_id, width in raw_widths.items()
            if isinstance(width, int) and width > 0
        }
        for column_index, column in enumerate(self.source_table_model.columns):
            width = width_by_column_id.get(str(column.id))
            if width is not None:
                self.table_view.setColumnWidth(column_index, width)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._confirm_save_if_needed():
            event.accept()
            return
        event.ignore()
