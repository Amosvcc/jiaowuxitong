import pandas as pd
import pytest

from app.models import Project
from app.services.statistics_service import StatisticsService


def build_project() -> Project:
    project = Project.create_empty(row_count=5, column_count=2)
    project.columns[0].name = "状态"
    project.columns[1].name = "负责人"
    project.set_cell_value(1, 1, "已完成")
    project.set_cell_value(2, 1, "进行中")
    project.set_cell_value(3, 1, "已完成")
    project.set_cell_value(4, 1, "")
    project.set_cell_value(5, 1, "进行中")
    project.rows[4].is_terminated = True
    project.rows[4].terminated_at = "2026-05-14T10:00:00"
    project.dirty = False
    return project


def test_statistics_service_counts_single_field() -> None:
    project = build_project()

    items = StatisticsService().generate_statistics(
        project,
        column_index=0,
        include_terminated=True,
        ignore_empty=True,
    )

    assert [(item.value, item.count) for item in items] == [("已完成", 2), ("进行中", 2)]


def test_statistics_service_calculates_ratio() -> None:
    project = build_project()

    items = StatisticsService().generate_statistics(
        project,
        column_index=0,
        include_terminated=True,
        ignore_empty=True,
    )

    assert [round(item.ratio, 4) for item in items] == [0.5, 0.5]


def test_statistics_service_sorts_by_count_descending() -> None:
    project = Project.create_empty(row_count=4, column_count=1)
    project.columns[0].name = "状态"
    project.set_cell_value(1, 1, "已完成")
    project.set_cell_value(2, 1, "已完成")
    project.set_cell_value(3, 1, "进行中")
    project.set_cell_value(4, 1, "未开始")

    items = StatisticsService().generate_statistics(
        project,
        column_index=0,
        include_terminated=True,
        ignore_empty=True,
    )

    assert [(item.value, item.count) for item in items] == [
        ("已完成", 2),
        ("未开始", 1),
        ("进行中", 1),
    ]


def test_statistics_service_sorts_by_value_when_count_equal() -> None:
    project = Project.create_empty(row_count=2, column_count=1)
    project.set_cell_value(1, 1, "B")
    project.set_cell_value(2, 1, "A")

    items = StatisticsService().generate_statistics(
        project,
        column_index=0,
        include_terminated=True,
        ignore_empty=True,
    )

    assert [item.value for item in items] == ["A", "B"]


def test_statistics_service_ignore_empty_excludes_empty_values() -> None:
    project = build_project()

    items = StatisticsService().generate_statistics(
        project,
        column_index=0,
        include_terminated=True,
        ignore_empty=True,
    )

    assert all(item.value != "<空值>" for item in items)


def test_statistics_service_include_empty_uses_empty_label() -> None:
    project = build_project()

    items = StatisticsService().generate_statistics(
        project,
        column_index=0,
        include_terminated=True,
        ignore_empty=False,
    )

    assert [(item.value, item.count) for item in items] == [
        ("已完成", 2),
        ("进行中", 2),
        ("<空值>", 1),
    ]


def test_statistics_service_can_exclude_terminated_rows() -> None:
    project = build_project()

    items = StatisticsService().generate_statistics(
        project,
        column_index=0,
        include_terminated=False,
        ignore_empty=True,
    )

    assert [(item.value, item.count) for item in items] == [("已完成", 2), ("进行中", 1)]


def test_statistics_service_includes_terminated_rows_when_requested() -> None:
    project = build_project()

    items = StatisticsService().generate_statistics(
        project,
        column_index=0,
        include_terminated=True,
        ignore_empty=True,
    )

    assert [(item.value, item.count) for item in items] == [("已完成", 2), ("进行中", 2)]


def test_statistics_service_returns_empty_when_no_data() -> None:
    project = Project.create_empty(row_count=2, column_count=1)

    items = StatisticsService().generate_statistics(
        project,
        column_index=0,
        include_terminated=True,
        ignore_empty=True,
    )

    assert items == []


def test_statistics_service_rejects_invalid_column_index() -> None:
    project = Project.create_empty(row_count=1, column_count=1)

    with pytest.raises(ValueError, match="列索引超出范围"):
        StatisticsService().generate_statistics(
            project,
            column_index=2,
            include_terminated=True,
            ignore_empty=True,
        )


def test_statistics_service_does_not_modify_project_dirty() -> None:
    project = build_project()

    StatisticsService().generate_statistics(
        project,
        column_index=0,
        include_terminated=True,
        ignore_empty=True,
    )

    assert project.dirty is False


def test_statistics_service_exports_csv(workspace_tmp_path) -> None:
    service = StatisticsService()
    project = build_project()
    export_path = workspace_tmp_path / "统计结果.csv"
    items = service.generate_statistics(
        project,
        column_index=0,
        include_terminated=True,
        ignore_empty=False,
    )

    service.export_statistics(
        str(export_path),
        "状态",
        items,
        include_terminated=True,
        ignore_empty=False,
    )

    exported = pd.read_csv(export_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    assert exported.columns.tolist() == ["统计字段", "字段值", "数量", "占比", "包含已终止行", "忽略空值"]
    assert exported.iloc[0].to_dict() == {
        "统计字段": "状态",
        "字段值": "已完成",
        "数量": "2",
        "占比": "40.00%",
        "包含已终止行": "是",
        "忽略空值": "否",
    }


def test_statistics_service_exports_excel(workspace_tmp_path) -> None:
    service = StatisticsService()
    project = build_project()
    export_path = workspace_tmp_path / "统计结果.xlsx"
    items = service.generate_statistics(
        project,
        column_index=0,
        include_terminated=False,
        ignore_empty=True,
    )

    service.export_statistics(
        str(export_path),
        "状态",
        items,
        include_terminated=False,
        ignore_empty=True,
    )

    exported = pd.read_excel(export_path, dtype=str, keep_default_na=False)
    assert exported.iloc[0].to_dict() == {
        "统计字段": "状态",
        "字段值": "已完成",
        "数量": "2",
        "占比": "66.67%",
        "包含已终止行": "否",
        "忽略空值": "是",
    }
