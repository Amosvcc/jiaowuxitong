from PySide6.QtWidgets import QApplication

from app.models import Column
from app.ui.dialogs import ColumnSettingsDialog


def get_qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_column_settings_dialog_loads_column_data() -> None:
    app = get_qapp()
    dialog = ColumnSettingsDialog(
        Column(
            id=1,
            name="状态",
            field_type="dropdown",
            dropdown_options=["进行中", "已完成"],
            allow_custom_value=False,
        )
    )

    try:
        assert dialog.name_input.text() == "状态"
        assert dialog.field_type_combo.currentData() == "dropdown"
        assert dialog.dropdown_options_edit.toPlainText() == "进行中\n已完成"
        assert dialog.allow_custom_value_checkbox.isChecked() is False
        assert dialog.dropdown_options_edit.isEnabled() is True
    finally:
        dialog.close()
        app.processEvents()


def test_column_settings_dialog_cancel_does_not_apply_changes() -> None:
    app = get_qapp()
    column = Column(id=1, name="原列名")
    dialog = ColumnSettingsDialog(column)
    dialog.name_input.setText("新列名")

    try:
        dialog.reject()
        assert column.name == "原列名"
    finally:
        dialog.close()
        app.processEvents()
