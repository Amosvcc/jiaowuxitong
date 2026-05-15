from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from app.models import PivotResult


class PivotTableModel(QAbstractTableModel):
    def __init__(self, result: PivotResult | None = None, parent=None) -> None:
        super().__init__(parent)
        self._result = result

    def set_pivot_result(self, result: PivotResult | None) -> None:
        self.beginResetModel()
        self._result = result
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid() or self._result is None:
            return 0
        return len(self._result.row_headers) + (1 if self._result.show_column_totals else 0)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid() or self._result is None:
            return 0
        return 1 + len(self._result.column_headers) + (1 if self._result.show_row_totals else 0)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return None
        if self._result is None:
            return None

        row_index = index.row()
        column_index = index.column()
        is_total_row = self._result.show_column_totals and row_index == len(self._result.row_headers)

        if column_index == 0:
            return "合计" if is_total_row else self._result.row_headers[row_index]

        if column_index <= len(self._result.column_headers):
            column_header = self._result.column_headers[column_index - 1]
            if is_total_row:
                return self._result.column_totals.get(column_header, 0)
            row_header = self._result.row_headers[row_index]
            return self._result.matrix.get(row_header, {}).get(column_header, 0)

        if self._result.show_row_totals:
            if is_total_row:
                return self._result.grand_total
            row_header = self._result.row_headers[row_index]
            return self._result.row_totals.get(row_header, 0)

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if role != Qt.ItemDataRole.DisplayRole or self._result is None:
            return None

        if orientation == Qt.Orientation.Horizontal:
            if section == 0:
                return self._result.row_field
            if section <= len(self._result.column_headers):
                return self._result.column_headers[section - 1]
            if self._result.show_row_totals:
                return "合计"
            return None

        return str(section + 1)
