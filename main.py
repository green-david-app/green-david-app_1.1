# main.py
import os
import sqlite3
from datetime import datetime, date
from typing import Any, Dict, List

from flask import Flask, jsonify, request, session, send_from_directory, make_response

# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-this-secret")

DB_PATH = os.environ.get("DB_PATH", "app.db")


# -----------------------------------------------------------------------------
# DB helpers
# -----------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return [row["name"] for row in cur.fetchall()]


def _ensure_column(conn: sqlite3.Connection, table: str, col: str, ddl_type: str):
    cols = _table_columns(conn, table)
    if col not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl_type}")


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # users
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT
        )
        """
    )

    # jobs
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            customer TEXT,
            location TEXT,
            month_tag TEXT,
            status TEXT DEFAULT 'plan'
        )
        """
    )

    # tasks (lightweight)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER DEFAULT 0
        )
        """
    )

    # employees
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS employees(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            seq INTEGER
        )
        """
    )

    # timesheets
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS timesheets(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            employee_id INTEGER NOT NULL,
            job_id INTEGER,
            hours REAL NOT NULL,
            place TEXT,
            note TEXT,
            FOREIGN KEY(employee_id) REFERENCES employees(id),
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
        """
    )

    # calendar
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS calendar_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            title TEXT NOT NULL,
            job_id INTEGER,
            start_time TEXT,
            end_time TEXT,
            location TEXT,
            note TEXT,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
        """
    )

    # ---- migrations for older DBs ----
    # timesheets.note
    _ensure_column(conn, "timesheets", "note", "TEXT")
    # calendar columns
    for c, t in [
        ("job_id", "INTEGER"),
        ("start_time", "TEXT"),
        ("end_time", "TEXT"),
        ("location", "TEXT"),
        ("note", "TEXT"),
    ]:
        _ensure_column(conn, "calendar_events", c, t)

    # seed admin user if missing
    cur.execute("SELECT COUNT(*) AS n FROM users")
    if cur.fetchone()["n"] == 0:
        cur.execute(
            "INSERT OR IGNORE INTO users(email, password, name) VALUES(?,?,?)",
            ("admin@greendavid.local", "admin123", "Admin"),
        )

    # seed some employees if none
    cur.execute("SELECT COUNT(*) AS n FROM employees")
    if cur.fetchone()["n"] == 0:
        names = ["michal", "john", "honza"]
        for i, n in enumerate(names, start=1):
            cur.execute(
                "INSERT INTO employees(name, active, seq) VALUES(?,?,?)",
                (n, 1, i),
            )

    conn.commit()
    conn.close()


init_db()


# -----------------------------------------------------------------------------
# Utils
# -----------------------------------------------------------------------------
def _normalize_date(s: str) -> str:
    """
    Accepts formats like '2025-10-13', '13.10.2025', '13/10/2025'
    and returns ISO 'YYYY-MM-DD'.
    """
    if not s:
        return date.today().isoformat()
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    # fallback – try to parse like '2025-10-13T00:00:00'
    try:
        return datetime.fromisoformat(s).date().isoformat()
    except Exception:
        return date.today().isoformat()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, any]:
    return {k: row[k] for k in row.keys()}


def _json_ok(**extra):
    d = {"ok": True}
    d.update(extra)
    return jsonify(d)


def _json_err(msg: str, code: int = 400):
    return jsonify({"ok": False, "error": msg}), code


# -----------------------------------------------------------------------------
# Auth
# -----------------------------------------------------------------------------
@app.post("/api/login")
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    if not email or not password:
        return _json_err("email/password required", 400)

    db = get_db()
    row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not row or row["password"] != password:
        return _json_err("invalid credentials", 401)

    session["uid"] = row["id"]
    session["email"] = row["email"]
    session["name"] = row["name"] or row["email"]
    return _json_ok(user={"email": row["email"], "name": row["name"] or "User"})


@app.get("/api/logout")
def api_logout():
    session.clear()
    return _json_ok()


@app.get("/api/me")
def api_me():
    if "uid" in session:
        return jsonify(
            {
                "logged_in": True,
                "user": {"email": session.get("email"), "name": session.get("name")},
            }
        )
    return jsonify({"logged_in": False, "user": None})


