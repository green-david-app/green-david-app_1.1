-- Migration 004: Task Events Table
-- Event-driven system for Task entities

CREATE TABLE IF NOT EXISTS task_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    
    task_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    
    job_id INTEGER,
    employee_id INTEGER,
    
    payload TEXT NOT NULL DEFAULT '{}',
    
    occurred_at TEXT NOT NULL,
    recorded_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    occurred_offline INTEGER NOT NULL DEFAULT 0,
    synced_at TEXT,
    
    source TEXT NOT NULL DEFAULT 'web_app',
    source_device_id TEXT,
    
    ai_processed INTEGER NOT NULL DEFAULT 0,
    ai_processed_at TEXT,
    ai_insights TEXT,
    
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_event_task_type ON task_events(task_id, event_type);
CREATE INDEX IF NOT EXISTS idx_event_job_time ON task_events(job_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_event_type_time ON task_events(event_type, occurred_at);
CREATE INDEX IF NOT EXISTS idx_event_ai_unprocessed ON task_events(ai_processed);
CREATE INDEX IF NOT EXISTS idx_event_task_time ON task_events(task_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_event_uuid ON task_events(uuid);
CREATE INDEX IF NOT EXISTS idx_event_employee_time ON task_events(employee_id, occurred_at);
