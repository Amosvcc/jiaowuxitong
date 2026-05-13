from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QStatusBar, QToolBar, QVBoxLayout, QWidget

from app.ui.table_model import DataTableModel
from app.ui.table_view import DataTableView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数据分析软件 V1.0")
        self.resize(1200, 800)

        self.table_model = DataTableModel()
        self.table_view = DataTableView()
        self.table_view.setModel(self.table_model)

        self.setup_ui()
        self.setup_toolbar()
        self.setup_statusbar()

    def setup_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.table_view)
        self.setCentralWidget(central_widget)

    def setup_toolbar(self):
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)

        action_new = QAction("新建", self)
        action_import = QAction("导入", self)
        action_save = QAction("保存", self)
        action_add_row = QAction("新增行", self)
        action_add_col = QAction("新增列", self)
        action_statistics = QAction("统计", self)

        toolbar.addAction(action_new)
        toolbar.addAction(action_import)
        toolbar.addAction(action_save)
        toolbar.addSeparator()
        toolbar.addAction(action_add_row)
        toolbar.addAction(action_add_col)
        toolbar.addSeparator()
        toolbar.addAction(action_statistics)

        action_add_row.triggered.connect(self.table_model.add_empty_row)
        action_add_col.triggered.connect(self.table_model.add_empty_column)

    def setup_statusbar(self):
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("就绪")
