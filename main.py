import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request, g, send_from_directory

# --- App setup ---
app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "app.db")
os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)

# --- DB helpers & migrations ---

def get_db() -> sqlite3.Connection:
    db = getattr(g, "_db", None)
    if db is None:
        db = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
        db.row_factory = sqlite3.Row
        g._db = db
        _ensure_schema(db)
    return db

@app.teardown_appcontext
def _close_db(exc=None):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()

def _table_columns(db: sqlite3.Connection, table: str) -> List[str]:
    cur = db.execute(f"PRAGMA table_info({table})")
    return [r["name"] for r in cur.fetchall()]

def _add_column_if_missing(db: sqlite3.Connection, table: str, name: str, ddl_type: str, default_sql: Optional[str] = None):
    cols = _table_columns(db, table)
    if name not in cols:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl_type}")
        if default_sql is not None:
            db.execute(f"UPDATE {table} SET {name} = {default_sql}")

def _ensure_schema(db: sqlite3.Connection):
    # users
    db.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        name TEXT,
        role TEXT DEFAULT 'admin'
    )""")
    # employees
    db.execute("""CREATE TABLE IF NOT EXISTS employees(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        active INTEGER DEFAULT 1
    )""")
    # jobs
    db.execute("""CREATE TABLE IF NOT EXISTS jobs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        city TEXT,
        label TEXT
    )""")
    # timesheets
    db.execute("""CREATE TABLE IF NOT EXISTS timesheets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        employee_id INTEGER NOT NULL,
        job_id INTEGER,
        hours REAL NOT NULL,
        place TEXT,
        note TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(id),
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    )""")
    # calendar_events
    db.execute("""CREATE TABLE IF NOT EXISTS calendar_events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        title TEXT,
        kind TEXT DEFAULT 'note',
        job_id INTEGER,
        start_time TEXT,
        end_time TEXT,
        note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # Migrations: guard for missing columns on existing DBs
    for col, type_ in [
        ("title", "TEXT"), ("kind", "TEXT"), ("job_id", "INTEGER"),
        ("start_time", "TEXT"), ("end_time", "TEXT"), ("note", "TEXT"),
        ("created_at", "TEXT")
    ]:
        _add_column_if_missing(db, "calendar_events", col, type_)

    for col, type_ in [("place", "TEXT"), ("note", "TEXT")]:
        _add_column_if_missing(db, "timesheets", col, type_)

    # seed minimal data if empty
    if db.execute("SELECT COUNT(1) AS c FROM users").fetchone()["c"] == 0:
        db.execute("INSERT INTO users(email,name,role) VALUES(?,?,?)",
                   ("admin@greendavid.local", "Admin", "admin"))
    if db.execute("SELECT COUNT(1) AS c FROM employees").fetchone()["c"] == 0:
        db.executemany("INSERT INTO employees(name,active) VALUES(?,1)",
                       [("michal",), ("john",), ("honza",)])
    if db.execute("SELECT COUNT(1) AS c FROM jobs").fetchone()["c"] == 0:
        db.executemany("INSERT INTO jobs(title,city,label) VALUES(?,?,?)",
                       [("zahrada Třebonice", "Praha", "09-2025"),
                        ("bla", "Praha", "10-2025")])

# --- utility ---

def _normalize_date(s: Optional[str]) -> str:
    if not s:
        return datetime.utcnow().strftime("%Y-%m-%d")
    # Accept 'DD.MM.YYYY' or 'YYYY-MM-DD'
    s = s.strip()
    if "." in s:
        d, m, y = s.split(".")[:3]
        d = d.zfill(2); m = m.zfill(2)
        return f"{y}-{m}-{d}"
    return s

def require_role(write: bool=False):
    # trivial auth stub – always allow
    return ({"user": "admin", "role": "admin"}, None)

# --- Routes ---

@app.route("/api/me")
def api_me():
    return jsonify({"name":"Admin","email":"admin@greendavid.local","role":"admin","tasks":1})

# Jobs
@app.route("/api/jobs", methods=["GET","POST","DELETE"])
def api_jobs():
    get_db()  # ensure schema
    db = get_db()
    if request.method == "GET":
        rows = db.execute("SELECT id, title, city, label FROM jobs ORDER BY id DESC").fetchall()
        return jsonify([dict(r) for r in rows])
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "bez názvu").strip()
        city = (data.get("city") or "").strip()
        label = (data.get("label") or "").strip()
        db.execute("INSERT INTO jobs(title,city,label) VALUES(?,?,?)",(title,city,label))
        return jsonify({"ok":True})
    # DELETE
    job_id = request.args.get("id", type=int)
    if not job_id:
        return jsonify({"ok":False,"error":"id required"}), 400
    db.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    return jsonify({"ok":True})

