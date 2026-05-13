from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture
def workspace_tmp_path() -> Path:
    with TemporaryDirectory(dir=Path.cwd()) as temp_dir:
        yield Path(temp_dir)
