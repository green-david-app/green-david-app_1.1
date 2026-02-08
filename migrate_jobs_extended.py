#!/usr/bin/env python3
"""
GREEN DAVID - Jobs Extended Migration
=====================================
Tento script upgradne stávající databázi na novou strukturu s rozšířenými zakázkami.

USAGE:
    python migrate_jobs_extended.py

BACKUP:
    Script automaticky vytvoří zálohu DB před migrací: app.db.backup_TIMESTAMP
"""

import sqlite3
import sys
import os
from datetime import datetime
import json
import shutil

def backup_database(db_path):
    """Vytvoří zálohu databáze"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    
    print(f"📦 Vytvářím zálohu: {backup_path}")
    shutil.copy2(db_path, backup_path)
    print(f"✅ Záloha vytvořena")
    return backup_path

def table_exists(conn, table_name):
    """Zkontroluje jestli tabulka existuje"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def column_exists(conn, table_name, column_name):
    """Zkontroluje jestli sloupec existuje"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def migrate_database(db_path):
    """Hlavní migrace"""
    print("\n" + "="*60)
    print("🚀 GREEN DAVID - Jobs Extended Migration")
    print("="*60 + "\n")
    
    if not os.path.exists(db_path):
        print(f"❌ ERROR: Databáze {db_path} neexistuje!")
        return False
    
    # Záloha
    backup_path = backup_database(db_path)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("\n📊 Kontroluji stávající strukturu...")
        
        # ====================================================================
        # 1. UPGRADE HLAVNÍ TABULKY JOBS
        # ====================================================================
        
        print("\n1️⃣  Upgraduji tabulku 'jobs'...")
        
        # Přidání nových sloupců do jobs
        new_columns = [
            ("type", "TEXT DEFAULT 'construction'"),
            ("priority", "TEXT DEFAULT 'medium'"),
            ("description", "TEXT"),
            ("internal_note", "TEXT"),
            ("tags", "TEXT"),
            ("planned_end_date", "DATE"),
            ("actual_end_date", "DATE"),
            ("deadline", "DATE"),
            ("deadline_type", "TEXT DEFAULT 'soft'"),
            ("deadline_reason", "TEXT"),
            ("buffer_days", "INTEGER DEFAULT 0"),
            ("weather_dependent", "BOOLEAN DEFAULT false"),
            ("seasonal_constraints", "TEXT"),
            ("estimated_value", "DECIMAL(12,2)"),
            ("estimated_hours", "INTEGER"),
            ("actual_value", "DECIMAL(12,2) DEFAULT 0"),
            ("actual_hours", "INTEGER DEFAULT 0"),
            ("budget_labor", "DECIMAL(12,2) DEFAULT 0"),
            ("budget_materials", "DECIMAL(12,2) DEFAULT 0"),
            ("budget_equipment", "DECIMAL(12,2) DEFAULT 0"),
            ("budget_other", "DECIMAL(12,2) DEFAULT 0"),
            ("pricing_type", "TEXT DEFAULT 'fixed'"),
            ("hourly_rate", "DECIMAL(10,2)"),
            ("payment_terms", "TEXT"),
            ("vat_rate", "INTEGER DEFAULT 21"),
            ("price_includes_vat", "BOOLEAN DEFAULT true"),
            ("project_manager_id", "INTEGER"),
            ("completion_percent", "INTEGER DEFAULT 0"),
            ("budget_spent_percent", "INTEGER DEFAULT 0"),
            ("profit_margin", "DECIMAL(5,2)"),
            ("on_track", "BOOLEAN DEFAULT true"),
            ("created_by", "INTEGER"),
            ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("created_from_template", "TEXT"),
            ("is_template", "BOOLEAN DEFAULT false"),
        ]
        
        added_count = 0
        for col_name, col_def in new_columns:
            if not column_exists(conn, 'jobs', col_name):
                try:
                    cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_def}")
                    added_count += 1
                except sqlite3.OperationalError as e:
                    print(f"   ⚠️  Warning: Nepodařilo se přidat sloupec {col_name}: {e}")
        
        print(f"   ✅ Přidáno {added_count} nových sloupců")
        
        # ====================================================================
        # 2. VYTVOŘENÍ NOVÝCH TABULEK
        # ====================================================================
        
        tables_to_create = {
            "job_clients": """
                CREATE TABLE IF NOT EXISTS job_clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    company TEXT,
                    ico TEXT,
                    dic TEXT,
                    email TEXT,
                    phone TEXT,
                    phone_secondary TEXT,
                    preferred_contact TEXT DEFAULT 'phone',
                    billing_street TEXT,
                    billing_city TEXT,
                    billing_zip TEXT,
                    billing_country TEXT DEFAULT 'CZ',
                    client_since DATE,
                    total_projects INTEGER DEFAULT 1,
                    total_revenue DECIMAL(12,2) DEFAULT 0,
                    payment_rating TEXT DEFAULT 'good',
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(job_id)
                )
            """,
            
            "job_locations": """
                CREATE TABLE IF NOT EXISTS job_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    street TEXT,
                    city TEXT,
                    zip TEXT,
                    country TEXT DEFAULT 'CZ',
                    lat DECIMAL(10,6),
                    lng DECIMAL(10,6),
                    parking TEXT,
                    parking_notes TEXT,
                    access_notes TEXT,
                    gate_code TEXT,
                    key_location TEXT,
                    has_electricity BOOLEAN DEFAULT false,
                    has_water BOOLEAN DEFAULT false,
                    has_toilet BOOLEAN DEFAULT false,
                    neighbors_info TEXT,
                    noise_restrictions TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(job_id)
                )
            """,
            
            "job_milestones": """
                CREATE TABLE IF NOT EXISTS job_milestones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    description TEXT,
                    planned_date DATE,
                    actual_date DATE,
                    status TEXT DEFAULT 'pending',
                    completion_percent INTEGER DEFAULT 0,
                    order_num INTEGER DEFAULT 0,
                    depends_on INTEGER REFERENCES job_milestones(id),
                    reminder_days_before INTEGER DEFAULT 3,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            "job_materials": """
                CREATE TABLE IF NOT EXISTS job_materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    category TEXT,
                    quantity DECIMAL(10,2),
                    unit TEXT DEFAULT 'ks',
                    price_per_unit DECIMAL(10,2),
                    total_price DECIMAL(10,2),
                    supplier TEXT,
                    supplier_contact TEXT,
                    ordered BOOLEAN DEFAULT false,
                    order_date DATE,
                    order_number TEXT,
                    delivery_date DATE,
                    delivery_status TEXT DEFAULT 'pending',
                    actual_delivery_date DATE,
                    storage_location TEXT,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            "job_equipment": """
                CREATE TABLE IF NOT EXISTS job_equipment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    type TEXT,
                    days_needed INTEGER,
                    date_from DATE,
                    date_to DATE,
                    cost_per_day DECIMAL(10,2),
                    total_cost DECIMAL(10,2),
                    supplier TEXT,
                    supplier_contact TEXT,
                    reservation_date DATE,
                    reservation_confirmed BOOLEAN DEFAULT false,
                    status TEXT DEFAULT 'needed',
                    owned BOOLEAN DEFAULT false,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            "job_team_assignments": """
                CREATE TABLE IF NOT EXISTS job_team_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                    role TEXT DEFAULT 'worker',
                    hours_planned INTEGER DEFAULT 0,
                    hours_actual INTEGER DEFAULT 0,
                    availability TEXT DEFAULT 'full-time',
                    assigned_date DATE DEFAULT (date('now')),
                    removed_date DATE,
                    is_active BOOLEAN DEFAULT true,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(job_id, employee_id, assigned_date)
                )
            """,
            
            "job_subcontractors": """
                CREATE TABLE IF NOT EXISTS job_subcontractors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    company TEXT,
                    service TEXT NOT NULL,
                    contact_person TEXT,
                    phone TEXT,
                    email TEXT,
                    price DECIMAL(10,2),
                    payment_terms TEXT,
                    status TEXT DEFAULT 'requested',
                    start_date DATE,
                    end_date DATE,
                    contract_signed BOOLEAN DEFAULT false,
                    invoice_number TEXT,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            "job_risks": """
                CREATE TABLE IF NOT EXISTS job_risks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    description TEXT NOT NULL,
                    category TEXT,
                    probability TEXT DEFAULT 'medium',
                    impact TEXT DEFAULT 'medium',
                    risk_score INTEGER,
                    mitigation_plan TEXT,
                    contingency_plan TEXT,
                    status TEXT DEFAULT 'identified',
                    owner_id INTEGER REFERENCES users(id),
                    identified_date DATE DEFAULT (date('now')),
                    review_date DATE,
                    closed_date DATE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            "job_communications": """
                CREATE TABLE IF NOT EXISTS job_communications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    communication_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    type TEXT DEFAULT 'note',
                    direction TEXT DEFAULT 'internal',
                    subject TEXT,
                    summary TEXT NOT NULL,
                    full_content TEXT,
                    by_user_id INTEGER REFERENCES users(id),
                    with_client BOOLEAN DEFAULT true,
                    participants TEXT,
                    outcome TEXT,
                    action_items TEXT,
                    is_internal BOOLEAN DEFAULT false,
                    attachments TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            "job_change_requests": """
                CREATE TABLE IF NOT EXISTS job_change_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    requested_by TEXT DEFAULT 'client',
                    requested_by_name TEXT,
                    description TEXT NOT NULL,
                    reason TEXT,
                    impact_cost DECIMAL(10,2),
                    impact_time INTEGER,
                    impact_scope TEXT,
                    urgency TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    approved_by INTEGER REFERENCES users(id),
                    approved_date DATE,
                    rejection_reason TEXT,
                    implemented_date DATE,
                    implementation_notes TEXT,
                    requested_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            "job_payments": """
                CREATE TABLE IF NOT EXISTS job_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    planned_date DATE,
                    amount DECIMAL(12,2) NOT NULL,
                    percentage INTEGER,
                    payment_type TEXT DEFAULT 'progress',
                    status TEXT DEFAULT 'pending',
                    paid_date DATE,
                    paid_amount DECIMAL(12,2),
                    payment_method TEXT,
                    invoice_id TEXT,
                    invoice_date DATE,
                    invoice_due_date DATE,
                    note TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            "job_documents": """
                CREATE TABLE IF NOT EXISTS job_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    type TEXT DEFAULT 'other',
                    category TEXT,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    mime_type TEXT,
                    version INTEGER DEFAULT 1,
                    is_latest BOOLEAN DEFAULT true,
                    replaces_document_id INTEGER REFERENCES job_documents(id),
                    description TEXT,
                    uploaded_by INTEGER REFERENCES users(id),
                    uploaded_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    signed BOOLEAN DEFAULT false,
                    signed_date DATE,
                    approval_status TEXT DEFAULT 'pending',
                    approval_date DATE,
                    expires_date DATE,
                    tags TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            "job_photos": """
                CREATE TABLE IF NOT EXISTS job_photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    file_path TEXT NOT NULL,
                    thumbnail_path TEXT,
                    phase TEXT DEFAULT 'progress',
                    milestone_id INTEGER REFERENCES job_milestones(id),
                    caption TEXT,
                    description TEXT,
                    taken_by INTEGER REFERENCES users(id),
                    taken_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    location_on_site TEXT,
                    lat DECIMAL(10,6),
                    lng DECIMAL(10,6),
                    related_issue_id INTEGER REFERENCES issues(id),
                    severity TEXT,
                    tags TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            "job_metrics": """
                CREATE TABLE IF NOT EXISTS job_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    days_elapsed INTEGER,
                    days_remaining INTEGER,
                    days_planned INTEGER,
                    schedule_variance INTEGER,
                    budget_spent DECIMAL(12,2),
                    budget_remaining DECIMAL(12,2),
                    budget_variance DECIMAL(12,2),
                    cost_performance_index DECIMAL(5,2),
                    completion_percent INTEGER,
                    on_track BOOLEAN,
                    avg_hours_per_day DECIMAL(5,2),
                    productive_hours_percent INTEGER,
                    defects_count INTEGER DEFAULT 0,
                    rework_hours INTEGER DEFAULT 0,
                    predicted_completion_date DATE,
                    predicted_final_cost DECIMAL(12,2),
                    predicted_profit DECIMAL(12,2),
                    confidence_level TEXT
                )
            """
        }
        
        print("\n2️⃣  Vytvářím nové tabulky...")
        created_count = 0
        for table_name, create_sql in tables_to_create.items():
            if not table_exists(conn, table_name):
                cursor.execute(create_sql)
                created_count += 1
                print(f"   ✅ Vytvořena tabulka: {table_name}")
            else:
                print(f"   ⏭️  Tabulka {table_name} již existuje")
        
        print(f"\n   ✅ Vytvořeno {created_count} nových tabulek")
        
        # ====================================================================
        # 3. MIGRACE EXISTUJÍCÍCH DAT
        # ====================================================================
        
        print("\n3️⃣  Migruji existující data...")
        
        # Migrace klientů z jobs.client do job_clients
        cursor.execute("""
            SELECT id, client, city FROM jobs 
            WHERE client IS NOT NULL AND client != ''
        """)
        jobs_data = cursor.fetchall()
        
        migrated_clients = 0
        for job in jobs_data:
            job_id = job['id']
            client_name = job['client']
            
            # Zkontroluj jestli už není migrovaný
            cursor.execute("SELECT id FROM job_clients WHERE job_id = ?", (job_id,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO job_clients (job_id, name)
                    VALUES (?, ?)
                """, (job_id, client_name))
                migrated_clients += 1
        
        print(f"   ✅ Migrováno {migrated_clients} klientů")
        
        # Migrace lokací z jobs.city do job_locations
        migrated_locations = 0
        for job in jobs_data:
            job_id = job['id']
            city = job['city']
            
            if city:
                cursor.execute("SELECT id FROM job_locations WHERE job_id = ?", (job_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO job_locations (job_id, city)
                        VALUES (?, ?)
                    """, (job_id, city))
                    migrated_locations += 1
        
        print(f"   ✅ Migrováno {migrated_locations} lokací")
        
        # ====================================================================
        # 4. VYTVOŘENÍ INDEXŮ
        # ====================================================================
        
        print("\n4️⃣  Vytvářím indexy...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_milestones_job ON job_milestones(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_milestones_status ON job_milestones(status)",
            "CREATE INDEX IF NOT EXISTS idx_materials_job ON job_materials(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_materials_status ON job_materials(delivery_status)",
            "CREATE INDEX IF NOT EXISTS idx_equipment_job ON job_equipment(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_equipment_status ON job_equipment(status)",
            "CREATE INDEX IF NOT EXISTS idx_team_job ON job_team_assignments(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_team_employee ON job_team_assignments(employee_id)",
            "CREATE INDEX IF NOT EXISTS idx_subcontractors_job ON job_subcontractors(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_risks_job ON job_risks(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_risks_status ON job_risks(status)",
            "CREATE INDEX IF NOT EXISTS idx_communications_job ON job_communications(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_communications_date ON job_communications(communication_date)",
            "CREATE INDEX IF NOT EXISTS idx_change_requests_job ON job_change_requests(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_change_requests_status ON job_change_requests(status)",
            "CREATE INDEX IF NOT EXISTS idx_payments_job ON job_payments(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_payments_status ON job_payments(status)",
            "CREATE INDEX IF NOT EXISTS idx_payments_due_date ON job_payments(invoice_due_date)",
            "CREATE INDEX IF NOT EXISTS idx_documents_job ON job_documents(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_documents_type ON job_documents(type)",
            "CREATE INDEX IF NOT EXISTS idx_photos_job ON job_photos(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_photos_phase ON job_photos(phase)",
            "CREATE INDEX IF NOT EXISTS idx_photos_date ON job_photos(taken_date)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_job ON job_metrics(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_date ON job_metrics(calculated_at)",
        ]
        
        for idx_sql in indexes:
            try:
                cursor.execute(idx_sql)
            except sqlite3.OperationalError:
                pass  # Index už existuje
        
        print(f"   ✅ Vytvořeno {len(indexes)} indexů")
        
        # ====================================================================
        # 5. VYTVOŘENÍ VIEWS
        # ====================================================================
        
        print("\n5️⃣  Vytvářím views...")
        
        # Drop views if exist (pro re-create)
        cursor.execute("DROP VIEW IF EXISTS v_jobs_complete")
        cursor.execute("DROP VIEW IF EXISTS v_jobs_finances")
        cursor.execute("DROP VIEW IF EXISTS v_jobs_timeline")
        
        # View: Kompletní info o zakázce
        cursor.execute("""
            CREATE VIEW v_jobs_complete AS
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
                (SELECT COUNT(*) FROM job_photos WHERE job_id = j.id) as photos_count
            FROM jobs j
            LEFT JOIN job_clients c ON j.id = c.job_id
            LEFT JOIN job_locations l ON j.id = l.job_id
            LEFT JOIN users u ON j.project_manager_id = u.id
        """)
        
        print("   ✅ Views vytvořeny")
        
        # ====================================================================
        # COMMIT
        # ====================================================================
        
        conn.commit()
        print("\n✅ Migrace úspěšně dokončena!")
        print(f"📦 Záloha uložena: {backup_path}")
        print("\n" + "="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: Migrace selhala!")
        print(f"   {str(e)}")
        print(f"\n📦 Databáze nebyla změněna. Záloha: {backup_path}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def main():
    """Main entry point"""
    db_path = "app.db"
    
    # Možnost specifikovat cestu jako argument
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print(f"📍 Databáze: {db_path}\n")
    
    success = migrate_database(db_path)
    
    if success:
        print("\n🎉 Vše hotovo! Můžeš restartovat aplikaci.")
        print("\n💡 TIP: Zkontroluj že všechno funguje, pak můžeš smazat zálohu.")
        sys.exit(0)
    else:
        print("\n❌ Migrace selhala. Zkontroluj chybové hlášky výše.")
        sys.exit(1)

if __name__ == "__main__":
    main()
