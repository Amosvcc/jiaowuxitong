from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from app.models import ColumnFilterCriteria


class ColumnFilterDialog(QDialog):
    BLANK_LABEL = "空白"

    def __init__(
        self,
        *,
        column_id: str,
        column_name: str,
        unique_values: dict[str, int],
        current_criteria: ColumnFilterCriteria | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.column_id = str(column_id)
        self.unique_values = unique_values
        self._cleared = False

        self.setWindowTitle(f"筛选：{column_name}")
        self.title_label = QLabel(f"筛选列：{column_name}", self)
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("搜索筛选值...")
        self.value_list = QListWidget(self)
        self.select_all_button = QPushButton("全选", self)
        self.select_none_button = QPushButton("全不选", self)
        self.invert_selection_button = QPushButton("反选", self)
        self.clear_button = QPushButton("清除当前列筛选", self)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )

        self._setup_ui()
        self._populate_values(current_criteria)
        self._connect_signals()

    @property
    def is_cleared(self) -> bool:
        return self._cleared

    def get_criteria(self) -> ColumnFilterCriteria:
        selected_values: set[str] = set()
        include_blank = False

        for index in range(self.value_list.count()):
            item = self.value_list.item(index)
            if item.checkState() != Qt.CheckState.Checked:
                continue
            value = item.data(Qt.ItemDataRole.UserRole)
            if value == "":
                include_blank = True
            else:
                selected_values.add(str(value))

        return ColumnFilterCriteria(
            column_id=self.column_id,
            selected_values=selected_values,
            include_blank=include_blank,
        )

    def clear_current_filter(self) -> None:
        self._cleared = True
        self.accept()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.search_input)
        layout.addWidget(self.value_list)

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.select_all_button)
        action_layout.addWidget(self.select_none_button)
        action_layout.addWidget(self.invert_selection_button)
        action_layout.addStretch(1)
        action_layout.addWidget(self.clear_button)
        layout.addLayout(action_layout)
        layout.addWidget(self.button_box)
        self.resize(360, 480)

    def _populate_values(self, current_criteria: ColumnFilterCriteria | None) -> None:
        selected_values = current_criteria.selected_values if current_criteria else set()
        include_blank = current_criteria.include_blank if current_criteria else False
        has_active_filter = current_criteria.is_active if current_criteria else False

        for value, count in self.unique_values.items():
            label = self.BLANK_LABEL if value == "" else value
            item = QListWidgetItem(f"{label} ({count})")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setData(Qt.ItemDataRole.UserRole, value)

            checked = True
            if has_active_filter:
                checked = include_blank if value == "" else value in selected_values
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            self.value_list.addItem(item)

    def _connect_signals(self) -> None:
        self.search_input.textChanged.connect(self._filter_visible_items)
        self.select_all_button.clicked.connect(lambda: self._set_all_visible_checked(True))
        self.select_none_button.clicked.connect(lambda: self._set_all_visible_checked(False))
        self.invert_selection_button.clicked.connect(self._invert_visible_checked)
        self.clear_button.clicked.connect(self.clear_current_filter)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def _filter_visible_items(self, keyword: str) -> None:
        normalized_keyword = keyword.strip().lower()
        for index in range(self.value_list.count()):
            item = self.value_list.item(index)
            value = item.data(Qt.ItemDataRole.UserRole)
            label = self.BLANK_LABEL if value == "" else str(value)
            item.setHidden(normalized_keyword not in label.lower())

    def _set_all_visible_checked(self, checked: bool) -> None:
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for index in range(self.value_list.count()):
            item = self.value_list.item(index)
            if not item.isHidden():
                item.setCheckState(state)

    def _invert_visible_checked(self) -> None:
        for index in range(self.value_list.count()):
            item = self.value_list.item(index)
            if item.isHidden():
                continue
            next_state = (
                Qt.CheckState.Unchecked
                if item.checkState() == Qt.CheckState.Checked
                else Qt.CheckState.Checked
            )
            item.setCheckState(next_state)
