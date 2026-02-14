import sqlite3
import os
from flask import g
from app.config import DATABASE as DB_PATH

def get_db():
    if "db" not in g:
        # Ensure directory exists for DB_PATH
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                print(f"[DB] Created directory: {db_dir}")
            except Exception as e:
                print(f"[DB] Warning: Could not create directory {db_dir}: {e}")
        
        # Log database path (only once at startup)
        if not hasattr(get_db, '_logged'):
            print(f"[DB] Using database: {DB_PATH}")
            get_db._logged = True
        
        # Connect with WAL mode for better concurrency
        # Use a small timeout to reduce 'database is locked' errors under concurrent requests
        g.db = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=5)
        g.db.row_factory = sqlite3.Row
        # Enable WAL mode for better performance and durability
        try:
            g.db.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass
    return g.db

def _table_has_column(db, table: str, column: str) -> bool:
    try:
        rows = db.execute(f"PRAGMA table_info({table})").fetchall()
        return any(r[1] == column for r in rows)
    except Exception:
        return False


def _table_exists(db, table: str) -> bool:
    """Return True if a table exists in the current SQLite database."""
    try:
        r = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
            (table,),
        ).fetchone()
        return bool(r)
    except Exception:
        return False


def close_db(exception=None):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass
