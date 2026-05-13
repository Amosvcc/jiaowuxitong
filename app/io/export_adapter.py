from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.core import UnsupportedFileFormatError
from app.io.csv_adapter import CsvAdapter
from app.io.excel_adapter import ExcelAdapter


class ExportAdapter:
    def __init__(self) -> None:
        self.csv_adapter = CsvAdapter()
        self.excel_adapter = ExcelAdapter()

    def write(self, dataframe: pd.DataFrame, path: str) -> None:
        suffix = Path(path).suffix.lower()
        if suffix == ".csv":
            self.csv_adapter.write(dataframe, path)
            return
        if suffix == ".xlsx":
            self.excel_adapter.write(dataframe, path)
            return
        raise UnsupportedFileFormatError(f"不支持的导出格式：{suffix or '无扩展名'}")
