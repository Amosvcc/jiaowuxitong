from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models import Column


class ColumnSettingsDialog(QDialog):
    FIELD_TYPES = [
        ("文本", "text"),
        ("数字", "number"),
        ("日期", "date"),
        ("下拉", "dropdown"),
    ]

    def __init__(self, column: Column, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("列设置")
        self.column = column

        self.name_input = QLineEdit(self)
        self.field_type_combo = QComboBox(self)
        self.dropdown_options_edit = QPlainTextEdit(self)
        self.allow_custom_value_checkbox = QCheckBox("允许自定义值", self)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )

        self._setup_ui()
        self._load_column()
        self._connect_signals()

    def _setup_ui(self) -> None:
        form_layout = QFormLayout()
        form_layout.addRow("列名", self.name_input)
        form_layout.addRow("字段类型", self.field_type_combo)
        form_layout.addRow("下拉选项", self.dropdown_options_edit)
        form_layout.addRow("", self.allow_custom_value_checkbox)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)

        for label, value in self.FIELD_TYPES:
            self.field_type_combo.addItem(label, value)

        self.dropdown_options_edit.setPlaceholderText("每行一个选项")

    def _load_column(self) -> None:
        self.name_input.setText(self.column.name)
        combo_index = self.field_type_combo.findData(self.column.field_type)
        self.field_type_combo.setCurrentIndex(max(combo_index, 0))
        self.dropdown_options_edit.setPlainText("\n".join(self.column.dropdown_options))
        self.allow_custom_value_checkbox.setChecked(self.column.allow_custom_value)
        self._update_dropdown_widgets()

    def _connect_signals(self) -> None:
        self.field_type_combo.currentIndexChanged.connect(self._update_dropdown_widgets)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def _update_dropdown_widgets(self) -> None:
        is_dropdown = self.field_type_combo.currentData() == "dropdown"
        self.dropdown_options_edit.setEnabled(is_dropdown)
        self.allow_custom_value_checkbox.setEnabled(is_dropdown)

    def get_settings(self) -> dict[str, object]:
        dropdown_options = self.dropdown_options_edit.toPlainText().splitlines()
        return {
            "name": self.name_input.text(),
            "field_type": self.field_type_combo.currentData(),
            "dropdown_options": dropdown_options,
            "allow_custom_value": self.allow_custom_value_checkbox.isChecked(),
        }

    def show_validation_error(self, message: str) -> None:
        QMessageBox.warning(self, "列设置错误", message)
