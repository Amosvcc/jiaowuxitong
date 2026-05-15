from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from app.models import DataUpdateAction, DataUpdateDetail


class DataUpdateDetailTableModel(QAbstractTableModel):
    HEADERS = ["类型", "匹配值", "源表行号", "主表行号", "字段名", "原值", "新值", "说明"]
    ACTION_LABELS = {
        DataUpdateAction.ADD_COLUMN: "新增列",
        DataUpdateAction.UPDATE_CELL: "更新单元格",
        DataUpdateAction.SKIP_EMPTY: "跳过空值",
        DataUpdateAction.SKIP_EXISTING: "跳过已有值",
        DataUpdateAction.SKIP_TERMINATED: "跳过终止行",
        DataUpdateAction.APPEND_ROW: "追加行",
        DataUpdateAction.UNMATCHED_ROW: "未匹配行",
        DataUpdateAction.NO_CHANGE: "无变化",
    }

    def __init__(self, details: list[DataUpdateDetail] | None = None, parent=None) -> None:
        super().__init__(parent)
        self._all_details = details or []
        self._filtered_details = list(self._all_details)
        self._action_filter: DataUpdateAction | None = None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._filtered_details)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return None

        detail = self._filtered_details[index.row()]
        values = [
            self.ACTION_LABELS.get(detail.action, detail.action.value),
            detail.key_value,
            self._display_value(detail.source_row_index),
            self._display_value(detail.target_row_index),
            self._display_value(detail.column_name),
            self._display_value(detail.old_value),
            self._display_value(detail.new_value),
            self._display_value(detail.message),
        ]
        return values[index.column()]

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return str(section + 1)

    def set_action_filter(self, action: DataUpdateAction | None) -> None:
        self.beginResetModel()
        self._action_filter = action
        if action is None:
            self._filtered_details = list(self._all_details)
        else:
            self._filtered_details = [detail for detail in self._all_details if detail.action == action]
        self.endResetModel()

    def current_details(self) -> list[DataUpdateDetail]:
        return list(self._filtered_details)

    @staticmethod
    def _display_value(value) -> str:
        return "" if value is None else str(value)
