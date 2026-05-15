import pytest

from app.core import DuplicateMatchKeyError
from app.models import DataUpdateAction, Project
from app.services import DataUpdateService


def build_target_project() -> Project:
    project = Project.create_empty(row_count=3, column_count=3)
    project.columns[0].name = "学号"
    project.columns[1].name = "姓名"
    project.columns[2].name = "班级"
    project.set_cell_value(1, 1, "1001")
    project.set_cell_value(1, 2, "张三")
    project.set_cell_value(1, 3, "")
    project.set_cell_value(2, 1, "1002")
    project.set_cell_value(2, 2, "李四")
    project.set_cell_value(2, 3, "一班")
    project.set_cell_value(3, 1, "")
    project.set_cell_value(3, 2, "空键")
    project.set_cell_value(3, 3, "")
    project.dirty = False
    return project


def test_update_by_student_id_adds_missing_column() -> None:
    project = build_target_project()

    result = DataUpdateService().update_project_from_table(
        project,
        ["学号", "成绩"],
        [["1001", "90"], ["1002", "88"]],
        "学号",
        "学号",
    )

    score_column = next(column for column in project.columns if column.name == "成绩")
    assert result.matched_rows == 2
    assert result.added_columns == ["成绩"]
    assert result.updated_cells == 2
    assert project.get_cell_value(1, score_column.id) == "90"
    assert project.get_cell_value(2, score_column.id) == "88"
    assert any(
        detail.action == DataUpdateAction.ADD_COLUMN and detail.column_name == "成绩"
        for detail in result.details
    )


def test_update_by_student_id_fills_empty_value_without_overwriting_existing() -> None:
    project = build_target_project()

    result = DataUpdateService().update_project_from_table(
        project,
        ["学号", "班级"],
        [["1001", "二班"], ["1002", "三班"]],
        "学号",
        "学号",
    )

    assert result.updated_cells == 1
    assert result.skipped_existing_values == 1
    assert project.get_cell_value(1, 3) == "二班"
    assert project.get_cell_value(2, 3) == "一班"


def test_overwrite_existing_false_keeps_old_value() -> None:
    project = build_target_project()

    result = DataUpdateService().update_project_from_table(
        project,
        ["学号", "姓名"],
        [["1001", "新张三"]],
        "学号",
        "学号",
        overwrite_existing=False,
    )

    assert result.updated_cells == 0
    assert result.skipped_existing_values == 1
    assert project.get_cell_value(1, 2) == "张三"


def test_overwrite_existing_true_replaces_old_value() -> None:
    project = build_target_project()

    result = DataUpdateService().update_project_from_table(
        project,
        ["学号", "姓名"],
        [["1001", "新张三"]],
        "学号",
        "学号",
        overwrite_existing=True,
    )

    assert result.updated_cells == 1
    assert project.get_cell_value(1, 2) == "新张三"
    assert any(
        detail.action == DataUpdateAction.UPDATE_CELL
        and detail.column_name == "姓名"
        and detail.old_value == "张三"
        and detail.new_value == "新张三"
        for detail in result.details
    )


def test_ignore_empty_values_true_does_not_overwrite_target() -> None:
    project = build_target_project()

    result = DataUpdateService().update_project_from_table(
        project,
        ["学号", "姓名"],
        [["1001", ""]],
        "学号",
        "学号",
        overwrite_existing=True,
        ignore_empty_values=True,
    )

    assert result.updated_cells == 0
    assert result.skipped_empty_values == 1
    assert project.get_cell_value(1, 2) == "张三"
    assert any(detail.action == DataUpdateAction.SKIP_EMPTY for detail in result.details)


def test_add_missing_columns_false_skips_unknown_columns() -> None:
    project = build_target_project()

    result = DataUpdateService().update_project_from_table(
        project,
        ["学号", "成绩"],
        [["1001", "90"]],
        "学号",
        "学号",
        add_missing_columns=False,
    )

    assert result.added_columns == []
    assert result.updated_cells == 0
    assert [column.name for column in project.columns] == ["学号", "姓名", "班级"]


