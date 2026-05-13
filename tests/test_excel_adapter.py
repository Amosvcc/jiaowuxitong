import pandas as pd

from app.io.excel_adapter import ExcelAdapter


def test_excel_adapter_reads_chinese_headers_and_content(workspace_tmp_path) -> None:
    path = workspace_tmp_path / "中文数据.xlsx"
    source = pd.DataFrame([["姓名", "状态"], ["张三", "进行中"], ["李四", "已完成"]])
    source.to_excel(path, index=False, header=False, engine="openpyxl")

    dataframe = ExcelAdapter().read(str(path))

    assert dataframe.columns.tolist() == ["姓名", "状态"]
    assert dataframe.values.tolist() == [["张三", "进行中"], ["李四", "已完成"]]


def test_excel_adapter_writes_expected_content(workspace_tmp_path) -> None:
    path = workspace_tmp_path / "导出.xlsx"
    dataframe = pd.DataFrame([["张三", "进行中"]], columns=["姓名", "状态"])

    ExcelAdapter().write(dataframe, str(path))

    exported = pd.read_excel(path, dtype=str, keep_default_na=False)
    assert exported.columns.tolist() == ["姓名", "状态"]
    assert exported.values.tolist() == [["张三", "进行中"]]
