import pandas as pd
import pytest

from app.models import PivotResult, Project
from app.services.pivot_service import PivotService


def build_basic_project() -> Project:
    project = Project.create_empty(row_count=6, column_count=3)
    project.columns[0].name = "学号"
    project.columns[1].name = "班级"
    project.columns[2].name = "性别"
    project.set_cell_value(1, 1, "001")
    project.set_cell_value(1, 2, "一班")
    project.set_cell_value(1, 3, "男")
    project.set_cell_value(2, 1, "002")
    project.set_cell_value(2, 2, "一班")
    project.set_cell_value(2, 3, "女")
    project.set_cell_value(3, 1, "003")
    project.set_cell_value(3, 2, "二班")
    project.set_cell_value(3, 3, "男")
    project.set_cell_value(4, 1, "004")
    project.set_cell_value(4, 2, "二班")
    project.set_cell_value(4, 3, "女")
    project.set_cell_value(5, 1, "005")
    project.set_cell_value(5, 2, "二班")
    project.set_cell_value(5, 3, "女")
    project.set_cell_value(6, 1, "006")
    project.set_cell_value(6, 2, "")
    project.set_cell_value(6, 3, "")
    project.rows[4].is_terminated = True
    project.rows[4].terminated_at = "2026-05-15T10:00:00"
    project.dirty = False
    return project


def build_tag_project() -> Project:
    project = Project.create_empty(row_count=4, column_count=3)
    project.columns[0].name = "姓名"
    project.columns[1].name = "班级"
    project.columns[2].name = "兴趣标签"
    project.set_cell_value(1, 1, "张三")
    project.set_cell_value(1, 2, "一班")
    project.set_cell_value(1, 3, "篮球;音乐")
    project.set_cell_value(2, 1, "李四")
    project.set_cell_value(2, 2, "一班")
    project.set_cell_value(2, 3, "音乐")
    project.set_cell_value(3, 1, "王五")
    project.set_cell_value(3, 2, "二班")
    project.set_cell_value(3, 3, "篮球;绘画")
    project.set_cell_value(4, 1, "赵六")
    project.set_cell_value(4, 2, "二班")
    project.set_cell_value(4, 3, "篮球，篮球、 音乐 / 绘画|\n编程;;")
    project.dirty = False
    return project


def test_pivot_service_generates_two_dimensional_counts() -> None:
    result = PivotService().build_pivot(
        build_basic_project(),
        row_field="班级",
        column_field="性别",
        include_terminated_rows=True,
    )

    assert result.matrix == {
        "一班": {"男": 1, "女": 1},
        "二班": {"男": 1, "女": 2},
    }


def test_pivot_service_preserves_row_header_order() -> None:
    result = PivotService().build_pivot(
        build_basic_project(),
        row_field="班级",
        column_field="性别",
        include_terminated_rows=True,
    )

    assert result.row_headers == ["一班", "二班"]


def test_pivot_service_preserves_column_header_order() -> None:
    result = PivotService().build_pivot(
        build_basic_project(),
        row_field="班级",
        column_field="性别",
        include_terminated_rows=True,
    )

    assert result.column_headers == ["男", "女"]


def test_pivot_service_calculates_row_totals() -> None:
    result = PivotService().build_pivot(
        build_basic_project(),
        row_field="班级",
        column_field="性别",
        include_terminated_rows=True,
    )

    assert result.row_totals == {"一班": 2, "二班": 3}


def test_pivot_service_calculates_column_totals() -> None:
    result = PivotService().build_pivot(
        build_basic_project(),
        row_field="班级",
        column_field="性别",
        include_terminated_rows=True,
    )

    assert result.column_totals == {"男": 2, "女": 3}


def test_pivot_service_calculates_grand_total() -> None:
    result = PivotService().build_pivot(
        build_basic_project(),
        row_field="班级",
        column_field="性别",
        include_terminated_rows=True,
    )

    assert result.grand_total == 5


def test_pivot_service_ignores_empty_row_values_by_default() -> None:
    result = PivotService().build_pivot(
        build_basic_project(),
        row_field="班级",
        column_field="性别",
        include_terminated_rows=True,
    )

    assert "" not in result.row_headers
    assert result.skipped_empty_row_values == 1


