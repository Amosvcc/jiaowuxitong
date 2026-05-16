from pathlib import Path

from app.core import file_dialog_state


class FakeSettings:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def value(self, key: str, default: str = "", _type=str) -> str:
        return self.values.get(key, default)

    def setValue(self, key: str, value: str) -> None:
        self.values[key] = value


def test_file_dialog_state_remembers_selected_parent(monkeypatch, workspace_tmp_path) -> None:
    settings = FakeSettings()
    selected_file = workspace_tmp_path / "数据.csv"
    selected_file.write_text("", encoding="utf-8")
    monkeypatch.setattr(file_dialog_state, "_settings", lambda: settings)

    file_dialog_state.remember_file_dialog_path(str(selected_file))

    assert file_dialog_state.last_file_dialog_dir() == str(workspace_tmp_path)


def test_file_dialog_state_ignores_missing_directory(monkeypatch) -> None:
    settings = FakeSettings()
    settings.setValue(
        file_dialog_state.LAST_FILE_DIALOG_DIR_KEY,
        str(Path("Z:/missing/path")),
    )
    monkeypatch.setattr(file_dialog_state, "_settings", lambda: settings)

    assert file_dialog_state.last_file_dialog_dir("fallback") == "fallback"
