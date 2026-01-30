-- ============================================================================
-- GREEN DAVID - EXTENDED JOBS SCHEMA
-- Kompletní struktura pro profesionální správu zakázek
-- ============================================================================

-- ============================================================================
-- 1. HLAVNÍ TABULKA JOBS - Rozšířená
-- ============================================================================

CREATE TABLE IF NOT EXISTS jobs_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  
  -- Základní informace
  title TEXT NOT NULL,
  code TEXT UNIQUE,
  type TEXT CHECK(type IN ('construction','landscaping','maintenance','renovation')) DEFAULT 'construction',
  status TEXT CHECK(status IN ('Plán','Aktivní','Pozastavené','Dokončené','Zrušené')) DEFAULT 'Plán',
  priority TEXT CHECK(priority IN ('low','medium','high','urgent')) DEFAULT 'medium',
  description TEXT,
  internal_note TEXT,  -- Poznámka jen pro tým, klient nevidí
  tags TEXT,           -- JSON array: ["terasa", "zavlažování"]
  
  -- Časové informace
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  start_date DATE,
  planned_end_date DATE,
  actual_end_date DATE,
  deadline DATE,
  deadline_type TEXT CHECK(deadline_type IN ('soft','hard','flexible')) DEFAULT 'soft',
  deadline_reason TEXT,
  buffer_days INTEGER DEFAULT 0,
  weather_dependent BOOLEAN DEFAULT false,
  seasonal_constraints TEXT,
  
  -- Finanční informace
  estimated_value DECIMAL(12,2),
  estimated_hours INTEGER,
  actual_value DECIMAL(12,2) DEFAULT 0,
  actual_hours INTEGER DEFAULT 0,
  
  -- Rozpočet breakdown
  budget_labor DECIMAL(12,2) DEFAULT 0,
  budget_materials DECIMAL(12,2) DEFAULT 0,
  budget_equipment DECIMAL(12,2) DEFAULT 0,
  budget_other DECIMAL(12,2) DEFAULT 0,
  
  -- Pricing
  pricing_type TEXT CHECK(pricing_type IN ('fixed','hourly','materials_plus')) DEFAULT 'fixed',
  hourly_rate DECIMAL(10,2),
  payment_terms TEXT,
  
  -- DPH
  vat_rate INTEGER DEFAULT 21,
  price_includes_vat BOOLEAN DEFAULT true,
  
  -- Tým
  project_manager_id INTEGER REFERENCES users(id),
  
  -- Metriky (auto-calculated)
  completion_percent INTEGER DEFAULT 0,
  budget_spent_percent INTEGER DEFAULT 0,
  profit_margin DECIMAL(5,2),
  on_track BOOLEAN DEFAULT true,
  
  -- Pro zpětnou kompatibilitu
  city TEXT,
  note TEXT,
  date DATE,
  completed_at DATETIME,
  
  -- Metadata
  created_by INTEGER REFERENCES users(id),
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  -- Template info
  created_from_template TEXT,
  is_template BOOLEAN DEFAULT false
);

-- ============================================================================
-- 2. KLIENT INFO - Rozšířené kontaktní údaje
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_clients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  
  -- Základní údaje
  name TEXT NOT NULL,
  company TEXT,
  ico TEXT,
  dic TEXT,
  
  -- Kontakty
  email TEXT,
  phone TEXT,
  phone_secondary TEXT,
  preferred_contact TEXT CHECK(preferred_contact IN ('email','phone','sms','meeting')) DEFAULT 'phone',
  
  -- Fakturační adresa
  billing_street TEXT,
  billing_city TEXT,
  billing_zip TEXT,
  billing_country TEXT DEFAULT 'CZ',
  
  -- Klientská historie
  client_since DATE,
  total_projects INTEGER DEFAULT 1,
  total_revenue DECIMAL(12,2) DEFAULT 0,
  payment_rating TEXT CHECK(payment_rating IN ('excellent','good','slow','problematic')) DEFAULT 'good',
  
  -- Poznámky
  notes TEXT,
  
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(job_id)
);

