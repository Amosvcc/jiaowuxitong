from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.core import UnsupportedFileFormatError
from app.io import CsvAdapter, ExcelAdapter, ExportAdapter
from app.models import PivotResult, Project
from app.services.pivot_service import PivotService


class ImportExportService:
    def __init__(self) -> None:
        self.csv_adapter = CsvAdapter()
        self.excel_adapter = ExcelAdapter()
        self.export_adapter = ExportAdapter()
        self.pivot_service = PivotService()

    def import_file(self, path: str) -> Project:
        return Project.from_dataframe(self._read_dataframe(path))

    def read_table(self, path: str) -> tuple[list[str], list[list[str]]]:
        dataframe = self._read_dataframe(path)
        columns = Project._normalize_column_names(list(dataframe.columns))
        rows = [
            ["" if pd.isna(value) else str(value) for value in row]
            for row in dataframe.itertuples(index=False, name=None)
        ]
        return columns, rows

    def export_file(self, project: Project, path: str) -> None:
        self.export_adapter.write(project.to_dataframe(), path)

    def export_pivot_result(self, result: PivotResult, path: str) -> None:
        self.export_adapter.write(self.pivot_service.build_pivot_dataframe(result), path)

    def _read_dataframe(self, path: str):
        suffix = Path(path).suffix.lower()
        if suffix == ".csv":
            return self.csv_adapter.read(path)
        if suffix == ".xlsx":
            return self.excel_adapter.read(path)
        raise UnsupportedFileFormatError(f"不支持的导入格式：{suffix or '无扩展名'}")
