-- ================================================================
-- MIGRATION 002: Planning Extended Features
-- Trvalkové školka, Recurring tasks, Materials, Photos, etc.
-- ================================================================

-- ================================================================
-- 1. TRVALKOVÉ ŠKOLKA 🌸
-- ================================================================

CREATE TABLE IF NOT EXISTS nursery_plants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    species TEXT NOT NULL,              -- Druh rostliny
    variety TEXT,                        -- Odrůda
    quantity INTEGER NOT NULL DEFAULT 0, -- Počet kusů
    unit TEXT DEFAULT 'ks',             -- Jednotka
    stage TEXT NOT NULL,                -- semínko/sazenice/prodejní/prodáno
    location TEXT,                       -- Skleník A, Záhon 1, etc
    planted_date DATE,                   -- Kdy zasazeno
    ready_date DATE,                     -- Kdy ready na prodej
    purchase_price DECIMAL(10,2),       -- Nákupní cena
    selling_price DECIMAL(10,2),        -- Prodejní cena
    cost_per_unit DECIMAL(10,2),        -- Náklady na pěstování/ks
    notes TEXT,
    photo_url TEXT,
    status TEXT DEFAULT 'active',       -- active/sold/dead
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nursery_watering_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER,
    schedule_type TEXT NOT NULL,        -- daily/weekly/as_needed
    frequency_days INTEGER,             -- Každých X dní
    last_watered DATE,
    next_watering DATE,
    skip_if_rain BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES nursery_plants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS nursery_watering_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER,
    watered_date DATE NOT NULL,
    amount_liters DECIMAL(10,2),
    watered_by INTEGER,
    weather_condition TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES nursery_plants(id) ON DELETE CASCADE,
    FOREIGN KEY (watered_by) REFERENCES employees(id)
);

-- ================================================================
-- 2. RECURRING TASKS 🔄
-- ================================================================

