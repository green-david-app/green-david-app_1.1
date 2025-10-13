# main.py
# green david app – minimal backend (Flask + SQLite)
# - FIX: root/SPA a statiky (už žádné 404 na "/")
# - FIX: kalendář – schéma + GET/POST/DELETE, bezpečné migrace
# - FIX: výkazy (timesheets) – get_json, place/note sloupce
# - BONUS: /admin/resequence-employees pro "přečíslování" čísel zaměstnanců
# - Základní /api/me, /api/jobs, /api/tasks, /api/employees (kompatibilní JSON)

import os
import sqlite3
from datetime import datetime, date as dt_date, timedelta
from flask import Flask, request, jsonify, send_from_directory

# -----------------------------------------------------------------------------
# App & statické soubory
# -----------------------------------------------------------------------------
app = Flask(
    __name__,
    static_folder=".",     # očekává style.css / logo.jpg / index.html v kořeni projektu
    static_url_path=""
)

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def spa(path):
    """
    Single-page app router:
      - pokud existuje konkrýtní soubor (style.css, logo.jpg, ...), pošle ho
      - jinak servíruje index.html (pokud existuje)
      - jako úplná poslední záchrana vrátí malou HTML stránku (aby to nebyla 404)
    """
    if path and os.path.exists(path) and not os.path.isdir(path):
        return send_from_directory(".", path)
    if os.path.exists("index.html"):
        return send_from_directory(".", "index.html")
    return ("<!doctype html><meta charset='utf-8'><title>green david app</title>"
            "<h1>green david app</h1><p>Index soubor chybí.</p>", 200)

# -----------------------------------------------------------------------------
# SQLite – pomocné funkce
# -----------------------------------------------------------------------------
def _db_path():
    # Render ne vždy používá env proměnnou "DATABASE_URL" pro SQLite, proto default
    return os.getenv("DATABASE_URL", "app.db")

def _connect_db():
    db = sqlite3.connect(_db_path(), check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db

def _table_info(db, table):
    return {row["name"]: row for row in db.execute(f"PRAGMA table_info({table})")}

def _has_table(db, table):
    row = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    ).fetchone()
    return bool(row)

def _add_column_if_missing(db, table, col, col_type):
    cols = _table_info(db, table)
    if col not in cols:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")