def test_pivot_service_ignores_empty_column_values_by_default() -> None:
    project = build_basic_project()
    project.set_cell_value(6, 2, "三班")

    result = PivotService().build_pivot(
        project,
        row_field="班级",
        column_field="性别",
        include_terminated_rows=True,
    )

    assert "" not in result.column_headers
    assert result.skipped_empty_column_values == 1


def test_pivot_service_skips_terminated_rows_by_default() -> None:
    result = PivotService().build_pivot(
        build_basic_project(),
        row_field="班级",
        column_field="性别",
    )

    assert result.matrix == {
        "一班": {"男": 1, "女": 1},
        "二班": {"男": 1, "女": 1},
    }
    assert result.skipped_terminated_rows == 1


def test_pivot_service_can_include_terminated_rows() -> None:
    result = PivotService().build_pivot(
        build_basic_project(),
        row_field="班级",
        column_field="性别",
        include_terminated_rows=True,
    )

    assert result.matrix["二班"]["女"] == 2
    assert result.skipped_terminated_rows == 0


def test_pivot_service_uses_full_cell_when_not_expanding_tags() -> None:
    result = PivotService().build_pivot(
        build_tag_project(),
        row_field="班级",
        column_field="兴趣标签",
        expand_column_tags=False,
        include_terminated_rows=True,
    )

    assert result.column_headers == [
        "篮球;音乐",
        "音乐",
        "篮球;绘画",
        "篮球，篮球、 音乐 / 绘画|\n编程;;",
    ]


def test_pivot_service_expands_tags_when_enabled() -> None:
    result = PivotService().build_pivot(
        build_tag_project(),
        row_field="班级",
        column_field="兴趣标签",
        expand_column_tags=True,
        include_terminated_rows=True,
    )

    assert result.column_headers == ["篮球", "音乐", "绘画", "编程"]
    assert result.matrix["一班"] == {"篮球": 1, "音乐": 2}
    assert result.matrix["二班"] == {"篮球": 2, "绘画": 2, "音乐": 1, "编程": 1}


def test_pivot_service_expands_tags_with_multiple_separators() -> None:
    result = PivotService().build_pivot(
        build_tag_project(),
        row_field="班级",
        column_field="兴趣标签",
        expand_column_tags=True,
        include_terminated_rows=True,
    )

    assert result.column_headers == ["篮球", "音乐", "绘画", "编程"]


def test_pivot_service_ignores_empty_tags_when_expanding() -> None:
    project = build_tag_project()
    project.set_cell_value(2, 3, " ; ； ,, ")

    result = PivotService().build_pivot(
        project,
        row_field="班级",
        column_field="兴趣标签",
        expand_column_tags=True,
        include_terminated_rows=True,
    )

    assert "" not in result.column_headers
    assert result.skipped_empty_column_values == 1


def test_pivot_service_deduplicates_duplicate_tags_within_one_cell() -> None:
    result = PivotService().build_pivot(
        build_tag_project(),
        row_field="班级",
        column_field="兴趣标签",
        expand_column_tags=True,
        include_terminated_rows=True,
    )

    assert result.matrix["二班"]["篮球"] == 2


def test_pivot_service_raises_clear_error_when_field_missing() -> None:
    with pytest.raises(ValueError, match="字段不存在"):
        PivotService().build_pivot(
            build_basic_project(),
            row_field="不存在字段",
            column_field="性别",
        )


def test_pivot_service_does_not_modify_project_dirty() -> None:
    project = build_basic_project()

    PivotService().build_pivot(
        project,
        row_field="班级",
        column_field="性别",
        include_terminated_rows=True,
    )

    assert project.dirty is False


def test_pivot_service_builds_dataframe_for_export() -> None:
    result = PivotResult(
        row_field="班级",
        column_field="性别",
        row_headers=["一班", "二班"],
        column_headers=["男", "女"],
        matrix={"一班": {"男": 1, "女": 1}, "二班": {"男": 1, "女": 2}},
        row_totals={"一班": 2, "二班": 3},
        column_totals={"男": 2, "女": 3},
        grand_total=5,
        show_row_totals=True,
        show_column_totals=True,
    )

    dataframe = PivotService().build_pivot_dataframe(result)

    assert dataframe.columns.tolist() == ["班级", "男", "女", "合计"]
    assert dataframe.to_dict("records") == [
        {"班级": "一班", "男": 1, "女": 1, "合计": 2},
        {"班级": "二班", "男": 1, "女": 2, "合计": 3},
        {"班级": "合计", "男": 2, "女": 3, "合计": 5},
    ]
