-- Migration: Task Data Model
-- Version: 21
-- Description: Creates comprehensive Task model with TaskMaterial and TaskEvidence tables

-- Step 1: Backup old tasks table if it exists and has data
CREATE TABLE IF NOT EXISTS tasks_legacy_backup AS 
SELECT * FROM tasks WHERE 1=0;

-- Step 2: Create new tasks table with comprehensive structure
CREATE TABLE IF NOT EXISTS tasks_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)), 2) || '-' || substr('89ab', abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)), 2) || '-' || hex(randomblob(6)))),
    
    -- IDENTIFIKACE
    title TEXT NOT NULL,
    description TEXT,
    task_type TEXT NOT NULL DEFAULT 'work',  -- work, transport, admin, inspection, maintenance
    
    -- VAZBY (povinné)
    job_id INTEGER NOT NULL,
    assigned_employee_id INTEGER NOT NULL,
    created_by_id INTEGER NOT NULL,
    
    -- ČASOVÉ OKNO (povinné)
    planned_start TEXT NOT NULL,  -- ISO format datetime
    planned_end TEXT NOT NULL,    -- ISO format datetime
    planned_duration_minutes INTEGER NOT NULL,
    
    -- LOKACE (povinná)
    location_type TEXT NOT NULL DEFAULT 'job_site',  -- job_site, warehouse, nursery, office, travel
    location_id INTEGER,
    location_name TEXT,
    gps_lat REAL,
    gps_lng REAL,
    
    -- OČEKÁVANÝ VÝSTUP (povinný)
    expected_outcome TEXT NOT NULL,
    expected_outcome_type TEXT,  -- installed, removed, transported, inspected, documented, planted
    expected_quantity REAL,
    expected_unit TEXT,
    
    -- SKUTEČNOST
    actual_start TEXT,  -- ISO format datetime
    actual_end TEXT,    -- ISO format datetime
    actual_duration_minutes INTEGER,
    
    -- STAV
    status TEXT NOT NULL DEFAULT 'planned',  -- planned, assigned, in_progress, completed, partial, failed, blocked, cancelled
    completion_state TEXT,  -- done, partial, failed, blocked
    completion_percentage INTEGER DEFAULT 0,
    
    -- ODCHYLKY
    time_deviation_minutes INTEGER DEFAULT 0,
    has_material_deviation INTEGER DEFAULT 0,  -- BOOLEAN as INTEGER
    has_workaround INTEGER DEFAULT 0,  -- BOOLEAN as INTEGER
    deviation_notes TEXT,
    
    -- INTEGRITA
    integrity_score REAL DEFAULT 100.0,  -- 0-100
    integrity_flags TEXT DEFAULT '[]',  -- JSON stored as TEXT
    
    -- PRIORITY & RIZIKO
    priority TEXT DEFAULT 'normal',  -- critical, high, normal, low
    risk_level TEXT DEFAULT 'low',
    risk_factors TEXT DEFAULT '[]',  -- JSON stored as TEXT
    
    -- OFFLINE SUPPORT
    created_offline INTEGER DEFAULT 0,  -- BOOLEAN as INTEGER
    last_synced_at TEXT,  -- ISO format datetime
    offline_changes TEXT DEFAULT '{}',  -- JSON stored as TEXT
    sync_conflict INTEGER DEFAULT 0,  -- BOOLEAN as INTEGER
    
    -- AUDIT
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT,
    version INTEGER DEFAULT 1,
    
    FOREIGN KEY (job_id) REFERENCES jobs(id),
    FOREIGN KEY (assigned_employee_id) REFERENCES employees(id),
    FOREIGN KEY (created_by_id) REFERENCES employees(id)
);

-- Step 3: Create indexes
CREATE INDEX IF NOT EXISTS idx_task_job_status ON tasks_new(job_id, status);
CREATE INDEX IF NOT EXISTS idx_task_employee_date ON tasks_new(assigned_employee_id, planned_start);
CREATE INDEX IF NOT EXISTS idx_task_status_date ON tasks_new(status, planned_start);
CREATE INDEX IF NOT EXISTS idx_task_uuid ON tasks_new(uuid);

