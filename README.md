# 数据分析软件 V1.0

一个运行在 Windows 上的轻量级数据分析与数据表管理工具。

## 功能目标

- 类 Excel 表格编辑
- CSV / Excel 导入导出
- 顶部搜索框查找数据
- 每列可配置下拉选项
- 行终止 / 行冻结
- 单字段计数统计
- 统计结果导出

## 技术方案

- Python 3.11+
- PySide6
- SQLite
- pandas
- openpyxl
- PyInstaller

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 目录说明

```text
app/ui/            界面层
app/models/        数据模型
app/services/      业务逻辑
app/repositories/  SQLite 数据访问
app/io/            CSV / Excel 导入导出
app/core/          常量、异常、工具函数
docs/              产品和开发文档
sample_data/       测试导入用示例数据
scripts/           Windows 开发和打包脚本
tests/             单元测试
```

## Codex 开发建议

请将每次开发任务拆小，一次只完成一个阶段，例如：

1. 创建项目骨架。
2. 实现可编辑表格。
3. 增加 CSV 导入。
4. 增加 SQLite 保存。
5. 实现行终止。
6. 实现字段统计。
