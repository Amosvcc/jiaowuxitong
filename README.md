# 数据分析软件 V1.0

一个面向 Windows 桌面的轻量级结构化数据维护与统计工具，使用 `Python + PySide6 + SQLite + pandas + openpyxl` 开发。

## 项目简介

本项目提供类似 Excel 的表格编辑体验，同时补充项目文件保存、列下拉配置、行终止、全表搜索和字段统计等能力。  
V1.0 目标是交付一个可直接运行、可打包为绿色版 Windows 程序的单机工具。

## 功能列表

- 表格编辑
- 新增行 / 新增列
- CSV 导入导出
- Excel `.xlsx` 导入导出
- `.dasproj` SQLite 项目保存与打开
- 顶部搜索与匹配高亮
- 列设置与下拉选项
- 行终止 / 恢复
- 单字段统计
- 统计结果导出为 CSV / Excel

## 开发环境

- Windows 10 / Windows 11
- Python 3.11+
- 虚拟环境 `venv`

## 安装依赖

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 运行方式

直接运行：

```bat
python main.py
```

使用脚本运行：

```bat
scripts\run_dev.bat
```

## 测试方式

```bat
pytest
```

或：

```bat
.venv\Scripts\python.exe -m pytest
```

## 打包方式

先清理旧产物：

```bat
scripts\clean.bat
```

再执行打包：

```bat
scripts\build_windows.bat
```

核心打包命令为：

```bat
pyinstaller --noconfirm --clean --windowed --name DataAnalysisApp main.py
```

打包完成后，输出目录为：

```text
dist\DataAnalysisApp\
```

其中主程序为：

```text
dist\DataAnalysisApp\DataAnalysisApp.exe
```

## 当前版本功能范围

V1.0 当前已完成：

- 表格编辑
- CSV / Excel 导入导出
- `.dasproj` 项目保存与打开
- 搜索
- 列设置与下拉选项
- 行终止 / 恢复
- 字段统计与统计结果导出

V1.0 暂不包含：

- 多用户协作
- 云同步
- 图表系统
- 复杂数据透视表
- 高级筛选
- 批量更新界面

## 目录说明

```text
app/ui/            界面层
app/models/        数据模型
app/services/      业务逻辑
app/repositories/  SQLite 数据访问
app/io/            CSV / Excel 导入导出
app/core/          通用异常与工具
docs/              规格、架构与使用文档
scripts/           Windows 开发与打包脚本
tests/             测试代码
```
