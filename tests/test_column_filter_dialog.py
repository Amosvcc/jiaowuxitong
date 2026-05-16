from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.models import ColumnFilterCriteria
from app.ui.dialogs import ColumnFilterDialog


def get_qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def make_dialog(current_criteria=None) -> ColumnFilterDialog:
    get_qapp()
    return ColumnFilterDialog(
        column_id="1",
        column_name="专业",
        unique_values={"会计": 2, "计算机": 1, "": 1},
        current_criteria=current_criteria,
    )


def item_texts(dialog: ColumnFilterDialog) -> list[str]:
    return [dialog.value_list.item(index).text() for index in range(dialog.value_list.count())]


def test_dialog_can_be_created() -> None:
    app = get_qapp()
    dialog = make_dialog()

    assert dialog.windowTitle() == "筛选：专业"
    dialog.close()
    app.processEvents()


def test_dialog_displays_unique_values() -> None:
    dialog = make_dialog()

    assert "会计 (2)" in item_texts(dialog)
    assert "计算机 (1)" in item_texts(dialog)


def test_dialog_displays_counts() -> None:
    dialog = make_dialog()

    assert any(text.endswith("(2)") for text in item_texts(dialog))


def test_dialog_displays_blank_label() -> None:
    dialog = make_dialog()

    assert "空白 (1)" in item_texts(dialog)


def test_dialog_default_state_checks_all_values() -> None:
    dialog = make_dialog()

    assert all(
        dialog.value_list.item(index).checkState() == Qt.CheckState.Checked
        for index in range(dialog.value_list.count())
    )


def test_dialog_generates_criteria_from_checked_values() -> None:
    dialog = make_dialog()
    for index in range(dialog.value_list.count()):
        item = dialog.value_list.item(index)
        item.setCheckState(
            Qt.CheckState.Checked
            if item.data(Qt.ItemDataRole.UserRole) in {"会计", ""}
            else Qt.CheckState.Unchecked
        )

    criteria = dialog.get_criteria()

    assert criteria == ColumnFilterCriteria(
        column_id="1",
        selected_values={"会计"},
        include_blank=True,
    )


def test_dialog_can_invert_visible_checked_values() -> None:
    dialog = make_dialog()
    first_item = dialog.value_list.item(0)
    first_item.setCheckState(Qt.CheckState.Unchecked)

    dialog.invert_selection_button.click()

    assert first_item.checkState() == Qt.CheckState.Checked
    assert all(
        dialog.value_list.item(index).checkState() == Qt.CheckState.Unchecked
        for index in range(1, dialog.value_list.count())
    )


def test_dialog_invert_only_affects_visible_values() -> None:
    dialog = make_dialog()
    hidden_item = dialog.value_list.item(1)
    hidden_item.setHidden(True)
    hidden_item.setCheckState(Qt.CheckState.Checked)

    dialog.invert_selection_button.click()

    assert hidden_item.checkState() == Qt.CheckState.Checked


def test_dialog_clear_current_filter_accepts_as_cleared() -> None:
    dialog = make_dialog(ColumnFilterCriteria(column_id="1", selected_values={"会计"}))

    dialog.clear_current_filter()

    assert dialog.is_cleared is True
    assert dialog.result() == ColumnFilterDialog.DialogCode.Accepted


def test_dialog_cancel_does_not_mark_cleared() -> None:
    dialog = make_dialog(ColumnFilterCriteria(column_id="1", selected_values={"会计"}))

    dialog.reject()

    assert dialog.is_cleared is False
    assert dialog.result() == ColumnFilterDialog.DialogCode.Rejected
