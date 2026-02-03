#!/usr/bin/env python3
"""
Planning Module Migration Runner
Applies database changes for the Planning section
"""
import sqlite3
import os
import sys

DB_PATH = os.environ.get("DB_PATH", "app.db")

def run_migration():
    """Apply planning module migration"""
    print(f"[Migration] Connecting to: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        sys.exit(1)
    
    # Backup first
    backup_path = f"{DB_PATH}.backup_planning_{os.environ.get('USER', 'user')}"
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    print(f"[Backup] Created: {backup_path}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Read migration file
    migration_file = os.path.join(os.path.dirname(__file__), "migrations", "001_planning_module.sql")
    
    if not os.path.exists(migration_file):
        print(f"[ERROR] Migration file not found: {migration_file}")
        sys.exit(1)
    
    print(f"[Migration] Reading: {migration_file}")
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    try:
        # Execute migration
        print("[Migration] Applying changes...")
        cursor.executescript(sql_script)
        conn.commit()
        print("[Migration] ✅ SUCCESS - Planning module installed!")
        
        # Verify new tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('action_items', 'material_deliveries', 'daily_plans', 'employee_groups')")
        tables = cursor.fetchall()
        print(f"[Verify] New tables created: {', '.join([t[0] for t in tables])}")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"[ERROR] Migration failed: {e}")
        print(f"[Restore] Use backup: {backup_path}")
        sys.exit(1)
    
    finally:
        conn.close()
    
    print("\n[Next Steps]")
    print("1. Restart your Flask app")
    print("2. Navigate to /planning/timeline")
    print("3. Start planning!")

if __name__ == "__main__":
    run_migration()
