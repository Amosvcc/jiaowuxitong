# AGENTS.md

## 项目概述

本项目是一个 Windows 桌面数据分析软件，使用 Python + PySide6 + SQLite + pandas + openpyxl 开发。

软件核心能力：

- 类 Excel 表格编辑
- CSV / Excel 导入导出
- 每列下拉选项配置
- 行终止 / 行冻结机制
- 全表搜索
- 单字段统计
- 统计结果导出

## 技术栈

- Python 3.11+
- PySide6
- SQLite
- pandas
- openpyxl
- pytest
- PyInstaller

## 架构要求

代码必须按以下分层组织：

- `app/ui/`：界面层，只处理窗口、控件、信号槽
- `app/models/`：数据模型
- `app/services/`：业务逻辑
- `app/repositories/`：SQLite 数据访问
- `app/io/`：CSV / Excel 导入导出
- `app/core/`：常量、异常、工具函数

不要把业务逻辑直接写在 `main_window.py` 中。

## 表格实现要求

主表格必须使用：

- `QTableView`
- `QAbstractTableModel`

不要使用 `QTableWidget` 作为主表格实现。

## 数据规则

- 单元格修改后，新值直接覆盖旧值。
- 已终止行默认禁止编辑。
- 批量更新时必须跳过已终止行。
- 新增列时，已终止行不自动填充默认值。
- 搜索时包含正常行和已终止行。
- 统计时默认包含已终止行，但用户可以选择排除。
- CSV / Excel 只作为导入导出格式，不作为内部项目存储格式。
- 软件内部项目文件使用 SQLite，扩展名为 `.dasproj`。

## 开发命令

创建虚拟环境：

```bash
python -m venv .venv
```

安装依赖：

```bash
pip install -r requirements.txt
```

运行程序：

```bash
python main.py
```

运行测试：

```bash
pytest
```

打包 Windows 程序：

```bash
scripts/build_windows.bat
```

## 开发原则

- 每次只实现一个小功能，保持程序始终可运行。
- 新增功能后尽量补充测试。
- 修改数据库结构时同步更新 `docs/数据库表结构.sql`。
- 修改业务规则时同步更新 `docs/V1_0_验收清单.md`。
- 不要引入不必要的大型框架。
- 不要在 V1.0 中实现云同步、登录、多用户协作、复杂数据透视表、图表系统。
- 代码注释和界面文案优先使用中文；变量名和函数名使用英文。
- 对外部文件读写要兼容中文路径和中文内容。

## 任务执行方式

Codex 执行任务时应遵循：

1. 先阅读 `AGENTS.md`、`docs/功能规格说明书.md`、`docs/代码架构设计.md`。
2. 根据用户指定的任务，只修改与该任务相关的文件。
3. 不要一次性实现多个阶段。
4. 完成后说明修改了哪些文件、如何运行、是否通过测试。
5. 若发现需求冲突，优先遵守 `AGENTS.md` 和 `docs/功能规格说明书.md`。