# Employees
@app.route("/api/employees")
def api_employees():
    db = get_db()
    rows = db.execute("SELECT id, name, active FROM employees ORDER BY id").fetchall()
    return jsonify([dict(r) for r in rows])

# Timesheets (aliases)
def _timesheets_get(db):
    emp_id = request.args.get("employee_id", type=int)
    if emp_id:
        rows = db.execute("""SELECT t.id, t.date, e.name as employee, t.employee_id, j.title as job,
                                  t.job_id, t.hours, t.place, t.note
                             FROM timesheets t
                             LEFT JOIN employees e ON e.id=t.employee_id
                             LEFT JOIN jobs j ON j.id=t.job_id
                             WHERE t.employee_id=?
                             ORDER BY t.date DESC, t.id DESC""", (emp_id,)).fetchall()
    else:
        rows = db.execute("""SELECT t.id, t.date, e.name as employee, t.employee_id, j.title as job,
                                  t.job_id, t.hours, t.place, t.note
                             FROM timesheets t
                             LEFT JOIN employees e ON e.id=t.employee_id
                             LEFT JOIN jobs j ON j.id=t.job_id
                             ORDER BY t.date DESC, t.id DESC""").fetchall()
    return jsonify([dict(r) for r in rows])

def _timesheets_post(db):
    data = request.get_json(silent=True) or {}
    date = _normalize_date(data.get("date"))
    employee_id = int(data.get("employee_id"))
    job_id = data.get("job_id")
    job_id = int(job_id) if job_id is not None else None
    hours = float(data.get("hours") or 0)
    place = (data.get("place") or "").strip()
    note = (data.get("note") or "").strip()
    db.execute("INSERT INTO timesheets(date, employee_id, job_id, hours, place, note) VALUES (?,?,?,?,?,?)",
               (date, employee_id, job_id, hours, place, note))
    return jsonify({"ok":True})

def _timesheets_delete(db):
    ts_id = request.args.get("id", type=int)
    if not ts_id:
        return jsonify({"ok":False,"error":"id required"}),400
    db.execute("DELETE FROM timesheets WHERE id=?", (ts_id,))
    return jsonify({"ok":True})

@app.route("/api/timesheets", methods=["GET","POST","DELETE"])
@app.route("/gd/api/timesheets", methods=["GET","POST","DELETE"])
def api_timesheets():
    db = get_db()
    if request.method == "GET":
        return _timesheets_get(db)
    if request.method == "POST":
        return _timesheets_post(db)
    return _timesheets_delete(db)

# Calendar (aliases)
def _calendar_list(db):
    d_from = request.args.get("from")
    d_to = request.args.get("to")
    if d_from and d_to:
        rows = db.execute("""SELECT * FROM calendar_events
                             WHERE date BETWEEN ? AND ?
                             ORDER BY date ASC, COALESCE(start_time,'') ASC""",
                          (d_from, d_to)).fetchall()
    else:
        rows = db.execute("""SELECT * FROM calendar_events
                             ORDER BY date DESC, COALESCE(start_time,'') ASC
                             LIMIT 1000""").fetchall()
    return jsonify([dict(r) for r in rows])

def _calendar_create(db):
    data = request.get_json(silent=True) or {}
    date = _normalize_date(data.get("date"))
    title = (data.get("title") or "").strip()
    kind = (data.get("kind") or "note").strip()
    job_id = data.get("job_id")
    job_id = int(job_id) if job_id is not None else None
    start_time = (data.get("start_time") or "").strip()
    end_time = (data.get("end_time") or "").strip()
    note = (data.get("note") or "").strip()
    cur = db.execute("""INSERT INTO calendar_events(date,title,kind,job_id,start_time,end_time,note)
                        VALUES(?,?,?,?,?,?,?)""",
                     (date,title,kind,job_id,start_time,end_time,note))
    return jsonify({"ok":True,"id":cur.lastrowid})

def _calendar_delete(db):
    cid = request.args.get("id", type=int)
    if not cid:
        return jsonify({"ok":False,"error":"id required"}), 400
    db.execute("DELETE FROM calendar_events WHERE id=?", (cid,))
    return jsonify({"ok":True})

@app.route("/api/calendar", methods=["GET","POST","DELETE"])
@app.route("/gd/api/calendar", methods=["GET","POST","DELETE"])
def api_calendar():
    db = get_db()
    if request.method == "GET":
        return _calendar_list(db)
    if request.method == "POST":
        return _calendar_create(db)
    return _calendar_delete(db)

# Basic static files for logo/style (optional)
@app.route("/logo.jpg")
def logo():
    return send_from_directory(".", "logo.jpg")

@app.route("/style.css")
def style():
    return send_from_directory(".", "style.css")

# WSGI export
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
