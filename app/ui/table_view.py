from PySide6.QtWidgets import QTableView


class DataTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectItems)
        self.setSelectionMode(QTableView.ExtendedSelection)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSortingEnabled(False)
