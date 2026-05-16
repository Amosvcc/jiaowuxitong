from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
)

from app.core import last_file_dialog_dir, remember_file_dialog_path
from app.models import PivotResult, Project
from app.services import ImportExportService, PivotService
from app.ui.models import PivotTableModel


class PivotDialog(QDialog):
    def __init__(
        self,
        project: Project,
        parent=None,
        *,
        pivot_service: PivotService | None = None,
        import_export_service: ImportExportService | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("数据透视 / 交叉统计")
        self.resize(960, 640)

        self.project = project
        self.pivot_service = pivot_service or PivotService()
        self.import_export_service = import_export_service or ImportExportService()
        self.current_result: PivotResult | None = None

        self.row_field_combo = QComboBox(self)
        self.column_field_combo = QComboBox(self)
        self.expand_tags_checkbox = QCheckBox("按标签展开列头字段", self)
        self.tag_separators_input = QLineEdit(self)
        self.ignore_empty_row_checkbox = QCheckBox("忽略空行字段", self)
        self.ignore_empty_column_checkbox = QCheckBox("忽略空列头字段", self)
        self.include_terminated_rows_checkbox = QCheckBox("包含已终止行", self)
        self.show_row_totals_checkbox = QCheckBox("显示行合计", self)
        self.show_column_totals_checkbox = QCheckBox("显示列合计", self)
        self.generate_button = QPushButton("生成", self)
        self.export_button = QPushButton("导出", self)
        self.close_button = QPushButton("关闭", self)
        self.status_label = QLabel("请选择行字段和列头字段后生成结果。", self)
        self.result_table = QTableView(self)
        self.result_model = PivotTableModel(parent=self)

        self._setup_ui()
        self._load_columns()
        self._load_default_options()
        self._connect_signals()
        self._update_generate_button()

    def _setup_ui(self) -> None:
        self.result_table.setModel(self.result_model)
        self.result_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.result_table.horizontalHeader().setStretchLastSection(True)

        form_layout = QFormLayout()
        form_layout.addRow("行字段", self.row_field_combo)
        form_layout.addRow("列头字段", self.column_field_combo)
        form_layout.addRow("", self.expand_tags_checkbox)
        form_layout.addRow("标签分隔符", self.tag_separators_input)
        form_layout.addRow("", self.ignore_empty_row_checkbox)
        form_layout.addRow("", self.ignore_empty_column_checkbox)
        form_layout.addRow("", self.include_terminated_rows_checkbox)
        form_layout.addRow("", self.show_row_totals_checkbox)
        form_layout.addRow("", self.show_column_totals_checkbox)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.generate_button)
        buttons_layout.addWidget(self.export_button)
        buttons_layout.addWidget(self.close_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addWidget(self.result_table, 1)
        layout.addWidget(self.status_label)
        layout.addLayout(buttons_layout)

    def _load_columns(self) -> None:
        self.row_field_combo.clear()
        self.column_field_combo.clear()
        self.row_field_combo.addItem("", "")
        self.column_field_combo.addItem("", "")
        for column in self.project.get_ordered_columns():
            self.row_field_combo.addItem(column.name, column.name)
            self.column_field_combo.addItem(column.name, column.name)

    def _load_default_options(self) -> None:
        self.expand_tags_checkbox.setChecked(False)
        self.tag_separators_input.setText(";；,，、/|\\n")
        self.tag_separators_input.setPlaceholderText(";；,，、/|\\n")
        self.ignore_empty_row_checkbox.setChecked(True)
        self.ignore_empty_column_checkbox.setChecked(True)
        self.include_terminated_rows_checkbox.setChecked(True)
        self.show_row_totals_checkbox.setChecked(True)
        self.show_column_totals_checkbox.setChecked(True)
        self.export_button.setEnabled(False)
        self._update_tag_separator_state()

    def _connect_signals(self) -> None:
        self.row_field_combo.currentIndexChanged.connect(self._update_generate_button)
        self.column_field_combo.currentIndexChanged.connect(self._update_generate_button)
        self.expand_tags_checkbox.toggled.connect(self._update_tag_separator_state)
        self.generate_button.clicked.connect(self.generate_pivot)
        self.export_button.clicked.connect(self.export_pivot)
        self.close_button.clicked.connect(self.close)

    def generate_pivot(self) -> None:
        if not self.can_generate():
            QMessageBox.warning(self, "数据透视", "请选择行字段和列头字段。")
            return

        try:
            result = self.pivot_service.build_pivot(
                self.project,
                row_field=self.row_field_combo.currentText(),
                column_field=self.column_field_combo.currentText(),
                expand_column_tags=self.expand_tags_checkbox.isChecked(),
                tag_separators=self._parse_tag_separators(),
                ignore_empty_row_values=self.ignore_empty_row_checkbox.isChecked(),
                ignore_empty_column_values=self.ignore_empty_column_checkbox.isChecked(),
                include_terminated_rows=self.include_terminated_rows_checkbox.isChecked(),
                show_row_totals=self.show_row_totals_checkbox.isChecked(),
                show_column_totals=self.show_column_totals_checkbox.isChecked(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "数据透视", str(exc))
            return

        self.current_result = result
        self.result_model.set_pivot_result(result)
        self.export_button.setEnabled(True)
        self.status_label.setText(
            f"已生成 {len(result.row_headers)} 行 x {len(result.column_headers)} 列的数据透视结果。"
        )

    def export_pivot(self) -> None:
        if self.current_result is None:
            QMessageBox.warning(self, "导出数据透视结果", "请先生成数据透视结果。")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出数据透视结果",
            last_file_dialog_dir(),
            "Excel 文件 (*.xlsx);;CSV 文件 (*.csv)",
        )
        if not file_path:
            return
        if not Path(file_path).suffix:
            file_path = f"{file_path}.xlsx"
        remember_file_dialog_path(file_path)

        try:
            self.import_export_service.export_pivot_result(self.current_result, file_path)
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", str(exc))
            return

        self.status_label.setText(f"已导出数据透视结果：{Path(file_path).name}")

    def can_generate(self) -> bool:
        return bool(self.row_field_combo.currentText().strip() and self.column_field_combo.currentText().strip())

    def _update_generate_button(self) -> None:
        self.generate_button.setEnabled(self.can_generate())

    def _update_tag_separator_state(self) -> None:
        self.tag_separators_input.setEnabled(self.expand_tags_checkbox.isChecked())

    def _parse_tag_separators(self) -> list[str]:
        text = self.tag_separators_input.text()
        if not text.strip():
            return list(PivotService.DEFAULT_TAG_SEPARATORS)

        normalized = text.replace("\\n", "\n")
        separators: list[str] = []
        for separator in normalized:
            if separator.isspace() and separator != "\n":
                continue
            if separator not in separators:
                separators.append(separator)
        return separators or list(PivotService.DEFAULT_TAG_SEPARATORS)
