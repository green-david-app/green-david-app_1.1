#!/usr/bin/env python3
"""
Safe Column Addition - Planning Module
Adds columns to existing tables only if they don't exist
"""
import sqlite3
import os
import sys

DB_PATH = os.environ.get("DB_PATH", "app.db")

def column_exists(cursor, table, column):
    """Check if column exists in table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

def add_column_safe(cursor, table, column, type_def, default=None):
    """Add column only if it doesn't exist"""
    if not column_exists(cursor, table, column):
        sql = f"ALTER TABLE {table} ADD COLUMN {column} {type_def}"
        if default is not None:
            sql += f" DEFAULT {default}"
        print(f"  [+] Adding {table}.{column}")
        cursor.execute(sql)
        return True
    else:
        print(f"  [✓] {table}.{column} already exists")
        return False

def run_safe_migration():
    """Add columns safely"""
    print(f"[Migration] Connecting to: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        sys.exit(1)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("\n[Step 1] Adding columns to TASKS table...")
        add_column_safe(cursor, "tasks", "planned_date", "DATE")
        add_column_safe(cursor, "tasks", "planned_end_date", "DATE")
        add_column_safe(cursor, "tasks", "estimated_hours", "REAL")
        add_column_safe(cursor, "tasks", "actual_cost", "REAL", "0")
        add_column_safe(cursor, "tasks", "budget_hours", "REAL")
        
        print("\n[Step 2] Adding columns to JOBS table...")
        add_column_safe(cursor, "jobs", "start_date_planned", "DATE")
        add_column_safe(cursor, "jobs", "weather_check_enabled", "BOOLEAN", "0")
        
        conn.commit()
        print("\n[SUCCESS] ✅ All columns added safely!")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        sys.exit(1)
    
    finally:
        conn.close()

if __name__ == "__main__":
    run_safe_migration()
