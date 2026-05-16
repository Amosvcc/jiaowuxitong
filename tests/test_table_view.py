from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QApplication

from app.ui.table_view import DataTableView, FilterHeaderView


def get_qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_table_view_uses_filter_header_view() -> None:
    app = get_qapp()
    view = DataTableView()

    try:
        assert isinstance(view.horizontalHeader(), FilterHeaderView)
    finally:
        view.close()
        app.processEvents()


def test_filter_header_indicator_rect_is_on_right_side() -> None:
    app = get_qapp()
    header = FilterHeaderView(Qt.Orientation.Horizontal)
    section_rect = QRect(0, 0, 120, 30)

    try:
        indicator_rect = header.indicator_rect(section_rect)

        assert indicator_rect.right() == section_rect.right()
        assert indicator_rect.width() == FilterHeaderView.INDICATOR_WIDTH
    finally:
        header.close()
        app.processEvents()
