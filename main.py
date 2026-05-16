import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.core import resource_path
from app.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    icon_path = resource_path("icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
