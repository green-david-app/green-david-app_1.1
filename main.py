import os, sqlite3, io
from datetime import datetime, date, timedelta
from flask import Flask, send_from_directory, request, jsonify, session, g, render_template, send_file
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.environ.get("DB_PATH", "app.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-" + os.urandom(16).hex())
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = SECRET_KEY
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    db = get_db()
    row = db.execute("SELECT id,email,name,role,active FROM users WHERE id=?", (uid,)).fetchone()
    return dict(row) if row else None

def require_auth():
    u = current_user()
    if not u or not u.get("active"):
        return None, (jsonify({"ok": False, "error": "unauthorized"}), 401)
    return u, None

def require_role(write=False):
    u, err = require_auth()
    if err: return None, err
    if write and u["role"] not in ("admin","manager"):
        return None, (jsonify({"ok": False, "error": "forbidden"}), 403)
    return u, None

def _normalize_date(v):
    if not v: return v
    s = str(v).strip()
    import re as _re
    m = _re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        y, M, d = m.groups()
        return f"{int(y):04d}-{int(M):02d}-{int(d):02d}"
    m = _re.match(r"^(\d{1,2})[\\.\s-](\d{1,2})[\\.\s-](\d{4})$", s)
    if m:
        d, M, y = m.groups()
        return f"{int(y):04d}-{int(M):02d}-{int(d):02d}"
    return s

# ---------- bootstrap (minimal tables we touch) ----------
def ensure_schema():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin','manager','worker')),
        password_hash TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'worker'
    );
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        client TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Plán',
        city TEXT NOT NULL DEFAULT '',
        code TEXT NOT NULL DEFAULT '',
        date TEXT NOT NULL DEFAULT '',
        note TEXT
    );
    CREATE TABLE IF NOT EXISTS timesheets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        hours REAL NOT NULL DEFAULT 0,
        place TEXT DEFAULT '',
        activity TEXT DEFAULT ''
    );
    """)
    db.commit()

@app.before_request
def _ensure():
    ensure_schema()

# ---------- static ----------
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

# ---------- employees API ----------
@app.route("/api/employees", methods=["GET","POST","PATCH","DELETE"])
def api_employees():
    # read allowed to all logged in; writes require manager/admin
    write = (request.method != "GET")
    u, err = require_role(write=write) if write else require_auth()
    if err: return err
    db = get_db()
    if request.method == "GET":
        rows = db.execute("SELECT * FROM employees ORDER BY id DESC").fetchall()
        return jsonify({"ok": True, "employees": [dict(r) for r in rows]})
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        name = data.get("name"); role = data.get("role") or "worker"
        if not name: return jsonify({"ok": False, "error":"invalid_input"}), 400
        db.execute("INSERT INTO employees(name,role) VALUES (?,?)", (name, role))
        db.commit()
        return jsonify({"ok": True})
    if request.method == "PATCH":
        data = request.get_json(force=True, silent=True) or {}
        eid = data.get("id")
        if not eid: return jsonify({"ok": False, "error":"missing_id"}), 400
        fields = []; params = []
        if "name" in data: fields.append("name=?"); params.append(data["name"])
        if "role" in data: fields.append("role=?"); params.append(data["role"] or "worker")
        if not fields: return jsonify({"ok": False, "error":"no_fields"}), 400
        params.append(int(eid))
        db.execute(f"UPDATE employees SET {', '.join(fields)} WHERE id=?", params)
        db.commit()
        return jsonify({"ok": True})
    # DELETE
    eid = request.args.get("id", type=int)
    if not eid: return jsonify({"ok": False, "error":"missing_id"}), 400
    db.execute("DELETE FROM employees WHERE id=?", (eid,))
    db.commit()
    return jsonify({"ok": True})

# ---------- template routes ----------
@app.route("/employees")
def page_employees():
    return render_template("employees.html")

@app.route("/brigadnici.html")
def page_brigadnici():
    return render_template("brigadnici.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
