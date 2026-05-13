from pathlib import Path

from app.core import app_base_dir, resource_path, runtime_dir


def test_path_helpers_work_in_source_mode() -> None:
    base_dir = app_base_dir()
    current_runtime_dir = runtime_dir()

    assert base_dir == Path.cwd()
    assert current_runtime_dir == Path.cwd()
    assert resource_path("main.py") == Path.cwd() / "main.py"
