import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash
from app.database import get_db, _table_exists, _table_has_column

def apply_migrations():
    """Lightweight, non-breaking migration runner.

    Tracks applied versions in schema_migrations and applies idempotent ALTERs when needed.
    """
    db = get_db()
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT (datetime('now')))")
    applied = {r[0] for r in db.execute("SELECT version FROM schema_migrations").fetchall()}

    migrations = [
        # v1: baseline (existing ensure_schema creates core tables)
        (1, []),

        # v2: employees extra contact fields (safe idempotent)
        (2, [
            ("employees", "phone",   "ALTER TABLE employees ADD COLUMN phone TEXT DEFAULT ''"),
            ("employees", "email",   "ALTER TABLE employees ADD COLUMN email TEXT DEFAULT ''"),
            ("employees", "address", "ALTER TABLE employees ADD COLUMN address TEXT DEFAULT ''"),
        ]),

        # v3: core search stability (jobs/tasks/issues timestamps + assignment tables)
        (3, [
            ("jobs", "created_at", "ALTER TABLE jobs ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))"),
            ("tasks", "created_at", "ALTER TABLE tasks ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))"),
            """
            CREATE TABLE IF NOT EXISTS task_assignments (
                task_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                is_primary INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (task_id, employee_id)
            );
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                type TEXT DEFAULT 'issue',
                status TEXT NOT NULL DEFAULT 'open',
                severity TEXT DEFAULT '',
                assigned_to INTEGER,
                created_by INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS issue_assignments (
                issue_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                is_primary INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (issue_id, employee_id)
            );
            """,
        ]),

        # v4: assignment tables primary flag (backward compatibility)
        (4, [
            ("task_assignments", "is_primary", "ALTER TABLE task_assignments ADD COLUMN is_primary INTEGER NOT NULL DEFAULT 0"),
            ("issue_assignments", "is_primary", "ALTER TABLE issue_assignments ADD COLUMN is_primary INTEGER NOT NULL DEFAULT 0"),
        ]),

        # v5: notifications (safe create)
        (5, [
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                employee_id INTEGER,
                kind TEXT NOT NULL DEFAULT 'info',
                title TEXT NOT NULL DEFAULT '',
                body TEXT NOT NULL DEFAULT '',
                entity_type TEXT,
                entity_id INTEGER,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read, created_at);
            CREATE INDEX IF NOT EXISTS idx_notifications_emp_read ON notifications(employee_id, is_read, created_at);
            """,
        ]),

        # v6: tasks extra columns (deadline, depends_on, due_date)
        (6, [
            ("tasks", "deadline", "ALTER TABLE tasks ADD COLUMN deadline TEXT"),
            ("tasks", "depends_on", "ALTER TABLE tasks ADD COLUMN depends_on TEXT"),
            ("tasks", "due_date", "ALTER TABLE tasks ADD COLUMN due_date TEXT"),
        ]),

        # v7: jobs extra columns (invoiced, address, budget)
        (7, [
            ("jobs", "invoiced", "ALTER TABLE jobs ADD COLUMN invoiced INTEGER DEFAULT 0"),
            ("jobs", "address", "ALTER TABLE jobs ADD COLUMN address TEXT DEFAULT ''"),
            ("jobs", "budget", "ALTER TABLE jobs ADD COLUMN budget REAL DEFAULT 0"),
        ]),

        # v8: planning_assignments table
        (8, [
            """
            CREATE TABLE IF NOT EXISTS planning_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                job_id INTEGER,
                task_id INTEGER,
                date TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                hours REAL DEFAULT 8,
                note TEXT DEFAULT '',
                status TEXT DEFAULT 'planned',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (job_id) REFERENCES jobs(id),
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            );
            CREATE INDEX IF NOT EXISTS idx_planning_date ON planning_assignments(date);
            CREATE INDEX IF NOT EXISTS idx_planning_employee ON planning_assignments(employee_id);
            """,
        ]),

        # v9: inventory/warehouse table
        (9, [
            """
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT,
                category TEXT DEFAULT 'general',
                quantity REAL DEFAULT 0,
                unit TEXT DEFAULT 'ks',
                unit_price REAL DEFAULT 0,
                min_quantity REAL DEFAULT 0,
                location TEXT DEFAULT '',
                supplier TEXT DEFAULT '',
                note TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_inventory_category ON inventory(category);
            CREATE INDEX IF NOT EXISTS idx_inventory_sku ON inventory(sku);
            """,
        ]),

        # v10: attachments table
        (10, [
            """
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                filesize INTEGER DEFAULT 0,
                mimetype TEXT DEFAULT '',
                uploaded_by INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (uploaded_by) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_attachments_entity ON attachments(entity_type, entity_id);
            """,
        ]),

        # v11: warehouse_items table (alternative naming)
        (11, [
            """
            CREATE TABLE IF NOT EXISTS warehouse_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT,
                category TEXT DEFAULT 'general',
                quantity REAL DEFAULT 0,
                unit TEXT DEFAULT 'ks',
                unit_price REAL DEFAULT 0,
                min_quantity REAL DEFAULT 0,
                location TEXT DEFAULT '',
                supplier TEXT DEFAULT '',
                note TEXT DEFAULT '',
                job_id INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """,
        ]),

        # v12: job_plan_proposals table (Ghost plán)
        (12, [
            """
            CREATE TABLE IF NOT EXISTS job_plan_proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                proposal_type TEXT NOT NULL DEFAULT 'ghost',
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                proposed_timeline JSON,
                proposed_resources JSON,
                proposed_budget REAL DEFAULT 0,
                risk_score INTEGER DEFAULT 0,
                health_score INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                created_by INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                reviewed_at TEXT,
                reviewed_by INTEGER,
                FOREIGN KEY (job_id) REFERENCES jobs(id),
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (reviewed_by) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_job_plan_proposals_job ON job_plan_proposals(job_id, status);
            """,
        ]),

        # v13: timesheets extended (work logs as data package)
        (13, [
            ("timesheets", "user_id", "ALTER TABLE timesheets ADD COLUMN user_id INTEGER NULL"),
            ("timesheets", "duration_minutes", "ALTER TABLE timesheets ADD COLUMN duration_minutes INTEGER NULL"),
            ("timesheets", "work_type", "ALTER TABLE timesheets ADD COLUMN work_type TEXT DEFAULT 'manual'"),
            ("timesheets", "start_time", "ALTER TABLE timesheets ADD COLUMN start_time TEXT NULL"),
            ("timesheets", "end_time", "ALTER TABLE timesheets ADD COLUMN end_time TEXT NULL"),
            ("timesheets", "location", "ALTER TABLE timesheets ADD COLUMN location TEXT NULL"),
            ("timesheets", "task_id", "ALTER TABLE timesheets ADD COLUMN task_id INTEGER NULL"),
            ("timesheets", "material_used", "ALTER TABLE timesheets ADD COLUMN material_used TEXT NULL"),
            ("timesheets", "weather_snapshot", "ALTER TABLE timesheets ADD COLUMN weather_snapshot TEXT NULL"),
            ("timesheets", "performance_signal", "ALTER TABLE timesheets ADD COLUMN performance_signal TEXT DEFAULT 'normal'"),
            ("timesheets", "delay_reason", "ALTER TABLE timesheets ADD COLUMN delay_reason TEXT NULL"),
            ("timesheets", "photo_url", "ALTER TABLE timesheets ADD COLUMN photo_url TEXT NULL"),
            ("timesheets", "note", "ALTER TABLE timesheets ADD COLUMN note TEXT NULL"),
            ("timesheets", "ai_flags", "ALTER TABLE timesheets ADD COLUMN ai_flags TEXT NULL"),
            ("timesheets", "created_at", "ALTER TABLE timesheets ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))"),
            ("timesheets", "labor_cost", "ALTER TABLE timesheets ADD COLUMN labor_cost REAL NULL"),
            """
            -- Migrate existing hours to duration_minutes
            UPDATE timesheets SET duration_minutes = CAST(hours * 60 AS INTEGER) WHERE duration_minutes IS NULL AND hours IS NOT NULL;
            
            -- Migrate place to location
            UPDATE timesheets SET location = place WHERE location IS NULL AND place IS NOT NULL AND place != '';
            
            -- Migrate activity to note
            UPDATE timesheets SET note = activity WHERE note IS NULL AND activity IS NOT NULL AND activity != '';
            
            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_timesheets_user_date ON timesheets(user_id, date);
            CREATE INDEX IF NOT EXISTS idx_timesheets_job_date ON timesheets(job_id, date);
            CREATE INDEX IF NOT EXISTS idx_timesheets_task ON timesheets(task_id);
            CREATE INDEX IF NOT EXISTS idx_timesheets_employee_date ON timesheets(employee_id, date);
            """,
        ]),

        # v14: timesheets delay_note (doplněk k delay_reason)
        (14, [
            ("timesheets", "delay_note", "ALTER TABLE timesheets ADD COLUMN delay_note TEXT NULL"),
        ]),

        # v15: trainings module (školení a vzdělávání)
        (15, [
            """
            CREATE TABLE IF NOT EXISTS trainings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                training_type TEXT DEFAULT 'external',
                category TEXT,
                provider TEXT,
                provider_type TEXT,
                date_start TEXT NOT NULL,
                date_end TEXT,
                duration_hours REAL,
                is_paid INTEGER DEFAULT 1,
                cost_training REAL DEFAULT 0,
                cost_travel REAL DEFAULT 0,
                cost_accommodation REAL DEFAULT 0,
                cost_meals REAL DEFAULT 0,
                cost_other REAL DEFAULT 0,
                cost_total REAL DEFAULT 0,
                cost_opportunity REAL DEFAULT 0,
                location TEXT,
                is_remote INTEGER DEFAULT 0,
                has_certificate INTEGER DEFAULT 0,
                certificate_name TEXT,
                certificate_valid_until TEXT,
                rating INTEGER,
                notes TEXT,
                skills_gained TEXT,
                skill_level_increase INTEGER DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                created_by INTEGER
            );
            CREATE TABLE IF NOT EXISTS training_attendees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                training_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                status TEXT DEFAULT 'registered',
                attendance_confirmed INTEGER DEFAULT 0,
                test_score REAL,
                certificate_issued INTEGER DEFAULT 0,
                certificate_url TEXT,
                personal_rating INTEGER,
                personal_notes TEXT,
                FOREIGN KEY (training_id) REFERENCES trainings(id) ON DELETE CASCADE,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_trainings_date ON trainings(date_start);
            CREATE INDEX IF NOT EXISTS idx_trainings_category ON trainings(category);
            CREATE INDEX IF NOT EXISTS idx_training_attendees_employee ON training_attendees(employee_id);
            CREATE INDEX IF NOT EXISTS idx_training_attendees_training ON training_attendees(training_id);
            """,
        ]),

        # v16: employees skills tracking
        (16, [
            ("employees", "skills", "ALTER TABLE employees ADD COLUMN skills TEXT NULL"),
            ("employees", "skill_score", "ALTER TABLE employees ADD COLUMN skill_score REAL DEFAULT 50"),
            ("employees", "training_hours_total", "ALTER TABLE employees ADD COLUMN training_hours_total REAL DEFAULT 0"),
            ("employees", "last_training_date", "ALTER TABLE employees ADD COLUMN last_training_date TEXT NULL"),
        ]),

        # v17: training compensation type (typ proplácení školení)
        (17, [
            ("trainings", "compensation_type", "ALTER TABLE trainings ADD COLUMN compensation_type TEXT DEFAULT 'paid_workday'"),
            ("trainings", "wage_cost", "ALTER TABLE trainings ADD COLUMN wage_cost REAL DEFAULT 0"),
            ("trainings", "wage_cost_per_person", "ALTER TABLE trainings ADD COLUMN wage_cost_per_person REAL NULL"),
        ]),

        # v18: worklogs training_id (propojení výkazů se školením)
        (18, [
            ("timesheets", "training_id", "ALTER TABLE timesheets ADD COLUMN training_id INTEGER NULL"),
            ("timesheets", "fk_timesheets_training", """
                CREATE INDEX IF NOT EXISTS idx_timesheets_training ON timesheets(training_id)
            """),
        ]),
        
        # v19: trainings participants field (účastníci jako JSON)
        (19, [
            ("trainings", "participants", "ALTER TABLE trainings ADD COLUMN participants TEXT DEFAULT '[]'"),
            ("trainings", "title", "ALTER TABLE trainings ADD COLUMN title TEXT NULL"),
            ("trainings", "date", "ALTER TABLE trainings ADD COLUMN date TEXT NULL"),
            ("trainings", "skills_improved", "ALTER TABLE trainings ADD COLUMN skills_improved TEXT NULL"),
            ("trainings", "skill_increase", "ALTER TABLE trainings ADD COLUMN skill_increase INTEGER DEFAULT 5"),
        ]),
        
        # v20: Crew Control System - team member profiles and capacity tracking
        (20, [
            """
            CREATE TABLE IF NOT EXISTS team_member_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL UNIQUE,
                skills TEXT DEFAULT '[]',
                certifications TEXT DEFAULT '[]',
                weekly_capacity_hours REAL DEFAULT 40.0,
                preferred_work_types TEXT DEFAULT '[]',
                performance_stability_score REAL DEFAULT 0.5,
                ai_balance_score REAL DEFAULT 0.5,
                burnout_risk_level TEXT DEFAULT 'normal',
                total_jobs_completed INTEGER DEFAULT 0,
                current_active_jobs INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_team_profile_employee ON team_member_profile(employee_id);
            CREATE INDEX IF NOT EXISTS idx_team_profile_burnout ON team_member_profile(burnout_risk_level);
            
            CREATE TABLE IF NOT EXISTS team_capacity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                planned_hours REAL DEFAULT 0,
                actual_hours REAL DEFAULT 0,
                capacity_status TEXT DEFAULT 'normal',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_capacity_log_employee_date ON team_capacity_log(employee_id, date);
            CREATE INDEX IF NOT EXISTS idx_capacity_log_date ON team_capacity_log(date);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_capacity_log_unique ON team_capacity_log(employee_id, date);
            """,
        ]),

        # v21: standardize task statuses - 'open' → 'todo'
        (21, [
            """
            UPDATE tasks SET status = 'todo' WHERE status = 'open';
            """,
        ]),

        # v22: add priority column to tasks table
        (22, [
            ("tasks", "priority", "ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium'"),
        ]),

        # v23: Day planning - přiřazení zaměstnanců na zakázky s plánovanými/skutečnými hodinami
        (23, [
            """
            CREATE TABLE IF NOT EXISTS day_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                employee_id INTEGER NOT NULL,
                job_id INTEGER,
                planned_hours REAL DEFAULT 8.0,
                actual_hours REAL,
                status TEXT DEFAULT 'planned',
                note TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                confirmed_at TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            );
            CREATE INDEX IF NOT EXISTS idx_day_plans_date ON day_plans(date);
            CREATE INDEX IF NOT EXISTS idx_day_plans_emp_date ON day_plans(employee_id, date);
            """,
        ]),
        (24, [
            """
            CREATE TABLE IF NOT EXISTS parties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL DEFAULT 'ORG',
                display_name TEXT NOT NULL,
                legal_name TEXT,
                email TEXT,
                phone TEXT,
                website TEXT,
                street TEXT,
                city TEXT,
                zip TEXT,
                country TEXT DEFAULT 'CZ',
                gps_lat REAL,
                gps_lon REAL,
                ico TEXT,
                dic TEXT,
                bank_account TEXT,
                roles TEXT DEFAULT '["CLIENT"]',
                tier TEXT DEFAULT 'ONE_OFF',
                status TEXT DEFAULT 'LEAD',
                health_index INTEGER DEFAULT 50,
                total_revenue REAL DEFAULT 0,
                total_jobs INTEGER DEFAULT 0,
                last_job_date TEXT,
                payment_reliability INTEGER DEFAULT 50,
                tags TEXT DEFAULT '[]',
                note TEXT,
                source TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS party_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                party_id INTEGER NOT NULL REFERENCES parties(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                role TEXT,
                email TEXT,
                phone TEXT,
                is_primary INTEGER DEFAULT 0,
                note TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS party_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                party_id INTEGER NOT NULL REFERENCES parties(id) ON DELETE CASCADE,
                type TEXT NOT NULL,
                summary TEXT,
                date TEXT DEFAULT (date('now')),
                created_by TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_parties_status ON parties(status);
            CREATE INDEX IF NOT EXISTS idx_parties_tier ON parties(tier);
            CREATE INDEX IF NOT EXISTS idx_party_contacts_party ON party_contacts(party_id);
            CREATE INDEX IF NOT EXISTS idx_party_interactions_party ON party_interactions(party_id);
            """,
            ("jobs", "party_id", "ALTER TABLE jobs ADD COLUMN party_id INTEGER REFERENCES parties(id)"),
        ]),
        (25, [
            ("tasks", "created_by", "ALTER TABLE tasks ADD COLUMN created_by TEXT"),
            ("tasks", "priority", "ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'normal'"),
            ("tasks", "deadline", "ALTER TABLE tasks ADD COLUMN deadline TEXT"),
            ("jobs", "tags", "ALTER TABLE jobs ADD COLUMN tags TEXT DEFAULT '[]'"),
            ("jobs", "deadline", "ALTER TABLE jobs ADD COLUMN deadline TEXT"),
        ]),
        # v26: notes table (sekce Poznámky)
        (26, [
            """
            CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    color TEXT DEFAULT 'default',
                    is_pinned INTEGER DEFAULT 0,
                    job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
                    employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
                    party_id INTEGER REFERENCES parties(id) ON DELETE SET NULL,
                    created_by INTEGER REFERENCES users(id),
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_notes_job ON notes(job_id);
                CREATE INDEX IF NOT EXISTS idx_notes_employee ON notes(employee_id);
                CREATE INDEX IF NOT EXISTS idx_notes_party ON notes(party_id);
                CREATE INDEX IF NOT EXISTS idx_notes_created_by ON notes(created_by);
                CREATE INDEX IF NOT EXISTS idx_notes_category ON notes(category);
                CREATE INDEX IF NOT EXISTS idx_notes_pinned ON notes(is_pinned);
            """,
        ]),
        # v27: notes table — oprava schématu (replace stará notes s jinou strukturou)
        (27, [
            """
            DROP TABLE IF EXISTS notes;
            CREATE TABLE notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                color TEXT DEFAULT 'default',
                is_pinned INTEGER DEFAULT 0,
                job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
                employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
                party_id INTEGER REFERENCES parties(id) ON DELETE SET NULL,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_notes_job ON notes(job_id);
            CREATE INDEX IF NOT EXISTS idx_notes_employee ON notes(employee_id);
            CREATE INDEX IF NOT EXISTS idx_notes_party ON notes(party_id);
            CREATE INDEX IF NOT EXISTS idx_notes_created_by ON notes(created_by);
            CREATE INDEX IF NOT EXISTS idx_notes_category ON notes(category);
            CREATE INDEX IF NOT EXISTS idx_notes_pinned ON notes(is_pinned);
            """,
        ]),
        # v28: budget_sections + budget_items (rozpočet zakázky) — DEPRECATED, v29 replaces
        (28, []),
        # v29: budget v3 — section_type na sekci, žádný item_type na položce
        (29, [
            "DROP TABLE IF EXISTS budget_items",
            "DROP TABLE IF EXISTS budget_sections",
            """CREATE TABLE IF NOT EXISTS budget_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                section_type TEXT NOT NULL DEFAULT 'material',
                sort_order INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
            )""",
            "CREATE INDEX IF NOT EXISTS idx_budget_sections_job ON budget_sections(job_id)",
            """CREATE TABLE IF NOT EXISTS budget_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                unit TEXT DEFAULT 'ks',
                quantity REAL DEFAULT 0,
                unit_price REAL DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                note TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (section_id) REFERENCES budget_sections(id) ON DELETE CASCADE
            )""",
            "CREATE INDEX IF NOT EXISTS idx_budget_items_section ON budget_items(section_id)"
        ]),

        # v30: job_type (interní vs. klientská zakázka)
        (30, [
            ("jobs", "job_type", "ALTER TABLE jobs ADD COLUMN job_type TEXT DEFAULT 'client'"),
        ]),

        # v31: job detail extended tables (from migrate_jobs_extended.py)
        (31, [
            """CREATE TABLE IF NOT EXISTS job_clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                company TEXT, ico TEXT, dic TEXT,
                email TEXT, phone TEXT, phone_secondary TEXT,
                preferred_contact TEXT DEFAULT 'phone',
                billing_street TEXT, billing_city TEXT, billing_zip TEXT,
                billing_country TEXT DEFAULT 'CZ',
                client_since DATE, total_projects INTEGER DEFAULT 1,
                total_revenue DECIMAL(12,2) DEFAULT 0,
                payment_rating TEXT DEFAULT 'good', notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(job_id)
            )""",
            """CREATE TABLE IF NOT EXISTS job_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                street TEXT, city TEXT, zip TEXT,
                country TEXT DEFAULT 'CZ',
                lat DECIMAL(10,6), lng DECIMAL(10,6),
                parking TEXT, parking_notes TEXT, access_notes TEXT,
                gate_code TEXT, key_location TEXT,
                has_electricity BOOLEAN DEFAULT false,
                has_water BOOLEAN DEFAULT false,
                has_toilet BOOLEAN DEFAULT false,
                neighbors_info TEXT, noise_restrictions TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(job_id)
            )""",
            """CREATE TABLE IF NOT EXISTS job_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                name TEXT NOT NULL, description TEXT,
                planned_date DATE, actual_date DATE,
                status TEXT DEFAULT 'pending',
                completion_percent INTEGER DEFAULT 0,
                order_num INTEGER DEFAULT 0,
                depends_on INTEGER REFERENCES job_milestones(id),
                reminder_days_before INTEGER DEFAULT 3,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS job_equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                name TEXT NOT NULL, type TEXT,
                days_needed INTEGER, date_from DATE, date_to DATE,
                cost_per_day DECIMAL(10,2), total_cost DECIMAL(10,2),
                supplier TEXT, supplier_contact TEXT,
                reservation_date DATE, reservation_confirmed BOOLEAN DEFAULT false,
                status TEXT DEFAULT 'needed', owned BOOLEAN DEFAULT false,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS job_team_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                role TEXT DEFAULT 'worker',
                hours_planned INTEGER DEFAULT 0, hours_actual INTEGER DEFAULT 0,
                availability TEXT DEFAULT 'full-time',
                assigned_date DATE DEFAULT (date('now')),
                removed_date DATE, is_active BOOLEAN DEFAULT true, notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(job_id, employee_id, assigned_date)
            )""",
            """CREATE TABLE IF NOT EXISTS job_subcontractors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                name TEXT NOT NULL, company TEXT, service TEXT NOT NULL,
                contact_person TEXT, phone TEXT, email TEXT,
                price DECIMAL(10,2), payment_terms TEXT,
                status TEXT DEFAULT 'requested',
                start_date DATE, end_date DATE,
                contract_signed BOOLEAN DEFAULT false, invoice_number TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS job_risks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                description TEXT NOT NULL, category TEXT,
                probability TEXT DEFAULT 'medium', impact TEXT DEFAULT 'medium',
                risk_score INTEGER, mitigation_plan TEXT, contingency_plan TEXT,
                status TEXT DEFAULT 'identified',
                owner_id INTEGER REFERENCES users(id),
                identified_date DATE DEFAULT (date('now')),
                review_date DATE, closed_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS job_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                planned_date DATE, amount DECIMAL(12,2) NOT NULL,
                percentage INTEGER, payment_type TEXT DEFAULT 'progress',
                status TEXT DEFAULT 'pending',
                paid_date DATE, paid_amount DECIMAL(12,2),
                payment_method TEXT, invoice_id TEXT,
                invoice_date DATE, invoice_due_date DATE, note TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS job_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                file_path TEXT NOT NULL, thumbnail_path TEXT,
                phase TEXT DEFAULT 'progress',
                milestone_id INTEGER REFERENCES job_milestones(id),
                caption TEXT, description TEXT,
                taken_by INTEGER REFERENCES users(id),
                taken_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                location_on_site TEXT,
                lat DECIMAL(10,6), lng DECIMAL(10,6),
                related_issue_id INTEGER, severity TEXT, tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS job_communications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                communication_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                type TEXT DEFAULT 'note', direction TEXT DEFAULT 'internal',
                subject TEXT, summary TEXT NOT NULL, full_content TEXT,
                by_user_id INTEGER REFERENCES users(id),
                with_client BOOLEAN DEFAULT true, participants TEXT,
                outcome TEXT, action_items TEXT,
                is_internal BOOLEAN DEFAULT false, attachments TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS job_change_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                requested_by TEXT DEFAULT 'client', requested_by_name TEXT,
                description TEXT NOT NULL, reason TEXT,
                impact_cost DECIMAL(10,2), impact_time INTEGER, impact_scope TEXT,
                urgency TEXT DEFAULT 'medium', status TEXT DEFAULT 'pending',
                approved_by INTEGER REFERENCES users(id),
                approved_date DATE, rejection_reason TEXT,
                implemented_date DATE, implementation_notes TEXT,
                requested_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS job_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                name TEXT NOT NULL, type TEXT DEFAULT 'other', category TEXT,
                file_path TEXT NOT NULL, file_size INTEGER, mime_type TEXT,
                version INTEGER DEFAULT 1, is_latest BOOLEAN DEFAULT true,
                replaces_document_id INTEGER REFERENCES job_documents(id),
                description TEXT, uploaded_by INTEGER REFERENCES users(id),
                uploaded_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                signed BOOLEAN DEFAULT false, signed_date DATE,
                approval_status TEXT DEFAULT 'pending', approval_date DATE,
                expires_date DATE, tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS job_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                days_elapsed INTEGER, days_remaining INTEGER, days_planned INTEGER,
                schedule_variance INTEGER,
                budget_spent DECIMAL(12,2), budget_remaining DECIMAL(12,2),
                budget_variance DECIMAL(12,2), cost_performance_index DECIMAL(5,2),
                completion_percent INTEGER, on_track BOOLEAN,
                avg_hours_per_day DECIMAL(5,2), productive_hours_percent INTEGER,
                defects_count INTEGER DEFAULT 0, rework_hours INTEGER DEFAULT 0,
                predicted_completion_date DATE,
                predicted_final_cost DECIMAL(12,2), predicted_profit DECIMAL(12,2),
                confidence_level TEXT
            )"""
        ]),

        # v32: employees.position column (missing on production)
        (32, [
            ("employees", "position", "ALTER TABLE employees ADD COLUMN position TEXT DEFAULT ''"),
        ]),

        # v33: finance invoices table (for Finance stránka)
        (33, [
            """
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL DEFAULT 'issued',
                number TEXT NOT NULL,
                client TEXT DEFAULT '',
                supplier TEXT DEFAULT '',
                amount REAL NOT NULL DEFAULT 0,
                date TEXT NOT NULL,
                due_date TEXT,
                status TEXT DEFAULT 'pending',
                note TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_invoices_type ON invoices(type);
            CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(date);
            CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
            """
        ]),

        # v34: trainings days_of_week (Po–Pá, víkend, vlastní výběr)
        (34, [
            ("trainings", "days_of_week", "ALTER TABLE trainings ADD COLUMN days_of_week TEXT DEFAULT '[0,1,2,3,4,5,6]'"),
        ]),
    ]

    for version, alters in migrations:
        if version in applied:
            continue
        for item in alters:
            # Allow either (table, col, sql) ALTERs or raw DDL scripts as strings
            if isinstance(item, str):
                try:
                    db.executescript(item)
                except Exception:
                    pass
                continue
            table, col, sql = item
            # Skip ALTERs for tables that do not exist yet (fresh DB before ensure_schema).
            if not _table_exists(db, table):
                continue
            if not _table_has_column(db, table, col):
                try:
                    db.execute(sql)
                except Exception:
                    # last-resort: ignore to avoid breaking startup
                    pass
        db.execute("INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)", (version,))
        db.commit()


def _migrate_completed_at():
    """Add missing columns to jobs table if they don't exist"""
    db = get_db()
    try:
        if not _table_exists(db, "jobs"):
            return
        cols = [r[1] for r in db.execute("PRAGMA table_info(jobs)").fetchall()]
        if "completed_at" not in cols:
            db.execute("ALTER TABLE jobs ADD COLUMN completed_at TEXT")
            db.commit()
            print("[DB] Added column: completed_at")
        if "created_date" not in cols:
            db.execute("ALTER TABLE jobs ADD COLUMN created_date TEXT")
            db.commit()
            print("[DB] Added column: created_date")
        if "start_date" not in cols:
            db.execute("ALTER TABLE jobs ADD COLUMN start_date TEXT")
            db.commit()
            print("[DB] Added column: start_date")
        if "progress" not in cols:
            db.execute("ALTER TABLE jobs ADD COLUMN progress INTEGER DEFAULT 0")
            db.commit()
            print("[DB] Added column: progress")
    except Exception as e:
        print(f"[DB] Migration warning: {e}")