-- ============================================================================
-- 3. LOKACE STAVENIŠTĚ - GPS, přístup, parkování
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_locations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  
  -- Adresa
  street TEXT,
  city TEXT,
  zip TEXT,
  country TEXT DEFAULT 'CZ',
  
  -- GPS souřadnice
  lat DECIMAL(10,6),
  lng DECIMAL(10,6),
  
  -- Parkovací možnosti
  parking TEXT,
  parking_notes TEXT,
  
  -- Přístup
  access_notes TEXT,
  gate_code TEXT,
  key_location TEXT,
  
  -- Dostupné zdroje
  has_electricity BOOLEAN DEFAULT false,
  has_water BOOLEAN DEFAULT false,
  has_toilet BOOLEAN DEFAULT false,
  
  -- Sousedé (pro hlučné práce)
  neighbors_info TEXT,
  noise_restrictions TEXT,
  
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(job_id)
);

-- ============================================================================
-- 4. MILNÍKY - Klíčové body projektu
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_milestones (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  
  name TEXT NOT NULL,
  description TEXT,
  
  -- Datumy
  planned_date DATE,
  actual_date DATE,
  
  -- Status
  status TEXT CHECK(status IN ('pending','in_progress','completed','skipped','blocked')) DEFAULT 'pending',
  completion_percent INTEGER DEFAULT 0,
  
  -- Pořadí
  order_num INTEGER DEFAULT 0,
  
  -- Závislosti
  depends_on INTEGER REFERENCES job_milestones(id),
  
  -- Upozornění
  reminder_days_before INTEGER DEFAULT 3,
  
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_milestones_job ON job_milestones(job_id);
CREATE INDEX idx_milestones_status ON job_milestones(status);

-- ============================================================================
-- 5. MATERIÁL - Tracking objednávek a dodávek
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_materials (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  
  -- Základní info
  name TEXT NOT NULL,
  category TEXT, -- "cement", "dlažba", "elektromateriál"
  
  -- Množství
  quantity DECIMAL(10,2),
  unit TEXT DEFAULT 'ks', -- "ks", "m", "m2", "m3", "kg", "t"
  
  -- Ceny
  price_per_unit DECIMAL(10,2),
  total_price DECIMAL(10,2),
  
  -- Dodavatel
  supplier TEXT,
  supplier_contact TEXT,
  
  -- Objednávka
  ordered BOOLEAN DEFAULT false,
  order_date DATE,
  order_number TEXT,
  
  -- Dodání
  delivery_date DATE,
  delivery_status TEXT CHECK(delivery_status IN ('pending','confirmed','in_transit','delivered','cancelled')) DEFAULT 'pending',
  actual_delivery_date DATE,
  
  -- Lokace
  storage_location TEXT, -- "Sklad Beroun", "Na staveništi"
  
  -- Poznámky
  notes TEXT,
  
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_materials_job ON job_materials(job_id);
CREATE INDEX idx_materials_status ON job_materials(delivery_status);

-- ============================================================================
-- 6. TECHNIKA - Rezervace strojů a nářadí
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_equipment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  
  name TEXT NOT NULL,
  type TEXT, -- "bagr", "vibrační deska", "míchačka"
  
  -- Časové údaje
  days_needed INTEGER,
  date_from DATE,
  date_to DATE,
  
  -- Cena
  cost_per_day DECIMAL(10,2),
  total_cost DECIMAL(10,2),
  
  -- Dodavatel
  supplier TEXT,
  supplier_contact TEXT,
  
  -- Rezervace
  reservation_date DATE,
  reservation_confirmed BOOLEAN DEFAULT false,
  
  -- Status
  status TEXT CHECK(status IN ('needed','reserved','in_use','returned','cancelled')) DEFAULT 'needed',
  
  -- Vlastnictví
  owned BOOLEAN DEFAULT false, -- true = vlastní technika
  
  -- Poznámky
  notes TEXT,
  
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_equipment_job ON job_equipment(job_id);
CREATE INDEX idx_equipment_status ON job_equipment(status);

-- ============================================================================
-- 7. PŘIŘAZENÍ TÝMU - Kdo pracuje na projektu
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_team_assignments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  
  role TEXT CHECK(role IN ('manager','worker','supervisor','assistant')) DEFAULT 'worker',
  
  -- Plánované hodiny
  hours_planned INTEGER DEFAULT 0,
  hours_actual INTEGER DEFAULT 0,
  
  -- Dostupnost
  availability TEXT CHECK(availability IN ('full-time','part-time','on-call','unavailable')) DEFAULT 'full-time',
  
  -- Datum přiřazení
  assigned_date DATE DEFAULT (date('now')),
  removed_date DATE,
  is_active BOOLEAN DEFAULT true,
  
  -- Poznámky
  notes TEXT,
  
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(job_id, employee_id, assigned_date)
);

CREATE INDEX idx_team_job ON job_team_assignments(job_id);
CREATE INDEX idx_team_employee ON job_team_assignments(employee_id);

-- ============================================================================
-- 8. EXTERNÍ DODAVATELÉ - Subdodávky
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_subcontractors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  
  name TEXT NOT NULL,
  company TEXT,
  service TEXT NOT NULL, -- "Elektroinstalace", "Instalatérské práce"
  
  -- Kontakt
  contact_person TEXT,
  phone TEXT,
  email TEXT,
  
  -- Cena
  price DECIMAL(10,2),
  payment_terms TEXT,
  
  -- Status
  status TEXT CHECK(status IN ('requested','confirmed','in_progress','completed','cancelled')) DEFAULT 'requested',
  
  -- Datumy
  start_date DATE,
  end_date DATE,
  
  -- Dokumenty
  contract_signed BOOLEAN DEFAULT false,
  invoice_number TEXT,
  
  notes TEXT,
  
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subcontractors_job ON job_subcontractors(job_id);

-- ============================================================================
-- 9. RIZIKA - Risk management
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_risks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  
  description TEXT NOT NULL,
  category TEXT, -- "weather", "technical", "financial", "legal"
  
  -- Hodnocení
  probability TEXT CHECK(probability IN ('low','medium','high')) DEFAULT 'medium',
  impact TEXT CHECK(impact IN ('low','medium','high','critical')) DEFAULT 'medium',
  risk_score INTEGER, -- probability * impact (1-9)
  
  -- Mitigation
  mitigation_plan TEXT,
  contingency_plan TEXT,
  
  -- Status
  status TEXT CHECK(status IN ('identified','monitoring','mitigated','occurred','closed')) DEFAULT 'identified',
  
  -- Owner
  owner_id INTEGER REFERENCES users(id),
  
  -- Datumy
  identified_date DATE DEFAULT (date('now')),
  review_date DATE,
  closed_date DATE,
  
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_risks_job ON job_risks(job_id);
CREATE INDEX idx_risks_status ON job_risks(status);

-- ============================================================================
-- 10. KOMUNIKAČNÍ LOG - Historie komunikace s klientem
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_communications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  
  -- Datum a čas
  communication_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  -- Typ
  type TEXT CHECK(type IN ('phone','email','meeting','sms','note','video')) DEFAULT 'note',
  direction TEXT CHECK(direction IN ('inbound','outbound','internal')) DEFAULT 'internal',
  
  -- Obsah
  subject TEXT,
  summary TEXT NOT NULL,
  full_content TEXT,
  
  -- Účastníci
  by_user_id INTEGER REFERENCES users(id),
  with_client BOOLEAN DEFAULT true,
  participants TEXT, -- JSON array of names
  
  -- Výsledek
  outcome TEXT CHECK(outcome IN ('positive','neutral','negative','action_required','no_answer')),
  action_items TEXT, -- JSON array of action items
  
  -- Interní vs. externí
  is_internal BOOLEAN DEFAULT false,
  
  -- Přílohy
  attachments TEXT, -- JSON array of file paths
  
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_communications_job ON job_communications(job_id);
CREATE INDEX idx_communications_date ON job_communications(communication_date);

-- ============================================================================
-- 11. CHANGE REQUESTS - Změnové požadavky
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_change_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  
  -- Kdo požaduje
  requested_by TEXT CHECK(requested_by IN ('client','team','external')) DEFAULT 'client',
  requested_by_name TEXT,
  
  -- Popis změny
  description TEXT NOT NULL,
  reason TEXT,
  
  -- Dopady
  impact_cost DECIMAL(10,2),
  impact_time INTEGER, -- days
  impact_scope TEXT,
  
  -- Priorita
  urgency TEXT CHECK(urgency IN ('low','medium','high','critical')) DEFAULT 'medium',
  
  -- Status
  status TEXT CHECK(status IN ('pending','approved','rejected','implemented','cancelled')) DEFAULT 'pending',
  
  -- Schvalování
  approved_by INTEGER REFERENCES users(id),
  approved_date DATE,
  rejection_reason TEXT,
  
  -- Implementace
  implemented_date DATE,
  implementation_notes TEXT,
  
  -- Datumy
  requested_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_change_requests_job ON job_change_requests(job_id);
CREATE INDEX idx_change_requests_status ON job_change_requests(status);

-- ============================================================================
-- 12. PLATBY - Payment tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  
  -- Plánovaná platba
  planned_date DATE,
  amount DECIMAL(12,2) NOT NULL,
  percentage INTEGER, -- % z celkové částky
  
  -- Typ platby
  payment_type TEXT CHECK(payment_type IN ('advance','progress','final','penalty','refund')) DEFAULT 'progress',
  
  -- Status
  status TEXT CHECK(status IN ('pending','sent','paid','overdue','cancelled','refunded')) DEFAULT 'pending',
  
  -- Skutečná platba
  paid_date DATE,
  paid_amount DECIMAL(12,2),
  payment_method TEXT CHECK(payment_method IN ('bank_transfer','cash','card','other')),
  
  -- Faktura
  invoice_id TEXT,
  invoice_date DATE,
  invoice_due_date DATE,
  
  -- Poznámky
  note TEXT,
  
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payments_job ON job_payments(job_id);
CREATE INDEX idx_payments_status ON job_payments(status);
CREATE INDEX idx_payments_due_date ON job_payments(invoice_due_date);

-- ============================================================================
-- 13. DOKUMENTY - Smlouvy, povolení, plány
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  
  -- Základní info
  name TEXT NOT NULL,
  type TEXT CHECK(type IN ('contract','permit','blueprint','invoice','photo','other')) DEFAULT 'other',
  category TEXT, -- "legal", "technical", "financial"
  
  -- Soubor
  file_path TEXT NOT NULL,
  file_size INTEGER, -- bytes
  mime_type TEXT,
  
  -- Verze
  version INTEGER DEFAULT 1,
  is_latest BOOLEAN DEFAULT true,
  replaces_document_id INTEGER REFERENCES job_documents(id),
  
  -- Metadata
  description TEXT,
  uploaded_by INTEGER REFERENCES users(id),
  uploaded_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  -- Pro smlouvy/povolení
  signed BOOLEAN DEFAULT false,
  signed_date DATE,
  approval_status TEXT CHECK(approval_status IN ('pending','approved','rejected')) DEFAULT 'pending',
  approval_date DATE,
  expires_date DATE,
  
  -- Tags
  tags TEXT, -- JSON array
  
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_job ON job_documents(job_id);
CREATE INDEX idx_documents_type ON job_documents(type);

-- ============================================================================
-- 14. FOTODOKUMENTACE - Před/Průběh/Po fotky
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_photos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  
  -- Soubor
  file_path TEXT NOT NULL,
  thumbnail_path TEXT,
  
  -- Kategorie
  phase TEXT CHECK(phase IN ('before','progress','after','issue','other')) DEFAULT 'progress',
  milestone_id INTEGER REFERENCES job_milestones(id),
  
  -- Metadata
  caption TEXT,
  description TEXT,
  
  -- Kdo, kdy
  taken_by INTEGER REFERENCES users(id),
  taken_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  -- Lokace v projektu
  location_on_site TEXT, -- "Terasa", "Zadní část zahrady"
  
  -- GPS
  lat DECIMAL(10,6),
  lng DECIMAL(10,6),
  
  -- Pro issues
  related_issue_id INTEGER REFERENCES issues(id),
  severity TEXT CHECK(severity IN ('low','medium','high','critical')),
  
  -- Tags
  tags TEXT, -- JSON array
  
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_photos_job ON job_photos(job_id);
CREATE INDEX idx_photos_phase ON job_photos(phase);
CREATE INDEX idx_photos_date ON job_photos(taken_date);

-- ============================================================================
-- 15. METRIKY & KPI - Auto-calculated metrics
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  
  -- Timestamp
  calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  -- Časové metriky
  days_elapsed INTEGER,
  days_remaining INTEGER,
  days_planned INTEGER,
  schedule_variance INTEGER, -- negative = ahead of schedule
  
  -- Finanční metriky
  budget_spent DECIMAL(12,2),
  budget_remaining DECIMAL(12,2),
  budget_variance DECIMAL(12,2), -- negative = under budget
  cost_performance_index DECIMAL(5,2), -- >1 = good
  
  -- Pokrok
  completion_percent INTEGER,
  on_track BOOLEAN,
  
  -- Produktivita
  avg_hours_per_day DECIMAL(5,2),
  productive_hours_percent INTEGER,
  
  -- Kvalita
  defects_count INTEGER DEFAULT 0,
  rework_hours INTEGER DEFAULT 0,
  
  -- Predikce
  predicted_completion_date DATE,
  predicted_final_cost DECIMAL(12,2),
  predicted_profit DECIMAL(12,2),
  confidence_level TEXT CHECK(confidence_level IN ('low','medium','high'))
);

