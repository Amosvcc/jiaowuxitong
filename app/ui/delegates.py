from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QStyledItemDelegate, QWidget

from app.ui.table_model import DataTableModel


class DataColumnDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option, index):
        model = index.model()
        if not isinstance(model, DataTableModel):
            return super().createEditor(parent, option, index)

        column = model.columns[index.column()]
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

        model = index.model()
        if not isinstance(model, DataTableModel):
            return

        column = model.columns[index.column()]
        current_value = str(model.data(index))

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
