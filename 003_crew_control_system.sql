-- =====================================================
-- CREW CONTROL SYSTEM - Database Migration
-- Green David App v2.0
-- =====================================================

-- Employee Skills (dovednosti)
CREATE TABLE IF NOT EXISTS employee_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    skill_type TEXT NOT NULL,  -- planting, wood, logistics, planning, maintenance, heavy_work, communication
    skill_name TEXT NOT NULL,
    level INTEGER DEFAULT 1,  -- 1-5 (junior to expert)
    certified INTEGER DEFAULT 0,
    certified_date TEXT,
    certified_by TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- Employee Certifications (certifikace)
CREATE TABLE IF NOT EXISTS employee_certifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    cert_name TEXT NOT NULL,
    cert_type TEXT,  -- driving, machinery, safety, professional
    issued_date TEXT,
    expiry_date TEXT,
    issuer TEXT,
    document_url TEXT,
    status TEXT DEFAULT 'active',  -- active, expired, pending
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- Employee Work Preferences (preference práce)
CREATE TABLE IF NOT EXISTS employee_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL UNIQUE,
    preferred_work_types TEXT,  -- JSON array: ["planting", "maintenance"]
    avoided_work_types TEXT,    -- JSON array
    max_weekly_hours REAL DEFAULT 40,
    preferred_locations TEXT,   -- JSON array of location IDs
    travel_radius_km INTEGER DEFAULT 50,
    prefers_team_work INTEGER DEFAULT 1,
    prefers_solo_work INTEGER DEFAULT 0,
    notes TEXT,
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- Employee Capacity (kapacita - plánovaná vs skutečná)
CREATE TABLE IF NOT EXISTS employee_capacity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    week_start TEXT NOT NULL,  -- YYYY-MM-DD (Monday)
    planned_hours REAL DEFAULT 40,
    assigned_hours REAL DEFAULT 0,
    actual_hours REAL DEFAULT 0,
    utilization_pct REAL DEFAULT 0,
    status TEXT DEFAULT 'available',  -- available, partial, overloaded, vacation, sick
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE(employee_id, week_start)
);

-- Employee Performance Metrics (výkonové metriky)
CREATE TABLE IF NOT EXISTS employee_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    total_hours REAL DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    on_time_rate REAL DEFAULT 100,
    quality_score REAL DEFAULT 0,  -- 0-5
    efficiency_score REAL DEFAULT 0,  -- 0-5
    reliability_score REAL DEFAULT 0,  -- 0-5 (stability výkonu)
    notes TEXT,
    calculated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- AI Balance Score History
CREATE TABLE IF NOT EXISTS employee_ai_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    score_date TEXT NOT NULL,
    balance_score REAL DEFAULT 50,  -- 0-100 (50 = perfect balance)
    workload_score REAL DEFAULT 50,
    burnout_risk REAL DEFAULT 0,  -- 0-100
    recommendation TEXT,
    factors TEXT,  -- JSON with contributing factors
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- Employee Availability Calendar
CREATE TABLE IF NOT EXISTS employee_availability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    availability_type TEXT NOT NULL,  -- work, vacation, sick, training, personal
    start_time TEXT,  -- HH:MM
    end_time TEXT,    -- HH:MM
    all_day INTEGER DEFAULT 1,
    notes TEXT,
    approved INTEGER DEFAULT 0,
    approved_by INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- Add new columns to employees table (idempotent)
-- These will be added via Python migration to handle ALTER TABLE safely

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_employee_skills_employee ON employee_skills(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_skills_type ON employee_skills(skill_type);
CREATE INDEX IF NOT EXISTS idx_employee_certs_employee ON employee_certifications(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_certs_expiry ON employee_certifications(expiry_date);
CREATE INDEX IF NOT EXISTS idx_employee_capacity_week ON employee_capacity(week_start);
CREATE INDEX IF NOT EXISTS idx_employee_capacity_emp ON employee_capacity(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_performance_emp ON employee_performance(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_ai_scores_emp ON employee_ai_scores(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_availability_date ON employee_availability(date);
CREATE INDEX IF NOT EXISTS idx_employee_availability_emp ON employee_availability(employee_id);
