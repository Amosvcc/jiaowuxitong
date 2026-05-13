from __future__ import annotations

from pathlib import Path

import pandas as pd


class CsvAdapter:
    def read(self, path: str) -> pd.DataFrame:
        raw_dataframe = pd.read_csv(
            Path(path),
            header=None,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        return self._extract_header_dataframe(raw_dataframe)

    def write(self, dataframe: pd.DataFrame, path: str) -> None:
        dataframe.to_csv(Path(path), index=False, encoding="utf-8-sig")

    @staticmethod
    def _extract_header_dataframe(raw_dataframe: pd.DataFrame) -> pd.DataFrame:
        if raw_dataframe.empty:
            return pd.DataFrame()

        headers = ["" if pd.isna(value) else str(value) for value in raw_dataframe.iloc[0].tolist()]
        data = raw_dataframe.iloc[1:].reset_index(drop=True)
        data.columns = headers
        return data
