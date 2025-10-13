import os
import sqlite3
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, request, g, send_from_directory, session

# ---------- App setup ----------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

DB_PATH = os.environ.get("DB_PATH", "app.db")
os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)


# ---------- DB helpers ----------
def get_db() -> sqlite3.Connection:
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
        _ensure_base_schema(db)
    return db


@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()


def _col_exists(db: sqlite3.Connection, table: str, column: str) -> bool:
    cur = db.execute("PRAGMA table_info(%s)" % table)
    return any(row["name"] == column for row in cur.fetchall())


def _ensure_base_schema(db: sqlite3.Connection) -> None:
    # Users (simple auth: plaintext password just for internal tool)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            role TEXT DEFAULT 'admin'
        )
        """
    )

    # Jobs
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT,
            period TEXT,
            status TEXT DEFAULT 'Plan',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Employees
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            display_order INTEGER
        )
        """
    )

    # Timesheets
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS timesheets (
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

    # Calendar events
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            title TEXT,
            note TEXT,
            job_id INTEGER,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
        """
    )

    # --- Migrations / backfills ---
    # Add missing columns if DB already existed
    for tbl, cols in {
        "timesheets": ["place", "note"],
        "calendar_events": ["start_time", "end_time", "note", "job_id"],
        "employees": ["display_order"],
    }.items():
        for col in cols:
            if not _col_exists(db, tbl, col):
                # Reasonable types chosen to be compatible with existing data
                ddl_type = "TEXT"
                if tbl == "employees" and col == "display_order":
                    ddl_type = "INTEGER"
                if tbl == "calendar_events" and col == "job_id":
                    ddl_type = "INTEGER"
                db.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {ddl_type}")

    # Ensure default admin exists
    cur = db.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        db.execute(
            "INSERT INTO users(email, password, name, role) VALUES (?, ?, ?, ?)",
            ("admin@greendavid.local", "admin123", "Admin", "admin"),
        )

    # Ensure some default employees (so select boxes are not empty)
    cur = db.execute("SELECT COUNT(*) AS c FROM employees")
    if cur.fetchone()["c"] == 0:
        db.executemany(
            "INSERT INTO employees(name, active, display_order) VALUES (?, 1, ?)",
            [("michal", 1), ("john", 2), ("honza", 3)],
        )

    db.commit()


# ---------- Helpers ----------
def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_date(s: Optional[str]) -> str:
    """Accept 'YYYY-MM-DD' or 'DD.MM.YYYY' and return 'YYYY-MM-DD'."""
    if not s:
        return date.today().isoformat()
    s = s.strip()
    # 2025-10-13
    try:
        return datetime.strptime(s, "%Y-%m-%d").date().isoformat()
    except ValueError:
        pass
    # 13.10.2025
    try:
        return datetime.strptime(s, "%d.%m.%Y").date().isoformat()
    except ValueError:
        pass
    return date.today().isoformat()


def _json_ok(**extra):
    d = {"ok": True}
    d.update(extra)
    return jsonify(d)


def _json_err(msg: str, code: int = 400):
    return jsonify({"ok": False, "error": msg}), code


# ---------- Auth ----------
@app.route("/api/me", methods=["GET"])
def api_me():
    if session.get("user_id"):
        return jsonify(
            {
                "authenticated": True,
                "email": session.get("email"),
                "name": session.get("name", ""),
                "role": session.get("role", "admin"),
            }
        )
    return jsonify({"authenticated": False})


@app.route("/api/login", methods=["POST"])
def api_login():
    db = get_db()
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "")

    if not email or not password:
        return _json_err("email and password required", 400)

    cur = db.execute("SELECT * FROM users WHERE LOWER(email)=?", (email,))
    row = cur.fetchone()
    if not row or row["password"] != password:
        return _json_err("bad credentials", 401)

    session["user_id"] = row["id"]
    session["email"] = row["email"]
    session["name"] = row["name"]
    session["role"] = row["role"]
    return _json_ok()


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return _json_ok()


# ---------- Jobs ----------
@app.route("/api/jobs", methods=["GET", "POST", "DELETE"])
def api_jobs():
    db = get_db()
    if request.method == "GET":
        rows = db.execute(
            "SELECT id, name, city, period, status FROM jobs ORDER BY id DESC"
        ).fetchall()
        return jsonify([dict(r) for r in rows])

    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        name = (data.get("name") or "").strip()
        city = (data.get("city") or "").strip()
        period = (data.get("period") or "").strip()
        status = (data.get("status") or "Plán").strip()
        if not name:
            return _json_err("name required")
        db.execute(
            "INSERT INTO jobs(name, city, period, status) VALUES (?, ?, ?, ?)",
            (name, city, period, status),
        )
        db.commit()
        return _json_ok()

    # DELETE
    jid = request.args.get("id")
    if not jid:
        return _json_err("id required", 400)
    db.execute("DELETE FROM jobs WHERE id=?", (jid,))
    db.commit()
    return _json_ok()


# ---------- Tasks (dummy small store on DB to persist) ----------
@app.route("/api/tasks", methods=["GET", "POST", "DELETE"])
def api_tasks():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    if request.method == "GET":
        rows = db.execute("SELECT id, title, done FROM tasks ORDER BY id DESC").fetchall()
        return jsonify([dict(r) for r in rows])
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        title = (data.get("title") or "").strip()
        if not title:
            return _json_err("title required")
        db.execute("INSERT INTO tasks(title) VALUES (?)", (title,))
        db.commit()
        return _json_ok()
    # DELETE
    tid = request.args.get("id")
    if not tid:
        return _json_err("id required", 400)
    db.execute("DELETE FROM tasks WHERE id=?", (tid,))
    db.commit()
    return _json_ok()


# ---------- Employees ----------
@app.route("/api/employees", methods=["GET"])
def api_employees():
    db = get_db()
    rows = db.execute(
        "SELECT id, name, active, COALESCE(display_order, id) AS display_order "
        "FROM employees WHERE active=1 ORDER BY display_order ASC, id ASC"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/admin/resequence-employees", methods=["POST", "GET"])
def resequence_employees():
    """Compact display_order for active employees to 1..N (removes 'dead' gaps)."""
    db = get_db()
    rows = db.execute(
        "SELECT id FROM employees WHERE active=1 ORDER BY COALESCE(display_order, id) ASC, id ASC"
    ).fetchall()
    for idx, r in enumerate(rows, start=1):
        db.execute("UPDATE employees SET display_order=? WHERE id=?", (idx, r["id"]))
    db.commit()
    return _json_ok(resequenced=len(rows))


# ---------- Timesheets ----------
def _ensure_timesheets_indexes(db: sqlite3.Connection) -> None:
    db.execute("CREATE INDEX IF NOT EXISTS idx_timesheets_employee ON timesheets(employee_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_timesheets_date ON timesheets(date)")


@app.route("/gd/api/timesheets", methods=["GET", "POST"])
@app.route("/api/timesheets", methods=["GET", "POST"])
def api_timesheets():
    db = get_db()
    _ensure_timesheets_indexes(db)
    if request.method == "GET":
        employee_id = request.args.get("employee_id")
        sql = (
            "SELECT t.id, t.date, t.employee_id, e.name AS employee_name, "
            "t.job_id, j.name AS job_name, t.hours, t.place, t.note "
            "FROM timesheets t "
            "LEFT JOIN employees e ON e.id=t.employee_id "
            "LEFT JOIN jobs j ON j.id=t.job_id "
        )
        args: Tuple[Any, ...] = ()
        if employee_id:
            sql += "WHERE t.employee_id=? "
            args = (employee_id,)
        sql += "ORDER BY t.date DESC, t.id DESC"
        rows = db.execute(sql, args).fetchall()
        return jsonify([dict(r) for r in rows])

    # POST
    data = request.get_json(force=True, silent=True) or {}
    date_str = _normalize_date(data.get("date"))
    employee_id = int(data.get("employee_id"))
    job_id = int(data.get("job_id")) if data.get("job_id") else None
    hours = float(data.get("hours") or 0)
    place = (data.get("place") or "").strip()
    note = (data.get("note") or "").strip()

    cur = db.execute(
        "INSERT INTO timesheets(date, employee_id, job_id, hours, place, note) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (date_str, employee_id, job_id, hours, place, note),
    )
    db.commit()
    return _json_ok(id=cur.lastrowid)


# ---------- Calendar ----------
def _ensure_calendar_indexes(db: sqlite3.Connection) -> None:
    db.execute("CREATE INDEX IF NOT EXISTS idx_cal_date ON calendar_events(date)")


@app.route("/gd/api/calendar", methods=["GET", "POST"])
@app.route("/api/calendar", methods=["GET", "POST"])
def api_calendar():
    db = get_db()
    _ensure_calendar_indexes(db)

    if request.method == "GET":
        d_from = _normalize_date(request.args.get("from"))
        d_to = _normalize_date(request.args.get("to"))
        rows = db.execute(
            "SELECT id, date, start_time, end_time, title, note, job_id "
            "FROM calendar_events WHERE date BETWEEN ? AND ? "
            "ORDER BY date ASC, COALESCE(start_time,'') ASC, id ASC",
            (d_from, d_to),
        ).fetchall()
        return jsonify([dict(r) for r in rows])

    # POST create/update
    data = request.get_json(force=True, silent=True) or {}
    ev_id = data.get("id")
    date_str = _normalize_date(data.get("date"))
    start_time = (data.get("start_time") or "").strip()
    end_time = (data.get("end_time") or "").strip()
    title = (data.get("title") or "").strip()
    note = (data.get("note") or "").strip()
    job_id = int(data.get("job_id")) if data.get("job_id") else None

    if ev_id:
        db.execute(
            "UPDATE calendar_events SET date=?, start_time=?, end_time=?, title=?, note=?, job_id=? "
            "WHERE id=?",
            (date_str, start_time, end_time, title, note, job_id, ev_id),
        )
        db.commit()
        return _json_ok(id=ev_id)

    cur = db.execute(
        "INSERT INTO calendar_events(date, start_time, end_time, title, note, job_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (date_str, start_time, end_time, title, note, job_id),
    )
    db.commit()
    return _json_ok(id=cur.lastrowid)


# ---------- Static (logo/style) ----------
@app.route("/logo.jpg")
def logo():
    return send_from_directory(".", "logo.jpg")


@app.route("/style.css")
def style():
    return send_from_directory(".", "style.css")


# ---------- Root (optional info page) ----------
@app.route("/", methods=["GET"])
def root():
    # Serve bare page if your frontend is separate. Keeping 200 for Render healthcheck.
    return "", 200


# ---------- WSGI ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=True)
