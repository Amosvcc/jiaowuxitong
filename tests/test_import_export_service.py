import pandas as pd
import pytest

from app.services import ImportExportService


def test_import_service_normalizes_empty_and_duplicate_headers(workspace_tmp_path) -> None:
    path = workspace_tmp_path / "headers.csv"
    path.write_text("状态,,状态\n进行中,,已完成\n", encoding="utf-8-sig")

    project = ImportExportService().import_file(str(path))

    assert [column.name for column in project.columns] == ["状态", "字段2", "状态_2"]
    assert project.get_cell_value(1, 2) == ""
    assert all(row.is_terminated is False for row in project.rows)
    assert all(column.field_type == "text" for column in project.columns)


def test_import_service_exports_csv_in_current_order(workspace_tmp_path) -> None:
    service = ImportExportService()
    project = service.import_file(_build_csv_file(workspace_tmp_path / "source.csv"))
    export_path = workspace_tmp_path / "导出结果.csv"

    service.export_file(project, str(export_path))

    exported = pd.read_csv(export_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    assert exported.columns.tolist() == ["姓名", "状态"]
    assert exported.values.tolist() == [["张三", "进行中"], ["李四", "已完成"]]


def test_import_service_exports_excel_in_current_order(workspace_tmp_path) -> None:
    service = ImportExportService()
    project = service.import_file(_build_csv_file(workspace_tmp_path / "source.csv"))
    export_path = workspace_tmp_path / "导出结果.xlsx"

    service.export_file(project, str(export_path))

    exported = pd.read_excel(export_path, dtype=str, keep_default_na=False)
    assert exported.columns.tolist() == ["姓名", "状态"]
    assert exported.values.tolist() == [["张三", "进行中"], ["李四", "已完成"]]


def test_export_includes_terminated_rows(workspace_tmp_path) -> None:
    service = ImportExportService()
    project = service.import_file(_build_csv_file(workspace_tmp_path / "source.csv"))
    project.rows[1].is_terminated = True
    export_path = workspace_tmp_path / "terminated.csv"

    service.export_file(project, str(export_path))

    exported = pd.read_csv(export_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    assert exported.values.tolist() == [["张三", "进行中"], ["李四", "已完成"]]


def test_import_service_rejects_unsupported_format(workspace_tmp_path) -> None:
    path = workspace_tmp_path / "unsupported.txt"
    path.write_text("test", encoding="utf-8")

    with pytest.raises(ValueError, match="不支持的导入格式"):
        ImportExportService().import_file(str(path))


def _build_csv_file(path) -> str:
    path.write_text("姓名,状态\n张三,进行中\n李四,已完成\n", encoding="utf-8-sig")
    return str(path)
