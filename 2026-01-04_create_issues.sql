-- Migration: Create issues table
-- Date: 2026-01-04

CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    type TEXT NOT NULL DEFAULT 'blocker', -- blocker, todo, note
    status TEXT NOT NULL DEFAULT 'open', -- open, in_progress, resolved
    severity TEXT, -- critical, high, medium, low
    assigned_to INTEGER, -- employee_id
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    resolved_at TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES employees(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_issues_job_id ON issues(job_id);
CREATE INDEX IF NOT EXISTS idx_issues_assigned_to ON issues(assigned_to);
CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);
