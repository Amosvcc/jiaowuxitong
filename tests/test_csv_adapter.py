import pandas as pd

from app.io.csv_adapter import CsvAdapter


def test_csv_adapter_reads_chinese_headers_and_content(workspace_tmp_path) -> None:
    path = workspace_tmp_path / "中文数据.csv"
    path.write_text("姓名,状态\n张三,进行中\n李四,已完成\n", encoding="utf-8-sig")

    dataframe = CsvAdapter().read(str(path))

    assert dataframe.columns.tolist() == ["姓名", "状态"]
    assert dataframe.values.tolist() == [["张三", "进行中"], ["李四", "已完成"]]


def test_csv_adapter_writes_expected_content(workspace_tmp_path) -> None:
    path = workspace_tmp_path / "导出.csv"
    dataframe = pd.DataFrame([["张三", "进行中"]], columns=["姓名", "状态"])

    CsvAdapter().write(dataframe, str(path))

    exported = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    assert exported.columns.tolist() == ["姓名", "状态"]
    assert exported.values.tolist() == [["张三", "进行中"]]
