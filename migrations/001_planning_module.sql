-- ================================================================
-- MIGRATION 001: Planning Module Foundation (FIXED)
-- Adds planning capabilities to existing structure
-- ================================================================

-- Record migration
INSERT OR IGNORE INTO schema_migrations (version) VALUES (1);

-- ----------------------------------------------------------------
-- STEP 1: Extend Tasks table for planning (SAFE)
-- ----------------------------------------------------------------
-- SQLite doesn't support IF NOT EXISTS for ALTER COLUMN, so we check manually

-- Add columns only if they don't exist
-- This is done through safe Python script, not SQL

-- ----------------------------------------------------------------
-- STEP 2: Extend Jobs table for planning (SAFE)
-- ----------------------------------------------------------------
-- Same approach - handled by Python

-- ----------------------------------------------------------------
-- STEP 3: Action Items - kritické úkoly co musíš vyřídit
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS action_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL DEFAULT 'other',
    deadline DATE NOT NULL,
    assigned_to INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    priority TEXT NOT NULL DEFAULT 'medium',
    notes TEXT,
    completed_at DATETIME,
    completed_by INTEGER,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES employees(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (completed_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_action_items_deadline ON action_items(deadline);
CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items(status);
CREATE INDEX IF NOT EXISTS idx_action_items_assigned ON action_items(assigned_to);

-- ----------------------------------------------------------------
-- STEP 4: Material Deliveries - logistika materiálu
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS material_deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    material_name TEXT NOT NULL,
    quantity REAL,
    unit TEXT,
    supplier TEXT,
    delivery_date DATE NOT NULL,
    delivery_time TEXT,
    driver_id INTEGER,
    pickup_location TEXT,
    delivery_location TEXT,
    cost DECIMAL(10,2),
    status TEXT NOT NULL DEFAULT 'planned',
    notes TEXT,
    tracking_number TEXT,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (driver_id) REFERENCES employees(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_material_deliveries_date ON material_deliveries(delivery_date);
CREATE INDEX IF NOT EXISTS idx_material_deliveries_status ON material_deliveries(status);
CREATE INDEX IF NOT EXISTS idx_material_deliveries_driver ON material_deliveries(driver_id);

-- ----------------------------------------------------------------
-- STEP 5: Daily Plans - denní přehled kdo-kde-co
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    employee_id INTEGER NOT NULL,
    job_id INTEGER,
    task_id INTEGER,
    hours_planned REAL,
    location TEXT,
    notes TEXT,
    status TEXT DEFAULT 'planned',
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_daily_plans_date ON daily_plans(date);
CREATE INDEX IF NOT EXISTS idx_daily_plans_employee ON daily_plans(employee_id);
CREATE INDEX IF NOT EXISTS idx_daily_plans_job ON daily_plans(job_id);

-- ----------------------------------------------------------------
-- STEP 6: Employee Groups - pro budoucí crew management
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employee_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    leader_id INTEGER,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (leader_id) REFERENCES employees(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS employee_group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES employee_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE(group_id, employee_id)
);

-- ----------------------------------------------------------------
-- STEP 7: Planning Conflicts - detekce kolizí
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS planning_conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    conflict_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'medium',
    description TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    job_id INTEGER,
    resolved BOOLEAN DEFAULT 0,
    resolved_at DATETIME,
    resolved_by INTEGER,
    resolution_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_planning_conflicts_date ON planning_conflicts(date);
CREATE INDEX IF NOT EXISTS idx_planning_conflicts_resolved ON planning_conflicts(resolved);

-- ================================================================
-- DONE
-- ================================================================
