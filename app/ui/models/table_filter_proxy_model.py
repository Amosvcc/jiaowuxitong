from __future__ import annotations

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel, Qt

from app.models.filter_criteria import ColumnFilterCriteria, TableFilterState
from app.services.filter_service import FilterService
from app.ui.table_model import DataTableModel


class TableFilterProxyModel(QSortFilterProxyModel):
    def __init__(
        self,
        parent=None,
        *,
        filter_service: FilterService | None = None,
    ) -> None:
        super().__init__(parent)
        self.filter_service = filter_service or FilterService()
        self.filter_state = TableFilterState()
        self._row_status_filter = "all"
        self._compiled_column_filters: list[tuple[int, set[str], bool]] = []
        self.setDynamicSortFilter(True)

    @property
    def source_table_model(self) -> DataTableModel:
        source_model = self.sourceModel()
        if not isinstance(source_model, DataTableModel):
            raise TypeError("TableFilterProxyModel 需要 DataTableModel 作为 sourceModel")
        return source_model

    @property
    def project(self):
        return self.source_table_model.project

    @property
    def rows(self):
        return self.source_table_model.rows

    @property
    def columns(self):
        return self.source_table_model.columns

    @property
    def cells(self):
        return self.source_table_model.cells

    @property
    def search_matches(self):
        return self.source_table_model.search_matches

    @property
    def current_search_index(self):
        return self.source_table_model.current_search_index

    def load_project(self, project) -> None:
        self.clear_filters()
        self.source_table_model.load_project(project)
        self._rebuild_filter_cache()

    def add_empty_row(self, after_row_index: int | None = None) -> None:
        self.source_table_model.add_empty_row(after_row_index)
        self._invalidate_rows_filter()

    def add_empty_column(self, after_column_index: int | None = None) -> None:
        self.source_table_model.add_empty_column(after_column_index)
        self._rebuild_filter_cache()
        self._invalidate_rows_filter()

    def mark_dirty(self) -> None:
        self.source_table_model.mark_dirty()

    def mark_clean(self) -> None:
        self.source_table_model.mark_clean()

    def set_search_matches(self, matches: list[tuple[int, int]], current_index: int = -1) -> None:
        self.source_table_model.set_search_matches(matches, current_index)

    def clear_search(self) -> None:
        self.source_table_model.clear_search()

    def set_current_search_index(self, index: int) -> None:
        self.source_table_model.set_current_search_index(index)

    def refresh_column(self, column_index: int) -> None:
        self.source_table_model.refresh_column(column_index)
        self.headerDataChanged.emit(Qt.Orientation.Horizontal, column_index, column_index)
        self._rebuild_filter_cache()
        self._invalidate_rows_filter()

    def refresh_rows(self, row_indexes: list[int]) -> None:
        self.source_table_model.refresh_rows(row_indexes)
        self._invalidate_rows_filter()

    def row_id_at(self, row_index: int) -> str:
        source_index = self.mapToSource(self.index(row_index, 0))
        return self.source_table_model.row_id_at(source_index.row())

    def column_id_at(self, column_index: int) -> str:
        return self.source_table_model.column_id_at(column_index)

    def set_filter_state(self, filter_state: TableFilterState) -> None:
        self.filter_state = filter_state
        self._rebuild_filter_cache()
        self._invalidate_rows_filter()
        if self.columnCount() > 0:
            self.headerDataChanged.emit(Qt.Orientation.Horizontal, 0, self.columnCount() - 1)

    def set_column_filter(self, criteria: ColumnFilterCriteria) -> None:
        if criteria.is_active:
            self.filter_state.filters[str(criteria.column_id)] = criteria
        else:
            self.filter_state.filters.pop(str(criteria.column_id), None)
        self._rebuild_filter_cache()
        self._invalidate_rows_filter()
        column_index = self._column_index_for_id(criteria.column_id)
        if column_index >= 0:
            self.headerDataChanged.emit(Qt.Orientation.Horizontal, column_index, column_index)

    def clear_column_filter(self, column_id: str) -> None:
        self.filter_state.filters.pop(str(column_id), None)
        self._rebuild_filter_cache()
        self._invalidate_rows_filter()
        column_index = self._column_index_for_id(column_id)
        if column_index >= 0:
            self.headerDataChanged.emit(Qt.Orientation.Horizontal, column_index, column_index)

    def set_terminated_only_filter(self, enabled: bool) -> None:
        self.set_row_status_filter("terminated" if enabled else "all")

    def set_row_status_filter(self, row_status: str) -> None:
        if row_status not in {"all", "terminated", "active"}:
            raise ValueError("不支持的行状态筛选")
        self.filter_state.row_status = row_status
        self._rebuild_filter_cache()
        self._invalidate_rows_filter()

    def clear_filters(self) -> None:
        self.filter_state = TableFilterState()
        self._rebuild_filter_cache()
        self._invalidate_rows_filter()
        if self.columnCount() > 0:
            self.headerDataChanged.emit(Qt.Orientation.Horizontal, 0, self.columnCount() - 1)

    def refresh_filter(self) -> None:
        self._rebuild_filter_cache()
        self._invalidate_rows_filter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        source_model = self.source_table_model
        if not self.filter_state.is_active:
            return True
        if source_parent.isValid() or source_row < 0 or source_row >= len(source_model.rows):
            return False

        row = source_model.rows[source_row]
        if self._row_status_filter == "terminated" and not row.is_terminated:
            return False
        if self._row_status_filter == "active" and row.is_terminated:
            return False

        cells = source_model.cells
        for column_id, selected_values, include_blank in self._compiled_column_filters:
            cell = cells.get((row.id, column_id))
            value = "" if cell is None else cell.value
            if value == "":
                if not include_blank:
                    return False
                continue
            if value not in selected_values:
                return False
        return True

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        value = super().headerData(section, orientation, role)
        if role != Qt.DisplayRole or orientation != Qt.Orientation.Horizontal:
            return value
        column_id = self.column_id_at(section)
        criteria = self.filter_state.filters.get(str(column_id))
        if criteria is not None and criteria.is_active:
            return f"{value} *"
        return value

    def _column_index_for_id(self, column_id: str) -> int:
        for index, column in enumerate(self.source_table_model.columns):
            if str(column.id) == str(column_id):
                return index
        return -1

    def _rebuild_filter_cache(self) -> None:
        self._row_status_filter = self.filter_state.row_status
        column_ids_by_string = {
            str(column.id): column.id for column in self.source_table_model.columns
        }
        compiled_filters: list[tuple[int, set[str], bool]] = []
        for criteria in self.filter_state.filters.values():
            if not criteria.is_active:
                continue
            column_id = column_ids_by_string.get(str(criteria.column_id))
            if column_id is None:
                continue
            compiled_filters.append(
                (column_id, set(criteria.selected_values), criteria.include_blank)
            )
        self._compiled_column_filters = compiled_filters

    def _invalidate_rows_filter(self) -> None:
        self.beginFilterChange()
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)
