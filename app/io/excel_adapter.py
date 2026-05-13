from __future__ import annotations

from pathlib import Path

import pandas as pd


class ExcelAdapter:
    def read(self, path: str) -> pd.DataFrame:
        raw_dataframe = pd.read_excel(
            Path(path),
            header=None,
            dtype=str,
            keep_default_na=False,
        )
        if raw_dataframe.empty:
            return pd.DataFrame()

        headers = ["" if pd.isna(value) else str(value) for value in raw_dataframe.iloc[0].tolist()]
        data = raw_dataframe.iloc[1:].reset_index(drop=True)
        data.columns = headers
        return data

    def write(self, dataframe: pd.DataFrame, path: str) -> None:
        dataframe.to_excel(Path(path), index=False, engine="openpyxl")
