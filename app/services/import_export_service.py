from __future__ import annotations

from pathlib import Path

from app.core import UnsupportedFileFormatError
from app.io import CsvAdapter, ExcelAdapter, ExportAdapter
from app.models import Project


class ImportExportService:
    def __init__(self) -> None:
        self.csv_adapter = CsvAdapter()
        self.excel_adapter = ExcelAdapter()
        self.export_adapter = ExportAdapter()

    def import_file(self, path: str) -> Project:
        suffix = Path(path).suffix.lower()
        if suffix == ".csv":
            dataframe = self.csv_adapter.read(path)
        elif suffix == ".xlsx":
            dataframe = self.excel_adapter.read(path)
        else:
            raise UnsupportedFileFormatError(f"不支持的导入格式：{suffix or '无扩展名'}")

        return Project.from_dataframe(dataframe)

    def export_file(self, project: Project, path: str) -> None:
        self.export_adapter.write(project.to_dataframe(), path)