# -----------------------------------------------------------------------------
# Jobs
# -----------------------------------------------------------------------------
@app.get("/api/jobs")
def api_jobs_list():
    db = get_db()
    rows = db.execute(
        "SELECT id, title, customer, location, month_tag, status FROM jobs ORDER BY id DESC"
    ).fetchall()
    return jsonify([_row_to_dict(r) for r in rows])


@app.post("/api/jobs")
def api_jobs_create():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or data.get("name") or "").strip()
    if not title:
        return _json_err("title required")
    customer = (data.get("customer") or "").strip()
    location = (data.get("location") or "").strip()
    month_tag = (data.get("month_tag") or data.get("month") or "").strip()
    status = (data.get("status") or "plan").strip()
    db = get_db()
    cur = db.execute(
        "INSERT INTO jobs(title, customer, location, month_tag, status) VALUES(?,?,?,?,?)",
        (title, customer, location, month_tag, status),
    )
    db.commit()
    return _json_ok(id=cur.lastrowid)


@app.delete("/api/jobs")
def api_jobs_delete():
    jid = request.args.get("id")
    if not jid:
        return _json_err("id required", 400)
    db = get_db()
    db.execute("DELETE FROM jobs WHERE id = ?", (jid,))
    db.commit()
    return _json_ok()


# -----------------------------------------------------------------------------
# Tasks
# -----------------------------------------------------------------------------
@app.get("/api/tasks")
def api_tasks_list():
    db = get_db()
    rows = db.execute("SELECT id, title, done FROM tasks ORDER BY id DESC").fetchall()
    return jsonify([_row_to_dict(r) for r in rows])


@app.post("/api/tasks")
def api_tasks_create():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return _json_err("title required")
    done = 1 if data.get("done") else 0
    db = get_db()
    cur = db.execute("INSERT INTO tasks(title, done) VALUES(?,?)", (title, done))
    db.commit()
    return _json_ok(id=cur.lastrowid)


@app.delete("/api/tasks")
def api_tasks_delete():
    tid = request.args.get("id")
    if not tid:
        return _json_err("id required", 400)
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", (tid,))
    db.commit()
    return _json_ok()


# -----------------------------------------------------------------------------
# Employees
# -----------------------------------------------------------------------------
@app.get("/api/employees")
def api_employees():
    db = get_db()
    rows = db.execute(
        "SELECT id, name, active, COALESCE(seq, id) as seq FROM employees ORDER BY seq ASC"
    ).fetchall()
    return jsonify([_row_to_dict(r) for r in rows])


@app.post("/api/employees")
def api_employees_create():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return _json_err("name required")
    active = 1 if data.get("active", 1) else 0
    db = get_db()
    # compute next seq
    next_seq = (
        db.execute("SELECT COALESCE(MAX(seq), 0) + 1 AS n FROM employees").fetchone()["n"]
    )
    cur = db.execute(
        "INSERT INTO employees(name, active, seq) VALUES(?,?,?)",
        (name, active, next_seq),
    )
    db.commit()
    return _json_ok(id=cur.lastrowid)


@app.get("/admin/resequence-employees")
def resequence_employees_preview():
    db = get_db()
    rows = db.execute(
        "SELECT id, name, active, COALESCE(seq, id) AS seq FROM employees ORDER BY seq ASC, id ASC"
    ).fetchall()
    preview = [{"id": r["id"], "name": r["name"], "from": r["seq"], "to": i + 1} for i, r in enumerate(rows)]
    return jsonify(preview)


@app.post("/admin/resequence-employees")
def resequence_employees_apply():
    db = get_db()
    rows = db.execute(
        "SELECT id FROM employees ORDER BY COALESCE(seq, id) ASC, id ASC"
    ).fetchall()
    for i, r in enumerate(rows, start=1):
        db.execute("UPDATE employees SET seq = ? WHERE id = ?", (i, r["id"]))
    db.commit()
    return _json_ok()


# -----------------------------------------------------------------------------
# Timesheets
# -----------------------------------------------------------------------------
def _timesheet_row_dict(r: sqlite3.Row) -> Dict[str, any]:
    return {
        "id": r["id"],
        "date": r["date"],
        "employee_id": r["employee_id"],
        "job_id": r["job_id"],
        "hours": r["hours"],
        "place": r["place"],
        "note": r["note"],
    }


