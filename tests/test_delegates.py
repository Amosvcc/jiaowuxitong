from PySide6.QtWidgets import QApplication, QComboBox

from app.models import Project
from app.ui.delegates import DataColumnDelegate
from app.ui.table_model import DataTableModel


def get_qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_delegate_uses_combobox_for_dropdown_column() -> None:
    app = get_qapp()
    project = Project.create_empty(row_count=1, column_count=1)
    project.columns[0].field_type = "dropdown"
    project.columns[0].dropdown_options = ["进行中", "已完成"]
    project.columns[0].allow_custom_value = True
    model = DataTableModel(project)
    delegate = DataColumnDelegate()

    editor = delegate.createEditor(None, None, model.index(0, 0))

    assert isinstance(editor, QComboBox)
    assert editor.isEditable() is True
    app.processEvents()


def test_delegate_combobox_not_editable_when_custom_value_disallowed() -> None:
    app = get_qapp()
    project = Project.create_empty(row_count=1, column_count=1)
    project.columns[0].field_type = "dropdown"
    project.columns[0].dropdown_options = ["进行中", "已完成"]
    project.columns[0].allow_custom_value = False
    model = DataTableModel(project)
    delegate = DataColumnDelegate()

    editor = delegate.createEditor(None, None, model.index(0, 0))

    assert isinstance(editor, QComboBox)
    assert editor.isEditable() is False
    app.processEvents()


def test_delegate_keeps_custom_value_when_allowed() -> None:
    app = get_qapp()
    project = Project.create_empty(row_count=1, column_count=1)
    project.columns[0].field_type = "dropdown"
    project.columns[0].dropdown_options = ["进行中", "已完成"]
    project.columns[0].allow_custom_value = True
    project.set_cell_value(1, 1, "自定义值")
    model = DataTableModel(project)
    delegate = DataColumnDelegate()
    editor = delegate.createEditor(None, None, model.index(0, 0))

    delegate.setEditorData(editor, model.index(0, 0))

    assert isinstance(editor, QComboBox)
    assert editor.currentText() == "自定义值"
    app.processEvents()
