from app.models import Project
from app.services import UndoService


def test_undo_service_pushes_and_pops_project_snapshot() -> None:
    project = Project.create_empty(row_count=1, column_count=1)
    service = UndoService()

    service.push_snapshot(project)
    project.set_cell_value(1, 1, "新值")

    restored = service.pop_snapshot()

    assert restored is not None
    assert restored.get_cell_value(1, 1) == ""
    assert service.can_undo is False


def test_undo_service_discards_latest_snapshot() -> None:
    project = Project.create_empty(row_count=1, column_count=1)
    service = UndoService()

    service.push_snapshot(project)
    service.discard_latest()

    assert service.pop_snapshot() is None


def test_undo_service_limits_snapshot_count() -> None:
    project = Project.create_empty(row_count=1, column_count=1)
    service = UndoService(max_snapshots=1)

    service.push_snapshot(project)
    project.set_cell_value(1, 1, "保留")
    service.push_snapshot(project)

    restored = service.pop_snapshot()

    assert restored is not None
    assert restored.get_cell_value(1, 1) == "保留"
    assert service.can_undo is False
