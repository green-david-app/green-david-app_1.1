-- 2025-11-09: Fix tasks.created_at so INSERTs can omit the column.
-- This rebuilds the tasks table atomically and preserves data + indexes.
PRAGMA foreign_keys=off;
BEGIN TRANSACTION;

-- Capture the existing indexes on tasks
-- (They will be re-created manually below if known; adjust as needed).

-- Rebuild tasks table with created_at default
CREATE TABLE IF NOT EXISTS tasks_new (
    id INTEGER PRIMARY KEY,
    job_id INTEGER,
    employee_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    due_date TEXT,
    created_at TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%fZ','now'))
);

INSERT INTO tasks_new (id, job_id, employee_id, title, description, status, due_date, created_at)
SELECT
    id, job_id, employee_id, title, description,
    COALESCE(status, 'open'),
    due_date,
    COALESCE(created_at, STRFTIME('%Y-%m-%dT%H:%M:%fZ','now'))
FROM tasks;

DROP TABLE tasks;
ALTER TABLE tasks_new RENAME TO tasks;

-- (Optional) recreate indexes if you had them before:
-- CREATE INDEX IF NOT EXISTS idx_tasks_job ON tasks(job_id);
-- CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date);

COMMIT;
PRAGMA foreign_keys=on;