#!/usr/bin/env python3
"""
Run Planning Extended Migration
"""
import sqlite3
import os
import sys
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "app.db")
MIGRATION_FILE = "migrations/002_planning_extended.sql"

def run_migration():
    print(f"[Migration] Connecting to: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        sys.exit(1)
    
    # Backup
    backup_name = f"{DB_PATH}.backup_extended_{os.getlogin()}"
    print(f"[Backup] Creating: {backup_name}")
    os.system(f"cp {DB_PATH} {backup_name}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print(f"[Migration] Reading: {os.path.abspath(MIGRATION_FILE)}")
        with open(MIGRATION_FILE, 'r') as f:
            sql = f.read()
        
        print("[Migration] Applying extended features...")
        cursor.executescript(sql)
        conn.commit()
        
        # Verify
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN (
                'nursery_plants',
                'recurring_task_templates',
                'materials',
                'task_photos',
                'plant_species',
                'maintenance_contracts'
            )
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"[Migration] ✅ SUCCESS - Extended features installed!")
        print(f"[Verify] New tables: {', '.join(tables)}")
        
        print("\n[Next Steps]")
        print("1. Restart Flask app")
        print("2. Navigate to /planning/nursery")
        print("3. Enjoy all new features!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        print(f"[Restore] Run: cp {backup_name} {DB_PATH}")
        sys.exit(1)
    
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