def _migrate_employees_enhanced():
    """Add enhanced columns to employees table and create new tables"""
    db = get_db()
    try:
        if not _table_exists(db, "employees"):
            return
        cols = [r[1] for r in db.execute("PRAGMA table_info(employees)").fetchall()]
        
        # Add new columns to employees table
        new_cols = {
            "birth_date": "TEXT",
            "contract_type": "TEXT DEFAULT 'HPP'",
            "start_date": "TEXT",
            "hourly_rate": "REAL",
            "salary": "REAL",
            "skills": "TEXT",
            "location": "TEXT",
            "status": "TEXT DEFAULT 'active'",
            "rating": "REAL DEFAULT 0",
            "avatar_url": "TEXT"

            ,"delegate_employee_id": "INTEGER NULL"
            ,"approver_delegate_employee_id": "INTEGER NULL"
        
            ,"user_id": "INTEGER NULL"
        }
        
        for col_name, col_def in new_cols.items():
            if col_name not in cols:
                db.execute(f"ALTER TABLE employees ADD COLUMN {col_name} {col_def}")
                db.commit()
                print(f"[DB] Added column: employees.{col_name}")
        
        # Create employee_documents table
        db.execute("""
            CREATE TABLE IF NOT EXISTS employee_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                file_url TEXT NOT NULL,
                uploaded_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            )
        """)
        db.commit()
        print("[DB] Created table: employee_documents")
        
        # Create employee_timeline table
        db.execute("""
            CREATE TABLE IF NOT EXISTS employee_timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            )
        """)
        db.commit()
        print("[DB] Created table: employee_timeline")
        
    except Exception as e:
        print(f"[DB] Migration warning: {e}")