@app.get("/api/timesheets")
@app.get("/gd/api/timesheets")
def api_timesheets_list():
    employee_id = request.args.get("employee_id")
    db = get_db()
    if employee_id:
        rows = db.execute(
            "SELECT * FROM timesheets WHERE employee_id = ? ORDER BY date DESC, id DESC",
            (employee_id,),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM timesheets ORDER BY date DESC, id DESC").fetchall()
    return jsonify([_timesheet_row_dict(r) for r in rows])


@app.post("/api/timesheets")
@app.post("/gd/api/timesheets")
def api_timesheets_create():
    data = request.get_json(silent=True) or {}
    employee_id = data.get("employee_id")
    job_id = data.get("job_id")
    hours = float(data.get("hours") or 0)
    place = (data.get("place") or "").strip()
    note = (data.get("note") or data.get("description") or "").strip()
    dt = _normalize_date(data.get("date"))
    if not employee_id or hours <= 0:
        return _json_err("employee_id and hours are required")
    db = get_db()
    cur = db.execute(
        "INSERT INTO timesheets(date, employee_id, job_id, hours, place, note) VALUES(?,?,?,?,?,?)",
        (dt, employee_id, job_id, hours, place, note),
    )
    db.commit()
    return _json_ok(id=cur.lastrowid)


# -----------------------------------------------------------------------------
# Calendar
# -----------------------------------------------------------------------------
def _calendar_row_dict(r: sqlite3.Row) -> Dict[str, any]:
    return {
        "id": r["id"],
        "date": r["date"],
        "title": r["title"],
        "job_id": r["job_id"],
        "start_time": r["start_time"],
        "end_time": r["end_time"],
        "location": r["location"],
        "note": r["note"],
    }


@app.get("/api/calendar")
@app.get("/gd/api/calendar")
def api_calendar_list():
    d_from = _normalize_date(request.args.get("from") or request.args.get("date_from") or date.today().isoformat())
    d_to = _normalize_date(request.args.get("to") or request.args.get("date_to") or date.today().isoformat())

    db = get_db()
    # ensure schema (old DBs)
    for c, t in [
        ("job_id", "INTEGER"),
        ("start_time", "TEXT"),
        ("end_time", "TEXT"),
        ("location", "TEXT"),
        ("note", "TEXT"),
    ]:
        _ensure_column(db, "calendar_events", c, t)
    rows = db.execute(
        "SELECT * FROM calendar_events WHERE date BETWEEN ? AND ? ORDER BY date ASC, start_time ASC",
        (d_from, d_to),
    ).fetchall()
    return jsonify([_calendar_row_dict(r) for r in rows])


@app.post("/api/calendar")
@app.post("/gd/api/calendar")
def api_calendar_create():
    data = request.get_json(silent=True) or {}

    dt = _normalize_date(data.get("date"))
    title = (data.get("title") or data.get("name") or "Poznámka").strip()
    job_id = data.get("job_id")
    start_time = (data.get("start_time") or "").strip()
    end_time = (data.get("end_time") or "").strip()
    location = (data.get("location") or "").strip()
    note = (data.get("note") or data.get("description") or "").strip()

    db = get_db()
    for c, t in [
        ("job_id", "INTEGER"),
        ("start_time", "TEXT"),
        ("end_time", "TEXT"),
        ("location", "TEXT"),
        ("note", "TEXT"),
    ]:
        _ensure_column(db, "calendar_events", c, t)

    cur = db.execute(
        "INSERT INTO calendar_events(date, title, job_id, start_time, end_time, location, note) VALUES(?,?,?,?,?,?,?)",
        (dt, title, job_id, start_time, end_time, location, note),
    )
    db.commit()
    return _json_ok(id=cur.lastrowid)


# -----------------------------------------------------------------------------
# Static fallbacks (logo, css)
# -----------------------------------------------------------------------------
@app.get("/logo.jpg")
def static_logo():
    # pokud máš soubor v kořeni, Flask ho pošle; jinak 200 prázdné
    if os.path.exists("logo.jpg"):
        return send_from_directory(".", "logo.jpg")
    return make_response(b"", 200, {"Content-Type": "image/jpeg"})


@app.get("/style.css")
def static_css():
    if os.path.exists("style.css"):
        return send_from_directory(".", "style.css")
    return make_response(b"", 200, {"Content-Type": "text/css"})


# -----------------------------------------------------------------------------
# Root – volitelný placeholder (200 OK)
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return make_response(b"", 200, {"Content-Type": "text/html; charset=utf-8"})


# -----------------------------------------------------------------------------
# WSGI
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
