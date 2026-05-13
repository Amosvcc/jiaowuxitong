from app.models import Project
from app.services.row_service import RowService


def test_row_service_terminates_single_row() -> None:
    project = Project.create_empty(row_count=2, column_count=1)

    affected_rows = RowService().terminate_rows(project, [0])

    assert affected_rows == 1
    assert project.rows[0].is_terminated is True
    assert project.rows[0].terminated_at is not None
    assert project.dirty is True


def test_row_service_restores_single_row() -> None:
    project = Project.create_empty(row_count=1, column_count=1)
    project.rows[0].is_terminated = True
    project.rows[0].terminated_at = "2026-05-14T10:00:00"
    project.dirty = False

    affected_rows = RowService().restore_rows(project, [0])

    assert affected_rows == 1
    assert project.rows[0].is_terminated is False
    assert project.rows[0].terminated_at is None
    assert project.dirty is True


def test_row_service_can_batch_terminate_and_restore() -> None:
    project = Project.create_empty(row_count=3, column_count=1)
    service = RowService()

    terminated_count = service.terminate_rows(project, [0, 2])
    restored_count = service.restore_rows(project, [0, 2])

    assert terminated_count == 2
    assert restored_count == 2
    assert [row.is_terminated for row in project.rows] == [False, False, False]


def test_row_service_repeated_operations_do_not_fail() -> None:
    project = Project.create_empty(row_count=1, column_count=1)
    service = RowService()

    service.terminate_rows(project, [0])
    terminated_count = service.terminate_rows(project, [0])
    service.restore_rows(project, [0])
    restored_count = service.restore_rows(project, [0])

    assert terminated_count == 1
    assert restored_count == 1
    assert project.rows[0].is_terminated is False


def test_row_service_ignores_invalid_indexes() -> None:
    project = Project.create_empty(row_count=1, column_count=1)

    affected_rows = RowService().terminate_rows(project, [-1, 3])

    assert affected_rows == 0
    assert project.rows[0].is_terminated is False