def _migrate_roles_and_hierarchy():
    """Migrace: přidání sloupců role a manager_id do users tabulky"""
    db = get_db()
    try:
        if not _table_exists(db, "users"):
            return
        # Zkontrolovat existující sloupce
        cols = [r[1] for r in db.execute("PRAGMA table_info(users)").fetchall()]
        
        # Přidat sloupec role pokud neexistuje nebo aktualizovat CHECK constraint
        if 'role' not in cols:
            db.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'worker'")
            db.commit()
            print("[DB] Added column: users.role")
        else:
            # Aktualizovat CHECK constraint pro nové role
            # SQLite nepodporuje ALTER COLUMN, takže musíme vytvořit novou tabulku
            # Poznámka: Pokud už existuje manager_id, přeskočíme tuto část
            if 'manager_id' not in cols:
                try:
                    # Vypnout foreign key kontroly během migrace
                    db.execute("PRAGMA foreign_keys=OFF")
                    db.execute("""
                        CREATE TABLE users_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            email TEXT UNIQUE NOT NULL,
                            name TEXT NOT NULL,
                            role TEXT NOT NULL DEFAULT 'worker' CHECK(role IN ('owner','admin','manager','lander','worker','team_lead')),
                            password_hash TEXT NOT NULL,
                            active INTEGER NOT NULL DEFAULT 1,
                            created_at TEXT NOT NULL DEFAULT (datetime('now')),
                            manager_id INTEGER NULL
                        )
                    """)
                    db.execute("""
                        INSERT INTO users_new (id, email, name, role, password_hash, active, created_at)
                        SELECT id, email, name, 
                               CASE 
                                   WHEN role = 'admin' THEN 'owner'
                                   ELSE role
                               END,
                               password_hash, active, created_at
                        FROM users
                    """)
                    db.execute("DROP TABLE users")
                    db.execute("ALTER TABLE users_new RENAME TO users")
                    db.execute("PRAGMA foreign_keys=ON")
                    db.commit()
                    print("[DB] Updated users table with new role system")
                except Exception as e:
                    db.execute("PRAGMA foreign_keys=ON")
                    print(f"[DB] Role migration warning: {e}")
        
        # Přidat manager_id pokud neexistuje
        if 'manager_id' not in cols:
            db.execute("ALTER TABLE users ADD COLUMN manager_id INTEGER NULL")
            db.commit()
            print("[DB] Added column: users.manager_id")
            
            # Přidat foreign key constraint (SQLite to podporuje přes CREATE INDEX)
            try:
                db.execute("CREATE INDEX IF NOT EXISTS idx_users_manager_id ON users(manager_id)")
                db.commit()
            except Exception as e:
                print(f"[DB] Index creation warning: {e}")
        
        # Aktualizovat existujícího uživatele david@greendavid.cz na owner
        try:
            db.execute("UPDATE users SET role = 'owner' WHERE email = 'david@greendavid.cz'")
            db.commit()
            print("[DB] Updated david@greendavid.cz to owner role")
        except Exception as e:
            print(f"[DB] Owner update warning: {e}")
            
    except Exception as e:
        print(f"[DB] Roles migration warning: {e}")

