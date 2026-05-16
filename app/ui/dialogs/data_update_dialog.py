from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core import DuplicateMatchKeyError, last_file_dialog_dir, remember_file_dialog_path
from app.models import DataUpdateResult, Project
from app.services import DataUpdateService, ImportExportService
from app.ui.dialogs.data_update_detail_dialog import DataUpdateDetailDialog


class DataUpdateDialog(QDialog):
    def __init__(
        self,
        project: Project,
        parent=None,
        *,
        import_export_service: ImportExportService | None = None,
        data_update_service: DataUpdateService | None = None,
        before_project_change: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("数据更新")

        self.project = project
        self.import_export_service = import_export_service or ImportExportService()
        self.data_update_service = data_update_service or DataUpdateService()
        self.before_project_change = before_project_change
        self.source_columns: list[str] = []
        self.source_rows: list[list[str]] = []
        self.result: DataUpdateResult | None = None
        self.undo_snapshot_pushed = False

        self.file_path_input = QLineEdit(self)
        self.file_path_input.setReadOnly(True)
        self.choose_file_button = QPushButton("选择文件", self)
        self.target_key_combo = QComboBox(self)
        self.source_key_combo = QComboBox(self)
        self.overwrite_existing_checkbox = QCheckBox("覆盖已有值", self)
        self.ignore_empty_values_checkbox = QCheckBox("忽略空值", self)
        self.add_missing_columns_checkbox = QCheckBox("自动新增列", self)
        self.append_unmatched_rows_checkbox = QCheckBox("追加未匹配行", self)
        self.update_terminated_rows_checkbox = QCheckBox("更新已终止行", self)
        self.preview_label = QLabel(self)
        self.view_details_button = QPushButton("查看详情", self)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, self)
        self.execute_button = self.button_box.addButton("执行更新", QDialogButtonBox.ButtonRole.ActionRole)

        self._setup_ui()
        self._load_target_columns()
        self._load_default_options()
        self._connect_signals()
        self._update_execute_button()
        self._update_view_details_button()

    def _setup_ui(self) -> None:
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_path_input, 1)
        file_layout.addWidget(self.choose_file_button)
        file_widget = QWidget(self)
        file_widget.setLayout(file_layout)

        form_layout = QFormLayout()
        form_layout.addRow("更新文件", file_widget)
        form_layout.addRow("主表匹配字段", self.target_key_combo)
        form_layout.addRow("更新表匹配字段", self.source_key_combo)
        form_layout.addRow("", self.overwrite_existing_checkbox)
        form_layout.addRow("", self.ignore_empty_values_checkbox)
        form_layout.addRow("", self.add_missing_columns_checkbox)
        form_layout.addRow("", self.append_unmatched_rows_checkbox)
        form_layout.addRow("", self.update_terminated_rows_checkbox)

        self.preview_label.setWordWrap(True)
        self.preview_label.setText("请选择 CSV 或 Excel 更新表，并确认匹配字段后执行。")

        summary_layout = QHBoxLayout()
        summary_layout.addWidget(self.preview_label, 1)
        summary_layout.addWidget(self.view_details_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addLayout(summary_layout)
        layout.addWidget(self.button_box)

    def _load_target_columns(self) -> None:
        self.target_key_combo.clear()
        for column in self.project.get_ordered_columns():
            self.target_key_combo.addItem(column.name)

    def _load_default_options(self) -> None:
        self.overwrite_existing_checkbox.setChecked(False)
        self.ignore_empty_values_checkbox.setChecked(True)
        self.add_missing_columns_checkbox.setChecked(True)
        self.append_unmatched_rows_checkbox.setChecked(True)
        self.update_terminated_rows_checkbox.setChecked(False)

    def _connect_signals(self) -> None:
        self.choose_file_button.clicked.connect(self.select_source_file)
        self.target_key_combo.currentIndexChanged.connect(self._update_execute_button)
        self.source_key_combo.currentIndexChanged.connect(self._update_execute_button)
        self.execute_button.clicked.connect(self.execute_update)
        self.view_details_button.clicked.connect(self.open_detail_dialog)
        self.button_box.accepted.connect(self.accept)
        close_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if close_button is not None:
            close_button.setText("关闭")

    def select_source_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择更新文件",
            last_file_dialog_dir(),
            "数据文件 (*.csv *.xlsx);;CSV 文件 (*.csv);;Excel 文件 (*.xlsx)",
        )
        if not file_path:
            return
        remember_file_dialog_path(file_path)
        self.load_source_file(file_path)

    def load_source_file(self, file_path: str) -> None:
        columns, rows = self.import_export_service.read_table(file_path)
        self.source_columns = columns
        self.source_rows = rows
        self.result = None
        self.file_path_input.setText(file_path)
        self.source_key_combo.clear()
        self.source_key_combo.addItems(columns)
        self.preview_label.setText(
            f"已加载 {Path(file_path).name}，共 {len(rows)} 行，{len(columns)} 列。"
            " 执行后会按匹配字段更新当前项目，不会替换主表。"
        )
        self._update_execute_button()
        self._update_view_details_button()

    def execute_update(self) -> None:
        if not self.can_execute():
            QMessageBox.warning(self, "数据更新", "请选择主表和更新表匹配字段。")
            return

        snapshot_pushed = False
        try:
            if self.before_project_change is not None:
                self.before_project_change()
                snapshot_pushed = True
                self.undo_snapshot_pushed = True
            result = self.data_update_service.update_project_from_table(
                project=self.project,
                source_columns=self.source_columns,
                source_rows=self.source_rows,
                target_key_column=self.target_key_combo.currentText(),
                source_key_column=self.source_key_combo.currentText(),
                overwrite_existing=self.overwrite_existing_checkbox.isChecked(),
                ignore_empty_values=self.ignore_empty_values_checkbox.isChecked(),
                add_missing_columns=self.add_missing_columns_checkbox.isChecked(),
                append_unmatched_rows=self.append_unmatched_rows_checkbox.isChecked(),
                update_terminated_rows=self.update_terminated_rows_checkbox.isChecked(),
            )
        except DuplicateMatchKeyError as exc:
            self._discard_parent_undo_snapshot(snapshot_pushed)
            lines = [str(exc)]
            if exc.duplicate_target_keys:
                lines.append(f"主表重复值：{', '.join(exc.duplicate_target_keys)}")
            if exc.duplicate_source_keys:
                lines.append(f"更新表重复值：{', '.join(exc.duplicate_source_keys)}")
            QMessageBox.critical(self, "数据更新失败", "\n".join(lines))
            return
        except Exception as exc:
            self._discard_parent_undo_snapshot(snapshot_pushed)
            QMessageBox.critical(self, "数据更新失败", str(exc))
            return

        self.result = result
        self.preview_label.setText(self.format_result_summary(result))
        self._update_view_details_button()
        QMessageBox.information(self, "数据更新完成", self.format_result_summary(result))

    def _discard_parent_undo_snapshot(self, snapshot_pushed: bool) -> None:
        if snapshot_pushed and self.parent() is not None and hasattr(self.parent(), "_discard_latest_undo_snapshot"):
            self.parent()._discard_latest_undo_snapshot()
            self.undo_snapshot_pushed = False

    def open_detail_dialog(self) -> None:
        if self.result is None or not self.result.details:
            return
        dialog = DataUpdateDetailDialog(self.result.details, self)
        dialog.exec()

    def can_execute(self) -> bool:
        return bool(
            self.source_columns
            and self.target_key_combo.currentText().strip()
            and self.source_key_combo.currentText().strip()
        )

    def format_result_summary(self, result: DataUpdateResult) -> str:
        added_columns_text = "、".join(result.added_columns) if result.added_columns else "无"
        return (
            f"匹配行数：{result.matched_rows}\n"
            f"未匹配更新表行数：{result.unmatched_source_rows}\n"
            f"追加行数：{result.appended_rows}\n"
            f"新增列：{added_columns_text}\n"
            f"更新单元格：{result.updated_cells}\n"
            f"跳过空值：{result.skipped_empty_values}\n"
            f"跳过已有值：{result.skipped_existing_values}\n"
            f"跳过已终止行：{result.skipped_terminated_rows}\n"
            f"详情条数：{len(result.details)}"
        )

    def _update_execute_button(self) -> None:
        self.execute_button.setEnabled(self.can_execute())

    def _update_view_details_button(self) -> None:
        self.view_details_button.setEnabled(bool(self.result and self.result.details))
