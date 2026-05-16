from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings


LAST_FILE_DIALOG_DIR_KEY = "file_dialog/last_directory"


def _settings() -> QSettings:
    return QSettings("ZY", "DataAnalysisApp")


def last_file_dialog_dir(default: str = "") -> str:
    value = _settings().value(LAST_FILE_DIALOG_DIR_KEY, default, str)
    if not value:
        return default
    path = Path(value)
    return str(path) if path.exists() and path.is_dir() else default


def remember_file_dialog_path(file_path: str) -> None:
    if not file_path:
        return
    parent = Path(file_path).expanduser().parent
    if parent.exists():
        _settings().setValue(LAST_FILE_DIALOG_DIR_KEY, str(parent))
