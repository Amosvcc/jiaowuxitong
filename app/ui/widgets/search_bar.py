from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget


class SearchBar(QWidget):
    search_requested = Signal(str)
    previous_requested = Signal()
    next_requested = Signal()
    clear_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("搜索...")
        self.previous_button = QPushButton("上一条", self)
        self.next_button = QPushButton("下一条", self)
        self.clear_button = QPushButton("清除", self)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.search_input)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.clear_button)

        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self._connect_signals()

    def _connect_signals(self) -> None:
        self.search_input.returnPressed.connect(self._emit_search_requested)
        self.previous_button.clicked.connect(self.previous_requested.emit)
        self.next_button.clicked.connect(self.next_requested.emit)
        self.clear_button.clicked.connect(self.clear_requested.emit)
        self.search_input.textChanged.connect(self._on_text_changed)

    def _emit_search_requested(self) -> None:
        self.search_requested.emit(self.keyword())

    def _on_text_changed(self, text: str) -> None:
        if not text:
            self.previous_button.setEnabled(False)
            self.next_button.setEnabled(False)

    def keyword(self) -> str:
        return self.search_input.text()

    def clear(self) -> None:
        self.search_input.clear()

    def set_navigation_enabled(self, enabled: bool) -> None:
        self.previous_button.setEnabled(enabled)
        self.next_button.setEnabled(enabled)
