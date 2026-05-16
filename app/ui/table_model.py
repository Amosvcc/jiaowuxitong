from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont

from app.models import Project


class DataTableModel(QAbstractTableModel):
    dirty_changed = Signal(bool)

    def __init__(self, project: Project | None = None, parent=None) -> None:
        super().__init__(parent)
        self.project = project or Project.create_empty()
        self.columns = self.project.columns
        self.rows = self.project.rows
        self.cells = self.project.cells
        self.search_matches: list[tuple[int, int]] = []
        self.current_search_index = -1
        self.before_project_change: Callable[[], None] | None = None
        self._search_match_set: set[tuple[int, int]] = set()
        self._search_brush = QBrush(QColor("#fff59d"))
        self._current_search_brush = QBrush(QColor("#ffcc80"))
        self._current_search_foreground_brush = QBrush(QColor("#e65100"))
        self._terminated_row_brush = QBrush(QColor("#e0e0e0"))
        self._terminated_cell_brush = QBrush(QColor("#ff5252"))

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None

        position = (index.row(), index.column())
        row = self.rows[index.row()]
        if role == Qt.BackgroundRole:
            if position in self._search_match_set:
                if (
                    self.current_search_index >= 0
                    and self.current_search_index < len(self.search_matches)
                    and position == self.search_matches[self.current_search_index]
                ):
                    return self._current_search_brush
                return self._search_brush
            column = self.columns[index.column()]
            if row.is_terminated and row.terminated_column_id == column.id:
                return self._terminated_cell_brush
            if row.is_terminated:
                return self._terminated_row_brush

        if role == Qt.ForegroundRole and self.is_current_search_match(index):
            return self._current_search_foreground_brush

        if role == Qt.FontRole and self.is_current_search_match(index):
            font = QFont()
            font.setBold(True)
            return font

        if role in (Qt.DisplayRole, Qt.EditRole):
            column = self.columns[index.column()]
            return self.project.get_cell_value(row.id, column.id)

        return None

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if not index.isValid() or role != Qt.EditRole:
            return False

        row = self.rows[index.row()]
        if row.is_terminated:
            return False

        column = self.columns[index.column()]
        old_value = self.project.get_cell_value(row.id, column.id)
        new_value = "" if value is None else str(value)
        if old_value == new_value:
            return False
        self._notify_before_project_change()
        self.project.set_cell_value(row.id, column.id, new_value)
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        self.mark_dirty()
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        base_flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        row = self.rows[index.row()]
        if row.is_terminated:
            return base_flags
        return base_flags | Qt.ItemFlag.ItemIsEditable

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal:
            return self.columns[section].name

        row = self.rows[section]
        row_number = section + 1
        return f"[终止] {row_number}" if row.is_terminated else str(row_number)

    def row_id_at(self, row_index: int) -> str:
        if row_index < 0 or row_index >= len(self.rows):
            raise IndexError("行索引超出范围")
        return str(self.rows[row_index].id)

    def column_id_at(self, column_index: int) -> str:
        if column_index < 0 or column_index >= len(self.columns):
            raise IndexError("列索引超出范围")
        return str(self.columns[column_index].id)

    def add_empty_row(self, after_row_index: int | None = None) -> None:
        self._notify_before_project_change()
        row_index = len(self.rows) if after_row_index is None else min(max(after_row_index + 1, 0), len(self.rows))
        self.beginInsertRows(QModelIndex(), row_index, row_index)
        self.project.insert_row(row_index)
        self.rows = self.project.rows
        self.cells = self.project.cells
        self.endInsertRows()
        self.mark_dirty()

    def add_empty_column(self, after_column_index: int | None = None) -> None:
        self._notify_before_project_change()
        column_index = (
            len(self.columns)
            if after_column_index is None
            else min(max(after_column_index + 1, 0), len(self.columns))
        )
        self.beginInsertColumns(QModelIndex(), column_index, column_index)
        self.project.insert_column(column_index)
        self.columns = self.project.columns
        self.cells = self.project.cells
        self.endInsertColumns()
        self.mark_dirty()

    def load_project(self, project: Project) -> None:
        self.beginResetModel()
        self.project = project
        self.columns = project.columns
        self.rows = project.rows
        self.cells = project.cells
        self.search_matches = []
        self.current_search_index = -1
        self._search_match_set = set()
        self.endResetModel()
        self.dirty_changed.emit(self.project.dirty)

    def mark_dirty(self) -> None:
        if not self.project.dirty:
            self.project.dirty = True
            self.dirty_changed.emit(True)

    def mark_clean(self) -> None:
        if self.project.dirty:
            self.project.dirty = False
            self.dirty_changed.emit(False)

    def set_search_matches(self, matches: list[tuple[int, int]], current_index: int = -1) -> None:
        affected_positions = set(self.search_matches) | set(matches)
        self.search_matches = matches
        self._search_match_set = set(matches)
        self.current_search_index = current_index if matches else -1
        self._emit_search_updates(affected_positions)

    def clear_search(self) -> None:
        self.set_search_matches([], -1)

    def set_current_search_index(self, index: int) -> None:
        if not self.search_matches:
            self.current_search_index = -1
            return

        affected_positions = set()
        if 0 <= self.current_search_index < len(self.search_matches):
            affected_positions.add(self.search_matches[self.current_search_index])
        self.current_search_index = index
        if 0 <= self.current_search_index < len(self.search_matches):
            affected_positions.add(self.search_matches[self.current_search_index])
        self._emit_search_updates(affected_positions)

    def is_current_search_match(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False
        if self.current_search_index < 0 or self.current_search_index >= len(self.search_matches):
            return False
        return (index.row(), index.column()) == self.search_matches[self.current_search_index]

    def refresh_column(self, column_index: int) -> None:
        self.headerDataChanged.emit(Qt.Orientation.Horizontal, column_index, column_index)
        if self.rowCount() == 0:
            return
        top_index = self.index(0, column_index)
        bottom_index = self.index(self.rowCount() - 1, column_index)
        self.dataChanged.emit(top_index, bottom_index, [Qt.DisplayRole, Qt.EditRole])

    def refresh_rows(self, row_indexes: list[int]) -> None:
        valid_indexes = sorted({index for index in row_indexes if 0 <= index < self.rowCount()})
        if not valid_indexes:
            return
        self.headerDataChanged.emit(Qt.Orientation.Vertical, valid_indexes[0], valid_indexes[-1])
        for row_index in valid_indexes:
            top_index = self.index(row_index, 0)
            bottom_index = self.index(row_index, max(self.columnCount() - 1, 0))
            self.dataChanged.emit(
                top_index,
                bottom_index,
                [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundRole],
            )

    def _emit_search_updates(self, positions: set[tuple[int, int]]) -> None:
        for row_index, column_index in positions:
            index = self.index(row_index, column_index)
            self.dataChanged.emit(index, index, [Qt.BackgroundRole, Qt.ForegroundRole, Qt.FontRole])

    def _notify_before_project_change(self) -> None:
        if self.before_project_change is not None:
            self.before_project_change()