def _ensure_jobs_schema(db):
    if not _has_table(db, "jobs"):
        db.execute("""
            CREATE TABLE jobs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT '',
                label TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'plan',   -- plan / running / done
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
    else:
        _add_column_if_missing(db, "jobs", "location",  "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(db, "jobs", "label",     "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(db, "jobs", "status",    "TEXT NOT NULL DEFAULT 'plan'")
        _add_column_if_missing(db, "jobs", "created_at","TEXT NOT NULL DEFAULT (datetime('now'))")

def _ensure_employees_schema(db):
    if not _has_table(db, "employees"):
        db.execute("""
            CREATE TABLE employees(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_no INTEGER UNIQUE,   -- číselník pro "přečíslování"
                name TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        # sem vložíme pár základních záznamů, pokud je tabulka nová
        db.executemany(
            "INSERT INTO employees(employee_no, name) VALUES (?, ?)",
            [(1, "michal"), (2, "john"), (3, "honza")]
        )
    else:
        _add_column_if_missing(db, "employees", "employee_no", "INTEGER")
        _add_column_if_missing(db, "employees", "active",      "INTEGER NOT NULL DEFAULT 1")
        _add_column_if_missing(db, "employees", "created_at",  "TEXT NOT NULL DEFAULT (datetime('now'))")

def _ensure_tasks_schema(db):
    if not _has_table(db, "tasks"):
        db.execute("""
            CREATE TABLE tasks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        db.executemany("INSERT INTO tasks(title, done) VALUES (?, ?)", [
            ("zavolat klientovi", 0),
            ("doplnit materiál", 0),
        ])
    else:
        _add_column_if_missing(db, "tasks", "done", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(db, "tasks", "created_at", "TEXT NOT NULL DEFAULT (datetime('now'))")

def _ensure_timesheets_schema(db):
    if not _has_table(db, "timesheets"):
        db.execute("""
            CREATE TABLE timesheets(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                employee_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL,
                hours REAL NOT NULL DEFAULT 0,
                place TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT ''
            )
        """)
    else:
        _add_column_if_missing(db, "timesheets", "place", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(db, "timesheets", "note",  "TEXT NOT NULL DEFAULT ''")

def _ensure_calendar_schema(db):
    if not _has_table(db, "calendar_events"):
        db.execute("""
            CREATE TABLE calendar_events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                title TEXT NOT NULL,
                kind TEXT NOT NULL DEFAULT 'note',   -- note/work/...
                job_id INTEGER,
                start_time TEXT,
                end_time TEXT,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
    else:
        _add_column_if_missing(db, "calendar_events", "title",      "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(db, "calendar_events", "kind",       "TEXT NOT NULL DEFAULT 'note'")
        _add_column_if_missing(db, "calendar_events", "job_id",     "INTEGER")
        _add_column_if_missing(db, "calendar_events", "start_time", "TEXT")
        _add_column_if_missing(db, "calendar_events", "end_time",   "TEXT")
        _add_column_if_missing(db, "calendar_events", "note",       "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(db, "calendar_events", "created_at", "TEXT NOT NULL DEFAULT (datetime('now'))")

# -----------------------------------------------------------------------------
# Utility
# -----------------------------------------------------------------------------
def normalize_date(s):
    """Bezpečně normalizuje datum do ISO YYYY-MM-DD (akceptuje např. '12.10.2025')."""
    if not s:
        return dt_date.today().isoformat()
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    # např. '2025-10' -> první den v měsíci
    if len(s) == 7 and s[4] == "-":
        return f"{s}-01"
    return dt_date.today().isoformat()

def month_end_from_first(iso_ymd: str) -> str:
    y, m, _ = map(int, iso_ymd.split("-"))
    first = datetime(y, m, 1)
    # první den dalšího měsíce, mínus 1 den
    if m == 12:
        first_next = datetime(y + 1, 1, 1)
    else:
        first_next = datetime(y, m + 1, 1)
    return (first_next - timedelta(days=1)).date().isoformat()

# -----------------------------------------------------------------------------
# API – identity / info
# -----------------------------------------------------------------------------
@app.route("/api/me")
def api_me():
    db = _connect_db()
    _ensure_tasks_schema(db)
    tasks_open = db.execute("SELECT COUNT(*) AS c FROM tasks WHERE done=0").fetchone()["c"]
    return jsonify({
        "user": "Admin",
        "role": "admin",
        "tasks_open": tasks_open
    })

# -----------------------------------------------------------------------------
# API – employees
# -----------------------------------------------------------------------------
@app.route("/api/employees")
def api_employees():
    db = _connect_db()
    _ensure_employees_schema(db)
    rows = db.execute(
        "SELECT id, COALESCE(employee_no, id) AS employee_no, name, active "
        "FROM employees ORDER BY active DESC, employee_no ASC, id ASC"
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/admin/resequence-employees")
def resequence_employees():
    """
    Přečísluje sloupec employee_no na kompaktní pořadí 1..N pouze pro active=1.
    (PRIMARY KEY id se nemění – je to bezpečné.)
    """
    db = _connect_db()
    _ensure_employees_schema(db)
    active = db.execute(
        "SELECT id FROM employees WHERE active=1 ORDER BY COALESCE(employee_no,id), id"
    ).fetchall()
    n = 1
    for r in active:
        db.execute("UPDATE employees SET employee_no=? WHERE id=?", (n, r["id"]))
        n += 1
    db.commit()
    return jsonify({"ok": True, "assigned": n - 1})

# -----------------------------------------------------------------------------
# API – jobs (základ, kompatibilní s frontendem)
# -----------------------------------------------------------------------------
@app.route("/api/jobs", methods=["GET", "POST", "DELETE"])
def api_jobs():
    db = _connect_db()
    _ensure_jobs_schema(db)

    if request.method == "GET":
        rows = db.execute(
            "SELECT id, name, location, label, status FROM jobs "
            "ORDER BY id DESC"
        ).fetchall()
        return jsonify([dict(r) for r in rows])

    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        name = (data.get("name") or data.get("title") or "").strip()
        location = (data.get("location") or "").strip()
        label = (data.get("label") or "").strip()
        status = (data.get("status") or "plan").strip() or "plan"
        if not name:
            return jsonify({"error": "name required"}), 400
        cur = db.execute(
            "INSERT INTO jobs(name, location, label, status) VALUES (?,?,?,?)",
            (name, location, label, status)
        )
        db.commit()
        new_row = db.execute("SELECT id, name, location, label, status FROM jobs WHERE id=?",
                             (cur.lastrowid,)).fetchone()
        return jsonify(dict(new_row)), 200

    # DELETE
    jid = request.args.get("id")
    if not jid:
        return jsonify({"error": "missing id"}), 400
    db.execute("DELETE FROM jobs WHERE id=?", (jid,))
    db.commit()
    return jsonify({"ok": True}), 200

# -----------------------------------------------------------------------------
# API – tasks (read-only pro dashboard)
# -----------------------------------------------------------------------------
@app.route("/api/tasks")
def api_tasks():
    db = _connect_db()
    _ensure_tasks_schema(db)
    rows = db.execute("SELECT id, title, done FROM tasks ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

# -----------------------------------------------------------------------------
# API – timesheets (výkazy)
# -----------------------------------------------------------------------------
@app.route("/gd/api/timesheets", methods=["GET", "POST", "DELETE"])
@app.route("/api/timesheets", methods=["GET", "POST", "DELETE"])
def api_timesheets():
    db = _connect_db()
    _ensure_timesheets_schema(db)

    if request.method == "GET":
        emp = request.args.get("employee_id")
        if emp:
            rows = db.execute(
                "SELECT * FROM timesheets WHERE employee_id=? ORDER BY date DESC, id DESC",
                (emp,)
            ).fetchall()
        else:
            rows = db.execute("SELECT * FROM timesheets ORDER BY date DESC, id DESC").fetchall()
        return jsonify([dict(r) for r in rows]), 200

    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        try:
            date_ = normalize_date(data.get("date"))
            employee_id = int(data.get("employee_id"))
            job_id = int(data.get("job_id"))
            hours = float(str(data.get("hours")).replace(",", "."))
        except Exception:
            return jsonify({"error": "invalid payload"}), 400
        place = (data.get("place") or "").strip()
        note  = (data.get("note") or "").strip()

        cur = db.execute(
            "INSERT INTO timesheets(date, employee_id, job_id, hours, place, note) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (date_, employee_id, job_id, hours, place, note)
        )
        db.commit()
        r = db.execute("SELECT * FROM timesheets WHERE id=?", (cur.lastrowid,)).fetchone()
        return jsonify(dict(r)), 200

    # DELETE
    tid = request.args.get("id")
    if not tid:
        return jsonify({"error": "missing id"}), 400
    db.execute("DELETE FROM timesheets WHERE id=?", (tid,))
    db.commit()
    return jsonify({"ok": True}), 200

# -----------------------------------------------------------------------------
# API – calendar
# -----------------------------------------------------------------------------
@app.route("/gd/api/calendar", methods=["GET", "POST", "DELETE"])
@app.route("/api/calendar", methods=["GET", "POST", "DELETE"])
def api_calendar():
    db = _connect_db()
    _ensure_calendar_schema(db)

    if request.method == "GET":
        d_from = normalize_date(request.args.get("from"))
        d_to   = request.args.get("to")
        if d_to:
            d_to = normalize_date(d_to)
        else:
            # pokud není "to", vrátíme celý měsíc d_from
            d_to = month_end_from_first(d_from)

        rows = db.execute(
            "SELECT * FROM calendar_events WHERE date BETWEEN ? AND ? "
            "ORDER BY date ASC, COALESCE(start_time,'') ASC, id ASC",
            (d_from, d_to)
        ).fetchall()
        return jsonify([dict(r) for r in rows]), 200

    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        date_ = normalize_date(data.get("date"))
        title = (data.get("title") or "").strip()
        kind  = (data.get("kind") or "note").strip() or "note"

        job_id = data.get("job_id")
        try:
            job_id = int(job_id) if job_id not in (None, "") else None
        except (TypeError, ValueError):
            job_id = None

        start_time = (data.get("start_time") or "").strip() or None
        end_time   = (data.get("end_time") or "").strip() or None
        note       = (data.get("note") or "").strip()

        cur = db.execute(
            "INSERT INTO calendar_events(date, title, kind, job_id, start_time, end_time, note) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (date_, title, kind, job_id, start_time, end_time, note)
        )
        db.commit()
        row = db.execute("SELECT * FROM calendar_events WHERE id=?", (cur.lastrowid,)).fetchone()
        return jsonify(dict(row)), 200

    # DELETE
    event_id = request.args.get("id")
    if not event_id:
        return jsonify({"error": "missing id"}), 400
    db.execute("DELETE FROM calendar_events WHERE id=?", (event_id,))
    db.commit()
    return jsonify({"ok": True}), 200

# -----------------------------------------------------------------------------
# WSGI – Render očekává "from main import app"
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Lokální běh (Render použije gunicorn/wsgi)
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=True)