CREATE INDEX idx_metrics_job ON job_metrics(job_id);
CREATE INDEX idx_metrics_date ON job_metrics(calculated_at);

-- ============================================================================
-- VIEWS - Pro snadnější dotazování
-- ============================================================================

-- View: Kompletní info o zakázce
CREATE VIEW IF NOT EXISTS v_jobs_complete AS
SELECT 
  j.*,
  c.name as client_name,
  c.phone as client_phone,
  c.email as client_email,
  l.city as location_city,
  l.street as location_street,
  u.username as project_manager_name,
  (SELECT COUNT(*) FROM job_milestones WHERE job_id = j.id) as milestones_count,
  (SELECT COUNT(*) FROM job_milestones WHERE job_id = j.id AND status = 'completed') as milestones_completed,
  (SELECT COUNT(*) FROM job_team_assignments WHERE job_id = j.id AND is_active = true) as team_size,
  (SELECT SUM(total_price) FROM job_materials WHERE job_id = j.id) as materials_total_cost,
  (SELECT COUNT(*) FROM job_materials WHERE job_id = j.id AND delivery_status = 'delivered') as materials_delivered,
  (SELECT COUNT(*) FROM job_photos WHERE job_id = j.id) as photos_count,
  (SELECT COUNT(*) FROM issues WHERE job_id = j.id AND status != 'resolved') as active_issues_count
