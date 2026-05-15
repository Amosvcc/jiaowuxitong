from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QTableView,
    QVBoxLayout,
)

from app.models import DataUpdateAction, DataUpdateDetail
from app.ui.models import DataUpdateDetailTableModel


class DataUpdateDetailDialog(QDialog):
    def __init__(self, details: list[DataUpdateDetail], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("更新详情")
        self.resize(1000, 600)

        self.details = details
        self.table_model = DataUpdateDetailTableModel(details, self)
        self.table_view = QTableView(self)
        self.count_label = QLabel(self)
        self.action_filter_combo = QComboBox(self)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)

        self._setup_ui()
        self._connect_signals()
        self._update_count_label()

    def _setup_ui(self) -> None:
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("类型筛选", self))
        filter_layout.addWidget(self.action_filter_combo)
        filter_layout.addStretch(1)
        filter_layout.addWidget(self.count_label)

        self.action_filter_combo.addItem("全部", None)
        for action, label in DataUpdateDetailTableModel.ACTION_LABELS.items():
            self.action_filter_combo.addItem(label, action)

        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table_view.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout(self)
        layout.addLayout(filter_layout)
        layout.addWidget(self.table_view)
        layout.addWidget(self.button_box)

    def _connect_signals(self) -> None:
        self.action_filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        self.button_box.rejected.connect(self.reject)

    def _on_filter_changed(self) -> None:
        action = self.action_filter_combo.currentData()
        self.table_model.set_action_filter(action)
        self._update_count_label()

    def _update_count_label(self) -> None:
        self.count_label.setText(f"详情数量：{self.table_model.rowCount()}")
