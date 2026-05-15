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


def test_row_service_deletes_rows_and_cells() -> None:
    project = Project.create_empty(row_count=3, column_count=2)
    deleted_row_id = project.rows[1].id

    affected_rows = RowService().delete_rows(project, [1])

    assert affected_rows == 1
    assert len(project.rows) == 2
    assert all(row.id != deleted_row_id for row in project.rows)
    assert all(row_id != deleted_row_id for row_id, _column_id in project.cells)
    assert [row.order_index for row in project.rows] == [0, 1]
    assert project.dirty is True


def test_row_service_delete_ignores_invalid_indexes() -> None:
    project = Project.create_empty(row_count=1, column_count=1)

    affected_rows = RowService().delete_rows(project, [-1, 2])

    assert affected_rows == 0
    assert len(project.rows) == 1
    assert project.dirty is False