CREATE TABLE IF NOT EXISTS recurring_task_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    job_id INTEGER,                     -- Link na zakázku (veřejné prostranství)
    frequency TEXT NOT NULL,            -- daily/weekly/biweekly/monthly/quarterly/yearly
    frequency_value INTEGER DEFAULT 1,  -- Každých X (1=každý týden, 2=každé 2 týdny)
    day_of_week INTEGER,                -- 1-7 for weekly
    day_of_month INTEGER,               -- 1-31 for monthly
    start_date DATE NOT NULL,
    end_date DATE,                      -- NULL = infinite
    assigned_to INTEGER,                -- Default employee
    estimated_hours REAL,
    checklist TEXT,                     -- JSON array checklist items
    require_photos BOOLEAN DEFAULT 0,
    require_signature BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES employees(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS recurring_task_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    task_id INTEGER,                    -- Link to actual task when generated
    scheduled_date DATE NOT NULL,
    status TEXT DEFAULT 'pending',      -- pending/generated/skipped
    generated_at DATETIME,
    skipped_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES recurring_task_templates(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

-- ================================================================
-- 3. MATERIAL TRACKING 📦
-- ================================================================

CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,                      -- substrát/hnojivo/mulč/rostliny/nářadí
    unit TEXT NOT NULL,                 -- kg/L/ks/m3
    current_stock REAL DEFAULT 0,
    min_stock REAL DEFAULT 0,           -- Alert když pod touto hodnotou
    unit_price DECIMAL(10,2),
    supplier TEXT,
    location TEXT,                      -- Kde skladováno
    photo_url TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS material_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id INTEGER NOT NULL,
    movement_type TEXT NOT NULL,        -- in/out/adjustment
    quantity REAL NOT NULL,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    job_id INTEGER,                     -- Link když spotřeba na zakázce
    task_id INTEGER,                    -- Link když spotřeba na úkolu
    supplier TEXT,
    invoice_number TEXT,
    movement_date DATE NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- ================================================================
-- 4. PHOTO DOCUMENTATION 📸
-- ================================================================

CREATE TABLE IF NOT EXISTS task_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    job_id INTEGER,
    photo_type TEXT NOT NULL,           -- before/after/progress/issue
    file_path TEXT NOT NULL,
    file_name TEXT,
    file_size INTEGER,
    caption TEXT,
    taken_at DATETIME,
    gps_lat DECIMAL(10,8),
    gps_lon DECIMAL(11,8),
    uploaded_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

-- ================================================================
-- 5. PLANTS DATABASE 🌺
-- ================================================================

CREATE TABLE IF NOT EXISTS plant_species (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scientific_name TEXT NOT NULL,
    common_name TEXT NOT NULL,
    category TEXT,                      -- trvalka/keř/strom/jednoletka/cibuloviny
    light_requirement TEXT,             -- plné slunce/polostín/stín
    water_requirement TEXT,             -- nízká/střední/vysoká
    soil_type TEXT,                     -- písčitá/hlinitá/jílovitá
    hardiness_zone TEXT,                -- Zóna mrazuvzdornosti
    height_cm_min INTEGER,
    height_cm_max INTEGER,
    bloom_season TEXT,                  -- jaro/léto/podzim
    planting_season TEXT,               -- jaro/podzim
    care_difficulty TEXT,               -- snadná/střední/náročná
    companion_plants TEXT,              -- JSON array dobrých sousedů
    avoid_plants TEXT,                  -- JSON array špatných sousedů
    notes TEXT,
    photo_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- 6. MAINTENANCE CONTRACTS 📋
-- ================================================================

CREATE TABLE IF NOT EXISTS maintenance_contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    client_name TEXT NOT NULL,
    contract_number TEXT,
    contract_type TEXT,                 -- monthly/quarterly/yearly
    start_date DATE NOT NULL,
    end_date DATE,
    monthly_fee DECIMAL(10,2),
    yearly_fee DECIMAL(10,2),
    billing_day INTEGER,                -- Den v měsíci kdy fakturovat
    service_frequency TEXT,             -- weekly/biweekly/monthly
    scope_of_work TEXT,                 -- Co je zahrnuto
    sla_hours INTEGER,                  -- Do kolika hodin reakce
    auto_renew BOOLEAN DEFAULT 0,
    status TEXT DEFAULT 'active',       -- active/expired/cancelled
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS contract_invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    invoice_number TEXT,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status TEXT DEFAULT 'draft',        -- draft/sent/paid/overdue
    issued_date DATE,
    due_date DATE,
    paid_date DATE,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES maintenance_contracts(id) ON DELETE CASCADE
);

-- ================================================================
-- 7. SEASONAL PLANNER 🌱
-- ================================================================

CREATE TABLE IF NOT EXISTS seasonal_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season TEXT NOT NULL,               -- spring/summer/autumn/winter
    month INTEGER NOT NULL,             -- 1-12
    week INTEGER,                       -- 1-4
    task_type TEXT NOT NULL,            -- planting/pruning/maintenance/harvest
    title TEXT NOT NULL,
    description TEXT,
    plant_categories TEXT,              -- JSON array které rostliny
    priority TEXT DEFAULT 'medium',
    estimated_hours REAL,
    weather_dependent BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- INDEXES
-- ================================================================

CREATE INDEX IF NOT EXISTS idx_nursery_plants_stage ON nursery_plants(stage);
CREATE INDEX IF NOT EXISTS idx_nursery_plants_status ON nursery_plants(status);
CREATE INDEX IF NOT EXISTS idx_nursery_watering_next ON nursery_watering_schedule(next_watering);

CREATE INDEX IF NOT EXISTS idx_recurring_templates_active ON recurring_task_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_recurring_instances_date ON recurring_task_instances(scheduled_date);

CREATE INDEX IF NOT EXISTS idx_materials_stock ON materials(current_stock);
CREATE INDEX IF NOT EXISTS idx_material_movements_date ON material_movements(movement_date);

CREATE INDEX IF NOT EXISTS idx_task_photos_task ON task_photos(task_id);
CREATE INDEX IF NOT EXISTS idx_task_photos_job ON task_photos(job_id);

CREATE INDEX IF NOT EXISTS idx_contracts_status ON maintenance_contracts(status);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON contract_invoices(status);

CREATE INDEX IF NOT EXISTS idx_seasonal_month ON seasonal_tasks(month);

-- ================================================================
-- DONE
-- ================================================================