FROM jobs j
LEFT JOIN job_clients c ON j.id = c.job_id
LEFT JOIN job_locations l ON j.id = l.job_id
LEFT JOIN users u ON j.project_manager_id = u.id;

-- View: Přehled financí
CREATE VIEW IF NOT EXISTS v_jobs_finances AS
SELECT 
  j.id,
  j.title,
  j.estimated_value,
  j.actual_value,
  j.budget_labor + j.budget_materials + j.budget_equipment + j.budget_other as total_budget,
  (SELECT SUM(amount) FROM job_payments WHERE job_id = j.id AND status = 'paid') as total_paid,
  (SELECT SUM(amount) FROM job_payments WHERE job_id = j.id AND status IN ('pending','overdue')) as total_outstanding,
  j.estimated_value - j.actual_value as remaining_budget,
  CASE 
    WHEN j.estimated_value > 0 THEN 
      ROUND((j.estimated_value - j.actual_value) * 100.0 / j.estimated_value, 2)
    ELSE 0
  END as profit_margin_percent
FROM jobs j;

-- View: Timeline přehled
CREATE VIEW IF NOT EXISTS v_jobs_timeline AS
SELECT
  j.id,
  j.title,
  j.start_date,
  j.deadline,
  j.planned_end_date,
  julianday(j.deadline) - julianday('now') as days_to_deadline,
  julianday('now') - julianday(j.start_date) as days_elapsed,
  (SELECT MIN(planned_date) FROM job_milestones WHERE job_id = j.id AND status = 'pending') as next_milestone_date,
  (SELECT name FROM job_milestones WHERE job_id = j.id AND status = 'pending' ORDER BY planned_date LIMIT 1) as next_milestone_name
