from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def get_qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_smoke() -> None:
    app = get_qapp()
    window = MainWindow()

    try:
        assert window.windowTitle().startswith("ZY专用 V1.0")
        assert window.table_model is not None
        assert window.table_view is not None
    finally:
        window.close()
        app.processEvents()
