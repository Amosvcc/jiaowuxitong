from __future__ import annotations

from copy import copy

from PySide6.QtCore import QSortFilterProxyModel
from PySide6.QtWidgets import QComboBox, QStyle, QStyledItemDelegate, QWidget

from app.ui.table_model import DataTableModel


class DataColumnDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index) -> None:
        model, source_index = self._source_model_and_index(index)
        if model is not None and model.is_current_search_match(source_index):
            option = copy(option)
            option.state &= ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, index)

    def createEditor(self, parent: QWidget, option, index):
        model, source_index = self._source_model_and_index(index)
        if model is None:
            return super().createEditor(parent, option, index)

        column = model.columns[source_index.column()]
        if column.field_type != "dropdown":
            return super().createEditor(parent, option, index)

        combo_box = QComboBox(parent)
        combo_box.addItems(column.dropdown_options)
        combo_box.setEditable(column.allow_custom_value)
        return combo_box

    def setEditorData(self, editor: QWidget, index) -> None:
        if not isinstance(editor, QComboBox):
            super().setEditorData(editor, index)
            return

        model, source_index = self._source_model_and_index(index)
        if model is None:
            return

        column = model.columns[source_index.column()]
        current_value = str(model.data(source_index))

        if column.allow_custom_value:
            if current_value and editor.findText(current_value) == -1:
                editor.addItem(current_value)
            editor.setCurrentText(current_value)
            return

        option_index = editor.findText(current_value)
        editor.setCurrentIndex(option_index if option_index >= 0 else 0)

    def setModelData(self, editor: QWidget, model, index) -> None:
        if not isinstance(editor, QComboBox):
            super().setModelData(editor, model, index)
            return

        model.setData(index, editor.currentText())

    def _source_model_and_index(self, index):
        model = index.model()
        if isinstance(model, DataTableModel):
            return model, index
        if isinstance(model, QSortFilterProxyModel) and isinstance(model.sourceModel(), DataTableModel):
            return model.sourceModel(), model.mapToSource(index)
        return None, index
