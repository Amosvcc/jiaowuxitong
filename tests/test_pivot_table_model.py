from PySide6.QtCore import Qt

from app.models import PivotResult
from app.ui.models.pivot_table_model import PivotTableModel


def build_result(
    *,
    show_row_totals: bool = True,
    show_column_totals: bool = True,
) -> PivotResult:
    return PivotResult(
        row_field="班级",
        column_field="性别",
        row_headers=["一班", "二班"],
        column_headers=["男", "女"],
        matrix={"一班": {"男": 1, "女": 1}, "二班": {"男": 1, "女": 2}},
        row_totals={"一班": 2, "二班": 3},
        column_totals={"男": 2, "女": 3},
        grand_total=5,
        show_row_totals=show_row_totals,
        show_column_totals=show_column_totals,
    )


def test_pivot_table_model_row_count_is_correct() -> None:
    model = PivotTableModel(build_result())

    assert model.rowCount() == 3


def test_pivot_table_model_column_count_is_correct() -> None:
    model = PivotTableModel(build_result())

    assert model.columnCount() == 4


def test_pivot_table_model_headers_are_correct() -> None:
    model = PivotTableModel(build_result())

    assert [model.headerData(index, Qt.Orientation.Horizontal) for index in range(4)] == [
        "班级",
        "男",
        "女",
        "合计",
    ]


def test_pivot_table_model_displays_cell_counts() -> None:
    model = PivotTableModel(build_result())

    assert model.data(model.index(0, 1), Qt.ItemDataRole.DisplayRole) == 1
    assert model.data(model.index(1, 2), Qt.ItemDataRole.DisplayRole) == 2


def test_pivot_table_model_displays_zero_for_missing_combination() -> None:
    result = build_result()
    result.matrix["一班"].pop("男")
    model = PivotTableModel(result)

    assert model.data(model.index(0, 1), Qt.ItemDataRole.DisplayRole) == 0


def test_pivot_table_model_displays_row_totals() -> None:
    model = PivotTableModel(build_result())

    assert model.data(model.index(0, 3), Qt.ItemDataRole.DisplayRole) == 2
    assert model.data(model.index(1, 3), Qt.ItemDataRole.DisplayRole) == 3


def test_pivot_table_model_displays_column_totals() -> None:
    model = PivotTableModel(build_result())

    assert model.data(model.index(2, 1), Qt.ItemDataRole.DisplayRole) == 2
    assert model.data(model.index(2, 2), Qt.ItemDataRole.DisplayRole) == 3


def test_pivot_table_model_displays_grand_total() -> None:
    model = PivotTableModel(build_result())

    assert model.data(model.index(2, 3), Qt.ItemDataRole.DisplayRole) == 5


def test_pivot_table_model_column_count_without_row_totals_is_correct() -> None:
    model = PivotTableModel(build_result(show_row_totals=False))

    assert model.columnCount() == 3
    assert model.headerData(2, Qt.Orientation.Horizontal) == "女"


def test_pivot_table_model_row_count_without_column_totals_is_correct() -> None:
    model = PivotTableModel(build_result(show_column_totals=False))

    assert model.rowCount() == 2

