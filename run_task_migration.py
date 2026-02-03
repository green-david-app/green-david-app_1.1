#!/usr/bin/env python3
"""
Script to run Task Data Model migration (version 21)
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, get_db, apply_migrations, ensure_schema

def run_migration():
    """Run the migration"""
    with app.app_context():
        print("[MIGRATION] Starting Task Data Model migration...")
        
        # Ensure base schema exists
        print("[MIGRATION] Ensuring base schema...")
        ensure_schema()
        
        # Apply migrations (including version 21)
        print("[MIGRATION] Applying migrations...")
        try:
            apply_migrations()
            print("[MIGRATION] ✓ Migration completed successfully!")
            
            # Verify tables were created
            db = get_db()
            tables_to_check = ['tasks_new', 'task_materials', 'task_evidence', 'material_reservations']
            for table in tables_to_check:
                from main import _table_exists
                if _table_exists(db, table):
                    print(f"[MIGRATION] ✓ Table '{table}' exists")
                else:
                    print(f"[MIGRATION] ⚠ Table '{table}' does not exist")
            
            # Check migration version
            version = db.execute("SELECT MAX(version) as max_version FROM schema_migrations").fetchone()
            if version and version[0]:
                print(f"[MIGRATION] ✓ Latest migration version: {version[0]}")
            
        except Exception as e:
            print(f"[MIGRATION] ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
