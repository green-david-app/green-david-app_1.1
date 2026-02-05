#!/usr/bin/env python3
"""
Přidá chybějící sloupce do databáze
"""

import sqlite3
import sys
from datetime import datetime

def add_columns():
    try:
        db = sqlite3.connect('app.db')
        cursor = db.cursor()
        
        print("🔧 Přidávám chybějící sloupce...\n")
        
        # 1. Přidat position do employees
        try:
            cursor.execute("ALTER TABLE employees ADD COLUMN position TEXT")
            print("✅ Přidán sloupec: employees.position")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("⏭️  Sloupec employees.position již existuje")
            else:
                print(f"⚠️  Warning: {e}")
        
        # 2. Přidat start_date do jobs
        try:
            cursor.execute("ALTER TABLE jobs ADD COLUMN start_date TEXT")
            print("✅ Přidán sloupec: jobs.start_date")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("⏭️  Sloupec jobs.start_date již existuje")
            else:
                print(f"⚠️  Warning: {e}")
        
        # 3. Přidat description do jobs (pokud neexistuje)
        try:
            cursor.execute("ALTER TABLE jobs ADD COLUMN description TEXT")
            print("✅ Přidán sloupec: jobs.description")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("⏭️  Sloupec jobs.description již existuje")
            else:
                print(f"⚠️  Warning: {e}")
        
        db.commit()
        print("\n✅ Hotovo!")
        
    except Exception as e:
        print(f"\n❌ Chyba: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    add_columns()
