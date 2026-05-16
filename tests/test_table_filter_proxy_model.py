from PySide6.QtCore import Qt

from app.models import ColumnFilterCriteria, Project, TableFilterState
from app.ui.models import TableFilterProxyModel
from app.ui.table_model import DataTableModel


def make_model() -> tuple[Project, DataTableModel, TableFilterProxyModel]:
    project = Project.create_empty(row_count=4, column_count=2)
    project.columns[0].name = "专业"
    project.columns[1].name = "班级"
    values = [
        ("会计", "1班"),
        ("计算机", "1班"),
        ("会计", "2班"),
        ("英语", "3班"),
    ]
    for row_index, (major, class_name) in enumerate(values):
        row = project.rows[row_index]
        project.set_cell_value(row.id, project.columns[0].id, major)
        project.set_cell_value(row.id, project.columns[1].id, class_name)
    project.dirty = False
    source_model = DataTableModel(project)
    proxy_model = TableFilterProxyModel()
    proxy_model.setSourceModel(source_model)
    return project, source_model, proxy_model


def set_filters(proxy_model: TableFilterProxyModel, project: Project, major=None, class_name=None) -> None:
    filters = {}
    if major is not None:
        filters[str(project.columns[0].id)] = ColumnFilterCriteria(
            column_id=str(project.columns[0].id),
            selected_values=set(major),
        )
    if class_name is not None:
        filters[str(project.columns[1].id)] = ColumnFilterCriteria(
            column_id=str(project.columns[1].id),
            selected_values=set(class_name),
        )
    proxy_model.set_filter_state(TableFilterState(filters=filters))


def test_proxy_shows_all_rows_without_filter() -> None:
    _project, _source_model, proxy_model = make_model()

    assert proxy_model.rowCount() == 4


def test_proxy_filters_major_accounting() -> None:
    project, _source_model, proxy_model = make_model()

    set_filters(proxy_model, project, major=["会计"])

    assert proxy_model.rowCount() == 2
    assert proxy_model.data(proxy_model.index(0, 0), Qt.ItemDataRole.DisplayRole) == "会计"
    assert proxy_model.data(proxy_model.index(1, 0), Qt.ItemDataRole.DisplayRole) == "会计"


def test_proxy_filters_multiple_columns_with_and_logic() -> None:
    project, _source_model, proxy_model = make_model()

    set_filters(proxy_model, project, major=["会计"], class_name=["1班"])

    assert proxy_model.rowCount() == 1
    assert proxy_model.data(proxy_model.index(0, 1), Qt.ItemDataRole.DisplayRole) == "1班"


def test_proxy_clear_filters_restores_all_rows() -> None:
    project, _source_model, proxy_model = make_model()
    set_filters(proxy_model, project, major=["会计"])

    proxy_model.clear_filters()

    assert proxy_model.rowCount() == 4


def test_proxy_can_filter_terminated_rows() -> None:
    project, _source_model, proxy_model = make_model()
    project.rows[1].is_terminated = True
    project.rows[3].is_terminated = True

    proxy_model.set_row_status_filter("terminated")

    assert proxy_model.rowCount() == 2
    assert proxy_model.mapToSource(proxy_model.index(0, 0)).row() == 1
    assert proxy_model.mapToSource(proxy_model.index(1, 0)).row() == 3


def test_proxy_can_filter_active_rows() -> None:
    project, _source_model, proxy_model = make_model()
    project.rows[1].is_terminated = True
    project.rows[3].is_terminated = True

    proxy_model.set_row_status_filter("active")

    assert proxy_model.rowCount() == 2
    assert proxy_model.mapToSource(proxy_model.index(0, 0)).row() == 0
    assert proxy_model.mapToSource(proxy_model.index(1, 0)).row() == 2


def test_proxy_empty_result_has_zero_rows() -> None:
    project, _source_model, proxy_model = make_model()

    set_filters(proxy_model, project, major=["不存在"])

    assert proxy_model.rowCount() == 0


def test_proxy_index_maps_to_source_index() -> None:
    project, source_model, proxy_model = make_model()
    set_filters(proxy_model, project, major=["计算机"])

    source_index = proxy_model.mapToSource(proxy_model.index(0, 0))

    assert source_index == source_model.index(1, 0)
    assert source_model.row_id_at(source_index.row()) == "2"


def test_proxy_refreshes_after_project_data_changes() -> None:
    project, source_model, proxy_model = make_model()
    set_filters(proxy_model, project, major=["会计"])

    source_model.setData(source_model.index(1, 0), "会计")
    proxy_model.refresh_filter()

    assert proxy_model.rowCount() == 3