FROM jobs j
WHERE j.status IN ('Aktivní', 'Pozastavené');

-- ============================================================================
-- TRIGGERS - Auto-update logic
-- ============================================================================

-- Update updated_at na jobs
CREATE TRIGGER IF NOT EXISTS update_jobs_timestamp 
AFTER UPDATE ON jobs
BEGIN
  UPDATE jobs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Auto-calculate completion percent při update milníků
CREATE TRIGGER IF NOT EXISTS update_job_completion
AFTER UPDATE OF status ON job_milestones
BEGIN
  UPDATE jobs 
  SET completion_percent = (
    SELECT CAST(COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*) AS INTEGER)
    FROM job_milestones 
    WHERE job_id = NEW.job_id
  )
  WHERE id = NEW.job_id;
END;

-- Auto-update total_price při změně materiálu
CREATE TRIGGER IF NOT EXISTS update_material_total_price
AFTER UPDATE OF quantity, price_per_unit ON job_materials
BEGIN
  UPDATE job_materials 
  SET total_price = NEW.quantity * NEW.price_per_unit
  WHERE id = NEW.id;
END;

-- ============================================================================
-- KONEC SCHÉMATU
-- ============================================================================

-- Poznámka: Toto schema je navrženo pro SQLite
-- Pro migrace z existující DB použij migration script níže