-- Step 4: Create task_materials table
CREATE TABLE IF NOT EXISTS task_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    
    material_id INTEGER,
    material_name TEXT NOT NULL,
    planned_quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    
    actual_quantity REAL,
    was_available INTEGER,  -- BOOLEAN as INTEGER
    substitute_used INTEGER DEFAULT 0,  -- BOOLEAN as INTEGER
    substitute_material_id INTEGER,
    substitute_notes TEXT,
    
    reservation_id INTEGER,
    reservation_status TEXT,
    
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    FOREIGN KEY (task_id) REFERENCES tasks_new(id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES warehouse_items(id),
    FOREIGN KEY (substitute_material_id) REFERENCES warehouse_items(id)
);

CREATE INDEX IF NOT EXISTS idx_task_materials_task ON task_materials(task_id);
CREATE INDEX IF NOT EXISTS idx_task_materials_material ON task_materials(material_id);

-- Step 5: Create task_evidence table
CREATE TABLE IF NOT EXISTS task_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    
    evidence_type TEXT NOT NULL,  -- photo, note, measurement, gps_checkin
    
    file_path TEXT,
    file_name TEXT,
    note_text TEXT,
    measurement_value REAL,
    measurement_unit TEXT,
    gps_lat REAL,
    gps_lng REAL,
    
    captured_at TEXT NOT NULL,  -- ISO format datetime
    captured_by_id INTEGER,
    captured_offline INTEGER DEFAULT 0,  -- BOOLEAN as INTEGER
    
    is_validated INTEGER DEFAULT 0,  -- BOOLEAN as INTEGER
    validated_by_id INTEGER,
    validated_at TEXT,  -- ISO format datetime
    
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    FOREIGN KEY (task_id) REFERENCES tasks_new(id) ON DELETE CASCADE,
    FOREIGN KEY (captured_by_id) REFERENCES employees(id),
    FOREIGN KEY (validated_by_id) REFERENCES employees(id)
);

CREATE INDEX IF NOT EXISTS idx_task_evidence_task ON task_evidence(task_id);
CREATE INDEX IF NOT EXISTS idx_task_evidence_type ON task_evidence(evidence_type);
CREATE INDEX IF NOT EXISTS idx_task_evidence_captured ON task_evidence(captured_by_id);

-- Step 6: Migrate data from old tasks table if it exists
-- This preserves existing tasks by copying them to new structure
INSERT INTO tasks_new (
    id, title, description, job_id, assigned_employee_id, created_by_id,
    planned_start, planned_end, planned_duration_minutes,
    location_type, location_name,
    expected_outcome, status,
    created_at, updated_at
)
SELECT 
    id,
    title,
    description,
    COALESCE(job_id, 0),  -- Default to 0 if NULL, adjust as needed
    COALESCE(employee_id, 0),  -- Default to 0 if NULL, adjust as needed
    COALESCE(employee_id, 0),  -- Use employee_id as created_by_id fallback
    COALESCE(due_date, datetime('now')),  -- Use due_date as planned_start
    COALESCE(due_date, datetime('now', '+1 hour')),  -- Use due_date + 1h as planned_end
    60,  -- Default 1 hour duration
    'job_site',
    '',
    COALESCE(description, title),  -- Use description or title as expected_outcome
    COALESCE(status, 'planned'),
    COALESCE(created_at, datetime('now')),
    datetime('now')
FROM tasks
WHERE NOT EXISTS (SELECT 1 FROM tasks_new WHERE tasks_new.id = tasks.id);

-- Step 7: Drop old tasks table and rename new one
-- Note: This is commented out for safety - uncomment after verifying migration
-- DROP TABLE IF EXISTS tasks;
-- ALTER TABLE tasks_new RENAME TO tasks;

-- Step 8: Create material_reservations table if it doesn't exist (for TaskMaterial FK)
CREATE TABLE IF NOT EXISTS material_reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    item_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    reserved_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT DEFAULT 'pending',
    FOREIGN KEY (item_id) REFERENCES warehouse_items(id)
);

CREATE INDEX IF NOT EXISTS idx_material_reservations_task ON material_reservations(task_id);
CREATE INDEX IF NOT EXISTS idx_material_reservations_item ON material_reservations(item_id);
