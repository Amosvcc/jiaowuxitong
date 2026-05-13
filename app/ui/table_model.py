from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class DataTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.columns = ["字段1", "字段2", "字段3"]
        self.data_rows = [
            ["", "", ""],
            ["", "", ""],
            ["", "", ""],
        ]

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.data_rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.data_rows[row][col]

        return None

    def setData(self, index, value, role=Qt.EditRole) -> bool:
        if not index.isValid() or role != Qt.EditRole:
            return False

        row = index.row()
        col = index.column()
        self.data_rows[row][col] = str(value)
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self.columns[section]

        return str(section + 1)

    def add_empty_row(self):
        row_index = len(self.data_rows)
        self.beginInsertRows(QModelIndex(), row_index, row_index)
        self.data_rows.append(["" for _ in self.columns])
        self.endInsertRows()

    def add_empty_column(self):
        col_index = len(self.columns)
        self.beginInsertColumns(QModelIndex(), col_index, col_index)
        self.columns.append(f"字段{col_index + 1}")
        for row in self.data_rows:
            row.append("")
        self.endInsertColumns()