def ensure_schema():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'worker' CHECK(role IN ('owner','manager','team_lead','worker','admin')),
        password_hash TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        manager_id INTEGER NULL
    );
    

    CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id INTEGER,
        before_json TEXT,
        after_json TEXT,
        meta_json TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'worker',
        position TEXT DEFAULT '',
        -- delegace: kam přesměrovat úkoly/problémy (např. při nepřítomnosti)
        delegate_employee_id INTEGER NULL,
        -- delegace: kam přesměrovat schvalování (výkazy apod.)
        approver_delegate_employee_id INTEGER NULL,
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        address TEXT DEFAULT '',
        user_id INTEGER NULL
    );
    -- prefer new schema; legacy DBs may still have jobs.name (possibly NOT NULL)
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        name TEXT,
        client TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Plán',
        city TEXT NOT NULL DEFAULT '',
        code TEXT NOT NULL DEFAULT '',
        date TEXT,
        note TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    
    CREATE TABLE IF NOT EXISTS job_assignments (
        job_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        PRIMARY KEY (job_id, employee_id)
    );
    CREATE TABLE IF NOT EXISTS job_employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        role TEXT DEFAULT 'worker',
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs(id),
        FOREIGN KEY (employee_id) REFERENCES employees(id)
    );
    CREATE TABLE IF NOT EXISTS job_materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        qty REAL NOT NULL DEFAULT 0,
        unit TEXT NOT NULL DEFAULT 'ks'
    );
    CREATE TABLE IF NOT EXISTS job_tools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        qty REAL NOT NULL DEFAULT 0,
        unit TEXT NOT NULL DEFAULT 'ks'
    );
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        employee_id INTEGER,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'open',
        due_date TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS task_assignments (
        task_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        is_primary INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (task_id, employee_id)
    );
    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        type TEXT DEFAULT 'issue',
        status TEXT NOT NULL DEFAULT 'open',
        severity TEXT DEFAULT '',
        assigned_to INTEGER,
        created_by INTEGER,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS issue_assignments (
        issue_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        is_primary INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (issue_id, employee_id)
    );

    CREATE TABLE IF NOT EXISTS timesheets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        hours REAL NOT NULL DEFAULT 0,
        place TEXT DEFAULT '',
        activity TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS calendar_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        title TEXT NOT NULL,
        kind TEXT NOT NULL DEFAULT 'note',
        job_id INTEGER,
        start_time TEXT,
        end_time TEXT,
        note TEXT DEFAULT '',
        color TEXT DEFAULT '#2e7d32'
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        employee_id INTEGER,
        kind TEXT NOT NULL DEFAULT 'info',
        title TEXT NOT NULL DEFAULT '',
        body TEXT NOT NULL DEFAULT '',
        entity_type TEXT,
        entity_id INTEGER,
        is_read INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read, created_at);
    CREATE INDEX IF NOT EXISTS idx_notifications_emp_read ON notifications(employee_id, is_read, created_at);

    -- Katalog rostlin pro autocomplete
    CREATE TABLE IF NOT EXISTS plant_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        latin_name TEXT NOT NULL,
        variety TEXT,
        container_size TEXT,
        flower_color TEXT,
        flowering_time TEXT,
        leaf_color TEXT,
        height TEXT,
        light_requirements TEXT,
        site_type TEXT,
        plants_per_m2 TEXT,
        hardiness_zone TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(latin_name, variety)
    );
    CREATE INDEX IF NOT EXISTS idx_plant_catalog_latin ON plant_catalog(latin_name);
    CREATE INDEX IF NOT EXISTS idx_plant_catalog_variety ON plant_catalog(variety);

    -- Rostliny ve školce (inventář)
    CREATE TABLE IF NOT EXISTS nursery_plants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        species TEXT NOT NULL,
        variety TEXT,
        quantity INTEGER DEFAULT 0,
        unit TEXT DEFAULT 'ks',
        stage TEXT DEFAULT 'sazenice',
        location TEXT,
        planted_date TEXT,
        ready_date TEXT,
        purchase_price REAL DEFAULT 0,
        selling_price REAL DEFAULT 0,
        flower_color TEXT,
        flowering_time TEXT,
        height TEXT,
        light_requirements TEXT,
        leaf_color TEXT,
        hardiness_zone TEXT,
        site_type TEXT,
        plants_per_m2 TEXT,
        botanical_notes TEXT,
        notes TEXT,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_nursery_plants_species ON nursery_plants(species);
    CREATE INDEX IF NOT EXISTS idx_nursery_plants_status ON nursery_plants(status);

    -- Job detail tables (required by job-detail.html /complete endpoint)
    CREATE TABLE IF NOT EXISTS job_clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        name TEXT,
        company TEXT,
        ico TEXT,
        dic TEXT,
        email TEXT,
        phone TEXT,
        phone_secondary TEXT,
        billing_street TEXT,
        billing_city TEXT,
        billing_zip TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_job_clients_job ON job_clients(job_id);

    CREATE TABLE IF NOT EXISTS job_locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        street TEXT,
        city TEXT,
        zip TEXT,
        lat REAL,
        lng REAL,
        parking TEXT,
        access_notes TEXT,
        gate_code TEXT,
        address TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_job_locations_job ON job_locations(job_id);

    CREATE TABLE IF NOT EXISTS job_milestones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        planned_date TEXT,
        actual_date TEXT,
        status TEXT DEFAULT 'pending',
        completion_percent INTEGER DEFAULT 0,
        order_num INTEGER DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_job_milestones_job ON job_milestones(job_id);

    CREATE TABLE IF NOT EXISTS job_equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        name TEXT,
        type TEXT,
        date_from TEXT,
        date_to TEXT,
        cost REAL DEFAULT 0,
        note TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS job_subcontractors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        name TEXT,
        company TEXT,
        phone TEXT,
        email TEXT,
        scope TEXT,
        cost REAL DEFAULT 0,
        status TEXT DEFAULT 'active',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS job_risks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        name TEXT,
        description TEXT,
        probability TEXT DEFAULT 'medium',
        impact TEXT DEFAULT 'medium',
        mitigation TEXT,
        status TEXT DEFAULT 'open',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS job_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        description TEXT,
        amount REAL DEFAULT 0,
        planned_date TEXT,
        paid_date TEXT,
        status TEXT DEFAULT 'pending',
        type TEXT DEFAULT 'invoice',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS job_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        url TEXT,
        caption TEXT,
        taken_at TEXT,
        uploaded_by INTEGER,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS job_team_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        role TEXT DEFAULT 'worker',
        hours_planned REAL DEFAULT 0,
        hours_actual REAL DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES employees(id)
    );
    CREATE INDEX IF NOT EXISTS idx_job_team_job ON job_team_assignments(job_id);
    CREATE INDEX IF NOT EXISTS idx_job_team_emp ON job_team_assignments(employee_id);

    -- Budget tables
    CREATE TABLE IF NOT EXISTS budget_sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        section_type TEXT NOT NULL DEFAULT 'material',
        sort_order INTEGER DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_budget_sections_job ON budget_sections(job_id);

    CREATE TABLE IF NOT EXISTS budget_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        unit TEXT DEFAULT 'ks',
        quantity REAL DEFAULT 0,
        unit_price REAL DEFAULT 0,
        sort_order INTEGER DEFAULT 0,
        note TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (section_id) REFERENCES budget_sections(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_budget_items_section ON budget_items(section_id);

    -- Parties (CRM) tables
    CREATE TABLE IF NOT EXISTS parties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL DEFAULT 'ORG',
        display_name TEXT NOT NULL,
        legal_name TEXT,
        email TEXT,
        phone TEXT,
        website TEXT,
        street TEXT,
        city TEXT,
        zip TEXT,
        country TEXT DEFAULT 'CZ',
        gps_lat REAL,
        gps_lon REAL,
        ico TEXT,
        dic TEXT,
        bank_account TEXT,
        roles TEXT DEFAULT '["CLIENT"]',
        tier TEXT DEFAULT 'ONE_OFF',
        status TEXT DEFAULT 'LEAD',
        health_index INTEGER DEFAULT 50,
        total_revenue REAL DEFAULT 0,
        total_jobs INTEGER DEFAULT 0,
        last_job_date TEXT,
        payment_reliability INTEGER DEFAULT 50,
        tags TEXT DEFAULT '[]',
        note TEXT,
        source TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_parties_status ON parties(status);
    CREATE INDEX IF NOT EXISTS idx_parties_tier ON parties(tier);

    CREATE TABLE IF NOT EXISTS party_contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        party_id INTEGER NOT NULL REFERENCES parties(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        role TEXT,
        email TEXT,
        phone TEXT,
        is_primary INTEGER DEFAULT 0,
        note TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_party_contacts_party ON party_contacts(party_id);

    CREATE TABLE IF NOT EXISTS party_interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        party_id INTEGER NOT NULL REFERENCES parties(id) ON DELETE CASCADE,
        type TEXT NOT NULL,
        summary TEXT,
        date TEXT DEFAULT (date('now')),
        created_by TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_party_interactions_party ON party_interactions(party_id);

    -- Warehouse
    CREATE TABLE IF NOT EXISTS warehouse_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT,
        category TEXT DEFAULT 'general',
        quantity REAL DEFAULT 0,
        unit TEXT DEFAULT 'ks',
        unit_price REAL DEFAULT 0,
        min_quantity REAL DEFAULT 0,
        location TEXT DEFAULT '',
        supplier TEXT DEFAULT '',
        note TEXT DEFAULT '',
        job_id INTEGER,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT,
        category TEXT DEFAULT 'general',
        quantity REAL DEFAULT 0,
        unit TEXT DEFAULT 'ks',
        unit_price REAL DEFAULT 0,
        min_quantity REAL DEFAULT 0,
        location TEXT DEFAULT '',
        supplier TEXT DEFAULT '',
        note TEXT DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- Training
    CREATE TABLE IF NOT EXISTS trainings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        training_type TEXT DEFAULT 'external',
        category TEXT,
        provider TEXT,
        provider_type TEXT,
        date_start TEXT NOT NULL DEFAULT (date('now')),
        date_end TEXT,
        duration_hours REAL,
        is_paid INTEGER DEFAULT 1,
        cost_training REAL DEFAULT 0,
        cost_travel REAL DEFAULT 0,
        cost_accommodation REAL DEFAULT 0,
        cost_meals REAL DEFAULT 0,
        cost_other REAL DEFAULT 0,
        cost_total REAL DEFAULT 0,
        cost_opportunity REAL DEFAULT 0,
        location TEXT,
        is_remote INTEGER DEFAULT 0,
        has_certificate INTEGER DEFAULT 0,
        certificate_name TEXT,
        certificate_valid_until TEXT,
        rating INTEGER,
        notes TEXT,
        skills_gained TEXT,
        skill_level_increase INTEGER DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        created_by INTEGER
    );

    CREATE TABLE IF NOT EXISTS training_attendees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        training_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        status TEXT DEFAULT 'registered',
        attendance_confirmed INTEGER DEFAULT 0,
        test_score REAL,
        certificate_issued INTEGER DEFAULT 0,
        certificate_url TEXT,
        personal_rating INTEGER,
        personal_notes TEXT,
        FOREIGN KEY (training_id) REFERENCES trainings(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
    );

    -- Planning
    CREATE TABLE IF NOT EXISTS day_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        employee_id INTEGER NOT NULL,
        job_id INTEGER,
        planned_hours REAL DEFAULT 8.0,
        actual_hours REAL,
        status TEXT DEFAULT 'planned',
        note TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        confirmed_at TEXT,
        FOREIGN KEY (employee_id) REFERENCES employees(id),
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    );

    CREATE TABLE IF NOT EXISTS planning_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        job_id INTEGER,
        task_id INTEGER,
        date TEXT NOT NULL,
        start_time TEXT,
        end_time TEXT,
        hours REAL DEFAULT 8,
        note TEXT DEFAULT '',
        status TEXT DEFAULT 'planned',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (employee_id) REFERENCES employees(id),
        FOREIGN KEY (job_id) REFERENCES jobs(id),
        FOREIGN KEY (task_id) REFERENCES tasks(id)
    );

    -- Notes & Attachments
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT NOT NULL,
        category TEXT DEFAULT 'general',
        color TEXT DEFAULT 'default',
        is_pinned INTEGER DEFAULT 0,
        job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
        employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
        party_id INTEGER REFERENCES parties(id) ON DELETE SET NULL,
        created_by INTEGER REFERENCES users(id),
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        filesize INTEGER DEFAULT 0,
        mimetype TEXT DEFAULT '',
        uploaded_by INTEGER,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (uploaded_by) REFERENCES users(id)
    );

    -- Employee extended
    CREATE TABLE IF NOT EXISTS employee_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        file_url TEXT NOT NULL,
        uploaded_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS employee_timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        description TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
    );

    -- Job extended detail tables
    CREATE TABLE IF NOT EXISTS job_communications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        communication_date TEXT DEFAULT (datetime('now')),
        type TEXT DEFAULT 'note',
        direction TEXT DEFAULT 'internal',
        subject TEXT,
        summary TEXT NOT NULL,
        full_content TEXT,
        by_user_id INTEGER REFERENCES users(id),
        with_client INTEGER DEFAULT 1,
        participants TEXT,
        outcome TEXT,
        action_items TEXT,
        is_internal INTEGER DEFAULT 0,
        attachments TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS job_change_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        requested_by TEXT DEFAULT 'client',
        requested_by_name TEXT,
        description TEXT NOT NULL,
        reason TEXT,
        impact_cost REAL,
        impact_time INTEGER,
        impact_scope TEXT,
        urgency TEXT DEFAULT 'medium',
        status TEXT DEFAULT 'pending',
        approved_by INTEGER REFERENCES users(id),
        approved_date TEXT,
        rejection_reason TEXT,
        implemented_date TEXT,
        implementation_notes TEXT,
        requested_date TEXT DEFAULT (datetime('now')),
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );

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
        is_latest INTEGER DEFAULT 1,
        replaces_document_id INTEGER REFERENCES job_documents(id),
        description TEXT,
        uploaded_by INTEGER REFERENCES users(id),
        uploaded_date TEXT DEFAULT (datetime('now')),
        signed INTEGER DEFAULT 0,
        signed_date TEXT,
        approval_status TEXT DEFAULT 'pending',
        approval_date TEXT,
        expires_date TEXT,
        tags TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS job_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        calculated_at TEXT DEFAULT (datetime('now')),
        days_elapsed INTEGER,
        days_remaining INTEGER,
        days_planned INTEGER,
        schedule_variance INTEGER,
        budget_spent REAL,
        budget_remaining REAL,
        budget_variance REAL,
        cost_performance_index REAL,
        completion_percent INTEGER,
        on_track INTEGER,
        avg_hours_per_day REAL,
        productive_hours_percent INTEGER,
        defects_count INTEGER DEFAULT 0,
        rework_hours INTEGER DEFAULT 0,
        predicted_completion_date TEXT,
        predicted_final_cost REAL,
        predicted_profit REAL,
        confidence_level TEXT
    );

    CREATE TABLE IF NOT EXISTS job_plan_proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        proposal_type TEXT NOT NULL DEFAULT 'ghost',
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        proposed_timeline TEXT,
        proposed_resources TEXT,
        proposed_budget REAL DEFAULT 0,
        risk_score INTEGER DEFAULT 0,
        health_score INTEGER DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'pending',
        created_by INTEGER,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        reviewed_at TEXT,
        reviewed_by INTEGER,
        FOREIGN KEY (job_id) REFERENCES jobs(id),
        FOREIGN KEY (created_by) REFERENCES users(id),
        FOREIGN KEY (reviewed_by) REFERENCES users(id)
    );

    -- Team capacity
    CREATE TABLE IF NOT EXISTS team_capacity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        planned_hours REAL DEFAULT 0,
        actual_hours REAL DEFAULT 0,
        capacity_status TEXT DEFAULT 'normal',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS team_member_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL UNIQUE,
        skills TEXT DEFAULT '[]',
        certifications TEXT DEFAULT '[]',
        weekly_capacity_hours REAL DEFAULT 40.0,
        preferred_work_types TEXT DEFAULT '[]',
        performance_stability_score REAL DEFAULT 0.5,
        ai_balance_score REAL DEFAULT 0.5,
        burnout_risk_level TEXT DEFAULT 'normal',
        total_jobs_completed INTEGER DEFAULT 0,
        current_active_jobs INTEGER DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
    );

    -- GPS logs
    CREATE TABLE IF NOT EXISTS gps_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        accuracy REAL,
        timestamp TEXT NOT NULL DEFAULT (datetime('now')),
        job_id INTEGER,
        FOREIGN KEY (employee_id) REFERENCES employees(id),
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    );
    """)
    
    # Vytvoření FTS (Full-Text Search) tabulky pro katalog rostlin
    try:
        db.executescript("""
        CREATE VIRTUAL TABLE IF NOT EXISTS plant_catalog_fts USING fts5(
            latin_name,
            variety,
            flower_color,
            notes,
            content=plant_catalog,
            content_rowid=id
        );
        
        -- Trigger pro automatickou aktualizaci FTS při INSERT
        CREATE TRIGGER IF NOT EXISTS plant_catalog_ai AFTER INSERT ON plant_catalog BEGIN
            INSERT INTO plant_catalog_fts(rowid, latin_name, variety, flower_color, notes)
            VALUES (new.id, new.latin_name, new.variety, new.flower_color, new.notes);
        END;
        
        -- Trigger pro automatickou aktualizaci FTS při DELETE
        CREATE TRIGGER IF NOT EXISTS plant_catalog_ad AFTER DELETE ON plant_catalog BEGIN
            DELETE FROM plant_catalog_fts WHERE rowid = old.id;
        END;
        
        -- Trigger pro automatickou aktualizaci FTS při UPDATE
        CREATE TRIGGER IF NOT EXISTS plant_catalog_au AFTER UPDATE ON plant_catalog BEGIN
            UPDATE plant_catalog_fts SET 
                latin_name = new.latin_name,
                variety = new.variety,
                flower_color = new.flower_color,
                notes = new.notes
            WHERE rowid = new.id;
        END;
        """)
        db.commit()
    except Exception as fts_err:
        print(f"[DB] FTS setup note: {fts_err}")
    
    # ============================================================
    # SAFETY NET: Ensure ALL columns exist on ALL tables
    # Migrations can fail silently - this catches everything
    # ============================================================
    _ensure_columns = {
        "jobs": [
            ("completed_at", "TEXT"),
            ("created_date", "TEXT"),
            ("start_date", "TEXT"),
            ("progress", "INTEGER DEFAULT 0"),
            ("type", "TEXT DEFAULT 'construction'"),
            ("priority", "TEXT DEFAULT 'medium'"),
            ("description", "TEXT"),
            ("internal_note", "TEXT"),
            ("tags", "TEXT DEFAULT '[]'"),
            ("planned_end_date", "DATE"),
            ("actual_end_date", "DATE"),
            ("deadline", "DATE"),
            ("deadline_type", "TEXT DEFAULT 'soft'"),
            ("deadline_reason", "TEXT"),
            ("buffer_days", "INTEGER DEFAULT 0"),
            ("weather_dependent", "INTEGER DEFAULT 0"),
            ("seasonal_constraints", "TEXT"),
            ("estimated_value", "REAL"),
            ("estimated_hours", "INTEGER"),
            ("actual_value", "REAL DEFAULT 0"),
            ("actual_hours", "INTEGER DEFAULT 0"),
            ("budget_labor", "REAL DEFAULT 0"),
            ("budget_materials", "REAL DEFAULT 0"),
            ("budget_equipment", "REAL DEFAULT 0"),
            ("budget_other", "REAL DEFAULT 0"),
            ("pricing_type", "TEXT DEFAULT 'fixed'"),
            ("hourly_rate", "REAL"),
            ("payment_terms", "TEXT"),
            ("vat_rate", "INTEGER DEFAULT 21"),
            ("price_includes_vat", "INTEGER DEFAULT 1"),
            ("project_manager_id", "INTEGER"),
            ("completion_percent", "INTEGER DEFAULT 0"),
            ("budget_spent_percent", "INTEGER DEFAULT 0"),
            ("profit_margin", "REAL"),
            ("on_track", "INTEGER DEFAULT 1"),
            ("created_by", "INTEGER"),
            ("created_from_template", "TEXT"),
            ("is_template", "INTEGER DEFAULT 0"),
            ("actual_labor_cost", "REAL DEFAULT 0"),
            ("actual_material_cost", "REAL DEFAULT 0"),
            ("invoiced", "INTEGER DEFAULT 0"),
            ("address", "TEXT DEFAULT ''"),
            ("budget", "REAL DEFAULT 0"),
            ("party_id", "INTEGER"),
            ("job_type", "TEXT DEFAULT 'client'"),
        ],
        "employees": [
            ("phone", "TEXT DEFAULT ''"),
            ("email", "TEXT DEFAULT ''"),
            ("address", "TEXT DEFAULT ''"),
            ("position", "TEXT DEFAULT ''"),
            ("birth_date", "TEXT"),
            ("contract_type", "TEXT DEFAULT 'HPP'"),
            ("start_date", "TEXT"),
            ("hourly_rate", "REAL"),
            ("salary", "REAL"),
            ("skills", "TEXT"),
            ("location", "TEXT"),
            ("status", "TEXT DEFAULT 'active'"),
            ("rating", "REAL DEFAULT 0"),
            ("avatar_url", "TEXT"),
            ("delegate_employee_id", "INTEGER"),
            ("approver_delegate_employee_id", "INTEGER"),
            ("user_id", "INTEGER"),
            ("skill_score", "REAL DEFAULT 50"),
            ("training_hours_total", "REAL DEFAULT 0"),
            ("last_training_date", "TEXT"),
        ],
        "users": [
            ("role", "VARCHAR(20) DEFAULT 'worker'"),
            ("manager_id", "INTEGER"),
        ],
        "tasks": [
            ("created_at", "TEXT NOT NULL DEFAULT (datetime('now'))"),
            ("deadline", "TEXT"),
            ("depends_on", "TEXT"),
            ("due_date", "TEXT"),
            ("created_by", "TEXT"),
            ("priority", "TEXT DEFAULT 'normal'"),
        ],
        "task_assignments": [
            ("is_primary", "INTEGER NOT NULL DEFAULT 0"),
        ],
        "issue_assignments": [
            ("is_primary", "INTEGER NOT NULL DEFAULT 0"),
        ],
        "timesheets": [
            ("user_id", "INTEGER"),
            ("duration_minutes", "INTEGER"),
            ("work_type", "TEXT DEFAULT 'manual'"),
            ("start_time", "TEXT"),
            ("end_time", "TEXT"),
            ("location", "TEXT"),
            ("task_id", "INTEGER"),
            ("material_used", "TEXT"),
            ("weather_snapshot", "TEXT"),
            ("performance_signal", "TEXT DEFAULT 'normal'"),
            ("delay_reason", "TEXT"),
            ("photo_url", "TEXT"),
            ("note", "TEXT"),
            ("ai_flags", "TEXT"),
            ("created_at", "TEXT NOT NULL DEFAULT (datetime('now'))"),
            ("labor_cost", "REAL"),
            ("delay_note", "TEXT"),
            ("training_id", "INTEGER"),
        ],
        "trainings": [
            ("compensation_type", "TEXT DEFAULT 'paid_workday'"),
            ("wage_cost", "REAL DEFAULT 0"),
            ("wage_cost_per_person", "REAL"),
            ("participants", "TEXT DEFAULT '[]'"),
            ("title", "TEXT"),
        ],
    }
    for table, columns in _ensure_columns.items():
        try:
            existing = [r[1] for r in db.execute(f"PRAGMA table_info({table})").fetchall()]
        except Exception:
            continue
        for col_name, col_def in columns:
            if col_name not in existing:
                try:
                    db.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")
                    print(f"[DB] Added missing column: {table}.{col_name}")
                except Exception:
                    pass
    db.commit()

def seed_admin():
    db = get_db()
    cur = db.execute("SELECT COUNT(*) c FROM users")
    if cur.fetchone()["c"] == 0:
        db.execute(
            "INSERT INTO users(email,name,role,password_hash,active,created_at) VALUES (?,?,?,?,1,?)",
            (
                os.environ.get("ADMIN_EMAIL","admin@greendavid.local"),
                os.environ.get("ADMIN_NAME","Admin"),
                "owner",  # Vytvořit jako owner místo admin
                generate_password_hash(os.environ.get("ADMIN_PASSWORD","admin123"), method='pbkdf2:sha256'),
                datetime.utcnow().isoformat()
            )
        )
        db.commit()

def _auto_upgrade_admins_to_owner():
    """Automaticky upgrade admin účtů na owner při startu"""
    db = get_db()
    try:
        # Upgrade známých admin emailů
        admin_emails = ['admin@greendavid.local', 'david@greendavid.cz', 'admin@greendavid.cz', 'admin@example.com']
        for email in admin_emails:
            result = db.execute(
                "UPDATE users SET role = 'owner' WHERE email = ? AND (role IS NULL OR role != 'owner' OR role = 'admin')",
                (email,)
            )
            if result.rowcount > 0:
                db.commit()
                print(f"[DB] Auto-upgraded {email} to owner role")
        
        # Pokud žádný owner neexistuje, upgrade prvního uživatele
        owner_exists = db.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'owner'").fetchone()
        if owner_exists['cnt'] == 0:
            first_user = db.execute("SELECT id, email FROM users ORDER BY id LIMIT 1").fetchone()
            if first_user:
                db.execute("UPDATE users SET role = 'owner' WHERE id = ?", (first_user['id'],))
                db.commit()
                print(f"[DB] Auto-upgraded first user {first_user['email']} to owner role")
        
        # Upgrade všech admin účtů na owner
        result = db.execute(
            "UPDATE users SET role = 'owner' WHERE role = 'admin' OR role IS NULL"
        )
        if result.rowcount > 0:
            db.commit()
            print(f"[DB] Auto-upgraded {result.rowcount} admin/NULL accounts to owner role")
    except Exception as e:
        print(f"[DB] Warning: Could not auto-upgrade admin: {e}")

def seed_employees():
    db = get_db()
    cur = db.execute("SELECT COUNT(*) c FROM employees")
    if cur.fetchone()["c"] == 0:
        # Původní zaměstnanci
        employees = [
            ("david", "zahradník"),
            ("vendi", "zahradník"),
            ("jason", "zahradník"),
        ]
        for name, role in employees:
            db.execute("INSERT INTO employees(name,role) VALUES (?,?)", (name, role))
        db.commit()

def seed_plant_catalog():
    """Automaticky naplní katalog rostlin z JSON souboru pokud je prázdný"""
    db = get_db()
    cur = db.execute("SELECT COUNT(*) c FROM plant_catalog")
    if cur.fetchone()["c"] == 0:
        # Hledej JSON soubor s daty
        import json
        json_paths = [
            'plant_catalog_data.json',
            os.path.join(os.path.dirname(__file__), 'plant_catalog_data.json'),
            '/app/plant_catalog_data.json',
        ]
        
        for json_path in json_paths:
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        plants = json.load(f)
                    
                    imported = 0
                    for plant in plants:
                        try:
                            db.execute('''
                                INSERT OR IGNORE INTO plant_catalog 
                                (latin_name, variety, container_size, flower_color, flowering_time,
                                 leaf_color, height, light_requirements, site_type, plants_per_m2,
                                 hardiness_zone, notes)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                plant.get('latin_name'),
                                plant.get('variety'),
                                plant.get('container_size'),
                                plant.get('flower_color'),
                                plant.get('flowering_time'),
                                plant.get('leaf_color'),
                                plant.get('height'),
                                plant.get('light_requirements'),
                                plant.get('site_type'),
                                plant.get('plants_per_m2'),
                                plant.get('hardiness_zone'),
                                plant.get('notes')
                            ))
                            imported += 1
                        except Exception as e:
                            pass  # Skip duplicates or errors
                    
                    db.commit()
                    
                    # Rebuild FTS index
                    try:
                        db.execute("INSERT INTO plant_catalog_fts(plant_catalog_fts) VALUES('rebuild')")
                        db.commit()
                    except Exception:
                        pass
                    
                    print(f"[DB] Imported {imported} plants from {json_path}")
                    break
                except Exception as e:
                    print(f"[DB] Error importing plant catalog: {e}")

def _migrate_crew_control_tables():
    """Create Crew Control System tables if they don't exist"""
    db = get_db()
    try:
        # Check if tables exist
        tables_to_create = [
            ("employee_skills", '''
                CREATE TABLE IF NOT EXISTS employee_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    skill_type TEXT NOT NULL,
                    skill_name TEXT NOT NULL,
                    level INTEGER DEFAULT 1,
                    certified INTEGER DEFAULT 0,
                    certified_date TEXT,
                    certified_by TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            '''),
            ("employee_certifications", '''
                CREATE TABLE IF NOT EXISTS employee_certifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    cert_name TEXT NOT NULL,
                    cert_type TEXT,
                    issued_date TEXT,
                    expiry_date TEXT,
                    issuer TEXT,
                    document_url TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            '''),
            ("employee_preferences", '''
                CREATE TABLE IF NOT EXISTS employee_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL UNIQUE,
                    preferred_work_types TEXT,
                    avoided_work_types TEXT,
                    max_weekly_hours REAL DEFAULT 40,
                    preferred_locations TEXT,
                    travel_radius_km INTEGER DEFAULT 50,
                    prefers_team_work INTEGER DEFAULT 1,
                    prefers_solo_work INTEGER DEFAULT 0,
                    notes TEXT,
                    updated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            '''),
            ("employee_capacity", '''
                CREATE TABLE IF NOT EXISTS employee_capacity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    week_start TEXT NOT NULL,
                    planned_hours REAL DEFAULT 40,
                    assigned_hours REAL DEFAULT 0,
                    actual_hours REAL DEFAULT 0,
                    utilization_pct REAL DEFAULT 0,
                    status TEXT DEFAULT 'available',
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                    UNIQUE(employee_id, week_start)
                )
            '''),
            ("employee_performance", '''
                CREATE TABLE IF NOT EXISTS employee_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    total_hours REAL DEFAULT 0,
                    completed_tasks INTEGER DEFAULT 0,
                    on_time_rate REAL DEFAULT 100,
                    quality_score REAL DEFAULT 0,
                    efficiency_score REAL DEFAULT 0,
                    reliability_score REAL DEFAULT 0,
                    notes TEXT,
                    calculated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            '''),
            ("employee_ai_scores", '''
                CREATE TABLE IF NOT EXISTS employee_ai_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    score_date TEXT NOT NULL,
                    balance_score REAL DEFAULT 50,
                    workload_score REAL DEFAULT 50,
                    burnout_risk REAL DEFAULT 0,
                    recommendation TEXT,
                    factors TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            '''),
            ("employee_availability", '''
                CREATE TABLE IF NOT EXISTS employee_availability (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    availability_type TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    all_day INTEGER DEFAULT 1,
                    notes TEXT,
                    approved INTEGER DEFAULT 0,
                    approved_by INTEGER,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            ''')
        ]
        
        for table_name, create_sql in tables_to_create:
            if not _table_exists(db, table_name):
                db.execute(create_sql)
                db.commit()
                print(f"[DB] Created table: {table_name}")
        
        # Add new columns to employees table
        if _table_exists(db, "employees"):
            cols = [r[1] for r in db.execute("PRAGMA table_info(employees)").fetchall()]
            new_cols = {
                "weekly_capacity": "REAL DEFAULT 40",
                "current_workload": "REAL DEFAULT 0",
                "ai_balance_score": "REAL DEFAULT 50",
                "burnout_risk": "REAL DEFAULT 0",
                "reliability_score": "REAL DEFAULT 0",
                "specializations": "TEXT",
                "availability_status": "TEXT DEFAULT 'available'",
            }
            for col_name, col_def in new_cols.items():
                if col_name not in cols:
                    try:
                        db.execute(f"ALTER TABLE employees ADD COLUMN {col_name} {col_def}")
                        db.commit()
                        print(f"[DB] Added column: employees.{col_name}")
                    except Exception as e:
                        pass  # Column might already exist
                        
    except Exception as e:
        print(f"[DB] Crew Control migration warning: {e}")


