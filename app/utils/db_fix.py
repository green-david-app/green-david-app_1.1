"""
Emergency database fix — přidej tento soubor do projektu jako app/utils/db_fix.py
a zavolej fix_database() z main.py PŘED startem aplikace.

Nebo přidej route /api/admin/fix-db pro manuální spuštění.
"""


def fix_database():
    """Fix missing columns in tasks and notes tables."""
    from app.database import get_db
    db = get_db()
    fixes_applied = []

    # === FIX 1: tasks.updated_at ===
    try:
        cols = [r[1] for r in db.execute("PRAGMA table_info(tasks)").fetchall()]
        if "updated_at" not in cols:
            db.execute("ALTER TABLE tasks ADD COLUMN updated_at TEXT")
            db.commit()
            fixes_applied.append("tasks.updated_at added")
            print("[DB-FIX] Added tasks.updated_at")
        else:
            print("[DB-FIX] tasks.updated_at already exists")
    except Exception as e:
        print(f"[DB-FIX] Error fixing tasks: {e}")

    # === FIX 2: notes table — check and rebuild if wrong schema ===
    try:
        # Check if notes table exists
        table_check = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='notes'"
        ).fetchone()

        if table_check:
            # Table exists — check columns
            cols = [r[1] for r in db.execute("PRAGMA table_info(notes)").fetchall()]
            print(f"[DB-FIX] Current notes columns: {cols}")

            missing = []
            required = ['title', 'content', 'category', 'color', 'is_pinned',
                        'job_id', 'employee_id', 'party_id', 'created_by',
                        'created_at', 'updated_at']
            for col in required:
                if col not in cols:
                    missing.append(col)

            if missing:
                print(f"[DB-FIX] Notes missing columns: {missing}")
                print("[DB-FIX] Rebuilding notes table...")
                # Count existing rows
                count = db.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
                print(f"[DB-FIX] Notes table has {count} rows (will be lost in rebuild)")

                db.executescript("""
                    DROP TABLE IF EXISTS notes;
                    CREATE TABLE notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        content TEXT NOT NULL DEFAULT '',
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
                """)
                fixes_applied.append("notes table rebuilt")
                print("[DB-FIX] Notes table rebuilt successfully")
            else:
                print("[DB-FIX] Notes table schema OK")
        else:
            # Table doesn't exist — create it
            print("[DB-FIX] Notes table missing, creating...")
            db.executescript("""
                CREATE TABLE notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    content TEXT NOT NULL DEFAULT '',
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
            """)
            fixes_applied.append("notes table created")
            print("[DB-FIX] Notes table created")

    except Exception as e:
        print(f"[DB-FIX] Error fixing notes: {e}")
        import traceback
        traceback.print_exc()

    # === FIX 3: Mark migration v33 as applied ===
    try:
        db.execute("INSERT OR IGNORE INTO schema_migrations(version) VALUES (33)")
        db.commit()
    except Exception:
        pass

    print(f"[DB-FIX] Done. Fixes applied: {fixes_applied or 'none needed'}")
    return fixes_applied
