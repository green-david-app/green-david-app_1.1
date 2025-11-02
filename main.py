import os, re, io, sqlite3
from datetime import datetime
from flask import Flask, send_from_directory, request, jsonify, session, g, send_file, abort, render_template, make_response
from jinja2 import TemplateNotFound

DB_PATH = os.environ.get("DB_PATH", "app.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-" + os.urandom(16).hex())
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = SECRET_KEY
os.makedirs(UPLOAD_DIR, exist_ok=True)

from functools import wraps
def require_role(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        return wrapper
    return deco

TEMPLATE_MARKER = "<!-- GD_V2 -->"

def _no_store(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp

def _normalize_date(v):
    if not v: return v
    s = str(v).strip()
    import re as _re
    m = _re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        y,M,d = m.groups()
        return f"{int(y):04d}-{int(M):02d}-{int(d):02d}"
    m = _re.match(r"^(\d{1,2})[\.\s-](\d{1,2})[\.\s-](\d{4})$", s)
    if m:
        d,M,y = m.groups()
        return f"{int(y):04d}-{int(M):02d}-{int(d):02d}"
    return s

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

def ensure_schema():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        name TEXT,
        role TEXT DEFAULT 'admin',
        password_hash TEXT,
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
        title TEXT,
        name TEXT,
        client TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Plán',
        city TEXT NOT NULL DEFAULT '',
        code TEXT NOT NULL DEFAULT '',
        date TEXT,
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
    CREATE TABLE IF NOT EXISTS calendar_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        title TEXT NOT NULL,
        kind TEXT NOT NULL DEFAULT 'note',
        job_id INTEGER,
        start_time TEXT,
        end_time TEXT,
        note TEXT DEFAULT '',
        color TEXT DEFAULT '#2e7d32'
    );
    """)
    db.commit()

def migrate_legacy_defaults():
    db = get_db()
    info = {r[1]: r for r in db.execute("PRAGMA table_info(jobs)").fetchall()}
    now = datetime.utcnow().isoformat()
    if "created_at" in info:
        db.execute("UPDATE jobs SET created_at=? WHERE created_at IS NULL OR created_at=''", (now,))
    if "updated_at" in info:
        db.execute("UPDATE jobs SET updated_at=? WHERE updated_at IS NULL OR updated_at=''", (now,))
    if "owner_id" in info:
        admin = db.execute("SELECT id FROM users WHERE active=1 ORDER BY id ASC").fetchone()
        owner = admin["id"] if admin else 1
        db.execute("UPDATE jobs SET owner_id=? WHERE owner_id IS NULL OR CAST(owner_id AS TEXT)=''", (owner,))
    db.commit()

@app.before_request
def _ensure():
    ensure_schema()
    migrate_legacy_defaults()

@app.route("/")
def index():
    if os.path.exists("index.html"):
        return send_from_directory(".", "index.html")
    from flask import redirect
    return redirect('/calendar.html', code=302)
    return _no_store(make_response(html))

@app.route("/calendar")
def page_calendar():
    if os.path.exists("calendar.html"):
        return send_from_directory(".", "calendar.html")
    return index()

@app.route("/calendar.html")
def page_calendar_html():
    if os.path.exists("calendar.html"):
        return send_from_directory(".", "calendar.html")
    return index()

from jinja2 import TemplateNotFound
from flask import render_template, make_response

def _render_or_fallback(tpl_name, fallback_html):
    try:
        html = render_template(tpl_name)
        if TEMPLATE_MARKER in html:
            return _no_store(make_response(html))
    except TemplateNotFound:
        pass
    return _no_store(make_response(fallback_html))

@app.route("/employees")
def page_employees():
    return _render_or_fallback("employees.html", "<!-- fallback employees -->")

@app.route("/brigadnici.html")
def page_brigadnici():
    return _render_or_fallback("brigadnici.html", "<!-- fallback brigadnici -->")

@app.route("/timesheets.html")
def page_timesheets():
    try:
        return render_template("timesheets.html")
    except TemplateNotFound:
        return index()

@app.route("/api/me")
def api_me():
    return jsonify({"ok": True})

@app.route("/api/employees", methods=["GET","POST","DELETE"])
def api_employees():
    db = get_db()
    if request.method=="GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM employees ORDER BY id DESC")]
        scope = (request.args.get("scope") or "").lower().strip()
        if scope == "brig":
            rows = [e for e in rows if "brig" in str(e.get("role","")).lower()]
        elif scope == "employees":
            rows = [e for e in rows if "brig" not in str(e.get("role","")).lower()]
        return jsonify({"ok": True, "employees": rows})
    if request.method=="POST":
        data = request.get_json(force=True, silent=True) or {}
        name = (data.get("name") or "").strip()
        role = (data.get("role") or "worker").strip()
        if not name: return jsonify({"ok": False}), 400
        db.execute("INSERT INTO employees(name,role) VALUES (?,?)", (name, role))
        db.commit()
        return jsonify({"ok": True})
    # DELETE
    eid = request.args.get("id", type=int)
    if not eid: return jsonify({"ok": False}), 400
    db.execute("DELETE FROM employees WHERE id=?", (eid,))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/jobs", methods=["GET","POST"])
def api_jobs():
    db = get_db()
    if request.method=="GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY id DESC")]
        return jsonify({"ok": True, "jobs": rows})
    data = request.get_json(force=True, silent=True) or {}
    title = (data.get("title") or data.get("name") or "").strip()
    city = (data.get("city") or "").strip()
    code = (data.get("code") or "").strip()
    if not all([title,city,code]): return jsonify({"ok": False}), 400
    db.execute("INSERT INTO jobs(title,client,status,city,code,date,note) VALUES (?,?,?,?,?,?,?)",
               (title, data.get("client") or "", data.get("status") or "Plán", city, code, data.get("date"), data.get("note") or ""))
    db.commit()
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