def _backfill_labor_costs():
    """Přepočítá labor_cost u výkazů kde chybí (NULL nebo 0)."""
    db = get_db()
    try:
        ts_cols = [r[1] for r in db.execute("PRAGMA table_info(timesheets)").fetchall()]
        if "labor_cost" not in ts_cols:
            return
        rows = db.execute("""
            SELECT t.id, t.employee_id, t.hours, t.duration_minutes, e.hourly_rate
            FROM timesheets t
            JOIN employees e ON e.id = t.employee_id
            WHERE t.labor_cost IS NULL OR t.labor_cost = 0
        """).fetchall()
        for r in rows:
            rate = r["hourly_rate"] if r["hourly_rate"] is not None else 250.0
            hours = r["hours"] if r["hours"] is not None else (r["duration_minutes"] or 0) / 60.0
            cost = round(rate * hours, 2)
            db.execute("UPDATE timesheets SET labor_cost = ? WHERE id = ?", (cost, r["id"]))
        db.commit()
        if rows:
            print(f"[DB] Backfilled labor_cost for {len(rows)} timesheets")
    except Exception as e:
        print(f"[DB] Backfill labor_cost warning: {e}")


from app.database import get_db, _table_exists
from app.utils.migrations import (
    seed_admin, _auto_upgrade_admins_to_owner, seed_employees, seed_plant_catalog,
    _migrate_completed_at, _migrate_employees_enhanced,
    _migrate_roles_and_hierarchy, _migrate_crew_control_tables,
    ensure_schema, apply_migrations
)

