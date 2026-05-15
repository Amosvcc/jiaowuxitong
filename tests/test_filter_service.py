import pytest

from app.models import ColumnFilterCriteria, Project, TableFilterState
from app.services import FilterService


def make_project() -> Project:
    project = Project.create_empty(row_count=5, column_count=2)
    project.columns[0].name = "专业"
    project.columns[1].name = "班级"
    values = [
        ("会计", "1班"),
        ("计算机", "1班"),
        ("会计", "2班"),
        ("", "1班"),
        ("英语", ""),
    ]
    for row_index, (major, class_name) in enumerate(values):
        row = project.rows[row_index]
        project.set_cell_value(row.id, project.columns[0].id, major)
        project.set_cell_value(row.id, project.columns[1].id, class_name)
    project.dirty = False
    return project


def test_get_unique_values_and_counts() -> None:
    project = make_project()

    values = FilterService().get_unique_values(project, str(project.columns[0].id))

    assert values["会计"] == 2
    assert values["计算机"] == 1
    assert values["英语"] == 1


def test_blank_values_are_grouped_as_empty_string() -> None:
    project = make_project()

    values = FilterService().get_unique_values(project, str(project.columns[0].id))

    assert values[""] == 1


def test_single_column_single_value_filter_matches_rows() -> None:
    project = make_project()
    state = TableFilterState(
        filters={
            str(project.columns[0].id): ColumnFilterCriteria(
                column_id=str(project.columns[0].id),
                selected_values={"会计"},
            )
        }
    )

    assert FilterService().get_matching_row_ids(project, state) == {"1", "3"}


def test_single_column_multiple_values_use_or_logic() -> None:
    project = make_project()
    state = TableFilterState(
        filters={
            str(project.columns[0].id): ColumnFilterCriteria(
                column_id=str(project.columns[0].id),
                selected_values={"会计", "计算机"},
            )
        }
    )

    assert FilterService().get_matching_row_ids(project, state) == {"1", "2", "3"}


def test_multiple_columns_use_and_logic() -> None:
    project = make_project()
    state = TableFilterState(
        filters={
            str(project.columns[0].id): ColumnFilterCriteria(
                column_id=str(project.columns[0].id),
                selected_values={"会计"},
            ),
            str(project.columns[1].id): ColumnFilterCriteria(
                column_id=str(project.columns[1].id),
                selected_values={"1班"},
            ),
        }
    )

    assert FilterService().get_matching_row_ids(project, state) == {"1"}


def test_no_filter_matches_all_rows() -> None:
    project = make_project()

    assert FilterService().get_matching_row_ids(project, TableFilterState()) == {
        "1",
        "2",
        "3",
        "4",
        "5",
    }


def test_blank_value_filter_matches_blank_rows() -> None:
    project = make_project()
    state = TableFilterState(
        filters={
            str(project.columns[0].id): ColumnFilterCriteria(
                column_id=str(project.columns[0].id),
                include_blank=True,
            )
        }
    )

    assert FilterService().get_matching_row_ids(project, state) == {"4"}


def test_terminated_rows_are_included_in_unique_values_by_default() -> None:
    project = make_project()
    project.rows[4].is_terminated = True

    values = FilterService().get_unique_values(project, str(project.columns[0].id))

    assert values["英语"] == 1


def test_missing_column_raises_clear_error() -> None:
    project = make_project()

    with pytest.raises(ValueError, match="字段不存在"):
        FilterService().get_unique_values(project, "missing")


def test_filter_does_not_modify_project_dirty_state() -> None:
    project = make_project()
    project.dirty = False
    state = TableFilterState(
        filters={
            str(project.columns[0].id): ColumnFilterCriteria(
                column_id=str(project.columns[0].id),
                selected_values={"会计"},
            )
        }
    )

    service = FilterService()
    service.get_unique_values(project, str(project.columns[0].id))
    service.get_matching_row_ids(project, state)

    assert project.dirty is False
