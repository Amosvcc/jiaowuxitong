from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPolygon
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QMenu, QTableView


class FilterHeaderView(QHeaderView):
    filter_indicator_clicked = Signal(int)
    INDICATOR_WIDTH = 20

    def __init__(self, orientation: Qt.Orientation, parent=None) -> None:
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)

    def paintSection(self, painter: QPainter, rect: QRect, logical_index: int) -> None:
        super().paintSection(painter, rect, logical_index)
        if not rect.isValid() or self.orientation() != Qt.Orientation.Horizontal:
            return

        indicator_rect = self.indicator_rect(rect)
        center = indicator_rect.center()
        triangle = QPolygon(
            [
                QPoint(center.x() - 4, center.y() - 2),
                QPoint(center.x() + 4, center.y() - 2),
                QPoint(center.x(), center.y() + 3),
            ]
        )
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#555555")))
        painter.drawPolygon(triangle)
        painter.restore()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            logical_index = self.logicalIndexAt(event.position().toPoint())
            if logical_index >= 0 and self._is_indicator_position(logical_index, event.position().toPoint()):
                self.filter_indicator_clicked.emit(logical_index)
                return
        super().mouseReleaseEvent(event)

    def indicator_rect(self, section_rect: QRect) -> QRect:
        return QRect(
            section_rect.right() - self.INDICATOR_WIDTH + 1,
            section_rect.top(),
            self.INDICATOR_WIDTH,
            section_rect.height(),
        )

    def _is_indicator_position(self, logical_index: int, position: QPoint) -> bool:
        section_rect = QRect(
            self.sectionViewportPosition(logical_index),
            0,
            self.sectionSize(logical_index),
            self.height(),
        )
        return self.indicator_rect(section_rect).contains(position)


class DataTableView(QTableView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setHorizontalHeader(FilterHeaderView(Qt.Orientation.Horizontal, self))
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.AnyKeyPressed
        )
        self.setSortingEnabled(False)

        horizontal_header = self.horizontalHeader()
        horizontal_header.setStretchLastSection(True)
        horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        horizontal_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        vertical_header = self.verticalHeader()
        vertical_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def show_header_menu(
        self,
        global_position,
        column_settings_callback,
        column_filter_callback=None,
        clear_column_filter_callback=None,
        delete_column_callback=None,
    ) -> None:
        menu = QMenu(self)
        column_filter_action = menu.addAction("筛选此列")
        clear_column_filter_action = menu.addAction("清除当前列筛选")
        menu.addSeparator()
        column_settings_action = menu.addAction("列设置")
        delete_column_action = menu.addAction("删除此列")
        chosen_action = menu.exec(global_position)
        if chosen_action == column_filter_action and column_filter_callback is not None:
            column_filter_callback()
        if chosen_action == clear_column_filter_action and clear_column_filter_callback is not None:
            clear_column_filter_callback()
        if chosen_action == column_settings_action:
            column_settings_callback()
        if chosen_action == delete_column_action and delete_column_callback is not None:
            delete_column_callback()

    def show_row_header_menu(
        self,
        global_position,
        terminate_callback,
        restore_callback,
        delete_callback,
    ) -> None:
        menu = QMenu(self)
        terminate_action = menu.addAction("终止此行")
        restore_action = menu.addAction("恢复此行")
        delete_action = menu.addAction("删除此行")
        chosen_action = menu.exec(global_position)
        if chosen_action == terminate_action:
            terminate_callback()
        if chosen_action == restore_action:
            restore_callback()
        if chosen_action == delete_action:
            delete_callback()