# Startup initialization function from main.py
def _ensure():
    # Run schema checks / migrations once per process to avoid unnecessary locking
    if not getattr(_ensure, "_schema_ready", False):
        ensure_schema()
        try:
            apply_migrations()
        except Exception as e:
            # Never break the app startup/runtime on a migration helper issue
            print(f"[DB] Migration failed: {e}")
        # Legacy migrations (kept for backward compatibility with older app.db variants)
        try:
            _migrate_completed_at()
            _migrate_employees_enhanced()
            _migrate_roles_and_hierarchy()
            _migrate_crew_control_tables()  # New: Crew Control System tables
            _backfill_labor_costs()  # Propojení výkazů → finance (PRÁCE)
        except Exception as e:
            print(f"[DB] Migration warning: {e}")
        _ensure._schema_ready = True
    seed_admin()
    _auto_upgrade_admins_to_owner()
    seed_employees()
    seed_plant_catalog()

    """Create Crew Control System tables if they don't exist"""
    db = get_db()
    try:
        tables_to_create = [
            ("employee_skills", '''
                CREATE TABLE IF NOT EXISTS employee_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    skill_type TEXT NOT NULL,
                    skill_name TEXT NOT NULL,
                    level INTEGER DEFAULT 1,
                    certified INTEGER DEFAULT 0,
                    certified_date TEXT,
                    certified_by TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            '''),
            ("employee_certifications", '''
                CREATE TABLE IF NOT EXISTS employee_certifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    cert_name TEXT NOT NULL,
                    cert_type TEXT,
                    issued_date TEXT,
                    expiry_date TEXT,
                    issuer TEXT,
                    document_url TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            '''),
            ("employee_preferences", '''
                CREATE TABLE IF NOT EXISTS employee_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL UNIQUE,
                    preferred_work_types TEXT,
                    avoided_work_types TEXT,
                    max_weekly_hours REAL DEFAULT 40,
                    preferred_locations TEXT,
                    travel_radius_km INTEGER DEFAULT 50,
                    prefers_team_work INTEGER DEFAULT 1,
                    prefers_solo_work INTEGER DEFAULT 0,
                    notes TEXT,
                    updated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            '''),
            ("employee_capacity", '''
                CREATE TABLE IF NOT EXISTS employee_capacity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    week_start TEXT NOT NULL,
                    planned_hours REAL DEFAULT 40,
                    assigned_hours REAL DEFAULT 0,
                    actual_hours REAL DEFAULT 0,
                    utilization_pct REAL DEFAULT 0,
                    status TEXT DEFAULT 'available',
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                    UNIQUE(employee_id, week_start)
                )
            '''),
            ("employee_performance", '''
                CREATE TABLE IF NOT EXISTS employee_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    total_hours REAL DEFAULT 0,
                    completed_tasks INTEGER DEFAULT 0,
                    on_time_rate REAL DEFAULT 100,
                    quality_score REAL DEFAULT 0,
                    efficiency_score REAL DEFAULT 0,
                    reliability_score REAL DEFAULT 0,
                    notes TEXT,
                    calculated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            '''),
            ("employee_ai_scores", '''
                CREATE TABLE IF NOT EXISTS employee_ai_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    score_date TEXT NOT NULL,
                    balance_score REAL DEFAULT 50,
                    workload_score REAL DEFAULT 50,
                    burnout_risk REAL DEFAULT 0,
                    recommendation TEXT,
                    factors TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            '''),
            ("employee_availability", '''
                CREATE TABLE IF NOT EXISTS employee_availability (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    availability_type TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    all_day INTEGER DEFAULT 1,
                    notes TEXT,
                    approved INTEGER DEFAULT 0,
                    approved_by INTEGER,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            ''')
        ]
        for table_name, create_sql in tables_to_create:
            if not _table_exists(db, table_name):
                db.execute(create_sql)
                db.commit()
                print(f"[DB] Created table: {table_name}")
        if _table_exists(db, "employees"):
            cols = [r[1] for r in db.execute("PRAGMA table_info(employees)").fetchall()]
            new_cols = {
                "weekly_capacity": "REAL DEFAULT 40",
                "current_workload": "REAL DEFAULT 0",
                "ai_balance_score": "REAL DEFAULT 50",
                "burnout_risk": "REAL DEFAULT 0",
                "reliability_score": "REAL DEFAULT 0",
                "specializations": "TEXT",
                "availability_status": "TEXT DEFAULT 'available'",
            }
            for col_name, col_def in new_cols.items():
                if col_name not in cols:
                    try:
                        db.execute(f"ALTER TABLE employees ADD COLUMN {col_name} {col_def}")
                        db.commit()
                        print(f"[DB] Added column: employees.{col_name}")
                    except Exception as e:
                        pass  # Column might already exist
    except Exception as e:
        print(f"[DB] Crew Control migration warning: {e}")
