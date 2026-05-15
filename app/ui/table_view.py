from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QMenu, QTableView


class DataTableView(QTableView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
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
