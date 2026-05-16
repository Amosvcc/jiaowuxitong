from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.core import last_file_dialog_dir, remember_file_dialog_path
from app.models import Project, StatisticsItem
from app.services import StatisticsService


class StatisticsDialog(QDialog):
    def __init__(
        self,
        project: Project,
        parent=None,
        *,
        statistics_service: StatisticsService | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("字段统计")
        self.resize(760, 520)

        self.project = project
        self.statistics_service = statistics_service or StatisticsService()
        self.current_results: list[StatisticsItem] = []
        self.has_generated_results = False

        self.column_combo = QComboBox(self)
        self.include_terminated_checkbox = QCheckBox("包含已终止行", self)
        self.ignore_empty_checkbox = QCheckBox("忽略空值", self)
        self.generate_button = QPushButton("生成统计", self)
        self.export_button = QPushButton("导出统计结果", self)
        self.close_button = QPushButton("关闭", self)
        self.status_label = QLabel("", self)
        self.result_table = QTableWidget(self)

        self._setup_ui()
        self._load_columns()
        self._connect_signals()

    def _setup_ui(self) -> None:
        self.include_terminated_checkbox.setChecked(True)
        self.ignore_empty_checkbox.setChecked(True)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("统计字段", self))
        controls_layout.addWidget(self.column_combo, 1)
        controls_layout.addWidget(self.include_terminated_checkbox)
        controls_layout.addWidget(self.ignore_empty_checkbox)
        controls_layout.addWidget(self.generate_button)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.export_button)
        buttons_layout.addWidget(self.close_button)

        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["字段值", "数量", "占比"])
        self.result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.result_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.result_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.verticalHeader().setVisible(False)

        layout = QVBoxLayout(self)
        layout.addLayout(controls_layout)
        layout.addWidget(self.result_table)
        layout.addWidget(self.status_label)
        layout.addLayout(buttons_layout)

    def _load_columns(self) -> None:
        for column in self.project.get_ordered_columns():
            self.column_combo.addItem(column.name, column.id)
        has_columns = self.column_combo.count() > 0
        self.generate_button.setEnabled(has_columns)
        self.export_button.setEnabled(has_columns)
        if not has_columns:
            self.status_label.setText("无可统计字段")

    def _connect_signals(self) -> None:
        self.generate_button.clicked.connect(self.generate_statistics)
        self.export_button.clicked.connect(self.export_statistics)
        self.close_button.clicked.connect(self.close)

    def generate_statistics(self) -> None:
        if self.column_combo.count() == 0:
            self.current_results = []
            self.has_generated_results = True
            self._load_results([])
            self.status_label.setText("无可统计字段")
            return

        try:
            results = self.statistics_service.generate_statistics(
                self.project,
                column_index=self.column_combo.currentIndex(),
                include_terminated=self.include_terminated_checkbox.isChecked(),
                ignore_empty=self.ignore_empty_checkbox.isChecked(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "统计失败", str(exc))
            return

        self.current_results = results
        self.has_generated_results = True
        self._load_results(results)
        if results:
            self.status_label.setText(f"共 {len(results)} 条统计结果")
        else:
            self.status_label.setText("无统计结果")

    def export_statistics(self) -> None:
        if not self.has_generated_results:
            QMessageBox.warning(self, "导出统计结果", "请先生成统计结果")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出统计结果",
            last_file_dialog_dir(),
            "CSV 文件 (*.csv);;Excel 文件 (*.xlsx)",
        )
        if not file_path:
            return

        if not Path(file_path).suffix:
            file_path = f"{file_path}.csv"
        remember_file_dialog_path(file_path)

        try:
            self.statistics_service.export_statistics(
                file_path,
                self.column_combo.currentText(),
                self.current_results,
                include_terminated=self.include_terminated_checkbox.isChecked(),
                ignore_empty=self.ignore_empty_checkbox.isChecked(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", str(exc))
            return

        self.status_label.setText(f"已导出统计结果：{Path(file_path).name}")

    def _load_results(self, results: list[StatisticsItem]) -> None:
        self.result_table.setRowCount(len(results))
        for row_index, item in enumerate(results):
            self.result_table.setItem(row_index, 0, QTableWidgetItem(item.value))
            self.result_table.setItem(row_index, 1, QTableWidgetItem(str(item.count)))
            self.result_table.setItem(
                row_index,
                2,
                QTableWidgetItem(self.statistics_service.format_ratio(item.ratio)),
            )
