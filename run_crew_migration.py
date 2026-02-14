#!/usr/bin/env python3
"""
Crew Control System Migration Script
Adds all necessary tables and columns for the Crew Control System feature.
Run this script to migrate your database.
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.environ.get('DATABASE_PATH', 'app.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def table_exists(db, table_name):
    cur = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cur.fetchone() is not None

def column_exists(db, table_name, column_name):
    cur = db.execute(f"PRAGMA table_info({table_name})")
    cols = [row[1] for row in cur.fetchall()]
    return column_name in cols

def run_migration():
    db = get_db()
    print("=" * 60)
    print("CREW CONTROL SYSTEM - Database Migration")
    print("=" * 60)
    
    # 1. Add new columns to employees table
    print("\n[1/4] Adding new columns to employees table...")
    
    new_employee_cols = {
        "weekly_capacity": "REAL DEFAULT 40",
        "current_workload": "REAL DEFAULT 0",
        "ai_balance_score": "REAL DEFAULT 50",
        "burnout_risk": "REAL DEFAULT 0",
        "reliability_score": "REAL DEFAULT 0",
        "last_performance_calc": "TEXT",
        "preferred_work_type": "TEXT",
        "crew_role": "TEXT DEFAULT 'general'",  # general, specialist, lead, support
        "mission_count": "INTEGER DEFAULT 0",
        "specializations": "TEXT",  -- JSON array
        "availability_status": "TEXT DEFAULT 'available'",  -- available, partial, unavailable, vacation
        "current_location_id": "INTEGER",
        "last_location_update": "TEXT",
    }
    
    for col_name, col_def in new_employee_cols.items():
        if not column_exists(db, "employees", col_name):
            try:
                db.execute(f"ALTER TABLE employees ADD COLUMN {col_name} {col_def}")
                db.commit()
                print(f"  ✓ Added: employees.{col_name}")
            except Exception as e:
                print(f"  ⚠ Skipped employees.{col_name}: {e}")
        else:
            print(f"  - Exists: employees.{col_name}")
    
    # 2. Run SQL migration file
    print("\n[2/4] Creating Crew Control System tables...")
    
    sql_path = os.path.join(os.path.dirname(__file__), 'migrations', '003_crew_control_system.sql')
    if os.path.exists(sql_path):
        with open(sql_path, 'r') as f:
            sql_script = f.read()
        
        try:
            db.executescript(sql_script)
            db.commit()
            print("  ✓ All tables created successfully")
        except Exception as e:
            print(f"  ⚠ Some statements may have failed: {e}")
    else:
        print(f"  ⚠ SQL file not found: {sql_path}")
        # Create tables inline
        create_tables_inline(db)
    
    # 3. Seed skill types
    print("\n[3/4] Seeding default skill types...")
    seed_default_skills(db)
    
    # 4. Calculate initial capacity for existing employees
    print("\n[4/4] Calculating initial capacity...")
    calculate_initial_capacity(db)
    
    db.close()
    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)

def create_tables_inline(db):
    """Create tables if SQL file is not available"""
    
    tables = [
        """
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
        """,
        """
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
        """,
        """
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
        """,
        """
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
        """,
        """
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
        """,
        """
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
        """,
        """
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
        """
    ]
    
    for sql in tables:
        try:
            db.execute(sql)
            db.commit()
        except Exception as e:
            print(f"  ⚠ Table creation warning: {e}")

def seed_default_skills(db):
    """Seed default skill categories"""
    
    # Check if we have any employees
    emp_count = db.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    if emp_count == 0:
        print("  - No employees to seed skills for")
        return
    
    # Default skill types with Czech names
    skill_types = {
        'planting': 'Výsadba',
        'wood': 'Práce se dřevem',
        'logistics': 'Logistika',
        'planning': 'Plánování',
        'maintenance': 'Údržba',
        'heavy_work': 'Těžká práce',
        'communication': 'Komunikace',
        'machinery': 'Stroje',
        'irrigation': 'Zavlažování',
        'lawn': 'Trávníky',
        'stonework': 'Kamenické práce',
        'fencing': 'Oplocení',
    }
    
    print(f"  Available skill types: {len(skill_types)}")
    
def calculate_initial_capacity(db):
    """Calculate initial capacity for all employees"""
    
    today = datetime.now()
    # Get Monday of current week
    monday = today - timedelta(days=today.weekday())
    week_start = monday.strftime('%Y-%m-%d')
    
    employees = db.execute("SELECT id, name FROM employees").fetchall()
    
    for emp in employees:
        # Check if capacity record exists
        existing = db.execute(
            "SELECT id FROM employee_capacity WHERE employee_id=? AND week_start=?",
            (emp['id'], week_start)
        ).fetchone()
        
        if not existing:
            # Calculate assigned hours from timesheets this week
            week_end = (monday + timedelta(days=6)).strftime('%Y-%m-%d')
            
            hours_result = db.execute("""
                SELECT COALESCE(SUM(hours), 0) as total 
                FROM timesheets 
                WHERE employee_id=? AND date >= ? AND date <= ?
            """, (emp['id'], week_start, week_end)).fetchone()
            
            actual_hours = hours_result['total'] if hours_result else 0
            
            db.execute("""
                INSERT INTO employee_capacity 
                (employee_id, week_start, planned_hours, assigned_hours, actual_hours, utilization_pct, status)
                VALUES (?, ?, 40, ?, ?, ?, ?)
            """, (
                emp['id'],
                week_start,
                actual_hours,
                actual_hours,
                min(100, (actual_hours / 40) * 100) if actual_hours else 0,
                'available' if actual_hours < 32 else ('partial' if actual_hours < 45 else 'overloaded')
            ))
            
            print(f"  ✓ Capacity initialized for: {emp['name']}")
    
    db.commit()

if __name__ == '__main__':
    run_migration()