def test_append_unmatched_rows_true_appends_new_row() -> None:
    project = build_target_project()

    result = DataUpdateService().update_project_from_table(
        project,
        ["学号", "姓名", "班级"],
        [["1003", "王五", "三班"]],
        "学号",
        "学号",
        append_unmatched_rows=True,
    )

    assert result.unmatched_source_rows == 1
    assert result.appended_rows == 1
    assert len(project.rows) == 4
    assert project.get_cell_value(4, 1) == "1003"
    assert project.get_cell_value(4, 2) == "王五"
    assert project.get_cell_value(4, 3) == "三班"
    assert any(detail.action == DataUpdateAction.APPEND_ROW for detail in result.details)


def test_append_unmatched_rows_false_ignores_new_row() -> None:
    project = build_target_project()

    result = DataUpdateService().update_project_from_table(
        project,
        ["学号", "姓名"],
        [["1003", "王五"]],
        "学号",
        "学号",
        append_unmatched_rows=False,
    )

    assert result.unmatched_source_rows == 1
    assert result.appended_rows == 0
    assert len(project.rows) == 3
    assert any(detail.action == DataUpdateAction.UNMATCHED_ROW for detail in result.details)


def test_duplicate_target_keys_block_update() -> None:
    project = build_target_project()
    project.set_cell_value(3, 1, "1001")

    with pytest.raises(DuplicateMatchKeyError, match="主表匹配字段存在重复值"):
        DataUpdateService().update_project_from_table(
            project,
            ["学号", "姓名"],
            [["1001", "新张三"]],
            "学号",
            "学号",
        )


def test_duplicate_source_keys_block_update() -> None:
    project = build_target_project()

    with pytest.raises(DuplicateMatchKeyError, match="更新表匹配字段存在重复值"):
        DataUpdateService().update_project_from_table(
            project,
            ["学号", "姓名"],
            [["1001", "张三"], ["1001", "张三2"]],
            "学号",
            "学号",
        )


def test_empty_key_does_not_participate_in_matching() -> None:
    project = build_target_project()

    result = DataUpdateService().update_project_from_table(
        project,
        ["学号", "姓名"],
        [["", "无效"], ["1001", "新张三"]],
        "学号",
        "学号",
        overwrite_existing=True,
    )

    assert result.matched_rows == 1
    assert result.unmatched_source_rows == 0
    assert project.get_cell_value(3, 2) == "空键"


def test_terminated_rows_are_not_updated_by_default() -> None:
    project = build_target_project()
    project.rows[0].is_terminated = True

    result = DataUpdateService().update_project_from_table(
        project,
        ["学号", "班级"],
        [["1001", "终止班级"]],
        "学号",
        "学号",
        overwrite_existing=True,
    )

    assert result.updated_cells == 0
    assert result.skipped_terminated_rows == 1
    assert project.get_cell_value(1, 3) == ""
    assert any(detail.action == DataUpdateAction.SKIP_TERMINATED for detail in result.details)


def test_terminated_rows_can_be_updated_when_enabled() -> None:
    project = build_target_project()
    project.rows[0].is_terminated = True

    result = DataUpdateService().update_project_from_table(
        project,
        ["学号", "班级"],
        [["1001", "终止班级"]],
        "学号",
        "学号",
        overwrite_existing=True,
        update_terminated_rows=True,
    )

    assert result.updated_cells == 1
    assert project.get_cell_value(1, 3) == "终止班级"


def test_no_actual_change_does_not_mark_dirty() -> None:
    project = build_target_project()

    result = DataUpdateService().update_project_from_table(
        project,
        ["学号", "姓名"],
        [["1001", "张三"]],
        "学号",
        "学号",
        overwrite_existing=False,
    )

    assert result.has_changes is False
    assert project.dirty is False


def test_actual_change_leaves_dirty_to_caller() -> None:
    project = build_target_project()

    result = DataUpdateService().update_project_from_table(
        project,
        ["学号", "班级"],
        [["1001", "二班"]],
        "学号",
        "学号",
    )

    assert result.has_changes is True
    assert result.updated_cells == 1
    assert project.dirty is False


def test_skip_existing_generates_detail() -> None:
    project = build_target_project()

    result = DataUpdateService().update_project_from_table(
        project,
        ["学号", "班级"],
        [["1002", "二班"]],
        "学号",
        "学号",
        overwrite_existing=False,
    )

    assert result.skipped_existing_values == 1
    assert any(
        detail.action == DataUpdateAction.SKIP_EXISTING
        and detail.key_value == "1002"
        and detail.column_name == "班级"
        for detail in result.details
    )
