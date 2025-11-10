-- Optional: give tasks.created_at a default and backfill any NULLs
PRAGMA foreign_keys=off;
BEGIN TRANSACTION;

-- If column has no default, recreate table with default
-- (Only needed if you prefer DB-level default, the code already sets it.)
-- Example shape – adjust to your exact schema:
-- CREATE TABLE tasks_new (
--   id INTEGER PRIMARY KEY,
--   job_id INTEGER,
--   employee_id INTEGER,
--   title TEXT NOT NULL,
--   description TEXT,
--   status TEXT NOT NULL DEFAULT 'open',
--   due_date TEXT,
--   created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
-- );
-- INSERT INTO tasks_new (id, job_id, employee_id, title, description, status, due_date, created_at)
--   SELECT id, job_id, employee_id, title, description, status, due_date,
--          COALESCE(created_at, CURRENT_TIMESTAMP)
--   FROM tasks;
-- DROP TABLE tasks;
-- ALTER TABLE tasks_new RENAME TO tasks;

-- Or simpler backfill (if column exists and allows UPDATE):
UPDATE tasks SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP);

COMMIT;
PRAGMA foreign_keys=on;
