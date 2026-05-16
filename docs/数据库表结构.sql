CREATE TABLE IF NOT EXISTS project_info (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    app_version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS columns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    field_type TEXT NOT NULL DEFAULT 'text',
    order_index INTEGER NOT NULL,
    dropdown_options TEXT NOT NULL DEFAULT '[]',
    allow_custom_value INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_index INTEGER NOT NULL,
    is_terminated INTEGER NOT NULL DEFAULT 0,
    terminated_at TEXT,
    terminated_column_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(terminated_column_id) REFERENCES columns(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS cells (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id INTEGER NOT NULL,
    column_id INTEGER NOT NULL,
    value TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL,
    FOREIGN KEY(row_id) REFERENCES rows(id) ON DELETE CASCADE,
    FOREIGN KEY(column_id) REFERENCES columns(id) ON DELETE CASCADE,
    UNIQUE(row_id, column_id)
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_columns_order ON columns(order_index);
CREATE INDEX IF NOT EXISTS idx_rows_order ON rows(order_index);
CREATE INDEX IF NOT EXISTS idx_cells_row_id ON cells(row_id);
CREATE INDEX IF NOT EXISTS idx_cells_column_id ON cells(column_id);
